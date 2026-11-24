# Builds ../ad_types_reach.json ("Ad types & reach" section) from:
#  adlib_sample.json  (logged-out Ad Library listing scrape, India, active; adlib_scrape.mjs)
#  ../ads_meta.json   (Ad Library tool counts), reach_real.json (EU transparency + political ads; adlib_detail.mjs)
#  ig_followers.json, similarweb.json (third-party estimates), own_summary.json (Dorje's own Meta account, read-only)
import json, math, datetime as dt
from collections import Counter
CHECK='2026-11-13'; today=dt.date(2026,11,13)
S=json.load(open('adlib_sample.json')); M=json.load(open('../ads_meta.json'))['brands']
R=json.load(open('reach_real.json')); IG=json.load(open('ig_followers.json')); SW=json.load(open('similarweb.json')); OWN=json.load(open('own_summary.json'))
NAME={'dorje':'Dorje Teas','vahdam':'Vahdam','teabox':'Teabox','tcotw':'Tea Culture of the World','sancha':'Sancha','goldentips':'Golden Tips','goodricke':'Goodricke',
 'makaibari':'Makaibari','organicindia':'Organic India','kaahu':'Kaahu','mittal':'Mittal Teas','happyvalley':'Happy Valley Organic','jayshree':'Jay Shree Tea','udyan':'Udyan'}
PL={'FB':'Facebook','IG':'Instagram','AN':'Audience Network','MSG':'Messenger','TH':'Threads','WA':'WhatsApp'}
def pdate(s):
  try: return dt.datetime.strptime(s,'%b %d, %Y').date()
  except Exception: return None
brands=[]
for b in NAME:
  s=S.get(b); ads=(s or {}).get('ads',[]); lt=(s or {}).get('total'); active=max(int(M.get(b,{}).get('active') or 0), int(str(lt).replace(',','')) if lt and str(lt).replace(',','').isdigit() else 0)
  w=[a.get('same',1) for a in ads]; n=sum(w)
  row={'b':b,'name':NAME[b],'active':active,'listingTotal':lt,'cards':len(ads),'covered':n,
       'src':f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id={s['pid']}&media_type=all" if s else None}
  if ads:
    f=Counter(); pl=Counter(); cta=Counter(); dom=Counter(); lang=Counter(); age=[]; new7=new28=0; multi=0; price=0
    for a,k in zip(ads,w):
      fm='Video' if a['vids'] else ('Carousel' if a['imgs']>=2 else 'Single image')
      f[fm]+=k
      if a['multi']: multi+=k
      if a['cards']>=2: price+=k
      for p in a['pl']: pl[PL[p]]+=k
      cs=[c for c in a['ctas'] if not (c=='learn more' and a['vids'] and len(a['ctas'])>1)]
      for c in cs or ['(not shown)']: cta[c.title() if c!='(not shown)' else c]+=k
      d=(a['doms'] or ['(not shown)'])[0].split('/')[0].lower(); dom[d]+=k
      lang['Hindi (Devanagari)' if a['deva'] else 'Bengali' if a['beng'] else 'Hinglish' if a['hinglish'] else 'English']+=k
      sd=pdate(a.get('start') or '')
      if sd:
        days=(today-sd).days; age+= [days]*k
        if days<=7: new7+=k
        if days<=28: new28+=k
    pct=lambda c:[[x,round(v*100/n)] for x,v in c.most_common()]
    age.sort(); med=age[len(age)//2] if age else None
    buckets=[['≤7 days',sum(1 for x in age if x<=7)],['8–30 days',sum(1 for x in age if 7<x<=30)],['31–90 days',sum(1 for x in age if 30<x<=90)],['>90 days',sum(1 for x in age if x>90)]]
    row.update({'formats':pct(f),'placements':pct(pl),'ctas':pct(cta),'landing':pct(dom)[:4],'langs':pct(lang),
      'multiPct':round(multi*100/n),'pricePct':round(price*100/n),'variantsPerConcept':round(n/len(ads),1),'medianDays':med,'maxDays':age[-1] if age else None,
      'longevity':[[k,round(v*100/len(age))] for k,v in buckets] if age else [],
      'new7':new7,'new28':new28,'perWeekNote':'at least (new ads seen in the sampled cards, last 28 days ÷ 4)','perWeek':round(new28/4,1)})
  ig=IG.get(b,{}); row['ig']={'handle':ig.get('handle'),'followers':ig.get('followers'),'posts':ig.get('posts'),'url':f"https://www.instagram.com/{ig.get('handle')}/" if ig.get('handle') else None}
  sw=SW.get(b); row['sw']=dict(sw, url=f"https://www.similarweb.com/website/{sw['domain'].split(' ')[0]}/") if sw else None
  row['real']=[r for r in R if r['brand']==b]
  brands.append(row)
# Estimated ad pressure index (0-100): NOT reach. Relative weight of visible Meta activity in India.
def norm(vals):
  mx=max(vals) or 1; return [v/mx for v in vals]
act=norm([math.log1p(r['active']) for r in brands]); cad=norm([math.log1p(r.get('perWeek') or 0) for r in brands])
lon=norm([min(r.get('medianDays') or 0,180) for r in brands]); var=norm([(r.get('variantsPerConcept') or 0)*(1+(r.get('multiPct') or 0)/100) for r in brands])
brd=norm([len(r.get('placements') or []) for r in brands])
for i,r in enumerate(brands):
  r['api']=round(100*(.40*act[i]+.20*cad[i]+.15*lon[i]+.15*var[i]+.10*brd[i])) if r['active'] else 0
brands.sort(key=lambda r:-r['api'])
own=OWN
out={'checked':CHECK,'brands':brands,'own':own,
 'apiMethod':'Estimated ad pressure index (0–100, relative to the busiest brand): 40% active Meta ads in India (log), 20% launch cadence (new ads per week, log), 15% median age of sampled ads, 15% variants per concept × multi-version share, 10% placement breadth. It is an ESTIMATE of visible ad activity, not reach, impressions or spend — Meta does not publish those for commercial ads in India.',
 'limits':['Meta publishes reach only for ads shown in the EU/UK and spend/impressions only for political or social-issue ads; India commercial ads have neither. Google Ads Transparency shows ad counts, formats and regions but no impressions for commercial ads.',
   'Format/placement/CTA mix comes from the first ~20–30 ad cards Meta shows logged out (identical ads are grouped, so "covered" counts the ads those cards represent). Vahdam and Organic India have hundreds of ads, so theirs is the newest slice only. Makaibari\'s Ad Library page did not load logged out.',
   'Catalogue/DPA and Collection ads cannot be told apart reliably from the public card; "shows prices" flags cards with two or more ₹ prices. "Multiple versions" means dynamic/flexible creative.',
   'Instagram post engagement (likes/comments per post) is not readable without logging in, so only follower and post counts are shown.',
   'Similarweb numbers are third-party modelled estimates for October 2026, not measured traffic.']}
json.dump(out,open('../ad_types_reach.json','w'),separators=(',',':'),ensure_ascii=False)
for r in brands: print(r['name'],r['active'],r['api'],r.get('perWeek'),r.get('medianDays'),r.get('multiPct'),r.get('variantsPerConcept'),(r.get('formats') or [])[:3],(r.get('placements') or [])[:6])
