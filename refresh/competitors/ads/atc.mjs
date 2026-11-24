import { chromium } from 'playwright-core';
const doms = process.argv.slice(2);
const b = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',args:['--no-sandbox']});
const p = await b.newPage({viewport:{width:1280,height:1200},locale:'en-IN'});
const out={};
for (const d of doms){
  try{
    await p.goto(`https://adstransparency.google.com/?region=IN&domain=${d}&preset-date=Last+30+days`,{waitUntil:'domcontentloaded',timeout:45000});
    await p.waitForTimeout(9000);
    const t=(await p.evaluate(()=>document.body.innerText)).replace(/\s+/g,' ');
    const n=await p.evaluate(()=>document.querySelectorAll('creative-preview, priority-creative-grid creative-preview, .creative-preview').length);
    const m=t.match(/(\d[\d,]*|No) ads? /); const adv=[...new Set((t.match(/arrow_drop_down ([^]*?) See all ads|arrow_drop_down All formats arrow_drop_down (.*?) (?:See all ads|Discover more)/)||['',''])[0].split(' Verified').map(s=>s.replace(/.*arrow_drop_down /,'').trim()).filter(Boolean))]; out[d]={n:m?m[1]:null,adv:adv.slice(0,3),t:t.slice(250,520)};
  }catch(e){out[d]={err:String(e).slice(0,150)}}
  console.log(d, JSON.stringify(out[d]));
}
await b.close();
