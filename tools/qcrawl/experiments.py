"""Experiment schema + deterministic guardrails for the reduce step (D14).

The reason agents emit experiments as dicts following CANONICAL_FIELDS (matching
target_report.md). This module provides:
  - `make_exp_id`        — stable hex id from title+url (matches the report style)
  - `validate_experiment`— per-experiment schema check
  - `validate_report_set`— set-level budget: exactly 10, all 5 pillars, ≈2/pillar,
                           unique ids, every experiment cites an evidence path

Semantic dedupe / "which 10 are best" stays agent-driven; this enforces the
objective budget so the final set can't drift.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from .pillars import PILLARS

CANONICAL_FIELDS = [
    "exp_id", "title", "pillar", "surface", "url", "evidence",
    "hypothesis", "primary_change", "primary_kpi", "decision_rule",
    "expected_lift", "confidence",
]

TARGET_TOTAL = 10
PER_PILLAR_CEILING = 4   # hard cap on what one pillar agent may emit
SELECT_ROUNDS = 2        # take up to top-2 per pillar before global fill


def _confidence(exp: dict) -> float:
    try:
        return float(str(exp.get("confidence", 0)).rstrip("%") or 0)
    except ValueError:
        return 0.0


def make_exp_id(title: str, url: str) -> str:
    """12-hex id like the reference report's `exp-<hex>` style."""
    digest = hashlib.sha1(f"{title}|{url}".encode("utf-8")).hexdigest()
    return f"exp-{digest[:12]}"


def validate_experiment(exp: dict) -> list[str]:
    """Return a list of problems for one experiment (empty == valid)."""
    errors: list[str] = []
    for field in CANONICAL_FIELDS:
        if field == "exp_id":
            continue  # may be auto-generated
        if not exp.get(field):
            errors.append(f"missing/empty field: {field}")

    pillar = exp.get("pillar")
    if pillar and pillar not in PILLARS:
        errors.append(f"invalid pillar: {pillar!r} (must be one of {PILLARS})")

    conf = exp.get("confidence")
    if conf is not None:
        try:
            c = float(str(conf).rstrip("%"))
            if not 0 <= c <= 100:
                errors.append(f"confidence out of range: {conf}")
        except ValueError:
            errors.append(f"confidence not numeric: {conf}")

    # Evidence must point at something (a manifest/screenshot path or a URL).
    ev = exp.get("evidence")
    if ev and not (str(ev).startswith(("pages/", "evidence/", "http://", "https://"))
                   or str(ev).endswith((".png", ".html", ".json"))):
        errors.append(f"evidence does not look like a path/URL: {ev!r}")

    return errors


def validate_report_set(experiments: list[dict]) -> dict:
    """Set-level budget check. Returns {'ok': bool, 'errors': [...], 'by_pillar': {...}}."""
    errors: list[str] = []

    if len(experiments) != TARGET_TOTAL:
        errors.append(f"expected {TARGET_TOTAL} experiments, got {len(experiments)}")

    ids = [e.get("exp_id") for e in experiments if e.get("exp_id")]
    if len(ids) != len(set(ids)):
        errors.append("duplicate exp_id(s)")

    by_pillar: dict[str, int] = {p: 0 for p in PILLARS}
    for e in experiments:
        if e.get("pillar") in by_pillar:
            by_pillar[e["pillar"]] += 1

    missing = [p for p, n in by_pillar.items() if n == 0]
    if missing:
        errors.append(f"pillars with no experiment: {missing}")

    for i, e in enumerate(experiments):
        for problem in validate_experiment(e):
            errors.append(f"experiment[{i}] ({e.get('title','?')}): {problem}")

    return {"ok": not errors, "errors": errors, "by_pillar": by_pillar}


def select_experiments(candidates: list[dict], *, total: int = TARGET_TOTAL,
                       rounds: int = SELECT_ROUNDS) -> list[dict]:
    """Coverage-floor + confidence-greedy selection (decision D15).

    Pillar agents emit open-ended candidates (capped at PER_PILLAR_CEILING each).
    We then:
      Round 1: take the top-1 (by confidence) from each pillar -> all 5 represented.
      Round 2..rounds: take the next-best from each pillar where available.
      Fill: if still < total, greedily add the highest-confidence leftovers.
    Returns exactly `total` experiments (or fewer if not enough candidates exist).
    """
    by_pillar: dict[str, list[int]] = {p: [] for p in PILLARS}
    for i, exp in enumerate(candidates):
        if exp.get("pillar") in by_pillar:
            by_pillar[exp["pillar"]].append(i)
    for pillar in by_pillar:
        by_pillar[pillar].sort(key=lambda i: _confidence(candidates[i]), reverse=True)

    chosen: list[int] = []
    for rnd in range(rounds):
        for pillar in PILLARS:
            if len(chosen) >= total:
                break
            if len(by_pillar[pillar]) > rnd:
                idx = by_pillar[pillar][rnd]
                if idx not in chosen:
                    chosen.append(idx)

    if len(chosen) < total:
        leftovers = sorted(
            (i for i in range(len(candidates)) if i not in chosen),
            key=lambda i: _confidence(candidates[i]), reverse=True,
        )
        for idx in leftovers:
            if len(chosen) >= total:
                break
            chosen.append(idx)

    return [candidates[i] for i in chosen[:total]]
