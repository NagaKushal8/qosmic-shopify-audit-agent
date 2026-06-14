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
