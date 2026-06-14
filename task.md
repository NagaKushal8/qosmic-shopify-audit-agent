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

## Phase 2 — Reason (later)
- [ ] T2.x — reasoning skill: find revenue leaks across 5 pillars, build 10 experiments

## Phase 3 — Write (later)
- [ ] T3.x — write-report skill: emit canonical report + competitor + tech checks

## Phase 4 — Eval system (Part 2, headline, later)
- [ ] T4.x — deterministic checks + LLM-judge rubric + `EVAL_LOOP.md`

## Phase 5 — Wrap (later)
- [ ] T5.x — `WORKFLOWS.md` + Loom + sample_output for both stores
