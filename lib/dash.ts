import type { Zoko } from "./zoko"

export type Daily = [string, ...number[]]
export type Campaign = {
  name: string; type: string; status: string; spend: number; purchases: number; value: number
  roas: number; cpa: number | null; cpm: number; ctr: number; freq: number; impressions: number; flags: string[]
}
export type Decision = { n: string; ask: string; why: string; impact: string; rec: string; tone?: string; owner: string; status: string }
export type Dash = {
  updated: string; endDate: string; keys: string[]; daily: Daily[]
  aov: { first: number; repeat: number; firstOrders: number; repeatOrders: number }
  products12m: [string, number, number][]; top30: [string, number, number][]; mix: [string, number][]
  campaigns: Record<string, Campaign[]>
  retention: {
    heat: { cohort: string; size: number; cells: (number | null)[] }[]
    cohorts: { cohort: string; new: number; orders: number; spend: number }[]
    segments: { seg: string; customers: number; spend: number; days: number; orders: number }[]
    buyers: number; ltv: number; ordersPerBuyer: number; subs30: [string, string, number, number][]
  }
  abandoned: { n: number; value: number; recovered: number; prior: number; withContact: number; daily: [string, number, number][]; top: [string, number, number][]; window: string }
  inventory: { oos: [string, string, number, number, number][]; priceErrors: { product: string; variant: string; price: number; compareAt: number; issue: string; available: boolean }[]; activeProducts: number; variants: number }
  seo: {
    score: number; geo: number
    site: { sitemap_ok: boolean; robots_has_sitemap: boolean; ai_bots_blocked: string[]; llms_txt: boolean; llms_has_brand_facts: boolean }
    pages: { path: string; score: number; title: string; titleLen: number; descLen: number; h1: number; h1Empty: boolean; schema: string[]; imgs: number; noAlt: number; kb: number; scripts: number }[]
    fixes: string[][]
  }
  alerts: { lead: string; title: string; detail: string; status: { label: string; tone?: string } }[]
  decisions: Decision[]
  plan: Record<string, { title: string; items: string[] }[]>
  verdict: string; working: string[]; notWorking: string[]; amazonPublic: string; notConnected: string[]
  zoko?: Zoko
  comp?: any
}

type Blob = { s: string; i: string; c: string; n: number }
const b64 = (s: string) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0))

export async function decrypt(blob: Blob, passcode: string): Promise<Dash> {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(passcode), "PBKDF2", false, ["deriveKey"])
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: b64(blob.s), iterations: blob.n, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["decrypt"])
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(blob.i) }, key, b64(blob.c))
  return JSON.parse(new TextDecoder().decode(pt))
}

export const inr = (x: number, digits = 0) => {
  const a = Math.abs(x)
  if (a >= 1e7) return `₹${(x / 1e7).toFixed(2)} Cr`
  if (a >= 1e5) return `₹${(x / 1e5).toFixed(2)}L`
  return `₹${x.toLocaleString("en-IN", { maximumFractionDigits: digits })}`
}
export const num = (x: number) => Math.round(x).toLocaleString("en-IN")
export const pct = (x: number, d = 1) => `${x.toFixed(d)}%`

export type Totals = {
  rev: number; tot: number; ord: number; new: number; ret: number; ses: number; atc: number; chk: number; done: number
  spend: number; mp: number; mv: number; days: number; metaDays: number
}
export function sumRange(d: Dash, from: number, to: number): Totals {
  const t: Totals = { rev: 0, tot: 0, ord: 0, new: 0, ret: 0, ses: 0, atc: 0, chk: 0, done: 0, spend: 0, mp: 0, mv: 0, days: 0, metaDays: 0 }
  const ks = d.keys as (keyof Totals)[]
  for (let i = Math.max(0, from); i < Math.min(d.daily.length, to); i++) {
    const row = d.daily[i]
    ks.forEach((k, j) => { (t[k] as number) += Number(row[j + 1]) || 0 })
    t.days++
    if (Number(row[10]) > 0) t.metaDays++
  }
  return t
}
export function windows(d: Dash, range: number) {
  const n = d.daily.length
  return { cur: sumRange(d, n - range, n), prev: sumRange(d, n - 2 * range, n - range), hasPrev: n - 2 * range >= 0 }
}
export const derived = (t: Totals) => ({
  aov: t.ord ? t.rev / t.ord : 0,
  cvr: t.ses ? (t.done / t.ses) * 100 : 0,
  repeat: t.new + t.ret ? (t.ret / (t.new + t.ret)) * 100 : 0,
  cac: t.new ? t.spend / t.new : 0,
  mer: t.spend ? t.tot / t.spend : 0,
  roas: t.spend ? t.mv / t.spend : 0,
  cpa: t.mp ? t.spend / t.mp : 0,
})
export const change = (a: number, b: number) => (b ? ((a - b) / b) * 100 : null)

export function series(d: Dash, range: number) {
  const n = d.daily.length
  const rows = d.daily.slice(Math.max(0, n - range))
  const bucket = range <= 30 ? "day" : range <= 90 ? "week" : "month"
  const out: Record<string, Record<string, number | string>> = {}
  const order: string[] = []
  rows.forEach((r, idx) => {
    const date = new Date(r[0] + "T00:00:00")
    let key: string, label: string
    if (bucket === "day") { key = r[0]; label = date.toLocaleDateString("en-IN", { day: "numeric", month: "short" }) }
    else if (bucket === "week") { const w = Math.floor(idx / 7); key = "w" + w; label = date.toLocaleDateString("en-IN", { day: "numeric", month: "short" }) }
    else { key = r[0].slice(0, 7); label = date.toLocaleDateString("en-IN", { month: "short", year: "2-digit" }) }
    if (!out[key]) { out[key] = { label, n: 0, rev: 0, ord: 0, new: 0, ret: 0, ses: 0, spend: 0, mv: 0, mp: 0, done: 0 }; order.push(key) }
    const o = out[key]
    ;(o.n as number) += 1
    const k = d.keys
    const g = (name: string) => Number(r[k.indexOf(name) + 1]) || 0
    for (const f of ["rev", "ord", "new", "ret", "ses", "spend", "mv", "mp", "done"]) (o[f] as number) += g(f)
  })
  return {
    bucket,
    data: order.filter((k) => bucket !== "month" || (out[k].n as number) >= 20).map((k) => {
      const o = out[k] as Record<string, number> & { label: string }
      return { ...o, rev: Math.round(o.rev), spend: Math.round(o.spend), mv: Math.round(o.mv), aov: o.ord ? Math.round(o.rev / o.ord) : 0, cac: o.new ? Math.round(o.spend / o.new) : 0, roas: o.spend ? +(o.mv / o.spend).toFixed(2) : 0 }
    }),
  }
}

export const HELP: Record<string, string> = {
  revenue: "Net sales: what customers paid for products after discounts and returns, before shipping and tax.",
  orders: "Number of website orders placed.",
  aov: "Average order value: revenue divided by orders. How much a typical order is worth.",
  sessions: "Visits to the website. One person can make several visits.",
  cvr: "Conversion rate: share of website visits that ended in a completed order.",
  new: "People who ordered for the first time in this period.",
  ret: "People who had ordered before and ordered again in this period.",
  repeat: "Share of this period's buyers who are returning customers.",
  spend: "Money spent on Meta ads (Instagram + Facebook). Google Ads is not connected yet.",
  cac: "Cost per new customer (CAC): ad spend divided by new customers. Lower is better.",
  mer: "Blended return: total website sales for every ₹1 of ad spend. Counts all sales, not only ad-driven ones.",
  roas: "ROAS (return on ad spend): sales Meta says its ads caused, for every ₹1 spent. Meta tends to over-count.",
  cpa: "Cost per purchase as reported by Meta: ad spend divided by purchases Meta credits to its ads.",
  freq: "Frequency: how many times the average person saw the ads. Above 4 usually means people are tired of them.",
  firstAov: "Average value of a customer's first order. If cost per new customer is higher, the first order loses money.",
  ltv: "Lifetime value: total spent so far by the average customer across all their orders.",
  abandoned: "Checkouts where the customer entered contact details but did not pay.",
  recovery: "Share of unfinished checkouts that were later completed.",
  heat: "Of the customers who first bought in a month, the share who bought again N months later.",
  seo: "Basic search-engine checks on key pages: title, description, one heading, structured data, image text.",
  geo: "How ready the site is to be read and quoted by AI tools like ChatGPT, Perplexity and Google AI answers.",
}
