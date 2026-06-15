"""Tests for qcrawl.experiments — schema + report-set budget guardrails."""
from qcrawl.experiments import (
    PILLARS,
    make_exp_id,
    select_experiments,
    validate_experiment,
    validate_report_set,
)


def _exp(pillar, title="t", url="https://s.com/p"):
    return {
        "exp_id": make_exp_id(title + pillar, url),
        "title": title,
        "pillar": pillar,
        "surface": "PDP",
        "url": url,
        "evidence": "pages/01_product_x/screenshot.png",
        "hypothesis": "h",
        "primary_change": "c",
        "primary_kpi": "k",
        "decision_rule": "ship if k improves",
        "expected_lift": "+5-10%",
        "confidence": 75,
    }


def _ten_balanced():
    # 2 per pillar = 10
    out = []
    for p in PILLARS:
        out.append(_exp(p, title=f"{p}-1"))
        out.append(_exp(p, title=f"{p}-2"))
    return out


def test_make_exp_id_stable_and_prefixed():
    a = make_exp_id("title", "https://s.com")
    b = make_exp_id("title", "https://s.com")
    assert a == b and a.startswith("exp-") and len(a) == 16


def test_valid_experiment_has_no_errors():
    assert validate_experiment(_exp("Conversion")) == []


def test_missing_field_flagged():
    e = _exp("Conversion")
    del e["hypothesis"]
    assert any("hypothesis" in err for err in validate_experiment(e))


def test_invalid_pillar_flagged():
    e = _exp("Conversion")
    e["pillar"] = "Growth"
    assert any("invalid pillar" in err for err in validate_experiment(e))


def test_confidence_out_of_range_flagged():
    e = _exp("Conversion")
    e["confidence"] = 140
    assert any("confidence out of range" in err for err in validate_experiment(e))


def test_bad_evidence_flagged():
    e = _exp("Conversion")
    e["evidence"] = "I saw it somewhere"
    assert any("evidence" in err for err in validate_experiment(e))


def test_valid_report_set_passes():
    res = validate_report_set(_ten_balanced())
    assert res["ok"] and all(n == 2 for n in res["by_pillar"].values())


def test_wrong_count_fails():
    res = validate_report_set(_ten_balanced()[:8])
    assert not res["ok"] and any("expected 10" in e for e in res["errors"])


def test_missing_pillar_fails():
    exps = _ten_balanced()
    # replace both Performance with Conversion -> Performance missing
    fixed = [e for e in exps if e["pillar"] != "Performance"]
    fixed.append(_exp("Conversion", title="extra1"))
    fixed.append(_exp("Conversion", title="extra2"))
    res = validate_report_set(fixed)
    assert not res["ok"] and any("Performance" in e for e in res["errors"])


# ----------------------------- selection (D15) -----------------------------

def _cand(pillar, conf, title):
    e = _exp(pillar, title=title)
    e["confidence"] = conf
    return e


def test_select_guarantees_all_pillars_and_total_ten():
    # Conversion-heavy pool, others sparse
    candidates = [_cand("Conversion", 90 - i, f"c{i}") for i in range(6)]
    candidates += [_cand("AOV", 80, "a1"), _cand("AOV", 70, "a2")]
    candidates += [_cand("Retention", 60, "r1")]
    candidates += [_cand("Acquisition", 55, "ac1")]
    candidates += [_cand("Performance", 50, "p1")]
    chosen = select_experiments(candidates)
    pillars = {e["pillar"] for e in chosen}
    assert len(chosen) == 10
    assert pillars == set(PILLARS)  # coverage floor honored


def test_select_fills_from_highest_confidence_leftovers():
    # Only Conversion has surplus; fill slots should be the top Conversion leftovers
    candidates = [_cand("Conversion", c, f"c{c}") for c in (95, 92, 90, 40, 30)]
    candidates += [_cand("AOV", 88, "a1")]
    candidates += [_cand("Retention", 70, "r1")]
    candidates += [_cand("Acquisition", 65, "ac1")]
    candidates += [_cand("Performance", 60, "p1")]
    chosen = select_experiments(candidates)
    conv = sorted((e["confidence"] for e in chosen if e["pillar"] == "Conversion"), reverse=True)
    # the low-confidence Conversion ones (40,30) should be dropped before them
    assert 40 not in conv and 30 not in conv


def test_select_respects_total_cap():
    candidates = [_cand("Conversion", 80, f"c{i}") for i in range(20)]
    assert len(select_experiments(candidates, total=10)) == 10
