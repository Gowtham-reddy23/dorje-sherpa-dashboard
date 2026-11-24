#!/usr/bin/env python3
"""WEEKLY (not part of the 6-hourly run). Public, read-only: GET <store>/products.json for Dorje + competitor
Shopify stores (prices in INR storefronts), keeps only Darjeeling loose-leaf variants and works out price per 100 g.
Writes competitors/prices.json (compact). Manual facts (shipping, reviews, ads, search) live in competitors_manual.json.
Then run build_competitors.py."""
import json, re, statistics, time, urllib.request, datetime, os
H = os.path.dirname(os.path.abspath(__file__))
STORES = {  # key: (name, storefront, INR?)
 'dorje': ('Dorje Teas', 'https://dorjeteas.com'),
 'vahdam': ('VAHDAM India', 'https://www.vahdam.in'),
 'udyan': ('Udyan Tea', 'https://udyantea.com'),
 'goldentips': ('Golden Tips', 'https://www.goldentipstea.in'),
 'makaibari': ('Makaibari', 'https://makaibari.in'),
 'tcotw': ('Tea Culture of the World', 'https://www.teacultureoftheworld.com'),
 'mittal': ('Mittal Teas', 'https://www.mittalteas.com'),
 'sancha': ('Sancha Tea', 'https://www.sanchatea.com'),
 'karmakettle': ('Karma Kettle', 'https://www.karmakettle.com'),
 'teabox': ('Teabox India', 'https://in.teabox.com'),
 'goodricke': ('Goodricke', 'https://goodricketea.in'),
 'kaahu': ('Kaahu Teas', 'https://kaahuteas.com'),
 'organicindia': ('Organic India (wellness only)', 'https://organicindia.com'),
}
HERB = r'chamomile|hibiscus|kahwa|rose|lavender|blue pea|butterfly pea|jasmine|earl grey|honey lemon|marigold|mint|tulsi|wellness|herbal'
BAGN = re.compile(r'(\d+)\s*(?:pyramid\s*)?(?:tea\s*)?(?:bags|teabags|sachets|pyramids)', re.I)
W = re.compile(r'(\d+(?:\.\d+)?)\s*(kg|kgs|g|gm|gms|gr|gram|grams)\b', re.I)
MULT = re.compile(r'(?:pack of|set of)\s*(\d+)|(\d+)\s*(?:x|\*)\s*(\d+)\s*g', re.I)
def grams(*txt):
    for t in txt:
        if not t: continue
        m = W.search(t)
        if m:
            g = float(m.group(1)) * (1000 if m.group(2).lower().startswith('kg') else 1)
            mm = MULT.search(t); k = int(mm.group(1) or mm.group(2)) if mm else 1
            if mm and mm.group(3) and abs(g - k * float(mm.group(3))) < 1: k = 1  # total already stated, e.g. '300 GM (3x100GM)'
            return g * k
    return None
def kind(t):
    t = t.lower()
    if 'green' in t: return 'Green'
    if 'white' in t: return 'White'
    if 'oolong' in t: return 'Oolong'
    if 'roast' in t: return 'Other Darjeeling'
    if 'first flush' in t or 'spring' in t: return 'First Flush'
    if 'second flush' in t or 'muscatel' in t or 'summer' in t: return 'Second Flush'
    if 'autumn' in t: return 'Autumn Flush'
    if 'green' in t: return 'Green'
    if 'white' in t: return 'White'
    if 'oolong' in t: return 'Oolong'
    return 'Other Darjeeling'
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (DorjeCompetitorCheck)'})
    return json.load(urllib.request.urlopen(req, timeout=30))
out = {'checked': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M IST'), 'brands': {}}
for key, (name, base) in STORES.items():
    rows, gifts, bags, herbs, page = [], [], [], [], 1
    try:
        while page <= 4:
            ps = get(f'{base}/products.json?limit=250&page={page}')['products']
            if not ps: break
            for p in ps:
                tl = p['title']
                # pyramid teabags + wellness blends (all brands): per-bag and per-100 g
                if re.search(r'bag|pyramid|sachet', tl + ' ' + p['handle'], re.I) and not re.search(r'gift card|infuser|mug', tl, re.I):
                    for v in p['variants']:
                        m = BAGN.search(v.get('title') or '') or BAGN.search(tl)
                        if m and float(v['price']) > 0 and 5 <= int(m.group(1)) <= 200 and not re.search(r'pack of|subscri|x\s*\d', v.get('title') or '', re.I):
                            bags.append({'p': tl[:70], 'n': int(m.group(1)), 'inr': float(v['price']), 'per_bag': round(float(v['price']) / int(m.group(1)), 1),
                                         'herbal': bool(re.search(HERB, tl, re.I)), 'pyramid': 'pyramid' in (tl + p['handle']).lower(), 'avail': bool(v.get('available', True))})
                elif re.search(HERB, tl, re.I) and not re.search(r'gift|combo|box|set|collection|assort|sampler', tl, re.I):
                    for v in p['variants']:
                        g = grams(v.get('title') or '', tl)
                        if g and g >= 20 and float(v['price']) > 0 and not re.search(r'subscri|deliver|pack of', v.get('title') or '', re.I):
                            herbs.append({'p': tl[:70], 'g': g, 'inr': float(v['price']), 'per100': round(float(v['price']) / g * 100)})
                if key == 'organicindia': continue
                blob = (p['title'] + ' ' + ' '.join(p.get('tags') or []) + ' ' + (p.get('product_type') or '')).lower()
                if 'darjeeling' not in blob and key not in ('dorje', 'kaahu'): continue
                if re.search(r'gift|hamper|combo|\bbox\b|\bset\b|collection|assort', p['title'], re.I) and 'darjeeling' in blob:
                    gifts.append({'p': p['title'][:70], 'inr': min(float(v['price']) for v in p['variants'])})
                if re.search(r'bags', p['handle']) or re.search(r'tea ?bag|pyramid|\bbags\b|kettle|\bcups?\b(?! ?/)|mug|infuser|strainer|teapot|accessor|postcard|gift|hamper|combo|\bbox\b|\bset\b|collection|assort|sampler|chai|masala|bundle|duo|trio|pack of', p['title'], re.I): continue
                for v in p['variants']:
                    vt = v.get('title') or ''
                    if re.search(r'tea ?bag|\bbags\b|subscri|deliver|pack of|\bx\s*\d', vt, re.I): continue
                    g = grams(vt, p['title']) or (v.get('grams') or None)
                    price = float(v['price'])
                    if not g or g < 10 or price <= 0: continue
                    cap = float(v['compare_at_price']) if v.get('compare_at_price') else None
                    rows.append({'p': p['title'][:80], 'h': p['handle'], 'v': vt[:40], 'g': g, 'inr': price,
                                 'per100': round(price / g * 100), 'mrp': cap if cap and cap > price else None,
                                 'avail': bool(v.get('available', True)), 'k': kind(p['title'])})
            page += 1; time.sleep(1)
    except Exception as e:
        out['brands'][key] = {'name': name, 'url': base, 'error': str(e)[:120]}; continue
    pass
    def stat(rs):
        xs = sorted(r['per100'] for r in rs)
        return {'n': len(xs), 'min': xs[0], 'median': round(statistics.median(xs)), 'max': xs[-1]} if xs else None
    by = {k: stat([r for r in rows if r['k'] == k]) for k in ['First Flush', 'Second Flush', 'Autumn Flush', 'Green', 'White', 'Oolong', 'Other Darjeeling']}
    packs = sorted({int(r['g']) for r in rows})
    disc = [r for r in rows if r['mrp']]
    bst = lambda bs: {'n': len(bs), 'min': min(b['per_bag'] for b in bs), 'median': round(statistics.median(b['per_bag'] for b in bs), 1), 'max': max(b['per_bag'] for b in bs)} if bs else None
    out['brands'][key] = {'name': name, 'url': base, 'bags': bst(bags), 'bags_herbal': bst([b for b in bags if b['herbal']]), 'bags_pyramid_n': sum(b['pyramid'] for b in bags),
        'bag_eg': sorted(bags, key=lambda b: b['per_bag'])[len(bags)//2] if bags else None, 'herbal_loose': stat(herbs),
        'variants': len(rows), 'products': len({r['h'] for r in rows}),
        'oos_share': round(100 * sum(not r['avail'] for r in rows) / len(rows)) if rows else None,
        'on_sale_share': round(100 * len(disc) / len(rows)) if rows else None,
        'avg_off_pct': round(statistics.mean(100 * (1 - r['inr'] / r['mrp']) for r in disc)) if disc else None,
        'packs_g': packs[:12], 'gift_n': len(gifts), 'gift_min': min((g['inr'] for g in gifts), default=None), 'by_kind': {k: v for k, v in by.items() if v}, 'all': stat(rows),
        'cheapest': {k: min((r for r in rows if r['k'] == k), key=lambda r: r['per100'], default=None) for k in ('First Flush', 'Second Flush')}}
json.dump(out, open(os.path.join(H, 'competitors', 'prices.json'), 'w'), separators=(',', ':'))
for k, b in out['brands'].items():
    print(k, b.get('error') or (b['variants'], b['by_kind'].get('First Flush'), b['by_kind'].get('Second Flush'), b['oos_share'], b['on_sale_share'], b['packs_g']))
