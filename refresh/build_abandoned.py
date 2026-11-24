#!/usr/bin/env python3
"""Abandoned-checkout deep-dive -> abandoned.json (aggregates only, no names/emails/phones). Pure compute, no API calls.
Inputs: shopify/abandoned/*.json (rich read-only pages, ABANDONED_Q in shopify_queries.py, ingest_abandoned.py),
        shopify/daily_sessions_400.json, shopify/catalog.json, zoko/customers.json (phone join),
        zoko/abandoned_msgs.json (pull_zoko_abandoned.py, GET only).
Windows: last 30 and 90 complete IST days (ending yesterday)."""
import json, glob, os, re, datetime as dt, collections as C, statistics as ST
H=os.path.dirname(os.path.abspath(__file__)); IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
today=dt.datetime.now(IST).date(); y=today-dt.timedelta(days=1)
P=lambda s: dt.datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(IST)
N={}
for f in sorted(glob.glob(os.path.join(H,'shopify','abandoned','*.json')),key=os.path.getmtime):   # newest page wins
    for n in json.load(open(f))['data']['abandonedCheckouts']['nodes']: N[n['id']]=n
N=sorted(N.values(),key=lambda n:n['createdAt'])
def norm(x):
    d=re.sub(r'\D','',x or ''); return d[-10:] if len(d)>=10 and d[-10] in '6789' else None
CU=json.load(open(os.path.join(H,'zoko','customers.json'))) if os.path.exists(os.path.join(H,'zoko','customers.json')) else []
ZP={norm(c.get('channelId')) for c in CU}-{None}
amt=lambda n:float(n['totalPriceSet']['shopMoney']['amount'])
sub=lambda n:float(n['subtotalPriceSet']['shopMoney']['amount'])
lip=lambda n:float(n['totalLineItemsPriceSet']['shopMoney']['amount'])
def f(n):
    c=n.get('customer') or {}; t=P(n['createdAt'])
    em=(c.get('defaultEmailAddress') or {}); ph=norm((c.get('defaultPhoneNumber') or {}).get('phoneNumber') or (n.get('shippingAddress') or {}).get('phone') or (n.get('billingAddress') or {}).get('phone'))
    orders=int(c.get('numberOfOrders') or 0)-(1 if n['completedAt'] else 0)   # orders before this checkout (approx: count is as of today)
    lines=[l for l in n['lineItems']['nodes']]
    upd=(P(n['updatedAt'])-t).total_seconds()/60
    ship=round(amt(n)-sub(n),2)
    return {'t':t,'d':t.date(),'v':amt(n),'sub':sub(n),'lip':lip(n),'ship':ship,'rec':bool(n['completedAt']),
      'lag':(P(n['completedAt'])-t).total_seconds()/3600 if n['completedAt'] else None,
      'email':bool(em.get('emailAddress')),'emState':em.get('marketingState') or 'NO_EMAIL','phone':bool(ph),'zoko':bool(ph and ph in ZP),
      'ret':orders>0,'cust':(c.get('id') or n['id']),'rzp':any(a['key']=='__rzp_data' for a in n['customAttributes']),
      'cod':any(a['key']=='__rzp_data' and '"cod":1' in a['value'] for a in n['customAttributes']),
      'disc':n['discountCodes'],'state':(n.get('shippingAddress') or {}).get('provinceCode') or '—',
      'mail10h':570<=upd<=630,
      'lines':[{'p':re.sub(r'\s*\(\d{4}\)','',l['title'] or ''),'v':l['variantTitle'] or '','q':l['quantity'],
               'oos':bool(l.get('variant')) and not l['variant']['availableForSale'],'gone':not l.get('variant'),
               'sub':bool(re.search(r'Subscription|Deliveries|EVERY',l['variantTitle'] or '',re.I)),
               'size':(re.search(r'(\d+)\s*G',(l['variantTitle'] or '').upper()) or [None,None])[1]} for l in lines]}
R0=[f(n) for n in N]
# Junk: checkouts with only free (₹0) items, e.g. 97 'Seasonal Postcard' checkouts to Washington DC with ₹4,700 shipping, Aug-Sep 2026.
JUNK=lambda r: r['lip']<=0
R=[r for r in R0 if not JUNK(r)]
def win(days): return [r for r in R if y-dt.timedelta(days=days-1)<=r['d']<=y]
def inr(x):
    x=int(round(x)); s=str(abs(x)); h,t=s[:-3],s[-3:]
    h=re.sub(r'(\d)(?=(\d\d)+$)',r'\1,',h) if h else ''
    return ('-' if x<0 else '')+'₹'+(h+','+t if h else t)
pct=lambda a,b: round(100*a/b,1) if b else 0.0
def band(v):
    for lo,hi,l in [(0,399,'Under ₹399'),(399,499,'₹399–498'),(499,1000,'₹499–999'),(1000,2000,'₹1,000–1,999'),(2000,4000,'₹2,000–3,999'),(4000,1e9,'₹4,000+')]:
        if lo<=v<hi: return l
BANDS=['Under ₹399','₹399–498','₹499–999','₹1,000–1,999','₹2,000–3,999','₹4,000+']
def grp(S,key,order=None,top=None):
    g=C.defaultdict(list)
    for r in S: g[key(r)].append(r)
    ks=order or sorted(g,key=lambda k:-len(g[k]))
    rows=[{'k':k,'n':len(g[k]),'value':round(sum(r['v'] for r in g[k])),'rec':sum(r['rec'] for r in g[k]),'recPct':pct(sum(r['rec'] for r in g[k]),len(g[k]))} for k in ks if g.get(k)]
    return rows[:top] if top else rows
def summary(S,days):
    rec=[r for r in S if r['rec']]; un=[r for r in S if not r['rec']]
    prod=C.defaultdict(lambda:{'n':0,'value':0.0,'rec':0,'oos':0,'sub':0})
    for r in S:
        for p in {l['p'] for l in r['lines']}:
            x=prod[p]; x['n']+=1; x['value']+=r['v']; x['rec']+=r['rec']
        for l in r['lines']:
            if l['oos'] or l['gone']: prod[l['p']]['oos']+=1
            if l['sub']: prod[l['p']]['sub']+=1
    var=C.Counter((l['p'],l['v']) for r in S for l in r['lines'])
    oosc=sum(1 for r in S if any(l['oos'] or l['gone'] for l in r['lines']))
    subc=sum(1 for r in S if any(l['sub'] for l in r['lines']))
    shipc=[r for r in S if r['ship']>0]
    near=[r for r in S if 299<=r['lip']<499]
    lagb=C.Counter('Under 2 h' if r['lag']<2 else '2–12 h' if r['lag']<12 else '12–36 h' if r['lag']<36 else '36 h–7 days' if r['lag']<168 else 'Over 7 days' for r in rec)
    em=[r for r in S if r['email']]
    dow=grp(S,lambda r:r['t'].strftime('%a'),order=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    hr=grp(S,lambda r:('12–6 am' if r['t'].hour<6 else '6 am–12 pm' if r['t'].hour<12 else '12–6 pm' if r['t'].hour<18 else '6 pm–12 am'),order=['12–6 am','6 am–12 pm','12–6 pm','6 pm–12 am'])
    u399=[r for r in S if r['lip']<399]; o399=[r for r in S if r['lip']>=399]
    return {'days':days,'junk':sum(1 for r in R0 if JUNK(r) and y-dt.timedelta(days=days-1)<=r['d']<=y),
      'under399':len(u399),'under399Pct':pct(len(u399),len(S)),'under399FeePct':pct(sum(1 for r in u399 if r['ship']>0),len(u399)),'under399RecPct':pct(sum(r['rec'] for r in u399),len(u399)),
      'over399FeePct':pct(sum(1 for r in o399 if r['ship']>0),len(o399)),'over399RecPct':pct(sum(r['rec'] for r in o399),len(o399)),
'since':str(y-dt.timedelta(days=days-1)),'until':str(y),'n':len(S),'people':len({r['cust'] for r in S}),
      'value':round(sum(r['v'] for r in S)),'avg':round(ST.mean([r['v'] for r in S])) if S else 0,'median':round(ST.median([r['v'] for r in S])) if S else 0,
      'rec':len(rec),'recPct':pct(len(rec),len(S)),'recValue':round(sum(r['v'] for r in rec)),'lost':round(sum(r['v'] for r in un)),
      'perMonthN':round(len(S)*30/days),'perMonthLost':round(sum(r['v'] for r in un)*30/days),
      'bands':grp(S,lambda r:band(r['lip']),order=BANDS),
      'products':sorted([{'k':k,**{a:(round(b) if a=='value' else b) for a,b in v.items()},'recPct':pct(v['rec'],v['n'])} for k,v in prod.items()],key=lambda x:-x['n'])[:10],
      'variants':[{'p':p,'v':v,'n':c} for (p,v),c in var.most_common(10)],
      'oosCheckouts':oosc,'oosPct':pct(oosc,len(S)),'subCheckouts':subc,'subPct':pct(subc,len(S)),'subRecPct':pct(sum(1 for r in S if r['rec'] and any(l['sub'] for l in r['lines'])),subc),
      'newRet':grp(S,lambda r:'Returning customer' if r['ret'] else 'New customer',order=['New customer','Returning customer']),
      'contact':grp(S,lambda r:'Email + phone' if r['email'] and r['phone'] else 'Phone only' if r['phone'] else 'Email only' if r['email'] else 'No contact',order=['Email + phone','Phone only','Email only','No contact']),
      'emailState':grp(S,lambda r:{'SUBSCRIBED':'Subscribed to email','NOT_SUBSCRIBED':'Email, not subscribed','UNSUBSCRIBED':'Unsubscribed','NO_EMAIL':'No email'}.get(r['emState'],r['emState'])),
      'zoko':sum(r['zoko'] for r in S),'zokoPct':pct(sum(r['zoko'] for r in S),len(S)),'phonePct':pct(sum(r['phone'] for r in S),len(S)),'emailPct':pct(len(em),len(S)),
      'mail10hPct':pct(sum(r['mail10h'] for r in em),len(em)),
      'shipCharged':len(shipc),'shipChargedPct':pct(len(shipc),len(S)),'shipRecPct':pct(sum(r['rec'] for r in shipc),len(shipc)),
      'shipFreeRecPct':pct(sum(r['rec'] for r in S if r['ship']<=0),sum(1 for r in S if r['ship']<=0)),
      'shipFees':C.Counter(round(r['ship']) for r in shipc).most_common(4),
      'near499':len(near),'near499Pct':pct(len(near),len(S)),
      'withDiscount':sum(1 for r in S if r['disc']),'discCodes':C.Counter(c for r in S for c in r['disc']).most_common(5),
      'rzpPct':pct(sum(r['rzp'] for r in S),len(S)),'codPct':pct(sum(r['cod'] for r in S),len(S)),
      'lag':[{'k':k,'n':lagb.get(k,0)} for k in ['Under 2 h','2–12 h','12–36 h','36 h–7 days','Over 7 days']],
      'dow':dow,'hour':hr,'states':grp(S,lambda r:r['state'],top=8)}
S30,S90=win(30),win(90)
A={'asOf':dt.datetime.now(IST).strftime('%Y-%m-%d %H:%M IST'),'w30':summary(S30,30),'w90':summary(S90,90)}
# weekly series (Mon-start) over the 90-day window + Shopify sessions checkout funnel
ses={}
try:
    for r in json.load(open(os.path.join(H,'shopify','daily_sessions_400.json')))['rows']: ses[r[0]]=[int(x) for x in r[1:]]
except Exception: pass
wk=C.OrderedDict()
for r in S90:
    w=r['d']-dt.timedelta(days=r['d'].weekday()); x=wk.setdefault(w,{'n':0,'rec':0,'value':0.0,'rzp':0}); x['n']+=1; x['rec']+=r['rec']; x['value']+=r['v']; x['rzp']+=r['rzp']
weeks=[]
for w,x in sorted(wk.items()):
    s=[sum(ses.get(str(w+dt.timedelta(days=i)),[0,0,0,0])[j] for i in range(7) if w+dt.timedelta(days=i)<=y) for j in range(4)]
    weeks.append({'w':str(w),'n':x['n'],'rec':x['rec'],'recPct':pct(x['rec'],x['n']),'value':round(x['value']),'rzpPct':pct(x['rzp'],x['n']),
                  'carts':s[1],'checkouts':s[2],'completed':s[3],'cartToOrder':pct(s[3],s[1]),'partial':w+dt.timedelta(days=6)>y})
A['weeks']=weeks
# before/after Razorpay Magic Checkout (first week where most abandoned checkouts carry Razorpay data)
sw=next((dt.date.fromisoformat(w['w']) for w in weeks if w['rzpPct']>=50),None)
if sw:
    pre=[r for r in S90 if r['d']<sw]; post=[r for r in S90 if r['d']>=sw]
    dd=lambda S:max(1,len({r['d'] for r in S})) if S else 1
    def cfun(a,b):
        s=[sum(ses.get(str(a+dt.timedelta(days=i)),[0,0,0,0])[j] for i in range((b-a).days+1)) for j in range(4)]; return s
    cp=cfun(dt.date.fromisoformat(A['w90']['since']),sw-dt.timedelta(days=1)); cq=cfun(sw,y)
    A['switch']={'date':str(sw),'pre':{'perWeek':round(len(pre)*7/dd(pre),1),'recPct':pct(sum(r['rec'] for r in pre),len(pre)),'avg':round(ST.mean([r['v'] for r in pre])) if pre else 0,
                 'cartToOrder':pct(cp[3],cp[1]),'checkoutToOrder':pct(cp[3],cp[2]),'phoneOnlyPct':pct(sum(1 for r in pre if r['phone'] and not r['email']),len(pre))},
                 'post':{'perWeek':round(len(post)*7/dd(post),1),'recPct':pct(sum(r['rec'] for r in post),len(post)),'avg':round(ST.mean([r['v'] for r in post])) if post else 0,
                 'cartToOrder':pct(cq[3],cq[1]),'checkoutToOrder':pct(cq[3],cq[2]),'phoneOnlyPct':pct(sum(1 for r in post if r['phone'] and not r['email']),len(post))}}
# 30-day site funnel (sessions)
f30=[sum(ses.get(str(y-dt.timedelta(days=i)),[0,0,0,0])[j] for i in range(30)) for j in range(4)]
A['funnel30']={'sessions':f30[0],'carts':f30[1],'checkouts':f30[2],'completed':f30[3],'cartNoOrder':f30[1]-f30[3]}
# Zoko WhatsApp reminder evidence (GET-only sample)
zp=os.path.join(H,'zoko','abandoned_msgs.json')
if os.path.exists(zp):
    z=json.load(open(zp)); o=[x for x in z['out'] if 'msgs72h' in x]
    cw=[w for x in o for w in x['msgs72h'] if re.search(r'checkout|abandon|payment_reminder|cart',w['tpl'],re.I)]
    stc=C.Counter(w.get('status') or 'unknown' for w in cw)
    A['zokoFlow']={'checkedAt':z['at'][:16],'checked':len(o),'gotReminder':sum(1 for x in o if any(w in cw for w in x['msgs72h'])),
       'templates':C.Counter(w['tpl'] for w in cw).most_common(3),'sends':len(cw),
       'timing':[[k,sum(1 for w in cw if lo<=w['h']<hi)] for k,lo,hi in [('Within 1 h',0,1),('1–20 h',1,20),('20–30 h',20,30),('After 30 h',30,1e9)]],
       'medianFirstH':ST.median([min(w['h'] for w in x['msgs72h'] if w in cw) for x in o if any(w in cw for w in x['msgs72h'])]) if cw else None,
       'stepsPer':C.Counter(sum(1 for w in x['msgs72h'] if w in cw) for x in o).most_common(),
       'status':stc.most_common(),'failedPct':pct(stc.get('failed',0),len(cw)),'seenPct':pct(stc.get('seen',0)+stc.get('read',0),len(cw)),
       'deliveredPct':pct(stc.get('delivered',0)+stc.get('seen',0)+stc.get('read',0),len(cw)),
       'fail131049':sum(1 for w in cw if (w.get('fail') or '').startswith('Code: 131049')),'recovered':sum(1 for x in o if x['recovered'])}
# Opportunity (ESTIMATES): lift recovery on the 30-day base
w=A['w30']; base=w['n']*30/w['days']; avg=w['value']/max(1,w['n'])
A['opp']={'baseN':round(base),'avg':round(avg),'cur':w['recPct'],
  'targets':[{'to':t,'extraOrders':round(base*(t-w['recPct'])/100,1),'extraRevenue':round(base*(t-w['recPct'])/100*avg,-2)} for t in (15,20,25)],
  'note':'Estimate: monthly abandoned checkouts × (target − current recovery rate) × average abandoned-checkout value (last 30 days). Not a forecast.'}
# ---- plain-English findings + action plan (numbers filled from the data above; ₹ impacts are ESTIMATES)
w,w9=A['w30'],A['w90']; Fz=A.get('zokoFlow'); sw=A.get('switch'); F=A['funnel30']
try: AOV=round(sum(float(r[2]) for r in json.load(open(os.path.join(H,'shopify','daily_sales_400.json')))['rows'][-30:])/max(1,sum(float(r[1]) for r in json.load(open(os.path.join(H,'shopify','daily_sales_400.json')))['rows'][-30:])))
except Exception: AOV=round(w['avg'])
A['aov30']=AOV
nr={r['k']:r for r in w['newRet']}; hr={r['k']:r for r in w['hour']}
base=w['n']*30/w['days']; avg=w['value']/max(1,w['n'])
lift=lambda pts: round(base*pts/100*avg,-2)
fx=[]
fx.append({'title':f"Only {w['recPct']:.1f}% of unfinished checkouts come back and pay",
  'detail':f"{w['n']} unfinished checkouts in the last 30 days worth {inr(w['value'])}; {w['rec']} recovered ({inr(w['recValue'])}). {inr(w['lost'])} was left unpaid. Over 90 days the rate was {w9['recPct']:.1f}% ({w9['junk']} junk ₹0 checkouts left out).",'tone':'danger'})
if Fz: fx.append({'title':f"WhatsApp reminders do fire, but {Fz['failedPct']:.0f}% of them fail",
  'detail':f"Checked {Fz['checked']} recent unfinished checkouts in Zoko: all {Fz['gotReminder']} got the same 'payment pending' template, at about 45 minutes and again at about 25 hours. Of {Fz['sends']} sends, {Fz['failedPct']:.0f}% failed ({Fz['fail131049']} with WhatsApp error 131049, Meta's limit on marketing messages per person) and {Fz['seenPct']:.0f}% were read.",'tone':'danger'})
fx.append({'title':f"Email reminders: one email, about 10 hours later (inferred)",
  'detail':f"{w['mail10hPct']:.0f}% of checkouts with an email were updated almost exactly 10 hours after they started, which matches Shopify's abandoned-checkout email timing. There is no sign of a second or third email. {100-w['emailPct']:.0f}% of abandoners gave only a phone number, so email can't reach them.",'tone':'warning'})
fx.append({'title':f"New customers recover at {nr.get('New customer',{}).get('recPct',0):.1f}%, returning at {nr.get('Returning customer',{}).get('recPct',0):.1f}%",
  'detail':f"{nr.get('New customer',{}).get('n',0)} of {w['n']} abandoners were first-time buyers. They need trust (reviews, delivery time, COD, freshness) more than a reminder.",'tone':'warning'})
fx.append({'title':f"Carts under ₹399 pay ₹50 shipping and almost never come back ({w['under399RecPct']:.0f}%)",
  'detail':f"{w['under399']} checkouts ({w['under399Pct']:.0f}%) were under ₹399; {w['under399FeePct']:.0f}% of them were charged ₹50 shipping. Carts of ₹399 and up recovered at {w['over399RecPct']:.1f}%. The checkout's free-shipping line is effectively ₹399, but the site also says ₹499 in places, and {w['over399FeePct']:.0f}% of carts of ₹399 and up still show a ₹50 charge (check whether that is a COD fee).",'tone':'warning'})
if sw: fx.append({'title':f"Since Razorpay Magic Checkout went live (week of {dt.date.fromisoformat(sw['date']).strftime('%-d %b')}), Shopify sees fewer abandoned checkouts",
  'detail':f"Before: {sw['pre']['perWeek']:.0f} a week at {sw['pre']['recPct']:.1f}% recovery. After: {sw['post']['perWeek']:.0f} a week at {sw['post']['recPct']:.1f}%. Checkout-to-order went from {sw['pre']['checkoutToOrder']:.0f}% to {sw['post']['checkoutToOrder']:.0f}%. Shoppers who leave the Razorpay pop-up before typing a phone number never reach Shopify, so the full drop-off is only visible in Razorpay's dashboard.",'tone':None})
fx.append({'title':f"Evening abandoners are the hardest to win back",
  'detail':f"{hr.get('6 pm–12 am',{}).get('n',0)} checkouts ({pct(hr.get('6 pm–12 am',{}).get('n',0),w['n']):.0f}%) were left between 6 pm and midnight and recovered at {hr.get('6 pm–12 am',{}).get('recPct',0):.1f}%, against {hr.get('6 am–12 pm',{}).get('recPct',0):.1f}% for the morning.",'tone':None})
fx.append({'title':f"Stock and price errors are not what's stopping checkouts now",
  'detail':f"Only {w['oosCheckouts']} of {w['n']} unfinished checkouts in the last 30 days held an item that is sold out today ({w9['oosPct']:.0f}% over 90 days). Sold-out 250g packs lose sales earlier, on the product page. No checkout carried a Shopify discount code (Razorpay coupons may not be passed back to Shopify).",'tone':None})
A['findings']=fx
cart_pt=round(F['carts']*0.01*AOV,-2)
A['actions']=[
 {'n':1,'who':'Growth (CRM) in Zoko','what':'Fix the WhatsApp reminder flow: 3 different messages instead of the same "payment pending" one twice, the 2nd one at 10 am next morning, and send fewer promo broadcasts (error 131049 is Meta capping marketing messages per person, and cart reminders count as marketing). Fall back to email or SMS when WhatsApp fails',
  'copy':'30 min: "Hi {name}, your {product} is still in your cart. Fresh from Darjeeling, cash on delivery available. Finish your order: {link}" · Next morning 10 am: "Still thinking? Read what 600+ reviewers say about it. Free shipping over ₹399. Questions? Just reply here." · 48 h: "Last call: your cart is saved until tonight. {link}"',
  'impact':f"{inr(lift(3))}–{inr(lift(5))}/month",'basis':f"Estimate: +3 to +5 points of recovery on {round(base)} checkouts/month at {inr(round(avg))}"},
 {'n':2,'who':'Growth (CRM) in Shopify Messaging','what':'Move the abandoned-checkout email from 10 hours to 1 hour, add a second email at 24 hours (reviews, harvest notes) and a third at 72 hours with a small code for carts over ₹700 only',
  'copy':'Email 1 (1 h): "Your First Flush is waiting" · Email 2 (24 h): tasting notes + reviews · Email 3 (72 h): 10% for 24 hours, carts over ₹700',
  'impact':f"{inr(lift(2))}–{inr(lift(3))}/month",'basis':f"Estimate: +2 to +3 points of recovery; reaches the {w['emailPct']:.0f}% who gave an email"},
 {'n':3,'who':'Founders decide, web developer ships','what':'Pick one free-shipping line (₹399 is what checkout already uses), say it the same way everywhere, and add a "₹X away from free shipping" bar in the cart',
  'copy':'Cart bar: "Add ₹{gap} more for free shipping"','impact':f"{inr(round(w['under399']*0.07*AOV,-2))}/month direct (small); the bigger win is order value",
  'basis':f"Estimate: {w['under399']} carts under ₹399/month brought up to the {w['over399RecPct']:.0f}% recovery of bigger carts"},
 {'n':4,'who':'Growth (ads) + developer','what':"Check the Meta pixel sees checkouts on Razorpay: the 14-day 'Initiated checkout' and 30-day 'Add to cart' audiences show Meta's minimum size although Shopify logged "+f"{F['checkouts']:,} checkout sessions in 30 days. Once fixed, run a 7-day cart and checkout retargeting ad set (purchasers excluded, frequency cap 2 a week)",
  'copy':'Ad: product photo + "Your Darjeeling tea is still in your cart. Cash on delivery available."','impact':'Not estimated (needs pixel data first)','basis':'Meta audiences: 14D IC and 30D ATC at minimum size (read-only check)'},
 {'n':5,'who':'Founders + Razorpay account owner','what':"Open Razorpay Magic Checkout's analytics to see where people leave the pop-up (phone, address, payment) and check whether Razorpay's own cart-recovery messages are on, so customers don't get both Razorpay and Zoko reminders",
  'copy':'','impact':f"Each 1 point more of carts turning into orders ≈ {inr(cart_pt)}/month",'basis':f"Estimate: {F['carts']:,} cart sessions/month × 1% × {inr(AOV)} average order"},
 {'n':6,'who':'Ops (catalogue)','what':'Restock or hide sold-out 250g First Flush and Second Flush packs','copy':'','impact':'Not in this number (loss happens before checkout)','basis':f"{w['oosCheckouts']} of {w['n']} recent unfinished checkouts involved sold-out items"},
]
A['totalEst']={'low':lift(5),'high':lift(8),'note':'Actions 1–2 together, estimate'}
json.dump(A,open(os.path.join(H,'abandoned.json'),'w'),ensure_ascii=False,default=str)
# Compact data for the two Pages (Growth + Founders): one line `const AB: any = {...};` (ab_line.txt), rendered by render.py
def L(x): return f"₹{x/1e5:.2f}L" if x>=1e5 else inr(x)
w=A['w30']; Fz=A.get('zokoFlow') or {}
tbl=lambda rows:[[r['k'],str(r['n']),inr(r['value']),f"{r['recPct']:.1f}%"] for r in rows]
C={'asOf':A['asOf'],'period':f"{dt.date.fromisoformat(w['since']).strftime('%-d %b')} – {dt.date.fromisoformat(w['until']).strftime('%-d %b %Y')}",
 'metrics':[{'value':str(w['n']),'label':'Unfinished checkouts, 30 days','detail':f"{w['people']} people · {L(w['value'])} in carts"},
   {'value':f"{w['recPct']:.1f}%",'label':'Came back and paid','detail':f"{w['rec']} checkouts · {inr(w['recValue'])} (90 days: {A['w90']['recPct']:.1f}%)",**({'tone':'danger'} if w['recPct']<10 else {})},
   {'value':L(w['lost']),'label':'Left unpaid','detail':f"Average cart {inr(w['avg'])}; not all of it is winnable"},
   {'value':f"{w['zokoPct']:.0f}%",'label':'Reachable on WhatsApp','detail':f"Phone captured {w['phonePct']:.0f}% · email {w['emailPct']:.0f}%"}],
 'findings':[{'title':f['title'],'detail':f['detail'],'status':({'label':'Fix now','tone':'danger'} if f['tone']=='danger' else {'label':'Fix soon','tone':'warning'} if f['tone']=='warning' else {'label':'Context'})} for f in A['findings']],
 'weeks':{'labels':[dt.date.fromisoformat(x['w']).strftime('%-d %b')+('*' if x['partial'] else '') for x in A['weeks']],'n':[x['n'] for x in A['weeks']],'rec':[x['rec'] for x in A['weeks']]},
 'reminders':[['Shopify email','About 10 h after checkout (inferred)','1 email, no follow-up',f"{w['mail10hPct']:.0f}% of checkouts with an email"],
   ['Zoko WhatsApp',f"About 45 min and 25 h ({Fz.get('checked',0)} checked)",'Same "payment pending" template twice',f"{Fz.get('failedPct',0):.0f}% failed, {Fz.get('seenPct',0):.0f}% read"],
   ['Razorpay Magic Checkout','Not visible','Unknown',f"{w['rzpPct']:.0f}% of checkouts use it; needs Razorpay dashboard"]],
 'bands':tbl(w['bands']),'products':[[p['k'],str(p['n']),inr(p['value']),f"{p['recPct']:.1f}%"] for p in w['products'][:6]],
 'segments':tbl(w['newRet']+w['contact']+w['hour']),
 'opp':[['Today',f"{A['opp']['cur']:.1f}% ({w['rec']} orders)",'—']]+[[f"{t['to']}%",f"{t['extraOrders']:.0f}",inr(t['extraRevenue'])] for t in A['opp']['targets']],
 'oppNote':A['opp']['note']+f" The bigger pool: {A['funnel30']['cartNoOrder']:,} cart sessions a month never order; each extra 1% of carts that turn into orders ≈ {inr(round(A['funnel30']['carts']*0.01*A['aov30'],-2))} a month (estimate).",
 'actions':[[str(a['n']),a['who'],a['what']+(f". Copy: {a['copy']}" if a['copy'] else ''),a['impact']+' ('+a['basis']+')'] for a in A['actions']],
 'total':f"Actions 1–2 together: about {inr(A['totalEst']['low'])}–{inr(A['totalEst']['high'])} a month (estimate). Nothing has been changed in the store, Zoko or ads.",
 'fActions':[[str(a['n']),a['who'],a['what'].split(':')[0].split(' (')[0],a['impact']] for a in A['actions']]}
open(os.path.join(H,'ab_line.txt'),'w').write('const AB: any = '+json.dumps(C,ensure_ascii=False,default=str,separators=(',',':'))+';')
if __name__=='__main__':
    import sys
    if '-v' in sys.argv: print(json.dumps(A,indent=1,ensure_ascii=False,default=str))
    else: print('abandoned.json',A['w30']['n'],A['w30']['recPct'],A['w90']['n'],A['w90']['recPct'])
