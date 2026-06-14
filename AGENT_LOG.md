# AGENT_LOG.md

> Required deliverable. Tracks: **time per part**, **prompts fed to the agent**, and
> **where the agent drove vs. where I took the wheel**. Updated continuously.
> Timebox: ~4h target, **5h hard ceiling**.

## 1. Time log

| Part | Task | Start | End | Elapsed |
|---|---|---|---|---|
| Setup | Read brief + `target_report.md`, lock initial decisions | 2026-06-14 — | — | ~0.1h |
| Setup | Scaffold tracking files (plan / decision / agent log) | — | — | ~0.1h |
| Part 1 | Runtime harness | — | — | — |
| Part 2 | Eval system + autonomy plan | — | — | — |
| Wrap | WORKFLOWS.md + Loom | — | — | — |
| **Running total** | | | | **~0.2h / 5h** |

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

4. *(implement crawl)* "Never run tests/code on your own — I run it. Build the full
   crawl: URL in → discover pages → visit → screenshot + HTML + metadata for all
   pages → output under an `evidence/` folder, a fresh ordered run folder per run.
   Tell me when done; I'll run it, then give more edge cases."
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

6. *(dead-site gate)* "Don't just document it — solve it: after extracting pages,
   detect 404/error/'not found', stop after retries/depth when pages aren't
   reachable; bail with a clear 'server down/error' message. Cover in flow + tests."
   - Outcome: built `qcrawl/health.py` two-tier gate (D11) — pre-flight homepage
     (unreachable/5xx/hard+soft-404 w/ retries) + post-discovery reachability;
     wired into `crawl.py` with early-exit + always-manifest; `test_health.py`
     added (offline). Flipped the dead-site item in `wherewefail.md` to handled.

*(append new prompts here as the build proceeds)*

## 3. Agent-drove vs. took-the-wheel

| Task | Driver | Why |
|---|---|---|
| Reading brief + reverse-engineering `target_report.md` bar | Agent | Mechanical read + pattern extraction; agent surfaced the schema + bar quickly. |
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
