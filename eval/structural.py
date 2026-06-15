"""Layer 1 — structural checks (no LLM). Builds on qcrawl.experiments.validate_report_set
and adds report-section presence + a pillar-balance score."""
from __future__ import annotations

from collections import Counter

from qcrawl.experiments import PILLARS, validate_report_set

_SECTIONS = ["executive summary", "proposed experiments", "competitor analysis", "technical checks"]


def _balance(counts: Counter, total: int) -> float:
    """1.0 = perfectly even across 5 pillars; 0.0 = all in one pillar."""
    if total == 0:
        return 0.0
    ideal = total / 5
    imbalance = sum(abs(counts.get(p, 0) - ideal) for p in PILLARS)
    max_imbalance = (total - ideal) + 4 * ideal  # everything in a single pillar
    return round(1 - imbalance / max_imbalance, 3) if max_imbalance else 1.0


def evaluate(run: dict) -> dict:
    exps = run["experiments"]
    res = validate_report_set(exps)
    fails = list(res["errors"])

    md = (run.get("report_md") or "").lower()
    if run.get("report_md"):
        for section in _SECTIONS:
            if section not in md:
                fails.append(f"report.md missing section: {section}")

    counts = Counter(e.get("pillar") for e in exps)
    structural_integrity = round(max(0.0, 1 - len(fails) / 10), 3)
    return {
        "fails": fails,
        "pillar_distribution": {p: counts.get(p, 0) for p in PILLARS},
        "pillar_balance": _balance(counts, len(exps)),
        "structural_integrity": structural_integrity,
    }
