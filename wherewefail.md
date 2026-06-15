# Where We Fail — honest limitations & realistic expectations

> A living catalog of edge cases this harness **fails** or only **partially**
> handles, organized by phase. The goal is honest expectations, not excuses: a
> documented gap is engineering; a silent one is a bug. Updated as the system
> evolves (decision D10) — changes are also flagged in chat.
>
> **Legend:** 🟢 handled · 🟡 partial / degrades gracefully · 🔴 not handled.

---

## Phase 1 — Crawl (built)

### Coverage / sampling
- 🟡 **Large catalogs (e.g. 800 products).** We **sample**, we don't audit
  everything: caps are `--max-fetch 60` (discovery) and `--max-capture 30`
  (capture), with per-category limits (≈3 products). → *Long-tail / per-SKU issues
  on un-sampled products are missed.* This is by design (representative coverage),
  but it means "no issue found" ≠ "no issue exists" across the full catalog.
- 🟡 **Orphan pages.** BFS only finds linked pages (+ seeded functional routes). A
  valid landing page linked from nowhere (email/ads only) won't be discovered.

### Access / blocking
- 🟡 **Password-protected store.** Detected up front; we capture the homepage as
  proof and exit with `status=blocked:password`. → *We cannot audit anything behind
  the gate — the report will be near-empty by necessity.*
- 🟡 **Cloudflare / bot protection (mitigated, D22).** We now use a realistic UA
  (no bot tag), lightweight Playwright stealth (automation flags patched), and
  **browser gate-escalation**: when the httpx pre-flight is challenged we re-probe
  with the stealth browser and, if it passes, run a full browser-based crawl. A
  `--proxy` flag helps with IP-level blocks. STILL: an aggressive WAF (managed
  challenge / advanced fingerprinting) can beat lightweight stealth — then we report
  `blocked:challenge` honestly (homepage proof), never fabricate. Heavier escalations
  (residential proxy rotation, persistent real-profile, cookie injection) are
  possible but not built.
- 🔴 **IP / rate-based blocking on repeated runs.** No proxy rotation; running many
  audits from one IP may get throttled or blocked.
- 🟢 **Dead / down / all-404 site (D11).** Two-tier health gate: pre-flight homepage
  check (unreachable / 5xx / hard+soft 404, with retries) and post-discovery
  reachability check (every page an error). On failure we abort early, capture the
  homepage as proof, and report `status=dead:*` / `dead_site` instead of grinding
  through 404s and misreporting `ok`.

### Rendering / interaction
- 🟡 **Slow / never-completing JS hydration.** We wait for a bounded `networkidle`
  settle, then snapshot. → *Very slow or infinite-spinner pages may be captured
  pre-hydration (skeleton state).*
- 🟡 **Interaction-gated content (partially mitigated, D21).** We now drive a few
  best-effort recipes: **add-to-cart → cart drawer** (cross-sell / free-shipping bar)
  and **email popup** capture. Signals from these are **tri-state** (`present` /
  `absent` / `unverified`), and the reasoner is barred from claiming a feature is
  "missing" from an `unverified` signal — so a static snapshot can no longer produce a
  confidently-wrong "you're missing X". STILL uncaptured: mega-menus, "load more",
  accordions, quick-view modals, tabbed content; and recipes are theme-brittle (when a
  selector misses, the signal stays `unverified`, never falsely `absent`).
- 🟡 **Cookie/consent & promo overlays.** May obscure screenshots; we don't
  auto-dismiss them.

### Representativeness
- 🔴 **Personalization / geo / currency / A/B tests.** We capture one variant, from
  one IP/locale, logged-out. → *Not representative of all users; geo-priced or
  experiment-bucketed experiences differ.*
- 🔴 **Authenticated surfaces.** `/account`, order history, wishlists — we're never
  logged in, so these are uninspectable.
- 🟡 **Checkout funnel.** We reach `/cart` and check `/checkout` reachability, but
  we **do not place orders** — steps beyond the first checkout screen are uninspected.

### Robustness (mitigated by D9, residuals noted)
- 🟢 Page never loads → timeout + load→domcontentloaded fallback, recorded, non-fatal.
- 🟢 Playwright crash → relaunch once + always-write manifest.
- 🟢 Mobile screenshot fails → isolated, desktop unaffected.
- 🟡 **Crawl-delay honored only up to `--max-delay` (default 1.5s).** A store asking
  for a 10s delay is not fully honored (speed vs politeness tradeoff).
- 🟡 **Category heuristics assume Shopify URL conventions** (`/products/`,
  `/collections/`…). Heavily customized routing or non-Shopify stores may be
  mis-categorized.

---

## Phase 2 — Reason (digest + 5-agent generation; built)
- 🟡 **Digest signals are heuristics, not truth.** `price_present` /
  `add_to_cart_present` / `reviews` etc. use generic DOM + regex rules. They can
  **false-positive** (e.g. "$5 shipping" reads as a price) or **false-negative**
  (unusual theme markup). Mitigation: they're *hints* — the pillar agent confirms
  against the screenshot and pulls HTML on demand. Still, a wrong signal can mislead.
- 🟡 **Routing is approximate.** The preset surface→pillar map is fixed; a page's
  real best pillar may differ. Mitigation: Pass-2 self-correction lets agents pull
  cross-relevant pages — but a badly misrouted page could still be under-weighted.
- 🟡 **Reduce/dedup is agent-judged.** Count/pillar-coverage + the selection
  algorithm are deterministic (`experiments.py`), but semantic dedupe ("are these two
  the same experiment?") relies on agent judgment → run-to-run variance.
- 🟡 **Confidence isn't calibrated across pillars (D15).** Selection's fill step sorts
  candidates from different pillar agents by `confidence`, but an 80% from the
  Conversion agent ≠ 80% from the Performance agent. The fill order is therefore
  noisy. *Planned: the eval/judge phase normalizes confidence across agents.*
- 🟡 **Forced pillar balance.** Targeting ≈2/pillar can yield a weak experiment for a
  pillar where the store has few real problems (we allow a justified skew, but the
  "all 5 present" rule can still stretch a thin pillar).
- 🟡 **Evidence ceiling.** Reasoning is only as good as what Crawl captured — every
  Crawl limitation above propagates (can't flag a leak on a page we never saw).
- 🔴 **Residual hallucination risk.** Citation is *required* by the skill and
  evidence paths are validated to be paths/URLs, but we don't yet verify the cited
  artifact actually supports the specific claim. *Planned: the eval system closes this.*

## Phase 3 — Write = deterministic assembly (built)
- 🟢 **Format drift** vs `target_report.md` — eliminated: `assemble.py` renders the
  fixed structure deterministically from structured JSON; no LLM in assembly.
- 🟡 **Competitor analysis requires a web-search tool.** If none is available, the
  section is honestly marked `unavailable` (not fabricated). So a run without web
  search ships **no competitor table** — by design (D19). Honest, but a gap.
- 🟡 **Competitor grounding is search-snippet-deep, not crawl-deep.** We don't crawl
  competitors; positioning/"what they make easier" rests on search results + model
  reasoning. Domain-verify only confirms the domain resolves, not the claims.
- 🟡 **Tech-check page speed is a proxy.** "Page Speed" uses navigation timing
  (`load_ms`), not a real Lighthouse run — flagged in the detail text. Image
  optimization counts images but doesn't measure bytes.
- 🟡 **Executive summary can be `unavailable`** if the LLM can't synthesize a valid
  structured summary — rendered as an honest note rather than faked.

## Phase 4 — Eval system (built, D24)
- 🟢 **Hallucinated evidence** — caught deterministically (citation existence + a hard
  gate); can't be averaged away.
- 🟡 **Grounding/genericness are agent-judged (D25).** Done via the `eval` skill (no
  API key). If the eval is run as bare `tools/eval.py` without the agent doing the
  judge step, those two dims stay `unavailable` and the scalar uses the deterministic
  dims only (honest, thinner signal).
- 🟡 **Grounding judge variance.** Even caged to yes/no, the vision judge can be wrong
  on ambiguous screenshots; single-vote (no N-way adversarial verify yet).
- 🟡 **Coverage is per surface-TYPE, not per-page**, and "plausibly applies" is the
  fixed preset map — a legitimately-barren surface can still flag as a gap.
- 🟡 **Scalar weights are a judgment call** (grounding 0.40, …), validated only against
  a sabotaged copy — not learned from outcomes.
- 🔴 **Real lift is not measured.** The eval scores "is the finding true/grounded," NOT
  "would shipping it win." True north star needs merchant A/B outcomes fed back — the
  thing that closes the loop for real (named in EVAL_LOOP.md).

---

_Last updated: 2026-06-14 (D24 eval system — layered, vector-first; real-lift gap named)._
