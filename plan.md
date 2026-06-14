# Qosmic Take-Home — Project Plan (living doc)

> Living map of the build. Updated as we go. Decisions and reasoning live in
> [decision.md](decision.md); agent time/prompts live in [AGENT_LOG.md](AGENT_LOG.md).

## Goal & contract

Build a **runtime harness** that turns any coding agent (Claude Code / Codex /
other) into the **Qosmic CRO audit agent**.

- **Input:** a single Shopify storefront URL. Nothing else.
- **Output:** one audit report (`.md`) at the bar of `target_report.md`, containing
  exactly:
  1. **Executive summary** — 2–3 prose paragraphs, each led by a bolded claim, the
     highest-level read on what's costing the store sales right now.
  2. **10 proposed experiments** — each with: title + `exp-id` (hex), pillar
     (Conversion / AOV / Retention / Acquisition / Performance), affected surface +
     URL, evidence (screenshot path or URL), hypothesis, primary change, primary
     KPI, decision rule, expected lift range, confidence %. The 10 span all 5 pillars.
  3. **Competitor analysis** — table vs 3–4 competitors: positioning, what they make
     easier, store's edge, pattern to adapt.
  4. **Technical checks** — ~15 standard checks, each Pass / Warn / Fail + one-line detail.
- **Plus (Part 2, weighted heavier):** an **eval system** that scores audit reports
  for *unseen* stores, and `EVAL_LOOP.md` — how that eval system becomes autonomous
  and self-learning.

**Quality bars:** cite everything (every claim → artifact path or URL); diversify
pillars; generalize (no gingerpeople-specific shortcuts).

## Architecture (Crawl → Reason → Write, hybrid)

```
qosmic-audit/
  CLAUDE.md                 # entry point: contract + how to run an audit
  .claude/skills/
    crawl/SKILL.md          # visit surfaces, capture screenshots + page content
    reason/SKILL.md         # find revenue leaks across 5 pillars, build experiments
    write-report/SKILL.md   # emit canonical report -> target_report.md
    competitor/SKILL.md     # find + compare 3-4 competitors
    tech-checks/SKILL.md    # ~15 storefront checks (SSL, sitemap, robots, etc.)
  tools/                    # thin deterministic crawl helper (screenshots/DOM/HTTP)
  eval/                     # Part 2: deterministic checks + LLM-judge rubric
  sample_output/            # gingerpeople + zenrojas audits (end-to-end proof)
```

- **Hybrid (D1):** Skills drive Reason/Write; a thin Python/crawl helper handles
  Crawl + screenshots so evidence is deterministic and reproducible.
- **Surfaces to crawl:** homepage, 1–2 PDPs, a collection, cart, key content pages
  (FAQ / Where To Buy / blog) — a representative set per the brief.

## Deliverables checklist

- [ ] Runtime harness (skills + `CLAUDE.md` + crawl helper)
- [ ] Eval system (`eval/`)
- [ ] `sample_output/gingerpeople.com` audit (calibration → approach target bar)
- [ ] `sample_output/zenrojas.com` audit (generalization → unseen store)
- [x] `AGENT_LOG.md` — time per part, prompts fed, agent-drove vs took-the-wheel
- [ ] `EVAL_LOOP.md` — eval autonomy + self-learning (≤1 page)
- [ ] `WORKFLOWS.md` — how I use coding agents day-to-day (≤1 page)
- [ ] 3–5 min Loom — walk harness + eval loop; one decision I'd reverse; one
      dimension I didn't measure that matters

## Time budget

| Part | Scope | Target | Ceiling |
|---|---|---|---|
| Setup | scaffolding (this) + planning | ~0.25h | — |
| Part 1 | Runtime harness, runs end-to-end on both URLs | ~2h | — |
| Part 2 | Eval system + autonomy plan (headline) | ~2h | — |
| Wrap | WORKFLOWS.md + Loom | ~0.25h | — |
| **Total** | | **~4h** | **5h hard** |

## Open questions

- **D2 — crawl/evidence mechanism** (Playwright MCP vs WebFetch-only). See decision.md.
- **D3 — eval system shape** (hybrid deterministic + LLM-judge). See decision.md.

## Status board

- [x] Scaffolding files created (plan / decision / agent log)
- [ ] Settle D2 + D3
- [ ] Build harness skills + crawl helper
- [ ] Run gingerpeople.com end-to-end
- [ ] Run zenrojas.com end-to-end
- [ ] Build eval system
- [ ] Write EVAL_LOOP.md
- [ ] Write WORKFLOWS.md
- [ ] Record Loom
