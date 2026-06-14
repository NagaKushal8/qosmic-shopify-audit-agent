"""Tests for qcrawl.health — the dead-site / unreachable gate (D11).

All offline via respx. Covers: hard 404, soft 404 (200 + 'not found' body),
5xx, total connection failure, healthy site, password gate, and the
post-discovery all-dead assessment.
"""
from dataclasses import dataclass
from typing import Optional

import httpx
import pytest
import respx

from qcrawl.capture import detect_block
from qcrawl.health import (
    assess_reachability,
    looks_not_found,
    page_is_dead,
    probe_homepage,
)


# ------------------------------ pure helpers -------------------------------

def test_looks_not_found():
    assert looks_not_found("404 Page Not Found")
    assert looks_not_found("Sorry, we couldn't find that page")
    assert not looks_not_found("Welcome to our store")


@pytest.mark.parametrize(
    "status,title,dead",
    [
        (404, None, True),
        (410, None, True),
        (500, None, True),
        (200, "Page Not Found", True),    # soft 404
        (200, "Home | Store", False),
        (200, None, False),
    ],
)
def test_page_is_dead(status, title, dead):
    assert page_is_dead(status, title) is dead


# ----------------------------- probe_homepage ------------------------------

OK_HTML = "<html><head><title>Home | Store</title></head><body>Shop now</body></html>"
NOT_FOUND_HTML = "<html><head><title>404 Page Not Found</title></head><body>not found</body></html>"
PASSWORD_HTML = "<html><body>Enter store password to continue</body></html>"


@respx.mock
def test_probe_healthy_homepage():
    respx.get("https://store.com").mock(return_value=httpx.Response(200, html=OK_HTML))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0, detect_block=detect_block)
    assert res.ok and res.reason is None and res.status == 200


@respx.mock
def test_probe_hard_404_is_not_found():
    respx.get("https://store.com").mock(return_value=httpx.Response(404, html=NOT_FOUND_HTML))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0)
    assert not res.ok and res.reason == "not_found"


@respx.mock
def test_probe_soft_404_is_not_found():
    # HTTP 200 but the page says "not found" -> soft 404
    respx.get("https://store.com").mock(return_value=httpx.Response(200, html=NOT_FOUND_HTML))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0)
    assert not res.ok and res.reason == "not_found"


@respx.mock
def test_probe_5xx_is_server_error():
    respx.get("https://store.com").mock(return_value=httpx.Response(503, html="oops"))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0)
    assert not res.ok and res.reason == "server_error"


@respx.mock
def test_probe_connection_failure_is_unreachable():
    respx.get("https://store.com").mock(side_effect=httpx.ConnectError("down"))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0)
    assert not res.ok and res.reason == "unreachable"


@respx.mock
def test_probe_password_gate_is_reachable_but_blocked():
    respx.get("https://store.com").mock(return_value=httpx.Response(200, html=PASSWORD_HTML))
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=0, detect_block=detect_block)
    assert res.ok and res.blocked == "password"


@respx.mock
def test_probe_retries_then_recovers():
    route = respx.get("https://store.com")
    route.side_effect = [httpx.Response(503), httpx.Response(200, html=OK_HTML)]
    with httpx.Client() as client:
        res = probe_homepage("https://store.com", client, retries=2, backoff=0.0)
    assert res.ok and res.status == 200


# --------------------------- assess_reachability ---------------------------

@dataclass
class _S:
    status: Optional[int]
    title: Optional[str] = None
    fetched: bool = True
    error: Optional[str] = None


def test_assess_all_dead():
    surfaces = [_S(404), _S(404), _S(500)]
    out = assess_reachability(surfaces)
    assert out["dead"] is True and out["reachable"] == 0


def test_assess_some_reachable_is_not_dead():
    surfaces = [_S(404), _S(200, "Home"), _S(404)]
    out = assess_reachability(surfaces)
    assert out["dead"] is False and out["reachable"] == 1


def test_assess_no_fetches_is_not_dead_flag():
    # nothing fetched (all connection errors) -> not flagged 'dead' here;
    # the homepage gate handles 'unreachable' upstream.
    surfaces = [_S(None, fetched=False, error="ConnectError")]
    out = assess_reachability(surfaces)
    assert out["dead"] is False and out["fetched"] == 0
