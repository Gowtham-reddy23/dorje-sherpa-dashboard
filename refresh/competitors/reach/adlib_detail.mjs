// Ad detail dialog text (logged out) incl. EU transparency / political spend+impressions sections
import { chromium } from 'playwright-core';
import fs from 'fs';
const [,,outFile,...ids]=process.argv;
const b = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',args:['--no-sandbox']});
const ctx = await b.newContext({viewport:{width:1200,height:1600},locale:'en-US',extraHTTPHeaders:{'Accept-Language':'en-US,en;q=0.9'}});
await ctx.addCookies([{name:'locale',value:'en_US',domain:'.facebook.com',path:'/'}]);
const p = await ctx.newPage();
const out={};
for(const id of ids){
  try{
    await p.goto('https://www.facebook.com/ads/library/?id='+id,{waitUntil:'domcontentloaded',timeout:45000});
    await p.waitForTimeout(7000);
    // expand transparency sections
    try{ await p.getByText('See ad details',{exact:true}).first().click({timeout:4000}); await p.waitForTimeout(4000);}catch(e){}
    for(const lbl of ['Transparency by location','European Union transparency','EU transparency','European Union','Reach','Beneficiary and payer']){
      const el=p.getByText(lbl,{exact:true}).first();
      try{ if(await el.count()) { await el.click({timeout:2000}); await p.waitForTimeout(1200);} }catch(e){}
    }
    const t=await p.evaluate(()=>{const ds=[...document.querySelectorAll('[role=dialog]')].map(d=>d.innerText);return ds.join('\n#####\n')||document.body.innerText.slice(0,4000)});
    out[id]=t.slice(0,9000);
  }catch(e){out[id]='ERR '+String(e).slice(0,150)}
}
fs.writeFileSync(outFile,JSON.stringify(out));
await b.close();
