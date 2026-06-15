#!/usr/bin/env python3
"""Verify competitor domains + validate the synth artifacts for a run.

    python tools/synth_check.py <run_dir>

Updates report/competitors.json with `domain_resolves` (dropping/flagging
hallucinated domains), then validates report/competitors.json and report/summary.json.
One command, no inline shell Python. Exit 1 if either artifact is invalid.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.synth import validate_competitors, validate_summary, verify_domains  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/synth_check.py <run_dir>", file=sys.stderr)
        return 2
    report = Path(args[0]) / "report"
    comp_path, summ_path = report / "competitors.json", report / "summary.json"
    rc = 0

    if comp_path.exists():
        comp = json.loads(comp_path.read_text(encoding="utf-8"))
        if comp.get("status") == "ok" and comp.get("competitors"):
            comp["competitors"] = verify_domains(comp["competitors"])
            comp_path.write_text(json.dumps(comp, indent=2, ensure_ascii=False), encoding="utf-8")
            for c in comp["competitors"]:
                print(f"[synth] {c.get('domain')} -> resolves={c.get('domain_resolves')}")
        errs = validate_competitors(comp)
        print(f"[synth] competitors valid={not errs}" + (f" {errs}" if errs else ""))
        rc = rc or (1 if errs else 0)
    else:
        print("[synth] no competitors.json (skipped)")

    if summ_path.exists():
        errs = validate_summary(json.loads(summ_path.read_text(encoding="utf-8")))
        print(f"[synth] summary valid={not errs}" + (f" {errs}" if errs else ""))
        rc = rc or (1 if errs else 0)
    else:
        print("[synth] no summary.json (skipped)")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
