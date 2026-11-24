#!/usr/bin/env python3
"""Order-level attribution dataset for the Founders app (Attribution tab + global filters).
Input: shopify/orders/*.json (Shopify Admin orders pages, see shopify_queries.py 'orders' section), meta_attr.json.
Output: attr.json (compact rows + dimension tables + summary)."""
import json, glob, os, re, collections as C
H=os.path.dirname(os.path.abspath(__file__))
O={}
for f in sorted(glob.glob(os.path.join(H,'shopify','orders','*.json')),key=os.path.getmtime):
    for o in json.load(open(f)): O[o['name']]=o
MA=json.load(open(os.path.join(H,'meta_attr.json'))); idmap=MA['idmap']; names=MA['names']
name2id={}
for i,n in names.items(): name2id.setdefault(n.strip().lower(),i)
STATES={'AN':'Andaman & Nicobar','AP':'Andhra Pradesh','AR':'Arunachal Pradesh','AS':'Assam','BR':'Bihar','CH':'Chandigarh','CT':'Chhattisgarh','CG':'Chhattisgarh','DN':'Dadra & Nagar Haveli','DD':'Daman & Diu','DL':'Delhi','GA':'Goa','GJ':'Gujarat','HR':'Haryana','HP':'Himachal Pradesh','JK':'Jammu & Kashmir','JH':'Jharkhand','KA':'Karnataka','KL':'Kerala','LA':'Ladakh','LD':'Lakshadweep','MP':'Madhya Pradesh','MH':'Maharashtra','MN':'Manipur','ML':'Meghalaya','MZ':'Mizoram','NL':'Nagaland','OR':'Odisha','OD':'Odisha','PY':'Puducherry','PB':'Punjab','RJ':'Rajasthan','SK':'Sikkim','TN':'Tamil Nadu','TS':'Telangana','TG':'Telangana','TR':'Tripura','UP':'Uttar Pradesh','UK':'Uttarakhand','UT':'Uttarakhand','WB':'West Bengal'}
NUM=re.compile(r'^\d{12,}$')
def meta_campaign(u):
    c=(u.get('campaign') or '').strip()
    if c and c.lower() in name2id: return name2id[c.lower()]
    for x in (u.get('campaign'),u.get('source'),u.get('medium'),u.get('content')):
        x=(x or '').strip()
        if NUM.match(x) and x in idmap: return idmap[x]
    return None
def channel(v):
    if not v: return 'Unknown (no visit data)', None
    s=(v.get('source') or '').lower(); ref=(v.get('referrerUrl') or '').lower(); u=v.get('utmParameters') or {}
    us=(u.get('source') or '').lower(); um=(u.get('medium') or '').lower()
    if 'zoko' in us or um=='broadcast' or 'whatsapp' in us+s+ref or 'wa.me' in ref or 'l.wl.co' in ref or 'wati' in us: return 'WhatsApp (Zoko)', None
    if us=='google' and um in ('cpc','ppc','paid') or um=='cpc' and 'google' in s: return 'Google Ads', None
    if us in ('google',) and um=='product_sync': return 'Google Shopping (free listing)', None
    if um=='email' or 'email' in us or 'klaviyo' in us or 'android-app://com.google.android.gm' in ref or s=='email': return 'Email', None
    metaish = us in ('fb','facebook','ig','instagram','meta','facebook-sitelink') or NUM.match(us or 'x') or um in ('paid_social','fb','ig') or ('facebook' in us)
    if u and (metaish or (s in ('facebook','instagram') or 'facebook' in ref or 'instagram' in ref)):
        return 'Meta ads', meta_campaign(u)
    if s in ('facebook','instagram') or 'facebook.com' in ref or 'instagram' in ref or 'threads' in ref: return 'Meta organic / social', None
    if 'chatgpt' in s+ref or 'perplexity' in s+ref or 'gemini' in ref or 'copilot' in ref: return 'AI assistants', None
    if s in ('google','bing','yahoo','duckduckgo') or 'googlequicksearchbox' in ref or 'search.brave' in ref or 'google.' in ref: return 'Search (unpaid or untagged)', None
    if 'shopify.com' in ref or 'shop.app' in ref: return 'Shop app / Shopify', None
    if s=='direct': return 'Direct', None
    if 'unknown' in s or not s: return 'Unknown source', None
    return 'Other websites', None
def group(t):
    t=t.lower()
    if 'teabag' in t: return 'Teabags'
    if 'plan' in t: return 'Tea plans'
    if 'combo' in t or 'pack of' in t or 'gift' in t or 'sampler' in t: return 'Combos & gifts'
    if 'green' in t or 'kukicha' in t or 'jasmine' in t: return 'Green teas'
    if 'first flush' in t: return 'First Flush'
    if 'second flush' in t: return 'Second Flush'
    if 'roasted' in t: return 'Roasted'
    if 'autumn' in t: return 'Autumn Flush'
    if 'chai' in t or 'masala' in t: return 'Chai'
    if 'white' in t or 'oolong' in t: return 'White & oolong'
    return 'Herbal & wellness'
def pack(v):
    v=(v or '').lower()
    if 'every' in v or 'deliver' in v or 'monthly' in v: return 'Subscription'
    if 'teabag' in v: return 'Teabags'
    if '1kg' in v or '1 kg' in v: return '1 kg'
    if '500' in v: return '500 g'
    if '250' in v: return '250 g'
    if '100' in v: return '100 g'
    if '50' in v: return '50 g'
    return 'Other'
dims={k:[] for k in ('ch','camp','state','grp','pack','sales','pay')}
def ix(k,v):
    a=dims[k]
    if v not in a: a.append(v)
    return a.index(v)
rows=[]; Lc=list(O.values()); Lc.sort(key=lambda o:o['createdAt'])
import datetime as dt
IST=dt.timedelta(hours=5,minutes=30)
skipped=0
for o in Lc:
    if o.get('cancelledAt'): skipped+=1; continue
    d=(dt.datetime.fromisoformat(o['createdAt'].replace('Z','+00:00'))+IST).date().isoformat()
    rev=round(float(o['currentSubtotalPriceSet']['shopMoney']['amount']))
    j=o.get('customerJourneySummary') or {}
    draft=o['sourceName']=='shopify_draft_order'
    if draft: fc=lc=('Draft / manual order',None)
    else: fc=channel(j.get('firstVisit')); lc=channel(j.get('lastVisit'))
    idx=j.get('customerOrderIndex'); new=1 if idx==1 else 0 if idx else 2
    tags=' '.join(o.get('tags') or []).lower()
    if 'wati' in tags or 'zoko' in tags or 'whatsapp' in tags: sales='WhatsApp order'
    elif draft: sales='Draft / manual'
    else: sales='Online store'
    gw=' '.join(o.get('paymentGatewayNames') or []).lower()
    pay='Cash on delivery' if 'cash' in gw or 'cod' in gw else 'Razorpay (Magic Checkout)' if 'razorpay' in gw else 'Manual / other'
    li=o['lineItems']['nodes']; gm=0; pm=0
    for l in li: gm|=1<<ix('grp',group(l['title'])); pm|=1<<ix('pack',pack(l['variantTitle']))
    st=(o.get('shippingAddress') or {}).get('provinceCode') or '—'
    rows.append([d,rev,ix('ch',fc[0]),ix('ch',lc[0]),ix('camp',names.get(lc[1],'Meta campaign not identified')) if lc[0]=='Meta ads' else -1,
                 new,(1 if o.get('discountCodes') else 0)|(2 if any('buy 1 get 1' in (l['title']+' '+(l['variantTitle'] or '')).lower() for l in li) else 0),ix('state',STATES.get(st,st)),gm,pm,ix('sales',sales),ix('pay',pay),1 if j.get('ready') and (j.get('lastVisit') or j.get('firstVisit')) else 0,
                 ix('camp',names.get(fc[1],'Meta campaign not identified')) if fc[0]=='Meta ads' else -1])
codes=C.Counter(c.upper() for o in Lc if not o.get('cancelledAt') for c in o.get('discountCodes') or [])
# Meta monthly campaign table (spend, purchases, value) keyed by campaign name for UTM match
mm=[[m,names.get(cid,cid),s,p,v] for m,cid,s,p,v in MA['monthly']]
out={'keys':['date','rev','first','last','campLast','new','disc','state','grpMask','packMask','sales','pay','journey','campFirst'],'rows':rows,'dims':dims,
     'codes':codes.most_common(15),'note':'disc bit1=discount code, bit2=Buy-1-Get-1 offer item; new 1=first order, 0=returning, 2=unknown','metaMonthly':mm,'cancelled':skipped,'total':len(Lc)}
json.dump(out,open(os.path.join(H,'attr.json'),'w'),separators=(',',':'))
J=sum(r[12] for r in rows); unk=sum(1 for r in rows if dims['ch'][r[3]] in ('Direct','Unknown source','Unknown (no visit data)'))
print('orders',len(rows),'cancelled',skipped,'journey %.1f%%'%(100*J/len(rows)),'direct/unknown last %.1f%%'%(100*unk/len(rows)),'size KB',os.path.getsize(os.path.join(H,'attr.json'))//1024)
print(dims['ch']); print(dims['grp']); print(dims['pack']); print(dims['sales'],dims['pay'])

# ---- Growth Dashboard (Canvas) summary: last 30 complete days ending at the last order day before today
def inr(x):
    return f"₹{x/1e5:.2f}L" if abs(x)>=1e5 else f"₹{x:,.0f}"
end=(dt.datetime.now()+dt.timedelta(0)).date()-dt.timedelta(days=1)
f30=(end-dt.timedelta(days=29)).isoformat(); e=end.isoformat()
R30=[r for r in rows if f30<=r[0]<=e]
tot=sum(r[1] for r in R30) or 1
UNK={'Direct','Unknown source','Unknown (no visit data)'}
def tab(i):
    c=C.defaultdict(lambda:[0,0,0])
    for r in R30: x=c[dims['ch'][r[i]]]; x[0]+=1; x[1]+=r[1]; x[2]+=r[5]==1
    return c
L=tab(3); F=tab(2)
chrows=[[k,str(v[0]),inr(v[1]),f"{v[1]/tot*100:.1f}%",str(F.get(k,[0,0])[0]),inr(F.get(k,[0,0])[1]),f"{v[2]/v[0]*100:.0f}%"] for k,v in sorted(L.items(),key=lambda kv:-kv[1][1])]
months=sorted({m for m,*_ in MA['monthly']})
mfrom=months[-1] if months and months[-1]<e[:7] else (months[-2] if len(months)>1 else months[-1])
last_full=[m for m in months if m<e[:7] or e.endswith(('-30','-31'))][-1]
mp=sum(p for m,_c,s,p,v in MA['monthly'] if m==last_full); ms=sum(s for m,_c,s,p,v in MA['monthly'] if m==last_full)
so=[r for r in rows if r[0][:7]==last_full and r[4]>=0]; sr=sum(r[1] for r in so)
cov=sum(r[12] for r in R30)/max(1,len(R30))*100; unk=sum(1 for r in R30 if dims['ch'][r[3]] in UNK)/max(1,len(R30))*100
summary={'window':f"{f30} to {e}",'metrics':[
  {'value':f"{cov:.1f}%",'label':'Orders with visit data, 30d','detail':'Shopify customer journey coverage'},
  {'value':f"{unk:.0f}%",'label':'Direct / unknown, 30d','detail':'last visit had no clear source','tone':'warning' if unk>20 else None},
  {'value':f"{(mp-len(so))/max(1,len(so))*100:+.0f}%",'label':f'Meta over-claim, {last_full}','detail':f"Meta {mp:,} purchases vs {len(so):,} Shopify orders from Meta links"},
  {'value':f"{sr/ms:.2f}" if ms else '–','label':f'Shopify-verified Meta ROAS, {last_full}','detail':f"{inr(sr)} tagged revenue on {inr(ms)} spend"}],
  'channels':chrows}
json.dump(summary,open(os.path.join(H,'attr_summary.json'),'w'),ensure_ascii=False)
print('summary',summary['metrics'])
