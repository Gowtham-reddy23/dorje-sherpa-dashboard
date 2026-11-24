// Weekly: render each competitor homepage in headless Chrome (wait ~10 s so popups fire) and record the
// announcement bar, any popup/modal text, coupon codes and % offers seen, and offer/loyalty/capture apps.
// Usage: NODE_PATH=<folder with playwright-core installed> node competitors/scan_offers.mjs  -> competitors/offers_scan.json
import { chromium } from 'playwright-core';
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const H = path.dirname(fileURLToPath(import.meta.url));
const SITES = {dorje:'https://dorjeteas.com',vahdam:'https://www.vahdam.in',teabox:'https://in.teabox.com',tcotw:'https://www.teacultureoftheworld.com',
 sancha:'https://www.sanchatea.com',goldentips:'https://www.goldentipstea.in',goodricke:'https://goodricketea.in',udyan:'https://udyantea.com',
 makaibari:'https://makaibari.in',organicindia:'https://organicindia.com',kaahu:'https://kaahuteas.com',mittal:'https://www.mittalteas.com',
 happyvalley:'https://happyvalleyorganictea.com',jayshree:'https://jayshreetea.com'};
const APPS = {'Spin wheel':/wheelio|spin.?(the|to|a).?wheel|spin-wheel|spinwheel/i,'Klaviyo popup':/klaviyo/i,'Privy':/privy\.com/i,'Poptin':/poptin/i,
 'Omnisend':/omnisend/i,'GoKwik':/gokwik/i,'Shopflo':/shopflo/i,'Razorpay Magic':/magic-checkout|magic\.razorpay/i,'Smile.io loyalty':/smile\.io|smile-ui/i,
 'Growave loyalty':/growave/i,'Nector loyalty':/nector/i,'Flits':/getflits|flits/i,'Rivo loyalty':/rivo\.io|rivo-/i,'BON loyalty':/bonloyalty|bon-loyalty/i,
 'Recharge/Appstle subs':/rechargecdn|rechargepayments|appstle/i,'WhatsApp widget':/wa\.me\/|api\.whatsapp\.com|whatsapp/i,'Zoko':/zoko/i,'Interakt':/interakt/i,
 'Gallabox':/gallabox/i,'Wati':/wati\.io/i,'Bik':/bik\.ai/i,'Judge.me':/judge\.me/i};
const out = {checked: new Date().toLocaleString('en-GB',{timeZone:'Asia/Kolkata',dateStyle:'medium',timeStyle:'short'})+' IST', sites:{}};
const b = await chromium.launch({executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',args:['--no-sandbox']});
for (const [k,url] of Object.entries(SITES)) {
  const ctx = await b.newContext({viewport:{width:1280,height:900},locale:'en-IN',timezoneId:'Asia/Kolkata',userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'});
  const p = await ctx.newPage();
  try {
    await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000}); await p.waitForTimeout(11000);
    await p.mouse.move(600,10); await p.waitForTimeout(1500); // exit-intent style trigger
    const r = await p.evaluate(()=>{
      const vis=e=>{const s=getComputedStyle(e),rc=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&+s.opacity>0.05&&rc.width>200&&rc.height>80};
      const pops=[...document.querySelectorAll('[role=dialog],[aria-modal=true],[class*=popup i],[class*=modal i],[id*=popup i],[class*=klaviyo-form i],iframe[title*=popup i]')]
        .filter(vis).map(e=>e.innerText.replace(/\s+/g,' ').trim()).filter(t=>t.length>15).slice(0,4);
      const top=[...document.querySelectorAll('[class*=announcement i],[id*=announcement i],[class*=marquee i],[class*=topbar i],[class*=top-bar i],[class*=promo-bar i]')]
        .map(e=>e.innerText.replace(/\s+/g,' ').trim()).filter(Boolean);
      const body=document.body.innerText.replace(/\s+/g,' ');
      return {top:[...new Set(top)].join(' | ').slice(0,400),pops:pops.map(t=>t.slice(0,300)),head:body.slice(0,300),body:body.slice(0,20000),html:document.documentElement.outerHTML.slice(0,900000)};
    });
    const t = r.body;
    const codes=[...new Set([...t.matchAll(/(?:code|coupon|use)\s*[:\-]?\s*["'“]?([A-Z][A-Z0-9]{3,14})\b/g)].map(m=>m[1]))].slice(0,8);
    const offers=[...new Set([...t.matchAll(/[^.|!]{0,50}(?:\d{1,2}\s?% ?off|flat ₹ ?\d+|buy \d+ get \d+|bogo|free (?:gift|sample|shipping|delivery)[^.|!]{0,40}|first order|sign ?up|subscribe and save|loyalty|reward points?|cashback)[^.|!]{0,50}/gi)].map(m=>m[0].trim()))].slice(0,10);
    out.sites[k]={url,top:r.top,head:r.head,popups:r.pops,codes,offers:offers.map(s=>s.slice(0,140)),apps:Object.entries(APPS).filter(([a,re])=>re.test(r.html)).map(([a])=>a)};
  } catch(e){ out.sites[k]={url,err:String(e).slice(0,160)}; }
  console.log(k, JSON.stringify(out.sites[k]).slice(0,900));
  await ctx.close();
}
await b.close();
fs.writeFileSync(path.join(H,'offers_scan.json'),JSON.stringify(out));
