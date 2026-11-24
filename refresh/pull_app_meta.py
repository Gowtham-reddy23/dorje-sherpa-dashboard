#!/usr/bin/env python3
"""Meta Ads pull for the Founders app (read-only): daily account series (730d) + campaign tables for 7/30/90/365d.
Writes meta_app.json. Never prints the token."""
import json, os, datetime as dt
from pull_meta_seo import get, act, summ, ACT, today
H=os.path.dirname(os.path.abspath(__file__))
y=today-dt.timedelta(days=1); start=y-dt.timedelta(days=729)
F='spend,impressions,frequency,cpm,ctr,actions,action_values'
daily=[]
s=start
while s<=y:
    e=min(s+dt.timedelta(days=89),y)
    r=get(f'{ACT}/insights',{'fields':'spend,impressions,actions,action_values','time_range':json.dumps({'since':str(s),'until':str(e)}),'time_increment':1,'level':'account','limit':500})
    for x in r if isinstance(r,list) else []:
        daily.append({'d':x['date_start'],'spend':round(float(x['spend']),2),'purch':int(act(x.get('actions'))),'value':round(act(x.get('action_values')),2),'impr':int(x.get('impressions',0))})
    s=e+dt.timedelta(days=1)
adsets=get(f'{ACT}/adsets',{'fields':'id,campaign_id,effective_status,targeting{custom_audiences,excluded_custom_audiences}','limit':300,
    'filter':json.dumps([{'field':'adset.effective_status','operator':'IN','value':['ACTIVE']}])})
ex={}
for a in adsets if isinstance(adsets,list) else []:
    t=a.get('targeting',{}); e=ex.setdefault(a['campaign_id'],{'active':0,'excl':0,'warm':0}); e['active']+=1
    if t.get('excluded_custom_audiences'): e['excl']+=1
    if t.get('custom_audiences'): e['warm']+=1
st={c['id']:c.get('effective_status') for c in get(f'{ACT}/campaigns',{'fields':'id,effective_status','limit':300}) or []}
camps={}
for k in (7,30,90,365):
    r=get(f'{ACT}/insights',{'fields':'campaign_id,campaign_name,'+F,'time_range':json.dumps({'since':str(y-dt.timedelta(days=k-1)),'until':str(y)}),'level':'campaign','limit':300})
    rows=[]
    for m in r if isinstance(r,list) else []:
        z=summ(m); e=ex.get(m['campaign_id'],{'active':0,'excl':0,'warm':0}); n=m['campaign_name']; nl=n.lower()
        typ='Retargeting' if 'retarget' in nl else ('Awareness' if 'aware' in nl else ('Catalogue' if 'catalog' in nl else 'Prospecting'))
        flags=[]
        if z['spend']>=5000*k/30 and z['roas']<0.8: flags.append('Dead spend')
        if typ=='Prospecting' and st.get(m['campaign_id'])=='ACTIVE' and e['active'] and e['excl']==0: flags.append('No buyer exclusion')
        if z['freq']>=4: flags.append('High frequency')
        rows.append({'name':n,'type':typ,'status':(st.get(m['campaign_id']) or '').capitalize(),**z,'flags':flags})
    camps[str(k)]=sorted(rows,key=lambda r:-r['spend'])
json.dump({'daily':daily,'campaigns':camps},open(os.path.join(H,'meta_app.json'),'w'))
print('meta days',len(daily),'spend 365',round(sum(x['spend'] for x in daily[-365:])),{k:len(v) for k,v in camps.items()})
