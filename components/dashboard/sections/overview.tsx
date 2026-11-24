"use client"

import { Area, AreaChart, Bar, ComposedChart, CartesianGrid, Line, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import { Card, CardContent } from "@/components/ui/card"
import { change, derived, HELP, inr, num, pct, series, windows, type Dash } from "@/lib/dash"
import { Grid, Kpi, NotConnected, Panel, Tone } from "../kit"
import { ZokoSummary } from "./whatsapp"

export function rangeLabel(r: number) { return r === 365 ? "last 12 months" : `last ${r} days` }

export function KpiGrid({ d, range }: { d: Dash; range: number }) {
  const { cur, prev, hasPrev } = windows(d, range)
  const a = derived(cur), b = derived(prev)
  const c = (x: number, y: number) => (hasPrev ? change(x, y) : null)
  const metaPartial = prev.metaDays < range * 0.9
  return (
    <Grid>
      <Kpi label="Revenue" value={inr(cur.rev)} help={HELP.revenue} delta={c(cur.rev, prev.rev)} />
      <Kpi label="Orders" value={num(cur.ord)} help={HELP.orders} delta={c(cur.ord, prev.ord)} />
      <Kpi label="Average order" value={inr(a.aov)} help={HELP.aov} delta={c(a.aov, b.aov)} />
      <Kpi label="Visits" value={num(cur.ses)} help={HELP.sessions} delta={c(cur.ses, prev.ses)} />
      <Kpi label="Visits that buy" value={pct(a.cvr, 2)} help={HELP.cvr} delta={c(a.cvr, b.cvr)} />
      <Kpi label="New customers" value={num(cur.new)} help={HELP.new} delta={c(cur.new, prev.new)} />
      <Kpi label="Returning customers" value={num(cur.ret)} help={HELP.ret} delta={c(cur.ret, prev.ret)} sub={`${pct(a.repeat, 0)} of buyers are repeat`} />
      <Kpi label="Ad spend (Meta)" value={inr(cur.spend)} help={HELP.spend} delta={c(cur.spend, prev.spend)} goodUp={false} sub={metaPartial ? "Earlier period has partial Meta history" : undefined} />
      <Kpi label="Cost per new customer" value={inr(a.cac)} help={HELP.cac} delta={metaPartial ? null : c(a.cac, b.cac)} goodUp={false} sub={`First order is worth ${inr(d.aov.first)} on average`} />
      <Kpi label="Sales per ₹1 of ads" value={`₹${a.mer.toFixed(2)}`} help={HELP.mer} delta={metaPartial ? null : c(a.mer, b.mer)} />
      <Kpi label="Meta ROAS" value={`₹${a.roas.toFixed(2)}`} help={HELP.roas} delta={metaPartial ? null : c(a.roas, b.roas)} sub="Meta's own count" />
      <Kpi label="Left in unfinished checkouts" value={inr(d.abandoned.value)} help={HELP.abandoned} sub={`${d.abandoned.n} checkouts, ${pct((d.abandoned.recovered / Math.max(1, d.abandoned.n)) * 100, 0)} recovered (last 30 days)`} />
    </Grid>
  )
}

const cfg = {
  rev: { label: "Revenue", color: "var(--chart-1)" },
  spend: { label: "Ad spend", color: "var(--chart-3)" },
  new: { label: "New customers", color: "var(--chart-2)" },
} satisfies ChartConfig

export function Overview({ d, range }: { d: Dash; range: number }) {
  const s = series(d, 365)
  const r = series(d, range)
  return (
    <div className="flex flex-col gap-4">
      <Card className="border-l-4 border-l-primary">
        <CardContent className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Business health</span>
          <p className="text-base leading-relaxed md:text-lg">{d.verdict}</p>
        </CardContent>
      </Card>
      <h2 className="text-sm font-medium text-muted-foreground">Headline numbers, {rangeLabel(range)} vs the {range === 365 ? "12 months" : `${range} days`} before</h2>
      <KpiGrid d={d} range={range} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Panel className="lg:col-span-2" title="Revenue, ad spend and new customers" description="Last 12 months, by month">
          <ChartContainer config={cfg} className="aspect-auto h-72 w-full">
            <ComposedChart data={s.data} margin={{ left: 4, right: 4 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} />
              <YAxis yAxisId="l" tickLine={false} axisLine={false} width={52} tickFormatter={(v) => inr(Number(v))} />
              <YAxis yAxisId="r" orientation="right" tickLine={false} axisLine={false} width={40} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar yAxisId="l" dataKey="rev" fill="var(--color-rev)" radius={4} />
              <Bar yAxisId="l" dataKey="spend" fill="var(--color-spend)" radius={4} />
              <Line yAxisId="r" dataKey="new" stroke="var(--color-new)" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ChartContainer>
        </Panel>
        <Panel title={`Revenue trend, ${rangeLabel(range)}`} description={`By ${r.bucket}`}>
          <ChartContainer config={cfg} className="aspect-auto h-72 w-full">
            <AreaChart data={r.data}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={24} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area dataKey="rev" type="monotone" fill="var(--color-rev)" fillOpacity={0.25} stroke="var(--color-rev)" />
            </AreaChart>
          </ChartContainer>
        </Panel>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="What's working">
          <ul className="flex flex-col gap-2">{d.working.map((w) => <li key={w} className="flex gap-2"><Tone tone="success">Working</Tone><span>{w}</span></li>)}</ul>
        </Panel>
        <Panel title="What's not">
          <ul className="flex flex-col gap-2">{d.notWorking.map((w) => <li key={w} className="flex gap-2"><Tone tone="danger">Fix</Tone><span>{w}</span></li>)}</ul>
        </Panel>
      </div>
      <h2 className="text-sm font-medium text-muted-foreground">Channels</h2>
      <div className="grid gap-3 md:grid-cols-3">
        <NotConnected name="Google Ads" what="Spend, cost per new customer and search terms will show here once access is connected." />
        <NotConnected name="Amazon" what="Marketplace sales, ratings and ad spend will show here once Seller Central is connected." />
        {d.zoko ? <ZokoSummary z={d.zoko} /> : <NotConnected name="Zoko (WhatsApp)" what="Broadcast and reminder results will show here once Zoko is connected." />}
      </div>
    </div>
  )
}
