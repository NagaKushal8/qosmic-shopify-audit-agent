"""Tests for qcrawl.assemble — deterministic report rendering."""
import json

from qcrawl.assemble import assemble_report


def _write(run_dir, name, obj):
    rd = run_dir / "report"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / name).write_text(json.dumps(obj), encoding="utf-8")


def _seed(run_dir):
    (run_dir / "manifest.json").write_text(json.dumps({"domain": "store.com"}), encoding="utf-8")
    _write(run_dir, "summary.json", {
        "status": "ok", "thesis_title": "the buy path is the constraint",
        "paragraphs": [{"claim": "Big leak.", "body": "Because reasons."},
                       {"claim": "Second.", "body": "More."}],
    })
    _write(run_dir, "experiments.json", [{
        "exp_id": "exp-abc123def456", "title": "Add buying box", "pillar": "Conversion",
        "surface": "PDP", "url": "https://store.com/products/x",
        "evidence": "pages/01_product_x/screenshot.png", "hypothesis": "h",
        "primary_change": "c", "primary_kpi": "CVR", "decision_rule": "ship if",
        "expected_lift": "+10%", "confidence": 78,
    }])
    _write(run_dir, "competitors.json", {
        "status": "ok", "intro": "Rivals make it easier.",
        "competitors": [{"competitor": "Rival", "domain": "rival.com", "positioning": "p",
                         "what_they_make_easier": "w", "store_edge": "e", "pattern_to_adapt": "a"}],
    })
    _write(run_dir, "tech_checks.json", {"checks": [
        {"check": "SSL Certificate", "status": "Pass", "detail": "ok"},
        {"check": "Broken Links", "status": "Fail", "detail": "/cart 404"},
    ]})


def test_full_report_has_all_sections(tmp_path):
    _seed(tmp_path)
    md = assemble_report(tmp_path)
    assert "# store.com audit — the buy path is the constraint" in md
    assert "## Executive summary" in md
    assert "**Big leak.** Because reasons." in md
    assert "### exp-abc123def456 — Add buying box" in md
    assert "**Confidence:** 78%" in md
    assert "## Competitor analysis" in md
    assert "| Competitor | Domain |" in md
    assert "## Technical checks" in md
    assert "| Broken Links | Fail | /cart 404 |" in md


def test_section_order_matches_target(tmp_path):
    _seed(tmp_path)
    md = assemble_report(tmp_path)
    assert (md.index("Executive summary") < md.index("Proposed experiments")
            < md.index("Competitor analysis") < md.index("Technical checks"))


def test_unavailable_competitors_render_honest_note(tmp_path):
    _seed(tmp_path)
    _write(tmp_path, "competitors.json", {"status": "unavailable", "note": "no web search"})
    md = assemble_report(tmp_path)
    assert "## Competitor analysis" in md
    assert "no web search" in md
    assert "| Competitor |" not in md  # no fabricated table


def test_missing_section_is_honest_not_crash(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"domain": "store.com"}), encoding="utf-8")
    md = assemble_report(tmp_path)  # no report/ files at all
    assert "## Executive summary" in md and "## Technical checks" in md
    assert "could not generate" in md.lower() or "not generated" in md.lower()
