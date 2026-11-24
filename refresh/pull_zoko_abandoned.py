#!/usr/bin/env python3
"""Read-only (GET only) check of whether Zoko's WhatsApp abandoned-checkout flow fires.
For recent Shopify abandoned checkouts (shopify/abandoned/*.json) whose phone matches a Zoko contact
(zoko/customers.json, last 10 digits), fetch that contact's messages and the delivery status of store messages
sent within 72 h after the checkout. Saves only non-personal fields to zoko/abandoned_msgs.json.
Usage: pull_zoko_abandoned.py [--days 45] [--max 40]"""
import json, glob, os, re, time, argparse, datetime as dt
from zoko_api import get
H=os.path.dirname(os.path.abspath(__file__)); Z=os.path.join(H,'zoko')
IST=dt.timezone(dt.timedelta(hours=5,minutes=30)); now=dt.datetime.now(IST)
ap=argparse.ArgumentParser(); ap.add_argument('--days',type=int,default=45); ap.add_argument('--max',type=int,default=40); a=ap.parse_args()
P=lambda s: dt.datetime.fromisoformat(str(s).replace('Z','+00:00').replace('+0000','+00:00')).astimezone(IST)
def norm(x):
    d=re.sub(r'\D','',x or ''); return d[-10:] if len(d)>=10 and d[-10] in '6789' else None
def phone(n):
    c=n.get('customer') or {}
    return norm((c.get('defaultPhoneNumber') or {}).get('phoneNumber') or (n.get('shippingAddress') or {}).get('phone') or (n.get('billingAddress') or {}).get('phone'))
N={}
for f in sorted(glob.glob(os.path.join(H,'shopify','abandoned','*.json')),key=os.path.getmtime):
    for n in json.load(open(f))['data']['abandonedCheckouts']['nodes']: N[n['id']]=n
CU=json.load(open(os.path.join(Z,'customers.json')))
zmap={}
for c in CU:
    k=norm(c.get('channelId'))
    if k: zmap.setdefault(k,c['id'])
rec=sorted([n for n in N.values() if P(n['createdAt'])>now-dt.timedelta(days=a.days) and P(n['createdAt'])<now-dt.timedelta(hours=72)],key=lambda n:n['createdAt'],reverse=True)
pick=[]; seen=set()
for n in rec:
    p=phone(n)
    if p and p in zmap and p not in seen: seen.add(p); pick.append((n,zmap[p]))
    if len(pick)>=a.max: break
out=[]
for n,zid in pick:
    t0=P(n['createdAt']); s,b=get(f"/customer/{zid}/messages",retries=2)
    if s!=200 or not isinstance(b,list): out.append({'at':str(t0),'err':s}); continue
    win=[]
    for m in b:
        at=m.get('platformTimestamp') or m.get('createdAt')
        try: tm=P(at)
        except Exception: continue
        if m.get('direction')=='FROM_STORE' and t0-dt.timedelta(minutes=5)<=tm<=t0+dt.timedelta(hours=72):
            win.append({'tpl':m.get('templateId') or '','src':m.get('zokoSource') or '','h':round((tm-t0).total_seconds()/3600,1),'mid':(m.get('key') or {}).get('msgId')})
    for w in win:
        if w['mid'] and re.search(r'checkout|abandon|payment_reminder|cart',w['tpl'],re.I):
            s2,h=get(f"/message/{w['mid']}",retries=2)
            if s2==200 and isinstance(h,dict): w['status']=h.get('deliveryStatus'); w['fail']=(h.get('failureReason') or '')[:80]
            time.sleep(0.5)
        w.pop('mid',None)
    last=max((P(m.get('platformTimestamp') or m.get('createdAt')) for m in b if m.get('direction')=='FROM_STORE' and re.search(r'checkout|abandon|payment_reminder',m.get('templateId') or '',re.I)),default=None)
    out.append({'at':str(t0),'recovered':bool(n['completedAt']),'value':float(n['totalPriceSet']['shopMoney']['amount']),'msgs72h':win,'lastCartTplEver':str(last) if last else None,'nMsgs':len(b)})
    time.sleep(0.5)
json.dump({'at':str(now),'checked':len(out),'candidates':len(rec),'out':out},open(os.path.join(Z,'abandoned_msgs.json'),'w'))
print('checked',len(out),'of',len(rec),'abandoned in window; with cart reminder within 72h:',sum(1 for o in out if any(re.search(r'checkout|abandon|payment_reminder|cart',w['tpl'],re.I) for w in o.get('msgs72h',[]))))
