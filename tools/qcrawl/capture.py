"""Per-page evidence capture with Playwright.

For each surface handed in, this navigates with a real browser and saves:
  - `screenshot.png`        (full-page, desktop viewport)
  - `screenshot-mobile.png` (full-page, mobile viewport)
  - `page.html`             (rendered DOM, so JS-built content is captured)
  - `meta.json`             (title, description, canonical, OG, JSON-LD types, h1s)

Resilience (decision D9 — partial success is success):
  - per-page timeout with load -> domcontentloaded fallback + a bounded
    networkidle "settle" so JS-hydrated content is captured;
  - password / Cloudflare-challenge detection recorded per page;
  - if the browser CRASHES mid-run, relaunch once and continue;
  - if the browser won't launch at all, every surface is recorded as errored
    (the run still produces a manifest);
  - mobile failures are isolated and never affect desktop evidence.

All artifact paths are stored relative to the run directory so the audit report
can cite them portably.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PWError
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from .discovery import Surface, extract_links

DESKTOP_VIEWPORT = {"width": 1366, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}
# Realistic UAs (no "bot" tag) — a declared bot is blocked instantly by WAFs.
UA_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)
UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)

# Lightweight stealth (decision D22) — defeats bot checks that key on automation
# flags / missing JS. Honest fallback: if a hard WAF still blocks, we report it.
_STEALTH_ARGS = ["--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
_STEALTH_INIT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""

_PASSWORD_SIGNS = ("enter store password", "template-password", "store is password protected")
_CHALLENGE_SIGNS = ("just a moment", "attention required", "checking your browser", "cf-browser-verification")


@dataclass
class PageEvidence:
    order: int
    url: str
    category: str = "other"
    final_url: Optional[str] = None
    status: Optional[int] = None
    load_ms: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical: Optional[str] = None
    h1s: list[str] = field(default_factory=list)
    og: dict = field(default_factory=dict)
    jsonld_types: list[str] = field(default_factory=list)
    has_favicon: bool = False
    blocked: Optional[str] = None  # 'password' | 'challenge' | None
    error: Optional[str] = None
    dir: Optional[str] = None
    html_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    screenshot_mobile_path: Optional[str] = None
    meta_path: Optional[str] = None
    # interaction captures (Fix B — see decision D21)
    drawer_screenshot_path: Optional[str] = None
    drawer_html_path: Optional[str] = None
    popup_screenshot_path: Optional[str] = None
    interactions: dict = field(default_factory=dict)  # {'popup':..., 'add_to_cart':...}


def slugify(url: str) -> str:
    path = urlparse(url).path.strip("/")
    last = path.split("/")[-1] if path else "home"
    last = re.sub(r"[^A-Za-z0-9_-]+", "-", last).strip("-")[:40]
    return last or "page"


def extract_meta(html: str) -> dict:
    """Pull SEO/structured metadata out of rendered HTML (network-free, testable)."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else None

    canon = soup.find("link", rel=lambda v: bool(v) and "canonical" in v)
    canonical = canon.get("href") if canon else None

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)][:5]

    og = {}
    for tag in soup.find_all("meta"):
        prop = tag.get("property", "")
        if prop.startswith("og:") and tag.get("content"):
            og[prop] = tag["content"]

    jsonld_types: list[str] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get("@type"):
                t = item["@type"]
                jsonld_types.extend(t if isinstance(t, list) else [t])

    favicon = soup.find("link", rel=lambda v: bool(v) and "icon" in v)

    return {
        "title": title,
        "meta_description": meta_description,
        "canonical": canonical,
        "h1s": h1s,
        "og": og,
        "jsonld_types": sorted(set(jsonld_types)),
        "has_favicon": bool(favicon),
    }


def detect_block(html: str) -> Optional[str]:
    """Return 'password' / 'challenge' if the HTML looks like a gate, else None."""
    low = (html or "").lower()
    if any(s in low for s in _PASSWORD_SIGNS):
        return "password"
    if any(s in low for s in _CHALLENGE_SIGNS):
        return "challenge"
    return None


def _safe_close(obj) -> None:
    try:
        if obj is not None:
            obj.close()
    except Exception:
        pass


def _navigate(page, url: str, timeout_ms: int, settle_ms: int = 1500):
    """goto with graceful fallback (load -> domcontentloaded) + bounded settle.

    The settle waits for networkidle so JS-hydrated content is present before we
    snapshot; it's best-effort and never raises. Returns (response|None, err|None).
    """
    resp, err = None, None
    try:
        resp = page.goto(url, wait_until="load", timeout=timeout_ms)
    except PWTimeout:
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except (PWTimeout, PWError) as exc:
            err = type(exc).__name__
    except PWError as exc:
        err = type(exc).__name__

    if settle_ms:
        try:
            page.wait_for_load_state("networkidle", timeout=settle_ms)
        except (PWTimeout, PWError):
            pass  # hydration may never settle — snapshot what we have
    return resp, err


def _rel(path: Path, run_dir: Path) -> str:
    return path.relative_to(run_dir).as_posix()


# --- interaction recipes (Fix B / D21) — generic + best-effort; failure => 'unverified' ---
_ATC_SELECTORS = [
    'form[action*="/cart/add"] button[type="submit"]',
    'form[action*="/cart/add"] [type="submit"]',
    'button[name="add"]', '[name="add"]',
    'button[data-add-to-cart]', '[data-add-to-cart]',
    'button:has-text("Add to cart")', 'button:has-text("Add to Cart")',
    'button:has-text("Add to bag")',
]
_POPUP_SELECTOR = ('[role="dialog"], [class*="modal" i], [class*="popup" i], '
                   '[id*="popup" i], [class*="newsletter" i]')
_CLOSE_SELECTORS = ['[aria-label*="close" i]', '[class*="close" i]',
                    'button:has-text("No thanks")', 'button:has-text("Close")']


def _handle_popup(page, pdir: Path, run_dir: Path, ev: "PageEvidence") -> None:
    """Screenshot a visible popup/modal (e.g. email capture), then dismiss it so the
    main screenshot is clean. Records tri-state interaction status."""
    try:
        el = page.query_selector(_POPUP_SELECTOR)
        if el and el.is_visible():
            shot = pdir / "popup.png"
            try:
                el.screenshot(path=str(shot))
            except (PWError, OSError):
                page.screenshot(path=str(shot))
            ev.popup_screenshot_path = _rel(shot, run_dir)
            ev.interactions["popup"] = "shown"
            try:
                page.keyboard.press("Escape")
            except PWError:
                pass
            for sel in _CLOSE_SELECTORS:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    try:
                        btn.click(timeout=1000)
                    except PWError:
                        pass
                    break
        else:
            ev.interactions["popup"] = "none"
    except PWError:
        ev.interactions["popup"] = "error"


def _interact_add_to_cart(page, pdir: Path, run_dir: Path, ev: "PageEvidence") -> None:
    """Click add-to-cart on a PDP and capture the resulting cart drawer/page — the
    surface where cross-sell / free-shipping bars actually live. Harmless (no order
    is placed). Records tri-state status so the reasoner can tell verified-absent
    from never-observed."""
    try:
        clicked = False
        for sel in _ATC_SELECTORS:
            el = page.query_selector(sel)
            if el and el.is_visible():
                try:
                    el.click(timeout=2000)
                    clicked = True
                    break
                except PWError:
                    continue
        if not clicked:
            ev.interactions["add_to_cart"] = "no_button"
            return
        page.wait_for_timeout(1800)  # let the drawer animate / cart navigate
        shot = pdir / "drawer.png"
        page.screenshot(path=str(shot), full_page=True)
        ev.drawer_screenshot_path = _rel(shot, run_dir)
        html_file = pdir / "drawer.html"
        html_file.write_text(page.content(), encoding="utf-8")
        ev.drawer_html_path = _rel(html_file, run_dir)
        ev.interactions["add_to_cart"] = "ok"
    except (PWError, OSError):
        ev.interactions["add_to_cart"] = "error"


def _launch(pw, headless: bool, *, proxy: Optional[str] = None, stealth: bool = True):
    """Launch browser + desktop/mobile contexts. Raises on failure (caller handles)."""
    launch_kwargs: dict = {"headless": headless}
    if stealth:
        launch_kwargs["args"] = _STEALTH_ARGS
    if proxy:
        launch_kwargs["proxy"] = {"server": proxy}
    browser = pw.chromium.launch(**launch_kwargs)

    common = dict(ignore_https_errors=True, locale="en-US", timezone_id="America/New_York")
    desktop = browser.new_context(viewport=DESKTOP_VIEWPORT, user_agent=UA_DESKTOP, **common)
    mobile = browser.new_context(
        viewport=MOBILE_VIEWPORT, user_agent=UA_MOBILE, is_mobile=True,
        has_touch=True, device_scale_factor=2, **common,
    )
    if stealth:
        desktop.add_init_script(_STEALTH_INIT)
        mobile.add_init_script(_STEALTH_INIT)
    return browser, desktop, mobile


def _capture_one(desktop_ctx, mobile_ctx, surface: Surface, order: int, run_dir: Path,
                 pages_dir: Path, timeout_ms: int, settle_ms: int) -> PageEvidence:
    name = f"{order:02d}_{surface.category}_{slugify(surface.url)}"
    pdir = pages_dir / name
    pdir.mkdir(parents=True, exist_ok=True)
    ev = PageEvidence(order=order, url=surface.url, category=surface.category, dir=_rel(pdir, run_dir))

    # --- desktop: navigation + HTML + meta + screenshot ---
    # NOTE: new_page() is intentionally unguarded so a browser crash propagates
    # to capture_surfaces(), which relaunches and retries this page (D9 fix #1).
    page = desktop_ctx.new_page()
    t0 = time.monotonic()
    resp, err = _navigate(page, surface.url, timeout_ms, settle_ms)
    ev.load_ms = int((time.monotonic() - t0) * 1000)
    if resp is not None:
        ev.status = resp.status
        ev.final_url = page.url
    if err:
        ev.error = err

    # Popup BEFORE the clean screenshot (captures it, then dismisses it) — Fix B4
    _handle_popup(page, pdir, run_dir, ev)

    try:
        html = page.content()
        html_file = pdir / "page.html"
        html_file.write_text(html, encoding="utf-8")
        ev.html_path = _rel(html_file, run_dir)

        meta = extract_meta(html)
        ev.title = meta["title"]
        ev.meta_description = meta["meta_description"]
        ev.canonical = meta["canonical"]
        ev.h1s = meta["h1s"]
        ev.og = meta["og"]
        ev.jsonld_types = meta["jsonld_types"]
        ev.has_favicon = meta["has_favicon"]
        ev.blocked = detect_block(html)

        meta_file = pdir / "meta.json"
        meta_file.write_text(
            json.dumps({"url": surface.url, "final_url": ev.final_url, "status": ev.status, **meta},
                       indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        ev.meta_path = _rel(meta_file, run_dir)
    except (PWError, OSError) as exc:
        ev.error = ev.error or type(exc).__name__

    try:
        shot = pdir / "screenshot.png"
        page.screenshot(path=str(shot), full_page=True)
        ev.screenshot_path = _rel(shot, run_dir)
    except (PWError, OSError):
        pass

    # Add-to-cart -> cart drawer, PDPs only (after the clean screenshot) — Fix B1
    if surface.category == "product":
        _interact_add_to_cart(page, pdir, run_dir, ev)

    _safe_close(page)

    # --- mobile: screenshot only (isolated; failure never affects desktop) ---
    try:
        mpage = mobile_ctx.new_page()
        _navigate(mpage, surface.url, timeout_ms, settle_ms)
        mshot = pdir / "screenshot-mobile.png"
        mpage.screenshot(path=str(mshot), full_page=True)
        ev.screenshot_mobile_path = _rel(mshot, run_dir)
        _safe_close(mpage)
    except (PWError, OSError):
        pass

    return ev


def capture_surfaces(surfaces: list[Surface], run_dir: Path, *, timeout: int = 30,
                     crawl_delay: float = 0.0, headless: bool = True,
                     settle_ms: int = 1500, proxy: Optional[str] = None,
                     stealth: bool = True) -> list[PageEvidence]:
    """Capture all surfaces. Always returns one PageEvidence per surface (in order),
    even if the browser fails to launch or crashes mid-run."""
    run_dir = Path(run_dir)
    pages_dir = run_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    timeout_ms = timeout * 1000
    evidence: list[PageEvidence] = []

    with sync_playwright() as pw:
        try:
            browser, desktop_ctx, mobile_ctx = _launch(pw, headless, proxy=proxy, stealth=stealth)
        except (PWError, Exception) as exc:  # browser won't even start
            reason = f"browser_launch:{type(exc).__name__}"
            return [PageEvidence(order=i, url=s.url, category=s.category, error=reason)
                    for i, s in enumerate(surfaces)]

        try:
            for order, surface in enumerate(surfaces):
                try:
                    ev = _capture_one(desktop_ctx, mobile_ctx, surface, order, run_dir,
                                      pages_dir, timeout_ms, settle_ms)
                except PWError:
                    # likely a browser/context crash — relaunch once and retry this page
                    _safe_close(browser)
                    try:
                        browser, desktop_ctx, mobile_ctx = _launch(pw, headless, proxy=proxy, stealth=stealth)
                        ev = _capture_one(desktop_ctx, mobile_ctx, surface, order, run_dir,
                                          pages_dir, timeout_ms, settle_ms)
                    except (PWError, Exception) as exc2:
                        ev = PageEvidence(order=order, url=surface.url, category=surface.category,
                                          error=f"crash:{type(exc2).__name__}")
                evidence.append(ev)
                if crawl_delay:
                    time.sleep(crawl_delay)
        finally:
            _safe_close(browser)

    return evidence


def render_homepage_links(url: str, *, timeout: int = 30, headless: bool = True,
                          settle_ms: int = 2500, proxy: Optional[str] = None,
                          stealth: bool = True) -> tuple[str, set[str], Optional[int]]:
    """Browser-fallback discovery + stealth gate-escalation (D9 #4 / D22).

    Renders the homepage with a real (stealth) browser and extracts links. Used when
    httpx BFS comes back near-empty (JS-rendered storefront) OR when the httpx
    pre-flight gate was challenged (Cloudflare) and we re-probe with the browser.
    Returns (html, links, status).
    """
    html, links, status = "", set(), None
    with sync_playwright() as pw:
        try:
            browser, desktop_ctx, _mobile = _launch(pw, headless, proxy=proxy, stealth=stealth)
        except (PWError, Exception):
            return html, links, status
        try:
            page = desktop_ctx.new_page()
            resp, _ = _navigate(page, url, timeout * 1000, settle_ms)
            if resp is not None:
                status = resp.status
            html = page.content()
            links = extract_links(html, page.url)
        except (PWError, OSError):
            pass
        finally:
            _safe_close(browser)
    return html, links, status
