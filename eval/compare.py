"""Relative scoring — the self-improvement engine. No golden answer needed; you only
need a comparator. Diffs two evaluated runs (v1 vs v2, or two stores)."""
from __future__ import annotations


def compare(a: dict, b: dict) -> dict:
    va, vb = a["score"]["vector"], b["score"]["vector"]
    vector_deltas = {k: round(vb[k] - va[k], 3)
                     for k in va if va.get(k) is not None and vb.get(k) is not None}
    return {
        "score_delta": round(b["score"]["score"] - a["score"]["score"], 3),
        "vector_deltas": vector_deltas,
        "structural_fail_delta": len(b["structural"]["fails"]) - len(a["structural"]["fails"]),
        "coverage_delta": round(b["coverage"]["coverage"] - a["coverage"]["coverage"], 3),
        "gates_a": a["score"]["gates"],
        "gates_b": b["score"]["gates"],
    }
