# Decision Log

> Every meaningful decision on this project, with the reasoning behind it.
> **Convention:** append-only. Each entry = **Decision · Reasoning · Status · Date**.
> Don't delete — supersede with a new dated entry and mark the old one `Superseded`.
> Status: `Locked` (decided) / `Open` (recommendation noted, not yet committed) /
> `Superseded`.

---

## D1 — Harness type: Hybrid (Skills + thin crawl helper)
- **Status:** Locked · 2026-06-14
- **Decision:** Build the harness as Claude Code **Skills** (YAML frontmatter +
  progressive-disclosure bodies) + a `CLAUDE.md` entry point, plus a **thin
  Python/crawl helper** for the deterministic crawl + screenshot capture.
- **Reasoning:** The brief's default is skills-for-fastest-iteration; we keep that
  for Reason/Write where output quality is everything. But the "cite everything with
  a screenshot path" bar needs reproducible, deterministic evidence capture — that's
  what the thin crawl helper buys us. Pure-skills risks flaky/hand-waved evidence;
  pure-custom-runtime is over-engineering ("we're not testing infra plumbing").
  Hybrid gets the evidence rigor without the plumbing tax.

## D-format — Report output format: Markdown
- **Status:** Locked · 2026-06-14
- **Decision:** Audit reports are emitted as Markdown (`.md`).
- **Reasoning:** `target_report.md` is Markdown; matching it makes calibration
  direct and diff-able. Brief says styling is irrelevant and `.md`/`.html` is our
  call — Markdown is the lowest-friction path to the content bar that's actually read.

---

## D2 — Crawl / evidence mechanism  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** **Self-contained Python crawl tool, using Playwright as a library
  (NOT an MCP).** Real browser under the hood → screenshots to disk + rendered DOM +
  metadata. HTTP-level checks (robots, sitemap, SSL, redirects) via `httpx`/stdlib.
- **Reasoning:** Three reasons beat the MCP route. (1) **Portability** — the brief
  says "any coding agent"; an MCP-dependent harness only works for agents with that
  MCP configured, a Python tool runs anywhere with one shell command. (2)
  **Testability** — we explicitly want edge-case tests; you can unit-test your own
  script with mocked responses, you can't meaningfully unit-test an MCP server. (3)
  **Determinism** — a scripted tool captures the same surfaces the same way every
  run; an MCP lets the agent improvise (slop risk). Playwright-the-library gives us
  real screenshot paths for the "cite everything" bar without the MCP config tax.

## D4 — Skill/Python split & agent-driven selection  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Crawl *logic* lives in testable Python (`tools/`); a **crawl skill**
  documents how to call it; the **agent decides which surfaces** to capture at
  runtime, while the **Python tool enforces a hard cap** as a backstop.
- **Reasoning:** Skill = the manual, Python = the machine, agent = the operator.
  Keeps reasoning flexible (agent picks surfaces) and mechanics reliable (tool can't
  be talked into crawling 1000 pages). Partial success is success — one bad page
  never kills the audit; it's recorded and the report notes the gap.

## D5 — Entry point: CLAUDE.md / AGENTS.md  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** The runtime bootstraps from `CLAUDE.md` (Claude Code) /
  `AGENTS.md` (Codex) — same content, two filenames. It defines the contract, the
  `Crawl → Reason → Write` pipeline order, and points to the skills. Skills + tools
  are pulled in on demand (progressive disclosure).
- **Reasoning:** It's the one file an agent auto-loads. Agent-agnostic by shipping
  both filenames. Runtime pipeline is Crawl→Reason→Write; the **eval system is a
  separate harness that scores the finished report** — not a phase of the runtime.

## D6 — Discovery: BFS-only, no sitemap dependency  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Surface discovery is **BFS only**. We do **not** rely on
  `sitemap.xml`. Seed the frontier with **homepage + known functional routes**
  (`/cart`, `/checkout`, `/search`, `/collections/all`, `/account/login`), then BFS
  same-host (normalize `www`; off-host links recorded, not crawled), bounded by
  **max-depth 3 + page caps**, throttled. Categorize discovered URLs by Shopify path
  patterns and sample a representative set within caps.
- **Reasoning:** `sitemap.xml` is non-exhaustive (omits functional CRO surfaces,
  unpublished/noindex resources) and not guaranteed present (headless/Hydrogen,
  password-protected, edge-blocked). BFS walks the actual reachable link graph —
  what a real user can get to — which is what matters for CRO. Seeding with known
  functional routes covers unlinked-but-critical surfaces (e.g. `/cart`). Goal is
  *representative coverage of CRO-critical surfaces*, not an exhaustive crawl.
- **Note:** Sitemap could later be added as a cheap *optional seed* for breadth, but
  per user direction it is NOT a dependency. Supersedes earlier "sitemap-first" idea.
- **Functional seed routes (deliberately probed, recorded so they're not lost):**
  `/` (homepage), `/cart`, `/checkout`, `/search`, `/collections/all`,
  `/account/login`. These are seeded into the BFS frontier on top of the homepage
  because several aren't linked in nav/footer yet are CRO-critical (the reference's
  `/cart` 404 lives here). Still pure BFS — just better starting points.
  Additionally `robots.txt` + `/sitemap.xml` are probed for **technical checks only**
  (presence), not for discovery.

## D7 — Robots.txt: polite-only, not a crawl gate  *(LOCKED)*
- **Status:** Locked · 2026-06-14 · **supersedes** the initial "gate every BFS node
  on robots `Disallow`" instruction.
- **Decision:** Fetch + parse robots.txt, but use it **only** to (a) honor
  `Crawl-delay` and (b) report "robots.txt present" as a technical check. **Do NOT
  prune the BFS on `Disallow` rules.** Politeness comes from throttling (rate-limit +
  crawl-delay), same-host scoping, and bounded depth/caps.
- **Reasoning:** Shopify's default robots.txt disallows `/cart`, `/checkout`,
  `/account`, `/search`, and sort/filter collection URLs — the exact functional
  surfaces a CRO audit depends on. Strict gating would skip the highest-value
  findings (the reference audit's headline was a `/cart` 404, which is
  robots-disallowed). robots.txt is a directive for bulk indexing crawlers; we are
  doing bounded, browser-equivalent diagnostics on a store we were explicitly pointed
  at. We stay respectful via throttling, not by skipping the surfaces we're hired to
  inspect.

## D8 — Reproducible environment: pinned venv + idempotent setup  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Ship a pinned `requirements.txt` (exact `==` versions) + an
  idempotent pure-Python `tools/setup.py` that (1) creates `.venv` if missing,
  (2) installs the pinned requirements, (3) runs `playwright install chromium`,
  (4) writes a `.venv/.ready` marker so re-runs are instant. The runtime installs
  the env **before** crawling; the skill + `CLAUDE.md` document this as a mandatory
  Step 0 ("ensure environment, then crawl").
- **Reasoning:** Reproducibility across any machine without assuming Docker. `venv`
  is stdlib (works on win32 + posix, no external dep), pinned versions guarantee
  identical behavior, the Playwright browser binary is version-tied so it's installed
  by setup too. Idempotent + marker file makes it safe for the agent to run every
  time. Documenting it in the skill means the agent knows the contract instead of
  guessing. **Optional upgrade:** a Dockerfile for maximum reproducibility — noted,
  not default (heavier; receiving agent may lack Docker, which conflicts with the
  "any coding agent" portability goal).

## D9 — Crawl resilience & graceful degradation  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** The crawl must always finish with a usable `manifest.json`, even
  under failure. Five hardening measures:
  1. **Never lose a run.** `crawl.py` writes the manifest in a `finally`; a
     top-level guard sets `status="capture_aborted"` instead of crashing.
  2. **Browser-crash recovery.** `capture_surfaces` relaunches the browser once on
     a `PWError` and retries the page; if the browser won't launch at all, every
     surface is recorded as errored (run still produces output).
  3. **Store-level gate handling.** Pre-flight homepage check detects
     password/Cloudflare gates; if gated, capture the homepage only (as proof),
     set `status="blocked:<reason>"`, and exit cleanly instead of grinding through
     identical gated pages.
  4. **Browser-fallback discovery.** If httpx BFS returns near-empty (JS-rendered
     / CF-challenged), re-discover links from the *rendered* homepage via Playwright
     (`render_homepage_links`). Generalizes to headless/Hydrogen stores.
  5. **Hydration settle + retry/backoff.** Capture adds a bounded
     `networkidle` settle so JS-hydrated content is snapshotted; discovery retries
     once with backoff on transient errors / HTTP 429.
- **Reasoning:** Reliability is the product ("no slop, no half-shipped"). A real
  store will eventually hit every one of these; the audit's value is that it
  degrades honestly (records the limitation) instead of failing silently or
  hanging. Known *residual* limitations are tracked in `wherewefail.md`.

## D10 — Maintain `wherewefail.md` (honest limitations doc)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Keep `wherewefail.md` — a per-phase catalog of edge cases we still
  fail or only partially handle — current as the system evolves, and call out
  updates to it in chat when they happen.
- **Reasoning:** Sets realistic expectations and prevents over-claiming. A known,
  documented gap is engineering; a silent one is a bug.

## D11 — Dead-site health gate (don't crawl the uncrawlable)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** A two-tier health gate (`qcrawl/health.py`) lets the crawl abort
  early with an honest status instead of screenshotting a folder of 404s:
  1. **Pre-flight homepage gate** (`probe_homepage`): if the homepage is
     unreachable (conn error/timeout), 5xx, or a hard/soft 404 — after up to 2–3
     retries with backoff — abort with `status=dead:{unreachable|server_error|
     not_found}`, capture the homepage as proof, exit clean. A password/CF page is
     reachable, so it's reported as a *block*, not a death.
  2. **Post-discovery reachability gate** (`assess_reachability`): if every
     discovered page is an error/not-found page, abort with `status=dead_site` and
     skip the capture pass.
- **Reasoning:** User direction — a dead/erroring store shouldn't burn a full
  15-page browser pass and then misreport `status=ok`. Detect non-viability by
  status code AND content ("not found" / soft-404), bounded by retries + BFS depth,
  then stop and tell the user plainly. Manifest is still always written (D9).
- **Tests:** `tools/tests/test_health.py` covers hard/soft 404, 5xx, connection
  failure, healthy, password gate, retry-then-recover, and all-dead assessment.

## D12 — Generation (Reason) architecture: digest-first, signals pre-extracted, HTML on demand  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** The Reason phase does NOT pass raw HTML to the reasoning agents by
  default. Instead:
  1. A deterministic **digest builder** (`tools/qcrawl/digest.py`) reads a run's
     `manifest.json` + saved `page.html`/`meta.json` and **pre-extracts a small set
     of CRO signals** per page (e.g. price present? add-to-cart? reviews? variant
     selector? CTA count? empty-cart? email capture? trust badges?).
  2. A **preset Shopify surface→pillar map** (`tools/qcrawl/pillars.py`) tags each
     page with its 1–3 likely pillars. **Pillars live in the manifest/digest as
     structured fields — NOT encoded in filenames** (many-to-many + rename churn
     make filenames brittle). Folder names stay category-rich for human skim.
  3. Routing is **deterministic** (read the `pillars` field) → a per-pillar index
     (`digest/<pillar>.md`) is the artifact handed to each pillar agent.
  4. **5 pillar agents** (Conversion / AOV / Retention / Acquisition / Performance)
     each reason over their routed digest slice + **screenshots**; they **pull full
     `page.html` on demand** (the agent's Read tool) only when they need proof.
  5. **Two-pass self-correction:** Pass 1 = generate experiments from the routed
     slice. Pass 2 = each agent skims the full lightweight index, flags
     misclassified / cross-relevant pages, pulls only those, and refines.
  6. A **reduce/orchestrator** step dedupes overlapping experiments and enforces the
     final budget (10 experiments, balanced ≈2 per pillar).
- **Reasoning:** Capability isn't the issue — an LLM *can* read HTML. But raw
  Shopify HTML is 150k–400k chars/page; ×30 pages ×5 agents is huge, noisy, and
  non-reproducible. Pre-extracted signals are cheap, **deterministic** (same answer
  every run), and **eval-verifiable** (a fact the eval can check, closing the
  hallucination gap). The screenshot already carries most of what's needed to
  *reason*; the digest makes a few key facts exact + checkable. HTML-on-demand keeps
  the door open for depth without paying for it every time. Deterministic routing
  (preset map) needs no LLM; the two-pass + on-demand fetch absorbs the preset's
  approximation.

## D13 — Capture cap raised 15 → 30  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** `--max-capture` default 15→30, `--max-fetch` 40→60, per-category
  caps bumped (sum ~35) so 30 is the binding limit.
- **Reasoning:** User direction — 15 pages is too thin for a representative audit;
  30 gives the pillar agents more surface coverage while caps still bound huge stores.

## D14 — Digest is a separate, non-destructive step; reduce = deterministic guardrails + agent synthesis  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:**
  - **Digest is a separate command** (`python tools/digest.py evidence/<run>/`), not
    folded into crawl. It **never mutates raw evidence** — it reads
    `manifest.json` + `page.html`/`meta.json` and writes NEW files under
    `evidence/<run>/digest/` (`digest.json`, per-pillar `<pillar>.md`, `summary.md`).
  - **Reduce** = a thin **deterministic validator** (`tools/qcrawl/experiments.py`:
    schema validation, exp-id generation/uniqueness, count=10, all-5-pillars,
    ≈2/pillar) that guards an **agent-driven synthesis** (semantic dedupe + final
    selection lives in the reason skill).
- **Reasoning:** Separate digest = iterate signal logic offline without re-crawling,
  clean separation (capture vs interpret), independently testable, idempotent, and
  raw artifacts stay immutable for citation integrity. Reduce split = counts/coverage
  are objective (Python), but dedupe/"which 10 are best" is semantic (agent); pair
  them so the budget is enforced deterministically while quality stays agent-judged.

## D15 — Open-ended generation + coverage-floor selection + structured outputs  *(LOCKED)*
- **Status:** Locked · 2026-06-14 · refines D12's "≈2 per pillar"
- **Decision:**
  - Pillar agents generate **open-ended** experiment counts with a **hard ceiling of
    4** each — not a fixed 2/pillar quota.
  - **Selection** (`experiments.select_experiments`): Round 1 = top-1 by confidence
    per pillar (guarantees all 5 represented); Round 2 = top-2 per pillar where
    available; then **fill remaining slots to 10 from the highest-confidence global
    leftovers**.
  - **Structured outputs are mandatory:** pillar agents emit a **JSON array** matching
    `schema/experiment.schema.json` (12 fields, `confidence` numeric 0–100). Enforced
    by tool-use/structured-output where the runtime supports it, else schema-in-prompt
    + deterministic validation (`validate_report_set`) + re-ask on failure.
- **Reasoning:** A fixed quota manufactures weak experiments; open-ended + floor lets
  real problem concentration show while still spanning all 5 pillars. Selection needs
  a sortable numeric `confidence`, which *requires* structured output — you can't sort
  or validate prose. Structured JSON also makes every experiment machine-checkable by
  the eval system later.
- **Caveat (logged in wherewefail):** `confidence` isn't calibrated *across* pillar
  agents, so cross-pillar sorting in the fill step is noisy; the eval/judge phase can
  normalize later.

## D16 — Pillar specialization: one reason skill + 5 playbooks (Option B)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Keep a single `reason` skill for shared mechanics (read slice →
  screenshot → structured JSON → two-pass → select), and add five rich, tunable
  **pillar playbooks** (`.claude/skills/reason/playbooks/{conversion,aov,retention,
  acquisition,performance}.md`) injected per pass. Each playbook carries the
  pillar's leak patterns, KPIs, which digest signals to weight, and hypothesis /
  decision-rule templates.
- **Reasoning:** Running one generic prompt 5× is a loop, not 5 specialists. We
  already split the *data* per pillar; this splits the *prompt* per pillar too —
  deep specialization with DRY mechanics and per-pillar tunability. Avoids the
  duplication and relevance-invocation awkwardness of 5 full skills (rejected
  option A).

## D17 — Write = deterministic assembly, not an LLM writer  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** No monolithic "writer" agent. The LLM produces *data*; Python
  *assembles* the report. Per-run structured files in `report/`:
  - `experiments.json` — LLM (reason agents)
  - `summary.md` — **LLM** (executive-summary prose, via a small `synthesize` skill)
  - `competitors.json` — **LLM** (competitor analysis, structured)
  - `tech_checks.json` — **Python** (`tools/tech_checks.py`, deterministic from
    evidence + light HTTP probes; finally builds the deferred T1.5 — and beats the
    reference's "not inspected" Warns)
  - `report.md` — **Python** (`tools/assemble.py`, templating to the
    `target_report.md` structure; no LLM, no formatting drift)
- **Reasoning:** Determinism where possible; LLM only where judgment/world-knowledge
  is required (experiments, summary, competitors). Assembly is mechanical → make it
  reproducible Python, which also guarantees the final structure can't drift.

## D18 — Structured outputs everywhere until final assembly  *(LOCKED — guiding principle)*
- **Status:** Locked · 2026-06-14
- **Decision:** Every inter-stage handoff is a **validated structured artifact**
  (JSON with a schema in `schema/`), all the way to the final stage. The ONLY
  prose-rendered artifact is `report.md`, produced deterministically by `assemble.py`
  from the structured files. Each LLM step (experiments, summary, competitors) emits
  to its schema, validated before the next stage consumes it; re-ask on failure.
- **Reasoning:** User priority — the final report structure is critical, so we
  protect it by keeping data machine-checkable end-to-end and only rendering prose at
  the very last, deterministic step. Structured-everywhere also makes every stage
  eval-verifiable later.

## D19 — Competitor = web-search only (no fabrication); honest-unavailable everywhere  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:**
  - Competitor analysis uses **web search only** (option B). **No fallback to
    pure-LLM world knowledge.** If no web-search tool is available, the section is
    written as `status:"unavailable"` with an honest note — never fabricated.
  - The executive summary likewise marks `status:"unavailable"` if it can't be
    synthesized validly. `assemble.py` renders the honest note for any unavailable
    section instead of inventing content.
  - A deterministic **domain-verify guard** (`synth.verify_domains`) drops competitor
    domains that don't resolve (kills hallucinated domains).
  - Cached structured artifacts per run live in `evidence/<run>/report/`:
    `experiments.json`, `summary.json`, `competitors.json`, `tech_checks.json`.
    `tools/assemble.py` stitches them into `report.md` (target_report.md structure),
    deterministically, every time, in fixed order.
- **Reasoning:** User principle — fabricating competitors and shipping them is
  dishonest; better to state plainly that the config couldn't produce a section.
  Honest "unavailable" is recorded in `wherewefail.md`. Web-search grounding +
  domain-verify is what makes competitor analysis generalize to unseen stores
  without hallucinating.

## D20 — Generic, research-backed pillar playbooks   *(LOCKED)*
- **Status:** Locked · 2026-06-14 · refines D16
- **Decision:** The 5 pillar playbooks are rewritten to be **generic and
  framework-driven**, grounded in real CRO research (Baymard, NN/g, Google web.dev,
  McKinsey, Klaviyo, Recharge, Smile.io, Ahrefs, Shopify, etc.). Each playbook =
  mission · "how to think" (evidence-first, anti-overfit) · store-agnostic leak
  patterns with on-page signals · diagnostic questions per surface · KPIs +
  **labeled benchmarks** (authoritative vs rule-of-thumb) · lever library ·
  hypothesis + decision-rule framing with guardrails · sources. The reason skill
  gained a **reasoning-discipline** section (evidence-first not template-first, no
  overfit, benchmark-anchored confidence, honest absence).
- **Reasoning:** The earlier playbooks were overfit — they named the calibration
  store and baked in its specific experiments, which would bias every audit and fail
  to generalize. Open-ended, research-backed playbooks tell the LLM *how to
  interrogate evidence* (and give real numbers to calibrate confidence/lift),
  which is what makes the output defensible vs. "an LLM doing a vibe search."
  Research gathered via 5 parallel web-research subagents; benchmarks labeled by
  source quality so the LLM doesn't over-claim.

## D21 — Interaction capture + tri-state signals (fix "confidently-wrong" absences)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Two complementary fixes for the crawl's biggest credibility risk —
  asserting a feature is "missing" when it's merely interaction-gated:
  1. **Tri-state signals (Fix A):** interaction-dependent signals are
     `present | absent | unverified` (not binary). `unverified` = never observed. The
     reason skill forbids proposing a "missing X" experiment from an `unverified`
     signal — downgrade or verify instead.
  2. **Interaction capture (Fix B):** Playwright drives a few generic, best-effort
     Shopify recipes during capture: **B1** add-to-cart → screenshot + DOM of the
     **cart drawer** (where cross-sell / free-shipping bars live), and **B4**
     screenshot-then-dismiss the **email popup/modal**. Artifacts: `drawer.png`,
     `drawer.html`, `popup.png`. The digest turns these into verified tri-state
     signals (`cart_cross_sell`, `cart_free_shipping_bar`, `email_popup`).
- **Reasoning:** A static, logged-out, no-interaction snapshot can't see Shopify's
  most important conversion surfaces (cart drawer, modal, mega-menu), so a binary
  `absent` produces confidently-wrong "you're missing X" findings — the fastest way to
  lose merchant trust. Capturing the interaction fixes the *data*; tri-state + the
  skill rule fix the *epistemics*, so when a best-effort recipe fails (theme variance)
  the worst case is "less complete," never "wrong." No order is ever placed
  (add-to-cart only; checkout never completed).

## D22 — Stealth + browser gate-escalation (Cloudflare / WAF fallback)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Three changes so bot-protected stores don't dead-end the crawl:
  1. **Realistic UA** — dropped the `QosmicAuditBot` tag from httpx + Playwright. A
     *declared* bot is auto-blocked by WAFs; this was self-sabotage.
  2. **Lightweight stealth** — Playwright launches with
     `--disable-blink-features=AutomationControlled` and an init-script patching
     `navigator.webdriver` / `window.chrome` / `navigator.languages` / `plugins`, plus
     realistic locale/timezone. Default on (`--no-stealth` to disable).
  3. **Browser gate-escalation** — when the httpx pre-flight is challenged
     (Cloudflare always blocks JS-less httpx) or fails, we **re-probe with the stealth
     browser** before concluding. If the browser passes → full browser-based discovery
     (`seed_surfaces` from the rendered homepage). Only if the browser *also* fails →
     honest `blocked:challenge` (homepage proof) or `dead`. Added `--proxy` passthrough
     for IP-level blocks.
- **Reasoning:** gingerpeople.com returned 403 on every page — partly because we
  announced ourselves as a bot, and partly because the httpx gate gave up before the
  real browser tried. Stealth + escalation gives the browser a fair shot; password
  pages still aren't bypassed (real gate); and the honesty rule holds — a hard WAF
  that beats stealth is reported as `blocked`, never fabricated. Stealth is applied to
  audit storefronts the operator explicitly chose.

## D23 — Ship CLIs for reduce/synth steps (no inline shell Python)  *(LOCKED)*
- **Status:** Locked · 2026-06-14
- **Decision:** Add `tools/select.py` (select + exp-ids + validate) and
  `tools/synth_check.py` (domain-verify + validate competitors/summary). The reason
  and synthesize skills now call these CLIs instead of suggesting inline
  `python -c "..."`. Also documented playbook filenames as lowercase.
- **Reasoning:** A real zenrojas.com run surfaced repeated failures where the agent
  hand-wrote inline Python through PowerShell: quotes/f-strings/`%` broke the shell
  (unterminated string / invalid syntax), and a temp script run from repo root hit
  `ModuleNotFoundError: qcrawl` (our `pythonpath=tools` is pytest-only). The pipeline
  logic was fine — the ergonomics weren't. CLIs that self-insert the path (like the
  other `tools/*.py`) remove both failure modes and are cross-shell safe. (Pillar
  playbook casing fixed for case-sensitive OS portability.)

## D3 — Eval system shape  *(OPEN — headline deliverable)*
- **Status:** Open · 2026-06-14 · settle at start of Part 2
- **Recommendation:** **Hybrid** — deterministic checks + LLM-judge rubric.
  - *Deterministic:* exactly 10 experiments? all 5 pillars present? every evidence
    path/URL resolves? schema complete per experiment? competitor table 3–4 rows?
    ~15 tech checks with valid statuses?
  - *LLM-judge:* hypothesis quality, evidence-claim grounding, exec-summary prose,
    competitor insight, pillar-fit — scored against a versioned rubric.
- **Reasoning:** Deterministic checks are objective, fast, reproducible, and catch
  the easy failures; the LLM-judge catches "is this a *good* experiment" which is
  where the real signal is. The hybrid is also what makes the loop self-improving:
  rubric + judge prompt are versioned artifacts the system can refine. Pure-judge =
  not reproducible; pure-deterministic = blind to reasoning quality. This must
  generalize to unseen stores, so checks are store-agnostic by construction.
