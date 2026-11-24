"use client"

import * as React from "react"
import type { SortDescriptor } from "react-aria-components"
import { Bar, CartesianGrid, ComposedChart, Line, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { change, derived, HELP, inr, num, series, windows, type Campaign, type Dash } from "@/lib/dash"
import { Grid, Kpi, NotConnected, Panel, Tone, Info } from "../kit"
import { rangeLabel } from "./overview"
import { DownloadIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { download, toCsv } from "@/lib/attr"

const cfg = { spend: { label: "Ad spend", color: "var(--chart-3)" }, mv: { label: "Sales Meta credits to ads", color: "var(--chart-1)" }, cac: { label: "Cost per new customer", color: "var(--chart-5)" } } satisfies ChartConfig
const FLAG_HELP: Record<string, string> = {
  "Dead spend": "Spent a meaningful amount but Meta reports less than ₹0.80 back per ₹1.",
  "No buyer exclusion": "A new-customer campaign that does not leave out people who already bought, so we may pay to reach existing customers.",
  "High frequency": "People saw these ads 4+ times on average. Usually a sign the audience is tired of them.",
}

export function Acquisition({ d, range }: { d: Dash; range: number }) {
  const { cur, prev, hasPrev } = windows(d, range)
  const a = derived(cur), b = derived(prev)
  const partial = prev.metaDays < range * 0.9
  const c = (x: number, y: number) => (hasPrev && !partial ? change(x, y) : null)
  const s = series(d, range)
  const camps = d.campaigns[String(range)] ?? []
  const [sort, setSort] = React.useState<SortDescriptor>({ column: "spend", direction: "descending" })
  const sorted = React.useMemo(() => {
    const k = sort.column as keyof Campaign
    return [...camps].sort((x, y) => {
      const va = x[k] ?? -1, vb = y[k] ?? -1
      const r = typeof va === "string" ? String(va).localeCompare(String(vb)) : Number(va) - Number(vb)
      return sort.direction === "descending" ? -r : r
    })
  }, [camps, sort])
  const flagged = camps.filter((x) => x.flags.length)
  const cacVsFirst = a.cac / Math.max(1, d.aov.first)
  return (
    <div className="flex flex-col gap-4">
      <Grid>
        <Kpi label="Ad spend (Meta)" value={inr(cur.spend)} help={HELP.spend} delta={c(cur.spend, prev.spend)} goodUp={false} />
        <Kpi label="Meta ROAS" value={`₹${a.roas.toFixed(2)}`} help={HELP.roas} delta={c(a.roas, b.roas)} sub={`${inr(cur.mv)} of sales credited by Meta`} />
        <Kpi label="Meta cost per purchase" value={inr(a.cpa)} help={HELP.cpa} delta={c(a.cpa, b.cpa)} goodUp={false} sub={`${num(cur.mp)} purchases credited by Meta`} />
        <Kpi label="Cost per new customer" value={inr(a.cac)} help={HELP.cac} delta={c(a.cac, b.cac)} goodUp={false} sub="Uses real new customers from Shopify" />
      </Grid>
      <Panel title="Cost per new customer vs first-order value" help={HELP.firstAov}>
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-8">
          <div><div className="text-3xl font-semibold tabular-nums">{inr(a.cac)} <span className="text-base font-normal text-muted-foreground">to win a customer</span></div>
            <div className="text-3xl font-semibold tabular-nums">{inr(d.aov.first)} <span className="text-base font-normal text-muted-foreground">their first order is worth (revenue, before costs)</span></div></div>
          <p className="max-w-xl text-sm text-muted-foreground">
            {cacVsFirst >= 1 ? `We spend more to win a customer than their first order brings in (${(cacVsFirst * 100).toFixed(0)}%). Profit depends on them coming back.` : `Winning a customer costs ${(cacVsFirst * 100).toFixed(0)}% of their first order's revenue. After product and shipping costs, the first order is roughly break-even at best, so repeat orders carry the profit.`} Ad spend here is Meta only.
          </p>
        </div>
      </Panel>
      <Panel title="Spend vs results" description={`${rangeLabel(range)}, by ${s.bucket}`}>
        <ChartContainer config={cfg} className="aspect-auto h-72 w-full">
          <ComposedChart data={s.data}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={20} />
            <YAxis yAxisId="l" tickLine={false} axisLine={false} width={52} tickFormatter={(v) => inr(Number(v))} />
            <YAxis yAxisId="r" orientation="right" tickLine={false} axisLine={false} width={48} tickFormatter={(v) => inr(Number(v))} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Bar yAxisId="l" dataKey="spend" fill="var(--color-spend)" radius={4} />
            <Bar yAxisId="l" dataKey="mv" fill="var(--color-mv)" radius={4} />
            <Line yAxisId="r" dataKey="cac" stroke="var(--color-cac)" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ChartContainer>
      </Panel>
      <Panel title={`Meta campaigns, ${rangeLabel(range)}`} description={`${camps.length} campaigns with spend. ${flagged.length} flagged. Click a column to sort.`}
        action={<Button variant="outline" size="sm" onPress={() => download(`dorje-meta-campaigns-${range}d.csv`, toCsv(["name","type","status","spend","roas","cpa","purchases","value","freq","ctr","cpm"].map((k) => ({ key: k, label: k })).concat([{ key: "flags", label: "flags" }]), sorted.map((x) => ({ ...x, flags: x.flags.join("; ") }))))}><DownloadIcon /> CSV</Button>}>
        <Table aria-label="Meta campaigns" sortDescriptor={sort} onSortChange={setSort}>
          <TableHeader>
            <TableHead id="name" isRowHeader allowsSorting>Campaign</TableHead>
            <TableHead id="type" allowsSorting>Type</TableHead>
            <TableHead id="spend" allowsSorting className="text-right">Spend</TableHead>
            <TableHead id="roas" allowsSorting className="text-right">ROAS</TableHead>
            <TableHead id="cpa" allowsSorting className="text-right">Cost/purchase</TableHead>
            <TableHead id="purchases" allowsSorting className="text-right">Purchases</TableHead>
            <TableHead id="freq" allowsSorting className="text-right">Frequency</TableHead>
            <TableHead id="flags">Flags</TableHead>
          </TableHeader>
          <TableBody>
            {sorted.map((x) => (
              <TableRow key={x.name} id={x.name}>
                <TableCell className="max-w-64 truncate" >{x.name}<div className="text-xs text-muted-foreground">{x.status}</div></TableCell>
                <TableCell>{x.type}</TableCell>
                <TableCell className="text-right tabular-nums">{inr(x.spend)}</TableCell>
                <TableCell className="text-right tabular-nums">{x.roas.toFixed(2)}</TableCell>
                <TableCell className="text-right tabular-nums">{x.cpa ? inr(x.cpa) : "–"}</TableCell>
                <TableCell className="text-right tabular-nums">{num(x.purchases)}</TableCell>
                <TableCell className="text-right tabular-nums">{x.freq.toFixed(2)}</TableCell>
                <TableCell><div className="flex flex-wrap gap-1">{x.flags.length ? x.flags.map((f) => <Tone key={f} tone={f === "High frequency" ? "warning" : "danger"}>{f}</Tone>) : <Tone tone="success">OK</Tone>}</div></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
          {Object.entries(FLAG_HELP).map(([k, v]) => <span key={k} className="flex items-center gap-1">{k} <Info text={v} /></span>)}
          <span>ROAS and cost/purchase are Meta&apos;s own numbers. Buyer-exclusion checks look at ad sets that are live today.</span>
        </div>
      </Panel>
      <div className="grid gap-3 md:grid-cols-2">
        <NotConnected name="Google Ads" what="Needed for true blended cost per new customer. Until then, ad spend is Meta only." />
        <NotConnected name="Amazon Ads" what="Sponsored Products spend and sales will show here once connected." />
      </div>
    </div>
  )
}
