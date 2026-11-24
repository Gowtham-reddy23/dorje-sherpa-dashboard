import { chromium } from 'playwright-core';
const qs = process.argv.slice(2);
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true, args: ['--disable-blink-features=AutomationControlled'] });
const c = await b.newContext({ locale: 'en-IN', userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36' });
const p = await c.newPage(); const out = {};
for (const q of qs) {
  await p.goto('https://www.amazon.in/s?k=' + encodeURIComponent(q), { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2500);
  const r = await p.evaluate(() => [...document.querySelectorAll('[data-component-type="s-search-result"]')].slice(0, 16).map(e => ({
    t: [...e.querySelectorAll('h2')].map(h=>h.innerText).join(' | ').slice(0, 110), brand: (e.querySelector('h2')?.closest('[data-cy="title-recipe"]')?.querySelector('.a-row .a-size-base-plus, .a-size-mini span')?.innerText || ''),
    sp: !!e.querySelector('.puis-sponsored-label-text, .s-sponsored-label-text'),
    stars: (e.querySelector('[aria-label*="out of 5"]')?.getAttribute('aria-label') || '').slice(0, 30),
    n: (e.querySelector('[aria-label*="ratings"], a[href*="customerReviews"] span')?.innerText || e.querySelector('[aria-label*="ratings"]')?.getAttribute('aria-label') || ''),
    price: e.querySelector('.a-price .a-offscreen')?.innerText || '', mrp: e.querySelector('.a-price.a-text-price .a-offscreen')?.innerText || '', deal: (e.innerText.match(/Limited time deal|Deal of the Day|Lightning Deal|Great Indian Festival|Black Friday[^\n]{0,20}|Prime Day/i)||[''])[0], coupon: (e.innerText.match(/(Save|Apply) [^\n]{0,30}coupon[^\n]{0,10}|[0-9]+% off coupon|₹ ?[0-9]+ off coupon/i)||[''])[0], offx: (e.innerText.match(/\([0-9]+% off\)/)||[''])[0], asin: e.getAttribute('data-asin') })));
  out[q] = r; console.log('##', q, r.length, (await p.title()).slice(0, 60)); r.forEach(x => console.log(JSON.stringify(x)));
  await p.waitForTimeout(3000);
}
(await import('fs')).writeFileSync((process.env.SHOT_DIR || '/tmp/dorje-shot') + '/amzdeals.json', JSON.stringify(out)); await b.close();
