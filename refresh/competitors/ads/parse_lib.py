import re,json,sys,datetime
IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
def parse(path):
    t=open(path).read().replace('\n','')
    tot=re.search(r'"estimated_total_count":(\d+)',t)
    ads=[]
    for m in re.finditer(r'\{"id":"(\d+)".*?"page_name":"((?:[^"\\]|\\.)*)","ad_creative_link_title":"((?:[^"\\]|\\.)*)","ad_creation_time":(\d+),"ad_delivery_start_time":(\d+)',t):
        title=json.loads('"'+m.group(3)+'"')
        ads.append(dict(id=m.group(1),page=json.loads('"'+m.group(2)+'"'),title=title,start=datetime.datetime.fromtimestamp(int(m.group(5)),IST).strftime('%Y-%m-%d')))
    return (int(tot.group(1)) if tot else None), ads
if __name__=='__main__':
    for p in sys.argv[1:]:
        n,a=parse(p); print('==',p[:8],n,len(a))
        for x in a: print(x['start'],x['id'],x['page'][:20],'|',x['title'][:90])
