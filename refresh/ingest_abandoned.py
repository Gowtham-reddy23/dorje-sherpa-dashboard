#!/usr/bin/env python3
"""Usage: ingest_abandoned.py <mcp_output_file>...  Saves rich abandoned-checkout pages (read-only Shopify graphql_query
output, see ABANDONED_Q in shopify_queries.py) to shopify/abandoned/<pageN>.json and prints hasNext/endCursor.
Files contain contact details (box only, never deployed)."""
import sys,json,os,hashlib
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'shopify','abandoned'); os.makedirs(D,exist_ok=True)
for f in sys.argv[1:]:
    t=open(f).read(); i=t.find('{"data"')
    d,_=json.JSONDecoder(strict=False).raw_decode(t[i:])
    ac=d['data']['abandonedCheckouts']; n=ac['nodes']
    key=hashlib.sha1((n[0]['id'] if n else f).encode()).hexdigest()[:10]
    json.dump(d,open(os.path.join(D,key+'.json'),'w'))
    print(key,len(n),n[0]['createdAt'] if n else '',n[-1]['createdAt'] if n else '',ac['pageInfo']['hasNextPage'],ac['pageInfo']['endCursor'])
