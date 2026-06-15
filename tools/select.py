#!/usr/bin/env python3
"""Select the final experiments from candidates (D15) + assign exp_ids + validate.

    python tools/select.py <candidates.json> [out.json]

Writes `experiments.json` next to the candidates file by default. One command, no
inline shell Python (avoids PowerShell quoting issues + the qcrawl import-path gap).
Exit 1 (with errors) if the selected set fails validation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.experiments import make_exp_id, select_experiments, validate_report_set  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/select.py <candidates.json> [out.json]", file=sys.stderr)
        return 2
    cand_path = Path(args[0])
    if not cand_path.exists():
        print(f"[select] not found: {cand_path}", file=sys.stderr)
        return 2
    out_path = Path(args[1]) if len(args) > 1 else cand_path.with_name("experiments.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = json.loads(cand_path.read_text(encoding="utf-8"))
    chosen = select_experiments(candidates)
    for e in chosen:
        e.setdefault("exp_id", make_exp_id(e.get("title", ""), e.get("url", "")))
    out_path.write_text(json.dumps(chosen, indent=2, ensure_ascii=False), encoding="utf-8")

    res = validate_report_set(chosen)
    print(f"[select] {len(chosen)} experiments -> {out_path}")
    print(f"[select] by_pillar: {res['by_pillar']}  ok={res['ok']}")
    for e in chosen:
        print(f"   [{e['pillar']}] {e.get('confidence')}% - {e.get('title', '')[:60]}")
    if not res["ok"]:
        for err in res["errors"]:
            print(f"   ! {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
