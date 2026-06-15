"""Synthesis-phase helpers (D17/D18): deterministic guards for the LLM steps.

- `verify_domains`     — drop/flag competitor domains that don't resolve (kills
                         hallucinated domains cheaply).
- `validate_summary`   — schema check for the structured executive summary.
- `validate_competitors` — schema check for the competitor analysis.

No fabrication: if a synth step is marked `status="unavailable"`, that's honest and
valid — assemble.py renders the honest note rather than inventing content.
"""
from __future__ import annotations

from typing import Optional

import httpx

_UA = {"user-agent": "QosmicAuditBot/1.0 (+storefront-audit)"}
_COMPETITOR_FIELDS = [
    "competitor", "domain", "positioning", "what_they_make_easier",
    "store_edge", "pattern_to_adapt",
]


def verify_domains(competitors: list[dict], *, timeout: int = 10,
                   client: Optional[httpx.Client] = None) -> list[dict]:
    """Annotate each competitor with `domain_resolves` (a cheap reality check)."""
    owns = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=timeout, headers=_UA)
    out: list[dict] = []
    try:
        for c in competitors:
            domain = str(c.get("domain", "")).strip()
            url = domain if "//" in domain else "https://" + domain
            resolves = False
            if domain:
                try:
                    resolves = client.get(url).status_code < 500
                except httpx.HTTPError:
                    resolves = False
            out.append({**c, "domain_resolves": resolves})
    finally:
        if owns:
            client.close()
    return out


def validate_summary(summary: dict) -> list[str]:
    errors: list[str] = []
    status = summary.get("status")
    if status not in ("ok", "unavailable"):
        errors.append("summary.status must be 'ok' or 'unavailable'")
    if status == "unavailable":
        if not summary.get("note"):
            errors.append("unavailable summary must include an honest 'note'")
        return errors
    paras = summary.get("paragraphs") or []
    if not 2 <= len(paras) <= 3:
        errors.append(f"summary needs 2-3 paragraphs, got {len(paras)}")
    for i, p in enumerate(paras):
        if not p.get("claim"):
            errors.append(f"paragraph[{i}] missing claim")
        if not p.get("body"):
            errors.append(f"paragraph[{i}] missing body")
    if not summary.get("thesis_title"):
        errors.append("summary missing thesis_title")
    return errors


def validate_competitors(comp: dict) -> list[str]:
    errors: list[str] = []
    status = comp.get("status")
    if status not in ("ok", "unavailable"):
        errors.append("competitors.status must be 'ok' or 'unavailable'")
    if status == "unavailable":
        if not comp.get("note"):
            errors.append("unavailable competitors must include an honest 'note'")
        return errors
    rows = comp.get("competitors") or []
    if not 3 <= len(rows) <= 4:
        errors.append(f"need 3-4 competitors, got {len(rows)}")
    for i, c in enumerate(rows):
        for field in _COMPETITOR_FIELDS:
            if not c.get(field):
                errors.append(f"competitor[{i}] missing {field}")
        if c.get("domain_resolves") is False:
            errors.append(f"competitor[{i}] domain does not resolve: {c.get('domain')!r}")
    return errors
