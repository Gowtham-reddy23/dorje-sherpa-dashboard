#!/usr/bin/env python3
"""Weekly, optional: parse $SHOT_DIR/serp_*.log (default /tmp/dorje-shot; from a headless-Chrome SERP script, headless Chrome, google.com gl=in) into competitors/google.json.
Google blocks after ~2-4 rapid queries; run one query per launch with ~40 s gaps. Missing/blocked queries keep last week's result."""
import json, glob, os, re
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, 'google.json')
g = json.load(open(P)) if os.path.exists(P) else json.load(open(os.path.join(H, 'google_first2.json')))
for f in glob.glob(os.path.join(os.environ.get('SHOT_DIR','/tmp/dorje-shot'),'serp_*.log')):
    for l in open(f):
        if l.startswith('{'):
            d = json.loads(l)
            if not d['blocked'] and d['res']: g[d['q']] = {k: d.get(k) for k in ('res', 'ai', 'shop', 'blocked')}
json.dump(g, open(P, 'w'), ensure_ascii=False, separators=(',', ':')); print(len(g), 'queries in google.json')
