"""Tests for qcrawl.discovery — categorize, link extraction, BFS, sampling.

All network is mocked with respx, so these run offline + deterministically.
Covers the edge cases agreed in decision.md: off-host exclusion, error nodes,
seed inclusion, depth + fetch caps, and per-category sampling.
"""
import httpx
import pytest
import respx

from qcrawl.discovery import (
    DEFAULT_CAPS,
    bfs_discover,
    categorize,
    extract_links,
    normalize_host,
    same_host,
    select_for_capture,
)


# ----------------------------- pure helpers --------------------------------

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://s.com/", "home"),
        ("https://s.com", "home"),
        ("https://s.com/products/gin-gins", "product"),
        ("https://s.com/collections/all", "collection"),
        ("https://s.com/blogs/news/post", "blog"),
        ("https://s.com/pages/faq", "page"),
        ("https://s.com/policies/privacy-policy", "policy"),
        ("https://s.com/cart", "cart"),
        ("https://s.com/checkout", "checkout"),
        ("https://s.com/search?q=x", "search"),
        ("https://s.com/account/login", "account"),
        ("https://s.com/random", "other"),
    ],
)
def test_categorize(url, expected):
    assert categorize(url) == expected


def test_normalize_host_strips_www():
    assert normalize_host("www.Store.com") == "store.com"
    assert normalize_host("store.com") == "store.com"


def test_same_host_with_www_normalization():
    assert same_host("https://www.store.com/x", "store.com")
    assert same_host("https://store.com/x", "www.store.com")
    assert not same_host("https://cdn.shopify.com/x", "store.com")
    assert not same_host("https://other.com/x", "store.com")


def test_extract_links_absolutizes_and_filters():
    html = """
      <a href="/products/a">a</a>
      <a href="https://store.com/pages/faq">faq</a>
      <a href="mailto:x@y.com">mail</a>
      <a href="#section">anchor</a>
      <a href="https://twitter.com/store">social</a>
    """
    links = extract_links(html, "https://store.com/")
    assert "https://store.com/products/a" in links
    assert "https://store.com/pages/faq" in links
    assert "https://twitter.com/store" in links  # extracted; same-host filtering is BFS's job
    assert not any(l.startswith(("mailto:", "#")) for l in links)


# ------------------------------- BFS engine --------------------------------

def _html(*hrefs: str) -> str:
    body = "".join(f'<a href="{h}">x</a>' for h in hrefs)
    return f"<html><head><title>T</title></head><body>{body}</body></html>"


@respx.mock
def test_bfs_seeds_homepage_and_functional_routes():
    # Homepage links to one product; functional seeds resolve independently.
    respx.get("https://store.com/").mock(
        return_value=httpx.Response(200, html=_html("/products/a"), headers={"content-type": "text/html"})
    )
    respx.get("https://store.com/products/a").mock(
        return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"})
    )
    respx.get("https://store.com/cart").mock(return_value=httpx.Response(404, html="nope", headers={"content-type": "text/html"}))
    respx.get("https://store.com/checkout").mock(return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"}))
    respx.get("https://store.com/search").mock(return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"}))
    respx.get("https://store.com/collections/all").mock(return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"}))
    respx.get("https://store.com/account/login").mock(return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"}))

    with httpx.Client() as client:
        surfaces = bfs_discover("https://store.com", client)

    by_url = {s.url: s for s in surfaces}
    # functional seeds were visited even though unlinked
    assert "https://store.com/cart" in by_url
    assert by_url["https://store.com/cart"].status == 404  # the classic finding
    # homepage-discovered product was crawled
    assert "https://store.com/products/a" in by_url


@respx.mock
def test_bfs_excludes_offhost_links():
    respx.get("https://store.com/").mock(
        return_value=httpx.Response(200, html=_html("https://evil.com/x", "/pages/faq"),
                                    headers={"content-type": "text/html"})
    )
    respx.get("https://store.com/pages/faq").mock(
        return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"})
    )
    # functional seeds (avoid network errors in mock)
    for path in ("cart", "checkout", "search", "collections/all", "account/login"):
        respx.get(f"https://store.com/{path}").mock(
            return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"})
        )

    with httpx.Client() as client:
        surfaces = bfs_discover("https://store.com", client)

    urls = {s.url for s in surfaces}
    assert "https://store.com/pages/faq" in urls
    assert "https://evil.com/x" not in urls  # off-host never enqueued


@respx.mock
def test_bfs_records_node_errors_without_crashing():
    respx.get("https://store.com/").mock(side_effect=httpx.ConnectTimeout("slow"))
    for path in ("cart", "checkout", "search", "collections/all", "account/login"):
        respx.get(f"https://store.com/{path}").mock(
            return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"})
        )

    with httpx.Client() as client:
        surfaces = bfs_discover("https://store.com", client)

    home = next(s for s in surfaces if s.url == "https://store.com/")
    assert home.error == "ConnectTimeout"
    assert home.fetched is False
    # crawl still produced other surfaces
    assert any(s.fetched for s in surfaces)


@respx.mock
def test_bfs_respects_max_fetch_cap():
    # Homepage links to many products; cap fetches low.
    links = [f"/products/p{i}" for i in range(50)]
    respx.get("https://store.com/").mock(
        return_value=httpx.Response(200, html=_html(*links), headers={"content-type": "text/html"})
    )
    respx.route(host="store.com").mock(
        return_value=httpx.Response(200, html=_html(), headers={"content-type": "text/html"})
    )
    with httpx.Client() as client:
        surfaces = bfs_discover("https://store.com", client, max_fetch=5)
    assert sum(1 for s in surfaces if s.fetched) <= 5


def test_select_for_capture_enforces_per_category_caps():
    from qcrawl.discovery import Surface
    surfaces = [Surface(url=f"https://s.com/products/p{i}", category="product", depth=1,
                        status=200, fetched=True) for i in range(10)]
    surfaces.append(Surface(url="https://s.com/", category="home", depth=0, status=200, fetched=True))
    chosen = select_for_capture(surfaces)
    cats = [s.category for s in chosen]
    assert cats.count("product") == DEFAULT_CAPS["product"]
    assert cats.count("home") == 1


def test_select_prefers_successful_pages():
    from qcrawl.discovery import Surface
    good = Surface(url="https://s.com/products/ok", category="product", depth=1, status=200, fetched=True)
    bad = Surface(url="https://s.com/products/bad", category="product", depth=1, status=500, fetched=True)
    chosen = select_for_capture([bad, good], caps={"product": 1})
    assert chosen[0].url == good.url
