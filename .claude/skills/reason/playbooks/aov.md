# Pillar playbook — AOV (Average Order Value)

**Mission:** grow revenue per order. AOV = revenue ÷ orders, and decomposes into
**units per order** and **revenue per unit**. It's the cheapest growth lever (adds
revenue at flat CAC) — but every AOV move must be guarded against conversion harm.

## How to think (read this first)
Look for **missing** monetization surfaces, not broken ones — AOV leaks are usually
*absences*. Walk PDP → collection → cart and ask "what higher-value path is NOT
offered here?" Propose only where the catalog plausibly supports it (a single
expensive durable good rarely needs a free-ship threshold; consumables and
multi-SKU catalogs do). True-north metric is **revenue per session (CVR × AOV)**, not
AOV alone — a high threshold can lift AOV while cutting orders.

## Leak patterns to hunt (store-agnostic — the absence IS the signal)
- **PDP:** no cross-sell / "frequently bought together" / "complete the set"; no
  bundle/kit; no quantity break on consumables; no subscribe-and-save on
  replenishables; no Good/Better/Best tier; no sampler/multipack where trial demand exists.
- **Collection:** everything single-unit — no bundles/sets/multipacks merchandised;
  no value-pack anchoring.
- **Cart:** no **free-shipping progress bar / threshold**; no cart-aware cross-sell;
  dead-end cart (only "checkout"); OR irrelevant generic best-seller widgets — Baymard:
  **52% of sites show irrelevant cart cross-sells**, and one bad rec makes users
  distrust *all* recs.
- **Post-purchase:** no one-click post-purchase upsell on the thank-you step; OR (bad)
  cross-sells crammed into the payment step where they hurt CVR.

## Diagnostic questions
- **PDP:** cross-sell/FBT present + complementary (not competing)? bundle/kit or
  quantity break? subscribe-and-save on a replenishable? premium-tier upsell path?
- **Collection:** any bundles/sets/multipacks, or all single units? value packs surfaced?
- **Cart:** free-shipping threshold + progress bar? cross-sells cart-aware vs generic?
  any basket-building prompt at all? offers proportionate to cart value?
- **Cross-cutting:** is a visible threshold near/below likely AOV (weak) vs ~10–30% above (effective)?

## Digest signals to weight
`product_tiles` (catalog breadth), `variant_selector`, `price_present`, cart
`add_to_cart_present` + cross-sell cues, `empty_cart` (no recovery merchandising).

## KPIs + benchmarks (label your confidence)
- **AOV** global avg ~$145; varies by vertical (beauty $15–90, apparel $40–170, luxury $300+) [Shopify, directional].
- **Units/order** ~4–5 avg; beauty/F&B higher, fashion ~2.8 [Dynamic Yield, directional].
- **Free-ship threshold**: +15–25% AOV when set right; ~58% add items to qualify [directional].
- **Bundling**: commonly +20–35% AOV [vendor/CXL, rule of thumb].
- **Personalized recs**: ~+10–15% revenue [McKinsey, authoritative range].
- **Post-purchase upsell** take rate ~3–8% (well-targeted 8–15%) [vendor, rule of thumb].

## Lever library
Free-ship threshold + goal-gradient progress bar (set ~10–30% above current AOV) ·
mixed bundling / kits / build-your-own · Good/Better/Best tiers · cart-aware
cross-sell (relevant + labeled) · quantity breaks (~8–20%/tier) · subscribe-and-save ·
samplers/variety packs · one-click post-purchase upsell (<~$30) · order-minimum gift.

## Hypothesis + decision-rule framing
> "For [audience/page], adding [lever] will raise **AOV by ≥X%** without dropping
> **CVR by more than Y%**, netting higher **revenue per session**."

- **Decision metric:** revenue per session (CVR × AOV) — AOV alone is gameable.
- **Guardrail:** CVR (tight — it usually outweighs AOV in revenue), return rate, margin.
- **Ship** if AOV↑, CVR within guardrail, RPS↑ significant. **Kill** if CVR breaks even when AOV rises.
- Gate cross-sells on **relevance** before quantity; A/B the *threshold level* (AOV+10% vs +30%).

## Remember
Cite the exact screenshot/html path. Max 4 experiments. Emit JSON per
`schema/experiment.schema.json`; calibrate `confidence` (authoritative levers like
free-ship threshold deserve higher confidence than rule-of-thumb bundle %s).
Generalize — only propose levers the catalog supports.


