#!/usr/bin/env python3
"""Dorje Growth Dashboard - Meta Ads + SEO/GEO pull (read-only).
Writes meta.json and seo.json next to this file. Never prints the token."""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime as dt
HERE=os.path.dirname(os.path.abspath(__file__))
from _env import need, env
TOK=need('META_ACCESS_TOKEN')                      # long-lived token with ads_read (see docs/SETUP.md)
ACT=env('META_AD_ACCOUNT_ID','act_XXXXXXXXXXXXXXX')  # e.g. act_1234567890; set in .env
if not ACT.startswith('act_'): ACT='act_'+ACT
V=env('META_API_VERSION','v21.0')
IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
today=dt.datetime.now(IST).date()
def rng(days,offset=0):
    end=today-dt.timedelta(days=1+offset); start=end-dt.timedelta(days=days-1); return str(start),str(end)
W={'7d':rng(7),'p7d':rng(7,7),'30d':rng(30),'p30d':rng(30,30)}
def get(path,params):
    params=dict(params); params['access_token']=TOK
    url=f'https://graph.facebook.com/{V}/{path}?'+urllib.parse.urlencode(params); out=[]
    while url:
        try: r=json.load(urllib.request.urlopen(url,timeout=120))
        except urllib.error.HTTPError as e: return {'error':e.read().decode().replace(TOK,'***')[:300]}
        if 'data' not in r: return r
        out+=r['data']; url=r.get('paging',{}).get('next')
    return out
def act(l,k='omni_purchase'):
    for x in l or []:
        if x['action_type']==k: return float(x['value'])
    return 0.0
def summ(m):
    s=float(m.get('spend',0)); p=act(m.get('actions')); v=act(m.get('action_values'))
    return {'spend':round(s),'purchases':int(p),'value':round(v),'roas':round(v/s,2) if s else 0,'cpa':round(s/p) if p else None,
            'cpm':round(float(m.get('cpm',0))),'ctr':round(float(m.get('ctr',0)),2),'freq':round(float(m.get('frequency',0)),2),'impressions':int(m.get('impressions',0))}
def meta():
    F='spend,impressions,frequency,cpm,ctr,actions,action_values'
    out={'windows':W,'account':ACT,'totals':{}}
    for k,(a,b) in W.items():
        r=get(f'{ACT}/insights',{'fields':F,'time_range':json.dumps({'since':a,'until':b}),'level':'account'})
        out['totals'][k]=summ(r[0]) if isinstance(r,list) and r else {'spend':0,'purchases':0,'value':0,'roas':0,'cpa':None,'cpm':0,'ctr':0,'freq':0,'impressions':0}
    a,b=W['30d']
    camps=get(f'{ACT}/insights',{'fields':'campaign_id,campaign_name,'+F,'time_range':json.dumps({'since':a,'until':b}),'level':'campaign','limit':200})
    meta_c={c['id']:c for c in get(f'{ACT}/campaigns',{'fields':'id,name,effective_status,objective','limit':200})}
    adsets=get(f'{ACT}/adsets',{'fields':'id,name,campaign_id,effective_status,targeting{custom_audiences,excluded_custom_audiences}','limit':300,
        'filter':json.dumps([{'field':'adset.effective_status','operator':'IN','value':['ACTIVE']}])})
    ex={}
    for s in adsets if isinstance(adsets,list) else []:
        t=s.get('targeting',{}); cid=s['campaign_id']
        e=ex.setdefault(cid,{'active_adsets':0,'with_exclusion':0,'warm':0})
        e['active_adsets']+=1
        if t.get('excluded_custom_audiences'): e['with_exclusion']+=1
        if t.get('custom_audiences'): e['warm']+=1
    rows=[]
    for m in camps if isinstance(camps,list) else []:
        c=meta_c.get(m['campaign_id'],{}); r=summ(m); r['name']=m['campaign_name']; r['status']=c.get('effective_status','')
        e=ex.get(m['campaign_id'],{'active_adsets':0,'with_exclusion':0,'warm':0}); r.update(e)
        n=r['name'].lower()
        r['type']='Retargeting' if (e['warm'] or 'retarget' in n) else ('Awareness' if 'aware' in n else 'Prospecting')
        flags=[]
        if r['spend']>=5000 and r['roas']<0.8: flags.append('Dead spend')
        if r['type']=='Prospecting' and r['status']=='ACTIVE' and e['active_adsets'] and e['with_exclusion']==0: flags.append('No buyer exclusion')
        if r['freq']>=4: flags.append('High frequency')
        r['flags']=flags; rows.append(r)
    rows.sort(key=lambda r:-r['spend']); out['campaigns']=rows
    cm=today.replace(day=1); y=cm-dt.timedelta(days=1); m0=dt.date(cm.year-1,cm.month,1)
    mo=get(f'{ACT}/insights',{'fields':'spend','time_range':json.dumps({'since':str(m0),'until':str(y)}),'time_increment':'monthly','level':'account','limit':50})
    out['monthly_spend']={x['date_start'][:7]:round(float(x['spend'])) for x in mo} if isinstance(mo,list) else {}
    return out
PAGES=['/','/products/first-flush-tea','/products/second-flush','/collections/black-tea','/collections/wellness-range','/collections/seasonal-subscription','/collections/pyramid-teabags']
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120'}
def fetch(u):
    t=time.time()
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60); b=r.read(); return r.status,b.decode('utf-8','ignore'),time.time()-t,len(b)
    except urllib.error.HTTPError as e: return e.code,'',time.time()-t,0
def seo():
    base='https://dorjeteas.com'; pages=[]
    for p in PAGES:
        code,h,secs,size=fetch(base+p)
        title=(re.search(r'<title>(.*?)</title>',h,re.S) or [None,''])[1].strip() if h else ''
        desc=re.search(r'<meta name="description" content="([^"]*)"',h); desc=desc.group(1) if desc else ''
        h1=[re.sub(r'<[^>]+>|\s+',' ',x).strip() for x in re.findall(r'<h1[^>]*>(.*?)</h1>',h,re.S)]
        types=[]
        for blk in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',h,re.S):
            try:
                d=json.loads(blk); items=d if isinstance(d,list) else d.get('@graph',[d])
                types+= [str(i.get('@type')) for i in items if isinstance(i,dict)]
            except Exception: pass
        imgs=re.findall(r'<img[^>]*>',h); noalt=sum(1 for i in imgs if 'alt=""' in i or 'alt=' not in i)
        scripts=len(re.findall(r'<script[^>]+src=',h))
        checks={'status_200':code==200,'title_ok':10<=len(title)<=65,'desc_ok':70<=len(desc)<=160,'one_h1':len([x for x in h1 if x])==1,
                'product_schema':('Product' in types) if '/products/' in p else None,'org_schema':'Organization' in types,'faq_schema':'FAQPage' in types,
                'breadcrumb_schema':'BreadcrumbList' in types,'alt_ok':(noalt/len(imgs)<0.1) if imgs else True}
        applicable=[v for v in checks.values() if v is not None]
        pages.append({'path':p,'status':code,'title':title,'title_len':len(title),'desc_len':len(desc),'h1':h1[:2],'schema':sorted(set(types)),
            'images':len(imgs),'images_no_alt':noalt,'html_kb':round(size/1024),'ttfb_s':round(secs,2),'scripts':scripts,'checks':checks,
            'score':round(100*sum(1 for v in applicable if v)/len(applicable))})
    _,robots,_,_=fetch(base+'/robots.txt'); _,llms,_,_=fetch(base+'/llms.txt'); c,_,_,_=fetch(base+'/sitemap.xml')
    ai_block=[b for b in ['GPTBot','PerplexityBot','ClaudeBot','Google-Extended','CCBot'] if re.search(r'User-agent:\s*'+b+r'[\s\S]{0,80}Disallow:\s*/\s',robots,re.I)]
    site={'sitemap_ok':c==200,'robots_has_sitemap':'Sitemap:' in robots,'ai_bots_blocked':ai_block,'llms_txt':bool(llms),
          'llms_has_brand_facts':bool(re.search(r'Selim Hill|first flush',llms,re.I))}
    sc=round(sum(p['score'] for p in pages)/len(pages))
    gs=sum([site['sitemap_ok'],site['robots_has_sitemap'],not ai_block,site['llms_txt'],site['llms_has_brand_facts']])
    return {'pages':pages,'site':site,'seo_score':sc,'geo_score':round(100*gs/5)}
if __name__=='__main__':
    out={'refreshed_ist':dt.datetime.now(IST).strftime('%d %b %Y, %H:%M IST')}
    out['meta']=meta(); out['seo']=seo()
    json.dump(out,open(os.path.join(HERE,'meta_seo.json'),'w'),indent=1)
    print('ok', out['refreshed_ist'], 'meta 30d spend', out['meta']['totals']['30d']['spend'], 'seo', out['seo']['seo_score'], 'geo', out['seo']['geo_score'])
