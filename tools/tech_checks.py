#!/usr/bin/env python3
"""Technical-checks CLI — deterministic ~15 storefront checks for a crawl run.

Writes `evidence/<run>/report/tech_checks.json`. No LLM.

Usage:
    python tools/tech_checks.py evidence/store.com_20260614-190000
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.tech_checks import run_checks  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/tech_checks.py <evidence/run_dir>", file=sys.stderr)
        return 2
    run_dir = Path(args[0])
    if not (run_dir / "manifest.json").exists():
        print(f"[tech] no manifest.json in {run_dir}", file=sys.stderr)
        return 2

    checks = run_checks(run_dir)
    report_dir = run_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / "tech_checks.json"
    out.write_text(json.dumps({"checks": checks}, indent=2, ensure_ascii=False), encoding="utf-8")

    counts = {s: sum(1 for c in checks if c["status"] == s) for s in ("Pass", "Warn", "Fail")}
    print(f"[tech] {len(checks)} checks -> {counts}")
    print(f"[tech] wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
