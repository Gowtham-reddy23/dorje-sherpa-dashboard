"""Ingest Shopify order-page tool outputs (graphql_query, write_to_file) into shopify/orders/*.json.
Usage: python3 ingest_orders.py <file> [<file>...]  -> prints month, count, hasNext, endCursor per file."""
import json,sys,os,hashlib
H=os.path.dirname(os.path.abspath(__file__)); OD=os.path.join(H,'shopify','orders'); os.makedirs(OD,exist_ok=True)
for f in sys.argv[1:]:
    t=open(f).read(); i=t.find('{"data"')
    if i<0: print('ERR',f,t[:300]); continue
    d=json.loads(t[i:t.rfind('}')+1])['data']['orders']; n=d['nodes']
    key=hashlib.sha1((n[0]['name']+n[-1]['name']).encode()).hexdigest()[:10] if n else 'empty'
    json.dump(n,open(os.path.join(OD,key+'.json'),'w'))
    print(n[0]['createdAt'][:7] if n else '-', n[-1]['createdAt'][:10] if n else '-', len(n), d['pageInfo']['hasNextPage'], d['pageInfo']['endCursor'])
