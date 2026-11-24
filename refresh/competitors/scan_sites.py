#!/usr/bin/env python3
"""Weekly helper: public homepage + flagship product page signals (apps, reviews, free-shipping text). Writes competitors/signals.json."""
import re, json, urllib.request, datetime, os, html
H = os.path.dirname(os.path.abspath(__file__))
SITES = {'dorje': ('https://dorjeteas.com', 'first-flush-tea'), 'vahdam': ('https://www.vahdam.in', 'darjeeling-first-flush-black-tea'),
 'udyan': ('https://udyantea.com', 'darjeeling-spring-splendour-black-tea'), 'goldentips': ('https://www.goldentipstea.in', None),
 'makaibari': ('https://makaibari.in', 'summer-solstice-muscatel-tin-caddy'), 'tcotw': ('https://www.teacultureoftheworld.com', 'darjeeling-first-flush'),
 'mittal': ('https://www.mittalteas.com', None), 'sancha': ('https://www.sanchatea.com', 'rare-darjeeling-first-flush-spring-season'),
 'karmakettle': ('https://www.karmakettle.com', 'darjeeling-first-flush'), 'teabox': ('https://in.teabox.com', None), 'goodricke': ('https://goodricketea.in', None), 'kaahu': ('https://kaahuteas.com', 'darjeeling'), 'organicindia': ('https://organicindia.com', None)}
APPS = {'GoKwik': r'gokwik', 'Shopflo': r'shopflo', 'Razorpay Magic': r'magic-checkout|razorpay.*magic|rzp.*magic|magic\.razorpay', 'Shiprocket checkout': r'fastrr|shiprocket.*checkout',
 'Simpl': r'getsimpl', 'Judge.me': r'judge\.me|judgeme', 'Yotpo': r'yotpo', 'Okendo': r'okendo', 'Loox': r'loox\.io', 'Stamped': r'stamped\.io',
 'Klaviyo': r'klaviyo', 'Omnisend': r'omnisend', 'Privy': r'privy', 'WhatsApp button': r'wa\.me/|api\.whatsapp\.com|whatsapp-widget|wa-widget',
 'Zoko': r'zoko', 'Interakt': r'interakt', 'Wati': r'wati\.io', 'Gallabox': r'gallabox', 'Recharge': r'rechargecdn|rechargepayments', 'Appstle subs': r'appstle',
 'Spin wheel': r'spin.?(the|to).?wheel|wheelio|spin-wheel', 'Google Ads tag': r'AW-\d{6,}', 'Meta pixel': r'fbq\(|connect\.facebook\.net', 'GA4': r'G-[A-Z0-9]{8,}'}
def get(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 Chrome/120'}), timeout=30).read().decode('utf-8', 'ignore')
    except Exception as e:
        return ''
def txt(h): return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', ' ', h))))
out = {'checked': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M IST'), 'sites': {}}
for k, (base, handle) in SITES.items():
    home = get(base); prod = get(f'{base}/products/{handle}') if handle else ''
    pj = get(f'{base}/products/{handle}.js') if handle else ''
    pol = {n: txt(get(f'{base}/policies/{n}')) for n in ('shipping-policy', 'refund-policy')}
    ship_pol = sorted({m.strip()[:140] for m in re.findall(r'[^.]{0,80}(?:free (?:shipping|delivery)|above ₹ ?[\d,]+|over ₹ ?[\d,]+|Rs\.? ?[\d,]+)[^.]{0,60}', pol['shipping-policy'], re.I)})[:4]
    ret_pol = sorted({m.strip()[:160] for m in re.findall(r'[^.]{0,80}(?:\d+ ?(?:hours|days)|non-returnable|no returns?|not accept)[^.]{0,60}', pol['refund-policy'], re.I)})[:4]
    both = home + prod; t = txt(home) + ' ' + txt(prod)
    fs = sorted({m.strip()[:110] for m in re.findall(r'[^.|!]{0,60}free (?:shipping|delivery)[^.|!]{0,60}', t, re.I)})[:6]
    cod = bool(re.search(r'\bCOD\b|cash on delivery', t, re.I))
    rat = re.findall(r'"ratingValue"\s*:\s*"?([\d.]+)"?[^}]{0,80}?"(?:reviewCount|ratingCount)"\s*:\s*"?(\d+)', prod) or re.findall(r'"(?:reviewCount|ratingCount)"\s*:\s*"?(\d+)"?[^}]{0,80}?"ratingValue"\s*:\s*"?([\d.]+)', prod)
    subs = '"selling_plan_groups":[{' in pj.replace(' ', '')
    codes = sorted(set(re.findall(r'(?:use|code)[:\s]+["\']?([A-Z][A-Z0-9]{3,14})\b', t)))[:6]
    out['sites'][k] = {'url': base, 'product': f'{base}/products/{handle}' if handle else None, 'home_ok': bool(home), 'apps': [a for a, r in APPS.items() if re.search(r, both, re.I)],
        'free_ship_text': fs, 'ship_policy': ship_pol, 'return_policy': ret_pol, 'cod_mention': cod, 'product_rating': rat[:1], 'subscription_on_product': subs, 'codes_seen': codes,
        'has_product_schema': '"@type":"Product"' in prod.replace(' ', '') or '"@type": "Product"' in prod}
    print(k, json.dumps(out['sites'][k], ensure_ascii=False)[:1400])
json.dump(out, open(os.path.join(H, 'signals.json'), 'w'), separators=(',', ':'))
