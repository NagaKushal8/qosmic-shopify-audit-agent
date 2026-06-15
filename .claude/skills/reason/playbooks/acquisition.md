# Pillar playbook — Acquisition

**Mission:** attract and convert *new* visitors via organic discoverability (SEO),
content, and intent-matched landing. Upstream of cart/checkout CRO.

## How to think (read this first)
The master rule: **page type must match search intent type.** Informational queries
("how to…") want content; commercial ("best X", "X vs Y") want comparison/collection;
transactional ("buy X") want PDP/collection; navigational (brand) want home. A
transactional query landing on a blog post leaks; an informational query on a bare PDP
leaks. SEO is **slow-feedback and compounding** — separate fast levers (meta, content
links: judge in weeks) from slow bets (new pages, clusters: 3–6+ months). Reason from
what the store actually has (its meta tags, JSON-LD, blog, homepage copy).

## Leak patterns to hunt (store-agnostic)
- **Weak/templated meta** — Shopify default appends store name to every title (pushes
  keyword past ~60-char cutoff); missing/duplicate descriptions. (Meta doesn't rank but
  drives CTR; #1 organic ~27.6% CTR vs #10 ~2.4%.)
- **Poor/missing Open Graph** — no `og:title/description/image` → broken social
  previews kill referral CTR. (OG image ~1200×630.)
- **Missing/thin structured data** — no/incomplete **Product** JSON-LD (ineligible for
  price/review rich results); no Article/Breadcrumb/Organization schema. Validate it's
  in **server HTML**, not JS-injected. *(Note: Google FAQ rich results were deprecated
  May 2026 — do NOT flag "missing FAQ schema" as a rich-result gap.)*
- **No intent-specific landing pages** — only home + PDPs; no use-case/occasion/problem/
  audience pages, so commercial demand lands on a competitor.
- **"Read-then-dead-end" content** — ranking blog posts with **no links to collections/
  PDPs**, no product modules, no CTA. *Highest-ROI fix on stores that already rank.*
- **Generic homepage** — brand-narrative only, no keyword-relevant copy or links to top
  collections/use-cases.
- **Weak internal linking** — orphan pages, no topic clusters/pillar pages.

## Diagnostic questions
- **Meta:** every page a unique keyword-led title ≤~60 chars (not just "Product – Store")?
  unique benefit-driven description (150–160)? duplicates across PDPs/collections?
- **OG/social:** `og:title/description/image/url/type` present + page-specific? image ~1200×630?
- **Structured data:** Product JSON-LD on PDPs with offers/price/availability/review? in
  server HTML? Article on blog posts? Breadcrumb/Organization sitewide?
- **Content:** does each ranking/high-traffic page link to a relevant collection/PDP +
  CTA, or dead-end? targets a specific intent or generic storytelling? topic clusters?
- **Home/landing:** does it satisfy the queries it receives? dedicated intent landing
  pages for high-volume commercial queries? pre-click→post-click message match?

## Digest signals to weight
`meta_description` present + quality, `jsonld_types`, blog/content presence,
`word_count`, `og` tags, `nav_links`, title quality.

## KPIs + benchmarks (label your confidence)
- **Organic CTR by position**: #1 ~27.6% → #10 ~2.4% [Backlinko, authoritative].
- **Landing-page CVR** all-industry ~2.35%, top-25% ~5.31% [Shopify/Smart Insights, directional].
- **Message match** lifting CVR ~31% [CXL, single-study].
- **Time-to-result**: meaningful SEO movement in 3–6 months (up to 12) [Ahrefs, authoritative].
- **Rich-result eligibility**: target 100% valid Product schema (GSC), treat errors as leaks.

## Lever library
Rewrite titles (keyword-led, drop redundant store-name padding) + unique descriptions ·
add/repair Product + Article + Breadcrumb + Organization schema (server HTML) · fix
OG tags · build intent landing pages (use-case/occasion/problem/audience) ·
content-to-commerce routing (contextual links + product modules + CTAs from content) ·
topic clusters / pillar pages · internal-linking cleanup / de-orphaning · message match.

## Hypothesis + decision-rule framing
> "Because [observed leak — e.g., N ranking posts have zero product links], [tactic]
> will [outcome — e.g., raise content→PDP CTR from ~0%, lift assisted organic revenue],
> measured by [metric] within [window]."

- **Set expectations by feedback speed:** fast levers (meta, OG, content links) — judge
  in 2–6 weeks; slow bets (new pages, clusters) — 3–6+ months, watch impressions/position
  as leading indicators before clicks/revenue.
- **Guardrails:** no drop in valid rich-result count or indexed-page count (schema/meta
  changes can regress rankings if mis-implemented); annotate windows against algorithm updates.

## Remember
Cite the exact screenshot/html path or meta/JSON-LD evidence. Max 4 experiments. Emit
JSON per `schema/experiment.schema.json`; be explicit that SEO lift is slower-feedback
when setting `expected_lift`/`confidence`. Do NOT flag missing FAQ schema. Generalize.


