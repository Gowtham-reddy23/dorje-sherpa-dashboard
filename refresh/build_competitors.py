#!/usr/bin/env python3
"""Merges competitors/prices.json (pull_competitors.py), competitors/signals.json (competitors/scan_sites.py),
competitors/manual.json (competitors/manual.py) and competitors/google.json (competitors/save_serp.py) into
competitors.json (Founders app, key `comp`) and comp_line.txt (`const COMP: any = ...;` line for BOTH Pages).
Fast and offline: safe to run in the 6-hourly refresh. The pulls themselves are WEEKLY (see README)."""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(H, 'competitors')
L = lambda n: json.load(open(os.path.join(C, n)))
P, S, M, G = L('prices.json'), L('signals.json'), L('manual.json'), L('google.json')
ORDER = ['dorje', 'teabox', 'vahdam', 'udyan', 'goldentips', 'makaibari', 'goodricke', 'tcotw', 'mittal', 'sancha', 'karmakettle', 'kaahu']
NAME = {k: P['brands'][k]['name'] for k in P['brands']}; NAME['organicindia'] = 'Organic India'
def kd(k, kind):
    b = P['brands'].get(k, {}); x = (b.get('by_kind') or {}).get(kind)
    if k == 'kaahu' and kind == 'First Flush': return {'median': None, 'min': M['kaahu_per100']['min'], 'max': M['kaahu_per100']['max'], 'n': 0}
    return x
price = []
for k in ORDER:
    b = P['brands'][k]; ff, sf = kd(k, 'First Flush'), kd(k, 'Second Flush')
    price.append({'k': k, 'brand': NAME[k], 'ff': ff and ff['median'], 'ffMin': ff and ff['min'], 'ffMax': ff and ff['max'], 'ffN': ff and ff['n'],
                  'sf': sf and sf['median'], 'sfMin': sf and sf['min'], 'sfMax': sf and sf['max'], 'sfN': sf and sf['n'],
                  'packs': b.get('packs_g'), 'onSale': b.get('on_sale_share'), 'oos': b.get('oos_share'), 'loose': b.get('variants'),
                  'gifts': b.get('gift_n'), 'giftMin': b.get('gift_min'), 'src': (M['kaahu_per100']['src'] if k == 'kaahu' else b['url'] + '/products.json')})
bags = []
for k in ORDER + ['organicindia']:
    b = P['brands'].get(k, {}); hb = b.get('bags_herbal') or b.get('bags')
    if not hb or hb['n'] < 2: continue   # too few boxes to compare
    eg = b.get('bag_eg') or {}
    bags.append({'k': k, 'brand': NAME[k], 'perBag': hb['median'], 'min': hb['min'], 'max': hb['max'], 'n': hb['n'], 'pyramid': b.get('bags_pyramid_n', 0),
                 'eg': f"{eg.get('p','')} – {eg.get('n')} bags ₹{eg.get('inr', 0):,.0f}" if eg else '', 'herbal100': (b.get('herbal_loose') or {}).get('median'),
                 'herbalN': (b.get('herbal_loose') or {}).get('n'), 'src': b['url'] + '/products.json'})
offers = []
for k in ORDER + ['organicindia']:
    m, s = M['brands'][k], S['sites'].get(k, {})
    offers.append({'k': k, 'brand': NAME[k], 'type': m['type'], 'ship': m['ship'], 'returns': m['returns'], 'offers': m['offers'], 'rating': m['site_rating'], 'amazon': m['amazon'],
                   'checkout': ', '.join(a for a in s.get('apps', []) if a in ('Razorpay Magic', 'GoKwik', 'Shopflo', 'Shiprocket checkout')) or 'Shopify checkout',
                   'capture': ', '.join(a for a in s.get('apps', []) if a in ('Klaviyo', 'Omnisend', 'Zoko', 'Interakt', 'Wati', 'WhatsApp button', 'Gallabox')) or '—',
                   'reviewsApp': ', '.join(a for a in s.get('apps', []) if a in ('Judge.me', 'Yotpo', 'Okendo', 'Loox', 'Stamped')) or '—', 'cod': s.get('cod_mention'),
                   'src': [m['ship_src'], m['ret_src'], m['offers_src'], m['rating_src'], m['amazon_src']]})
ads = sorted([{'k': k, 'brand': NAME[k], 'active': M['brands'][k]['meta'], 'angles': M['brands'][k]['meta_angles'], 'src': M['brands'][k]['meta_src']}
              for k in ORDER if M['brands'][k]['meta'] is not None], key=lambda a: -(a['active'] or 0))
DOM = {'dorjeteas.com': 'Dorje', 'makaibari.in': 'Makaibari', 'goldentipstea.in': 'Golden Tips', 'in.teabox.com': 'Teabox', 'teabox.com': 'Teabox', 'vahdam.in': 'Vahdam',
       'gopaldharaindia.com': 'Gopaldhara', 'gopaldhara.com': 'Gopaldhara', 'mayukhtea.com': 'Mayukh', 'goodricketea.in': 'Goodricke', 'mittalteas.com': 'Mittal',
       'sanchatea.com': 'Sancha', 'teacultureoftheworld.com': 'Tea Culture', 'udyantea.com': 'Udyan', 'amazon.in': 'Amazon', '10+': 'Reddit/Quora', 'goodwyntea.com': 'Goodwyn',
       'tatatea1868.com': 'Tata 1868', 'nathmullstea.in': 'Nathmull\'s', 'octavius.in': 'Octavius', 'flipkart.com': 'Flipkart', 'jiomart.com': 'JioMart', 'firstflush.in': 'firstflush.in'}
BR = ['Sancha', 'Goodricke', 'Vahdam', 'Teabox', 'Mayukh', 'Makaibari', 'Golden Tips', 'Dorje', 'Gopaldhara', 'Udyan', 'Mittal']
search = []
for q, r in G.items():
    doms = [re.sub(r'^https?://(www\.)?', '', x.split(' :: ')[0]).strip('/') for x in r['res']]
    names = [DOM.get(d, d) for d in doms]
    pos = next((i + 1 for i, n in enumerate(names) if n == 'Dorje'), None)
    ai = r.get('ai') or ''
    cited = [b for b in BR if re.search(re.escape(b), ai, re.I)] if ai.startswith('AI Overview') else None
    search.append({'q': q, 'dorje': pos, 'top': names[:5], 'aio': ai.startswith('AI Overview'), 'cited': cited, 'src': 'https://www.google.com/search?hl=en&gl=in&q=' + q.replace(' ', '+')})
QO = ['best darjeeling tea', 'first flush darjeeling tea buy online', 'second flush darjeeling tea', 'darjeeling tea online', 'darjeeling tea price', 'organic darjeeling tea',
      'muscatel darjeeling tea', 'single estate darjeeling tea', 'darjeeling green tea', 'darjeeling tea gift box']
search.sort(key=lambda s: QO.index(s['q']) if s['q'] in QO else 99)
avs = [{'item': a, 'amazon': z, 'site': s, 'gap': round(100 * (s - z) / s)} for a, z, s in M['amazon_vs_site']]
d = P['brands']['dorje']; dff = kd('dorje', 'First Flush')['min']; dsf = kd('dorje', 'Second Flush')['min']; dsf2 = kd('dorje', 'Second Flush')['max']
peers_ff = sorted(p['ff'] for p in price if p['k'] not in ('dorje', 'kaahu') and p['ff'])
dbag = next(b for b in bags if b['k'] == 'dorje')
peer_bags = sorted(b['perBag'] for b in bags if b['k'] != 'dorje')
med = lambda xs: xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2
gap_lo, gap_hi = min(a['gap'] for a in avs), max(a['gap'] for a in avs)
findings = [
 f"Dorje is the value pick for single-estate Darjeeling: First Flush ₹{dff}/100 g vs a ₹{med(peers_ff):,.0f} median for the {len(peers_ff)} D2C peers checked (Teabox ₹{kd('teabox','First Flush')['median']:,}, Vahdam ₹{kd('vahdam','First Flush')['median']:,}, Tea Culture ₹{kd('tcotw','First Flush')['median']:,}). Second Flush ₹{dsf}–{dsf2}/100 g is also below most peers. Only Udyan (₹{kd('udyan','First Flush')['median']}) and Karma Kettle (₹{kd('karmakettle','First Flush')['median']}) come close on First Flush. Watch: Happy Valley Organic now runs 16 active Meta ads (8 started in the last week; 18 a week ago) with prices in the headline (First Flush ₹799, Second Flush ₹420).",
 f"The same Dorje items are {gap_lo}–{gap_hi}% cheaper on Dorje's own Amazon listings than on dorjeteas.com (e.g. Kahwa 100 g ₹359 on Amazon vs ₹499 on site). Shoppers who compare have a reason to leave the site cart: a likely (not measured) drag on the 8.7% checkout recovery.",
 f"Pyramid teabags cost more per bag than most rivals: Dorje ₹21–24/bag on site vs a ₹{med(peer_bags):.1f} median (Teabox ₹10.4, Organic India ₹11, Mittal ₹13.8; only Sancha ₹20.9 and Tea Culture ₹19.1 come close). The printed catalogue (₹450/₹799) is the struck-through price; the site sells at ₹360/₹640.",
 "Dorje has the strongest on-site review proof checked (4.63★ from 606 reviews on First Flush) and a rare 7-day taste-replacement promise; most peers refuse taste returns. Neither is used in ads today.",
 "Offers: Teabox and Udyan match Dorje's ₹399 free-shipping line; Teabox, Udyan, Mittal and Organic India push COD. Sancha, Udyan and Vahdam add free samples with orders; Tea Culture shows a 'free shipping in ₹X' cart bar. Dorje has none of the sample offers.",
 f"Meta: Vahdam runs ~{next(a['active'] for a in ads if a['k']=='vahdam')} active India ads (offer-led, mostly supplements); Dorje ~{next(a['active'] for a in ads if a['k']=='dorje')} (story-led); Teabox {next(a['active'] for a in ads if a['k']=='teabox')} (scarcity 'last 500 units'). Udyan has no active Meta ads; Karma Kettle was not re-checked this week.",
 f"Search: Dorje is in Google's top 3 for {sum(1 for x in search if x['dorje'] and x['dorje'] <= 3)} of {len(search)} key searches (#1 'second flush darjeeling tea', #2 'first flush… buy online' and 'muscatel'), but is not in the top 10 for 'organic darjeeling tea' or 'single estate darjeeling tea', the two phrases that describe Dorje best. Google's AI answers name Dorje in {sum(1 for x in search if x['cited'] and 'Dorje' in x['cited'])} of {sum(1 for x in search if x['aio'])}; for 'best darjeeling tea' they cite Sancha and Goodricke. On Amazon, Makaibari, Gopaldhara and Goodricke own 'darjeeling tea' and 'darjeeling first flush tea'; Dorje is now sponsored #2/#4 (and #7 not sponsored) for 'darjeeling first flush tea' and #5 sponsored for 'darjeeling tea' (not in the top 16 last week).",
]
win = [["Price per 100 g", "Win", f"First Flush ₹{dff} vs ₹{med(peers_ff):,.0f} peer median; Second Flush ₹{dsf}–{dsf2}"],
       ["Reviews on site", "Win", "4.63★ (606) on First Flush – the most proof among the sites checked"],
       ["Taste guarantee", "Win", "7-day replacement if stale/bad; Udyan, Sancha, Kaahu refuse taste returns"],
       ["Google organic (flush searches)", "Win", "Top 3 for second flush (#1), first flush, muscatel, best darjeeling tea, green tea, gift box"],
       ["Google for 'organic' / 'single estate'", "Lose", "Not in the top 10 for either, though both are Dorje's core claims"],
       ["Free shipping line", "Even", "₹399 = Teabox, Udyan; lower than Vahdam ₹599, Golden Tips/Goodricke/Tea Culture ₹499 – but Dorje's cart bar shows a different amount"],
       ["Amazon price vs site", "Lose", f"Own Amazon listings {gap_lo}–{gap_hi}% cheaper than the site"],
       ["Teabag price per bag", "Lose", f"₹21–24 vs ₹{med(peer_bags):.1f} peer median"],
       ["Stock on flagship 250 g", "Lose", "First & Second Flush 250 g out of stock – the best ₹/100 g packs"],
       ["Order sweeteners", "Lose", "No free samples / gift-with-purchase tiers (Sancha, Udyan, Vahdam all do this)"],
       ["Amazon search visibility", "Lose", "#5 (sponsored) for 'darjeeling tea' (new this week); #2, #4 (sponsored) and #7 for 'darjeeling first flush tea'; #1 sponsored for 'second flush'"],
       ["AI answers", "Lose", "Dorje named only for 'darjeeling tea online' and 'gift box'; 'best darjeeling tea' cites Sancha and Goodricke"]]
actions = [
 {'n': 1, 'title': 'Close the Amazon-vs-site price gap', 'why': f"Same items are {gap_lo}–{gap_hi}% cheaper on Dorje's Amazon listings than on the site.", 'do': 'Either price Amazon at or above the site, or give site buyers a visible extra (free 10 g sample + infuser, or subscription price). We recheck prices weekly.', 'impact': 'Protects site margin and checkout completion (estimate: part of the 8.7% → 15% recovery goal)', 'owner': 'Gowtham / Amazon ops', 'est': True},
 {'n': 2, 'title': 'Restock First & Second Flush 250 g', 'why': 'They are Dorje\'s best value packs (₹500 and ₹360/100 g) and Vahdam shows 60% of its loose Darjeeling out of stock – shoppers are looking.', 'do': 'Restock or hide; add "back in stock" WhatsApp alert via Zoko.', 'impact': 'Higher order value; fewer bounced carts', 'owner': 'Ops', 'est': False},
 {'n': 3, 'title': 'One free-shipping line: ₹399 everywhere + cart bar', 'why': 'Policy says ₹399; the cart shows a different amount. ₹399 already matches Teabox and Udyan and beats Vahdam (₹599) and the ₹499 group.', 'do': 'Set the cart bar to ₹399 ("₹X away from free shipping", like Tea Culture). Keep ₹399 in ads.', 'impact': 'Removes a checkout surprise; supports AOV', 'owner': 'Theme (fix ready, awaiting publish)', 'est': False},
 {'n': 4, 'title': 'Add a free-sample tier', 'why': 'Sancha (2 samples + coasters), Udyan (3 samples) and Vahdam (2 minis above ₹999) all sweeten orders.', 'do': 'Free 10 g flush sample above ₹699; use it in the abandoned-cart WhatsApp/email copy ("your free First Flush sample is waiting").', 'impact': 'Estimate: +₹40–60 AOV and a reason to come back to the cart', 'owner': 'Growth', 'est': True},
 {'n': 5, 'title': 'Put price-per-cup and reviews into Meta ads', 'why': f"Dorje ads are story-led; rivals lead with offers. Dorje's real edge is ₹{dff}/100 g single-estate (≈₹12.5/cup, 40 cups) with 4.63★ from 606 reviews.", 'do': 'Test 3 creatives: "Single-estate First Flush ₹499 – estate brands charge ₹1,300–2,400", "4.63★ from 606 tea drinkers", "Don\'t like it? We replace it in 7 days."', 'impact': 'Estimate: aim to lift Meta ROAS from ~1.6 toward 2.0+', 'owner': 'Performance', 'est': True},
 {'n': 6, 'title': 'Reposition pyramid teabags', 'why': f"₹21–24/bag on site vs ₹10–14 at Teabox, Organic India, Mittal; Dorje's Amazon 15-bag box is ₹13.5/bag.", 'do': 'Sell as premium (whole-leaf Selim Hill green + real flowers, plastic-free) in bundles of 2–3 boxes, or lead with the 30-bag box (₹21.3/bag). Fix catalogue vs site prices.', 'impact': 'Clearer value story; fewer price-driven drop-offs', 'owner': 'Growth', 'est': False},
 {'n': 7, 'title': 'Publish the SEO/GEO theme to win AI answers', 'why': 'AI answers for "best darjeeling tea" cite Sancha and Goodricke, and Dorje is not in the top 10 for "organic darjeeling tea" or "single estate darjeeling tea".', 'do': 'Publish the prepared SEO theme (Product + Offer + AggregateRating schema); add llms.txt with estate facts and prices; add a Selim Hill single-estate organic page (certification, altitude, flush calendar) targeting both phrases.', 'impact': 'More AI citations and rich results (stars, price) in Google', 'owner': 'Gowtham (approve publish)', 'est': False},
 {'n': 8, 'title': 'Amazon: own the generic Darjeeling searches', 'why': 'Makaibari, Gopaldhara, Duncans and Goodricke take the sponsored and organic top spots; Dorje is only visible on "second flush" and "chamomile pyramid".', 'do': 'When Amazon Ads is connected: Sponsored Products on "darjeeling tea" and "darjeeling first flush tea"; improve 3.4–3.8★ listings (Original Chai, Monsoon green).', 'impact': 'Needs Amazon Ads data to size', 'owner': 'Amazon (pending access)', 'est': True},
]
mismatch = [
 'Pyramid teabags: catalogue ₹450 (15) / ₹799 (30) are the struck-through prices on the site; the live price is ₹360 / ₹640.',
 'Catalogue lists Jasmine, Rose, Blue Pea, Hibiscus, Lavender and Ginger Marigold teabags as 30-bag only; the site also has 15-bag versions (all out of stock).',
 'Catalogue lists Honey Lemon teabags as 15-bag only; the site has 15 and 30, both out of stock.',
 'The site has a "Green Tea Monsoon Flush Pyramid Teabags – 30" (₹640) that is not in the catalogue.',
 'Catalogue "Blue Pea" loose blend is "Blue Pea Mint Tea" on the site. Loose flush teas, wellness blends (₹499/100 g) and Original Chai (₹299 = 250 g) match.',
]
out = {'checked': M['checked'], 'pricesChecked': P['checked'], 'findings': findings, 'price': price, 'bags': bags, 'offers': offers, 'ads': ads, 'search': search,
       'amazonSerp': M['amazon_serp'], 'amazonVsSite': avs, 'amazonVsSiteSrc': M['amazon_vs_site_src'], 'win': win, 'actions': actions, 'mismatch': mismatch,
       'method': 'Prices: public Shopify products.json of each INR store (loose-leaf Darjeeling only; subscriptions, tea bags, gift boxes and multi-packs excluded; median of all pack sizes). Teabags: price ÷ bag count on herbal/flavoured boxes. Meta: Meta Ad Library estimated active ads reaching India. Google: google.com (hl=en, gl=in) from a non-India server, logged out; local results can differ. Amazon: amazon.in search cards.'}
# ---- Ads & Offers intel (competitors/ads_offers.json = curated; ads_meta.json = parsed Ad Library + Google ATC) ----
AO = json.load(open(os.path.join(H, 'competitors', 'ads_offers.json')))
AM = json.load(open(os.path.join(H, 'competitors', 'ads_meta.json')))['brands']
ORDER = ['dorje', 'vahdam', 'teabox', 'tcotw', 'sancha', 'goldentips', 'goodricke', 'udyan', 'makaibari', 'organicindia', 'kaahu', 'mittal', 'happyvalley', 'jayshree']
ANGCOLS = [('Health', ['Health / wellness']), ('Price/%', ['Price / discount']), ('Free gift', ['Free gift / sample']), ('Scarcity', ['Scarcity / urgency']),
           ('Festive/gift', ['Festive / seasonal', 'Gifting']), ('Origin/craft', ['Origin / estate', 'Quality / craft']), ('Creator', ['UGC / creator']),
           ('Q-commerce', ['Quick-commerce / retail']), ('1st order', ['First-order / signup offer']), ('Plastic-free', ['Plastic-free / sustainability'])]
ao = []
for k in ORDER:
    m = AM.get(k, {}); g = m.get('google') or {}
    pid = AO['pages'].get(k)
    ao.append({'k': k, 'brand': AO['name'][k], 'strategy': AO['strat'][k], 'meta': m.get('active'), 'sampled': m.get('sampled'), 'last7': m.get('last7'),
               'oldest': m.get('oldest'), 'oldestDays': m.get('oldestDays'), 'formats': m.get('formats', {}), 'angles': m.get('angles', {}),
               'google30d': g.get('ads30d'), 'googleAdv': g.get('advertiser'), 'googleSrc': AO['gaUrl'] + g['domain'] if g.get('domain') else None,
               'metaSrc': AO['pageUrl'] + pid if pid else 'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=Udyan%20tea',
               'offers': AO['offers'][k], 'examples': [{'text': t, 'url': AO['adUrl'] + i} for t, i in AO['ex'].get(k, [])],
               'thumb': AO['thumb'].get(k), 'thumbUrl': AO['adUrl'] + AO['thumbId'][k] if k in AO['thumbId'] else None})
out['ao'] = {'checked': AO['checked'], 'brands': ao, 'angleCols': [c for c, _ in ANGCOLS], 'angleKeys': [ks for _, ks in ANGCOLS], 'amz': AO['amz'], 'patterns': AO['patterns'],
             'gaps': AO['gaps'], 'play': AO['play'], 'test': AO['test'],
             'method': 'Meta: Meta Ad Library, country India, active ads; counts are Meta\'s estimate. Copy, format and landing page come from each ad\'s Ad Library page (a sample of 2–4 ads per brand); angle tags are keyword matches on the headlines and sampled copy, so they show direction, not exact shares. "Running since" is only shown when every active ad was returned. Google: Ads Transparency Center, region India, last 30 days, by website. Offers: each homepage with India store settings on 13 Nov 2026 (banner, popup, cart). Amazon: amazon.in search cards. Strategy lines and the playbook are our analysis; budget splits and impacts are estimates.'}

# ---- Ad types & reach (competitors/ad_types_reach.json, built weekly by competitors/reach/build_reach.py) ----
ATR = json.load(open(os.path.join(H, 'competitors', 'ad_types_reach.json')))
def _mix(l, n=4): return ', '.join(f"{k} {v}%" for k, v in (l or [])[:n]) or '—'
def _inr(v): return '₹' + format(int(round(v)), ',')
own = ATR['own']; ot = own['total']
TAKE = [
 "On visible Meta activity Dorje is already third of 14 (estimated pressure index 57), behind only Vahdam (84) and Organic India (72) and ahead of every Darjeeling estate brand. More ads won't fix much; making the current spend work harder will.",
 f"Instagram Reels took {_inr(next(p['spend'] for p in own['byPosition'] if p['k']=='instagram · instagram_reels'))} at ROAS {next(p['roas'] for p in own['byPosition'] if p['k']=='instagram · instagram_reels')}, the weakest big placement. Facebook Feed ({next(p['roas'] for p in own['byPosition'] if p['k']=='facebook · feed')}), Facebook Reels ({next(p['roas'] for p in own['byPosition'] if p['k']=='facebook · facebook_reels')}) and Stories do better. Move Reels budget to Feed and Stories, or rebuild the Reels creative.",
 f"WhatsApp marketing messages took {_inr(next(p['spend'] for p in own['byPosition'] if p['k']=='whatsapp · whatsapp_marketing_messages'))} (about a quarter of Meta spend) at about ₹1.6 per impression and ROAS {next(p['roas'] for p in own['byPosition'] if p['k']=='whatsapp · whatsapp_marketing_messages')}. Sancha and Mittal use click-to-WhatsApp ads into their own chat instead. Test click-to-WhatsApp into Zoko against the paid message placement.",
 "By format, Dorje's single-image ads (ROAS " + str(next(f['roas'] for f in own['byFormat'] if f['k']=='Single image')) + ") and flexible ads (" + str(next(f['roas'] for f in own['byFormat'] if f['k'].startswith('Flexible'))) + ") beat video/Reels (" + str(next(f['roas'] for f in own['byFormat'] if f['k']=='Video / Reel')) + "), which get the most spend. Most peers lean on single images (Sancha 86%, Organic India 85%, Tea Culture 81%). Shift spend toward price-and-proof statics.",
 "Low-quality placements are being hit over and over: Audience Network frequency " + str(next(p['freq'] for p in own['byPosition'] if p['k']=='audience_network · an_classic')) + ", right column " + str(next(p["freq"] for p in own["byPosition"] if p["k"]=="facebook · right_hand_column")) + ", WhatsApp Status " + str(next(p["freq"] for p in own["byPosition"] if p["k"]=="whatsapp · status")) + ". Exclude them or cap frequency. Golden Tips and Sancha keep evergreen ads running 2–3 months (median age 93 and 56 days); Dorje's evergreen winners should get the same treatment instead of being relaunched in batches.",
]
out['atr'] = dict(ATR, takeaways=TAKE)

json.dump(out, open(os.path.join(H, 'competitors.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
# Canvas-ready, compact copy for both Pages (one line: `const COMP: any = ...;`)
SHORT = lambda n: n.replace(' Teas', '').replace('Tea Culture of the World', 'Tea Culture').replace('VAHDAM India', 'Vahdam').replace('Teabox India', 'Teabox').replace('Sancha Tea', 'Sancha')
r = lambda n: '—' if n is None else '₹' + f'{round(n):,}'
ffb = sorted([p for p in price if p['ff']], key=lambda p: -p['ff'])
bgb = sorted(bags, key=lambda b: -b['perBag'])
TONE = {'Win': 'success', 'Lose': 'danger'}
FT = ['Dorje is the price-value leader', 'Our Amazon listings undercut our own site', 'Teabags cost more per bag than rivals', 'Best review proof, not used in ads', 'Rivals sweeten orders; Dorje does not', 'Rivals lead ads with offers', "Search: strong on flushes, missing on 'organic' and 'single estate'"]
cv = {'checked': out['checked'],
 'findings': [{'lead': str(i + 1), 'title': t, 'detail': re.sub(r'^(Offers|Meta|Search): ', '', f)} for i, (t, f) in enumerate(zip(FT, findings))],
 'ffBars': [{'label': SHORT(p['brand']), 'value': p['ff'], 'display': r(p['ff']), 'meta': f"Second Flush {r(p['sf'])}"} for p in ffb],
 'ffEm': [i for i, p in enumerate(ffb) if p['k'] == 'dorje'][0],
 'bagBars': [{'label': SHORT(b['brand']), 'value': b['perBag'], 'display': f"₹{b['perBag']}", 'meta': f"{b['n']} boxes"} for b in bgb],
 'bagEm': [i for i, b in enumerate(bgb) if b['k'] == 'dorje'][0],
 'priceRows': [[p['brand'], ('₹1,998–8,396' if p['k'] == 'kaahu' else r(p['ff'])), r(p['sf']), ', '.join(map(str, p['packs'] or [])), '—' if p['oos'] is None else f"{p['oos']}%"] for p in price],
 'offerRows': [[o['brand'], o['ship'], o['returns'], o['offers'], o['checkout'], o['rating'], o['amazon']] for o in offers],
 'adRows': [[a['brand'], '—' if a['active'] is None else str(a['active']), a['angles']] for a in ads],
 'searchRows': [[x['q'], {'text': f"#{x['dorje']}", 'tone': 'success' if x['dorje'] <= 3 else 'warning'} if x['dorje'] else {'text': 'Not top 10', 'tone': 'danger'}, ' · '.join(x['top']), (', '.join(x['cited']) if x['cited'] else 'No brand named') if x['aio'] else 'No AI answer'] for x in search],
 'amzRows': [[a['q'], a['top'], a['dorje']] for a in M['amazon_serp']],
 'avsRows': [[a['item'], f"₹{a['amazon']:g}", r(a['site']), {'text': f"{a['gap']}%", 'tone': 'danger' if a['gap'] >= 30 else 'warning'}] for a in avs],
 'winRows': [[w[0], {'text': w[1], 'tone': TONE[w[1]]} if w[1] in TONE else w[1], w[2]] for w in win],
 'actRows': [[str(a['n']), a['title'], a['do'], a['impact'] + (' (estimate)' if a['est'] and 'stimate' not in a['impact'] else ''), a['owner']] for a in actions],
 'mismatch': mismatch, 'method': out['method'],
 'sources': 'Sources: each store’s /products.json and policy pages; Meta Ad Library (facebook.com/ads/library, country IN, active); google.com (gl=in); amazon.in search. Links per fact are in the Founders web app (Competitors tab).',
}
def _cell(n): return str(n) if n else ''
cv['ao'] = {
 'cards': [{'lead': b['brand'], 'title': ('—' if b['meta'] is None else f"{b['meta']} Meta") + ' · ' + (f"{b['google30d']} Google" if b['google30d'] not in (None,) else '— Google'), 'detail': b['strategy']} for b in ao],
 'offerRows': [[b['brand']] + b['offers'][:5] for b in ao],
 'angleRows': [[b['brand'], '—' if b['meta'] is None else str(b['meta']), b['google30d'] or '—'] + [_cell(sum(b['angles'].get(x, 0) for x in ks)) for ks in out['ao']['angleKeys']] for b in ao],
 'angleCols': ['Brand', 'Meta ads', 'Google 30 d'] + out['ao']['angleCols'],
 'copyRows': [[b['brand'], e['text']] for b in ao for e in b['examples'][:2]],
 'amzRows': [a[:2] for a in AO['amz']],
 'patterns': AO['patterns'], 'gaps': AO['gaps'],
 'playRows': [p[:4] for p in AO['play']], 'test': AO['test'],
}

_B = ATR['brands']
cv['atr'] = {
 'apiRows': [[b['name'], str(b['api']), str(b['active']), (b['ig'] or {}).get('followers') or '—', (b['sw'] or {}).get('visits') or '—', (b['sw'] or {}).get('paidKw') or '—'] for b in _B],
 'typeRows': [[b['name'], _mix(b.get('formats'), 3), f"{b['multiPct']}%" if b.get('multiPct') is not None else '—', str(b.get('variantsPerConcept') or '—'), f"{b['pricePct']}%" if b.get('pricePct') is not None else '—', _mix(b.get('langs'), 2), f"{b['covered']} of {b['active']}" if b.get('covered') else '—'] for b in _B],
 'placeRows': [[b['name'], _mix(b.get('placements'), 6), _mix(b.get('ctas'), 3), _mix(b.get('landing'), 3)] for b in _B],
 'cadRows': [[b['name'], str(b.get('new7', '—')), str(b.get('new28', '—')), str(b.get('perWeek', '—')), str(b.get('medianDays') if b.get('medianDays') is not None else '—'), _mix(b.get('longevity'), 4)] for b in _B],
 'realRows': [[NAMEB, r['dates'], r['type'], (f"EU reach {r['euReach']:,} accounts · " + ', '.join(r['countries'])) if r['type'] == 'EU' else f"Spend {r['spend']} · impressions {r['impr']}", (f"Ages {', '.join(k + ' ' + str(v) + '%' for k, v in sorted(r['ageMix'].items(), key=lambda x: -x[1])[:2])} · men {r['genderMix'].get('Male', 0)}%" if r['type'] == 'EU' else f"Audience {r['aud']}"), r.get('copy', '(old political/issue-tagged ad)')] for b in _B for r in b['real'] for NAMEB in [b['name']]],
 'ownMetrics': [{'value': _inr(ot['amount_spent']), 'label': 'Spend (30 days)'}, {'value': format(int(ot['impressions']), ','), 'label': 'Impressions'}, {'value': format(int(ot['reach']), ','), 'label': 'Reach (accounts)'},
   {'value': str(round(ot['frequency'], 2)), 'label': 'Frequency'}, {'value': _inr(ot['cpm']), 'label': 'CPM'}, {'value': f"{ot['ctr']}%", 'label': 'CTR (all clicks)'}, {'value': str(round(ot['purchase_roas'], 2)), 'label': 'ROAS'}, {'value': str(int(ot['omni_purchase'])), 'label': 'Purchases'}],
 'ownFmtRows': [[f['k'], str(f['n']), _inr(f['spend']), f"{f['share']}%", format(f['impr'], ','), _inr(f['cpm']) if f['cpm'] else '—', f"{f['ctr']}%", str(f['purch']), str(f['roas'])] for f in own['byFormat']],
 'ownPlatRows': [[p['k'].replace('_', ' ').title(), _inr(p['spend']), f"{p['share']}%", format(p['impr'], ','), _inr(p['cpm']) if p['cpm'] else '—', f"{p['ctr']}%", str(p['purch']), str(p['roas'])] for p in own['byPlatform'] if p['spend'] >= 100],
 'ownPosRows': [[p['k'].replace('_', ' '), _inr(p['spend']), format(p['impr'], ','), format(p['reach'], ','), str(p['freq']), _inr(p['cpm']), f"{p['ctr']}%", str(p['purch']), str(p['roas'] or '—')] for p in own['byPosition']],
 'ownNote': f"Dorje's own Meta account, {own['period']} (read-only). {own['adsWithSpend']} ads spent. Format comes from ad names and creative type (Reel/Video, Static, Carousel, Flex); 'Unlabelled' are concept tests without a format in the name. ROAS is spend-weighted from each ad. Link CTR by format = link clicks ÷ impressions. CTR on the cards is Meta's all-clicks CTR.",
 'takeaways': TAKE, 'limits': ATR['limits'], 'method': ATR['apiMethod'],
}

cv = {'atr': cv.pop('atr'), 'ao': cv.pop('ao'), **cv}  # 'atr','ao' first  # 'ao' first, so the rest of the line stays byte-identical week to week
open(os.path.join(H, 'comp_line.txt'), 'w').write('const COMP: any = ' + json.dumps(cv, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('competitors.json', os.path.getsize(os.path.join(H, 'competitors.json')) // 1024, 'KB |', len(price), 'brands |', len(search), 'queries')
for f in findings: print('-', f)
