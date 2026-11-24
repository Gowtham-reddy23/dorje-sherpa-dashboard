"use client"

import * as React from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { inr, num, pct, type Dash } from "@/lib/dash"
import { agg, bits, dateWindow, groupBy, metaReported, monthWindow, R, select, UNKNOWN, type Attr, type AttrRow, type Filters } from "@/lib/attr"
import { DataTable } from "../datatable"
import { Grid, Kpi, NotConnected, Panel, Tone } from "../kit"
import { rangeLabel } from "./overview"
import { WhatsAppSection } from "./whatsapp"

export const AHELP = {
  coverage: "Share of orders where Shopify recorded the customer's visits (first and last). Orders without it can't be credited to a channel.",
  known: "Share of orders whose last visit has a real source (an ad, search, WhatsApp link…). The rest are direct or unknown: typed-in, bookmarks, untagged app links.",
  first: "First visit: the visit where this customer first arrived on the journey that ended in the order. Good for 'who finds us'.",
  last: "Last visit: the visit right before the purchase. Good for 'who closes the sale'.",
  gap: "How many more (or fewer) purchases Meta claims than the orders Shopify saw arriving from that campaign's ad links. Positive = Meta over-counts.",
  rev: "Order value after discounts, before shipping and tax. Cancelled orders are left out.",
  direct: "Orders whose last visit was direct or had no recorded source. High numbers mean links are not tagged.",
}
const cfg = { first: { label: "First visit", color: "var(--chart-2)" }, last: { label: "Last visit", color: "var(--chart-1)" } } satisfies ChartConfig
const DIMS = [["ch", "Channel"], ["grp", "Product group"], ["pack", "Pack size"], ["state", "State"], ["pay", "Payment"], ["sales", "Sales channel"], ["cust", "New vs returning"]] as const

export function Attribution({ d, a, range, f }: { d: Dash; a: Attr; range: number; f: Filters }) {
  const w = dateWindow(d.endDate, range)
  const rows = React.useMemo(() => select(a, w.from, w.to, f), [a, w.from, w.to, f])
  const prev = React.useMemo(() => select(a, w.pFrom, w.pTo, f), [a, w.pFrom, w.pTo, f])
  const noCh = React.useMemo(() => select(a, w.from, w.to, f, ["channel"]), [a, w.from, w.to, f])
  const A = agg(rows), P = agg(prev)
  const hasPrev = a.rows.length > 0 && a.rows[0][R.date] <= w.pFrom
  const ch = (x: number, y: number) => (hasPrev && y ? ((x - y) / y) * 100 : null)
  const unknownIdx = a.dims.ch.map((c, i) => (UNKNOWN.includes(c) ? i : -1)).filter((i) => i >= 0)
  const unk = rows.filter((r) => unknownIdx.includes(r[R.last])).length
  const unkPct = rows.length ? (unk / rows.length) * 100 : 0
  const known = 100 - unkPct

  // First vs last by channel (all channel filters ignored so both models are comparable)
  const firstBy = groupBy(noCh, (r) => r[R.first], (i) => a.dims.ch[i])
  const lastBy = groupBy(noCh, (r) => r[R.last], (i) => a.dims.ch[i])
  const fm = new Map(firstBy.map((x) => [x.key, x]))
  const totalRev = noCh.reduce((s, r) => s + r[R.rev], 0) || 1
  const chRows = lastBy.map((l) => {
    const fi = fm.get(l.key)
    return { name: l.name, lastOrders: l.orders, lastRev: Math.round(l.rev), share: (l.rev / totalRev) * 100, firstOrders: fi?.orders ?? 0, firstRev: Math.round(fi?.rev ?? 0), shift: fi?.rev ? ((l.rev - fi.rev) / fi.rev) * 100 : null, newPct: l.newPct, aov: Math.round(l.aov) }
  })
  for (const fi of firstBy) if (!lastBy.some((l) => l.key === fi.key)) chRows.push({ name: fi.name, lastOrders: 0, lastRev: 0, share: 0, firstOrders: fi.orders, firstRev: Math.round(fi.rev), shift: -100, newPct: fi.newPct, aov: Math.round(fi.aov) })
  const chart = chRows.slice(0, 8).map((r) => ({ name: r.name.replace(" (unpaid or untagged)", ""), first: r.firstRev, last: r.lastRev }))

  // Meta campaign UTM match vs Meta-reported purchases (month-aligned, unfiltered)
  const mw = monthWindow(a, d.endDate, range)
  const mrows = select(a, mw.from, mw.to, { ...f, channel: null, grp: null, pack: null, cust: "all", disc: "all", state: null, pay: null })
  const mShop = groupBy(mrows, (r) => r[R.campLast], (i) => a.dims.camp[i])
  const mRep = metaReported(a, mw.from, mw.to)
  const names = new Set([...mShop.map((x) => x.name), ...mRep.keys()])
  const metaRows = [...names].map((n) => {
    const s = mShop.find((x) => x.name === n); const m = mRep.get(n)
    const so = s?.orders ?? 0, mp = m?.purchases ?? 0
    return { name: n, spend: m?.spend ?? 0, shopOrders: so, shopRev: Math.round(s?.rev ?? 0), metaPurch: mp, metaValue: m?.value ?? 0, gap: so ? ((mp - so) / so) * 100 : null }
  }).filter((r) => r.spend > 0 || r.shopOrders > 0)
  const tShop = metaRows.reduce((s, r) => s + r.shopOrders, 0), tMeta = metaRows.reduce((s, r) => s + r.metaPurch, 0)
  const tShopRev = metaRows.reduce((s, r) => s + r.shopRev, 0), tMetaVal = metaRows.reduce((s, r) => s + r.metaValue, 0)
  const tSpend = metaRows.reduce((s, r) => s + r.spend, 0)
  const over = tShop ? ((tMeta - tShop) / tShop) * 100 : 0
  const mwLabel = `${new Date(mw.from + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" })} – ${new Date(mw.to + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" })}`

  // Slice table
  const [dim, setDim] = React.useState<string>("ch")
  const keyFn = (r: AttrRow): number | number[] => dim === "ch" ? r[f.model === "last" ? R.last : R.first] : dim === "grp" ? bits(r[R.grp]) : dim === "pack" ? bits(r[R.pack]) : dim === "state" ? r[R.state] : dim === "pay" ? r[R.pay] : dim === "sales" ? r[R.sales] : r[R.new]
  const lab = (i: number) => dim === "cust" ? ["Returning", "New", "Unknown"][i] : (a.dims as Record<string, string[]>)[dim][i]
  const slice = groupBy(rows, keyFn, lab).map((x) => ({ name: x.name, orders: x.orders, rev: Math.round(x.rev), share: A.rev ? (x.rev / A.rev) * 100 : 0, aov: Math.round(x.aov), newPct: x.newPct, discPct: x.orders ? (x.disc / x.orders) * 100 : 0 }))

  const zoko = chRows.find((r) => r.name === "WhatsApp (Zoko)")
  return (
    <div className="flex flex-col gap-4">
      <Grid>
        <Kpi label="Orders (filtered)" value={num(A.orders)} help="Orders matching the filters in this period. Cancelled orders are left out." delta={ch(A.orders, P.orders)} />
        <Kpi label="Revenue (filtered)" value={inr(A.rev)} help={AHELP.rev} delta={ch(A.rev, P.rev)} />
        <Kpi label="New customers" value={pct(A.newPct, 0)} help="Share of these orders that were the customer's first ever order." sub={`${num(A.newC)} first orders`} />
        <Kpi label="Direct / unknown" value={pct(unkPct, 0)} help={AHELP.direct} goodUp={false} sub={`${num(unk)} orders without a clear source`} />
      </Grid>
      <Panel title="How much can we trust this?" help={AHELP.coverage}>
        <div className="grid gap-4 md:grid-cols-3">
          <div><div className="text-2xl font-semibold tabular-nums">{pct(A.journey, 1)}</div><p className="text-sm text-muted-foreground">of orders have visit data from Shopify (coverage)</p></div>
          <div><div className="text-2xl font-semibold tabular-nums">{pct(known, 0)}</div><p className="text-sm text-muted-foreground">have a clear last-visit source. The other {pct(unkPct, 0)} are direct or unknown.</p></div>
          <p className="text-sm text-muted-foreground">Based on {num(a.total)} Shopify orders from the last 12 months ({num(a.cancelled)} cancelled left out). Sources come from link tags (UTMs) and the referring site. Untagged WhatsApp, email and app links show up as Direct, so channels that use them are under-counted.</p>
        </div>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="First visit vs last visit: revenue by channel" help={`${AHELP.first} ${AHELP.last}`} description={`${rangeLabel(range)} · other filters applied, channel filter ignored`}>
          <ChartContainer config={cfg} className="aspect-auto h-80 w-full">
            <BarChart data={chart} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={(v) => inr(Number(v))} />
              <YAxis type="category" dataKey="name" width={130} tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="first" fill="var(--color-first)" radius={3} isAnimationActive={false} />
              <Bar dataKey="last" fill="var(--color-last)" radius={3} isAnimationActive={false} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Meta: what Meta claims vs what Shopify saw" help={AHELP.gap} description={`${mwLabel} (whole months so both sides match) · all orders`}>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border p-3"><div className="text-xs text-muted-foreground">Purchases Meta claims</div><div className="text-2xl font-semibold tabular-nums">{num(tMeta)}</div><div className="text-xs text-muted-foreground">{inr(tMetaVal)} sales value</div></div>
            <div className="rounded-lg border p-3"><div className="text-xs text-muted-foreground">Orders arriving from Meta ad links</div><div className="text-2xl font-semibold tabular-nums">{num(tShop)}</div><div className="text-xs text-muted-foreground">{inr(tShopRev)} revenue (last visit)</div></div>
          </div>
          <p className="mt-3 text-sm">
            {over >= 0 ? <>Meta claims <b>{pct(over, 0)} more</b> purchases than Shopify can trace to Meta links.</> : <>Meta claims <b>{pct(-over, 0)} fewer</b> purchases than Shopify traced to Meta links.</>}{" "}
            On Shopify&apos;s count, each ₹1 of Meta spend brought <b>₹{tSpend ? (tShopRev / tSpend).toFixed(2) : "–"}</b> back (Meta says ₹{tSpend ? (tMetaVal / tSpend).toFixed(2) : "–"}).
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Meta counts view-throughs and multiple devices; Shopify only counts the click that led to the order. The truth is usually in between. Meta value includes shipping and tax; Shopify revenue does not.</p>
        </Panel>
      </div>
      <Panel title="Channels" description={`${rangeLabel(range)} · revenue credited by last visit, compared with first visit`}>
        <DataTable label="Channels" file="dorje-channels.csv" rowKey={(r) => r.name} rows={chRows}
          initial={{ column: "lastRev", direction: "descending" }}
          cols={[
            { key: "name", label: "Channel" },
            { key: "lastOrders", label: "Orders (last)", align: "right", fmt: (v) => num(Number(v)) },
            { key: "lastRev", label: "Revenue (last)", align: "right", fmt: (v) => inr(Number(v)), help: AHELP.last },
            { key: "share", label: "Share", align: "right", fmt: (v) => pct(Number(v), 1), csv: (r) => r.share.toFixed(1) },
            { key: "firstOrders", label: "Orders (first)", align: "right", fmt: (v) => num(Number(v)) },
            { key: "firstRev", label: "Revenue (first)", align: "right", fmt: (v) => inr(Number(v)), help: AHELP.first },
            { key: "shift", label: "Last vs first", align: "right", help: "Positive: this channel closes more sales than it starts. Negative: it starts journeys that other channels finish.", fmt: (v) => v === null ? "–" : <span className={Number(v) >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}>{Number(v) >= 0 ? "+" : ""}{Number(v).toFixed(0)}%</span>, csv: (r) => r.shift === null ? "" : r.shift.toFixed(0) },
            { key: "newPct", label: "New customers", align: "right", fmt: (v) => pct(Number(v), 0), csv: (r) => r.newPct.toFixed(0) },
            { key: "aov", label: "Avg order", align: "right", fmt: (v) => inr(Number(v)) },
          ]} />
      </Panel>
      <Panel title="Meta campaigns: Meta's count vs Shopify's count" help={AHELP.gap} description={`${mwLabel}. Matched by campaign name or ID in the ad link tags`}>
        <DataTable label="Meta campaign match" file="dorje-meta-vs-shopify.csv" rowKey={(r) => r.name} rows={metaRows}
          initial={{ column: "spend", direction: "descending" }}
          cols={[
            { key: "name", label: "Campaign" },
            { key: "spend", label: "Spend", align: "right", fmt: (v) => inr(Number(v)) },
            { key: "metaPurch", label: "Meta purchases", align: "right", fmt: (v) => num(Number(v)) },
            { key: "shopOrders", label: "Shopify orders", align: "right", fmt: (v) => num(Number(v)), help: "Orders whose last visit came from this campaign's ad link." },
            { key: "gap", label: "Gap", align: "right", help: AHELP.gap, fmt: (v) => v === null ? <Tone tone="warning">No tagged orders</Tone> : <Tone tone={Number(v) > 25 ? "danger" : Number(v) < -25 ? "warning" : "success"}>{Number(v) >= 0 ? "+" : ""}{Number(v).toFixed(0)}%</Tone>, csv: (r) => r.gap === null ? "" : r.gap.toFixed(0) },
            { key: "metaValue", label: "Meta sales value", align: "right", fmt: (v) => inr(Number(v)) },
            { key: "shopRev", label: "Shopify revenue", align: "right", fmt: (v) => inr(Number(v)) },
          ]} />
        <p className="mt-2 text-xs text-muted-foreground">“Meta campaign not identified” = orders from Meta ad links whose tags don&apos;t name a campaign. Big negative gaps on retargeting usually mean the ad links were tagged with an older campaign name.</p>
      </Panel>
      <Panel title="Slice and compare" description={`${rangeLabel(range)} · all filters applied`} action={
        <ToggleGroup aria-label="Group by" variant="outline" size="sm" spacing={0} selectionMode="single" disallowEmptySelection selectedKeys={new Set([dim])} onSelectionChange={(k) => { const v = [...k][0]; if (v) setDim(String(v)) }} className="hidden lg:flex">
          {DIMS.map(([k, l]) => <ToggleGroupItem key={k} id={k}>{l}</ToggleGroupItem>)}
        </ToggleGroup>}>
        <select aria-label="Group by" value={dim} onChange={(e) => setDim(e.target.value)} className="mb-3 h-8 rounded-md border bg-background px-2 text-sm lg:hidden">
          {DIMS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        <DataTable key={dim} label="Slice" file={`dorje-orders-by-${dim}.csv`} rowKey={(r) => r.name} rows={slice} max={15}
          initial={{ column: "rev", direction: "descending" }}
          cols={[
            { key: "name", label: DIMS.find((x) => x[0] === dim)![1] },
            { key: "orders", label: "Orders", align: "right", fmt: (v) => num(Number(v)) },
            { key: "rev", label: "Revenue", align: "right", fmt: (v) => inr(Number(v)), help: dim === "grp" || dim === "pack" ? "Full value of orders containing this group/size (an order with two groups counts in both)." : AHELP.rev },
            { key: "share", label: "Share", align: "right", fmt: (v) => pct(Number(v), 1), csv: (r) => r.share.toFixed(1) },
            { key: "aov", label: "Avg order", align: "right", fmt: (v) => inr(Number(v)) },
            { key: "newPct", label: "New customers", align: "right", fmt: (v) => pct(Number(v), 0), csv: (r) => r.newPct.toFixed(0) },
            { key: "discPct", label: "With offer", align: "right", help: "Share of orders with a discount code or a Buy-1-Get-1 item.", fmt: (v) => pct(Number(v), 0), csv: (r) => r.discPct.toFixed(0) },
          ]} />
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Discount codes used" description="Last 12 months. Most offers run as automatic Buy-1-Get-1 deals, not codes">
          <DataTable label="Discount codes" file="dorje-discount-codes.csv" rowKey={(r) => r.code} rows={a.codes.map(([code, n]) => ({ code, n }))}
            initial={{ column: "n", direction: "descending" }}
            cols={[{ key: "code", label: "Code" }, { key: "n", label: "Orders", align: "right", fmt: (v) => num(Number(v)) }]} />
        </Panel>
        <div className="flex flex-col gap-3">
          <Panel title="WhatsApp (Zoko) from Shopify's side" help="Orders whose visit came from a Zoko broadcast link (tagged utm_source=ZOKO) or a WhatsApp link.">
            <p className="text-sm">{zoko ? <>{num(zoko.lastOrders)} orders and {inr(zoko.lastRev)} in this period came from WhatsApp links; {pct(zoko.newPct, 0)} were new customers, so WhatsApp mostly brings back people who already know us.</> : "No WhatsApp-tagged orders in this period."}</p>
          </Panel>
          <NotConnected name="Google Ads" what="Orders from Google ad links are counted above, but spend and Google's own conversion numbers need the Google Ads connection." />
        </div>
      </div>
      {d.zoko && <WhatsAppSection z={d.zoko} />}
    </div>
  )
}

/** Shown on Overview and Revenue when filters are on: the same headline numbers from order-level data. */
export function FilteredStrip({ d, a, range, f, active }: { d: Dash; a: Attr; range: number; f: Filters; active: number }) {
  const w = dateWindow(d.endDate, range)
  const A = agg(select(a, w.from, w.to, f)), P = agg(select(a, w.pFrom, w.pTo, f))
  const T = agg(select(a, w.from, w.to, { ...f, channel: null, grp: null, pack: null, cust: "all", disc: "all", state: null, pay: null }))
  if (!active) return null
  const ch = (x: number, y: number) => (y ? ((x - y) / y) * 100 : null)
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-primary/30 bg-primary/5 p-3">
      <p className="text-sm font-medium">Filtered view · {rangeLabel(range)} · {pct(T.rev ? (A.rev / T.rev) * 100 : 0, 1)} of all revenue</p>
      <Grid>
        <Kpi label="Orders" value={num(A.orders)} help="Orders matching the filters." delta={ch(A.orders, P.orders)} />
        <Kpi label="Revenue" value={inr(A.rev)} help={AHELP.rev} delta={ch(A.rev, P.rev)} />
        <Kpi label="Average order" value={inr(A.aov)} help="Revenue divided by orders, for the filtered orders." delta={ch(A.aov, P.aov)} />
        <Kpi label="New customers" value={num(A.newC)} help="First-ever orders among the filtered orders." delta={ch(A.newC, P.newC)} sub={`${pct(A.newPct, 0)} of these orders`} />
      </Grid>
      <p className="text-xs text-muted-foreground">Cards and charts below are for all orders (store analytics). The filtered numbers come from individual orders, so totals can differ slightly from store analytics.</p>
    </div>
  )
}
