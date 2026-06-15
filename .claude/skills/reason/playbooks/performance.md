# Pillar playbook — Performance

**Mission:** remove technical and experience friction that ends a session *before*
the shopper reaches a buying decision — speed, errors, mobile, infra hygiene. These
are leaks of mechanics, not merchandising.

## How to think (read this first)
Ground every claim in a **measurable signal** from the evidence (status codes,
`load_ms`, mobile vs desktop screenshots, `tech_checks.json`). Speed→conversion
figures below are **correlational** — use them to *prioritize and size*, not to
*promise* a result; only a controlled test proves a given store's lift. On Shopify,
SSL/sitemap/robots/HTTPS-redirect/canonical are auto-handled — so audit for the
**broken** state, not mere absence.

## Leak patterns to hunt (store-agnostic — with the measurable signal)
- **Slow load / poor Core Web Vitals** — p75 LCP > 2.5s, CLS > 0.1, INP > 200ms.
  Causes: lazy-loaded/unprioritized hero (LCP) image; unsized media/late banners (CLS);
  heavy app JS / long tasks (INP). Signal: `load_ms`, Lighthouse/CrUX, render-blocking flags.
- **Heavy/unoptimized images** — images are ~half of page weight; >70% of pages have an
  image as LCP. Signal: high `image_count`, legacy formats, oversized intrinsic dims.
- **Broken links / 404s / dead cart-checkout** — 4xx/5xx status codes; a dead `/cart` or
  `/checkout` kills conversion directly (and on Shopify can't be fixed via URL Redirects —
  reserved paths → theme/app debug). Signal: any captured page status ≥400.
- **Mobile layout problems** — tap targets <48×48dp, intrusive popups, content shift,
  non-responsive viewport. Signal: compare mobile vs desktop screenshots; missing viewport meta.
- **Broken infra hygiene** — no HTTPS redirect, invalid SSL, missing/blocked sitemap or
  robots, `noindex` on pages meant to rank, missing/duplicate canonical. Signal: tech_checks.
- **Render-blocking / app bloat** — third-party app scripts (~62% of JS on many stores),
  orphaned ScriptTags from uninstalled apps, fast paint but long non-interactive gap.

## Diagnostic questions
- What status code does each key URL return? any 4xx/5xx, 302-should-be-301, redirect chains?
- Do `/cart` and `/checkout` load and complete? (a dead one is a critical, direct-conversion leak)
- p75 LCP/CLS/INP (mobile vs desktop) — pass the good thresholds? is the LCP element a lazy image?
- Mobile vs desktop screenshot: layout breakage, crowded tap targets, popups, content shift?
- SSL valid + HTTP→HTTPS enforced? sitemap reachable (store not password-protected)? canonical correct?
- How many third-party app scripts? orphaned/ghost scripts from uninstalled apps?

## Digest / evidence signals to weight
`load_ms`, `image_count`, page `status` (404/5xx), `blocked`, presence/absence of the
mobile screenshot, and the deterministic `tech_checks.json` (SSL, redirect, sitemap,
broken links, checkout reachable). Performance overlaps heavily with the tech checks —
lean on them.

## KPIs + benchmarks (these are firm — quote them)
- **Core Web Vitals (p75): LCP ≤2.5s good / >4s poor; INP ≤200ms / >500ms poor; CLS ≤0.1 / >0.25 poor** [web.dev, authoritative]. INP replaced FID Mar 2024.
- **Speed→conversion** [authoritative]: Google/Deloitte — a 0.1s mobile speed gain → **+8.4% retail conversions, +9.2% spend**. Portent — 1s loads convert **2.5×** higher than 5s. Google — **53% of mobile visits abandoned if load >3s**. Akamai — 100ms delay → ~7% fewer conversions. (All **correlational** — see "How to think".)
- **Cart abandonment** ~70.2%; "site had errors/crashed" ~12% of abandons [Baymard].

## Lever library
Prioritize/preload hero image + `fetchpriority="high"`, never lazy-load LCP · set
width/height on media + reserve banner space (CLS) · audit/remove unused apps + ghost
scripts, defer non-critical JS (INP) · serve AVIF/WebP responsive images · 301 broken
URLs to relevant pages (no chains) · debug dead cart/checkout · fix SSL/redirect/sitemap/
canonical · mobile tap targets ≥48dp, remove intrusive interstitials.

## Hypothesis + decision-rule framing
> "Based on [observed metric — e.g., p75 mobile LCP 4.2s / `/cart` returns 404],
> [change] will [outcome], measured by [primary metric] with [leading indicator]."

- **Primary:** the metric tied to the fix (mobile CVR, error rate, the CWV value itself).
- **Guardrails:** revenue/session, AOV, CVR, error rate, page load time. Keep the set small.
- Pre-register MDE / power / significance and run the full window; the speed→CVR benchmarks
  size the bet — a controlled before/after proves the lift.

## Remember
Cite the exact status code / `load_ms` / screenshot / tech-check that grounds each
finding. Max 4 experiments. Emit JSON per `schema/experiment.schema.json`; CWV
thresholds are firm so confidence can be high, but frame speed→revenue as correlational.
Generalize — audit for the broken state on Shopify, not mere absence.


