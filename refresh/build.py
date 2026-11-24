#!/usr/bin/env python3
"""Builds data.json + data_line.txt (the single `const DATA = ...;` line of the dashboard Page)
from shopify/*.json (saved by ingest.py from the Shopify MCP) and meta_seo.json (pull_meta_seo.py)."""
import json, os, datetime as dt, collections
H=os.path.dirname(os.path.abspath(__file__))
def L(n): return json.load(open(os.path.join(H,'shopify',n+'.json')))
def rows(n):
    d=L(n); cols=[c['name'] for c in d['columns']]; return [dict(zip(cols,r)) for r in d['rows']]
MS=json.load(open(os.path.join(H,'meta_seo.json'))); M=MS['meta']; S=MS['seo']; W=M['windows']
def inr(x):
    x=float(x)
    if abs(x)>=1e5: return f"₹{x/1e5:.2f}L"
    return "₹"+f"{x:,.0f}"
def pct(a,b):
    if not b: return "n/a"
    c=(a-b)/b*100; return f"{'+' if c>=0 else '−'}{abs(c):.0f}%"
def win(key,daily,fields):
    a,b=W[key]; t=collections.Counter()
    for r in daily:
        if a<=r['day']<=b:
            for f in fields: t[f]+=float(r[f] or 0)
    return t
sales=rows('daily_sales'); sess=rows('daily_sessions')
SF=['orders','net_sales','total_sales','new_customers','returning_customers']; XF=['sessions','sessions_with_cart_additions','sessions_that_reached_checkout','sessions_that_completed_checkout']
K={}
for k in W:
    s=win(k,sales,SF); x=win(k,sess,XF); m=M['totals'][k]
    K[k]=dict(rev=s['net_sales'],tot=s['total_sales'],orders=s['orders'],aov=s['net_sales']/s['orders'] if s['orders'] else 0,
        sessions=x['sessions'],cvr=x['sessions_that_completed_checkout']/x['sessions']*100 if x['sessions'] else 0,
        new=s['new_customers'],ret=s['returning_customers'],spend=m['spend'],
        mer=s['total_sales']/m['spend'] if m['spend'] else 0,cac=m['spend']/s['new_customers'] if s['new_customers'] else 0,
        atc=x['sessions_with_cart_additions'],chk=x['sessions_that_reached_checkout'],done=x['sessions_that_completed_checkout'])
def tone(c,good_up=True):
    if c in (None,): return None
    return None if abs(c)<5 else ('success' if (c>0)==good_up else 'danger')
def kpis(cur,prev):
    a,b=K[cur],K[prev]
    def ch(f): return (a[f]-b[f])/b[f]*100 if b[f] else 0
    def m(label,val,f,good_up=True,detail=None):
        c=ch(f); d=f"{pct(a[f],b[f])} vs prior ({detail(b) if detail else ''})"
        out={'value':val,'label':label,'detail':d}; t=tone(c,good_up)
        if t: out['tone']=t
        return out
    return [m('Net revenue',inr(a['rev']),'rev',detail=lambda b:inr(b['rev'])),
            m('Orders',f"{a['orders']:,.0f}",'orders',detail=lambda b:f"{b['orders']:,.0f}"),
            m('AOV',inr(a['aov']),'aov',detail=lambda b:inr(b['aov'])),
            m('Sessions',f"{a['sessions']:,.0f}",'sessions',detail=lambda b:f"{b['sessions']:,.0f}"),
            m('Conversion rate',f"{a['cvr']:.2f}%",'cvr',detail=lambda b:f"{b['cvr']:.2f}%"),
            m('New customers',f"{a['new']:,.0f}",'new',detail=lambda b:f"{b['new']:,.0f}"),
            m('Returning customers',f"{a['ret']:,.0f}",'ret',detail=lambda b:f"{b['ret']:,.0f}"),
            m('Ad spend (Meta)',inr(a['spend']),'spend',good_up=False,detail=lambda b:inr(b['spend'])),
            m('Blended ROAS (MER)',f"{a['mer']:.2f}x",'mer',detail=lambda b:f"{b['mer']:.2f}x"),
            m('Blended CAC',inr(a['cac']),'cac',good_up=False,detail=lambda b:inr(b['cac']))]
# Meta
mt=M['totals']
meta_metrics=[{'value':inr(mt['30d']['spend']),'label':'Meta spend, 30d','detail':f"{pct(mt['30d']['spend'],mt['p30d']['spend'])} vs prior ({inr(mt['p30d']['spend'])})"},
  {'value':f"{mt['30d']['roas']:.2f}","label":'Meta-reported ROAS, 30d','detail':f"prior {mt['p30d']['roas']:.2f}. 7d {mt['7d']['roas']:.2f} vs {mt['p7d']['roas']:.2f}",**({'tone':'warning'} if mt['30d']['roas']<2 else {})},
  {'value':inr(mt['30d']['cpa'] or 0),'label':'Meta-reported CPA, 30d','detail':f"{mt['30d']['purchases']} purchases. Prior {inr(mt['p30d']['cpa'] or 0)}"},
  {'value':f"₹{mt['30d']['cpm']}",'label':'CPM, 30d','detail':f"prior ₹{mt['p30d']['cpm']}. Frequency {mt['30d']['freq']}",**({'tone':'danger'} if mt['30d']['cpm']>2*max(mt['p30d']['cpm'],1) else {})}]
camp_rows=[[c['name'],c['type'],inr(c['spend']),f"{c['roas']:.2f}",inr(c['cpa']) if c['cpa'] else '–',f"{c['freq']:.2f}",f"{c['with_exclusion']}/{c['active_adsets']}",', '.join(c['flags']) or 'OK'] for c in M['campaigns']]
dead=[c for c in M['campaigns'] if 'Dead spend' in c['flags']]; noex=[c for c in M['campaigns'] if 'No buyer exclusion' in c['flags']]
# Retention
rfm={r['rfm_group']:r for r in rows('rfm')}
buyers=sum(int(r['new_customer_records']) for g,r in rfm.items() if g!='prospects')
orders_all=sum(int(r['total_number_of_orders']) for g,r in rfm.items() if g!='prospects')
def c(g): return int(rfm.get(g,{}).get('new_customer_records',0))
ret_metrics=[{'value':f"{orders_all/buyers:.2f}",'label':'Orders per customer (lifetime)','detail':f"{orders_all:,} orders from {buyers:,} buyers"},
  {'value':f"{K['30d']['ret']/(K['30d']['new']+K['30d']['ret'])*100:.0f}%",'label':'Returning share of buyers, 30d','detail':f"{K['30d']['ret']:,.0f} returning, {K['30d']['new']:,.0f} new"},
  {'value':f"{c('at_risk')+c('almost_lost')+c('previously_loyal'):,}",'label':'At-risk customers','detail':f"at risk {c('at_risk'):,}, almost lost {c('almost_lost'):,}, previously loyal {c('previously_loyal'):,}",'tone':'warning'},
  {'value':f"{c('dormant'):,}",'label':'Dormant customers','detail':f"{c('dormant')/buyers*100:.0f}% of buyers. {float(rfm['dormant']['days_since_last_order']):.0f} days since last order (Shopify RFM)",'tone':'danger'}]
seg_order=['champions','loyal','active','new','promising','needs_attention','almost_lost','at_risk','previously_loyal','dormant']
seg_rows=[[g.replace('_',' ').capitalize(),f"{c(g):,}",f"{c(g)/buyers*100:.0f}%",inr(float(rfm[g]['total_amount_spent'])),f"{float(rfm[g]['days_since_last_order']):.0f}"] for g in seg_order if g in rfm]
subs=rows('subs_30d'); sub_net=sum(float(r['net_sales']) for r in subs); sub_ord=sum(int(r['orders']) for r in subs)
coh=rows('cohorts'); coh_rows=[[dt.date.fromisoformat(r['month']).strftime('%b %Y'),f"{int(r['new_customer_records']):,}",f"{int(r['total_number_of_orders']):,}",f"{int(r['total_number_of_orders'])/int(r['new_customer_records']):.2f}",inr(float(r['total_amount_spent'])/int(r['new_customer_records']))] for r in coh]
coh_chart={'labels':[dt.date.fromisoformat(r['month']).strftime('%b') for r in coh],'values':[round(int(r['total_number_of_orders'])/int(r['new_customer_records']),2) for r in coh]}
# Abandoned
ab=L('abandoned_p1')['data']; cat=L('catalog')['data']
nodes=list(ab['abandonedCheckouts']['nodes'])
import os as _os
for _p in ('abandoned_p2','abandoned_p3'):
    if _os.path.exists(f'shopify/{_p}.json'): nodes+=L(_p)['data']['abandonedCheckouts']['nodes']
nodes=list({(x['createdAt'],x['totalPriceSet']['shopMoney']['amount']):x for x in nodes}.values()); n=len(nodes); val=sum(float(x['totalPriceSet']['shopMoney']['amount']) for x in nodes)
rec=[x for x in nodes if x['completedAt']]; known=sum(1 for x in nodes if x['customer'])
pc=collections.Counter(); pv=collections.Counter()
for x in nodes:
    for li in x['lineItems']['nodes']: pc[li['title']]+=li['quantity']; pv[li['title']]+=1
prior_ab=cat['prior']['count']
ab_metrics=[{'value':f"{n}",'label':'Abandoned checkouts, 30d','detail':f"{pct(n,prior_ab)} vs prior ({prior_ab})"},
  {'value':inr(val),'label':'Value left in checkout','detail':f"avg {inr(val/n if n else 0)} per checkout"},
  {'value':f"{len(rec)/n*100:.1f}%" if n else '0%','label':'Recovery rate','detail':f"{len(rec)} recovered later. Good flows reach 10–15%",**({'tone':'danger'} if n and len(rec)/n<0.1 else {})},
  {'value':f"{(1-K['30d']['done']/K['30d']['chk'])*100:.0f}%" if K['30d']['chk'] else 'n/a','label':'Checkout drop-off, 30d','detail':f"{K['30d']['chk']:,.0f} sessions reached checkout, {K['30d']['done']:,.0f} completed"}]
funnel={'labels':['Sessions','Added to cart','Reached checkout','Completed'],'values':[round(K['30d'][k]) for k in ['sessions','atc','chk','done']]}
top_ab=[[t,str(pv[t]),str(pc[t])] for t,_ in pv.most_common(6)]
# Catalog alerts
alerts=[]
for p in cat['products']['nodes']:
    vs=p['variants']['nodes']
    mon=[v for v in vs if 'Monthly' in v['title'] or 'EVERY MONTH' in v['title']]
    small=[v for v in mon if v['title'].startswith('100')]; big=[v for v in mon if v['title'].startswith('250')]
    for s in small:
        for b in big:
            if s['price']==b['price']: alerts.append({'lead':'Pricing','title':f"{p['title']}: 100g monthly sub priced like 250g",'detail':f"Both ₹{float(s['price']):,.0f}. Live in the store now. Set the 100g price (comparable 100g monthly plans are ₹3,549)",'status':{'label':'Critical','tone':'danger'}})
    oos=[v['title'].split(' / ')[0] for v in vs if not v['availableForSale']]
    if p['handle'] in ('first-flush-tea','second-flush') and oos:
        alerts.append({'lead':'Stock','title':f"{p['title']}: {', '.join(sorted(set(oos)))} out of stock",'detail':f"{len(oos)} of {len(vs)} variants unavailable on a hero product. Restock or hide the size and point ads to the 100g",'status':{'label':'High','tone':'danger'}})
oos_all=sum(1 for p in cat['products']['nodes'] for v in p['variants']['nodes'] if not v['availableForSale'])
alerts.append({'lead':'Checkout','title':'Cart drawer shows the wrong free-shipping threshold','detail':'Says “Rs. 100 from free shipping”, while checkout and policy give free shipping from ₹399. Theme setting, last confirmed in admin. Not auto-checked: verify after fixing','status':{'label':'High','tone':'danger'}})
for c_ in dead: alerts.append({'lead':'Meta','title':f"Dead spend: {c_['name']}",'detail':f"{inr(c_['spend'])} in 30d at ROAS {c_['roas']:.2f}",'status':{'label':'High','tone':'danger'}})
if noex: alerts.append({'lead':'Meta','title':f"{len(noex)} prospecting campaigns have no buyer exclusion",'detail':f"{', '.join(x['name'].split('|')[0].split('–')[0].strip() for x in noex)}: {inr(sum(x['spend'] for x in noex))} in 30d can reach existing customers. Add a purchasers-180d custom audience exclusion",'status':{'label':'High','tone':'danger'}})
for c_ in M['campaigns']:
    if 'High frequency' in c_['flags']: alerts.append({'lead':'Meta','title':f"Frequency {c_['freq']:.1f} on {c_['name']}",'detail':'Audience saturated. Refresh creative or widen the retargeting window','status':{'label':'Medium','tone':'warning'}})
if mt['30d']['cpm']>2*max(mt['p30d']['cpm'],1): alerts.append({'lead':'Meta','title':f"CPM up from ₹{mt['p30d']['cpm']} to ₹{mt['30d']['cpm']}",'detail':'The prior 30 days included cheap awareness reach. Sales campaigns now buy pricier, warmer impressions','status':{'label':'Watch','tone':'warning'}})
if n and len(rec)/n<0.1: alerts.append({'lead':'Retention','title':f"Abandoned-checkout recovery is {len(rec)/n*100:.1f}%",'detail':f"{inr(val)} left in {n} checkouts in 30d. Turn on the email + WhatsApp flows below",'status':{'label':'High','tone':'danger'}})
oos_p=sorted({p['title'].split('|')[0].strip() for p in cat['products']['nodes'] for v in p['variants']['nodes'] if not v['availableForSale']})
alerts.append({'lead':'Catalogue','title':f"{oos_all} variants out of stock across {len(oos_p)} active products",'detail':'Affected: '+', '.join(oos_p)+'. Hide sold-out sizes from Newly Launched and exclude them from ads and catalogue sets','status':{'label':'Medium','tone':'warning'}})
alerts.sort(key=lambda a:['Critical','High','Medium','Watch'].index(a['status']['label']))
# SEO
P=S['pages']; st=S['site']
seo_rows=[[p['path'],str(p['score']),f"{p['title_len']}",f"{p['desc_len']}",'Yes' if p['checks']['one_h1'] else (f"{len(p['h1'])} H1s" if len([x for x in p['h1'] if x])>1 else ('Empty' if p['h1'] else 'Missing')),', '.join(p['schema']) or 'None',f"{p['images_no_alt']}/{p['images']}",f"{p['html_kb']} KB, {p['scripts']} scripts"] for p in P]
fixes=[]
def cnt(f): return sum(1 for p in P if p['checks'].get(f) is False)
if cnt('org_schema'): fixes.append(['1','Add Organization + WebSite JSON-LD (logo, sameAs: Instagram, LinkedIn, Amazon; Selim Hill estate)',f"Missing on {cnt('org_schema')}/{len(P)} pages",'High'])
if cnt('one_h1'): fixes.append([str(len(fixes)+1),'One real H1 per page: fill the empty homepage H1, add H1 to collections, remove duplicate PDP H1',f"{cnt('one_h1')}/{len(P)} pages fail",'High'])
if cnt('desc_ok'): fixes.append([str(len(fixes)+1),'Rewrite meta descriptions to 140–155 chars with the keyword + offer',f"{cnt('desc_ok')}/{len(P)} pages too long or missing",'High'])
if cnt('faq_schema'): fixes.append([str(len(fixes)+1),'Add FAQPage schema on PDPs and collections (brew guide, caffeine, shipping, freshness)',f"Missing on {cnt('faq_schema')}/{len(P)} pages",'High'])
if not st['llms_has_brand_facts']: fixes.append([str(len(fixes)+1),'Extend /llms.txt with brand facts: estate, flush calendar, certifications, best-sellers, prices','Current file is the default Shopify agent-commerce text','Medium'])
if cnt('breadcrumb_schema'): fixes.append([str(len(fixes)+1),'Add BreadcrumbList schema',f"Missing on {cnt('breadcrumb_schema')}/{len(P)} pages",'Medium'])
if cnt('alt_ok'): fixes.append([str(len(fixes)+1),'Add alt text to product and lifestyle images',f"{sum(p['images_no_alt'] for p in P)} images without alt across key pages",'Medium'])
if cnt('title_ok'): fixes.append([str(len(fixes)+1),'Lengthen short titles to 50–60 chars (e.g. collections with keyword + Darjeeling)',f"{cnt('title_ok')}/{len(P)} titles out of range",'Low'])
heavy=[p for p in P if p['html_kb']>300]
if heavy: fixes.append([str(len(fixes)+1),'Cut HTML weight and third-party scripts (inline JSON, app embeds)',f"HTML {min(p['html_kb'] for p in heavy)}–{max(p['html_kb'] for p in heavy)} KB per page, ~{P[0]['scripts']} external scripts",'Medium'])
site_rows=[{'title':'sitemap.xml','detail':'Reachable' if st['sitemap_ok'] else 'Not reachable','status':{'label':'OK' if st['sitemap_ok'] else 'Fix','tone':'success' if st['sitemap_ok'] else 'danger'}},
  {'title':'robots.txt','detail':('Lists the sitemap. ' if st['robots_has_sitemap'] else 'No sitemap line. ')+('No AI crawlers blocked' if not st['ai_bots_blocked'] else 'Blocks '+', '.join(st['ai_bots_blocked'])),'status':{'label':'OK' if not st['ai_bots_blocked'] else 'Fix','tone':'success' if not st['ai_bots_blocked'] else 'danger'}},
  {'title':'llms.txt','detail':('Present' if st['llms_txt'] else 'Missing')+(', with brand facts' if st['llms_has_brand_facts'] else ', but only Shopify\'s default shopping-agent text, no brand facts'),'status':{'label':'OK' if st['llms_has_brand_facts'] else 'Improve','tone':'success' if st['llms_has_brand_facts'] else 'warning'}},
  {'title':'Server response','detail':f"HTML fetched in {min(p['ttfb_s'] for p in P):.2f}–{max(p['ttfb_s'] for p in P):.2f}s from the crawler. Run PageSpeed Insights for Core Web Vitals",'status':{'label':'OK','tone':'success'}}]
seo_metrics=[{'value':f"{S['seo_score']}/100",'label':'On-page SEO score','detail':f"Avg of {len(P)} key pages: title, description, H1, schema, alt",**({'tone':'danger'} if S['seo_score']<50 else {})},
  {'value':f"{S['geo_score']}/100",'label':'GEO readiness score','detail':'Sitemap, robots, AI crawlers allowed, llms.txt, brand facts'},
  {'value':str(sum(1 for p in P if 'Product' in p['schema'])),'label':'PDPs with Product schema','detail':f"of {sum(1 for p in P if '/products/' in p['path'])} checked"},
  {'value':str(sum(1 for p in P if 'FAQPage' in p['schema'])),'label':'Pages with FAQ schema','detail':f"of {len(P)}",'tone':'danger'}]
tp=rows('top_products_30d'); top_rows=[[r['product_title'],inr(float(r['net_sales'])),r['orders']] for r in tp]
headline=f"Last 30 days: {inr(K['30d']['rev'])} net revenue ({pct(K['30d']['rev'],K['p30d']['rev'])}), {K['30d']['new']:,.0f} new customers ({pct(K['30d']['new'],K['p30d']['new'])}), blended CAC {inr(K['30d']['cac'])} on {inr(K['30d']['spend'])} Meta spend."
D=dict(refreshed=MS['refreshed_ist'],windows={k:f"{dt.date.fromisoformat(a).strftime('%d %b')} – {dt.date.fromisoformat(b).strftime('%d %b')}" for k,(a,b) in W.items()},
  headline=headline,k7=kpis('7d','p7d'),k30=kpis('30d','p30d'),meta=meta_metrics,camps=camp_rows,ret=ret_metrics,segs=seg_rows,
  subs={'net':inr(sub_net),'orders':sub_ord,'share':f"{sub_net/K['30d']['rev']*100:.1f}%"},coh=coh_rows,cohChart=coh_chart,
  ab=ab_metrics,funnel=funnel,topAb=top_ab,known=f"{known}/{n}",alerts=alerts,seo=seo_metrics,seoRows=seo_rows,site=site_rows,fixes=fixes,top=top_rows)
json.dump({'K':K,'ab':{'n':n,'val':val,'rec':len(rec),'prior':prior_ab},'noex':[(x['name'],x['spend']) for x in noex],'camps':M['campaigns'],'rfm':{g:c(g) for g in rfm},'top':[(r['product_title'],float(r['net_sales'])) for r in tp]},open(os.path.join(H,'raw.json'),'w'))
AS=os.path.join(H,'attr_summary.json')
if os.path.exists(AS): D['attr']=json.load(open(AS))
ZP=os.path.join(H,'zoko.json')
if os.path.exists(ZP):
    Zk=json.load(open(ZP)); J=Zk['join']; Cz=Zk['customers']; Tz=Zk['templates']; S=J['segments']
    eng=S.get('In Zoko, has messaged you') or {}; out_=S.get('Not in Zoko') or {}
    part='' if Cz['complete'] else f" (partial: {Cz['fetched']:,} of {Cz['total']:,} contacts downloaded)"
    D['wa']={'asOf':Zk['asOf'],'partial':part,
      'metrics':[{'value':f"{Cz['total']:,}",'label':'WhatsApp contacts','detail':f"{Cz['contactableNow']:,} reachable with a free-form message right now"},
                 {'value':f"{J['reachablePct']:.0f}%",'label':'Buyers reachable on WhatsApp','detail':f"{J['reachable']:,} of {J['buyers']:,} buyers in the last 12 months"+('' if Cz['complete'] else ' (lower bound: contact list partly downloaded)')},
                 {'value':inr(J['revenueReachable']),'label':'Revenue from Zoko contacts','detail':f"{J['revenueReachablePct']:.0f}% of 12-month buyer revenue (who they are, not what WhatsApp caused)"},
                 {'value':(f"{eng.get('repeatRate',0):.0f}% vs {out_.get('repeatRate',0):.0f}%" if eng.get('buyers') else '—'),'label':'Repeat rate: messaged us vs not in Zoko','detail':'Share of buyers with 2+ orders in 12 months'}],
      'segs':[[k,f"{v['buyers']:,}",inr(v['revenue']),inr(v['revPerBuyer']),f"{v['repeatRate']:.0f}%"] for k,v in S.items()],
      'tmpl':[[c,f"{n:,}",f"{a:,}"] for c,n,a in Tz['categories']],
      'abandoned':('Yes: '+', '.join(x['id'] for x in Tz['abandoned'])+' (approved)') if Tz['abandonedExists'] else 'No abandoned-cart template found',
      'recency':[[k,f"{n:,}"] for k,n in Cz['recency']],
      'gaps':Zk['gaps']}
    m=Zk.get('messageSample')
    if m: D['wa']['sample']=f"Sample of {m['contacts']} contacts ({m['messages']:,} messages), estimate: {dict(m['sources']).get('Broadcast',0)*100//max(1,m['outgoing'])}% of messages sent are broadcasts. Of {m['checked']} recent messages checked, {m['delivered']:.0f}% were delivered, {m['read']:.0f}% read and {m['failed']:.0f}% failed, mostly WhatsApp error 131049 (Meta holds back marketing messages to people who get too many). {m['repliedPct']:.0f}% of sampled contacts have written back. Latest abandoned-cart reminder seen in the sample: {m['abandonedLast'] or 'none'}."
json.dump(D,open(os.path.join(H,'data.json'),'w'),ensure_ascii=False,indent=1)
open(os.path.join(H,'data_line.txt'),'w').write('const DATA: any = '+json.dumps(D,ensure_ascii=False,separators=(',',':'))+';')
print(headline); print('alerts',len(alerts),'fixes',len(fixes))
