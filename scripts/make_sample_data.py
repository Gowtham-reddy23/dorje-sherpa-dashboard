#!/usr/bin/env python3
"""Makes sample-data/dashboard.sample.json: a FABRICATED copy of the dashboard dataset with the same shape as the real one.
Every number is randomly scaled, order-level rows are re-sampled and shuffled, discount-code names are replaced, and the
'updated' label says SAMPLE DATA. Use it to regenerate the demo after the data model changes:
    python3 scripts/make_sample_data.py data/dashboard.json
Never commit data/dashboard.json itself (it is git-ignored)."""
import json, random, re, sys, os
random.seed(2611)
SRC = sys.argv[1] if len(sys.argv) > 1 else 'data/dashboard.json'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sample-data', 'dashboard.sample.json')
d = json.load(open(SRC))
SKIP_KEYS = {'src', 'url', 'link', 'img', 'thumb', 'href', 'id', 'pageId', 'page', 'date', 'w', 'since', 'until', 'endDate', 'd', 'k', 'n', 'keys', 'note'}
def fnum(x, lo=0.6, hi=1.3):
    if isinstance(x, bool) or x == 0: return x
    if isinstance(x, int):
        if abs(x) <= 5: return x                      # flags, small indices, ranks
        y = int(round(x * random.uniform(lo, hi)))
        return min(y, 100) if 0 < x <= 100 else y
    y = x * random.uniform(lo, hi)
    if 0 < x <= 100: y = min(y, 100.0)
    return round(y, 2)
NUM = re.compile(r'(?<![\w/.-])(\d{1,3}(?:,\d{2,3})+|\d{2,})(?:\.\d+)?(?![\w/-])')
def fstr(s):
    if 'http' in s or len(s) < 30: return s
    def r(m):
        t = m.group(0); v = float(t.replace(',', ''))
        if 1990 <= v <= 2100: return t                # keep years
        if re.match(r'\s?(days?|d\b|h\b|hours?|g\b|gm|GM|cups|bags)', m.string[m.end():m.end()+6]): return t   # keep windows, pack sizes
        nv = int(round(v * random.uniform(0.6, 1.3)))
        return f'{nv:,}' if ',' in t else str(nv)
    s = re.sub(r'(\d+\.\d+)(L|Cr|K)\b', lambda m: f"{float(m.group(1)) * random.uniform(0.6, 1.3):.2f}{m.group(2)}", s)
    return NUM.sub(r, s)
def walk(x, key=None):
    if isinstance(x, dict): return {k: (v if k in SKIP_KEYS and not isinstance(v, (dict, list)) else walk(v, k)) for k, v in x.items()}
    if isinstance(x, list):
        if x and isinstance(x[0], str) and re.match(r'^\d{4}-\d{2}', x[0]): return [x[0]] + [walk(v) for v in x[1:]]   # dated rows
        return [walk(v, key) for v in x]
    if isinstance(x, (int, float)): return fnum(x)
    if isinstance(x, str): return fstr(x)
    return x
attr = d.pop('attr', None)
s = walk(d)
s['updated'] = 'SAMPLE DATA (fabricated demo, not real numbers)'
s['sample'] = True
if attr:
    keys = attr['keys']; ri = keys.index('rev')
    rows = random.sample(attr['rows'], min(1800, len(attr['rows'])))
    for r in rows: r[ri] = int(round(r[ri] * random.uniform(0.6, 1.3)))
    rows.sort(key=lambda r: r[0])
    codes = [[f'SAMPLECODE{i+1}', c[1]] for i, c in enumerate(attr.get('codes', []))]
    s['attr'] = {**attr, 'rows': rows, 'codes': codes, 'metaMonthly': walk(attr.get('metaMonthly', [])), 'cancelled': random.randint(5, 20), 'total': len(rows)}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(s, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
