#!/usr/bin/env python3
"""Ads & Offers intel (Meta/Google/site/Amazon counts re-checked 23 Nov 2026 IST; EX ad quotes and gap/playbook analysis carried from 16 Nov). Re-check weekly, edit here, run, then build_competitors.py.
Facts come from: Meta Ad Library (country IN, active) incl. the ad's own page (facebook.com/ads/library/?id=<ad id>);
Google Ads Transparency Center (region India, last 30 days); each brand's homepage seen with India settings
(banner/popup/cart text; competitors/scan_offers.mjs); amazon.in search cards. Strategy lines and the Dorje playbook are
our analysis of those facts; anything forward-looking is marked (estimate)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
AD = 'https://www.facebook.com/ads/library/?id='
PG = 'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id='
GA = 'https://adstransparency.google.com/?region=IN&preset-date=Last+30+days&domain='
PAGES = {'dorje': '302251162980335', 'vahdam': '1491430561130722', 'teabox': '509251098946332', 'tcotw': '800871513266267', 'sancha': '203853022985323',
 'goldentips': '1142228112496445', 'goodricke': '226335644073160', 'makaibari': '1132999483237601', 'organicindia': '194411414144', 'kaahu': '722512074285827',
 'mittal': '234289799983346', 'happyvalley': '1041551119046707', 'jayshree': '136284389760335', 'udyan': None}
NAME = {'dorje': 'Dorje', 'vahdam': 'Vahdam', 'teabox': 'Teabox', 'tcotw': 'Tea Culture of the World', 'sancha': 'Sancha', 'goldentips': 'Golden Tips', 'goodricke': 'Goodricke',
 'udyan': 'Udyan', 'makaibari': 'Makaibari', 'organicindia': 'Organic India (Tata)', 'kaahu': 'Kaahu', 'mittal': 'Mittal Teas', 'happyvalley': 'Happy Valley Organic (new)', 'jayshree': 'Jay Shree Tea (new)'}
SITE = {'dorje': 'https://dorjeteas.com', 'vahdam': 'https://www.vahdam.in', 'teabox': 'https://in.teabox.com', 'tcotw': 'https://www.teacultureoftheworld.com', 'sancha': 'https://www.sanchatea.com',
 'goldentips': 'https://www.goldentipstea.in', 'goodricke': 'https://goodricketea.in', 'udyan': 'https://udyantea.com', 'makaibari': 'https://makaibari.in', 'organicindia': 'https://organicindia.com',
 'kaahu': 'https://kaahuteas.com', 'mittal': 'https://www.mittalteas.com', 'happyvalley': 'https://happyvalleyorganictea.com', 'jayshree': 'https://jayshreetea.com'}
# Per-brand strategy (our one-line read of the evidence) + who/how/offer
STRAT = {
 'vahdam': 'Has turned Meta into a supplements shop: joint, curcumin, hormone and weight hooks for 35+ buyers, creator videos and a money-back line, always with "up to 30% off + free gifts". Tea is barely advertised.',
 'teabox': 'One seasonal push: a Diwali chai gift pack with 3 freebies, run as 32 near-identical scarcity ads ("Last 500 units left") all started 13 Oct. The India site leans on ₹399 free shipping and COD.',
 'tcotw': 'Wellness-benefit tea bags (throat, skin, hair, stress) plus premium-origin hero teas (Makaibari, Japanese, Moroccan). Some ads send people to Blinkit and Zepto instead of the site. Code-gated AOV tiers, heavy on Google.',
 'sancha': 'Heritage boutique ("master tea taster since 1981"): wellness chai and herbal blends, wedding and corporate gifting via WhatsApp, and a chai video running since Nov 2025. 2 free samples and coasters on every order.',
 'goldentips': 'Low-key range-discovery ads ("22+ Second Flush 2026 teas", carousel by tea type), the oldest running since Aug. Seasonal codes, a 9% newsletter discount and Smile.io loyalty.',
 'goodricke': 'Estate names plus catalogue retargeting that shows the price ("Your stash is probably running low… restock"), and festive gifting. One catalogue ad has run since 25 May. 17 Google ads in 30 days (52 last week).',
 'udyan': 'No Meta ads found; 4 Google ads in 30 days. Competes on the site: sitewide "up to 15% + extra 20% off", 3 free samples, ₹399 free shipping and COD.',
 'makaibari': 'Estate and biodynamic story; 22 active Meta ads (19 started in the last week, up from 7) and 86 Google ads in 30 days (5 last week). Wins on Amazon with sponsored listings and "Limited time deal" badges. Site: 5% prepaid discount, loyalty points, subscriptions.',
 'organicindia': 'Tata-owned wellness brand: supplements and tulsi teas sent to Amazon and Blinkit ("Delivered in 10 mins"). Site has swapped its Diwali sale for a "Winter Wellness Sale": up to 25% off herbal supplements and teas + extra 5% prepaid (PREPAY5) + free gift above ₹999.',
 'kaahu': 'Ultra-premium rare-harvest storytelling ("The least processed tea in the world", "The Most Refreshing Tea of India"). Meta active ads down to 3 (11 last week), all started 12 Nov, now led by "India\'s Finest Green Tea from Darjeeling". No Google ads in 30 days. 10% off the first order (KAAHUNEW).',
 'mittal': 'Price-point hooks ("Perfect Pour @₹499", "Brewing Luxury @ ₹499", "Matcha now at 50% off", COD); all 10 active ads started 16 Nov (13 last week) for value buyers, plus separate B2B bulk-supply ads.',
 'happyvalley': 'Scaling: 16 active Meta ads (18 last week; 8 started in the last week, newest today), price-in-the-headline catalogue ads (First Flush ₹799, White ₹699, Moonlight ₹849, MeghTara Duo ₹399, Second Flush ₹420). Site still has 23% off tins; sponsored on Amazon.',
 'jayshree': 'Garden-discovery angle (25 g "Discovery Lots", "What makes Darjeeling Second Flush so exceptional?") with 10% off the first order (FIRST10) and free delivery over ₹999; 27 active Meta ads (14 started in the last week) and 32 Google ads in 30 days (back up from 4 last week).',
 'dorje': 'Story and estate ads (Selim Hill, plastic-free pyramids, "champagne of teas"). Price, reviews and the 7-day guarantee rarely appear in ads, and only one sampled ad shows an offer (20% off above ₹999).',
}
# Live offers seen on the site (India view) 23 Nov 2026 (only sites whose banner changed are edited; other cells as of 16 Nov)
OFFERS = {
 'dorje': ['Banner now reads "20% Off on Cart Value Over ₹999!" (Diwali wording dropped)', 'Free above ₹399 (policy page); COD ₹50 fee', 'None seen (no popup)', 'None', 'Growave loyalty app; monthly/quarterly subscriptions', SITE['dorje']],
 'vahdam': ['Products 15–27% off; ads say "up to 30% off + free gifts"', 'Free above ₹599', 'None seen', '2 free minis ≥₹999; free full-size gift ≥₹1,499; extra 10% ≥₹1,999', '—', SITE['vahdam']],
 'teabox': ['Diwali gift pack + 3 freebies (ad); trial packs', 'Free above ₹399; COD; 2–4 days', 'Klaviyo email form; back-in-stock alerts', 'Free playing cards, glass cup + scoop with gift pack (ad)', '—', SITE['teabox']],
 'tcotw': ['10% off ≥₹1,999 (TCWTEA10); 20% off ≥₹2,999 (TCW20)', 'Free above ₹499; cart progress bar', 'None seen', '—', '—', SITE['tcotw']],
 'sancha': ['10% off ≥₹1,000 (SANCHA10)', 'Free above ₹400; same-day delivery ₹150', 'Email signup: 10% off first order ≥₹1,000', '2 free samples + 2 tea coasters with every order', 'WhatsApp for wedding/corporate gifting', SITE['sancha']],
 'goldentips': ['Pre-Christmas: buy 7 teas, code XMAS15; Sale section', 'Free above ₹499', 'Newsletter: 9% off first order', '—', 'Smile.io loyalty; WhatsApp button', SITE['goldentips']],
 'goodricke': ['Ads: "up to 20% off storewide"; catalogue ads show prices', 'Free above ₹499 (prepaid); COD fee ₹100', 'None seen', '—', '—', SITE['goodricke']],
 'udyan': ['"Up to 15% off + extra 20% off sitewide", no code', 'Free above ₹399; COD', 'None seen', '3 free samples', '—', SITE['udyan']],
 'makaibari': ['Flat 5% off prepaid (auto at checkout)', 'Threshold not stated', 'Klaviyo email form', '—', 'Nector loyalty points; subscriptions', SITE['makaibari']],
 'organicindia': ['Winter Wellness Sale: up to 25% off herbal supplements & teas; extra 5% prepaid (PREPAY5)', 'Free delivery across India; COD', 'None seen', 'Free mystery gift worth ₹250 ≥₹999', '—', SITE['organicindia']],
 'kaahu': ['Flat 10% off first order (KAAHUNEW)', 'Free above ₹500 (policy page)', 'First-order code in banner', '—', 'GoKwik checkout; WhatsApp', SITE['kaahu']],
 'mittal': ['"Save up to 50%" (e.g. First Flush ₹120, was ₹240); matcha 50% off (ad)', '"COD & free delivery"', 'None seen', '—', 'Growave loyalty; GoKwik + Shopflo checkout', SITE['mittal']],
 'happyvalley': ['23% off all tin caddies at checkout, no code; Meta catalogue ads show First Flush ₹799, Second Flush ₹420, White ₹699', 'Free ₹1,299+; COD +₹40 (as seen 13 Nov)', 'None seen', '—', '—', SITE['happyvalley']],
 'jayshree': ['10% off first purchase (FIRST10); 25 g Discovery Lots', 'Free above ₹999', 'First-order code in banner and ads', '—', '—', SITE['jayshree']],
}
EX = {  # 2–3 short quotes per brand, each from the ad's own Ad Library page
 'vahdam': [('Joint Comfort or Your Money Back | Up to 30% Off + Free Gifts', '1843899736605094'), ('Day 1 — waistband already less tight by evening… Day 7 — it\'s just part of the routine now.', '2130406977838547'), ('Creator: "70 plus, and lifting heavier than ever."', '990073296981054')],
 'teabox': [('Last 500 Units Left! Selling out fast 🚨', '1061505710259083'), ('The Chai Valencia Diwali Gift Pack comes with 10 Indian chais + 3 festive freebies.', '2064503284197492')],
 'tcotw': [('Sore Throat? Brew Relief.', '920771951000915'), ('Makaibari. A timeless expression of fine tea.', '1088194040712655')],
 'sancha': [('Super Food Mint Masala Chai: "Take a sip toward better health" (running since 26 Nov 2025)', '1167947112208003'), ('🎁 A Gift They’ll Remember · Personalised for Your Celebration (WhatsApp)', '2266918057485692'), ('Introducing Hibiscus & Rose Herbal Iced Tea', '1343602271115967')],
 'goldentips': [('Discover 22+ exceptional Second Flush 2026 teas', '1083891037834189'), ('Find Your Perfect Tea (carousel: Assam, Darjeeling, Masala Chai)', '1632878605023008')],
 'goodricke': [('Your Goodricke stash is probably running low by now… Restock before you run out. (Badamtam 100 g ₹283.05)', '3010723519287421'), ('Grab upto 20% Off on Goodricke Tea! (running since 25 May)', '1289111820042801'), ('Gift Moments of Togetherness', '2013661286007426')],
 'makaibari': [('Shop Bai Mu Dan Loose White Tea Pack - Tin Caddy', '4584400368466321')],
 'organicindia': [('Delivered in 10 mins on Blinkit ⚡', '1091266617060268'), ('Nature\'s Fiber Support (links to Amazon)', '964602996331254')],
 'kaahu': [('The Least Processed Tea in the World', '1827557738397110'), ('The Most Refreshing Tea of India', '1632599678503583'), ('Do you feel an after taste of bitterness in your Green Tea?', '1059235940508962')],
 'mittal': [('Perfect Pour @₹499', '1178808974810963'), ('Premium Japanese Matcha ~ now at 50% Off… COD Available', '2158048714800993')],
 'happyvalley': [('Spring Bloom First Flush · ₹799 (catalogue ad)', '3837832316365232'), ('Darjeeling Moonlight Tea · ₹849', '2976678962708222'), ('Second flush, ₹420 | White tea, ₹699 | Rose tea, ₹332 | Moonlight, ₹849', '910269062078016')],
 'jayshree': [('Choose The Leaf Not Just The Label', '2157520721511551'), ('Try our 25g Discovery Lots… without committing to a larger pack', '1661132685379596')],
 'dorje': [('The champagne of teas, from Selim Hill', '1808466920467846'), ('For full houses and fuller cups · 20% off above Rs 999', '2159433274653937'), ('Your teabag is plastic, Ours is not.', '938301518827590')],
}
THUMB = {k: f'/ads/{k}.jpg' for k in ['dorje', 'vahdam', 'teabox', 'tcotw', 'sancha', 'goldentips', 'goodricke', 'organicindia', 'kaahu', 'mittal', 'happyvalley', 'jayshree']}
THUMB_ID = {'dorje': '1808466920467846', 'vahdam': '1843899736605094', 'teabox': '1061505710259083', 'tcotw': '920771951000915', 'sancha': '1343602271115967', 'goldentips': '1083891037834189',
 'goodricke': '3010723519287421', 'organicindia': '1091266617060268', 'kaahu': '1827557738397110', 'mittal': '1178808974810963', 'happyvalley': '1080834954943208', 'jayshree': '1609933397573838'}
AMZ = [  # amazon.in search cards 16 Nov 2026 (S = sponsored); % off = card's struck-through price vs current, as shown
 ['Makaibari', 'Summer Solstice Muscatel ₹581, Smoky Roasted 100 g ₹278, Green Valley Apoorva ₹180: "Limited time deal" badges + sponsored; holds the top sponsored slots on first-flush and Darjeeling searches', 'https://www.amazon.in/s?k=teabox+darjeeling+tea'],
 ['Vahdam', 'First Flush 100 g ₹529 (4.1★, 1.5K), Darjeeling 250 g ₹799, Summer Second Flush 15 bags ₹219; sponsored on its own-brand search', 'https://www.amazon.in/s?k=vahdam+darjeeling+tea'],
 ['Sancha', 'Rare Darjeeling First Flush 2026, 100 g ₹599 (4.2★, 272)', 'https://www.amazon.in/s?k=darjeeling+first+flush+tea'],
 ['Gopaldhara', 'Sponsored in 5 cards for "darjeeling first flush tea": Mellow Gold 200 g ₹780, Muscatel 2nd flush ₹630', 'https://www.amazon.in/s?k=darjeeling+first+flush+tea'],
 ['Happy Valley', '1854 Vintage Heritage Black ₹892 (4.4★, 16), sponsored on "dorje teas"', 'https://www.amazon.in/s?k=dorje+teas'],
 ['Goodricke', 'Roasted 250 g ₹279; Thurbo ₹351; Castleton ₹574 "Limited time deal" (organic, not sponsored)', 'https://www.amazon.in/s?k=darjeeling+tea'],
 ['Jay Shree (Bagicha)', 'Roasted Darjeeling 250 g ₹275 and Reserve ₹200, sponsored on "darjeeling tea"', 'https://www.amazon.in/s?k=darjeeling+tea'],
 ['Dorje', 'Sponsored #2 and #4 (Kukicha ₹359.10, Roasted ₹224.10) plus #7 (First Flush 100 g ₹377.10 vs ₹499 on dorjeteas.com) for "darjeeling first flush tea"; now #5 sponsored on "darjeeling tea" (was not in top 16); #1 and #3 sponsored on "second flush darjeeling tea"', 'https://www.amazon.in/s?k=darjeeling+first+flush+tea'],
]
PATTERNS = [
 'The offer goes in the headline. Vahdam ("Up to 30% off + free gifts"), Mittal ("@₹499"), Happy Valley ("Second Flush, ₹199") and Jay Shree ("10% off for first-time buyers") all put a price or % in the headline. Dorje shows an offer in 1 of its sampled ads, and only in the sub-line.',
 'Free gifts and samples are everywhere: Vahdam gives free minis and a full-size gift as the order grows, Sancha 2 samples + coasters, Udyan 3 samples, Organic India a ₹250 mystery gift, Teabox 3 freebies with its gift pack. Dorje has none.',
 'A 9–10% first-order code is standard (Golden Tips 9%, Sancha 10%, Kaahu 10%, Jay Shree 10%), shown in the banner or an email form. Dorje shows no first-order offer or email/WhatsApp popup.',
 'The biggest spenders sell benefits, not origin: Vahdam, Organic India, Tea Culture and Sancha lead with sleep, throat, joints, skin and weight. Only Kaahu, Golden Tips, Happy Valley and Jay Shree lead with the garden.',
 'Retargeting uses catalogue ads with the price and a "restock" nudge (Goodricke). Tea Culture and Organic India also send ad traffic to Blinkit, Zepto and Amazon.',
 'Seasonal bursts: Teabox started all 32 Diwali ads on one day; Happy Valley has a Pujo hook; Golden Tips and Sancha are already on Christmas. Dorje\'s banner has dropped "Diwali" but is still the old 20% over ₹999 offer; Organic India moved from a Diwali to a Winter Wellness sale.',
 'Long-running ads (likely winners): Sancha\'s mint masala chai video (~352 days), Goodricke\'s catalogue ads (~172 days), Golden Tips\' range carousel (~93 days).',
 'Google ads, last 30 days (India, 23 Nov): Sancha ~300, Makaibari 86 (5 last week), Tea Culture 40, Jay Shree 32 (4 last week), Organic India 30, Vahdam 18, Goodricke 16, Mittal 14, Golden Tips 10, Teabox 10, Udyan 5, Happy Valley 4, Kaahu 0 (the Transparency page count is approximate). Dorje\'s domain shows 4, all under the advertiser "Bella Vita Agri Products Private Limited".',
]
GAPS = [
 'No big advertiser combines single estate + organic + price per cup. Happy Valley is scaling it now (18 active Meta ads, all started 15 Nov); Dorje\'s First Flush is still cheaper (₹499 vs ₹616 after Happy Valley\'s 23% tin discount, and vs a ₹1,699 peer median).',
 'No tea brand advertises a taste guarantee (Vahdam\'s money-back line is for supplements). Dorje has a 7-day taste replacement and 4.62★ from 600+ reviews; both are missing from its ads.',
 '"Plastic-free pyramid" is Dorje-only, and the wellness tea-bag angle Tea Culture and Vahdam use fits it.',
 'Happy Valley\'s current Meta ads show Second Flush ₹420 (vs Dorje ₹399) and First Flush ₹799 (vs Dorje ₹499); the ₹199 Second Flush seen last week is no longer what its ads show. Dorje should not chase that price; its edge is reviews, flush freshness and the guarantee.',
]
PLAY = [  # n, move, what, budget share (estimate), measure
 ['1', 'Put price per cup in the headline', 'Static + 15-s video: "Single-estate First Flush from Selim Hill, ₹499 for 40 cups (~₹12.50 a cup)" (add "organic" only once certification is confirmed). Test against the current story ads, with the same audiences.', '30% of total (estimate)', 'Cost per purchase and ROAS vs the ~1.6 baseline after 14 days'],
 ['2', 'Lead with proof and the guarantee', '"4.62★ from 600+ reviews. Don\'t love it? We replace it within 7 days." Use real review quotes (UGC style) on First and Second Flush.', '20% of total (estimate)', 'CTR and purchase rate vs move 1'],
 ['3', 'Replace the stale Diwali banner with an order ladder', 'Free shipping ₹399 → free 10 g sample above ₹699 → 20% off (or a free mini) above ₹999. Show it in a cart progress bar and repeat it in ads.', 'No media cost; sample cost per order (estimate)', 'AOV and share of orders above ₹699 / ₹999'],
 ['4', 'Add a first-order WhatsApp/email capture', '10% off the first order (market standard 9–10%) for a WhatsApp opt-in via Zoko. Feeds abandoned-cart flows (recovery now 8.7%).', 'No media cost (estimate)', 'Opt-in rate; abandoned-cart recovery from 8.7% toward 12–15% (estimate)'],
 ['5', 'Fix retargeting before spending more', 'Exclude purchasers in the 4 prospecting campaigns; cap retargeting frequency (now ~5.9) at about 3/week; switch retargeting to catalogue ads that show price + reviews, with a 30–45-day "restock" ad for past buyers (Goodricke-style).', '20% of total (estimate)', 'Frequency, retargeting ROAS, repeat rate'],
 ['6', 'Winter wellness + plastic-free teabags', 'Chamomile, Kahwa and Lavender blends and pyramid bags: "Plastic-free bedtime tea" / "Winter throat comfort", to meet Tea Culture and Vahdam on benefits. Fix the 15-bag stock first.', '15% of total (estimate)', 'ROAS on teabags; ₹/bag kept vs peers'],
 ['7', 'Christmas / New Year gifting burst', 'Gift boxes from ₹749, with a 2-week scarcity window (Teabox-style) and personalisation via WhatsApp (Sancha-style).', '15% of total, 1 Dec–31 Dec (estimate)', 'Gift-box revenue vs last season'],
 ['8', 'Fix Amazon pricing, then advertise there', 'Close the 10–44% Amazon-vs-site gap; run time-boxed Amazon deals/coupons instead of a permanently lower price, and Sponsored Products on "darjeeling first flush tea", where Makaibari, Happy Valley and Gopaldhara already bid.', 'Amazon budget TBD, needs Amazon access', 'Amazon rank for the 2 Darjeeling searches; site conversion'],
]
TEST = 'Test plan (estimate): run 3 creatives per angle for 14 days with buyer exclusions on. Judge on cost per purchase and ROAS against the ~1.6 baseline. Pause an angle when it has spent about 3× the target cost per purchase without beating the baseline, and move its budget to the winner. Suggested split of Meta budget: 50% prospecting (moves 1–2, Advantage+ broad), 20% retargeting/catalogue (move 5), 15% wellness teabags (move 6), 15% seasonal gifting (move 7).'
out = {'checked': '23 Nov 2026', 'pages': PAGES, 'name': NAME, 'site': SITE, 'strat': STRAT, 'offers': OFFERS, 'ex': EX, 'thumb': THUMB, 'thumbId': THUMB_ID, 'amz': AMZ,
       'patterns': PATTERNS, 'gaps': GAPS, 'play': PLAY, 'test': TEST, 'adUrl': AD, 'pageUrl': PG, 'gaUrl': GA}
json.dump(out, open(os.path.join(H, 'ads_offers.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('ads_offers.json', os.path.getsize(os.path.join(H, 'ads_offers.json')), 'bytes')
