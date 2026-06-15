# AGENT_LOG.md

> Required deliverable. Tracks: **time per part**, **prompts fed to the agent**, and
> **where the agent drove vs. where I took the wheel**. Updated continuously.
> Timebox: ~4h target, **5h hard ceiling**.

## 1. Time log

Single working session on **2026-06-14**, ~17:30 → ~22:15 (≈ **4h 45m**, under the 5h ceiling).

| Part | Block | Start | End | Elapsed |
|---|---|---|---|---|
| Setup | Read brief + `target_report.md`; scaffold plan/decision/task/agent-log; lock initial decisions | 17:30 | 17:45 | 0:15 |
| Part 1 | Crawl design (BFS, robots polite-only) + `robots.py`/`discovery.py` + pinned env (`setup_env.py`) + tests | 17:45 | 18:30 | 0:45 |
| Part 1 | `capture.py` (screenshots/HTML/meta) + `manifest.py` + `crawl.py` orchestrator → `evidence/<run>/` | 18:30 | 19:00 | 0:30 |
| Part 1 | Resilience pass (D9) + dead-site health gate (D11) + tests | 19:00 | 19:30 | 0:30 |
| Part 1 | Generation: `digest.py` + `pillars.py` + `experiments.py`; reason/synthesize/crawl skills; `tech_checks.py` + `assemble.py`; `CLAUDE.md`/`AGENTS.md` | 19:30 | 20:20 | 0:50 |
| Part 1 | Web research (5 agents) + rewrite 5 generic playbooks (D20); interaction capture + tri-state (D21) | 20:20 | 21:00 | 0:40 |
| Part 1 | Cloudflare stealth + browser gate-escalation (D22); git history cleanup (.gitignore) | 21:00 | 21:20 | 0:20 |
| Part 1 | zenrojas.com end-to-end run; CLI ergonomics fix (`select.py`/`synth_check.py`, D23) | 21:20 | 21:35 | 0:15 |
| Part 2 | Eval harness (layered: structural/citation/coverage/judge/score/compare/validate) + `tools/eval.py` + tests (D24); eval-as-skill (D25) | 21:35 | 22:15 | 0:40 |
| **Total** | | **17:30** | **22:15** | **≈ 4h 45m / 5h** |

> Remaining (outside this session / in progress): `EVAL_LOOP.md` (user-authored),
> `WORKFLOWS.md`, `sample_output/`, Loom.

## 2. Prompts fed to the agent

Chronological list of the actual prompts/instructions given.

1. *(setup)* "Create plan.md, decision.md, AGENT_LOG.md — track every important
   decision with its reasoning; pre-assign the content/responsibilities of each
   file. Then we plan the project together."
   - Agent response: read both provided files, asked 4 clarifying questions
     (harness type, crawl mechanism, eval shape, where's `target_report.md`),
     then scaffolded the three docs.

2. *(crawl design)* "Discuss the crawl approach — robots.txt first, sitemap for
   navigation, store HTML + screenshots + metadata per page, edge-case test cases.
   Should the harness rely on an MCP? Clarify where the runtime entry point starts."
   - Outcome: locked D2 (no MCP — Python + Playwright-as-library), D4 (skill/Python
     split, agent-driven selection + hard cap), D5 (CLAUDE.md entry point). Created
     `task.md`.

3. *(implement)* "Make it reproducible — pinned env installed before runtime;
   mention it in the skill. Then start building (BFS-only discovery, robots
   polite-only)."
   - Outcome: built pinned `requirements.txt` + idempotent `setup_env.py` (D8);
     implemented `qcrawl/robots.py` (D7) + `qcrawl/discovery.py` (D6) with 29
     passing unit tests (offline, respx-mocked). Env verified end-to-end (venv +
     chromium installed).

4. *(implement crawl)* "Build the full
   crawl: URL in → discover pages → visit → screenshot + HTML + metadata for all
   pages → output under an `evidence/` folder, a fresh ordered run folder per run.
   I'll run it, then give more edge cases."
   - Outcome: built `qcrawl/capture.py` (Playwright desktop+mobile shots, rendered
     HTML, meta), `qcrawl/manifest.py` (citation backbone), `tools/crawl.py`
     orchestrator → `evidence/<domain>_<ts>/`. Did NOT execute (per user). Saved
     working preference to memory.

5. *(resilience + docs)* "Reflect on 7 failure scenarios (password, 800 products,
   page never loads, Playwright crash, Cloudflare, mobile shots fail, JS hydration).
   Implement fixes, record in decision.md, and create `wherewefail.md` cataloguing
   residual edge cases per phase; keep it updated + notify in chat going forward."
   - Outcome: honest scorecard (3 solid / 3 partial / 1 gap). Implemented 5
     resilience fixes (D9) across capture/discovery/crawl. Added `wherewefail.md`
     (D10) + memory to maintain it. No execution (per user).

6. *(dead-site gate)* "After extracting pages,
   detect 404/error/'not found', stop after retries/depth when pages aren't
   reachable; bail with a clear 'server down/error' message. Cover in flow + tests."
   - Outcome: built `qcrawl/health.py` two-tier gate (D11) — pre-flight homepage
     (unreachable/5xx/hard+soft-404 w/ retries) + post-discovery reachability;
     wired into `crawl.py` with early-exit + always-manifest; `test_health.py`
     added (offline). Flipped the dead-site item in `wherewefail.md` to handled.

7. *(build generation phase)* "Approved: pre-extract signals + HTML on demand, 5
   pillar agents → 10 experiments, preset routing, two-pass self-correction. Build it
   all carefully, record decisions, track tasks, note limits in wherewefail. I'll
   review after you finish."
   - Outcome (agent drove, no execution): D12/D13/D14 recorded. Built
     `qcrawl/pillars.py` (preset map), `qcrawl/digest.py` + `tools/digest.py`
     (deterministic CRO-signal extraction + non-destructive digest), `qcrawl/
     experiments.py` (schema validator + exp-id + budget guardrails),
     `test_digest.py` + `test_experiments.py`. Wrote the agent layer:
     `.claude/skills/crawl/SKILL.md`, `.claude/skills/reason/SKILL.md`, and the
     `CLAUDE.md`/`AGENTS.md` entry point. Updated `wherewefail.md` (Reason limits).

8. *(selection + structured outputs)* "Make generation open-ended (ceiling 3–4) and
   select: top-2/pillar then fill by confidence; enforce structured confidence output
   for sorting. "
   - Outcome: added `select_experiments` (coverage-floor + confidence-greedy, D15),
     `schema/experiment.schema.json` (structured-output contract), updated reason
     skill to demand JSON output + deterministic select/validate, added selection
     tests. Logged the cross-pillar confidence-calibration caveat in wherewefail.

9. *(playbooks)* "Do the playbooks (Option B): shared reason skill + 5 rich
   pillar playbooks. Leave summary/competitor/assembly for later direction."
   - Outcome: refactored `reason/SKILL.md` to load a per-pillar playbook each pass
     (specialist, not loop); created `reason/playbooks/{conversion,aov,retention,
     acquisition,performance}.md` — each with mission, leak patterns, weighted
     digest signals, KPIs, hypothesis + decision-rule templates, example angles.

10. *(write phase)* "Competitor = web search only, no fabrication; if unavailable be
    honest in summary + competitors + wherewefail. Cache the 3 structured outputs;
    stitch with Python flawlessly to target_report.md shape; write a skill. Finish it."
    - Outcome (agent drove, no execution): D19 recorded. Built `synthesize` skill
      (LLM summary + web-search competitors, honest-unavailable), `schema/{summary,
      competitors}.schema.json`, `qcrawl/synth.py` (domain-verify + validators),
      `qcrawl/tech_checks.py` + `tools/tech_checks.py` (deterministic ~15 checks),
      `qcrawl/assemble.py` + `tools/assemble.py` (Python stitch → report.md).
      Tests: test_tech_checks / test_assemble / test_synth. Wired pipeline in
      CLAUDE.md/AGENTS.md; updated wherewefail (honest-unavailable + proxies).

11. *(de-overfit playbooks)* "Playbooks are overfit (tailored to the calibration
    store). Go on the internet, build a knowledge base, rewrite the playbooks
    generic + very rich in context + open-ended, and better the reason skill."
    - Outcome: spawned 5 parallel web-research subagents (one per pillar) → cited CRO
      knowledge (Baymard, NN/g, web.dev, McKinsey, Klaviyo, Recharge, Ahrefs,
      Shopify). Rewrote all 5 playbooks to be generic/framework-driven with labeled
      benchmarks + sources + "how to think"; removed all calibration-store
      references. Strengthened reason skill with a reasoning-discipline section
      (evidence-first, anti-overfit, benchmark-anchored confidence). D20 recorded.

12. *(loophole-1 fix)* "Fix the confidently-wrong-absences loophole ."
    - Outcome (no execution): D21. Added interaction capture to `capture.py`
      (add-to-cart → cart drawer B1; email popup capture+dismiss B4) and tri-state
      signals to `digest.py` (`present`/`absent`/`unverified`); reason skill now bars
      "missing X" claims from `unverified` signals. Tests added. `wherewefail.md`
      interaction-gated item flipped 🔴→🟡 (mitigated).

13. *(Cloudflare fallback)* "gingerpeople.com returns 403 (challenge). Add a stealth
    Playwright fallback like my notes; tell me what's relevant, plan, then do it."
    - Outcome (no execution): D22. Root cause = our UA literally said 'QosmicAuditBot'
      (auto-blocked) + httpx pre-flight gave up before the browser tried. Fixed:
      realistic UA, lightweight stealth (automation flags + init-script patches +
      locale/tz), and browser gate-escalation (httpx challenged → stealth browser
      re-probe → full browser discovery via `seed_surfaces` if it passes, else honest
      blocked/dead). Added `--proxy` + `--no-stealth`. wherewefail Cloudflare → 🟡.

14. *(zenrojas run debrief)* "Why did the first agent take so long — only the
    summary? And why the errors in generating the report?"
    - Answers: (1) the long block was the REASON phase (vision screenshots + large
      HTML + generating 13 experiments), not the summary. (2) Errors were inline
      `python -c` PowerShell quoting + qcrawl import-path from repo root — not
      harness logic; the pipeline produced 10 valid experiments + valid synth.
    - Fix (D23): added `tools/select.py` + `tools/synth_check.py`; skills now call
      these CLIs instead of inline Python; playbook filenames documented lowercase.

15. *(eval harness — headline)* "Implement this layered eval (provided design): gates
    + vector + grounded checks + comparator + meta-validation + self-improving loop.
    Python+API for the judge. Record in docs."
    - Outcome (no execution): D24 (supersedes D3). Built the `eval/` package —
      loader, structural, grounding (citation-existence), coverage (uses pillars
      preset), judge (caged LLM, graceful-unavailable), score (gates→vector→scalar),
      compare, validate_eval; `tools/eval.py` CLI + `eval/results/`; `test_eval.py`
      (deterministic). Wrote `EVAL_LOOP.md` (two loops + real-lift gap). Adapted to our
      schema; added `anthropic` (lazy). wherewefail Phase-4 filled in.

16. *(eval as a skill; EVAL_LOOP is mine)* "Make the judge a skill not an API dep;
    don't write EVAL_LOOP.md (I'll write it); invoke it as 'evaluate <run>'."
    - Outcome (no execution): D25. Deleted my EVAL_LOOP.md draft (user authors it).
      Removed anthropic from requirements. judge.py now agent-driven: `build_tasks`
      (caged tasks) + `from_agent_verdicts` (fold in); scripted API path optional/lazy.
      `tools/eval.py` emits judge_tasks.json + accepts `--judge`. New
      `.claude/skills/eval/SKILL.md` → "evaluate evidence/<run>". Tests added.

*(append new prompts here as the build proceeds)*

## 3. Agent-drove vs. took-the-wheel

| Task | Driver | Why |
|---|---|---|
| Reading brief + reverse-engineering `target_report.md` bar | **Me & agent** | Mechanical read + pattern extraction; agent surfaced the schema + bar quickly. |
| Architecture decision (hybrid harness) | **Me** | Core taste call — chose hybrid over pure-skills / pure-custom. |
| Crawl mechanism & eval shape | **Me (deferred)** | Held open deliberately; agent recorded recommendations to decide at impl start. |
| Scaffolding the tracking docs | Agent | Boilerplate structure; I steer content via review. |

## 4. Notes & observations

- The reference audit (`target_report.md`) was explicitly **"browser-first"** and
  honestly marked many technical checks as `Warn — not inspected`. That's a gap we
  can *beat* by actually fetching sitemap/robots.txt and checking SSL over HTTP.
- Evidence in the sample is literal screenshot **paths**, which is what pushes us
  toward real screenshot capture (see D2).
- Pillar distribution in the sample skews Conversion (4/10) but covers all 5 — our
  harness should enforce ≥1 per pillar while allowing a justified skew.
