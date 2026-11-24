#!/usr/bin/env python3
"""Meta pull for the Attribution tab (read-only): id map (campaign/adset/ad -> campaign) and monthly
campaign spend/purchases/value for the last 13 months. Writes meta_attr.json. Never prints the token."""
import json, os, datetime as dt
from pull_meta_seo import get, act, ACT, today
H=os.path.dirname(os.path.abspath(__file__))
idmap={}
camps=get(f'{ACT}/campaigns',{'fields':'id,name','limit':500}) or []
names={c['id']:c['name'] for c in camps}
for c in camps: idmap[c['id']]=c['id']
for a in get(f'{ACT}/adsets',{'fields':'id,campaign_id','limit':500}) or []: idmap[a['id']]=a['campaign_id']
for a in get(f'{ACT}/ads',{'fields':'id,campaign_id','limit':500}) or []: idmap[a['id']]=a['campaign_id']
start=(today.replace(day=1)-dt.timedelta(days=370)).replace(day=1); y=today-dt.timedelta(days=1)
r=get(f'{ACT}/insights',{'fields':'campaign_id,campaign_name,spend,actions,action_values','level':'campaign','time_increment':'monthly',
     'time_range':json.dumps({'since':str(start),'until':str(y)}),'limit':500})
monthly=[]
for m in r if isinstance(r,list) else []:
    names.setdefault(m['campaign_id'],m['campaign_name'])
    monthly.append([m['date_start'][:7],m['campaign_id'],round(float(m.get('spend',0))),int(act(m.get('actions'))),round(act(m.get('action_values')))])
json.dump({'idmap':idmap,'names':names,'monthly':monthly},open(os.path.join(H,'meta_attr.json'),'w'))
print('ids',len(idmap),'campaigns',len(names),'monthly rows',len(monthly))
