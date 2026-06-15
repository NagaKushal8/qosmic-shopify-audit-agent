#!/usr/bin/env python3
"""One-shot DETERMINISTIC audit pipeline: crawl -> digest -> tech_checks -> assemble.

    python tools/audit.py https://store.com [crawl flags...]

This chains the four Python phases into one command and prints the run folder.

The reasoning / executive-summary / competitor sections are **agent-driven** (the
`reason` + `synthesize` skills) by design — a pure script can't do them without an
LLM. For the FULL audit, hand this harness to a coding agent and say
"audit <url>" (see CLAUDE.md); the agent runs reason + synthesize between digest and
assemble. Run this script alone and those sections render as honest "not generated yet".
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
PY = sys.executable  # use whatever interpreter launched us (the venv one)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: python tools/audit.py <url> [crawl flags...]", file=sys.stderr)
        return 2
    url, extra = args[0], args[1:]

    # 1. crawl — capture stdout to recover the run-dir path it created
    print(f"\n$ {PY} tools/crawl.py {url} {' '.join(extra)}".rstrip())
    crawl = subprocess.run([PY, str(TOOLS / "crawl.py"), url, *extra],
                           text=True, capture_output=True)
    print(crawl.stdout)
    if crawl.stderr:
        print(crawl.stderr, file=sys.stderr)
    if crawl.returncode != 0:
        return crawl.returncode
    m = re.search(r"run dir:\s*(.+)", crawl.stdout)
    if not m:
        print("[audit] could not find run dir in crawl output", file=sys.stderr)
        return 1
    run_dir = m.group(1).strip()

    # 2-4. digest -> tech_checks -> assemble (stream their output)
    for tool in ("digest.py", "tech_checks.py", "assemble.py"):
        print(f"\n$ {PY} tools/{tool} {run_dir}")
        r = subprocess.run([PY, str(TOOLS / tool), run_dir])
        if r.returncode != 0:
            return r.returncode

    print(f"\n[audit] deterministic pipeline complete -> {run_dir}")
    print("[audit] report: " + str(Path(run_dir) / "report" / "report.md"))
    print("[audit] note: experiments/summary/competitors are agent-driven "
          "(reason + synthesize skills) — say \"audit <url>\" to a coding agent for the full report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
