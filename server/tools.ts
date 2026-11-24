import { tool } from "ai"
import { z } from "zod"
import { change, derived, inr, num, pct, series, windows, type Dash } from "../lib/dash"
import { bits, dateWindow, EMPTY, getAttr, groupBy, metaReported, monthWindow, R, select, type AttrRow } from "../lib/attr"
import type { ToolOut, View } from "../lib/ask-types"

/* eslint-disable @typescript-eslint/no-explicit-any */
const r0 = (x: number) => Math.round(x)
const r1 = (x: number) => Math.round(x * 10) / 10
const r2 = (x: number) => Math.round(x * 100) / 100
const chg = (a: number, b: number) => { const c = change(a, b); return c === null ? null : r1(c) }
const RANGE = z.enum(["7", "30", "90", "365"]).optional().describe("Days: 7, 30, 90 or 365 complete days ending on the data end date (default 30)")
const label = (r: number) => (r === 365 ? "last 12 months" : `last ${r} days`)
const fmtDate = (iso: string) => new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })

/** Keep `view` for the UI only; the model gets the compact facts. */
const toModel = ({ output }: { output: ToolOut }) => {
  const { view: _v, ...rest } = output
  void _v
  return { type: "json" as const, value: rest as any }
}

function attrWin(d: Dash, range: number) {
  const a = getAttr(d)
  if (!a) return null
  const w = dateWindow(d.endDate, range)
  return { a, w, cur: select(a, w.from, w.to, EMPTY), prev: select(a, w.pFrom, w.pTo, EMPTY), hasPrev: w.pFrom >= (a.rows[0]?.[R.date] as string) }
}

export function makeTools(d: Dash) {
  const asOf = d.updated
  const period = (range: number) => {
    const w = dateWindow(d.endDate, range)
    return `${label(range)}: ${fmtDate(w.from)} – ${fmtDate(w.to)} (compared with ${fmtDate(w.pFrom)} – ${fmtDate(w.pTo)})`
  }
  const ab = (d as any).abDeep, zk = d.zoko as any, comp = d.comp as any

  return {
    getDataStatus: tool({
      description: "Which data sources are connected, how fresh each one is, and what is NOT connected (Google Ads, Amazon). Call when the user asks about data coverage, or before saying something isn't available.",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => ({
        source: "Dashboard build metadata", asOf,
        data: {
          dashboardRefreshed: d.updated, dataThrough: d.endDate, refreshEvery: "about 6 hours (automatic refresh + redeploy)",
          connected: {
            shopify: "orders, sessions, products, inventory, abandoned checkouts (read-only)",
            meta: "Meta Ads API: spend, purchases, campaigns, formats, placements (read-only)",
            zoko: `WhatsApp templates, contacts, message sample (read-only), as of ${zk?.asOf ?? "n/a"}`,
            seoGeo: "public crawl of dorjeteas.com + Google/AI answer checks",
            competitors: `public prices, offers and ad libraries, checked ${comp?.checked ?? "n/a"} (weekly)`,
          },
          notConnected: d.notConnected,
          amazonPublicOnly: d.amazonPublic,
        },
      }),
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getKpis: tool({
      description: "Headline business numbers for a period vs the period before: revenue, orders, average order, visits, conversion, new/returning customers, Meta spend, cost per new customer, sales per ₹1 of ads (MER), Meta ROAS, unfinished checkouts. Same numbers as the dashboard Overview.",
      inputSchema: z.object({ range: RANGE }),
      execute: async ({ range = "30" }): Promise<ToolOut> => {
        const n = Number(range)
        const { cur, prev, hasPrev } = windows(d, n)
        const a = derived(cur), b = derived(prev)
        const c = (x: number, y: number) => (hasPrev ? chg(x, y) : null)
        const metaPartial = prev.metaDays < n * 0.9
        const s = series(d, n)
        const data = {
          revenue: r0(cur.rev), revenuePrev: r0(prev.rev), revenueChangePct: c(cur.rev, prev.rev),
          orders: cur.ord, ordersPrev: prev.ord, ordersChangePct: c(cur.ord, prev.ord),
          avgOrder: r0(a.aov), avgOrderPrev: r0(b.aov),
          visits: cur.ses, visitsPrev: prev.ses, conversionPct: r2(a.cvr), conversionPrevPct: r2(b.cvr),
          newCustomers: cur.new, newCustomersPrev: prev.new, returningCustomers: cur.ret, returningCustomersPrev: prev.ret, repeatSharePct: r1(a.repeat),
          metaSpend: r0(cur.spend), metaSpendPrev: r0(prev.spend), costPerNewCustomer: r0(a.cac), costPerNewCustomerPrev: r0(b.cac),
          salesPerRupeeOfAds_MER: r2(a.mer), merPrev: r2(b.mer), metaRoas_metaReported: r2(a.roas), metaRoasPrev: r2(b.roas),
          metaPurchases_metaReported: cur.mp, firstOrderAvg12m: d.aov.first, repeatOrderAvg12m: d.aov.repeat,
          unfinishedCheckouts30d: { count: d.abandoned.n, value: d.abandoned.value, recovered: d.abandoned.recovered, window: d.abandoned.window },
          earlierPeriodHasPartialMetaHistory: metaPartial,
          verdict: d.verdict,
        }
        const view: View = {
          title: `Headline numbers, ${label(n)}`,
          kpis: [
            { label: "Revenue", value: inr(cur.rev), delta: c(cur.rev, prev.rev) },
            { label: "Orders", value: num(cur.ord), delta: c(cur.ord, prev.ord) },
            { label: "Average order", value: inr(a.aov), delta: c(a.aov, b.aov) },
            { label: "New customers", value: num(cur.new), delta: c(cur.new, prev.new) },
            { label: "Meta spend", value: inr(cur.spend), delta: c(cur.spend, prev.spend), goodUp: false },
            { label: "Cost per new customer", value: inr(a.cac), delta: metaPartial ? null : c(a.cac, b.cac), goodUp: false },
            { label: "Meta ROAS", value: `₹${a.roas.toFixed(2)}`, delta: metaPartial ? null : c(a.roas, b.roas), sub: "Meta's own count" },
            { label: "Visits that buy", value: pct(a.cvr, 2), delta: c(a.cvr, b.cvr) },
          ],
          chart: { kind: "line", title: `Revenue and Meta spend by ${s.bucket}`, x: "label", format: "inr", series: [{ key: "rev", label: "Revenue" }, { key: "spend", label: "Meta spend" }], data: s.data.map((x: any) => ({ label: x.label, rev: x.rev, spend: x.spend })) },
        }
        return { source: "Shopify orders & sessions + Meta Ads API (daily series)", asOf, period: period(n), data, view, notes: ["Meta ROAS uses Meta's own attribution and tends to over-count.", "Revenue = Shopify net sales by order date (IST)."] }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getRevenue: tool({
      description: "Revenue broken down. breakdown='trend' gives revenue/orders/new/returning over time; 'channel' (last- or first-visit credit), 'campaign' (Meta campaign from UTMs), 'productGroup', 'packSize', 'state', 'payment', 'customerType', 'salesChannel' slice Shopify orders for the period and compare with the period before; 'topProducts' lists best sellers (fixed: last 30 days and last 12 months); 'productMix' is the 12-month product-group mix.",
      inputSchema: z.object({
        breakdown: z.enum(["trend", "channel", "campaign", "productGroup", "packSize", "state", "payment", "customerType", "salesChannel", "topProducts", "productMix"]),
        range: RANGE,
        credit: z.enum(["last", "first"]).optional().describe("Channel credit model: last visit (default) or first visit"),
        limit: z.number().int().min(3).max(20).optional().describe("Rows to return (default 10)"),
      }),
      execute: async ({ breakdown, range = "30", credit = "last", limit = 10 }): Promise<ToolOut> => {
        const n = Number(range)
        if (breakdown === "trend") {
          const s = series(d, n)
          const data = s.data.map((x: any) => ({ label: x.label, rev: x.rev, ord: x.ord, new: x.new, ret: x.ret, aov: x.aov, spend: x.spend, roas: x.roas }))
          return { source: "Shopify orders (daily series) + Meta spend", asOf, period: period(n), data: { bucket: s.bucket, points: data },
            view: { chart: { kind: "bar", title: `Revenue by ${s.bucket}, ${label(n)}`, x: "label", format: "inr", series: [{ key: "rev", label: "Revenue" }], data } } }
        }
        if (breakdown === "topProducts") {
          const t30 = d.top30.map(([p, rev, o]) => ({ product: p, revenue: rev, orders: o }))
          const t12 = d.products12m.slice(0, limit).map(([p, rev, o]) => ({ product: p, revenue: rev, orders: o }))
          return { source: "Shopify orders (line items)", asOf, period: "fixed: last 30 days and last 12 months", data: { last30: t30, last12m: t12 },
            view: { table: { title: "Top products, last 30 days", columns: [{ key: "product", label: "Product" }, { key: "revenue", label: "Revenue", format: "inr" }, { key: "orders", label: "Orders", format: "num" }], rows: t30 } } }
        }
        if (breakdown === "productMix") {
          const tot = d.mix.reduce((a, m) => a + m[1], 0)
          const rows = d.mix.map(([g, v]) => ({ group: g, revenue: v, sharePct: r1((v / tot) * 100) }))
          return { source: "Shopify orders (line items, grouped by product name)", asOf, period: "last 12 months", data: rows,
            view: { chart: { kind: "bar", title: "Product mix, last 12 months", x: "group", format: "inr", series: [{ key: "revenue", label: "Revenue" }], data: rows } } }
        }
        const w = attrWin(d, n)
        if (!w) return { source: "Shopify orders", asOf, error: "Order-level data not loaded" }
        const { a } = w
        const key = (r: AttrRow): number | number[] =>
          breakdown === "channel" ? r[credit === "last" ? R.last : R.first]
          : breakdown === "campaign" ? r[R.campLast]
          : breakdown === "productGroup" ? bits(r[R.grp])
          : breakdown === "packSize" ? bits(r[R.pack])
          : breakdown === "state" ? r[R.state]
          : breakdown === "payment" ? r[R.pay]
          : breakdown === "salesChannel" ? r[R.sales]
          : r[R.new] === 1 ? 1 : r[R.new] === 0 ? 0 : 2
        const dimName = { channel: "ch", campaign: "camp", productGroup: "grp", packSize: "pack", state: "state", payment: "pay", salesChannel: "sales" }[breakdown as string]
        const lab = (i: number) => breakdown === "customerType" ? ["Returning", "New", "Unknown"][i] : (a.dims as any)[dimName!][i]
        const cur = groupBy(w.cur, key, lab), prev = groupBy(w.prev, key, lab)
        const total = w.cur.reduce((s, r) => s + r[R.rev], 0)
        const rows = cur.slice(0, limit).map((x) => {
          const p = prev.find((y) => y.key === x.key)
          return { name: x.name, revenue: r0(x.rev), sharePct: r1((x.rev / total) * 100), orders: x.orders, avgOrder: r0(x.aov), newCustomerPct: r1(x.newPct), revenuePrev: p ? r0(p.rev) : null, changePct: p && w.hasPrev ? chg(x.rev, p.rev) : null }
        })
        return {
          source: "Shopify orders (order-level attribution rows: UTMs, first/last visit, line items)", asOf, period: period(n),
          data: { totalRevenue: r0(total), orders: w.cur.length, rows, credit: breakdown === "channel" ? credit : undefined, previousPeriodComplete: w.hasPrev },
          notes: ["Order-level data covers the last 12 months only, so 365-day comparisons have no previous period.", breakdown === "campaign" ? "Campaign = Meta campaign found in the order's last-visit UTMs (Shopify-traced, not Meta's own count)." : ""].filter(Boolean),
          view: {
            chart: { kind: "bar", title: `Revenue by ${breakdown}, ${label(n)}`, x: "name", format: "inr", series: [{ key: "revenue", label: label(n) }, ...(w.hasPrev ? [{ key: "revenuePrev", label: "period before" }] : [])], data: rows.slice(0, 8) },
            table: { columns: [{ key: "name", label: "Slice" }, { key: "revenue", label: "Revenue", format: "inr" }, { key: "sharePct", label: "Share", format: "pct" }, { key: "orders", label: "Orders", format: "num" }, { key: "changePct", label: "Change", format: "pct" }], rows },
          },
        }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getMetaAds: tool({
      description: "Dorje's own Meta ads. view='campaigns' (per campaign: spend, purchases, ROAS, cost per purchase, CPM, CTR, frequency, flags like 'No buyer exclusion'; any range); 'formats' (video vs image vs flexible), 'placements' (Facebook feed, Instagram Reels, WhatsApp, Audience Network…), 'platforms', 'summary' (reach, impressions, frequency, CPM, CTR) — these four are last 30 days only.",
      inputSchema: z.object({ view: z.enum(["campaigns", "formats", "placements", "platforms", "summary"]), range: RANGE }),
      execute: async ({ view, range = "30" }): Promise<ToolOut> => {
        const own = comp?.atr?.own
        if (view === "campaigns") {
          const rows = (d.campaigns[range] || []).map((c) => ({ name: c.name, type: c.type, status: c.status, spend: c.spend, purchases: c.purchases, value: c.value, roas: c.roas, costPerPurchase: c.cpa, cpm: c.cpm, ctrPct: c.ctr, frequency: c.freq, impressions: c.impressions, flags: c.flags.join("; ") }))
          return { source: "Meta Ads API (campaign insights, Meta-reported purchases)", asOf, period: period(Number(range)), data: rows,
            notes: ["Purchases/ROAS are Meta's own attribution (7-day click / 1-day view) and over-count vs Shopify; use getAttribution to compare."],
            view: { chart: { kind: "bar", title: "ROAS by campaign", x: "name", format: "x", series: [{ key: "roas", label: "ROAS" }], data: rows.map((r) => ({ name: r.name.replace(/\s*\|.*$/, ""), roas: r.roas })) },
              table: { columns: [{ key: "name", label: "Campaign" }, { key: "spend", label: "Spend", format: "inr" }, { key: "purchases", label: "Purchases", format: "num" }, { key: "roas", label: "ROAS", format: "x" }, { key: "costPerPurchase", label: "Cost / purchase", format: "inr" }, { key: "frequency", label: "Freq.", format: "x" }, { key: "flags", label: "Flags" }], rows } } }
        }
        if (!own) return { source: "Meta Ads API", asOf, error: "Format/placement breakdown not loaded" }
        if (view === "summary") {
          const t = own.total
          const data = { spend: r0(t.amount_spent), impressions: t.impressions, reach: t.reach, frequency: r2(t.frequency), cpm: r0(t.cpm), ctrPct: t.ctr, linkClicks: t.link_click, costPerLinkClick: r2(t.cost_per_link_click), roas: r2(t.purchase_roas), purchases: t.omni_purchase, purchaseValue: r0(t.omni_purchase_values), adsWithSpend: own.adsWithSpend }
          return { source: "Meta Ads API (account insights)", asOf: comp.atr.checked, period: own.period, data,
            view: { kpis: [{ label: "Spend", value: inr(data.spend) }, { label: "Impressions", value: num(data.impressions) }, { label: "Reach", value: num(data.reach) }, { label: "Frequency", value: data.frequency.toFixed(1) }, { label: "Cost per 1,000 views", value: inr(data.cpm) }, { label: "Click rate", value: pct(data.ctrPct, 2) }, { label: "Purchases (Meta)", value: num(data.purchases) }, { label: "ROAS (Meta)", value: `₹${data.roas.toFixed(2)}` }] } }
        }
        const src = view === "formats" ? own.byFormat : view === "placements" ? own.byPosition : own.byPlatform
        const rows = src.map((x: any) => ({ name: x.k, spend: x.spend, impressions: x.impr, cpm: x.cpm, ctrPct: x.ctr, purchases: x.purch, roas: x.roas, frequency: x.freq ?? null, sharePct: x.share ?? null }))
        return { source: "Meta Ads API (ad-level insights with breakdowns)", asOf: comp.atr.checked, period: own.period, data: rows, notes: comp.atr.takeaways?.slice(0, 3),
          view: { chart: { kind: "bar", title: `ROAS by ${view.replace(/s$/, "")}`, x: "name", format: "x", series: [{ key: "roas", label: "ROAS" }], data: rows.slice(0, 10) },
            table: { columns: [{ key: "name", label: view === "formats" ? "Format" : view === "placements" ? "Placement" : "Platform" }, { key: "spend", label: "Spend", format: "inr" }, { key: "cpm", label: "CPM", format: "inr" }, { key: "ctrPct", label: "CTR", format: "pct" }, { key: "purchases", label: "Purchases", format: "num" }, { key: "roas", label: "ROAS", format: "x" }], rows } } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getAttribution: tool({
      description: "Which channels drive revenue (last-visit vs first-visit credit), and Meta-claimed purchases vs purchases Shopify can trace to each Meta campaign (month-aligned). Use for 'is Meta really working', channel credit, over-counting.",
      inputSchema: z.object({ range: RANGE }),
      execute: async ({ range = "30" }): Promise<ToolOut> => {
        const n = Number(range)
        const w = attrWin(d, n)
        if (!w) return { source: "Shopify orders", asOf, error: "Order-level data not loaded" }
        const { a } = w
        const lastBy = groupBy(w.cur, (r) => r[R.last], (i) => a.dims.ch[i]), firstBy = groupBy(w.cur, (r) => r[R.first], (i) => a.dims.ch[i])
        const total = w.cur.reduce((s, r) => s + r[R.rev], 0)
        const channels = lastBy.slice(0, 10).map((l) => { const f = firstBy.find((x) => x.key === l.key); return { channel: l.name, lastVisitRevenue: r0(l.rev), sharePct: r1((l.rev / total) * 100), firstVisitRevenue: r0(f?.rev ?? 0), orders: l.orders, newCustomerPct: r1(l.newPct) } })
        const mw = monthWindow(a, d.endDate, n)
        const mrows = select(a, mw.from, mw.to, EMPTY)
        const mShop = groupBy(mrows, (r) => r[R.campLast], (i) => a.dims.camp[i])
        const mRep = metaReported(a, mw.from, mw.to)
        const names = new Set([...mShop.map((x) => x.name), ...mRep.keys()])
        const meta = [...names].map((nm) => { const s = mShop.find((x) => x.name === nm); const m = mRep.get(nm); return { campaign: nm, spend: r0(m?.spend ?? 0), metaPurchases: m?.purchases ?? 0, shopifyTracedOrders: s?.orders ?? 0, shopifyTracedRevenue: r0(s?.rev ?? 0), metaValue: r0(m?.value ?? 0) } }).filter((r) => r.spend > 0 || r.shopifyTracedOrders > 0).sort((x, y) => y.spend - x.spend)
        const tM = meta.reduce((s, r) => s + r.metaPurchases, 0), tS = meta.reduce((s, r) => s + r.shopifyTracedOrders, 0)
        return {
          source: "Shopify orders (customer journey first/last visit + UTMs) vs Meta Ads API monthly campaign results", asOf, period: `${period(n)}; Meta comparison month-aligned ${mw.from} – ${mw.to}`,
          data: { channels, metaVsShopify: { campaigns: meta.slice(0, 12), metaClaimedPurchases: tM, shopifyTracedOrders: tS, metaOverCountPct: tS ? r1(((tM - tS) / tS) * 100) : null } },
          notes: ["Shopify can only trace orders whose visit carried Meta UTMs; Direct/Unknown hides some Meta-driven orders, so the truth is between the two counts."],
          view: { chart: { kind: "bar", title: "Revenue by channel (last vs first visit)", x: "channel", format: "inr", series: [{ key: "lastVisitRevenue", label: "Last visit" }, { key: "firstVisitRevenue", label: "First visit" }], data: channels.slice(0, 8) },
            table: { title: "Meta-claimed vs Shopify-traced", columns: [{ key: "campaign", label: "Campaign" }, { key: "spend", label: "Spend", format: "inr" }, { key: "metaPurchases", label: "Meta claims", format: "num" }, { key: "shopifyTracedOrders", label: "Shopify traced", format: "num" }], rows: meta.slice(0, 10) } },
        }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getAbandoned: tool({
      description: "Unfinished (abandoned) checkouts deep-dive: count, value, recovery rate, weekly trend, cart→order funnel, which products/price bands/customers abandon, WhatsApp (Zoko) reminder delivery/failure, ranked fixes with estimated ₹ upside.",
      inputSchema: z.object({ window: z.enum(["30", "90"]).optional().describe("Days (default 30)") }),
      execute: async ({ window = "30" }): Promise<ToolOut> => {
        if (!ab) return { source: "Shopify abandoned checkouts", asOf, data: d.abandoned }
        const W = window === "90" ? ab.w90 : ab.w30
        const weeks = ab.weeks.map((x: any) => ({ week: x.w, checkouts: x.n, recovered: x.rec, recoveryPct: x.recPct, value: x.value, cartToOrderPct: x.cartToOrder, partialWeek: x.partial }))
        const data = {
          window: `${W.since} – ${W.until}`, unfinished: W.n, people: W.people, value: W.value, avgValue: W.avg, medianValue: W.median, recovered: W.rec, recoveryPct: W.recPct, recoveredValue: W.recValue, leftUnpaid: W.lost,
          under399Pct: W.under399Pct, recoveryUnder399Pct: W.under399RecPct, recoveryOver399Pct: W.over399RecPct,
          byCustomer: W.newRet, byProduct: W.products?.slice(0, 6), emailPct: W.emailPct, phonePct: W.phonePct,
          funnelLast30: ab.funnel30, weeks,
          whatsappReminders: ab.zokoFlow ? { checkedAbandoners: ab.zokoFlow.checked, failedPct: ab.zokoFlow.failedPct, seenPct: ab.zokoFlow.seenPct, metaCapError131049: ab.zokoFlow.fail131049, timing: ab.zokoFlow.timing, template: ab.zokoFlow.templates } : null,
          findings: ab.findings.map((f: any) => `${f.title}: ${f.detail}`),
          actions: ab.actions.map((x: any) => ({ n: x.n, who: x.who, what: x.what, impact: x.impact })),
          upsideEstimate: { ...ab.opp, combinedActions1and2: ab.totalEst },
        }
        return { source: "Shopify abandoned checkouts (read-only) + Zoko message statuses (sample)", asOf: ab.asOf, period: `last ${window} days`, data,
          notes: ["₹ upside figures are ESTIMATES (checkouts × rate lift × average value), not forecasts."],
          view: {
            kpis: [{ label: "Unfinished checkouts", value: num(W.n) }, { label: "Value left", value: inr(W.value) }, { label: "Recovered", value: pct(W.recPct, 1), sub: `${W.rec} paid later` }, { label: "WhatsApp reminders failed", value: ab.zokoFlow ? pct(ab.zokoFlow.failedPct, 0) : "—" }],
            chart: { kind: "line", title: "Weekly unfinished checkouts and recovery %", x: "week", format: "num", series: [{ key: "checkouts", label: "Unfinished" }, { key: "recoveryPct", label: "Recovered %" }], data: weeks.slice(-12) },
          } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getRetention: tool({
      description: "Repeat customers and cohorts: buyers, lifetime value, orders per buyer, first vs repeat order value, customer segments (active, at-risk, dormant…), monthly cohort repeat rates, subscriptions sold in 30 days.",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => {
        const rt = d.retention
        const cohorts = rt.heat.map((h) => ({ cohort: h.cohort, size: h.size, month1Pct: h.cells[0], month2Pct: h.cells[1], month3Pct: h.cells[2] }))
        return { source: "Shopify customers & orders (last 24 months)", asOf, period: "cohorts by first-order month, last 13 months",
          data: { buyers12m: rt.buyers, lifetimeValue: rt.ltv, ordersPerBuyer: rt.ordersPerBuyer, firstOrderAvg: d.aov.first, repeatOrderAvg: d.aov.repeat, segments: rt.segments, cohorts, cohortNewVsOrders: rt.cohorts, subscriptions30d: rt.subs30.slice(0, 8) },
          view: { kpis: [{ label: "Buyers (12 months)", value: num(rt.buyers) }, { label: "Lifetime value", value: inr(rt.ltv) }, { label: "Orders per buyer", value: rt.ordersPerBuyer.toFixed(2) }, { label: "Repeat order value", value: inr(d.aov.repeat), sub: `First order ${inr(d.aov.first)}` }],
            table: { title: "Customer segments", columns: [{ key: "seg", label: "Segment" }, { key: "customers", label: "Customers", format: "num" }, { key: "spend", label: "Lifetime spend", format: "inr" }, { key: "orders", label: "Orders", format: "num" }, { key: "days", label: "Days since last order (median)", format: "num" }], rows: rt.segments as any } } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getWhatsApp: tool({
      description: "WhatsApp via Zoko: contacts, % of buyers reachable, repeat rate of contacts who messaged vs not, templates (abandoned-cart, lifecycle), broadcast delivery/failure sample, gaps in Zoko's API.",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => {
        if (!zk) return { source: "Zoko", asOf, error: "Zoko data not loaded" }
        const segs = Object.entries(zk.join.segments).map(([k, v]: any) => ({ segment: k, buyers: v.buyers, revenue: v.revenue, repeatRatePct: v.repeatRate, revenuePerBuyer: v.revPerBuyer }))
        const ms = zk.messageSample
        return { source: "Zoko REST API (read-only GETs) joined to Shopify buyers by phone", asOf: zk.asOf,
          data: { contacts: zk.customers.total, contactsLoaded: zk.customers.fetched, coveragePct: zk.customers.coveragePct, buyersReachablePct: zk.join.reachablePct, revenueFromReachableBuyersPct: zk.join.revenueReachablePct, segments: segs, newContactsPerMonth: zk.customers.newPerMonth, templates: { total: zk.templates.total, abandonedCartTemplates: zk.templates.abandoned.length }, messageSample: ms ? { checked: ms.checked, delivered: ms.delivered, read: ms.read, failed: ms.failed, failReasons: ms.failReasons, abandonedLastSent: ms.abandonedLast, note: ms.note } : null, gaps: zk.gaps },
          notes: ["Zoko's API has no broadcast cost/results or opt-in field; message rates come from a sample.", zk.customers.newPerMonthNote],
          view: { kpis: [{ label: "Zoko contacts", value: num(zk.customers.total) }, { label: "Buyers reachable", value: pct(zk.join.reachablePct, 0) }, ...segs.slice(0, 2).map((s) => ({ label: `Repeat rate: ${s.segment}`, value: pct(s.repeatRatePct, 0) }))],
            table: { columns: [{ key: "segment", label: "Segment" }, { key: "buyers", label: "Buyers", format: "num" }, { key: "revenue", label: "Revenue", format: "inr" }, { key: "repeatRatePct", label: "Repeat rate", format: "pct" }], rows: segs } } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getSeoGeo: tool({
      description: "SEO and GEO (AI-answer visibility): site scores, page checks, ranked fixes, Google rank for key searches, whether AI answers cite Dorje, Amazon search presence.",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => {
        const s = d.seo
        const search = (comp?.search || []).map((x: any) => ({ query: x.q, dorjeGoogleRank: x.dorje ?? "not in top 10", top: (x.top || []).slice(0, 5).join(", "), aiAnswerCites: (x.cited || []).join(", ") || "—" }))
        return { source: "Public crawl of dorjeteas.com + Google (India) and AI-answer checks", asOf: `${asOf}; search checked ${comp?.checked ?? "n/a"}`,
          data: { seoScore: s.score, geoScore: s.geo, site: s.site, pages: s.pages.map((p) => ({ path: p.path, score: p.score, title: p.title, h1: p.h1, schema: p.schema, imagesWithoutAlt: p.noAlt, kb: p.kb })), fixes: s.fixes.map(([n, f, w, p]) => ({ n, fix: f, why: w, priority: p })), search, amazonSearch: comp?.amazonSerp },
          notes: ["A theme with SEO/GEO fixes is prepared (branch seo-geo) but NOT published yet; it awaits Gowtham's go-ahead."],
          view: { kpis: [{ label: "SEO score", value: `${s.score}/100` }, { label: "GEO score", value: `${s.geo}/100` }],
            table: { title: "Google rank for key searches", columns: [{ key: "query", label: "Search" }, { key: "dorjeGoogleRank", label: "Dorje rank" }, { key: "aiAnswerCites", label: "AI answer cites" }], rows: search } } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getInventoryAlerts: tool({
      description: "Stock-outs (sold-out variants with 12-month product revenue), price errors, and the current alert list (stock, cart, ads, checkout).",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => {
        const inv = d.inventory
        const oos = inv.oos.map(([p, v, price, qty, rev12]) => ({ product: p, variant: v, price, qty, productRevenue12m: rev12 }))
        return { source: "Shopify products & inventory (read-only)", asOf,
          data: { soldOutVariants: oos.length, activeProducts: inv.activeProducts, variants: inv.variants, soldOut: oos, priceErrors: inv.priceErrors, alerts: d.alerts.map((a) => ({ area: a.lead, title: a.title, detail: a.detail, severity: a.status.label })) },
          view: { table: { title: "Alerts", columns: [{ key: "severity", label: "Severity" }, { key: "area", label: "Area" }, { key: "title", label: "Alert" }], rows: d.alerts.map((a) => ({ severity: a.status.label, area: a.lead, title: a.title })) } } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getCompetitors: tool({
      description: "Competitor intel (public sources, weekly): topic='summary' (key findings, where Dorje wins/loses), 'prices' (₹ per 100 g First/Second Flush), 'teabags' (₹ per bag), 'offers' (shipping, returns, live offers, COD), 'ads' (each brand's Meta ad strategy, angles, offers in ads, Dorje playbook), 'adTypes' (formats, placements, CTAs, ad age, estimated ad-pressure index, Instagram followers, website visits), 'search' (Google/AI/Amazon visibility), 'amazon' (Dorje Amazon vs site prices, rivals' Amazon deals), 'actions' (recommended moves). Optional brand filter (e.g. 'vahdam', 'teabox', 'sancha', 'goodricke', 'udyan', 'happyvalley').",
      inputSchema: z.object({ topic: z.enum(["summary", "prices", "teabags", "offers", "ads", "adTypes", "search", "amazon", "actions"]), brand: z.string().max(40).optional() }),
      execute: async ({ topic, brand }): Promise<ToolOut> => {
        if (!comp) return { source: "Competitor checks", asOf, error: "Competitor data not loaded" }
        const want = (k?: string, name?: string) => !brand || (k || "").toLowerCase().includes(brand.toLowerCase().replace(/\s+/g, "")) || (name || "").toLowerCase().includes(brand.toLowerCase())
        const keepDorje = (k: string, n?: string) => want(k, n) || k === "dorje"
        const base = { source: "Public sources: brands' Shopify products.json & policy pages, Meta Ad Library (India), Google Ads Transparency, Google/Amazon search, Similarweb (estimates)", asOf: `prices ${comp.pricesChecked}; ads ${comp.ao?.checked ?? comp.checked}` }
        switch (topic) {
          case "summary":
            return { ...base, data: { findings: comp.findings, whereDorjeWinsLoses: comp.win, adsTakeaways: comp.atr?.takeaways, mismatchCatalogVsSite: comp.mismatch } }
          case "prices": {
            const rows = comp.price.filter((p: any) => keepDorje(p.k, p.brand)).map((p: any) => ({ brand: p.brand, firstFlushPer100g: p.ff, secondFlushPer100g: p.sf, packs: (p.packs || []).join("/"), onSale: p.onSale, outOfStock: p.oos, src: p.src }))
            return { ...base, data: rows, notes: [comp.method],
              view: { chart: { kind: "bar", title: "First Flush, ₹ per 100 g (median)", x: "brand", format: "inr", series: [{ key: "firstFlushPer100g", label: "First Flush" }, { key: "secondFlushPer100g", label: "Second Flush" }], data: rows.filter((r: any) => r.firstFlushPer100g) },
                table: { columns: [{ key: "brand", label: "Brand" }, { key: "firstFlushPer100g", label: "First Flush /100 g", format: "inr" }, { key: "secondFlushPer100g", label: "Second Flush /100 g", format: "inr" }, { key: "onSale", label: "On sale", format: "num" }], rows } } }
          }
          case "teabags": {
            const rows = comp.bags.filter((p: any) => keepDorje(p.k, p.brand)).map((b: any) => ({ brand: b.brand, perBag: b.perBag, min: b.min, max: b.max, example: b.eg, src: b.src }))
            return { ...base, data: rows, view: { chart: { kind: "bar", title: "₹ per tea bag (median)", x: "brand", format: "inr", series: [{ key: "perBag", label: "₹ per bag" }], data: rows } } }
          }
          case "offers": {
            const rows = comp.offers.filter((p: any) => keepDorje(p.k, p.brand)).map((o: any) => ({ brand: o.brand, type: o.type, shipping: o.ship, returns: o.returns, offers: o.offers, rating: o.rating, cod: o.cod, checkout: o.checkout }))
            return { ...base, data: rows, view: { table: { columns: [{ key: "brand", label: "Brand" }, { key: "offers", label: "Live offers" }, { key: "shipping", label: "Shipping" }], rows } } }
          }
          case "ads": {
            const rows = comp.ao.brands.filter((b: any) => keepDorje(b.k, b.brand)).map((b: any) => ({ brand: b.brand, strategy: b.strategy, activeMetaAds: b.meta, newIn7Days: b.last7, formats: b.formats, angles: b.angles, offersInAds: b.offers, googleAds30d: b.google30d, googleAdvertiser: b.googleAdv }))
            return { ...base, data: { brands: rows, patterns: comp.ao.patterns, gaps: comp.ao.gaps, dorjePlaybook: comp.ao.play, testPlan: comp.ao.test }, notes: [comp.ao.method],
              view: { table: { columns: [{ key: "brand", label: "Brand" }, { key: "activeMetaAds", label: "Active Meta ads", format: "num" }, { key: "strategy", label: "Strategy" }], rows } } }
          }
          case "adTypes": {
            const rows = comp.atr.brands.filter((b: any) => keepDorje(b.b, b.name)).map((b: any) => ({ brand: b.name, activeAds: b.active, pressureIndex_estimate: b.api, formats: b.formats, placements: b.placements?.slice(0, 5), ctas: b.ctas?.slice(0, 3), medianAdAgeDays: b.medianDays, newAdsPerWeek: b.perWeek, showsPricePct: b.pricePct, instagramFollowers: b.ig?.followers, websiteVisitsMonthly_estimate: b.sw?.visits }))
            return { ...base, data: { brands: rows, method: comp.atr.apiMethod, limits: comp.atr.limits, takeaways: comp.atr.takeaways },
              notes: ["Meta does not publish reach/impressions/spend for commercial ads in India: competitor reach is NOT available. The pressure index and Similarweb visits are ESTIMATES."],
              view: { chart: { kind: "bar", title: "Estimated ad-pressure index (0–100)", x: "brand", format: "num", series: [{ key: "pressureIndex_estimate", label: "Pressure index (estimate)" }], data: rows.filter((r: any) => r.pressureIndex_estimate != null).sort((a: any, b: any) => b.pressureIndex_estimate - a.pressureIndex_estimate) } } }
          }
          case "search":
            return { ...base, data: { google: comp.search, amazon: comp.amazonSerp } }
          case "amazon":
            return { ...base, data: { dorjeAmazonVsSite: comp.amazonVsSite, sources: comp.amazonVsSiteSrc, rivalsOnAmazon: comp.ao?.amz }, notes: ["Amazon Seller/Ads accounts are NOT connected; these are public listing prices."],
              view: { table: { title: "Dorje: Amazon vs website price", columns: [{ key: "item", label: "Item" }, { key: "amazon", label: "Amazon", format: "inr" }, { key: "site", label: "Website", format: "inr" }, { key: "gap", label: "Amazon cheaper by", format: "pct" }], rows: comp.amazonVsSite } } }
          case "actions":
            return { ...base, data: { actions: comp.actions, adsPlaybook: comp.ao?.play } }
        }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    getDecisions: tool({
      description: "The founders' open decisions (with recommendation, impact, owner, status), the 30/60/90-day plan, the business verdict, and what is / isn't working. Use for 'what should we do this week'.",
      inputSchema: z.object({}),
      execute: async (): Promise<ToolOut> => ({
        source: "Dashboard analysis (built from Shopify, Meta, Zoko, SEO and competitor data)", asOf,
        data: { verdict: d.verdict, working: d.working, notWorking: d.notWorking, decisions: d.decisions, plan: d.plan, abandonedActions: ab?.actions?.map((x: any) => ({ n: x.n, what: x.what, impact: x.impact })), competitorActions: comp?.actions?.map((x: any) => ({ n: x.n, title: x.title, do: x.do, impact: x.impact })) },
        view: { table: { title: "Open decisions", columns: [{ key: "ask", label: "Decision" }, { key: "owner", label: "Owner" }, { key: "status", label: "Status" }], rows: d.decisions.map((x) => ({ ask: x.ask, owner: x.owner, status: x.status })) } },
      }),
      toModelOutput: ({ output }) => toModel({ output }),
    }),

    compute: tool({
      description: "Exact arithmetic on numbers you already got from other tools (never invent inputs). op: pct_change (from values[0] to values[1]), diff (values[1]-values[0]), ratio (values[0]/values[1]), share (each value as % of the total), sum, average, per_unit (values[0]/values[1], e.g. ₹ per cup).",
      inputSchema: z.object({ op: z.enum(["pct_change", "diff", "ratio", "share", "sum", "average", "per_unit"]), values: z.array(z.object({ label: z.string().max(80), value: z.number() })).min(1).max(30) }),
      execute: async ({ op, values }): Promise<ToolOut> => {
        const v = values.map((x) => x.value)
        const need2 = ["pct_change", "diff", "ratio", "per_unit"].includes(op)
        if (need2 && v.length < 2) return { source: "compute", asOf, error: "Needs two values" }
        const tot = v.reduce((a, b) => a + b, 0)
        const result =
          op === "pct_change" ? (v[0] ? r2(((v[1] - v[0]) / Math.abs(v[0])) * 100) : null)
          : op === "diff" ? r2(v[1] - v[0])
          : op === "ratio" || op === "per_unit" ? (v[1] ? r2(v[0] / v[1]) : null)
          : op === "sum" ? r2(tot)
          : op === "average" ? r2(tot / v.length)
          : values.map((x) => ({ label: x.label, sharePct: tot ? r1((x.value / tot) * 100) : null }))
        return { source: "compute (exact arithmetic)", asOf, data: { op, inputs: values, result } }
      },
      toModelOutput: ({ output }) => toModel({ output }),
    }),
  }
}
