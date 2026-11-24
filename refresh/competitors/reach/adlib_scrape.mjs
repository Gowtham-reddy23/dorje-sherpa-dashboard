// Ad Library (logged out) listing scrape: per active India ad -> start date, platforms, versions, format signals, CTA, domain, language
import { chromium } from 'playwright-core';
import fs from 'fs';
const [,,outFile,...specs]=process.argv; // specs brand:pageId[:max]
const b = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',args:['--no-sandbox']});
const res={};
for(const s of specs){
  const [brand,pid,max='150']=s.split(':');
  const ctx = await b.newContext({viewport:{width:1300,height:1800},locale:'en-US',extraHTTPHeaders:{'Accept-Language':'en-US,en;q=0.9'}});
  await ctx.addCookies([{name:'locale',value:'en_US',domain:'.facebook.com',path:'/'}]);
  const p = await ctx.newPage();
  try{
  await p.goto(`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&view_all_page_id=${pid}&media_type=all`,{waitUntil:'domcontentloaded',timeout:60000});
  await p.waitForTimeout(14000);
  let last=0,same=0;
  for(let i=0;i<40;i++){
    const n=await p.evaluate(()=>document.body.innerText.split('Library ID:').length-1);
    if(n>=+max) break;
    if(n===last){ if(++same>=5) break;} else same=0; last=n;
    await p.evaluate(()=>window.scrollTo(0,document.body.scrollHeight)); await p.mouse.wheel(0,3000); await p.waitForTimeout(4000);
  }
  const r=await p.evaluate(()=>{
    const total=(document.body.innerText.match(/~?([\d,]+) results?/)||[])[1]||null;
    const spans=[...document.querySelectorAll('span')].filter(s=>/^Library ID: \d+$/.test(s.innerText));
    const ads=[];
    for(const sp of spans){
      let c=sp; const cnt=e=>(e.innerText.match(/Library ID:/g)||[]).length;
      while(c.parentElement && cnt(c.parentElement)===1) c=c.parentElement;
      if(!c.innerText.includes('Sponsored')) c=null;
      if(!c) continue;
      const t=c.innerText;
      const pf=[...c.querySelectorAll('span')].find(x=>x.innerText==='Platforms');
            const M={'M12 6.022C12 2':'FB','M6 3.227a2.773':'IG','M6 0c3.17 0 5.':'AN','M6 0C2.706 0 0':'MSG','M6.006.06c1.72':'TH','M4.28 2.92a.52':'WA'};
      const icons=pf?[...new Set([...pf.parentElement.querySelectorAll('svg path')].map(x=>M[(x.getAttribute('d')||'').slice(0,14)]).filter(Boolean))]:[];
      const imgs=[...c.querySelectorAll('img')].filter(i=>(i.naturalWidth||i.width)>=120).length;
      const vids=c.querySelectorAll('video').length + (t.includes('trouble playing this video')?1:0);
      const lines=t.split('\n').map(x=>x.trim()).filter(x=>x&&x!=='​');
      const ctas=lines.filter(x=>/^(Shop now|Learn more|Order now|Buy now|Sign up|Send message|Send WhatsApp message|WhatsApp|Get offer|Book now|Contact us|Download|See menu|Subscribe|Watch more|Apply now|Get quote|Call now|Install now|Get directions|Shop Now|Learn More|Order Now|Buy Now|Sign Up|Send Message|Get Offer|Book Now|Contact Us|Watch More|See Menu)$/i.test(x));
      const doms=lines.filter(x=>/^[A-Z0-9.-]+\.(IN|COM|CO|SHOP|STORE|APP|LINK|ME|CO\.IN)(\/.*)?$/.test(x));
      const si=lines.indexOf('Sponsored');
      const body=si>=0?(lines[si+1]||''):'';
      ads.push({id:sp.innerText.replace('Library ID: ',''),start:(t.match(/Started running on ([A-Za-z]{3} \d{1,2}, \d{4})/)||[])[1],
        pl:icons,multi:t.includes('multiple versions'),same:+((t.match(/(\d+) ads use this creative/)||[])[1]||1),
        imgs,vids,cards:(t.match(/\u20b9\s?[\d,]+/g)||[]).length,ctas:[...new Set(ctas.map(x=>x.toLowerCase()))],doms:[...new Set(doms)],
        body:body.slice(0,220),deva:/[\u0900-\u097F]/.test(t),beng:/[\u0980-\u09FF]/.test(t),tamil:/[\u0B80-\u0BFF]/.test(t),hinglish:/\b(hai|aur|ke liye|nahi|apne|karo|kijiye)\b/i.test(body)});
    }
    return {total,ads};
  });
  res[brand]={pid,...r}; console.error(brand,r.total,r.ads.length);
  }catch(e){res[brand]={pid,err:String(e).slice(0,200)};console.error(brand,'ERR',e.message.slice(0,100))}
  await ctx.close();
}
fs.writeFileSync(outFile,JSON.stringify(res));
await b.close();
