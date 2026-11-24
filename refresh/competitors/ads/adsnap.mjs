import { chromium } from 'playwright-core';
import fs from 'fs';
const ids = process.argv.slice(3); const shotDir=process.argv[2];
const b = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',args:['--no-sandbox']});
const p = await b.newPage({viewport:{width:1100,height:1400},locale:'en-IN'});
const out={};
for (const spec of ids){
  const [id,shot]=spec.split(':');
  try{
  await p.goto('https://www.facebook.com/ads/library/?id='+id,{waitUntil:'domcontentloaded',timeout:45000});
  await p.waitForTimeout(5000);
  const r = await p.evaluate(()=>{
    const dl=[...document.querySelectorAll('[role=dialog]')].find(d=>d.innerText.includes('Library ID'));
    if(!dl) return null;
    const t=dl.innerText;
    const links=[...dl.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>h.includes('l.facebook.com')||!h.includes('facebook.com')).map(h=>{try{const u=new URL(h);return u.searchParams.get('u')||h}catch(e){return h}});
    const vids=dl.querySelectorAll('video').length;
    const imgs=[...dl.querySelectorAll('img')].filter(i=>i.naturalWidth>=200||/s600x600|p600x600/.test(i.src)).length;
    return {t:t.slice(0,1500),links:[...new Set(links)].slice(0,3),vids,imgs};
  });
  out[id]=r||{err:'no dialog'};
  if(shot&&r){const dl=p.locator('[role=dialog]').filter({hasText:'Library ID'}).first();
    await dl.screenshot({path:`${shotDir}/${shot}.jpg`,type:'jpeg',quality:45});}
  }catch(e){out[id]={err:String(e).slice(0,200)}}
}
console.log(JSON.stringify(out));
await b.close();
