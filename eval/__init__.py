"""Qosmic eval harness — scores an audit report with NO golden answer.

Layered (most layers are deterministic Python; only the judge is a caged LLM):
  loader     — read a run folder's structured artifacts
  structural — Layer 1: schema/section/pillar-balance checks (no LLM)
  grounding  — Layer 2a: citation existence (no LLM)
  coverage   — Layer 3: high-value surfaces engaged by plausible pillars (no LLM)
  judge      — Layers 2b+4: grounded yes/no + genericness (caged LLM, optional)
  score      — gates -> vector -> weighted scalar (ranking only)
  compare    — relative scoring (v1 vs v2) — the self-improvement engine
  validate_eval — meta-validation: real run must outscore a sabotaged copy
"""

__all__ = ["loader", "structural", "grounding", "coverage", "judge", "score",
           "compare", "validate_eval"]
