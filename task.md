# Task Tracker

> Systematic list of everything we accomplish, in order. Source of truth for "what's
> done / what's next." Decisions + reasoning live in [decision.md](decision.md).
>
> **Legend:** `[ ]` todo · `[x]` done · `[~]` changed/superseded.
> **Change convention:** when a task changes, keep the original line, append
> `→ **changed: <what we used instead>**`, and put the **reason** on the line beneath.
> Nothing gets deleted — we keep the trail.

---

## Phase 0 — Setup & planning
- [x] T0.1 — Read brief + reverse-engineer `target_report.md` bar
- [x] T0.2 — Scaffold tracking docs (`plan.md`, `decision.md`, `AGENT_LOG.md`)
- [x] T0.3 — Discuss + fixate crawl approach (no MCP, Python + skill, agent-driven)
- [x] T0.4 — Create `task.md` (this file)

## Phase 1 — Crawl (current focus)
### 1a. Python crawl tool (`tools/`)
- [x] T1.0 — Reproducible env: pinned `requirements.txt` + idempotent `tools/setup_env.py` (venv + chromium). **Verified: env builds, marker written.**
- [x] T1.1 — `tools/crawl.py` CLI orchestrator — robots → discovery → select → capture → manifest; output to `evidence/<domain>_<timestamp>/` (fresh ordered run folder each run)
- [x] T1.2 — `robots.py` — fetch + parse robots.txt → **changed: parse for `Crawl-delay` + "robots present" tech-check ONLY; do NOT gate/prune BFS on `Disallow`**
      - Reason: polite-only policy (see decision.md D7). Shopify's default robots.txt disallows /cart, /checkout, /account, /search — the CRO-critical surfaces. Gating on Disallow would skip exactly the findings the audit exists for (e.g. the reference's /cart 404). We still fetch robots.txt to (a) honor `Crawl-delay` and (b) report "robots.txt present" as a tech check — we just don't use it to prune.
- [x] T1.3 — `sitemap.py` → **changed (twice): now `discovery.py` = BFS-only, no sitemap dependency** ✅ built + tested
      - ~~v1: union of sitemap + conventional routes + nav extraction + BFS fallback~~
      - **v2 (current):** **BFS-only** discovery (see decision.md D6). No reliance on `sitemap.xml` at all (it's non-exhaustive and may be absent on headless/password-protected stores). Mechanics: seed the frontier with **homepage + a small set of known functional routes** (`/cart`, `/checkout`, `/search`, `/collections/all`, `/account/login`) so unlinked-but-critical surfaces are still reached; then BFS same-host only (normalize `www`, off-host links recorded not crawled), bounded **max-depth 3** + page caps, throttled (rate-limit + `Crawl-delay`). Nav/footer links are captured naturally by BFS link extraction. Categorize discovered URLs by Shopify path patterns (`/products/`, `/collections/`, `/pages/`, `/blogs/`) → sample representative set within caps.
- [x] T1.4 — `capture.py` — Playwright: navigate (load→domcontentloaded fallback), desktop + mobile full-page screenshots, rendered HTML, meta extraction (title/desc/canonical/OG/JSON-LD/h1s/favicon)
- [ ] T1.5 — `tech_checks.py` — SSL, HTTPS redirect, sitemap/robots present, meta tags, structured data, favicon, broken links, etc. *(deferred — after user's edge-case round)*
- [x] T1.6 — `manifest.py` — build/write `manifest.json` (citation backbone)
- [x] T1.7 — `crawl.py` orchestrator — wired all phases, caps, politeness delay
- [x] T1.8 — Edge-case handling → **resilience pass complete (D9, 5 fixes): (1) always-write manifest + top-level guard, (2) browser-crash relaunch + launch-failure fallback, (3) store-level password/CF gate detection → homepage-only + clean exit, (4) browser-fallback discovery for JS-rendered/CF stores, (5) hydration networkidle settle + discovery retry/backoff on 429/transient.** Residual limits tracked in `wherewefail.md`.
- [x] T1.8b — `qcrawl/health.py` dead-site health gate (D11): pre-flight homepage gate (unreachable/5xx/hard+soft 404 w/ retries) + post-discovery reachability gate; wired into `crawl.py` with early-exit + always-manifest. **Tests in `test_health.py` (user runs).**
- [ ] T1.8c — Tests for browser-level resilience paths (relaunch, fallback discovery, settle) — still pending

### 1b. Tests (`tools/tests/`)
- [x] T1.9 — pytest setup (`pytest.ini`, `pythonpath=tools`) + respx mocking
- [~] T1.10 — Unit tests per edge case → **done for robots + discovery (29 passing): off-host exclusion, error nodes, seed inclusion, max-fetch cap, sampling caps, UA-group fallback. Remaining: capture + tech-checks edge cases (built with those modules).**
- [ ] T1.11 — Integration smoke test against a real test URL (or recorded fixture)

### 1c. Crawl skill
- [ ] T1.12 — `.claude/skills/crawl/SKILL.md` — document the helper interface for the agent
- [ ] T1.13 — `CLAUDE.md` / `AGENTS.md` entry point (contract + pipeline order + skill pointers)

### 1d. Validate crawl end-to-end
- [ ] T1.14 — Run crawl on `gingerpeople.com`, inspect manifest + artifacts
- [ ] T1.15 — Run crawl on `zenrojas.com`, confirm it generalizes

## Phase 2 — Reason (generation) — BUILT (user to run)
### 2a. Deterministic foundation (`tools/`)
- [x] T2.1 — `qcrawl/pillars.py` — preset Shopify surface→pillar map (D12)
- [x] T2.2 — `qcrawl/digest.py` — CRO-signal extraction per category (price/add-to-cart/reviews/variant/qty/cta/email/empty-cart/tiles/filters/perf), generic + defensive
- [x] T2.3 — `qcrawl/digest.py` builder + `tools/digest.py` CLI — read run folder → write `digest/digest.json` + per-pillar `<pillar>.md` + `summary.md` (NON-destructive, D14)
- [x] T2.4 — `qcrawl/experiments.py` — schema validator + `make_exp_id` + report-set checks (count=10, 5 pillars, unique ids, evidence-path)
- [x] T2.5 — tests: `test_digest.py` + `test_experiments.py` (**user runs**)

### 2b. Agent layer (skills + entry point)
- [x] T2.6 — `.claude/skills/crawl/SKILL.md` — setup_env + crawl.py + digest.py + health-gate handling
- [x] T2.7 — `.claude/skills/reason/SKILL.md` — 5 pillar passes + two-pass self-correction + reduce + schema
- [x] T2.8 — `CLAUDE.md` + `AGENTS.md` entry point — pipeline order + quality bars + skill pointers
- [x] T2.9 — `wherewefail.md` updated with Reason-phase limitations

### 2c. Selection + structured outputs (D15)
- [x] T2.11 — `experiments.select_experiments` — coverage-floor + confidence-greedy fill (open-ended, ceiling 4)
- [x] T2.12 — `schema/experiment.schema.json` — structured-output contract for pillar agents
- [x] T2.13 — reason skill updated: open-ended generation, JSON structured output, deterministic selection+validation
- [x] T2.14 — tests for selection (`test_experiments.py`) — user runs

### 2d. Pillar specialization (D16) — DONE
- [x] T2.15 — `reason/SKILL.md` refactored: each pass loads its playbook (specialist, not loop)
- [x] T2.16 — created all 5 `reason/playbooks/*.md` — rich per-pillar prompts

### 2e. De-overfit + research-back the playbooks (D20) — DONE
- [x] T2.17 — web research (5 parallel agents): CRO best practices/benchmarks per pillar (Baymard, NN/g, web.dev, McKinsey, Klaviyo, Recharge, Ahrefs, Shopify…)
- [x] T2.18 — rewrote all 5 playbooks: generic + framework-driven, removed store-specific overfit, added labeled benchmarks (authoritative vs rule-of-thumb) + sources + "how to think"
- [x] T2.19 — strengthened `reason/SKILL.md` with a reasoning-discipline section (evidence-first, no overfit, benchmark-anchored confidence, honest absence)

## Phase 3 — Write = deterministic assembly (D17/D18/D19) — BUILT (user to run)
- [x] T3.1 — `qcrawl/tech_checks.py` + `tools/tech_checks.py` — deterministic ~15 checks from evidence + live probes (sitemap, http→https) → `report/tech_checks.json` (builds deferred T1.5)
- [x] T3.2 — `schema/summary.schema.json` + `schema/competitors.schema.json` (structured-output contracts, D18; both carry `status` for honest-unavailable)
- [x] T3.3 — `.claude/skills/synthesize/SKILL.md` — LLM: summary → `summary.json`, competitors → `competitors.json` (web-search only, domain-verified, no fabrication — D19)
- [x] T3.4 — `qcrawl/synth.py` — domain-verify guard + structured validators (summary/competitors)
- [x] T3.5 — `qcrawl/assemble.py` + `tools/assemble.py` — stitch report/*.json → `report.md` (target_report.md structure, honest on missing sections)
- [x] T3.6 — tests: `test_tech_checks.py` + `test_assemble.py` + `test_synth.py` (**user runs**)
- [x] T3.7 — pipeline wired in `CLAUDE.md`/`AGENTS.md` (crawl→digest→reason→synthesize→tech_checks→assemble); reason caches to `report/experiments.json`
- [x] T3.8 — `wherewefail.md` updated (Write/competitor/tech-check limits + honest-unavailable behavior)

### 2f. Loophole-1 fix — interaction capture + tri-state honesty (D21) — DONE
- [x] T2.20 — `capture.py`: add-to-cart → cart-drawer capture (B1) + email-popup capture & dismiss (B4); new PageEvidence fields + `interactions` dict
- [x] T2.21 — `digest.py`: tri-state signals (`cart_cross_sell`/`cart_free_shipping_bar` from drawer, `email_popup`, verified cross-sell/free-ship on cart page); drawer/popup paths in digest + pillar index
- [x] T2.22 — `reason/SKILL.md`: "unverified ≠ absent" rule — never claim a missing feature from an unobserved signal
- [x] T2.23 — tests for detectors + tri-state in `test_digest.py` (**user runs**)

- [x] T3.9 — `tools/audit.py` one-shot deterministic runner (crawl→digest→tech_checks→assemble in one command)

### 2g. Cloudflare/WAF fallback — stealth + gate-escalation (D22) — DONE
- [x] T2.24 — realistic UA (dropped bot tag) for httpx + Playwright
- [x] T2.25 — lightweight Playwright stealth (launch args + init-script patches + locale/timezone) in `_launch` + `render_homepage_links`
- [x] T2.26 — browser gate-escalation in `crawl.py`: httpx challenged → stealth browser re-probe → full browser-based discovery (`seed_surfaces`) if it passes, else honest blocked/dead
- [x] T2.27 — `--proxy` + `--no-stealth` flags threaded through capture
- [x] T2.28 — `qcrawl/discovery.seed_surfaces` helper for browser-based discovery

### 2h. Ergonomics fix from zenrojas.com run (D23) — DONE
- [x] T2.29 — `tools/select.py` + `tools/synth_check.py` CLIs; reason/synthesize skills call them instead of inline `python -c` (fixes PowerShell quoting + qcrawl import-path errors)
- [x] T2.30 — playbook filenames documented as lowercase (case-sensitive OS portability)

### Validated by a real run
- [x] zenrojas.com end-to-end: 30 surfaces, 13 candidates → 10 valid experiments (all 5 pillars), web-search competitors (4 domains verified), summary — all validated clean. Errors seen were inline-Python ergonomics (now fixed), not pipeline logic.

## Phase 4 — Eval system (HEADLINE) — BUILT (user to run) (D24)
- [x] T4.1 — `eval/loader.py` — read run's structured artifacts (no prose parsing)
- [x] T4.2 — `eval/structural.py` — Layer 1 (schema + sections + pillar_balance)
- [x] T4.3 — `eval/grounding.py` — Layer 2a citation existence (catches hallucinated evidence)
- [x] T4.4 — `eval/coverage.py` — Layer 3 (high-value surfaces × plausible pillars)
- [x] T4.5 — `eval/judge.py` → **changed: judge is agent-driven via the `eval` skill (D25)**; `build_tasks` + `from_agent_verdicts` added; scripted API path kept optional/lazy
      - Reason: user wants the eval consistent with the harness (skill-driven, no API key). `tools/eval.py` emits judge tasks → agent judges → `--judge` folds verdicts in.
- [x] T4.6 — `eval/score.py` — gates → vector → weighted scalar (ranking only)
- [x] T4.7 — `eval/compare.py` — relative scoring (the improvement engine)
- [x] T4.8 — `eval/validate_eval.py` — meta-validation (real > sabotaged)
- [x] T4.9 — `tools/eval.py` CLI + `eval/results/` store
- [x] T4.10 — `test_eval.py` (deterministic layers: balance, citations, coverage, gates, meta-val) — **user runs**
- [x] T4.11 — `.claude/skills/eval/SKILL.md` — "evaluate evidence/<run>" (agent-driven judge, D25)
- [ ] T4.12 — **`EVAL_LOOP.md` — authored by the USER** (agent draft removed per request)
- [ ] T4.13 — user runs eval on the zenrojas run + `--validate`; feedback → iterate

## Phase 5 — Wrap (remaining)
- [ ] sample_output/ — zenrojas + gingerpeople report.md
- [ ] WORKFLOWS.md (≤1 page) + Loom

### Pending
- [ ] T2.10 — user runs crawl+digest+pytest; feedback → iterate
- [ ] Phase 4 (Eval — headline) still to come

## Phase 3 — Write (later)
- [ ] T3.x — write-report skill: emit canonical report + competitor + tech checks

## Phase 4 — Eval system (Part 2, headline, later)
- [ ] T4.x — deterministic checks + LLM-judge rubric + `EVAL_LOOP.md`

## Phase 5 — Wrap (later)
- [ ] T5.x — `WORKFLOWS.md` + Loom + sample_output for both stores
