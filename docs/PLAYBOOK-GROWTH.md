# Growth & retention playbook — decisions waiting for approval

As of **24 Nov 2026**. Every item below is a **proposal**. Nothing is changed in Shopify, Meta, Google Ads, Zoko or on Amazon until a
founder says "yes" to that exact item. ₹ effects are **estimates** from our own numbers, not forecasts. Claude refreshes the
numbers behind each item with `/abandoned`, `/ads`, `/competitors` and `/brief` before you decide.

How to use: read the item, then tell Claude "Approve #3" (Claude prepares the exact change for one last look), "Not now", or
"Tell me more about #5".

| # | Decision | Owner | Effort | Estimated effect |
|---|---|---|---|---|
| 1 | 3-step WhatsApp cart reminders (fix error 131049) | Growth (CRM) in Zoko | ½ day | +3–5 pts recovery (~₹5–9K / month) |
| 2 | Cart emails at 1 h / 24 h / 72 h, 10% only for carts over ₹700 | Growth (CRM) in Shopify Messaging | ½ day | +2–3 pts recovery (~₹3.5–5K / month) |
| 3 | One free-shipping line: ₹399 everywhere + "₹X away" cart bar | Founders decide, theme change | 1 hour (fix ready) | Fewer checkout surprises, higher order value |
| 4 | Exclude existing buyers from all prospecting campaigns | Growth (ads) | 1 hour | Less spend wasted on people who already buy |
| 5 | Shift spend from Instagram Reels/video to single-image ads; drop weak placements | Growth (ads) | 1 hour + creative | Lower cost per sale (test 2 weeks) |
| 6 | Frequency caps on retargeting (≤ 2 per week) | Growth (ads) | 30 min | Less ad fatigue; flags at frequency ≥ 4 |
| 7 | Amazon vs website price parity | Founders + marketplace | decision + 1 day | Protects site sales and margin |
| 8 | Refresh stale banners after every sale | Founders / web | 15 min per sale | Trust; no expired offers showing |
| 9 | Free-sample tier + 10% first order for WhatsApp opt-in | Founders | ½ day | Higher order value, more contactable customers |
| 10 | Stock: 300g (3 × 100g) pack replaces 250g; hide sold-out sizes | Ops | 1 hour | Fewer bounced carts |

---

## 1. WhatsApp cart reminders that actually arrive (Zoko)
**Why:** only ~8–9% of unfinished checkouts come back and pay (healthy is 10–15%+). Today the same "payment pending" message goes
twice, and many sends fail with Meta error **131049** — WhatsApp caps marketing messages per person, and cart reminders count as
marketing. Heavy promo broadcasts use up that cap.
**Proposal:** replace with 3 different messages, send fewer promo broadcasts, and fall back to email/SMS when WhatsApp fails.
- 30 min: "Hi {name}, your {product} is still in your cart. Fresh from Darjeeling, cash on delivery available. Finish your order: {link}"
- Next morning 10 am: "Still thinking? Read what our reviewers say about it. Free shipping over ₹399. Questions? Just reply here."
- 48 h: "Last call: your cart is saved until tonight. {link}"
Also check Razorpay Magic Checkout's own recovery messages are off (no double reminders).

## 2. Cart emails at 1 h / 24 h / 72 h (Shopify Messaging)
**Why:** one email goes out about 10 hours after the cart is left — too late, and only once. ~80% of these shoppers gave an email.
**Proposal:** Email 1 at **1 h** "Your First Flush is waiting" · Email 2 at **24 h** tasting notes + reviews + harvest story ·
Email 3 at **72 h** **10% off for 24 hours, only for carts over ₹700** (no discount for small carts, protects margin).

## 3. One free-shipping line: ₹399 + cart bar
**Why:** the policy and checkout use ₹399, but the cart drawer has shown a different amount. ₹399 matches Teabox/Udyan and beats
Vahdam (₹599). Carts under ₹399 pay ₹50 shipping and almost never come back.
**Proposal:** say "Free shipping over ₹399" everywhere (site, cart, ads, WhatsApp) and add a cart bar "Add ₹{gap} more for free
shipping". The theme fix is prepared on an unpublished theme copy; it goes live only on "publish".
**Confirm first:** ₹399 vs ₹499 threshold, and the 48-hour returns wording.

## 4. Leave existing buyers out of new-customer ads (Meta)
**Why:** several active prospecting campaigns have **no buyer exclusion**, so part of the "new customer" budget reaches people who
already buy (and would buy anyway).
**Proposal:** add a "Purchasers 180 days" custom-audience exclusion to every prospecting ad set; move money from the weakest test
campaigns into one new-customer campaign. Check the Meta pixel sees Razorpay checkouts first (cart audiences look too small).

## 5. Single-image ads over Reels/video; drop weak placements (Meta)
**Why:** our Reels/video placements cost more per sale than single-image ads in the last 30 days; some placements
(e.g. Audience Network) bring clicks but few sales. Competitors winning on Meta lead with **price in the headline**.
**Proposal:** for 2 weeks shift budget toward single-image product ads with price + "free shipping over ₹399" + COD; exclude
placements with no sales; compare cost per new customer (CAC) before/after.

## 6. Frequency caps on retargeting (Meta)
**Why:** retargeting frequency above 4–5 means the same people see the ad too often (fatigue, rising CPM).
**Proposal:** cap at ~2 impressions per person per week for cart/checkout retargeting; refresh creative when frequency ≥ 4.

## 7. Amazon vs website price parity
**Why:** the same items are **24–44% cheaper on Amazon** (e.g. First Flush 100g ₹377 on Amazon vs ₹499 on the site). Shoppers
compare, then buy on Amazon or leave the site cart.
**Proposal (pick one):** (a) price Amazon at or above the site, or (b) keep Amazon prices but give site buyers a visible extra —
free 10 g sample + infuser, or subscription price. Re-checked weekly by `/competitors`.

## 8. Refresh stale banners
**Why:** sale banners have stayed up after the sale ended (e.g. the Diwali offer). Expired offers cost trust.
**Proposal:** a checklist item at the end of every sale; `/competitors` also scans our own homepage banner weekly.

## 9. Free-sample tier and WhatsApp opt-in offer
**Why:** Sancha, Udyan and Vahdam add free samples to orders. We have few ways to grow the contactable list.
**Proposal:** free 10 g flush sample above ₹699; 10% off the first order for opting in to WhatsApp updates (with clear consent).

## 10. Stock and pack sizes
**Why:** the 250g packs sold out and are being replaced by a **300g (3 × 100g)** pack; sold-out sizes still appear in carts.
**Proposal:** list the 300g pack everywhere the 250g was, hide sold-out sizes, and add a Zoko "back in stock" alert.

---

## Also open (need a founder answer, not a change)
- Organic certification: confirm before using "organic" in ads and on product pages.
- Teabag prices/pack sizes: the catalogue (15 bags ₹450 / 30 bags ₹799) vs the site — which is correct?
- Read-only access to Razorpay analytics (where people drop out of the checkout pop-up).
- Google Ads API access (blocked on Google's Explorer approval) and Amazon seller/ads credentials.

## Product & price reference (catalogue, site list prices)
Darjeeling black — First Flush ₹499 · Second Flush ₹399 · Autumn Flush ₹399 · Roasted ₹299
Darjeeling green — First Flush ₹499 · Second Flush ₹399 · Monsoon ₹299 · Autumn ₹399
Chai ₹299 · Wellness blends ₹499 · Pyramid teabags: 15 bags ₹450 / 30 bags ₹799 (list)
