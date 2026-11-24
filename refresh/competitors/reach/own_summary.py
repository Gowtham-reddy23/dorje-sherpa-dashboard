# Builds own_summary.json from own_total.json, own_placement.json, own_ads*.json, own_creatives.json (Dorje's own Meta account, read-only pulls)
import json,re,glob
from collections import defaultdict,Counter
tot=json.load(open('own_total.json'))[0]; pl=json.load(open('own_placement.json'))
ads=[x for f in sorted(glob.glob('own_ads*.json')) for x in json.load(open(f)) if x['amount_spent']]
cr=json.load(open('own_creatives.json'))
def fmt(n,c):
  n=n.lower()
  if re.search('reel|video',n) or (cr.get(c) or {}).get('object_type')=='VIDEO': return 'Video / Reel'
  if 'carousel' in n: return 'Carousel'
  if 'static' in n: return 'Single image'
  if 'flex' in n: return 'Flexible (mixed media)'
  return 'Unlabelled TOF concept'
def agg(rows,key):
  g=defaultdict(lambda: defaultdict(float)); n=Counter()
  for x in rows:
    k=key(x); n[k]+=1
    for m in('amount_spent','impressions','reach','link_click','omni_purchase'): g[k][m]+=x.get(m) or 0
    g[k]['value']+= (x.get('purchase_roas') or 0)*(x['amount_spent'] or 0)
  out=[]
  for k,v in g.items():
    s=v['amount_spent']; im=v['impressions']
    out.append({'k':k,'n':n[k],'spend':round(s),'impr':int(im),'reachSum':int(v['reach']),'cpm':round(s/im*1000) if im else None,
      'ctr':round(v['link_click']/im*100,2) if im else None,'purch':int(v['omni_purchase']),'roas':round(v['value']/s,2) if s else None,'share':round(s/tot['amount_spent']*100,1)})
  return sorted(out,key=lambda r:-r['spend'])
byfmt=agg(ads,lambda x:fmt(x['name'],x['creative_id']))
byplat=agg(pl,lambda x:x['publisher_platform'])
# platform reach can't be summed across positions; use account-level reach only
for r in byplat: r.pop('reachSum')
for r in byfmt: r.pop('reachSum')
pos=[{'k':f"{x['publisher_platform']} · {x['platform_position']}",'spend':round(x['amount_spent']),'impr':int(x['impressions']),'reach':int(x['reach']),
  'freq':round(x['frequency'] or 0,1),'cpm':round(x['cpm'] or 0),'ctr':x['ctr'],'purch':int(x['omni_purchase'] or 0),'roas':round(x['purchase_roas'],2) if x['purchase_roas'] else None} for x in sorted(pl,key=lambda x:-x['amount_spent']) if x['amount_spent']>=100]
cta=Counter((cr.get(x['creative_id']) or {}).get('call_to_action_type') or 'set per asset (flexible/dynamic)' for x in ads)
camp=agg(ads,lambda x:x['campaign_name'].split('|')[0].split('–')[0].split('(')[0].strip())
json.dump({'period':'last 30 days to 12 Nov 2026','total':{k:tot[k] for k in('amount_spent','impressions','reach','frequency','cpm','ctr','link_click','cost_per_link_click','purchase_roas','omni_purchase','omni_purchase_values','video_thruplay_watched_actions','3_second_video_plays')},
  'adsWithSpend':len(ads),'byFormat':byfmt,'byPlatform':byplat,'byPosition':pos,'cta':cta.most_common(),'byCampaign':camp},open('own_summary.json','w'),separators=(',',':'))
print(json.dumps(byfmt,indent=0)[:1500]);print(byplat);print(cta);print([ (c['k'],c['spend'],c['roas']) for c in camp])
