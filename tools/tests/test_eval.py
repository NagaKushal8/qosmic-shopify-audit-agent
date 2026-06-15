"""Tests for the deterministic eval layers (no LLM needed)."""
from eval import coverage, grounding, judge, score, structural, validate_eval


def _exp(pillar="Conversion", evidence="pages/01_product_x/screenshot.png",
         url="https://s.com/products/x", title="t"):
    return {
        "exp_id": f"exp-{title}", "title": title, "pillar": pillar, "surface": "PDP",
        "url": url, "evidence": evidence, "hypothesis": "h", "primary_change": "c",
        "primary_kpi": "CVR", "decision_rule": "ship if", "expected_lift": "+5%",
        "confidence": 70,
    }


def _ten_balanced():
    out = []
    for p in ["Conversion", "AOV", "Retention", "Acquisition", "Performance"]:
        out += [_exp(p, title=f"{p}1"), _exp(p, title=f"{p}2")]
    return out


def _run(experiments, pages=None, run_dir="/tmp/x", report_md=""):
    return {"run_dir": run_dir, "experiments": experiments, "report_md": report_md,
            "manifest": {"pages": pages or []}}


# ----------------------------- structural ----------------------------------

def test_balanced_set_high_balance():
    s = structural.evaluate(_run(_ten_balanced()))
    assert s["pillar_balance"] == 1.0
    assert s["structural_integrity"] == 1.0


def test_skewed_set_low_balance_and_flags():
    exps = [_exp("Conversion", title=f"c{i}") for i in range(9)] + [_exp("AOV", title="a")]
    s = structural.evaluate(_run(exps))
    assert s["pillar_balance"] < 0.5
    assert any("missing pillar" in f.lower() or "Performance" in f for f in s["fails"])


# --------------------------- citation existence ----------------------------

def test_citation_resolves_via_manifest():
    pages = [{"category": "product", "screenshot_path": "pages/01_product_x/screenshot.png"}]
    g = grounding.evaluate(_run([_exp()], pages=pages))
    assert g["hallucinated"] == 0 and g["citation_validity"] == 1.0


def test_hallucinated_citation_flagged():
    g = grounding.evaluate(_run([_exp(evidence="pages/__nope__/ghost.png")]))
    assert g["hallucinated"] == 1


def test_url_evidence_accepted():
    g = grounding.evaluate(_run([_exp(evidence="https://s.com/products/x")]))
    assert g["hallucinated"] == 0


# ------------------------------- coverage ----------------------------------

def test_coverage_engaged_and_gap():
    pages = [
        {"category": "product", "url": "https://s.com/products/x", "dir": "pages/01_product_x"},
        {"category": "cart", "url": "https://s.com/cart", "dir": "pages/02_cart_cart"},
    ]
    # An experiment engages the product surface (Conversion is plausible) but nothing
    # touches the cart -> cart should be a flagged gap.
    exps = [_exp("Conversion", evidence="pages/01_product_x/screenshot.png",
                 url="https://s.com/products/x")]
    cov = coverage.evaluate(_run(exps, pages=pages))
    assert "product" in cov["categories_engaged"]
    assert any(g["category"] == "cart" for g in cov["flagged_gaps"])
    assert cov["coverage"] == 0.5


# -------------------------- scoring + gates --------------------------------

def _ev(experiments, pages=None, run_dir="/tmp/x"):
    run = _run(experiments, pages=pages, run_dir=run_dir)
    ev = {
        "n_experiments": len(experiments),
        "structural": structural.evaluate(run),
        "citations": grounding.evaluate(run),
        "coverage": coverage.evaluate(run),
        "judge": {"status": "unavailable", "grounding_precision": None, "specificity": None},
    }
    ev["score"] = score.score(ev)
    return ev


def test_clean_set_not_gated():
    pages = [{"category": "product", "screenshot_path": "pages/01_product_x/screenshot.png"}]
    # make all ten cite the resolvable artifact
    exps = [{**e, "evidence": "pages/01_product_x/screenshot.png"} for e in _ten_balanced()]
    ev = _ev(exps, pages=pages)
    assert ev["score"]["status"] == "ok"
    assert ev["score"]["partial_no_llm"] is True  # no LLM -> grounding/specificity None


def test_hallucination_gates_the_report():
    exps = [{**e, "evidence": "pages/__nope__/x.png"} for e in _ten_balanced()]
    ev = _ev(exps)
    assert ev["score"]["status"] == "GATED"
    assert ev["score"]["score"] <= 0.3


def test_missing_pillar_gates():
    exps = [_exp("Conversion", title=f"c{i}") for i in range(10)]
    ev = _ev(exps)
    assert ev["score"]["status"] == "GATED"


# --------------------------- meta-validation -------------------------------

def test_agent_verdicts_fold_in():
    data = {
        "verdicts": [{"exp_id": "a", "verdict": "supported"},
                     {"exp_id": "b", "verdict": "not_visible"},
                     {"exp_id": "c", "verdict": "supported"}],
        "generic": [{"exp_id": "a", "generic": False}, {"exp_id": "b", "generic": True}],
    }
    r = judge.from_agent_verdicts(data)
    assert r["status"] == "agent"
    assert r["grounding_precision"] == round(2 / 3, 3)   # 2 supported of 3
    assert r["specificity"] == 0.5                        # 1 generic of 2


def test_build_tasks_lists_claims_and_screenshots():
    run = _run([_exp(evidence="pages/01_product_x/screenshot.png")])
    tasks = judge.build_tasks(run)
    assert tasks["grounding"][0]["claim"] == "h"
    assert tasks["grounding"][0]["screenshot"] == "pages/01_product_x/screenshot.png"
    assert "experiment" in tasks["genericness"][0]


def test_meta_validation_real_beats_sabotaged():
    pages = [{"category": "product", "screenshot_path": "pages/01_product_x/screenshot.png"}]
    exps = [{**e, "evidence": "pages/01_product_x/screenshot.png"} for e in _ten_balanced()]
    run = _run(exps, pages=pages)
    v = validate_eval.validate(run)
    assert v["passed"] is True
    assert v["good_score"] > v["bad_score"]
