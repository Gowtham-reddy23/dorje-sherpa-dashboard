"""Ingest read-only Shopify order phone pages (graphql_query write_to_file outputs) into shopify/phones/*.json.
Prints window-first-date, count, hasNext, endCursor per file."""
import json,sys,os,hashlib
H=os.path.dirname(os.path.abspath(__file__)); OD=os.path.join(H,'shopify','phones'); os.makedirs(OD,exist_ok=True)
for f in sys.argv[1:]:
    t=open(f).read(); i=t.find('{"data"')
    if i<0: print('ERR',f,t[:300]); continue
    d=json.loads(t[i:t.rfind('}')+1])['data']['orders']; n=d['nodes']
    key=hashlib.sha1((n[0]['id']+n[-1]['id']).encode()).hexdigest()[:10] if n else 'empty'
    json.dump(n,open(os.path.join(OD,key+'.json'),'w'))
    print(n[0]['createdAt'][:10] if n else '-', n[-1]['createdAt'][:10] if n else '-', len(n), d['pageInfo']['hasNextPage'], d['pageInfo']['endCursor'])
