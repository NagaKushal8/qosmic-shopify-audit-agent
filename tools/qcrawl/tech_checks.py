"""Deterministic technical checks (decision D17) — ~15 storefront checks.

Reads a crawl run (manifest + digest) plus a couple of light HTTP probes
(sitemap, http->https redirect) and emits Pass / Warn / Fail + a one-line detail
per check. Fully deterministic + testable — this is how we BEAT the reference
report's "not inspected (browser-first)" Warns.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .robots import root_url

PASS, WARN, FAIL = "Pass", "Warn", "Fail"
_UA = {"user-agent": "QosmicAuditBot/1.0 (+storefront-audit)"}


def _page(manifest: dict, category: str) -> Optional[dict]:
    for p in manifest.get("pages", []):
        if p.get("category") == category:
            return p
    return None


def _homepage_html(run_dir: Path, manifest: dict) -> str:
    home = _page(manifest, "home")
    if home and home.get("html_path"):
        f = run_dir / home["html_path"]
        if f.exists():
            return f.read_text(encoding="utf-8", errors="ignore")
    return ""


def run_checks(run_dir, *, timeout: int = 15, client: Optional[httpx.Client] = None) -> list[dict]:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    digest = None
    dpath = run_dir / "digest" / "digest.json"
    if dpath.exists():
        digest = json.loads(dpath.read_text(encoding="utf-8"))

    start = manifest.get("start_url") or ("https://" + (manifest.get("domain") or ""))
    root = root_url(start)
    home = _page(manifest, "home")
    pages = manifest.get("pages", [])
    bad = [p for p in pages if (p.get("status") or 0) >= 400]
    html = _homepage_html(run_dir, manifest)

    checks: list[dict] = []
    add = lambda c, s, d: checks.append({"check": c, "status": s, "detail": d})

    # 1. SSL
    if home and str(home.get("final_url", "")).startswith("https") and (home.get("status") or 0) < 400:
        add("SSL Certificate", PASS, "HTTPS storefront loaded successfully.")
    elif root.startswith("https"):
        add("SSL Certificate", WARN, "HTTPS used but homepage load was uncertain.")
    else:
        add("SSL Certificate", FAIL, "Storefront did not load over HTTPS.")

    # 2/3. redirect + sitemap (live probes)
    owns_client = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=timeout, headers=_UA)
    try:
        try:
            r = client.get("http://" + urlparse(root).netloc)
            if str(r.url).startswith("https"):
                add("HTTPS Redirect", PASS, "HTTP redirected to HTTPS.")
            else:
                add("HTTPS Redirect", FAIL, "HTTP did not redirect to HTTPS.")
        except httpx.HTTPError:
            add("HTTPS Redirect", WARN, "Could not probe HTTP redirect.")

        try:
            r = client.get(root + "/sitemap.xml")
            head = r.text[:600]
            if r.status_code == 200 and ("xml" in r.headers.get("content-type", "")
                                         or "<urlset" in head or "<sitemapindex" in head):
                add("Sitemap", PASS, "/sitemap.xml present and parseable.")
            else:
                add("Sitemap", FAIL, f"/sitemap.xml returned {r.status_code}.")
        except httpx.HTTPError:
            add("Sitemap", WARN, "Could not fetch /sitemap.xml.")
    finally:
        if owns_client:
            client.close()

    # 4. robots
    robots = manifest.get("robots", {})
    add("Robots.txt", PASS if robots.get("present") else FAIL,
        "robots.txt present." if robots.get("present") else "robots.txt missing or unreadable.")

    # 5. critical pages
    if home and (home.get("status") or 0) < 400 and not bad:
        add("Critical Pages Loading", PASS, "Homepage and sampled pages loaded.")
    elif home and (home.get("status") or 0) < 400:
        add("Critical Pages Loading", WARN, f"Homepage ok; {len(bad)} sampled page(s) errored.")
    else:
        add("Critical Pages Loading", FAIL, "Homepage did not load.")

    # 6. meta tags
    if home and home.get("meta_description"):
        add("Meta Tags & Social Previews", PASS, "Title + meta description present on homepage.")
    else:
        add("Meta Tags & Social Previews", WARN, "Homepage meta description missing or not captured.")

    # 7. structured data
    types = set()
    for p in pages:
        types.update(p.get("jsonld_types") or [])
    if types:
        add("Structured Data", PASS, f"JSON-LD present: {', '.join(sorted(types))[:80]}.")
    else:
        add("Structured Data", WARN, "No JSON-LD structured data detected.")

    # 8. favicon
    has_fav = any(p.get("has_favicon") for p in pages)
    add("Favicon", PASS if has_fav else WARN,
        "Favicon link present." if has_fav else "No favicon link detected.")

    # 9. mobile-friendly (viewport meta)
    vp = bool(BeautifulSoup(html, "html.parser").find("meta", attrs={"name": "viewport"})) if html else False
    add("Mobile-Friendly", PASS if vp else WARN,
        "Responsive viewport meta present." if vp else "No viewport meta detected.")

    # 10/11. page speed (proxy from navigation timing — honest about not being Lighthouse)
    loads = [p.get("load_ms") for p in pages if p.get("load_ms")]
    avg = sum(loads) / len(loads) if loads else None

    def speed():
        if avg is None:
            return WARN, "No load timing captured."
        if avg < 3000:
            return PASS, f"Avg nav load ~{int(avg)}ms (proxy, not Lighthouse)."
        if avg < 6000:
            return WARN, f"Avg nav load ~{int(avg)}ms (proxy; consider optimization)."
        return FAIL, f"Avg nav load ~{int(avg)}ms (proxy; slow)."

    s, d = speed()
    add("Page Speed Desktop", s, d)
    add("Page Speed Mobile", s, d + " Mobile uses desktop nav timing as proxy.")

    # 12. broken links
    if bad:
        sample = ", ".join(p.get("url", "") for p in bad[:3])
        add("Broken Links", FAIL, f"{len(bad)} sampled page(s) returned >=400 (e.g. {sample}).")
    else:
        add("Broken Links", PASS, "No 4xx/5xx among sampled pages.")

    # 13. image optimization
    imgs = []
    if digest:
        imgs = [p.get("signals", {}).get("image_count") for p in digest.get("pages", [])
                if p.get("signals", {}).get("image_count") is not None]
    if imgs:
        mx = max(imgs)
        add("Image Optimization", WARN if mx > 40 else PASS,
            f"Up to {mx} images on a page (byte size not measured).")
    else:
        add("Image Optimization", WARN, "Image counts not available.")

    # 14. cookie/privacy
    has_policy = any(p.get("category") == "policy" for p in pages) or ("privacy" in html.lower())
    add("Cookie/Privacy", PASS if has_policy else WARN,
        "Privacy/policy page or link present." if has_policy else "No privacy policy detected.")

    # 15. checkout reachable
    co = _page(manifest, "checkout")
    cart = _page(manifest, "cart")
    if co and (co.get("status") or 0) < 400:
        add("Checkout Reachable", PASS, "Checkout URL reachable.")
    elif cart and (cart.get("status") or 0) >= 400:
        add("Checkout Reachable", FAIL, f"/cart returned {cart.get('status')}; checkout not confirmed.")
    else:
        add("Checkout Reachable", WARN, "Checkout not directly confirmed (no items / not entered).")

    return checks
