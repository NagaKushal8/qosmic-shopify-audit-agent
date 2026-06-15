"""Meta-validation — earn the right to trust the eval. A real run must out-score a
deliberately sabotaged copy (stripped citations + pillar collapse + generic prose).
If it can't tell good from sabotaged, the eval is broken.

Note: grounding meta-validation needs the run's OWN screenshots, so we sabotage a
self-produced run (not target_report.md, whose artifacts we don't possess). The
deterministic layers alone already separate good from sabotaged via gates."""
from __future__ import annotations

import copy

from . import coverage, grounding, judge, score, structural


def _evaluate(run: dict) -> dict:
    ev = {
        "n_experiments": len(run["experiments"]),
        "structural": structural.evaluate(run),
        "citations": grounding.evaluate(run),
        "coverage": coverage.evaluate(run),
        "judge": judge.evaluate(run),
    }
    ev["score"] = score.score(ev)
    return ev


def sabotage(run: dict) -> dict:
    bad = copy.deepcopy(run)
    for e in bad["experiments"]:
        e["evidence"] = "pages/__nonexistent__/fake.png"   # hallucinated citation
        e["pillar"] = "Conversion"                          # collapse pillar diversity
        e["hypothesis"] = "Add reviews to the product page to increase conversions."  # generic slop
    return bad


def validate(run: dict) -> dict:
    good = _evaluate(run)
    bad = _evaluate(sabotage(run))
    passed = good["score"]["score"] > bad["score"]["score"]
    return {
        "passed": passed,
        "good_score": good["score"]["score"],
        "bad_score": bad["score"]["score"],
        "good_gates": good["score"]["gates"],
        "bad_gates": bad["score"]["gates"],
        "message": ("OK: eval ranks the real run above the sabotaged copy."
                    if passed else
                    "BROKEN: eval cannot distinguish good from sabotaged — do not trust it."),
    }
