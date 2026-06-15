"""Tests for qcrawl.synth — domain verify + structured validators."""
import httpx
import respx

from qcrawl.synth import validate_competitors, validate_summary, verify_domains


@respx.mock
def test_verify_domains_flags_resolution():
    respx.get("https://real.com").mock(return_value=httpx.Response(200))
    respx.get("https://fake.invalid").mock(side_effect=httpx.ConnectError("nope"))
    out = verify_domains([{"domain": "real.com"}, {"domain": "fake.invalid"}])
    assert out[0]["domain_resolves"] is True
    assert out[1]["domain_resolves"] is False


def test_validate_summary_ok():
    summary = {"status": "ok", "thesis_title": "t",
               "paragraphs": [{"claim": "a", "body": "b"}, {"claim": "c", "body": "d"}]}
    assert validate_summary(summary) == []


def test_validate_summary_wrong_paragraph_count():
    summary = {"status": "ok", "thesis_title": "t", "paragraphs": [{"claim": "a", "body": "b"}]}
    assert any("2-3 paragraphs" in e for e in validate_summary(summary))


def test_validate_summary_unavailable_needs_note():
    assert any("note" in e for e in validate_summary({"status": "unavailable"}))
    assert validate_summary({"status": "unavailable", "note": "honest reason"}) == []


def _comp(**kw):
    base = {"competitor": "C", "domain": "c.com", "positioning": "p",
            "what_they_make_easier": "w", "store_edge": "e", "pattern_to_adapt": "a",
            "domain_resolves": True}
    base.update(kw)
    return base


def test_validate_competitors_ok():
    comp = {"status": "ok", "competitors": [_comp(), _comp(), _comp()]}
    assert validate_competitors(comp) == []


def test_validate_competitors_rejects_dead_domain():
    comp = {"status": "ok", "competitors": [_comp(), _comp(), _comp(domain_resolves=False)]}
    assert any("does not resolve" in e for e in validate_competitors(comp))


def test_validate_competitors_unavailable_is_valid_with_note():
    assert validate_competitors({"status": "unavailable", "note": "no web search"}) == []
