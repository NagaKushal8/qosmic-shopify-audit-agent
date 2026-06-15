"""Deterministic report assembly (decisions D17/D18).

Stitches the cached structured artifacts in `evidence/<run>/report/` into one
`report.md` matching `target_report.md`'s structure. NO LLM — pure templating, so
the final structure is identical every time. Sections that are missing or marked
`status="unavailable"` render an HONEST note rather than fabricated content.

Section order (matches target_report.md):
  title -> executive summary -> proposed experiments -> competitor analysis -> technical checks
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _load(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def render_title(summary: Optional[dict], domain: str) -> str:
    if summary and summary.get("status") == "ok" and summary.get("thesis_title"):
        return f"# {domain} audit — {summary['thesis_title']}"
    return f"# {domain} — CRO audit"


def render_summary(summary: Optional[dict]) -> str:
    if not summary or summary.get("status") != "ok":
        note = (summary or {}).get("note") or (
            "The audit configuration could not generate the executive summary "
            "(LLM unavailable). Reported honestly rather than fabricated."
        )
        return f"## Executive summary\n\n_{note}_"
    out = ["## Executive summary", ""]
    for para in summary.get("paragraphs", []):
        out.append(f"**{para.get('claim', '').strip()}** {para.get('body', '').strip()}")
        out.append("")
    return "\n".join(out).rstrip()


def render_experiments(experiments: Optional[list]) -> str:
    if not experiments:
        return "## Proposed experiments\n\n_No experiments were generated for this run._"
    out = ["## Proposed experiments", ""]
    for e in experiments:
        out += [
            f"### {e.get('exp_id', 'exp-?')} — {e.get('title', '')}",
            "",
            f"**Pillar:** {e.get('pillar', '')}",
            f"**Affected surface:** {e.get('surface', '')}",
            f"**URL:** {e.get('url', '')}",
            f"**Evidence:** `{e.get('evidence', '')}`",
            f"**Hypothesis:** {e.get('hypothesis', '')}",
            f"**Primary change:** {e.get('primary_change', '')}",
            f"**Primary KPI:** {e.get('primary_kpi', '')}",
            f"**Decision rule:** {e.get('decision_rule', '')}",
            f"**Expected lift:** {e.get('expected_lift', '')}",
            f"**Confidence:** {e.get('confidence', '')}%",
            "",
        ]
    return "\n".join(out).rstrip()


def render_competitors(comp: Optional[dict], domain: str) -> str:
    if not comp or comp.get("status") != "ok":
        note = (comp or {}).get("note") or (
            "The audit configuration could not generate competitor analysis "
            "(web search unavailable). Reported honestly rather than fabricated."
        )
        return f"## Competitor analysis\n\n_{note}_"
    out = ["## Competitor analysis", ""]
    if comp.get("intro"):
        out += [comp["intro"], ""]
    out += [
        f"| Competitor | Domain | Positioning | What they make easier | {domain} edge | Pattern to adapt |",
        "|---|---|---|---|---|---|",
    ]
    for c in comp.get("competitors", []):
        out.append(
            f"| {c.get('competitor','')} | {c.get('domain','')} | {c.get('positioning','')} | "
            f"{c.get('what_they_make_easier','')} | {c.get('store_edge','')} | "
            f"{c.get('pattern_to_adapt','')} |"
        )
    return "\n".join(out)


def render_tech_checks(tech) -> str:
    rows = tech.get("checks") if isinstance(tech, dict) else tech
    if not rows:
        return "## Technical checks\n\n_Technical checks were not generated for this run._"
    out = ["## Technical checks", "", "| Check | Status | Detail |", "|---|---|---|"]
    for c in rows:
        out.append(f"| {c.get('check','')} | {c.get('status','')} | {c.get('detail','')} |")
    return "\n".join(out)


def assemble_report(run_dir, *, domain: Optional[str] = None) -> str:
    """Build the full report.md text from the cached structured artifacts."""
    run_dir = Path(run_dir)
    report_dir = run_dir / "report"

    summary = _load(report_dir / "summary.json")
    experiments = _load(report_dir / "experiments.json")
    competitors = _load(report_dir / "competitors.json")
    tech = _load(report_dir / "tech_checks.json")

    if not domain:
        manifest = _load(run_dir / "manifest.json") or {}
        domain = manifest.get("domain", run_dir.name)

    sections = [
        render_title(summary, domain),
        "",
        render_summary(summary),
        "",
        render_experiments(experiments),
        "",
        render_competitors(competitors, domain),
        "",
        render_tech_checks(tech),
        "",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_report(run_dir, *, domain: Optional[str] = None) -> Path:
    run_dir = Path(run_dir)
    report_dir = run_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    text = assemble_report(run_dir, domain=domain)
    out = report_dir / "report.md"
    out.write_text(text, encoding="utf-8")
    return out
