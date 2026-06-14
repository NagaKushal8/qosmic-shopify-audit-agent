"""Site health gate (decision D11) — decide early when a store isn't crawlable.

Two tiers:
  1. `probe_homepage` — pre-flight: is the homepage reachable, not a 5xx, not a
     (hard or soft) 404, not a password/Cloudflare gate? Retries transient failures.
  2. `assess_reachability` — post-discovery: if EVERY discovered page is an error
     page (>=400 or a "not found" body), the site is dead and capture is pointless.

Both let `crawl.py` abort early with an honest status instead of screenshotting a
folder full of 404s.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

import httpx
from bs4 import BeautifulSoup

# Signatures of "page not found" content (catches soft-404s that return HTTP 200).
NOT_FOUND_SIGNS = (
    "page not found", "not found", "couldn't find", "could not find",
    "page doesn't exist", "page does not exist", "404 error", "error 404",
)


def looks_not_found(text: str) -> bool:
    low = (text or "").lower()
    return any(sign in low for sign in NOT_FOUND_SIGNS)


def page_is_dead(status: Optional[int], title: Optional[str] = None) -> bool:
    """A page is 'dead' if it errored (>=400) or its title/headline says not-found."""
    if status is not None and status >= 400:
        return True
    return looks_not_found(title or "")


def _title_and_h1(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    title = soup.title.string if soup.title and soup.title.string else ""
    h1 = " ".join(h.get_text(" ", strip=True) for h in soup.find_all("h1")[:2])
    return f"{title} {h1}".strip()


@dataclass
class HealthResult:
    ok: bool
    reason: Optional[str] = None      # 'unreachable' | 'server_error' | 'not_found'
    status: Optional[int] = None
    blocked: Optional[str] = None     # 'password' | 'challenge' (gate, but reachable)
    html: str = ""


def probe_homepage(
    url: str,
    client: httpx.Client,
    *,
    retries: int = 2,
    backoff: float = 1.0,
    detect_block: Optional[Callable[[str], Optional[str]]] = None,
) -> HealthResult:
    """Pre-flight homepage health, retrying transient failures up to `retries`."""
    last_status: Optional[int] = None
    html = ""
    for attempt in range(retries + 1):
        try:
            resp = client.get(url)
        except httpx.HTTPError:
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return HealthResult(ok=False, reason="unreachable")

        last_status = resp.status_code
        html = resp.text

        # A password/CF gate IS reachable — report it as a block, not a death.
        blocked = detect_block(html) if detect_block else None
        if blocked:
            return HealthResult(ok=True, status=last_status, blocked=blocked, html=html)

        if last_status >= 500:
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return HealthResult(ok=False, reason="server_error", status=last_status, html=html)

        if page_is_dead(last_status, _title_and_h1(html)):
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return HealthResult(ok=False, reason="not_found", status=last_status, html=html)

        return HealthResult(ok=True, status=last_status, html=html)

    return HealthResult(ok=False, reason="unreachable", status=last_status, html=html)


def assess_reachability(surfaces) -> dict:
    """Post-discovery: are ANY discovered pages actually reachable?

    `dead=True` means we fetched pages but every one is an error/not-found page —
    no point capturing. Duck-typed on Surface (.fetched/.status/.title/.error).
    """
    fetched = [s for s in surfaces if getattr(s, "fetched", False)]
    reachable = [s for s in fetched if not page_is_dead(s.status, s.title)]
    errored = [s for s in surfaces if getattr(s, "error", None)]
    return {
        "fetched": len(fetched),
        "reachable": len(reachable),
        "errored": len(errored),
        "dead": len(fetched) > 0 and len(reachable) == 0,
    }
