"""BFS surface discovery — decision **D6 (BFS-only, no sitemap dependency)**.

Seeds the frontier with the homepage + known functional routes, then walks
same-host links breadth-first, bounded by depth + a fetch cap, throttled by an
optional crawl-delay. Discovery uses httpx (fast, no rendering); the later
capture phase uses Playwright only on the *sampled* surfaces. Every per-node
failure is recorded on the Surface and never aborts the crawl (partial success
is success).
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Functional routes seeded on top of the homepage (decision D6). Several of these
# aren't linked in nav/footer yet are CRO-critical (e.g. the /cart 404 finding).
FUNCTIONAL_SEEDS = ["/", "/cart", "/checkout", "/search", "/collections/all", "/account/login"]

# Per-category sampling caps for the capture phase (backstop against huge stores).
DEFAULT_CAPS = {
    "home": 1, "cart": 1, "checkout": 1, "search": 1, "account": 1,
    "collection": 2, "product": 3, "page": 5, "blog": 2, "policy": 2, "other": 3,
}

# Priority for sampling order (lower = captured first).
_PRIORITY = {
    "home": 0, "cart": 1, "checkout": 1, "search": 1, "account": 1,
    "collection": 2, "product": 3, "page": 4, "blog": 5, "policy": 6, "other": 7,
}


@dataclass
class Surface:
    url: str
    category: str
    depth: int
    status: Optional[int] = None
    fetched: bool = False
    error: Optional[str] = None
    discovered_from: Optional[str] = None
    title: Optional[str] = None


def root_url(url: str) -> str:
    parsed = urlparse(url if "//" in url else "https://" + url)
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_host(host: str) -> str:
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_host(url: str, root_host: str) -> bool:
    try:
        netloc = urlparse(url).netloc
    except ValueError:
        return False
    return bool(netloc) and normalize_host(netloc) == normalize_host(root_host)


def categorize(url: str) -> str:
    """Map a URL to a Shopify surface category by path convention."""
    path = urlparse(url).path.rstrip("/")
    if path in ("", "/"):
        return "home"
    if "/products/" in path or path.endswith("/products"):
        return "product"
    if "/collections/" in path or path.endswith("/collections"):
        return "collection"
    if "/blogs/" in path:
        return "blog"
    if "/pages/" in path:
        return "page"
    if "/policies/" in path:
        return "policy"
    if path.startswith("/cart"):
        return "cart"
    if path.startswith("/checkout"):
        return "checkout"
    if path.startswith("/search"):
        return "search"
    if path.startswith("/account"):
        return "account"
    return "other"


def extract_links(html: str, base_url: str) -> set[str]:
    """All absolute, de-fragmented <a href> links on the page."""
    soup = BeautifulSoup(html, "html.parser")
    out: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute, _ = urldefrag(urljoin(base_url, href))
        out.add(absolute)
    return out


def _page_title(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def _get_with_retry(client: httpx.Client, url: str, *, retries: int = 1, backoff: float = 1.0):
    """GET with one retry on transient error / HTTP 429. Returns (response|None, err|None)."""
    last_err: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            resp = client.get(url)
            if resp.status_code == 429 and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return resp, None
        except httpx.HTTPError as exc:
            last_err = type(exc).__name__
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
    return None, last_err


def bfs_discover(
    start_url: str,
    client: httpx.Client,
    *,
    max_depth: int = 3,
    max_fetch: int = 40,
    crawl_delay: float = 0.0,
    seeds: Iterable[str] = FUNCTIONAL_SEEDS,
) -> list[Surface]:
    """Breadth-first, same-host surface discovery. Returns all surfaces seen."""
    root = root_url(start_url)
    root_host = urlparse(root).netloc

    surfaces: dict[str, Surface] = {}
    queue: deque[tuple[str, int, Optional[str]]] = deque()
    seen: set[str] = set()

    # Seed homepage + functional routes (still pure BFS, just better starts).
    for seed in seeds:
        url, _ = urldefrag(urljoin(root + "/", seed.lstrip("/")))
        if url not in seen:
            seen.add(url)
            queue.append((url, 0, None))

    fetched = 0
    while queue and fetched < max_fetch:
        url, depth, parent = queue.popleft()
        surface = surfaces.setdefault(
            url, Surface(url=url, category=categorize(url), depth=depth, discovered_from=parent)
        )
        resp, err = _get_with_retry(client, url)
        if resp is not None:
            surface.status = resp.status_code
            surface.fetched = True
            fetched += 1
            content_type = resp.headers.get("content-type", "")
            if resp.status_code < 400 and "html" in content_type:
                surface.title = _page_title(resp.text)
                if depth < max_depth:
                    for link in extract_links(resp.text, url):
                        if same_host(link, root_host) and link not in seen:
                            seen.add(link)
                            queue.append((link, depth + 1, url))
        else:
            surface.error = err

        if crawl_delay:
            time.sleep(crawl_delay)

    return list(surfaces.values())


def select_for_capture(surfaces: list[Surface], caps: Optional[dict] = None) -> list[Surface]:
    """Sample a representative, capped subset of surfaces for the capture phase.

    Prefers successfully fetched HTML pages, ordered by CRO priority then depth.
    """
    caps = caps or DEFAULT_CAPS
    ordered = sorted(
        surfaces,
        key=lambda s: (
            0 if (s.fetched and (s.status or 600) < 400) else 1,  # good pages first
            _PRIORITY.get(s.category, 9),
            s.depth,
        ),
    )
    chosen: list[Surface] = []
    counts: dict[str, int] = {}
    for surface in ordered:
        cap = caps.get(surface.category, 1)
        if counts.get(surface.category, 0) < cap:
            chosen.append(surface)
            counts[surface.category] = counts.get(surface.category, 0) + 1
    return chosen
