"""Tests for qcrawl.tech_checks — deterministic checks from a fake run."""
import json

import httpx
import respx

from qcrawl.tech_checks import run_checks


def _seed_run(run_dir, *, cart_status=404, checkout_status=404):
    manifest = {
        "start_url": "https://store.com",
        "domain": "store.com",
        "robots": {"present": True},
        "pages": [
            {"category": "home", "url": "https://store.com/", "status": 200,
             "final_url": "https://store.com/", "load_ms": 1200,
             "meta_description": "Best store", "jsonld_types": ["Product"],
             "has_favicon": True},
            {"category": "product", "url": "https://store.com/products/x", "status": 200,
             "final_url": "https://store.com/products/x", "load_ms": 1500,
             "jsonld_types": ["Product"], "has_favicon": True},
            {"category": "cart", "url": "https://store.com/cart", "status": cart_status,
             "load_ms": 300},
            {"category": "checkout", "url": "https://store.com/checkout", "status": checkout_status},
        ],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _status(checks, name):
    return next(c["status"] for c in checks if c["check"] == name)


@respx.mock
def test_checks_flag_cart_404_and_pass_ssl():
    respx.get("http://store.com").mock(return_value=httpx.Response(301, headers={"location": "https://store.com"}))
    respx.get("https://store.com").mock(return_value=httpx.Response(200, text="ok"))
    respx.get("https://store.com/sitemap.xml").mock(
        return_value=httpx.Response(200, text="<urlset></urlset>", headers={"content-type": "application/xml"})
    )

    import tempfile, pathlib
    run_dir = pathlib.Path(tempfile.mkdtemp())
    _seed_run(run_dir)
    checks = run_checks(run_dir)

    assert _status(checks, "SSL Certificate") == "Pass"
    assert _status(checks, "Robots.txt") == "Pass"
    assert _status(checks, "Sitemap") == "Pass"
    assert _status(checks, "HTTPS Redirect") == "Pass"
    assert _status(checks, "Broken Links") == "Fail"          # cart + checkout 404
    assert _status(checks, "Checkout Reachable") == "Fail"
    assert _status(checks, "Structured Data") == "Pass"
    assert len(checks) >= 14  # ~15 checks emitted


@respx.mock
def test_checks_pass_when_cart_ok():
    respx.get("http://store.com").mock(return_value=httpx.Response(301, headers={"location": "https://store.com"}))
    respx.get("https://store.com").mock(return_value=httpx.Response(200, text="ok"))
    respx.get("https://store.com/sitemap.xml").mock(return_value=httpx.Response(404))

    import tempfile, pathlib
    run_dir = pathlib.Path(tempfile.mkdtemp())
    _seed_run(run_dir, cart_status=200, checkout_status=200)
    checks = run_checks(run_dir)

    assert _status(checks, "Broken Links") == "Pass"
    assert _status(checks, "Checkout Reachable") == "Pass"
    assert _status(checks, "Sitemap") == "Fail"   # 404 sitemap
