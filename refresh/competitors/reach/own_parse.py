import json,sys
# usage: own_parse.py <full tool result text> <out.json>  -> rows from "ad_entities"
t=open(sys.argv[1]).read()
i=t.find('{"'); d=json.JSONDecoder(strict=False).raw_decode(t[i:])[0]
if 'text' in d and 'ad_entities' not in d: d=json.loads(d['text'],strict=False)
rows=d['ad_entities']; rows=json.loads(rows) if isinstance(rows,str) else rows
def v(x):
  if isinstance(x,dict): x=x.get('value')
  if x is None: return None
  try: return float(str(x).replace('%',''))
  except: return x
keep=('name','id','publisher_platform','platform_position','effective_status','campaign_name','adset_name','creative_id')
out=[{k:(r[k] if k in keep else v(r[k])) for k in r} for r in rows]
json.dump(out,open(sys.argv[2],'w'),separators=(',',':'))
print(len(out),'rows; pagination',d.get('pagination'))
