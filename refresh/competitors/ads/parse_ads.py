#!/usr/bin/env python3
"""Weekly: turn saved Meta Ad Library results (raw/<brand>.txt, one ads_library_search result per brand,
country IN, active only) + ad snapshot digest (snap_digest.json) + Google Ads Transparency log (google_atc.log)
into ads_meta.json. Angle tags are keyword matches on ad headlines/copy (labelled as such in the UI)."""
import json, os, re, sys, collections, datetime
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from parse_lib import parse
PAGE = {'goodricke': 'Goodricke tea', 'udyan': 'Udyan', 'organicindia': 'Organic India'}  # keyword searches: keep only the brand's own page
ANG = {'Health / wellness': r'joint|curcumin|immun|detox|stress|sleep|bedtime|calm|throat|skin|glow|hair|weight|metabol|gut|fiber|hormone|wellness|ayurved|caffeine.free|antioxid|relief|nutrition|vitality',
 'Price / discount': r'\d+\s?% ?off|₹ ?\d|rs\.? ?\d|sale|save|flat|deal|price|@ ?₹',
 'Free gift / sample': r'free (gift|mini|sample|playing|glass)|freebies|\+ free',
 'Scarcity / urgency': r'last \d+|only \d+|selling out|limited|while it lasts|act fast|hurry|once a year',
 'Festive / seasonal': r'diwali|festive|pujo|christmas|xmas|wedding|winter|celebrat',
 'Gifting': r'gift (set|box|pack|they|moments|hamper)|gifting|diwali gift|wedding|a gift',
 'Origin / estate': r'darjeeling|estate|garden|selim|makaibari|castleton|badamtam|harvest|flush|okayti|glenburn|since 18|\d,?\d{3} ?ft|himalaya',
 'Quality / craft': r'finest|rare|premium|refined|exquisite|least processed|hand.?pluck|whole.?leaf|real darjeeling|not a blend|authentic',
 'UGC / creator': r'weightlifter|creator|influencer| with vahdam|join \d|lovers|customers say|#ad\b',
 'Quick-commerce / retail': r'blinkit|zepto|instamart|amazon|delivered in|minutes|gofresh',
 'First-order / signup offer': r'first (order|time|purchase)|new here|welcome',
 'Plastic-free / sustainability': r'plastic|biodegrad|\beco[- ]',
 'B2B / bulk': r'business|bulk|b2b|distributor'}
ATC = {}
p = os.path.join(H, 'google_atc.log')
if os.path.exists(p):
    dom = {'dorjeteas.com': 'dorje', 'vahdam.in': 'vahdam', 'teabox.com': 'teabox', 'teacultureoftheworld.com': 'tcotw', 'sanchatea.com': 'sancha', 'goldentipstea.in': 'goldentips', 'goodricketea.in': 'goodricke', 'udyantea.com': 'udyan', 'makaibari.in': 'makaibari', 'organicindia.com': 'organicindia', 'kaahuteas.com': 'kaahu', 'mittalteas.com': 'mittal', 'happyvalleyorganictea.com': 'happyvalley', 'jayshreetea.com': 'jayshree'}
    for line in open(p):
        d, _, js = line.partition(' ')
        try: j = json.loads(js)
        except Exception: continue
        if d in dom: ATC[dom[d]] = {'domain': d, 'ads30d': j.get('n'), 'advertiser': (j.get('adv') or [''])[0].replace('videocam ', '') if j.get('n') not in ('0', None) else None}
snaps = {}
sp = os.path.join(H, 'snap_digest.json')
if os.path.exists(sp):
    for s in json.load(open(sp)): snaps[s['id']] = s
today = datetime.date.today()
out = {'checked': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%d %b %Y'), 'brands': {}}
for f in sorted(os.listdir(os.path.join(H, 'raw'))):
    k = f[:-4]; n, ads = parse(os.path.join(H, 'raw', f))
    if k in PAGE: ads = [a for a in ads if a['page'].startswith(PAGE[k])]; n = len(ads) if len(ads) < 25 else n
    texts = []; fm = collections.Counter(); samples = []
    for a in ads:
        s = snaps.get(a['id']); body = (s or {}).get('body', '')
        texts.append((a['title'] + ' ' + body).lower())
        if s:
            fm['Video' if s.get('vid') else ('Carousel/catalogue' if (s.get('imgs') or 0) > 2 else 'Static image')] += 1
            if s.get('multi'): fm['Multiple versions (dynamic creative)'] += 1
            land = s.get('link', '')
            samples.append({'id': a['id'], 'start': a['start'], 'title': a['title'][:120], 'land': re.sub(r'\?.*', '', land)[:110]})
        elif ' | ' in a['title'] and re.search(r'₹|\d+ ?g', a['title']): fm['Catalogue (product feed)'] += 1
    ang = collections.Counter()
    for t in texts:
        for name, rx in ANG.items():
            if re.search(rx, t): ang[name] += 1
    starts = sorted(a['start'] for a in ads)
    titles = collections.Counter(re.sub(r'\s*\|.*', '', a['title']).strip() for a in ads if a['title'].strip() and not a['title'].startswith('{{'))
    oldest = starts[0] if starts else None
    out['brands'][k] = {'active': 0 if (k == 'udyan' and not ads) else n, 'sampled': len(ads), 'newest': starts[-1] if starts else None, 'oldest': oldest if len(ads) >= (n or 0) else None,
        'oldestDays': (today - datetime.date.fromisoformat(oldest)).days if oldest and len(ads) >= (n or 0) else None,
        'last7': sum(1 for s in starts if (today - datetime.date.fromisoformat(s)).days <= 7),
        'angles': dict(ang.most_common()), 'formats': dict(fm), 'topTitles': titles.most_common(4), 'samples': samples[:4],
        'src': 'https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id=', 'google': ATC.get(k)}
json.dump(out, open(os.path.join(H, '..', 'ads_meta.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
for k, v in out['brands'].items(): print(k, v['active'], v['oldest'], v['oldestDays'], v['last7'], list(v['angles'].items())[:5], v['formats'], v['google'])
