# Pillar playbook — Conversion

**Mission:** turn *existing* traffic and intent into completed purchases. Everything
between landing and order-confirmation: value clarity, trust, friction. You are not
inventing demand — you are finding where present intent leaks out.

## How to think (read this first)
Reason **from this store's evidence**, not from a template. Walk the funnel
(home → collection → PDP → cart → checkout) and at each surface ask the diagnostic
questions below. Propose an experiment **only where the evidence shows a real leak**
— if a screenshot shows a clear price + add-to-cart + reviews, do NOT manufacture a
conversion problem. Benchmark against the store's vertical (CVR varies hugely:
food/beverage ~5–6%, home/furniture ~1.4%). Every finding is a hypothesis to A/B test.

## Leak patterns to hunt (store-agnostic — pair each with on-page signal)
- **Value-prop unclear** — within 5s, not obvious what's sold / for whom / why here.
  Hero is decorative with no benefit headline or primary CTA.
- **CTA hierarchy** — primary action (Add to Cart / Shop) not visually dominant;
  multiple competing equal-weight CTAs; CTA below the fold or not sticky on mobile.
- **Trust gap near the buy decision** — no reviews/ratings, returns, guarantee,
  security/payment badges. (Baymard: 19% abandon distrusting card security; 15% over
  returns policy; 18% over a too-long/complex checkout.)
- **Price/cost not transparent** — price hidden on PDP; shipping/total not shown till
  late checkout. (Baymard: **extra costs = #1 abandonment reason, 39%**.)
- **Add-to-cart / cart friction** — no add-to-cart feedback; cart hides costs; forced
  detours; weak "proceed to checkout." (Cart→checkout drop is often 50–60%.)
- **Checkout friction** — forced account creation (≈19–26% abandon), too many form
  fields, too few payment methods (10% abandon), unclear errors (15% abandon).
- **Social proof placement** — rating/review count not beside title/CTA; reviews
  buried or lacking helpful reviewer context.
- **Findability** — weak nav/search; collections without filter/sort on a big catalog.
- **PDP completeness** — thin images (no zoom/angles/scale), thin specs, unclear
  variants, dead out-of-stock states.

## Diagnostic questions (by surface)
- **Home:** clear value prop + one dominant CTA above the fold? differentiators
  (shipping/returns/guarantee) visible? relevant category in ≤2 clicks? search present?
- **Collection:** filter + sort? scannable cards (image/title/price/rating)? price on every card?
- **PDP:** price + key info + Add-to-Cart visible together above the fold? CTA most
  prominent + sticky on mobile? rating/review count near the CTA? shipping/returns/
  security cues present? images answer questions? variants clear?
- **Cart:** full cost (subtotal+shipping+tax) before checkout? dominant checkout CTA,
  no surprise costs? editable, with add-to-cart confirmation?
- **Checkout:** guest checkout offered up front? field count minimal? express/wallet pay?

## Digest signals to weight
`price_present`, `add_to_cart_present`, `reviews_present`/`review_count`,
`cta_count` (0 *or* too many both hurt), `variant_selector`, `checkout_button`,
`empty_cart`, `has_hero_cta`. Always confirm against the screenshot.

## KPIs + benchmarks (label your confidence)
- Sitewide **CVR**: Shopify avg ~1.4%; ≥3.2% top-20%, ≥4.7% top-10% [Littledata, directional].
- **Add-to-cart rate**: avg ~4.4%; <2% = early-funnel problem; 8–10% excellent [directional].
- **Cart abandonment** ~70.2% [Baymard, authoritative]. Checkout completion ~45% [directional].
- Baymard: average site can gain **~35% conversion** by fixing checkout-design issues [authoritative].

## Lever library
Above-the-fold value headline · single dominant CTA + reserved color · sticky PDP
add-to-cart · star rating beside CTA · security/returns badges near buy box · early
cost transparency + shipping-threshold cue · guest checkout + fewer fields + express
pay · real imagery over stock · robust filter/sort/search.

## Hypothesis + decision-rule framing
> "Because [observed leak + cited evidence], [change] on [surface/audience] will lift
> [primary metric, usually CVR or the specific step rate] without harming [guardrails]."

- **Primary metric:** CVR or the step being optimized (ATC rate, checkout-completion).
- **Guardrails (must not regress):** AOV, revenue/session, return rate, page speed, bounce.
- **Ship** if primary beats control at significance AND no guardrail breaks; size with a
  Minimum Detectable Effect, run full weeks, no early peeking.

## Remember
Cite the exact screenshot/html path. Max 4 experiments. Emit JSON per
`schema/experiment.schema.json`; set `confidence` honestly (higher when the leak is
visible AND backed by an authoritative benchmark). Generalize — reason from THIS store.


