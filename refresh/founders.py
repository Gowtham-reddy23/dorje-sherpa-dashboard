#!/usr/bin/env python3
"""Builds founders_line.txt: the single `const FDATA: any = ...;` line of the 'Dorje Teas — Founders Dashboard' Page.
Reads raw.json + data.json (build.py), meta_seo.json (pull_meta_seo.py) and shopify/{monthly,sources_30d,catalog}.json."""
import json, os, datetime as dt
H=os.path.dirname(os.path.abspath(__file__))
R=json.load(open(os.path.join(H,'raw.json'))); D=json.load(open(os.path.join(H,'data.json'))); MS=json.load(open(os.path.join(H,'meta_seo.json')))
def S(n): return json.load(open(os.path.join(H,'shopify',n+'.json')))
K=R['K']; a,b=K['30d'],K['p30d']; w7,p7=K['7d'],K['p7d']; AB=R['ab']
def inr(x):
    x=float(x); return f"₹{x/1e5:.2f}L" if abs(x)>=1e5 else "₹"+f"{x:,.0f}"
def ch(x,y): return (x-y)/y*100 if y else 0
def pc(x,y):
    c=ch(x,y); return f"{'up' if c>=0 else 'down'} {abs(c):.0f}%"
def tile(label,val,cur,prev,prevtxt,good_up=True,explain=None):
    c=ch(cur,prev); t={'value':val,'label':label,'detail':f"{pc(cur,prev)} vs previous 30 days ({prevtxt})"+(f". {explain}" if explain else '')}
    if abs(c)>=5: t['tone']='success' if (c>0)==good_up else 'danger'
    return t
rep=a['ret']/(a['ret']+a['new'])*100; rep_p=b['ret']/(b['ret']+b['new'])*100
tiles=[tile('Revenue',inr(a['rev']),a['rev'],b['rev'],inr(b['rev'])),
 tile('Orders',f"{a['orders']:,.0f}",a['orders'],b['orders'],f"{b['orders']:,.0f}"),
 tile('Average order',inr(a['aov']),a['aov'],b['aov'],inr(b['aov'])),
 tile('New customers',f"{a['new']:,.0f}",a['new'],b['new'],f"{b['new']:,.0f}"),
 tile('Repeat customers',f"{rep:.0f}%",rep,rep_p,f"{rep_p:.0f}%",explain='Share of buyers who had bought before'),
 {**tile('Ad spend',inr(a['spend']),a['spend'],b['spend'],inr(b['spend']),explain='Meta only'),'tone':None},
 tile('Cost per new customer',inr(a['cac']),a['cac'],b['cac'],inr(b['cac']),good_up=False,explain='Ad spend ÷ new customers'),
 {'value':inr(AB['val']),'label':'Left in unfinished checkouts','detail':f"{AB['n']} checkouts, only {AB['rec']/AB['n']*100:.0f}% came back to pay (previous 30 days: {AB['prior']} checkouts)",'tone':'danger' if AB['n'] and AB['rec']/AB['n']<0.1 else None}]
tiles=[{k:v for k,v in t.items() if v is not None} for t in tiles]
# verdict
rv=ch(a['rev'],b['rev']); r7=ch(w7['rev'],p7['rev']); nv=ch(a['new'],b['new'])
state='Growing' if rv>=5 else ('Holding steady' if rv>-5 else 'Shrinking')
verdict=f"{state}: revenue is {pc(a['rev'],b['rev'])} over 30 days ({pc(w7['rev'],p7['rev'])} in the last week) and new customers are {pc(a['new'],b['new'])}. Repeat buyers carry {rep:.0f}% of the business. The fixes below are mostly cheap and quick."
# monthly chart (last 12 complete months)
mon=[dict(zip([c['name'] for c in S('monthly')['columns']],r)) for r in S('monthly')['rows']]
cur=dt.date.today().strftime('%Y-%m'); mon=[m for m in mon if m['month'][:7]<cur][-12:]
ms=MS['meta'].get('monthly_spend',{})
labels=[dt.date.fromisoformat(m['month']).strftime('%b %y') for m in mon]
rev=[round(float(m['net_sales'])/1e5,2) for m in mon]; spend=[round(ms.get(m['month'][:7],0)/1e5,2) for m in mon]; newc=[int(m['new_customers']) for m in mon]
pk=max(range(len(newc)),key=lambda i:newc[i])
chart_note=f"New customers peaked at {newc[pk]:,} in {labels[pk]} and were {newc[-1]:,} in {labels[-1]} ({pc(newc[-1],newc[pk])}). Ad spend went from {inr(spend[pk]*1e5)} to {inr(spend[-1]*1e5)} over the same months, and revenue from {inr(rev[pk]*1e5)} to {inr(rev[-1]*1e5)}."
# channels
src={r[0] or 'direct':(int(r[1]),float(r[2])) for r in S('sources_30d')['rows']}
tot=sum(v[1] for v in src.values()) or 1
nm={'direct':'Direct or untracked (incl. WhatsApp and email links)','search':'Google and other search','social':'Social (Instagram, Facebook)'}
src_rows=[[nm.get(k,k.capitalize()),f"{v[0]:,}",inr(v[1]),f"{v[1]/tot*100:.0f}%"] for k,v in sorted(src.items(),key=lambda x:-x[1][1])]
mt=MS['meta']['totals']['30d']
channels=[{'title':'Website (Shopify)','detail':f"{inr(a['rev'])} revenue from {a['orders']:,.0f} orders in 30 days. {a['cvr']:.1f}% of visits end in an order",'status':{'label':'Live','tone':'success'}},
 {'title':'Meta ads (Instagram, Facebook)','detail':f"{inr(mt['spend'])} spent in 30 days. Meta credits itself with {inr(mt['value'])} of sales, ₹{mt['roas']:.2f} back for every ₹1 spent (Meta counts generously)",'status':{'label':'Live','tone':'success'}},
 {'title':'Google Ads','detail':'Numbers will appear once access is connected','status':{'label':'Coming soon — not connected'}},
 {'title':'Amazon','detail':'Numbers will appear once Seller Central is connected','status':{'label':'Coming soon — not connected'}}]
# working / not
top=R['top'][0]; noex=R['noex']; camps=R['camps']
working=[f"Visitors who arrive still buy: {a['cvr']:.1f}% of visits turn into orders, {pc(a['cvr'],b['cvr'])} on the previous 30 days.",
 f"Ads got cheaper per customer: cost per new customer fell from {inr(b['cac'])} to {inr(a['cac'])} while spend was cut {abs(ch(a['spend'],b['spend'])):.0f}%.",
 f"Loyal base and a hero product: {rep:.0f}% of buyers are repeat customers, and {top[0].split('(')[0].strip()} alone made {inr(top[1])} ({top[1]/a['rev']*100:.0f}% of revenue)."]
cat=S('catalog')['data']['products']['nodes']
oos=sum(1 for p in cat for v in p['variants']['nodes'] if not v['availableForSale'])
price_err=[]
for p_ in cat:
    mon=[v for v in p_['variants']['nodes'] if 'Monthly' in v['title'] or 'EVERY MONTH' in v['title']]
    for s in [v for v in mon if v['title'].startswith('100')]:
        for big in [v for v in mon if v['title'].startswith('250')]:
            if s['price']==big['price']: price_err.append((p_['title'], s['price']))
leak_txt=(("a live subscription price error, ") if price_err else "")+f"best-selling 250g packs sold out ({oos} items out of stock), and {inr(AB['val'])} left in unfinished checkouts with only {AB['rec']/AB['n']*100:.0f}% recovered"
notw=[f"Fewer new people are finding us: visits are {pc(a['sessions'],b['sessions'])} and new customers {pc(a['new'],b['new'])} in 30 days. Last week revenue was {pc(w7['rev'],p7['rev'])}.",
 f"Leaks at the till: {leak_txt}.",
 f"Ads also reach people who already buy from us: {len(noex)} of {len(camps)} campaigns ({inr(sum(x[1] for x in noex))} of spend) don't leave out existing customers."]
# decisions
import re
def friendly(n):
    n=re.sub(r'^C\d+-','',n).split('|')[0].split('–')[0].strip()
    return 'test' if n.upper()=='TEST' else n
weak=sorted([c for c in camps if c['type']=='Prospecting' or c['name'].startswith('TEST')],key=lambda c:c['roas'])[:2]
best=sorted([c for c in camps if c['cpa']],key=lambda c:c['cpa'])[:2]
wspend=sum(c['spend'] for c in weak); wp=sum(c['purchases'] for c in weak); bcpa=sum(c['cpa'] for c in best)/len(best)
est=wspend/bcpa
rec_gain=max(0,(0.12-AB['rec']/AB['n']))*AB['n']*(AB['val']/AB['n']) if AB['n'] else 0
search=src.get('search',(0,0))
r_=R['rfm']
decisions=[]
if price_err:
    _pt,_pr=price_err[0]
    decisions.append({'n':'1','ask':f'Fix the wrong price on the {_pt} 100g monthly plan','why':f'It is live at ₹{float(_pr):,.0f}, the same as the 250g plan. Comparable 100g monthly plans cost ₹3,549','impact':'Stops overcharging (about double) anyone who picks this plan','rec':'Approve ₹3,549 today. 10-minute fix','tone':'danger'})
decisions += [
 {'n':'2','ask':'Restock First Flush and Second Flush 250g packs','why':f"Both 250g sizes are sold out. First Flush is our best seller at {inr(top[1])} in 30 days",'impact':'Recovers sales from buyers who want the bigger pack. Size of the loss is not measurable yet','rec':'Restock if the harvest allows. If not, hide the 250g size and offer two 100g packs','tone':'danger'},
 {'n':'3','ask':'Switch on reminders for unfinished checkouts (email + WhatsApp)','why':f"{AB['n']} people left {inr(AB['val'])} in checkout in 30 days. Only {AB['rec']} came back",'impact':f"Estimate: reaching a 12% comeback rate adds about {inr(rec_gain)} a month",'rec':'Approve a 4-message sequence. Discount only in the last message','tone':'warning'},
 {'n':'4','ask':'Move money from the weakest ads to a campaign only for new customers','why':f"The {' and '.join(friendly(c['name']) for c in weak)} campaigns spent {inr(wspend)} for {wp} sales. {len(noex)} campaigns also show ads to existing buyers",'impact':f"Estimate: the same {inr(wspend)} at our best campaigns' cost per sale ({inr(bcpa)}) buys about {est:.0f} sales instead of {wp} (Meta's own counts)",'rec':'Approve moving it and leaving out existing customers from all new-customer ads','tone':'warning'},
 {'n':'5','ask':'Win back lapsed customers','why':f"{r_.get('at_risk',0):,} customers are at risk and {r_.get('previously_loyal',0):,} used to be loyal. They have spent heavily before",'impact':'Cheapest sales we can get: messages cost little compared with ads. In the last 12 months, WhatsApp broadcasts drove 566 orders (Shopify order sources)','rec':'Approve a WhatsApp + email First Flush offer to these groups','tone':'warning'},
 {'n':'6','ask':'Fix website basics for Google and AI search','why':f"Search brought {search[0]} orders and {inr(search[1])} in 30 days, yet key pages score {MS['seo']['seo_score']}/100 on search basics",'impact':'Protects and grows our second-biggest source. No reliable estimate yet','rec':'Approve about a week of website work (page headings, descriptions, product facts for AI tools)','tone':None},
 {'n':'7','ask':'Close the gap on Amazon First Flush','why':'A public check found the 250g listing rated 3.6 stars (232 ratings), listed at ₹595, with text that says 100g. Our site sells 250g at ₹1,249','impact':'Protects brand trust and pricing. Amazon numbers are not connected yet','rec':'Approve fixing the listing and deciding one price policy for Amazon vs the website','tone':None}]
decisions=[{k:v for k,v in d.items() if v is not None} for d in decisions]
t=dt.date.today()
def wk(i):
    s=t+dt.timedelta(days=1+7*i); e=s+dt.timedelta(days=6); return f"{s.strftime('%d %b')} – {e.strftime('%d %b')}"
w1=('Fix the price error and the cart’s free-shipping message. Restock or hide 250g. Switch on checkout reminders','Zero price errors. Reminders live') if price_err else ('Fix the cart’s free-shipping message. Restock or hide 250g. Switch on checkout reminders','Free-shipping message fixed. Reminders live')
plan=[[ 'Week 1',wk(0),w1[0],w1[1]],
 ['Week 2',wk(1),'New-customer ad campaign that leaves out existing buyers. Move money from the weakest ads. Win-back message to lapsed customers','Cost per new customer under '+inr(a['cac'])],
 ['Week 3',wk(2),'Website fixes for Google and AI search. Fix the Amazon First Flush listing','Key pages above 70/100'],
 ['Week 4',wk(3),'Review results and decide next month’s budget. Connect Google Ads and Amazon to this page','New customers back above '+f"{b['new']:,.0f}"+' a month']]
F=dict(updated=MS['refreshed_ist'],period=D['windows']['30d'],verdict=verdict,tiles=tiles,chart={'labels':labels,'rev':rev,'spend':spend,'newc':newc},chartNote=chart_note,
 channels=channels,sources=src_rows,working=working,notw=notw,decisions=decisions,plan=plan)
open(os.path.join(H,'founders_line.txt'),'w').write('const FDATA: any = '+json.dumps(F,ensure_ascii=False,separators=(',',':'))+';')
json.dump(F,open(os.path.join(H,'founders.json'),'w'),ensure_ascii=False,indent=1)
print(verdict)
