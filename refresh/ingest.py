#!/usr/bin/env python3
"""Usage: ingest.py <name> <mcp_output_file>  -> saves the JSON payload to shopify/<name>.json"""
import sys,json,re,os
name,f=sys.argv[1],sys.argv[2]; t=open(f).read()
i=t.find('{"query"') if '{"query"' in t else t.find('{"data"')
if i<0: i=t.find('{')
d,_=json.JSONDecoder().raw_decode(t[i:])
json.dump(d,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'shopify',name+'.json'),'w'))
print(name, len(d.get('rows',[])) if 'rows' in d else list(d)[:3])
