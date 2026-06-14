"""Assemble + write `manifest.json` — the citation backbone of an audit run.

Every evidence path the audit report later cites resolves to an entry here, so the
eval system can mechanically verify that claims are grounded in real artifacts.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from .capture import PageEvidence
from .discovery import Surface
from .robots import RobotsInfo


def build_manifest(
    start_url: str,
    run_dir: Path,
    robots: RobotsInfo,
    surfaces: list[Surface],
    evidence: list[PageEvidence],
    *,
    started_at: str,
    finished_at: str,
    run_status: str = "ok",
    blocked_reason: Optional[str] = None,
) -> dict:
    fetched = [s for s in surfaces if s.fetched]
    captured_categories = Counter(e.category for e in evidence)
    return {
        "start_url": start_url,
        "domain": urlparse(start_url if "//" in start_url else "https://" + start_url).netloc,
        "run_dir": Path(run_dir).name,
        "status": run_status,            # 'ok' | 'blocked:password' | 'blocked:challenge' | 'capture_aborted'
        "blocked_reason": blocked_reason,
        "started_at": started_at,
        "finished_at": finished_at,
        "robots": {
            "present": robots.present,
            "crawl_delay": robots.crawl_delay,
            "sitemaps": robots.sitemaps,
            "disallow_count": len(robots.disallows),
        },
        "discovery": {
            "total_discovered": len(surfaces),
            "fetched": len(fetched),
            "captured": len(evidence),
            "by_category_captured": dict(captured_categories),
        },
        "pages": [asdict(e) for e in evidence],
    }


def write_manifest(manifest: dict, run_dir: Path) -> Path:
    path = Path(run_dir) / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
