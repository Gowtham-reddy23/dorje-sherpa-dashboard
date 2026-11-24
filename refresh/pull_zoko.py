#!/usr/bin/env python3
"""Zoko (WhatsApp) pull for the dashboards. STRICTLY READ-ONLY: GET requests only (see zoko_api.py).
Never sends messages, never creates webhooks, never edits tags/properties, never deletes.
Rate limit seen on /customer: 1 request per 300 seconds, so the customer list is pulled with one large page
and resumable state in zoko/customers_state.json. Templates via /account/templates.
Usage: python3 pull_zoko.py [--customers] [--max-pages N] [--page-size N]
Writes zoko/templates.json, zoko/customers.json (merged by id)."""
import json, os, sys, time, argparse, datetime as dt
IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
nowist=lambda: dt.datetime.now(IST).strftime('%Y-%m-%d %H:%M')
from zoko_api import get
H=os.path.dirname(os.path.abspath(__file__)); Z=os.path.join(H,'zoko'); os.makedirs(Z,exist_ok=True)
ap=argparse.ArgumentParser(); ap.add_argument('--customers',action='store_true'); ap.add_argument('--max-pages',type=int,default=1); ap.add_argument('--page-size',type=int,default=2000); ap.add_argument('--sample',type=int,default=0); ap.add_argument('--skip-templates',action='store_true')
a=ap.parse_args()
SORTS=[('contactable','desc',1),('lastIncomingMessageAt','desc',5),('lastIncomingMessageAt','asc',5),('name','asc',5),('name','desc',5)]  # (sort, order, max pages)
s,b=(0,'skipped') if a.skip_templates else get('/account/templates')
if s==200: json.dump(b,open(os.path.join(Z,'templates.json'),'w')); print('templates',len(b))
elif not a.skip_templates: print('templates error',s,str(b)[:200])
if a.customers:
    # Zoko caps page*pageSize at 10,000 per sort order, so the list is pulled in up to 10,000-contact slices from
    # several sort orders and merged by contact id. 1 call per 305 s (Zoko limit: 1 per 300 s).
    SP=os.path.join(Z,'customers_state.json'); CP=os.path.join(Z,'customers.json')
    st=json.load(open(SP)) if os.path.exists(SP) else {}
    st.setdefault('last',0); st.setdefault('done',[])
    if st.get('cycle')!=time.strftime('%Y%m%d') and len(st['done'])>=len(SORTS): st['done']=[]
    st['cycle']=time.strftime('%Y%m%d')
    cust={c['id']:c for c in (json.load(open(CP)) if os.path.exists(CP) else [])}
    calls=0; fails=0
    for srt,od,mp in SORTS:
        tag=srt+':'+od
        if tag in st['done']: continue
        page=st.get('page',{}).get(tag,1)
        while page*a.page_size<=10000 and page<=mp and calls<a.max_pages:
            wait=st['last']+305-time.time()
            if wait>0: print(f'waiting {int(wait)}s for Zoko rate limit',flush=True)
            # Sleep in short chunks: a single long time.sleep can hang on this box.
            while True:
                wait=st['last']+305-time.time()
                if wait<=0: break
                time.sleep(min(wait, 5.0))
            s,b=get('/customer',{'channel':'whatsapp','page':page,'pageSize':a.page_size,'sortBy':srt,'orderBy':od},retries=1)
            st['last']=time.time(); calls+=1
            if s!=200:
                print('customer error',tag,page,s,str(b)[:160],flush=True); fails+=1; json.dump(st,open(SP,'w'))
                if fails<=3 and s in (429,0,500,502,503,504): continue
                break
            got=b.get('customers',[]); new_=sum(1 for c in got if c['id'] not in cust)
            for c in got: cust[c['id']]=c
            st.update(totalCustomers=b.get('totalCustomers'),fetchedAt=nowist())
            print('sort',tag,'page',page,'got',len(got),'new',new_,'have',len(cust),'of',b.get('totalCustomers'),flush=True)
            json.dump(list(cust.values()),open(CP,'w'))
            page+=1; st.setdefault('page',{})[tag]=page; json.dump(st,open(SP,'w'))
            if len(got)<a.page_size: break
        if page*a.page_size>10000 or page>mp or (st.get('page',{}).get(tag,1)>1 and calls<a.max_pages):
            st['done'].append(tag); st['page'].pop(tag,None); json.dump(st,open(SP,'w'))
        if calls>=a.max_pages: break
if a.sample:
    # Message sample (GET only): recent messages for a random, recency-stratified set of contacts, plus delivery
    # status for up to 3 recent outgoing messages each. Saves only non-personal fields to zoko/messages_sample.json.
    import random
    CU=json.load(open(os.path.join(Z,'customers.json'))); random.seed(7)
    eng=[c for c in CU if c.get('lastIncomingMessageAt')]; quiet=[c for c in CU if not c.get('lastIncomingMessageAt')]
    pick=random.sample(eng,min(len(eng),a.sample//2))+random.sample(quiet,min(len(quiet),a.sample-min(len(eng),a.sample//2)))
    out=[]
    for k,c in enumerate(pick):
        s,b=get(f"/customer/{c['id']}/messages",retries=2)
        if s!=200 or not isinstance(b,list): out.append({'id':c['id'],'err':s}); continue
        msgs=[{'dir':m.get('direction'),'type':m.get('type'),'tpl':m.get('templateId') or '','src':m.get('zokoSource') or '','bc':bool(m.get('broadcastName')),'at':m.get('platformTimestamp') or m.get('createdAt'),'mid':(m.get('key') or {}).get('msgId')} for m in b]
        n=0
        for m in sorted(msgs,key=lambda m:str(m['at']),reverse=True):
            if m['dir']=='FROM_STORE' and m['mid'] and n<3:
                s2,h=get(f"/message/{m['mid']}",retries=2); n+=1
                if s2==200 and isinstance(h,dict): m['status']=h.get('deliveryStatus'); m['fail']=(h.get('failureReason') or '')[:120]
        for m in msgs: m.pop('mid',None)
        s3,cd=get(f"/customer/{c['id']}",retries=2)
        tags=[(t.get('tag') if isinstance(t,dict) else t) for t in ((cd or {}).get('tags') or [])] if s3==200 and isinstance(cd,dict) else None
        out.append({'id':c['id'],'engaged':bool(c.get('lastIncomingMessageAt')),'msgs':msgs,'tags':tags})
        if k%25==0: print('sample',k,len(pick),flush=True)
    json.dump({'at':nowist(),'contacts':out},open(os.path.join(Z,'messages_sample.json'),'w'))
    print('sample saved',len(out))
