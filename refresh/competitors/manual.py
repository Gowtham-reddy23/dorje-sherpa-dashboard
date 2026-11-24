#!/usr/bin/env python3
"""Hand-checked competitor facts (Meta counts, Amazon cards, Dorje site rating re-checked 23 Nov 2026 IST; policy/shipping/returns text last read 16 Nov 2026). Edit here when re-checking; build_competitors.py merges with prices.json/signals.json.
Every fact carries a source URL. Meta counts = Meta Ad Library estimated active ads reaching India (user-meta-ads ads_library_search).
Amazon = amazon.in search results page (rating, count, price shown on the card). Google = google.com hl=en gl=in from a non-India server
(desktop, logged out) - local results in India can differ."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
CHK = '23 Nov 2026'
AL = 'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id='
AMZ = 'https://www.amazon.in/s?k='
B = {
 'dorje': dict(type='Single estate (Selim Hill), D2C + Amazon', ship='Free above ₹399 (policy); ₹50 below; COD ₹50 fee', ship_src='https://dorjeteas.com/policies/shipping-policy',
   returns='Wrong/missing items: tell us within 48 h. Stale/bad taste: replacement within 7 days', ret_src='https://dorjeteas.com/policies/refund-policy',
   offers='Monthly/quarterly subscription variants; cart progress bar to 20% off; gift & combo boxes from ₹749', offers_src='https://dorjeteas.com/',
   site_rating='4.63★ (606 reviews) on First Flush; 4.62★ (341) on Second Flush', rating_src='https://dorjeteas.com/products/first-flush-tea',
   amazon='4.0★ (314) First Flush black 100 g ₹377.10; 4.0★ (169) Muscatel Second Flush ₹269.10; 4.2★ (206) Kashmiri Kahwa 100 g ₹359.10; 4.0★ (345) Chamomile 15 bags ₹202.50; 4.3★ (21) Kukicha 100 g ₹359.10', amazon_src=AMZ+'dorje+teas',
   meta=48, meta_src=AL+'302251162980335', meta_angles='Story/estate-led: "The champagne of teas, from Selim Hill", "Your teabag is plastic, ours is not", "Still deciding? Take 20% off"'),
 'vahdam': dict(type='Big D2C brand (multi-estate, wellness)', ship='Free above ₹599 (site banner); policy page also says ₹50 below ₹499', ship_src='https://www.vahdam.in/policies/shipping-policy',
   returns='Not found on policy page', ret_src='https://www.vahdam.in/policies/refund-policy',
   offers='2 free minis above ₹999; free full-size gift above ₹1,499; extra 10% off above ₹1,999', offers_src='https://www.vahdam.in/',
   site_rating='Not shown on flagship First Flush page', rating_src='https://www.vahdam.in/products/darjeeling-first-flush-black-tea',
   amazon='4.1★ (1.5K) First Flush 100 g ₹529; 4.1★ (323) Summer Second Flush 15 bags ₹219; sponsored on "vahdam darjeeling tea"', amazon_src=AMZ+'vahdam+darjeeling+tea',
   meta=624, meta_src=AL+'1491430561130722', meta_angles='Offer-led wellness/supplements: "Up to 30% off + free gifts", curcumin, joint support, hormones. Very little Darjeeling'),
 'teabox': dict(type='Big D2C brand (multi-estate Darjeeling specialist)', ship='Free above ₹399; COD (pay 5% online up to ₹2,000); 2–4 days', ship_src='https://in.teabox.com/policies/shipping-policy',
   returns='Damaged: tell us within 24 h with photos; separate "not happy with the taste" clause', ret_src='https://in.teabox.com/policies/shipping-policy',
   offers='Trial packs; Klaviyo email capture', offers_src='https://in.teabox.com/',
   site_rating='4.40★ (10) on Darjeeling Himalayan Blend', rating_src='https://in.teabox.com/products/darjeeling-himalayan-blend',
   amazon='4.3★ (10.6K) Chamomile Green 25 bags ₹236', amazon_src=AMZ+'chamomile+pyramid+tea+bags',
   meta=32, meta_src=AL+'509251098946332', meta_angles='Scarcity: "Last 500 units left! Selling out fast"'),
 'udyan': dict(type='Darjeeling D2C (multi-estate)', ship='Free above ₹399; COD available', ship_src='https://udyantea.com/policies/shipping-policy',
   returns='No returns for taste ("teas you didn\'t personally like")', ret_src='https://udyantea.com/policies/refund-policy',
   offers='3 free samples; most products shown ~10–15% off', offers_src='https://udyantea.com/',
   site_rating='4.44★ (9) First Flush; 4.63★ (19) Second Flush', rating_src='https://udyantea.com/products/darjeeling-spring-splendour-black-tea',
   amazon='Not in the top 16 for the searches checked', amazon_src=AMZ+'darjeeling+tea', meta=0, meta_src=AL, meta_angles='No active ads found by name search'),
 'goldentips': dict(type='Darjeeling retailer (very wide range)', ship='Free above ₹499; flat fee below', ship_src='https://www.goldentipstea.in/policies/shipping-policy',
   returns='7 days with photos; teas otherwise non-returnable', ret_src='https://www.goldentipstea.in/policies/refund-policy',
   offers='Pre-Christmas: buy 7 teas, code XMAS15; WhatsApp chat button', offers_src='https://www.goldentipstea.in/',
   site_rating='Not shown in page data', rating_src='https://www.goldentipstea.in/',
   amazon='4.2★ (87) Summer Boost Second Flush 250 g ₹361', amazon_src=AMZ+'second+flush+darjeeling+tea', meta=8, meta_src=AL+'1142228112496445', meta_angles='Range discovery: "Discover Darjeeling Tea" (oldest active since 12 Aug)'),
 'makaibari': dict(type='Single estate (Makaibari), D2C + Amazon', ship='Threshold not stated on policy page', ship_src='https://makaibari.in/policies/shipping-policy',
   returns='Cancel within 48 h of ordering', ret_src='https://makaibari.in/policies/refund-policy',
   offers='Subscriptions on products; Klaviyo email capture; Shiprocket checkout', offers_src='https://makaibari.in/',
   site_rating='Few site reviews (5.0★, 1 on Summer Solstice)', rating_src='https://makaibari.in/products/summer-solstice-muscatel-tin-caddy',
   amazon='4.3★ (402) First Flush 100 g ₹684; 4.2★ (687) Smoky Roasted ₹278; 4.2★ (231) Black 250 g ₹849; heavy sponsored placements', amazon_src=AMZ+'darjeeling+first+flush+tea',
   meta=22, meta_src=AL+'1132999483237601', meta_angles='"Harvest Duo: First + Second Flush"; white tea tin caddy'),
 'goodricke': dict(type='Estate group (Castleton, Thurbo, Margaret\'s Hope…)', ship='Free above ₹499 prepaid; ₹75 below; ₹100 COD fee', ship_src='https://goodricketea.in/policies/shipping-policy',
   returns='Report within 48 h of receipt', ret_src='https://goodricketea.in/policies/refund-policy', offers='Estate names front and centre', offers_src='https://goodricketea.in/',
   site_rating='Not shown in page data', rating_src='https://goodricketea.in/',
   amazon='4.3★ (5.2K) Roasted 250 g ₹264; 4.2★ (3K) Thurbo ₹330; 4.3★ (2.7K) Castleton ₹574–789', amazon_src=AMZ+'darjeeling+tea', meta=24, meta_src=AL+'226335644073160', meta_angles='Estate names + product-catalogue ads with prices'),
 'tcotw': dict(type='Premium D2C (multi-origin, resells Makaibari)', ship='Free above ₹499, with a cart "₹X away from free shipping" bar', ship_src='https://www.teacultureoftheworld.com/policies/shipping-policy',
   returns='Cancel within 24 h of ordering', ret_src='https://www.teacultureoftheworld.com/policies/refund-policy',
   offers='10% off above ₹1,999 (TCWTEA10); 20% off above ₹2,999 (TCW20)', offers_src='https://www.teacultureoftheworld.com/',
   site_rating='Not shown in page data', rating_src='https://www.teacultureoftheworld.com/products/darjeeling-first-flush', amazon='Not in the top 16 for the searches checked', amazon_src=AMZ+'darjeeling+tea',
   meta=55, meta_src=AL+'800871513266267', meta_angles='Wellness problem/solution ("Sore throat? Brew relief", "Skin glow tea") + "Makaibari. A timeless expression of fine tea."'),
 'mittal': dict(type='Delhi tea house (multi-origin)', ship='"COD & free delivery" on site; threshold not stated', ship_src='https://www.mittalteas.com/',
   returns='30-day return policy', ret_src='https://www.mittalteas.com/policies/refund-policy', offers='GoKwik + Shopflo checkout; WhatsApp button; many items 40–50% off MRP', offers_src='https://www.mittalteas.com/',
   site_rating='Not shown in page data', rating_src='https://www.mittalteas.com/', amazon='5.0★ (1) Royal Muscatel ₹400', amazon_src=AMZ+'darjeeling+first+flush+tea',
   meta=10, meta_src=AL+'234289799983346', meta_angles='Price point "Perfect Pour @₹499", matcha, B2B bulk supply'),
 'sancha': dict(type='Premium tea boutique (Delhi)', ship='Free above ₹400 (tea only; gift boxes ₹100)', ship_src='https://www.sanchatea.com/policies/shipping-policy',
   returns='No returns or replacements after the order is processed', ret_src='https://www.sanchatea.com/policies/refund-policy',
   offers='2 free tea samples + 2 coasters with every order; 10% off ₹1,000 first order for email sign-up; Interakt WhatsApp', offers_src='https://www.sanchatea.com/',
   site_rating='Not shown in page data', rating_src='https://www.sanchatea.com/products/rare-darjeeling-first-flush-spring-season',
   amazon='4.1★ (271) First Flush ₹599; 4.1★ (150) Chamomile 25 pyramid bags ₹320', amazon_src=AMZ+'darjeeling+first+flush+tea',
   meta=28, meta_src=AL+'203853022985323', meta_angles='"Shop [tea] now" product ads: iced tea, masala chai, matcha, oolong'),
 'karmakettle': dict(type='Kolkata tea house', ship='Threshold not stated', ship_src='https://www.karmakettle.com/policies/shipping-policy',
   returns='Cancel within 24 h; no opened products', ret_src='https://www.karmakettle.com/policies/refund-policy', offers='Omnisend email; Stamped reviews', offers_src='https://www.karmakettle.com/',
   site_rating='4.29★ (7) First Flush; 4.83★ (6) Muscatel', rating_src='https://www.karmakettle.com/products/darjeeling-first-flush', amazon='Not in the top 16 for the searches checked', amazon_src=AMZ+'darjeeling+tea',
   meta=0, meta_src=AL, meta_angles='No active ads found by name search'),
 'kaahu': dict(type='Ultra-premium estate selections', ship='Free above ₹500', ship_src='https://kaahuteas.com/policies/shipping-policy',
   returns='No returns or replacements after processing', ret_src='https://kaahuteas.com/policies/refund-policy', offers='Exclusive "Day 1 pluck" lots (Glenburn, Castleton, Margaret\'s Hope); GoKwik; WhatsApp', offers_src='https://kaahuteas.com/',
   site_rating='Not shown', rating_src='https://kaahuteas.com/products/darjeeling', amazon='Not checked', amazon_src=AMZ+'kaahu',
   meta=3, meta_src=AL+'722512074285827', meta_angles='"The least processed tea in the world", "Hand plucked under the full moon"'),
 'organicindia': dict(type='Wellness/herbal mass brand (Tata)', ship='Free delivery across India; COD; extra 10% off prepaid (PREPAY10)', ship_src='https://organicindia.com/',
   returns='Exchange/return request within 7 days; damage within 24 h', ret_src='https://organicindia.com/policies/refund-policy', offers='Sale: up to 30% off + 25% cashback; mystery gift above ₹999', offers_src='https://organicindia.com/',
   site_rating='Not shown', rating_src='https://organicindia.com/', amazon='4.3★ (2.4K) Simply Chamomile 25 bags ₹138', amazon_src=AMZ+'chamomile+pyramid+tea+bags', meta=287, meta_src=AL+'194411414144', meta_angles='Catalogue ads for tulsi/wellness teas (keyword-filtered count)'),
}
# Kaahu product titles carry no flush, so price/100 g is worked out by hand from kaahuteas.com/products.json
KAAHU_PER100 = {'min': 1998, 'max': 8396, 'note': 'Darjeeling 40 g ₹799 = ₹1,998/100 g; Glenburn Moonshine 25 g ₹2,099 = ₹8,396/100 g', 'src': 'https://kaahuteas.com/products.json'}
# Amazon.in search: position of each brand's first card (S = sponsored). Source: amazon.in search page, 23 Nov 2026.
AMAZON_SERP = [
 {'q': 'darjeeling first flush tea', 'url': AMZ+'darjeeling+first+flush+tea', 'top': 'Makaibari (1 S, 6, 15 S), Gopaldhara (5 S, 8, 10, 13 S), Goodwyn (3 S), Sancha (9), Jay Shree Bagicha (11 S)', 'dorje': '#2 (sponsored) Kukicha ₹359.10, #4 (sponsored) Roasted ₹224.10, #7 First Flush black 100 g ₹377.10 (not sponsored)'},
 {'q': 'darjeeling tea', 'url': AMZ+'darjeeling+tea', 'top': 'Makaibari (1 S, 3 S, 13 S), Bagicha (2 S, 12 S), Gopaldhara (4 S), Lipton (6–7), Goodricke (8, 10, 16), Duncans (9, 11 S)', 'dorje': '#5 (sponsored) – Roasted Tea ₹224.10 (last week: not in top 16)'},
 {'q': 'second flush darjeeling tea', 'url': AMZ+'second+flush+darjeeling+tea', 'top': 'Makaibari (2 S, 5 S, 12 S), Happy Valley (4 S), Golden Tips (7), Gopaldhara (8, 9), Goodricke Castleton (10), Sancha (16)', 'dorje': '#1 (sponsored) Muscatel Second Flush ₹269.10; #3 (sponsored) First Flush ₹377.10; #6 (not sponsored)'},
 {'q': 'chamomile pyramid tea bags', 'url': AMZ+'chamomile+pyramid+tea+bags', 'top': 'Luxmi (2 S), Sancha (3 S, 8), Blue Tea (4 S, 14 S), Vahdam (5 S, 15 S), Organic India (9), Teabox (10), Twinings (13 S)', 'dorje': '#1 (sponsored) – 15 pyramid bags ₹202.50'},
]
# Dorje's own Amazon cards vs the same item on dorjeteas.com (one-time price), 23 Nov 2026
AMAZON_VS_SITE = [
 ['Kashmiri Kahwa loose 100 g', 359.10, 499], ['Lavender loose 100 g', 359.10, 499], ['Jasmine loose 100 g', 359.10, 499], ['Kukicha 100 g', 359.10, 499],
 ['Muscatel Second Flush green 100 g', 269.10, 399], ['Original Chai 250 g', 224.10, 299],
 ['Chamomile 15 pyramid bags', 202.50, 360], ['First Flush black 100 g', 377.10, 499], ['First Flush green 100 g', 377.10, 499],
]
json.dump({'checked': CHK, 'brands': B, 'kaahu_per100': KAAHU_PER100, 'amazon_serp': AMAZON_SERP, 'amazon_vs_site': AMAZON_VS_SITE,
           'amazon_vs_site_src': [AMZ+'dorje+teas', 'https://dorjeteas.com/products.json']}, open(os.path.join(H, 'manual.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('manual.json written')
