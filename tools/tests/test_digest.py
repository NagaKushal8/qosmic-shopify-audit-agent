"""Tests for qcrawl.digest signal extraction + qcrawl.pillars routing."""
import pytest

import json

from qcrawl.digest import (
    build_digest,
    cta_count,
    extract_signals,
    has_add_to_cart,
    has_cross_sell,
    has_free_shipping_bar,
    has_price,
    is_empty_cart,
    one_line,
    product_tile_count,
    reviews,
)
from qcrawl.digest import _soup
from qcrawl.pillars import PILLARS, pillars_for

PDP_FULL = """
<html><body>
  <h1>GIN GINS Original</h1>
  <span class="price">$5.99</span>
  <form action="/cart/add"><button name="add">Add to cart</button>
  <select name="id"><option>4oz</option><option>8oz</option></select>
  <input name="quantity" value="1"></form>
  <div class="reviews">86 reviews</div>
</body></html>
"""

PDP_LEAKY = """
<html><body>
  <h1>GIN GINS Original</h1>
  <div class="reviews">86 reviews</div>
  <p>America's #1 selling ginger candy. Buy online or find it locally.</p>
</body></html>
"""


# ------------------------------- detectors ---------------------------------

def test_price_present_and_absent():
    assert has_price(_soup(PDP_FULL)) is True
    assert has_price(_soup(PDP_LEAKY)) is False


def test_add_to_cart_present_and_absent():
    assert has_add_to_cart(_soup(PDP_FULL)) is True
    assert has_add_to_cart(_soup(PDP_LEAKY)) is False


def test_reviews_count():
    present, count = reviews(_soup(PDP_FULL))
    assert present and count == 86


def test_empty_cart_detection():
    assert is_empty_cart(_soup("<p>Your cart is empty</p>"), 200) is True
    assert is_empty_cart(_soup("<p>1 item</p>"), 200) is False
    assert is_empty_cart(_soup(""), 404) is None  # can't tell on error


def test_product_tile_count_dedupes():
    html = '<a href="/products/a">a</a><a href="/products/a">a2</a><a href="/products/b">b</a>'
    assert product_tile_count(_soup(html)) == 2


def test_cta_count_counts_action_labels():
    html = '<a>Add to cart</a><button>Subscribe</button><a>About us</a>'
    assert cta_count(_soup(html)) == 2


# ----------------------------- extract_signals -----------------------------

def test_extract_signals_pdp_leaky_matches_reference_finding():
    sig = extract_signals("product", PDP_LEAKY, 200)
    # The classic gingerpeople leak: proof present, but no price / add-to-cart.
    assert sig["price_present"] is False
    assert sig["add_to_cart_present"] is False
    assert sig["reviews_present"] is True


def test_extract_signals_full_pdp():
    sig = extract_signals("product", PDP_FULL, 200)
    assert sig["price_present"] and sig["add_to_cart_present"]
    assert sig["variant_selector"] and sig["quantity_selector"]


def test_one_line_is_signal_rich():
    sig = extract_signals("product", PDP_LEAKY, 200)
    line = one_line("product", "GIN GINS Original", 200, sig)
    assert "price ✗" in line and "add-to-cart ✗" in line


# -------------------------------- routing ----------------------------------

@pytest.mark.parametrize("category,expected_subset", [
    ("product", {"Conversion", "AOV"}),
    ("cart", {"Conversion", "AOV", "Performance"}),
    ("account", {"Retention"}),
    ("blog", {"Acquisition", "Retention"}),
])
def test_pillars_for(category, expected_subset):
    assert set(pillars_for(category)) == expected_subset


def test_every_pillar_is_reachable_by_some_surface():
    covered = set()
    for cat in ["home", "product", "collection", "cart", "checkout", "search",
                "account", "policy", "blog", "page"]:
        covered.update(pillars_for(cat))
    assert covered == set(PILLARS)  # the preset map can route to all 5 pillars


# ------------------ interaction-aware tri-state signals (D21) ------------------

def test_cross_sell_and_free_shipping_detectors():
    assert has_cross_sell(_soup("<div>You may also like</div>"))
    assert has_cross_sell(_soup('<div class="product-recommendations"></div>'))
    assert not has_cross_sell(_soup("<div>About us</div>"))
    assert has_free_shipping_bar(_soup("<div>You're $12 away from free shipping</div>"))
    assert not has_free_shipping_bar(_soup("<div>Free returns</div>"))


def _write_run(tmp_path, page):
    (tmp_path / "manifest.json").write_text(
        json.dumps({"domain": "s.com", "pages": [page]}), encoding="utf-8")


def test_drawer_signals_unverified_when_no_interaction(tmp_path):
    _write_run(tmp_path, {"order": 0, "url": "https://s.com/products/x", "category": "product",
                          "status": 200, "interactions": {"add_to_cart": "no_button"}})
    d = build_digest(tmp_path)
    sig = d["pages"][0]["signals"]
    assert sig["cart_cross_sell"] == "unverified"      # NOT 'absent'
    assert sig["cart_free_shipping_bar"] == "unverified"


def test_drawer_signals_present_when_drawer_captured(tmp_path):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "drawer.html").write_text(
        "<div>You may also like</div><div>You're $10 away from free shipping</div>",
        encoding="utf-8")
    _write_run(tmp_path, {"order": 0, "url": "https://s.com/products/x", "category": "product",
                          "status": 200, "drawer_html_path": "pages/drawer.html",
                          "interactions": {"add_to_cart": "ok"}})
    d = build_digest(tmp_path)
    sig = d["pages"][0]["signals"]
    assert sig["cart_cross_sell"] == "present"
    assert sig["cart_free_shipping_bar"] == "present"


def test_email_popup_tri_state(tmp_path):
    _write_run(tmp_path, {"order": 0, "url": "https://s.com/", "category": "home",
                          "status": 200, "interactions": {"popup": "shown"}})
    assert build_digest(tmp_path)["pages"][0]["signals"]["email_popup"] == "present"
