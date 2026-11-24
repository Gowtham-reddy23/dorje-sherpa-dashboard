#!/usr/bin/env python3
"""Builds the Founders app data from the dorje-dashboard pulls (real data only).
Writes <repo>/data/dashboard.json (plain, local only, git-ignored, never deployed) and
<repo>/public/data.enc.json (AES-256-GCM, key = PBKDF2-SHA256(passcode), git-ignored).
Passcode: the DASH_PASSCODE env var (.env, never committed)."""
import json, os, re, base64, secrets, hashlib, datetime as dt, collections
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
H=os.path.dirname(os.path.abspath(__file__)); APP=os.path.join(H,'..')   # repo root (the Next.js app)
from _env import need
def S(n): return json.load(open(os.path.join(H,'shopify',n+'.json')))
def rows(n):
    d=S(n); c=[x['name'] for x in d['columns']]; return [dict(zip(c,r)) for r in d['rows']]
f=lambda x: float(x or 0)
MA=json.load(open(os.path.join(H,'meta_app.json'))); MS=json.load(open(os.path.join(H,'meta_seo.json')))
D=json.load(open(os.path.join(H,'data.json'))); R=json.load(open(os.path.join(H,'raw.json'))); FD=json.load(open(os.path.join(H,'founders.json')))
# daily series
day=collections.defaultdict(dict)
for n in ('daily_sales_prev','daily_sales_400','daily_sales'):
    for r in rows(n): day[r['day']].update(rev=f(r['net_sales']),tot=f(r['total_sales']),ord=int(f(r['orders'])),new=int(f(r['new_customers'])),ret=int(f(r['returning_customers'])))
for n in ('daily_sessions_prev','daily_sessions_400','daily_sessions'):
    for r in rows(n): day[r['day']].update(ses=int(f(r['sessions'])),atc=int(f(r['sessions_with_cart_additions'])),chk=int(f(r['sessions_that_reached_checkout'])),done=int(f(r['sessions_that_completed_checkout'])))
for x in MA['daily']: day[x['d']].update(spend=x['spend'],mp=x['purch'],mv=x['value'])
end=max(k for k in day if 'rev' in k or 'rev' in day[k])
keys=['rev','tot','ord','new','ret','ses','atc','chk','done','spend','mp','mv']
daily=[[d]+[round(day[d].get(k,0),2) for k in keys] for d in sorted(day) if d<=end]
# products & mix
def cat(t):
    tl=t.lower()
    if 'buy 1' in tl: return 'BOGO sale packs'
    if 'plan' in tl or 'subscription' in tl: return 'Subscription plans'
    if 'pyramid' in tl: return 'Pyramid teabags'
    if 'flush' in tl or 'moonlight' in tl or 'darjeeling' in tl: return 'Darjeeling flush teas'
    if 'chai' in tl: return 'Chai'
    if any(w in tl for w in ['box','combo','gift','pack']): return 'Gift boxes & combos'
    if not t.strip(): return 'Other / unnamed'
    return 'Wellness & blends'
prods=[[r['product_title'] or '(unnamed item)',round(f(r['net_sales'])),int(f(r['orders']))] for r in rows('products_12m')]
mix=collections.Counter()
for p in prods: mix[cat(p[0] if p[0]!='(unnamed item)' else '')]+=p[1]
nvr={r['new_or_returning_customer']:r for r in rows('new_vs_ret_12m')}
top30=[[r['product_title'],round(f(r['net_sales'])),int(f(r['orders']))] for r in rows('top_products_30d')]
# cohorts (12 complete months)
months=sorted({r['month'] for r in rows('cohorts')})
cm=collections.defaultdict(dict)
for r in rows('cohort_matrix'): cm[r['customer_cohort_month']][r['month']]=int(f(r['customers']))
def moff(a,b): A=dt.date.fromisoformat(a); B=dt.date.fromisoformat(b); return (B.year-A.year)*12+B.month-A.month
heat=[]
for c in months:
    size=cm.get(c,{}).get(c,0)
    if not size: continue
    cells=[]
    for k in range(1,12):
        m=[mm for mm in cm[c] if moff(c,mm)==k]
        if moff(c,months[-1])<k: cells.append(None)
        else: cells.append(round(cm[c][m[0]]/size*100,1) if m else 0.0)
    heat.append({'cohort':dt.date.fromisoformat(c).strftime('%b %y'),'size':size,'cells':cells})
coh=[{'cohort':r['month'],'new':int(r['new_customer_records']),'orders':int(r['total_number_of_orders']),'spend':round(f(r['total_amount_spent']))} for r in rows('cohorts')]
rfm=rows('rfm'); buyers=sum(int(r['new_customer_records']) for r in rfm if r['rfm_group']!='prospects')
seg=[{'seg':r['rfm_group'],'customers':int(r['new_customer_records']),'spend':round(f(r['total_amount_spent'])),'days':round(f(r['days_since_last_order'])),'orders':int(r['total_number_of_orders'])} for r in rfm if r['rfm_group']!='prospects']
ltv_spend=sum(s['spend'] for s in seg)
subs=[[r['product_title'],r['product_variant_title'],round(f(r['net_sales'])),int(r['orders'])] for r in rows('subs_30d')]
# abandoned
ab=S('abandoned_p1')['data']['abandonedCheckouts']['nodes']
import os as _os
for _p in ('abandoned_p2','abandoned_p3'):
    try: ab=ab+S(_p)['data']['abandonedCheckouts']['nodes']
    except Exception: pass
ab=list({(x['createdAt'],x['totalPriceSet']['shopMoney']['amount']):x for x in ab}.values())
abd=collections.Counter(); abv=collections.Counter()
for x in ab: d0=(dt.datetime.fromisoformat(x['createdAt'].replace('Z','+00:00'))+dt.timedelta(hours=5,minutes=30)).date().isoformat(); abd[d0]+=1; abv[d0]+=f(x['totalPriceSet']['shopMoney']['amount'])
abprod=collections.Counter(); abpv=collections.Counter()
for x in ab:
    tv=f(x['totalPriceSet']['shopMoney']['amount']); its=x['lineItems']['nodes']
    for li in its: abprod[li['title']]+=1; abpv[li['title']]+=tv/len(its)
abandoned={'n':len(ab),'value':round(sum(abv.values())),'recovered':sum(1 for x in ab if x['completedAt']),'prior':R['ab']['prior'],
  'withContact':sum(1 for x in ab if x['customer']),'daily':[[k,abd[k],round(abv[k])] for k in sorted(abd)],
  'top':[[t,c,round(abpv[t])] for t,c in abprod.most_common(8)],'window':D['windows']['30d']}
# inventory
cat_=S('catalog')['data']['products']['nodes']
oos=[[p['title'],v['title'],round(f(v['price'])),v['inventoryQuantity']] for p in cat_ for v in p['variants']['nodes'] if not v['availableForSale']]
sales12={p[0]:p[1] for p in prods}
oos=[o+[sales12.get(o[0],0)] for o in oos]; oos.sort(key=lambda o:-o[4])
perr=[]
for p in cat_:
    mon=[v for v in p['variants']['nodes'] if 'Monthly' in v['title'] or 'EVERY MONTH' in v['title']]
    for s in [v for v in mon if v['title'].startswith('100')]:
        for b in [v for v in mon if v['title'].startswith('250')]:
            if s['price']==b['price']: perr.append({'product':p['title'],'variant':s['title'],'price':round(f(s['price'])),'compareAt':round(f(s['compareAtPrice'] or 0)),'issue':f"Same price as the 250g monthly plan (₹{f(b['price']):,.0f}). Comparable 100g monthly plans are ₹3,549",'available':s['availableForSale']})
# seo
seo={'score':MS['seo']['seo_score'],'geo':MS['seo']['geo_score'],'site':MS['seo']['site'],
  'pages':[{'path':p['path'],'score':p['score'],'title':p['title'],'titleLen':p['title_len'],'descLen':p['desc_len'],'h1':len([x for x in p['h1'] if x]),'h1Empty':bool(p['h1']) and not any(p['h1']),'schema':p['schema'],'imgs':p['images'],'noAlt':p['images_no_alt'],'kb':p['html_kb'],'scripts':p['scripts'],'checks':p['checks']} for p in MS['seo']['pages']],
  'fixes':D['fixes']}
owners={'1':'Ops (catalogue)','2':'Founders + supply','3':'Growth (CRM)','4':'Growth (ads)','5':'Growth (CRM)','6':'Growth + web developer','7':'Marketplace lead'}
decisions=[dict(d,owner=owners.get(d['n'],'Founders'),status='Awaiting decision') for d in FD['decisions']]
_leak=['Fix the cart free-shipping message'] if not perr else ['Fix the subscription price error and the cart free-shipping message']
plan={'30':[{'title':'Stop the leaks','items':_leak+['Restock or hide sold-out 250g packs','Switch on unfinished-checkout reminders (email + WhatsApp)','Leave existing buyers out of all new-customer ads']},
            {'title':'Restart new-customer growth','items':['Move spend from the weakest campaigns into one new-customer campaign','Win-back offer to at-risk and previously loyal customers']}],
      '60':[{'title':'Own the customer','items':['Email and WhatsApp sign-up on site, welcome series','Reorder reminder at day 35 (a 100g pack lasts about 40 days)','Website fixes for Google and AI search: headings, descriptions, FAQ and brand schema, llms.txt']},
            {'title':'Marketplace','items':['Fix the Amazon First Flush listing (rating, weight text, price policy)']}],
      '90':[{'title':'Scale what works','items':['Scale new-customer ads while cost per new customer stays below first-order value','Monthly flush launches to the loyal base','Connect Google Ads and Amazon so this app shows the full picture']}]}
data={'updated':FD['updated'],'endDate':end,'keys':keys,'daily':daily,
 'aov':{'first':round(f(nvr['New']['average_order_value'])),'repeat':round(f(nvr['Returning']['average_order_value'])),'firstOrders':int(nvr['New']['orders']),'repeatOrders':int(nvr['Returning']['orders'])},
 'products12m':prods[:25],'top30':top30,'mix':[[k,round(v)] for k,v in mix.most_common()],
 'campaigns':MA['campaigns'],'retention':{'heat':heat,'cohorts':coh,'segments':seg,'buyers':buyers,'ltv':round(ltv_spend/buyers) if buyers else 0,'ordersPerBuyer':round(sum(s['orders'] for s in seg)/buyers,2) if buyers else 0,'subs30':subs},
 'abandoned':abandoned,'inventory':{'oos':oos,'priceErrors':perr,'activeProducts':len(cat_),'variants':sum(len(p['variants']['nodes']) for p in cat_)},
 'seo':seo,'alerts':D['alerts'],'decisions':decisions,'plan':plan,'verdict':FD['verdict'],'working':FD['working'],'notWorking':FD['notw'],
 'amazonPublic':'Public check (earlier audit): First Flush 250g listing rated 3.6★ from 232 ratings, listed at ₹595 with text that says 100g; the website sells 250g at ₹1,249.',
 'notConnected':['Google Ads','Amazon']}
AP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'attr.json')
if os.path.exists(AP): data['attr']=json.load(open(AP))
ABP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'abandoned.json')
if os.path.exists(ABP): data['abDeep']=json.load(open(ABP))   # build_abandoned.py (aggregates only)
ZP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'zoko.json')
if os.path.exists(ZP): data['zoko']=json.load(open(ZP))
CP=os.path.join(os.path.dirname(os.path.abspath(__file__)),'competitors.json')
if os.path.exists(CP): data['comp']=json.load(open(CP))   # build_competitors.py (public data only)
os.makedirs(os.path.join(APP,'data'),exist_ok=True); os.makedirs(os.path.join(APP,'public'),exist_ok=True)
raw=json.dumps(data,ensure_ascii=False,separators=(',',':'))
open(os.path.join(APP,'data','dashboard.json'),'w').write(raw)
pw=need('DASH_PASSCODE').encode(); salt=secrets.token_bytes(16); iv=secrets.token_bytes(12); IT=250000
ct=AESGCM(hashlib.pbkdf2_hmac('sha256',pw,salt,IT,32)).encrypt(iv,raw.encode(),None)
json.dump({'s':base64.b64encode(salt).decode(),'i':base64.b64encode(iv).decode(),'c':base64.b64encode(ct).decode(),'n':IT},open(os.path.join(APP,'public','data.enc.json'),'w'))
print('app data', len(daily),'days to',end,'| heat',len(heat),'| enc',len(ct)//1024,'KB')
