"""Load a run folder's structured artifacts for evaluation.

The eval reads our cached structured JSON directly (experiments/summary/competitors/
tech_checks + manifest) — no prose-parsing needed, because the harness already emits
them. report.md is loaded too (for section-presence checks).
"""
from __future__ import annotations

import json
from pathlib import Path


def _load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def load_run(run_dir) -> dict:
    run_dir = Path(run_dir)
    report = run_dir / "report"
    rp = report / "report.md"
    return {
        "run_dir": run_dir,
        "manifest": _load_json(run_dir / "manifest.json") or {},
        "experiments": _load_json(report / "experiments.json") or [],
        "summary": _load_json(report / "summary.json"),
        "competitors": _load_json(report / "competitors.json"),
        "tech_checks": _load_json(report / "tech_checks.json"),
        "report_md": rp.read_text(encoding="utf-8", errors="ignore") if rp.exists() else "",
    }
