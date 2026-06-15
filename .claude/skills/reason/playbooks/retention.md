# Pillar playbook — Retention

**Mission:** turn first purchases into repeat purchases and lifetime value (LTV).
Retention is the input; LTV is the output. Economics: a 5% retention lift can raise
profits 25–95% (Bain, directional); purchase probability climbs with each order
(~27% buy a 2nd time, ~45% a 3rd after the 2nd, ~62% after the 3rd — Smile.io).

## How to think (read this first)
Retention work starts **at/after the first purchase** and must NOT cannibalize
first-order CVR or AOV (those are guardrails). Reason from the store's product type:
**is this a consumable/replenishable good?** If yes, absence of subscription/reorder
is a major leak; if it's a one-time durable, lead with capture + loyalty instead.
Most retention metrics lag (45–90+ days) — pair every recommendation with a fast
leading indicator.

## Leak patterns to hunt (store-agnostic — pair with on-site signal)
- **No subscription/replenishment** for a consumable — PDP has only "Add to cart," no
  subscribe toggle/cadence selector. (Replenishment subs churn far lower than curation.)
- **No easy reorder** — account has order history but no one-click "Buy it again"; no reorder CTA in email.
- **Weak/absent email & SMS capture** — no pop-up (or buried footer field), no opt-in
  incentive, no SMS consent at checkout. (Pop-up capture avg ~2%; good 3–5%.)
- **No post-purchase flow** — bare transactional confirmation; no shipping/educational/
  replenishment sequence. (Post-purchase emails have the highest open rate, ~60%.)
- **No loyalty/referral** — no rewards/points nav, no referral link, no tiers.
- **No account value** — logged-in state shows only address + raw order list.
- **Content not tied to a reorderable habit** — blog drives traffic but no routine/
  regimen/kit and no content→product→reorder loop.

## Diagnostic questions
- **Home:** email/SMS capture with incentive? any rewards/loyalty link? messaging hint
  recurring use (routines/refills/members) or only first-purchase acquisition?
- **PDP:** is the product consumable/depleting? if so, subscribe-and-save w/ cadence?
  bundle/kit/routine creating recurring multi-product need? "how long it lasts" copy?
- **Account:** one-click reorder? subscription management (skip/swap/pause)? saved prefs, loyalty balance?
- **Footer/site:** links to rewards, referral, subscription mgmt? incentivized signup?
- **Blog:** content tied to a reorderable habit, with a path to a subscribable kit?

## Digest signals to weight
`email_capture`, presence of `account` routes, subscription/auto-ship mentions,
blog/content presence (`category == blog`, `word_count`), repeat-use language on PDPs.

## KPIs + benchmarks (label your confidence)
- **Repeat purchase rate** avg ~28%; typical Shopify 20–25%; top DTC 40%+ [mixed/directional].
- **30/90-day RPR** ~20–25% / 25–30% target; median time-to-2nd ~45 days [rule of thumb].
- **Subscription retention** ~45% at 6mo, ~33% at 12mo [Recharge, authoritative].
- **Email pop-up capture** ~2% avg, 3–5% good [Omnisend, authoritative].
- **Post-purchase email** ~60% open rate [Klaviyo, authoritative]; **loyalty** lifts RPR ~20–27% [Smile.io].
- Benchmark against the **vertical** (health/beauty & F&B retain better than apparel/electronics).

## Lever library
Email/SMS capture w/ incentive → post-purchase flow → easy reorder + account value →
subscribe-and-save / replenishment reminders (consumables) → loyalty/referral →
routines/regimens/bundles → subscription flexibility / annual prepay.
**Sequencing heuristic:** you can't run loyalty/replenishment to people you can't
reach — so capture + post-purchase flow come first.

## Hypothesis + decision-rule framing
> "Because [leak + on-site signal], [lever] will raise [lagging retention metric] by
> [target] for [segment], without harming [first-order CVR/AOV]."

- **Lagging/primary:** RPR (30/90-day), subscription rate, LTV.
- **Leading (fast read):** capture rate, post-purchase placed-order rate, subscribe
  attach rate, loyalty enrollment, reorder-CTA clicks.
- **Guardrails:** first-order CVR, first-order AOV, early subscription churn, refunds.
- **Prioritize by reach × leverage** — a missing capture/post-purchase flow touches
  every buyer and usually outranks a loyalty-tier tweak.

## Remember
Cite the exact screenshot/html path. Max 4 experiments. Emit JSON per
`schema/experiment.schema.json`. Calibrate `confidence` to product fit (subscription
only makes sense for consumables). Generalize — reason from THIS store's product type.

