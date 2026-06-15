"""Gates -> vector -> weighted scalar. The vector is the real output (drives the
loop); the scalar exists only for ranking, and gates ensure no polish can launder
fabricated evidence into a good score."""
from __future__ import annotations

from qcrawl.experiments import PILLARS

# Grounding heaviest on purpose: it's the metric most tied to the disqualifying
# failure ("no slop") and the one that generalizes best to unseen stores.
WEIGHTS = {
    "grounding_precision": 0.40,
    "specificity": 0.20,
    "coverage": 0.20,
    "structural_integrity": 0.10,
    "pillar_balance": 0.10,
}


def score(ev: dict) -> dict:
    s, c, cov, j = ev["structural"], ev["citations"], ev["coverage"], ev["judge"]

    gates = []
    if c["hallucinated"] > 0:
        gates.append(f"{c['hallucinated']} hallucinated citation(s)")
    missing = [p for p in PILLARS if s["pillar_distribution"].get(p, 0) == 0]
    if missing:
        gates.append(f"missing pillars: {missing}")
    if ev.get("n_experiments") != 10:
        gates.append(f"{ev.get('n_experiments')} experiments (expected 10)")

    vector = {
        "grounding_precision": j.get("grounding_precision"),
        "specificity": j.get("specificity"),
        "coverage": cov["coverage"],
        "structural_integrity": s["structural_integrity"],
        "pillar_balance": s["pillar_balance"],
    }
    # Weighted scalar over AVAILABLE dims (LLM dims may be None -> renormalize).
    avail = {k: v for k, v in vector.items() if v is not None}
    wsum = sum(WEIGHTS[k] for k in avail)
    raw = round(sum(vector[k] * WEIGHTS[k] for k in avail) / wsum, 3) if wsum else 0.0

    gated = bool(gates)
    return {
        "status": "GATED" if gated else "ok",
        "gates": gates,
        "score": min(0.3, raw) if gated else raw,   # gated reports can't out-rank clean ones
        "vector": vector,
        "partial_no_llm": j.get("status") != "ok",
        "weights": WEIGHTS,
    }
