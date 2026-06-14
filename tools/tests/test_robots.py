"""Tests for qcrawl.robots — parsing + fetch, polite-only semantics (D7)."""
import httpx
import pytest
import respx

from qcrawl.robots import RobotsInfo, fetch_robots, parse_robots, root_url

SHOPIFY_ROBOTS = """\
# we use Shopify
User-agent: *
Disallow: /cart
Disallow: /checkout
Disallow: /account
Disallow: /search
Crawl-delay: 5

Sitemap: https://store.example/sitemap.xml
"""


def test_parse_extracts_crawl_delay_and_sitemaps():
    parsed = parse_robots(SHOPIFY_ROBOTS)
    assert parsed["crawl_delay"] == 5.0
    assert parsed["sitemaps"] == ["https://store.example/sitemap.xml"]


def test_parse_records_disallows_but_they_are_not_enforced():
    # D7: disallows are captured for transparency, never used to gate the crawl.
    parsed = parse_robots(SHOPIFY_ROBOTS)
    assert "/cart" in parsed["disallows"]
    assert "/checkout" in parsed["disallows"]


def test_parse_prefers_specific_user_agent_then_falls_back_to_star():
    text = """\
User-agent: *
Crawl-delay: 1
User-agent: Qosmic
Crawl-delay: 9
"""
    assert parse_robots(text, user_agent="Qosmic")["crawl_delay"] == 9.0
    assert parse_robots(text, user_agent="Other")["crawl_delay"] == 1.0


def test_parse_handles_comments_and_blank_lines():
    parsed = parse_robots("# just a comment\n\n   \nUser-agent: *\nDisallow:\n")
    assert parsed["disallows"] == []  # empty Disallow means "allow all", not a rule


def test_root_url_normalizes_input():
    assert root_url("gingerpeople.com/products/x") == "https://gingerpeople.com"
    assert root_url("http://a.com/b") == "http://a.com"


@respx.mock
def test_fetch_robots_present():
    respx.get("https://store.example/robots.txt").mock(
        return_value=httpx.Response(200, text=SHOPIFY_ROBOTS)
    )
    with httpx.Client() as client:
        info = fetch_robots("https://store.example", client)
    assert info.present is True
    assert info.crawl_delay == 5.0
    assert info.sitemaps == ["https://store.example/sitemap.xml"]


@respx.mock
def test_fetch_robots_missing_returns_not_present():
    respx.get("https://store.example/robots.txt").mock(return_value=httpx.Response(404))
    with httpx.Client() as client:
        info = fetch_robots("https://store.example", client)
    assert info.present is False
    assert info.status_code == 404


@respx.mock
def test_fetch_robots_network_error_is_not_fatal():
    respx.get("https://store.example/robots.txt").mock(side_effect=httpx.ConnectError("boom"))
    with httpx.Client() as client:
        info = fetch_robots("https://store.example", client)
    assert info == RobotsInfo(present=False)
