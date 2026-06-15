"""Deterministic digest builder (decisions D12 + D14).

Reads a crawl run's raw evidence (READ-ONLY) and writes a derived `digest/` folder:
  - `digest.json`      — per-page CRO signals + routed pillars (authoritative)
  - `<pillar>.md`      — per-pillar routing index handed to each pillar agent
  - `summary.md`       — store-level facts

It NEVER mutates raw evidence. CRO signals are extracted with generic, defensive
heuristics (no store-specific shortcuts) so they generalize across Shopify stores.
Signals are hints, not gospel — the pillar agent confirms against the screenshot
and may pull `page.html` on demand.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from .pillars import PILLARS, pillar_slug, pillars_for

_PRICE_RE = re.compile(r"[$£€¥₹]\s?\d[\d.,]*")
_REVIEW_COUNT_RE = re.compile(r"(\d[\d,]*)\s+reviews?", re.I)
_CTA_WORDS = (
    "add to cart", "add to bag", "add to basket", "buy now", "shop now",
    "subscribe", "sign up", "get started", "checkout", "order now", "find a store",
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


# --------------------------- signal detectors ------------------------------
# Each is defensive (never raises) and returns a plain bool/int/None.

def has_price(soup: BeautifulSoup) -> bool:
    if soup.select_one('[class*="price" i], [id*="price" i], [itemprop="price"], [data-price]'):
        return True
    return bool(_PRICE_RE.search(soup.get_text(" ")))


def has_add_to_cart(soup: BeautifulSoup) -> bool:
    if soup.select_one('form[action*="/cart/add"], button[name="add"], [name="add"], '
                        '[class*="add-to-cart" i], [id*="AddToCart" i]'):
        return True
    text = soup.get_text(" ").lower()
    return any(k in text for k in ("add to cart", "add to bag", "add to basket", "buy now"))


def reviews(soup: BeautifulSoup) -> tuple[bool, Optional[int]]:
    present = bool(soup.select_one('[class*="review" i], [class*="rating" i], [class*="stars" i], '
                                   '[data-reviews], [itemprop="aggregateRating"]'))
    text = soup.get_text(" ")
    if "review" in text.lower():
        present = True
    m = _REVIEW_COUNT_RE.search(text)
    count = int(m.group(1).replace(",", "")) if m else None
    return present, count


def has_variant_selector(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one(
        'select[name*="variant" i], select[name*="id" i] option, [name*="options" i], '
        '[data-variant], input[type="radio"][name*="option" i], .swatch, [class*="swatch" i], '
        '[class*="variant" i]'
    ))


def has_quantity(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one('[name="quantity"], input[name*="quantity" i], [class*="quantity" i]'))


def cta_count(soup: BeautifulSoup) -> int:
    n = 0
    for el in soup.find_all(["a", "button", "input"]):
        label = (el.get_text(" ") or el.get("value", "") or "").strip().lower()
        if label and any(w in label for w in _CTA_WORDS):
            n += 1
    return n


def has_email_capture(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one(
        'input[type="email"], [class*="newsletter" i], [id*="newsletter" i], '
        '[class*="subscribe" i], [class*="signup" i]'
    ))


def is_empty_cart(soup: BeautifulSoup, status: Optional[int]) -> Optional[bool]:
    if status and status >= 400:
        return None
    text = soup.get_text(" ").lower()
    if any(k in text for k in ("cart is empty", "your cart is empty", "no items in your cart")):
        return True
    return False


def has_checkout_button(soup: BeautifulSoup) -> bool:
    if soup.select_one('[name="checkout"], [href*="/checkout"], [class*="checkout" i]'):
        return True
    return "checkout" in soup.get_text(" ").lower()


_CROSS_SELL_TEXT = ("you may also like", "frequently bought", "complete the", "pairs well",
                    "goes well with", "customers also", "recommended for you", "you might also")


def has_cross_sell(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ").lower()
    if any(k in text for k in _CROSS_SELL_TEXT):
        return True
    return bool(soup.select_one('[class*="cross-sell" i], [class*="upsell" i], '
                                '[class*="recommend" i], [class*="related" i]'))


def has_free_shipping_bar(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ").lower()
    if "free shipping" in text and any(k in text for k in
                                       ("away", "more to", "spend", "left", "unlock", "qualify", "to get")):
        return True
    return bool(soup.select_one('[class*="free-ship" i], [class*="shipping-bar" i], '
                                '[class*="ship-progress" i]'))


def product_tile_count(soup: BeautifulSoup) -> int:
    return len({a.get("href") for a in soup.select('a[href*="/products/"]') if a.get("href")})


def has_filters_or_sort(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one('[class*="filter" i], [class*="facet" i], select[name*="sort" i], '
                                '[class*="sort" i]'))


def nav_link_count(soup: BeautifulSoup) -> int:
    nav = soup.find("nav") or soup.find("header")
    return len(nav.find_all("a")) if nav else 0


def image_count(soup: BeautifulSoup) -> int:
    return len(soup.find_all("img"))


def word_count(soup: BeautifulSoup) -> int:
    return len(soup.get_text(" ").split())


# --------------------------- per-category signals --------------------------

def extract_signals(category: str, html: str, status: Optional[int]) -> dict:
    """Generic + category-specific CRO signals for one page."""
    soup = _soup(html)
    sig: dict = {
        "cta_count": cta_count(soup),
        "email_capture": has_email_capture(soup),
        "image_count": image_count(soup),
        "word_count": word_count(soup),
        "nav_links": nav_link_count(soup),
    }
    if category == "product":
        present, count = reviews(soup)
        sig.update({
            "price_present": has_price(soup),
            "add_to_cart_present": has_add_to_cart(soup),
            "reviews_present": present,
            "review_count": count,
            "variant_selector": has_variant_selector(soup),
            "quantity_selector": has_quantity(soup),
        })
    elif category in ("cart", "checkout"):
        sig.update({
            "empty_cart": is_empty_cart(soup, status),
            "checkout_button": has_checkout_button(soup),
            "add_to_cart_present": has_add_to_cart(soup),
            # verified from the cart page we actually loaded
            "cross_sell": "present" if has_cross_sell(soup) else "absent",
            "free_shipping_bar": "present" if has_free_shipping_bar(soup) else "absent",
        })
    elif category == "collection":
        sig.update({
            "product_tiles": product_tile_count(soup),
            "filters_or_sort": has_filters_or_sort(soup),
            "price_present": has_price(soup),
        })
    elif category == "home":
        sig.update({
            "product_links": product_tile_count(soup),
            "has_hero_cta": cta_count(soup) > 0,
        })
    return sig


def one_line(category: str, title: Optional[str], status: Optional[int], sig: dict) -> str:
    """A compact, signal-rich summary line for the routing index."""
    t = (title or "(no title)")[:60]
    base = f"[{status}] {category}: {t}"
    if category == "product":
        return (f"{base} — price {'✓' if sig.get('price_present') else '✗'}, "
                f"add-to-cart {'✓' if sig.get('add_to_cart_present') else '✗'}, "
                f"reviews {sig.get('review_count') or ('✓' if sig.get('reviews_present') else '✗')}, "
                f"variants {'✓' if sig.get('variant_selector') else '✗'}")
    if category in ("cart", "checkout"):
        empty = sig.get("empty_cart")
        return (f"{base} — empty {'?' if empty is None else ('✓' if empty else '✗')}, "
                f"checkout-btn {'✓' if sig.get('checkout_button') else '✗'}")
    if category == "collection":
        return (f"{base} — {sig.get('product_tiles', 0)} tiles, "
                f"filters {'✓' if sig.get('filters_or_sort') else '✗'}")
    if category == "home":
        return f"{base} — CTAs {sig.get('cta_count', 0)}, email-capture {'✓' if sig.get('email_capture') else '✗'}"
    return f"{base} — CTAs {sig.get('cta_count', 0)}, words {sig.get('word_count', 0)}"


# ------------------------------- builder -----------------------------------

def build_digest(run_dir: Path) -> dict:
    """Read a run's raw evidence and return the digest dict (no files written)."""
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))

    pages_out = []
    for page in manifest.get("pages", []):
        category = page.get("category", "other")
        status = page.get("status")
        html = ""
        if page.get("html_path"):
            html_file = run_dir / page["html_path"]
            if html_file.exists():
                html = html_file.read_text(encoding="utf-8", errors="ignore")
        sig = extract_signals(category, html, status)

        # Interaction-aware tri-state signals (Fix A / D21): present | absent | unverified.
        interactions = page.get("interactions") or {}
        if category == "product":
            drawer_html = ""
            if page.get("drawer_html_path"):
                df = run_dir / page["drawer_html_path"]
                if df.exists():
                    drawer_html = df.read_text(encoding="utf-8", errors="ignore")
            if drawer_html:
                dsoup = _soup(drawer_html)
                sig["cart_cross_sell"] = "present" if has_cross_sell(dsoup) else "absent"
                sig["cart_free_shipping_bar"] = "present" if has_free_shipping_bar(dsoup) else "absent"
            else:
                # never triggered add-to-cart -> we did NOT observe it (not 'absent')
                sig["cart_cross_sell"] = "unverified"
                sig["cart_free_shipping_bar"] = "unverified"
        popup = interactions.get("popup")
        sig["email_popup"] = ("present" if popup == "shown"
                              else "absent" if popup == "none" else "unverified")

        pillars = pillars_for(category)
        pages_out.append({
            "order": page.get("order"),
            "url": page.get("url"),
            "final_url": page.get("final_url"),
            "category": category,
            "status": status,
            "pillars": pillars,
            "title": page.get("title"),
            "meta_description": page.get("meta_description"),
            "jsonld_types": page.get("jsonld_types", []),
            "load_ms": page.get("load_ms"),
            "blocked": page.get("blocked"),
            "signals": sig,
            "one_line": one_line(category, page.get("title"), status, sig),
            "screenshot": page.get("screenshot_path"),
            "screenshot_mobile": page.get("screenshot_mobile_path"),
            "drawer_screenshot": page.get("drawer_screenshot_path"),
            "popup_screenshot": page.get("popup_screenshot_path"),
            "interactions": interactions,
            "html_path": page.get("html_path"),   # for on-demand pull
            "drawer_html_path": page.get("drawer_html_path"),
            "meta_path": page.get("meta_path"),
        })

    return {
        "domain": manifest.get("domain"),
        "run_dir": manifest.get("run_dir"),
        "status": manifest.get("status"),
        "blocked_reason": manifest.get("blocked_reason"),
        "robots": manifest.get("robots"),
        "discovery": manifest.get("discovery"),
        "pages": pages_out,
    }


def _pillar_index_md(pillar: str, digest: dict) -> str:
    rows = [p for p in digest["pages"] if pillar in p["pillars"]]
    lines = [
        f"# {pillar} — routed evidence ({digest.get('domain')})",
        "",
        f"_Run: {digest.get('run_dir')} · status: {digest.get('status')} · "
        f"{len(rows)} pages routed to {pillar}._",
        "",
        "Pull `html_path` only if you need detail beyond the screenshot + signals.",
        "",
    ]
    for p in rows:
        lines.append(f"## {p['one_line']}")
        lines.append(f"- url: {p['url']}")
        lines.append(f"- screenshot: `{p['screenshot']}`")
        if p.get("drawer_screenshot"):
            lines.append(f"- cart drawer (post add-to-cart): `{p['drawer_screenshot']}`")
        if p.get("popup_screenshot"):
            lines.append(f"- popup/modal: `{p['popup_screenshot']}`")
        lines.append(f"- html (on demand): `{p['html_path']}`")
        lines.append(f"- signals: `{json.dumps(p['signals'], ensure_ascii=False)}`")
        lines.append("  (tri-state signals: present | absent | **unverified** = not observed, do NOT treat as absent)")
        lines.append("")
    return "\n".join(lines)


def _summary_md(digest: dict) -> str:
    from collections import Counter
    cats = Counter(p["category"] for p in digest["pages"])
    lines = [
        f"# Store summary — {digest.get('domain')}",
        "",
        f"- run: {digest.get('run_dir')}",
        f"- status: {digest.get('status')}"
        + (f" ({digest.get('blocked_reason')})" if digest.get("blocked_reason") else ""),
        f"- pages captured: {len(digest['pages'])}",
        f"- by category: {dict(cats)}",
        f"- robots: {digest.get('robots')}",
        "",
        "## Pages",
    ]
    for p in sorted(digest["pages"], key=lambda x: x.get("order") or 0):
        lines.append(f"- {p['one_line']}  → pillars: {', '.join(p['pillars'])}")
    return "\n".join(lines)


def write_digest(digest: dict, run_dir: Path) -> Path:
    """Write digest.json + per-pillar indexes + summary into run_dir/digest/."""
    out = Path(run_dir) / "digest"
    out.mkdir(parents=True, exist_ok=True)
    (out / "digest.json").write_text(json.dumps(digest, indent=2, ensure_ascii=False), encoding="utf-8")
    for pillar in PILLARS:
        (out / f"{pillar_slug(pillar)}.md").write_text(_pillar_index_md(pillar, digest), encoding="utf-8")
    (out / "summary.md").write_text(_summary_md(digest), encoding="utf-8")
    return out
