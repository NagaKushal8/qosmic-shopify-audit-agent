#!/usr/bin/env python3
"""Idempotent environment bootstrap (decision D8: reproducible env).

Creates a pinned `.venv`, installs `requirements.txt` exactly, installs the
Playwright Chromium binary, and writes a readiness marker. Safe to run on every
audit: it only does work when the venv is missing or `requirements.txt` changed
(detected via a content hash stored in the marker).

Usage:
    python tools/setup_env.py          # ensure env ready (idempotent)
    python tools/setup_env.py --check  # exit 0 if ready, 1 if not (makes no changes)

The skill / CLAUDE.md instruct the agent to run this as a mandatory Step 0 before
crawling, so the audit always runs against pinned versions.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
REQS = ROOT / "requirements.txt"
MARKER = VENV / ".ready"


def venv_python(v: Path) -> Path:
    """Path to the interpreter inside the venv (cross-platform)."""
    if sys.platform == "win32":
        return v / "Scripts" / "python.exe"
    return v / "bin" / "python"


def reqs_hash() -> str:
    return hashlib.sha256(REQS.read_bytes()).hexdigest() if REQS.exists() else ""


def is_ready() -> bool:
    return (
        MARKER.exists()
        and venv_python(VENV).exists()
        and MARKER.read_text().strip() == reqs_hash()
    )


def run(cmd: list[str]) -> None:
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.check_call(cmd)


def main() -> int:
    check_only = "--check" in sys.argv
    if is_ready():
        print("[setup] environment ready.")
        return 0
    if check_only:
        print("[setup] environment NOT ready -> run: python tools/setup_env.py")
        return 1
    if not REQS.exists():
        print(f"[setup] missing {REQS}", file=sys.stderr)
        return 2

    if not venv_python(VENV).exists():
        print(f"[setup] creating venv at {VENV}")
        venv.create(VENV, with_pip=True)

    py = str(venv_python(VENV))
    print("[setup] upgrading pip + installing pinned requirements")
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", str(REQS)])

    print("[setup] installing Playwright Chromium browser")
    run([py, "-m", "playwright", "install", "chromium"])

    MARKER.write_text(reqs_hash())
    print("[setup] environment ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
