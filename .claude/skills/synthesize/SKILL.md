---
name: synthesize
description: >-
  Generate the two LLM-authored report sections — executive summary and competitor
  analysis — as validated structured JSON. Use AFTER reason (experiments exist) and
  before assembly. Competitor analysis REQUIRES a web-search tool; never fabricate.
---

# Synthesize: executive summary + competitor analysis (structured)

Input: a run folder with `report/experiments.json` (from reason) + `digest/`.
Output: two cached structured artifacts in `evidence/<run>/report/`:
`summary.json` and `competitors.json`. Both are JSON only — prose appears only when
`assemble.py` renders. **Never fabricate**; if a piece can't be made, mark it
`status:"unavailable"` with an honest `note`.

## 1. Competitor analysis (web-search REQUIRED)
1. Derive a **store profile** from `digest/summary.md` + `digest/digest.json`
   (category, positioning, key products) — no guessing the brand's space.
2. **Search the web** for 3–4 real competitors in that space. If you have NO web
   search/fetch tool available, STOP this section and write:
   ```json
   { "status": "unavailable",
     "note": "Competitor analysis requires a web-search tool, which wasn't available in this run configuration. Reported honestly rather than fabricated from model memory." }
   ```
   Do **not** invent competitors from memory (hallucination risk → dishonest report).
3. For each competitor fill: `competitor, domain, positioning, what_they_make_easier,
   store_edge, pattern_to_adapt`. `store_edge` must reference OUR digest evidence.
4. Write it to `evidence/<run>/report/competitors.json`.
5. **Domain-verify + validate in one command** (no inline `python -c`):
   ```
   ./.venv/Scripts/python.exe tools/synth_check.py evidence/<run>
   ```
   It annotates each competitor with `domain_resolves`, rewrites competitors.json,
   and validates BOTH competitors.json and summary.json (exit 1 + errors if invalid).
   Replace/remove any competitor whose domain doesn't resolve, then re-run.

## 2. Executive summary (LLM synthesis — generate LAST)
Generate AFTER experiments (and competitors) so it stays consistent with them.
1. Read `report/experiments.json` — find the **dominant theme** (the single biggest
   leak across pillars), led by the highest-confidence / best-evidence experiments.
2. Emit `summary.json` per `schema/summary.schema.json`:
   `thesis_title` (the report's punchy H1) + 2–3 `paragraphs`, each
   `{claim, body}` (bolded lead + supporting prose). Claims must reference surfaces
   already cited by the experiments — no new uncited assertions.
3. If you cannot synthesize a valid summary, write
   `{ "status": "unavailable", "note": "<honest reason>" }` — never fake it.
4. Validation happens via `tools/synth_check.py evidence/<run>` (step 5 above —
   it validates both summary.json and competitors.json in one call).

## Output contract
- `report/competitors.json` — valid per schema, OR honest `status:"unavailable"`.
- `report/summary.json` — valid per schema, OR honest `status:"unavailable"`.
Both cached in `evidence/<run>/report/`. Then hand off to assembly
(`python tools/assemble.py evidence/<run>`), which renders the final `report.md`.

## Honesty rule (non-negotiable)
We would rather ship a report that says "this section couldn't be generated with the
available config" than one that fabricates competitors or claims. Any unavailable
section is also noted in `wherewefail.md`.
