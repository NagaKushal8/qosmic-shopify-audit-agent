#!/usr/bin/env python3
"""Digest CLI — turn a raw crawl run into a routed, signal-rich digest.

Reads `evidence/<run>/manifest.json` (+ saved HTML/meta) and writes a NEW
`evidence/<run>/digest/` folder (digest.json + per-pillar indexes + summary).
Never mutates raw evidence (decision D14). Re-runnable on any existing run.

Usage:
    python tools/digest.py evidence/store.com_20260614-190000
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.digest import build_digest, write_digest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/digest.py <evidence/run_dir>", file=sys.stderr)
        return 2
    run_dir = Path(args[0])
    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        print(f"[digest] no manifest.json in {run_dir}", file=sys.stderr)
        return 2

    digest = build_digest(run_dir)
    out = write_digest(digest, run_dir)
    routed = {pillar: sum(1 for p in digest["pages"] if pillar in p["pillars"])
              for pillar in ("Conversion", "AOV", "Retention", "Acquisition", "Performance")}
    print(f"[digest] {digest.get('domain')} status={digest.get('status')} "
          f"pages={len(digest['pages'])}")
    print(f"[digest] routed per pillar: {routed}")
    print(f"[digest] wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
