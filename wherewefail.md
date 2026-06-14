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
  everything: caps are `--max-fetch 40` (discovery) and `--max-capture 15`
  (capture), with per-category limits (≈3 products). → *Long-tail / per-SKU issues
  on un-sampled products are missed.* This is by design (representative coverage),
  but it means "no issue found" ≠ "no issue exists" across the full catalog.
- 🟡 **Orphan pages.** BFS only finds linked pages (+ seeded functional routes). A
  valid landing page linked from nowhere (email/ads only) won't be discovered.

### Access / blocking
- 🟡 **Password-protected store.** Detected up front; we capture the homepage as
  proof and exit with `status=blocked:password`. → *We cannot audit anything behind
  the gate — the report will be near-empty by necessity.*
- 🟡 **Cloudflare / bot protection.** Detected and recorded. A real browser may
  pass mild challenges, but an aggressive WAF can block even Playwright. → *Audit
  may degrade to homepage-only; httpx discovery under-performs under CF (mitigated
  by browser-fallback discovery, not eliminated).*
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
- 🔴 **Interaction-gated content.** We capture static loaded states only — no
  clicking. Mega-menus, "load more", accordions, quick-view modals, cart drawers,
  and content behind tabs are **not** expanded/captured.
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

## Phase 2 — Reason *(not built yet — anticipated)*
- 🔴 **Hallucinated findings.** Reasoning could assert issues not grounded in
  captured evidence. *Planned mitigation: every claim must cite a manifest path;
  eval enforces it.*
- 🟡 **Evidence ceiling.** Reasoning is only as good as what Crawl captured — gaps
  above propagate (can't flag a leak on a page we never saw).
- 🟡 **Pillar balance.** Forcing 2 experiments/pillar may produce weak ones for a
  store whose real problems cluster in one pillar.

## Phase 3 — Write *(not built yet — anticipated)*
- 🟡 **Schema/format drift** vs `target_report.md` (exp-id uniqueness, required
  fields). *Planned mitigation: deterministic eval checks.*

## Phase 4 — Eval *(not built yet — anticipated)*
- 🟡 **LLM-judge variance / generality** across unseen stores; rubric calibration
  drift. *Planned mitigation: versioned rubric + programmatic floor.*

---

_Last updated: 2026-06-14 (Phase 1 resilience pass + D11 dead-site health gate)._
