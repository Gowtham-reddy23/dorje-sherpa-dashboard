#!/usr/bin/env python3
"""Zoko (WhatsApp) metrics for the Founders app + Growth Dashboard. Pure compute, no API calls.
Inputs: zoko/templates.json, zoko/customers.json (+customers_state.json) from pull_zoko.py,
        shopify/orders/*.json (12-month orders) and shopify/phones/*.json (order phone numbers, read-only pull).
Output: zoko.json with aggregates only (no names, no phone numbers)."""
import json, glob, os, re, uuid, time, datetime as dt, collections as C
H=os.path.dirname(os.path.abspath(__file__)); Z=os.path.join(H,'zoko')
IST=dt.timezone(dt.timedelta(hours=5,minutes=30)); now=dt.datetime.now(IST)
T=json.load(open(os.path.join(Z,'templates.json')))
def tcat(t):
    i=t['templateId'].lower(); d=(t.get('templateDesc') or '').lower()
    if 'abandon' in i or 'checkout_reminder' in i or re.search(r'items in your cart|left .{0,20}in your cart|payment for your order .{0,40}pending',d): return 'Abandoned cart / checkout'
    if re.search(r'cod|prepa',i) or 'confirm your cod' in d: return 'COD confirm / COD-to-prepaid'
    if 'feedback' in i or 'review' in i or re.search(r'consider giving us a review|rate your (order|experience)',d): return 'Feedback / review'
    if 'order_confirm' in i or re.search(r'your order \{\{\d\}\} is confirmed',d): return 'Order confirmation'
    if re.search(r'ship|deliver|refund|track',i) or re.search(r'has been shipped|has been delivered|out for delivery|refund (has been|is) (initiated|processed)',d): return 'Shipping / delivery / refund'
    if re.search(r'restock|wapsi|back_in_stock',i) or 'back in stock' in d: return 'Back-in-stock / sign-up alert'
    if 'reorder' in i or 'we were told that you ordered' in d: return 'Reorder reminder'
    if re.search(r'support|contact_info|request',i): return 'Support / service'
    if re.search(r'group|invite',i): return 'Community / group invite'
    return 'Broadcast / promo'
cats=C.Counter(tcat(t) for t in T); act=C.Counter(tcat(t) for t in T if t.get('active'))
key=lambda c:[{'id':t['templateId'],'active':bool(t.get('active')),'type':t.get('templateType')} for t in T if tcat(t)==c]
ab=key('Abandoned cart / checkout')
tmpl={'total':len(T),'active':sum(1 for t in T if t.get('active')),'types':C.Counter(t.get('templateType') for t in T).most_common(),
      'languages':C.Counter(t.get('templateLanguage') for t in T).most_common(5),
      'categories':[[c,n,act[c]] for c,n in cats.most_common()],
      'abandoned':ab,'abandonedExists':bool(ab),'abandonedActive':any(x['active'] for x in ab),
      'lifecycle':{c:[x['id'] for x in key(c)] for c in ['Order confirmation','Shipping / delivery / refund','COD confirm / COD-to-prepaid','Back-in-stock / sign-up alert','Reorder reminder','Feedback / review']}}
# ---- customers
CU=json.load(open(os.path.join(Z,'customers.json'))) if os.path.exists(os.path.join(Z,'customers.json')) else []
ST=json.load(open(os.path.join(Z,'customers_state.json'))) if os.path.exists(os.path.join(Z,'customers_state.json')) else {}
def norm(x):
    d=re.sub(r'\D','',x or '')
    return d[-10:] if len(d)>=10 and d[-10] in '6789' else None
def uts(i):
    try:
        u=uuid.UUID(i)
        if u.version==1: return dt.datetime.fromtimestamp((u.time-0x01b21dd213814000)/1e7,IST)
    except Exception: pass
def lim(c):
    v=c.get('lastIncomingMessageAt')
    if not v: return None
    if isinstance(v,(int,float)) or str(v).replace('.','').isdigit():
        v=float(v); v=v/1000 if v>1e11 else v
        return dt.datetime.fromtimestamp(v,IST)
    return dt.datetime.strptime(str(v)[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=dt.timezone.utc).astimezone(IST)
rec=C.Counter(); newm=C.Counter(); lastm=C.Counter(); zphone={}
for c in CU:
    l=lim(c)
    if l is None: rec['Never messaged in']+=1
    else:
        d=(now-l).days; lastm[l.strftime('%Y-%m')]+=1
        rec['≤7 days' if d<=7 else '8–30 days' if d<=30 else '31–90 days' if d<=90 else '91–365 days' if d<=365 else 'Over a year']+=1
    t=uts(c['id'])
    if t: newm[t.strftime('%Y-%m')]+=1
    n=norm(c.get('channelId'))
    if n: zphone[n]={'eng':l is not None,'d':(now-l).days if l else None}
order=['≤7 days','8–30 days','31–90 days','91–365 days','Over a year','Never messaged in']
cust={'total':ST.get('totalCustomers') or len(CU),'fetched':len(CU),'complete':len(CU)>=(ST.get('totalCustomers') or 0)*0.97,'coveragePct':round(100*len(CU)/max(1,ST.get('totalCustomers') or len(CU)),1),
      'contactableNow':sum(1 for c in CU if c.get('contactable')),'recency':[[k,rec[k]] for k in order],
      'newPerMonth':sorted(newm.items())[-13:],'newPerMonthNote':'When each contact was created in Zoko (read from the contact ID, which matches Zoko\'s created date).',
      'lastInboundMonth':sorted(lastm.items())[-13:],'withPhone':len(zphone)}
# ---- join with Shopify buyers (12 months, non-cancelled)
ph={}
for f in glob.glob(os.path.join(H,'shopify','phones','*.json')):
    for o in json.load(open(f)):
        cid=(o.get('customer') or {}).get('id')
        for v in (o.get('phone'),(o.get('shippingAddress') or {}).get('phone'),(o.get('billingAddress') or {}).get('phone')):
            n=norm(v)
            if cid and n: ph.setdefault(cid,set()).add(n)
B={}; _seen=set()  # dedupe orders by name (overlapping incremental pages)
for f in sorted(glob.glob(os.path.join(H,'shopify','orders','*.json')),key=os.path.getmtime,reverse=True):
    for o in json.load(open(f)):
        if o['name'] in _seen: continue
        _seen.add(o['name'])
        if o.get('cancelledAt') or not o.get('customer'): continue
        b=B.setdefault(o['customer']['id'],{'n':0,'rev':0.0,'first':o['createdAt']})
        b['n']+=1; b['rev']+=float(o['currentSubtotalPriceSet']['shopMoney']['amount']); b['first']=min(b['first'],o['createdAt'])
seg={'In Zoko, has messaged you':[], 'In Zoko, never messaged':[], 'Not in Zoko':[]}
for cid,b in B.items():
    z=[zphone[n] for n in ph.get(cid,()) if n in zphone]
    k='Not in Zoko' if not z else 'In Zoko, has messaged you' if any(x['eng'] for x in z) else 'In Zoko, never messaged'
    seg[k].append(b)
def s(L):
    n=len(L); r=sum(b['rev'] for b in L); rep=sum(1 for b in L if b['n']>=2)
    return {'buyers':n,'revenue':round(r),'orders':sum(b['n'] for b in L),'repeatRate':round(100*rep/n,1) if n else 0,'revPerBuyer':round(r/n) if n else 0}
segs={k:s(v) for k,v in seg.items()}
allb=s([b for v in seg.values() for b in v]); inz=s(seg['In Zoko, has messaged you']+seg['In Zoko, never messaged'])
join={'buyers':allb['buyers'],'buyersWithPhone':sum(1 for c in B if c in ph),'reachable':inz['buyers'],'reachablePct':round(100*inz['buyers']/max(1,allb['buyers']),1),
      'revenueReachable':inz['revenue'],'revenueReachablePct':round(100*inz['revenue']/max(1,allb['revenue']),1),'revenueAll':allb['revenue'],'segments':segs,
      'note':'Matched on the last 10 digits of the phone number (+91 removed). Zoko contacts not yet downloaded are counted as not in Zoko.' }
# ---- message sample (optional, from pull_zoko.py --sample)
SP=os.path.join(Z,'messages_sample.json'); sample=None
if os.path.exists(SP):
    MS=json.load(open(SP)); CT=[c for c in MS['contacts'] if 'msgs' in c]; M=[m for c in CT for m in c['msgs']]
    out_=[m for m in M if m['dir']=='FROM_STORE']; st=C.Counter(m['status'] for m in out_ if m.get('status'))
    ns=sum(st.values()) or 1
    tid={t['templateId']:tcat(t) for t in T}
    def p_(x,n): return round(100*x/max(1,n),1)
    seen=st.get('seen',0)+st.get('read',0); dl=seen+st.get('delivered',0); fl=st.get('failed',0)
    sent_cat=C.Counter(tid.get(m['tpl'],'Other / free text') for m in out_)
    srcs=C.Counter('Broadcast' if m['bc'] or 'broadcast' in m['src'] else 'Automation (flow)' if 'flow' in m['src'] else 'Agent / other' for m in out_)
    ab=[m for m in out_ if tid.get(m['tpl'])=='Abandoned cart / checkout']
    sample={'contacts':len(CT),'messages':len(M),'outgoing':len(out_),'checked':sum(st.values()),
            'delivered':p_(dl,ns),'read':p_(seen,ns),'failed':p_(fl,ns),'statuses':st.most_common(),
            'repliedPct':p_(sum(1 for c in CT if any(m['dir']=='FROM_CUSTOMER' for m in c['msgs'])),len(CT)),
            'tags':C.Counter(t for c in CT for t in (c.get('tags') or [])).most_common(10),'tagged':p_(sum(1 for c in CT if c.get('tags')),len(CT)),
            'failReasons':C.Counter(re.sub(r'^Code: (\d+) Error: ','\\1: ',m.get('fail',''))[:90] for m in out_ if m.get('status')=='failed').most_common(5),
            'statusByType':{k:dict(C.Counter(m['status'] for m in out_ if m.get('status') and ('Broadcast' if m['bc'] or 'broadcast' in m['src'] else 'Automation (flow)' if 'flow' in m['src'] else 'Agent / other')==k)) for k in ('Broadcast','Automation (flow)','Agent / other')},
            'sources':srcs.most_common(),'sentByType':sent_cat.most_common(),'abandonedSent':len(ab),
            'abandonedLast':max((str(m['at'])[:10] for m in ab),default=None),
            'note':f"Sample of {len(CT)} contacts (half who have messaged us, half who never did), their latest messages, and delivery status for the 3 most recent outgoing messages each, pulled {MS['at']} IST."}
out={'asOf':now.strftime('%d %b %Y, %H:%M IST'),'templates':tmpl,'customers':cust,'join':join,'messageSample':sample,
     'gaps':['Opt-in / consent status is not exposed by the Zoko API.',
             'Tags are only available one contact at a time (no bulk tag list), so tags are not broken down here.',
             'Delivered / read rates come from a sample: the API gives delivery status one message at a time, with no account-wide or broadcast report.',
             'Broadcast campaign results, costs and automation (flow) on/off status are not in the API.',
             'The contact list is limited to 1 request every 5 minutes, 2,000 contacts per request and 10,000 per sort order, so contacts are pulled in slices from several sort orders (about 2 hours) and a few may be missed.']}
json.dump(out,open(os.path.join(H,'zoko.json'),'w'),indent=1,default=list)
print(json.dumps({'tmpl':{k:tmpl[k] for k in ('total','active','categories','abandonedExists','abandonedActive')},'cust':{k:cust[k] for k in ('total','fetched','contactableNow','recency','withPhone')},'join':{k:join[k] for k in ('buyers','buyersWithPhone','reachable','reachablePct','revenueReachablePct')},'segs':segs},indent=0))
