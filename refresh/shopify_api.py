#!/usr/bin/env python3
"""OPTIONAL fallback for step 1 of the refresh: runs the same READ-ONLY Shopify reads as shopify_queries.py directly against
the Shopify Admin GraphQL API (no Claude connector needed), and writes the same files the ingest scripts write.
Needs SHOPIFY_STORE_DOMAIN + SHOPIFY_ADMIN_TOKEN (custom app with read_* scopes only) in .env.
Preferred route is the official Shopify connector in Claude (CLAUDE.md -> Refresh data). This script only sends queries, never mutations.

  python3 refresh/shopify_api.py                 # analytics + catalog + orders (12 months) + abandoned (90 days)
  python3 refresh/shopify_api.py --only analytics

VERIFY: ShopifyQL over the Admin API (`shopifyqlQuery`) needs a recent API version and the read_reports scope; if Shopify
changes the response shape, fix to_table() below."""
import contextlib, datetime as dt, io, json, os, subprocess, sys, time, urllib.request, urllib.error
from _env import need, env
H = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    import shopify_queries as SQ                 # reuses the exact query list (its printout is suppressed)
SHOP = need('SHOPIFY_STORE_DOMAIN'); TOKEN = need('SHOPIFY_ADMIN_TOKEN'); VER = env('SHOPIFY_API_VERSION', '2026-10')
URL = f'https://{SHOP}/admin/api/{VER}/graphql.json'
TMP = os.path.join(H, 'tmp_api'); os.makedirs(TMP, exist_ok=True); os.makedirs(os.path.join(H, 'shopify'), exist_ok=True)

def gql(query, variables=None):
    assert not query.lstrip().startswith('mutation'), 'read-only: mutations are not allowed'
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    for i in range(5):
        req = urllib.request.Request(URL, data=body, method='POST', headers={'Content-Type': 'application/json', 'X-Shopify-Access-Token': TOKEN})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: out = json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace').replace(TOKEN, '***')[:300]
            if e.code in (429, 502, 503): time.sleep(2 * (i + 1)); continue
            sys.exit(f'Shopify HTTP {e.code}: {msg}')
        if any('THROTTLED' in json.dumps(x) for x in out.get('errors', [])): time.sleep(2 * (i + 1)); continue
        if out.get('errors'): sys.exit('Shopify errors: ' + json.dumps(out['errors'])[:400])
        return out
    sys.exit('Shopify: too many retries')

SQL = 'query($q: String!) { shopifyqlQuery(query: $q) { tableData { columns { name dataType } rows } parseErrors } }'
def to_table(q, res):
    t = res['data']['shopifyqlQuery']
    if t.get('parseErrors'): sys.exit(f'ShopifyQL parse error: {t["parseErrors"]}\n{q}')
    cols = t['tableData']['columns']; names = [c['name'] for c in cols]
    rows = [[r.get(n) for n in names] if isinstance(r, dict) else r for r in t['tableData']['rows']]
    return {'query': q, 'columns': cols, 'rows': rows, 'rowCount': len(rows)}

def analytics():
    for name, tool, q in SQ.Q:
        if tool == 'run-analytics-query':
            json.dump(to_table(q, gql(SQL, {'q': q})), open(os.path.join(H, 'shopify', name + '.json'), 'w')); print('ok', name)
        else:
            json.dump(gql(q), open(os.path.join(H, 'shopify', name + '.json'), 'w')); print('ok', name)

def paged(query, ingest, tag):
    after, page = None, 0
    while True:
        res = gql(query, {'after': after} if after else {})
        p = os.path.join(TMP, f'{tag}_{page:03d}.json'); json.dump(res, open(p, 'w'))
        subprocess.run([sys.executable, os.path.join(H, ingest), p], check=True)
        root = next(iter(res['data'].values())); info = root['pageInfo']
        if not info['hasNextPage']: break
        after, page = info['endCursor'], page + 1

def orders():
    y = dt.datetime.now(SQ.IST).date() - dt.timedelta(days=1); m = y.replace(day=1)
    for k in range(13):
        start = m; nxt = (start + dt.timedelta(days=32)).replace(day=1)
        q = SQ.ORDERS_Q.replace('YYYY-MM-01', str(start)).replace('NEXT-MM-01', str(nxt))
        paged(q, 'ingest_orders.py', f'orders_{start:%Y%m}')
        m = (start - dt.timedelta(days=1)).replace(day=1)

def abandoned():
    d = os.path.join(H, 'shopify', 'abandoned'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    paged(SQ.ABANDONED_Q, 'ingest_abandoned.py', 'abandoned')

only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else 'all'
if only in ('all', 'analytics'): analytics()
if only in ('all', 'orders'): orders()
if only in ('all', 'abandoned'): abandoned()
print('Shopify pull done. Next: bash refresh/refresh.sh')
