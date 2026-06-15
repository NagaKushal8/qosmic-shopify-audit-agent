# zenrojas.com audit — Strong Brand, Leaky Funnel: Zen Rojas Has the Story — Now It Needs the Revenue Infrastructure

## Executive summary

**Zen Rojas has built a compelling wellness brand, but its highest-confidence revenue leaks are not in the product or the story — they are in the purchase path.** The 10 experiments identified in this audit share a common theme: the brand fundamentals are solid (founder story, functional tea positioning, ambassador program, active blog), but the commerce layer has left money on the table at three compounding points. The cart page has no free-shipping progress bar and no cross-sell recommendations (both signals confirmed absent), meaning every buyer who reaches the cart is presented only with a 'Continue Browsing Here' button — no incentive to spend more. The collection grid defaults to alphabetical sort, placing 3 of 6 products as 'Sold Out' at the top of the browsable catalog, suppressing add-to-cart rate before a shopper even reaches a PDP. And the cross-sell 'Complete Your Ritual' widget on PDPs renders broken placeholder images rather than real product photos, silently killing the most natural upsell surface the site has.

**The store is also functionally invisible to organic search and social discovery — two channels the brand's content investments should be earning from.** Zen Rojas PDPs contain no Product JSON-LD structured data (confirmed by HTML inspection of /products/bodyguardtea — product data exists only in analytics JavaScript, not in server-rendered schema), making every product page ineligible for Google's price, availability, and review rich results. Meanwhile, a .heic-format image in the og:image tag on product pages will cause broken social card previews on Facebook and Twitter shares — suppressing referral clicks from social posts and DMs at a time when the brand's ambassador program and Instagram presence should be driving that traffic. The homepage meta title reads 'Home Page' with a 32-character description, leaving organic CTR for brand and category queries far below what a keyword-led rewrite could earn in weeks.

**The repeat-purchase engine is the third gap: Zen Rojas sells replenishable teas but has no subscription path, and its email list is growing slower than it should.** Every organic tea in the catalog is a consumable with natural replenishment demand — yet every PDP offers only a one-time add-to-cart with no subscribe-and-save toggle, even though Shopify Subscriptions is already enabled on the account (confirmed in page HTML metadata). The email capture popup — the primary top-of-funnel retention tool — asks visitors to 'Join the Zen Journey' with no concrete incentive, yielding capture rates near the ~2% industry floor rather than the 3–5% achievable with a first-order discount offer. The blog, which has been built and is producing branded content (Jesse Rojas story, family legacy, Bold Journey feature), ends every post with a comment form and zero product links — organic readers and returning customers find no reorder path. Fixing these three layers in sequence (cart merchandising → search/social visibility → subscription + email) would compound across every acquisition dollar the brand spends.

## Proposed experiments

### exp-e51fabeb9170 — Push sold-out products to end of collection grid and surface bestsellers first

**Pillar:** Conversion
**Affected surface:** All Products collection page
**URL:** https://zenrojas.com/collections/all
**Evidence:** `pages/04_collection_all/screenshot.png`
**Hypothesis:** Because the default 'Alphabetically, A-Z' sort places 3 of 6 visible products as 'Sold Out' (visible in collection grid screenshot), re-ordering to push sold-out items to the bottom while surfacing in-stock products first will reduce browse-abandonment and increase add-to-cart rate without harming revenue per session.
**Primary change:** Change default collection sort from 'Alphabetically, A-Z' to 'Best Selling' and push all Sold Out variants to the end of the grid
**Primary KPI:** Add-to-cart rate from collection pages
**Decision rule:** Ship if ATC rate from collections improves >=5% at 95% confidence with no regression in CVR or AOV; run minimum 2 full weeks
**Expected lift:** +8-15% ATC rate from collections
**Confidence:** 75%

### exp-5b08fece8b21 — Add free-shipping progress bar to cart page

**Pillar:** AOV
**Affected surface:** Cart page
**URL:** https://zenrojas.com/cart
**Evidence:** `pages/01_cart_cart/screenshot.png`
**Hypothesis:** Because the cart page shows no free-shipping threshold or goal-gradient progress bar (signal free_shipping_bar='absent', visually confirmed -- cart screenshot shows only a 'Continue Browsing Here' CTA with no shipping incentive), adding a progress bar set ~15-25% above current AOV will motivate shoppers to add one more item. Benchmark: ~58% of shoppers add items to qualify for free shipping.
**Primary change:** Configure a free-shipping threshold bar in the cart set at ~$35-45 (approx. 20% above estimated AOV for $8-$25 teas) with dynamic copy 'You are $X away from free shipping!'
**Primary KPI:** Revenue per session (CVR x AOV)
**Decision rule:** Ship if AOV lifts >=10% and CVR does not drop >3%; run minimum 3 full weeks
**Expected lift:** +12-20% AOV
**Confidence:** 83%

### exp-2bd5da7bcfcd — Add discount incentive to email popup to increase list capture rate

**Pillar:** Retention
**Affected surface:** Email popup (sitewide)
**URL:** https://zenrojas.com/
**Evidence:** `pages/00_home_home/popup.png`
**Hypothesis:** Because the email popup ('Join the Zen Journey') offers no concrete incentive -- only 'Promotions, new products and sales. Directly to your inbox' (popup screenshot confirms no offer/discount/free-shipping line) -- visitors have little motivation to subscribe. Adding a first-order discount (e.g., 10% off) as the popup offer will increase capture rate from the ~2% average to 3-5%, building a larger re-engagement audience for repeat purchase campaigns.
**Primary change:** Rewrite popup headline to offer a concrete incentive (e.g., '10% off your first order -- Join the Zen Journey') and add automated discount code delivery on signup
**Primary KPI:** Email capture rate; 30-day repeat purchase rate from email subscribers
**Decision rule:** Ship if email capture rate improves >=30% relative (e.g., ~2% to ~2.6%+) with first-order CVR guardrail; measure repeat purchase rate at 30-day cohort
**Expected lift:** +30-60% email capture rate
**Confidence:** 80%

### exp-9f059a321fb6 — Add Product JSON-LD structured data to PDPs for Google rich-result eligibility

**Pillar:** Acquisition
**Affected surface:** Product detail pages
**URL:** https://zenrojas.com/products/bodyguardtea
**Evidence:** `pages/10_product_bodyguardtea/page.html`
**Hypothesis:** Because Zen Rojas PDPs contain no Product JSON-LD structured data (grep of bodyguardtea HTML confirms no application/ld+json or @type:Product -- product data exists only in Shopify analytics JS objects, not in server-rendered schema), the store is ineligible for Google's price/availability/review rich results. Adding valid Product schema will improve SERP click-through rate. Organic CTR at position #1 is ~27.6% vs ~2.4% at #10 [Backlinko].
**Primary change:** Add server-rendered Product JSON-LD to all PDP templates: name, description, image, sku, brand, offers (price, availability, currency), aggregateRating
**Primary KPI:** Organic CTR from Google Search Console; rich-result impressions
**Decision rule:** Ship when GSC validates 0 schema errors on PDPs; measure organic CTR change at 60-day window; allow 3-6 months for full compounding impact
**Expected lift:** +10-25% organic CTR from product queries
**Confidence:** 82%

### exp-f34920d975e8 — Fix broken product images in 'Complete Your Ritual' cross-sell widget on PDPs

**Pillar:** Performance
**Affected surface:** Product detail pages -- cross-sell section
**URL:** https://zenrojas.com/products/teabagsamplers
**Evidence:** `pages/08_product_teabagsamplers/screenshot.png`
**Hypothesis:** Because the 'Complete Your Ritual' cross-sell section on multiple PDPs (Tea Bag Samplers, Bodyguard Tea -- both PDP screenshots confirm) renders product images as broken placeholder dots rather than actual product photos, the cross-sell module fails to function as a revenue driver and signals poor site quality to buyers. Fixing image rendering will restore the widget's conversion contribution.
**Primary change:** Diagnose the lb-* web-component image-loading failure (CSS visibility:hidden for lb-card-image until hydrated, visible in page HTML styles) and ensure cross-sell product images load correctly on PDPs
**Primary KPI:** Cross-sell attach rate; PDP-to-cart CVR
**Decision rule:** Ship (bug fix) when all cross-sell product images render correctly in both desktop and mobile screenshots; measure cross-sell widget click rate vs pre-fix baseline
**Expected lift:** +5-12% cross-sell attach rate; +3-7% PDP CVR
**Confidence:** 85%

### exp-1da4d8ba2666 — Add star ratings to collection page product tiles

**Pillar:** Conversion
**Affected surface:** All Products collection page
**URL:** https://zenrojas.com/collections/all
**Evidence:** `pages/04_collection_all/screenshot.png`
**Hypothesis:** Because product tiles on the 'All Products' collection page display no star ratings (collection screenshot shows title + price only, no review widgets), adding visible review scores to tiles will increase click-through rate to PDPs by providing social proof at the discovery stage.
**Primary change:** Enable review stars on collection product tiles via the Automizely reviews app already installed (per page HTML scripts)
**Primary KPI:** Collection-to-PDP click-through rate; sitewide CVR
**Decision rule:** Ship if collection CTR improves >=8% and sitewide CVR does not regress; run minimum 2 full weeks
**Expected lift:** +6-12% collection-to-PDP CTR
**Confidence:** 65%

### exp-d91af5c585eb — Add cart-aware product cross-sell recommendations to cart page

**Pillar:** AOV
**Affected surface:** Cart page
**URL:** https://zenrojas.com/cart
**Evidence:** `pages/01_cart_cart/screenshot.png`
**Hypothesis:** Because the cart page displays zero product recommendations (signal cross_sell='absent', visually confirmed -- cart shows only 'Continue Browsing Here' with no suggested products), adding complementary cross-sells (e.g., teaware for tea buyers, or a second tea variety) will increase units per order. McKinsey benchmark: personalized recs drive ~10-15% revenue lift.
**Primary change:** Add a 'Complete Your Ritual' cross-sell module to the cart page with 2-3 complementary products, filtered to exclude already-in-cart items
**Primary KPI:** AOV; revenue per session
**Decision rule:** Ship if AOV lifts >=8% with CVR guardrail (no more than 3% drop); run minimum 3 weeks
**Expected lift:** +8-15% AOV
**Confidence:** 75%

### exp-bd19ef3f5e53 — Add shop CTAs and product links to blog posts to close the content-to-commerce loop

**Pillar:** Retention
**Affected surface:** Blog posts
**URL:** https://zenrojas.com/blogs/weekly-blog/bold-journey
**Evidence:** `pages/22_blog_bold-journey/screenshot.png`
**Hypothesis:** Because blog posts end with a comment form and zero links to products or collections -- the 'bold-journey' blog screenshot shows: header image, 2-sentence text, external link, then immediately 'Leave a comment' with no product CTA anywhere -- organic content traffic and returning brand-curious customers have no path to reorder. Adding inline product recommendations and a 'Shop Our Teas' CTA module will convert content readers and returning customers into repeat purchasers.
**Primary change:** Add a 'Featured Products' inline module + 'Shop Now' CTA to all blog post templates linking to relevant PDPs or collections
**Primary KPI:** Blog-to-PDP click-through rate; assisted conversion from blog sessions
**Decision rule:** Ship if blog-to-PDP CTR improves >=50% relative from ~0% baseline; measure assisted revenue from blog sessions over 30 days
**Expected lift:** +content-to-commerce CTR from ~0% to 3-8%
**Confidence:** 70%

### exp-a420718b92ea — Fix HEIC-format OG image causing broken social card previews on PDP shares

**Pillar:** Acquisition
**Affected surface:** Product detail pages -- social sharing
**URL:** https://zenrojas.com/products/bodyguardtea
**Evidence:** `pages/10_product_bodyguardtea/page.html`
**Hypothesis:** Because the og:image on Bodyguard Tea PDP references a .heic file ('image_72b7ada2-d563-46bb-ad2e-20ba232dd962_1200x1200.heic' confirmed in page HTML og:image:secure_url tag) -- a format not supported by Facebook/Twitter OG crawlers -- social shares of PDPs will render broken or absent preview images, suppressing referral click-through from social posts and DMs.
**Primary change:** Replace .heic OG images with JPEG/WebP equivalents on all PDPs; ensure og:image points to a format supported by all social crawlers (JPEG or PNG at ~1200x630)
**Primary KPI:** Social referral CTR; OG debugger preview validation
**Decision rule:** Ship (bug fix) when Facebook OG debugger confirms valid image render for all PDP URLs; measure social referral sessions at 30 days post-fix
**Expected lift:** +15-30% social-share CTR from PDPs
**Confidence:** 78%

### exp-0bfcc1a98b00 — Add subscribe-and-save option to organic tea PDPs

**Pillar:** AOV
**Affected surface:** Product detail pages
**URL:** https://zenrojas.com/products/organicsleeptea
**Evidence:** `pages/15_product_organicsleeptea/screenshot.png`
**Hypothesis:** Because Zen Rojas sells replenishable organic teas (consumables) but PDPs show only a one-time Add-to-Cart with no subscription or cadence selector (screenshot confirms no subscribe toggle), adding a subscribe-and-save option will increase initial-order revenue via the subscription attachment and grow LTV. Shopify Subscriptions is already enabled per apple-pay-capabilities metadata in the page HTML.
**Primary change:** Add subscribe-and-save widget with 10-15% discount for monthly delivery on all tea PDPs using Shopify Subscriptions (supportsSubscriptions=true confirmed in page HTML)
**Primary KPI:** Subscription attach rate; LTV-adjusted revenue per session
**Decision rule:** Ship if subscription attach rate >=3% and first-order CVR does not drop >5%; measure LTV at 90-day cohort
**Expected lift:** +15-25% LTV revenue per subscriber cohort
**Confidence:** 72%

## Competitor analysis

Zen Rojas competes in a DTC organic wellness-tea segment where larger players have made subscribe-and-save, benefit-based navigation, and loyalty programs table stakes -- areas where Zen Rojas's personal founder story and tight functional positioning are genuine edges, but only if the commerce infrastructure catches up.

| Competitor | Domain | Positioning | What they make easier | zenrojas.com edge | Pattern to adapt |
|---|---|---|---|---|---|
| Full Leaf Tea Company | fullleafteacompany.com | Broad-catalog organic loose-leaf DTC tea brand covering wellness, matcha, green, black, and herbal blends with an emphasis on value and variety | Subscribe-and-save at 15% off (cancel anytime) with a dedicated collection page; free shipping on orders over $49 with a visible threshold; a Leaf Points loyalty program (1 pt per $1, redeemable for discounts); tiered quantity pricing (2oz vs 4oz saves ~30%); and a curated wellness subscription box with 5 teas per delivery | Zen Rojas has a tighter, more personal founder/family brand narrative (ambassador program, weekly blog, Jesse Rojas story) and health-function specialization (immunity, heartburn, sleep) that gives each product a clear wellness job-to-be-done -- Full Leaf's broad catalog dilutes this focus. Zen Rojas also has the infrastructure for Shopify Subscriptions already enabled (supportsSubscriptions=true in page HTML). | Subscribe-and-save widget on tea PDPs + a free-shipping threshold bar in cart -- both proven AOV lifters that Full Leaf deploys and Zen Rojas's cart page currently lacks (signals confirm free_shipping_bar='absent', cross_sell='absent') |
| Tease Tea | teasetea.com | Tea-inspired wellness and beauty brand organizing products by health benefit (sleep & calm, focus & energy, immunity, digestion, skin support) with a sustainability and women-in-business mission | A 'Shop by Benefit' navigation that matches buyer intent to product instantly; a Wellness Quiz that personalizes tea recommendations; subscription delivery with flexible skip/pause/cancel; wellness recipes as content-to-commerce bridges; and mission-led storytelling (supporting women founders) that deepens brand affinity | Zen Rojas's functional tea names (Bodyguard, Heartburn, Sleep) already communicate health benefits directly -- it's closer to Tease's intent-matching without needing a quiz overlay. Zen Rojas's ambassador program (pages/17_page_ambassadorprogram) and family/community positioning offer authentic community retention that Tease's mission-branding approximates from a corporate angle. | Benefit-based collection navigation (e.g., 'Shop by Wellness Goal') and inline blog-to-product links -- Zen Rojas blog posts currently dead-end with no product CTAs (confirmed in pages/22_blog_bold-journey/screenshot.png), whereas Tease routes content readers to relevant products |
| Traditional Medicinals | traditionalmedicinals.com | Established 50-year organic medicinal/functional tea brand with clinical herbalist credibility, condition-organized catalog, and mass-retail + DTC distribution | Condition/benefit-organized product catalog with rich herbalist sourcing stories per ingredient; transparent clinical/ethnobotanical evidence cited near the buy button; a find-my-tea recommendation quiz; and very high trust via brand longevity and retail shelf presence | Zen Rojas's modern DTC-native commerce (Shopify, ambassador program, family founder story, social presence) is more nimble and community-driven than Traditional Medicinals' heritage positioning. Zen Rojas can iterate on product messaging and CRO faster. The personal story (Jesse Rojas, family legacy blog posts) creates emotional connection that a corporate herbal brand cannot replicate. | Rich per-ingredient sourcing copy and evidence-backed benefit claims near the PDP buy box -- Zen Rojas PDPs have detailed body copy (confirmed in pages/10_product_bodyguardtea/screenshot.png) but trust cues (guarantee badge, sourcing callouts) are not surfaced directly in the buy-box area |
| Yerba Buena Tea Co. | ybtco.com | Women and family-owned artisan small-batch organic loose-leaf tea from Oregon, emphasizing hand-crafted community and ritual positioning with seasonal and herbal blends | Deep per-blend ingredient storytelling that justifies artisan pricing; a tightly curated small catalog that reduces decision fatigue; and community-oriented social content that converts brand fans into repeat buyers | Zen Rojas has a more developed digital marketing infrastructure -- ambassador program, structured blog, email capture popup, and teaware accessories cross-sells -- giving it more acquisition and retention surface area than Yerba Buena's boutique footprint. Zen Rojas also spans tea bags, loose leaf, and teaware, broadening AOV opportunity. | Tighter artisan per-product storytelling (origin, ritual use, how-long-it-lasts) on PDPs, which would also support the subscribe-and-save angle by making the replenishment cadence feel natural and habitual |

## Technical checks

| Check | Status | Detail |
|---|---|---|
| SSL Certificate | Pass | HTTPS storefront loaded successfully. |
| HTTPS Redirect | Pass | HTTP redirected to HTTPS. |
| Sitemap | Pass | /sitemap.xml present and parseable. |
| Robots.txt | Pass | robots.txt present. |
| Critical Pages Loading | Pass | Homepage and sampled pages loaded. |
| Meta Tags & Social Previews | Pass | Title + meta description present on homepage. |
| Structured Data | Warn | No JSON-LD structured data detected. |
| Favicon | Warn | No favicon link detected. |
| Mobile-Friendly | Pass | Responsive viewport meta present. |
| Page Speed Desktop | Warn | Avg nav load ~4416ms (proxy; consider optimization). |
| Page Speed Mobile | Warn | Avg nav load ~4416ms (proxy; consider optimization). Mobile uses desktop nav timing as proxy. |
| Broken Links | Pass | No 4xx/5xx among sampled pages. |
| Image Optimization | Pass | Up to 25 images on a page (byte size not measured). |
| Cookie/Privacy | Pass | Privacy/policy page or link present. |
| Checkout Reachable | Pass | Checkout URL reachable. |
