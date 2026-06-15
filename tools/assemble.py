#!/usr/bin/env python3
"""Assemble CLI — stitch cached structured artifacts into the final report.md.

Reads evidence/<run>/report/{experiments,summary,competitors,tech_checks}.json and
writes evidence/<run>/report/report.md (target_report.md structure). Pure Python —
no LLM, no formatting drift. Honest about any missing/unavailable section.

Usage:
    python tools/assemble.py evidence/store.com_20260614-190000
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.assemble import write_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/assemble.py <evidence/run_dir>", file=sys.stderr)
        return 2
    run_dir = Path(args[0])
    if not run_dir.exists():
        print(f"[assemble] run dir not found: {run_dir}", file=sys.stderr)
        return 2
    out = write_report(run_dir)
    print(f"[assemble] wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
