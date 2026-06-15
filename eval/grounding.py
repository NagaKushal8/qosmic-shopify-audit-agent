"""Layer 2a — citation existence (no LLM). Catches the worst failure mode
(hallucinated evidence) as a cheap set-membership / disk check."""
from __future__ import annotations

from pathlib import Path

_PATH_KEYS = ("screenshot_path", "screenshot_mobile_path", "html_path", "meta_path",
              "drawer_screenshot_path", "popup_screenshot_path")


def evaluate(run: dict) -> dict:
    run_dir = Path(run["run_dir"])
    artifact_paths = set()
    for p in run["manifest"].get("pages", []):
        for k in _PATH_KEYS:
            if p.get(k):
                artifact_paths.add(p[k])

    fails, total, resolved = [], 0, 0
    for e in run["experiments"]:
        ev = e.get("evidence")
        if not ev:
            continue
        total += 1
        if str(ev).startswith(("http://", "https://")):
            resolved += 1  # URL evidence — can't disk-verify; accepted
        elif ev in artifact_paths or (run_dir / ev).exists():
            resolved += 1
        else:
            fails.append(f"{e.get('exp_id', '?')}: cites non-existent artifact '{ev}'")

    return {
        "fails": fails,
        "hallucinated": len(fails),
        "citation_validity": round(resolved / total, 3) if total else 1.0,
    }
