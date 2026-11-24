"use client"

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { HELP, inr, num, type Dash } from "@/lib/dash"
import { Grid, Info, Kpi, Panel, SimpleTable } from "../kit"

const NAMES: Record<string, string> = { champions: "Champions", loyal: "Loyal", active: "Active", new: "New", promising: "Promising", needs_attention: "Needs attention", almost_lost: "Almost lost", at_risk: "At risk", previously_loyal: "Previously loyal", dormant: "Dormant" }
const SEG_HELP: Record<string, string> = {
  champions: "Bought recently, often, and spend the most.", loyal: "Buy regularly.", active: "Bought recently.", new: "First order very recently.",
  promising: "Recent first-time buyers who spent well.", needs_attention: "Were good customers, slowing down.", almost_lost: "Haven't bought in a while, low past spend.",
  at_risk: "Used to buy often and spend well, but haven't bought in a long time.", previously_loyal: "Were loyal, now gone quiet.", dormant: "No order in a very long time.",
}
const ORDER = ["champions", "loyal", "active", "new", "promising", "needs_attention", "almost_lost", "at_risk", "previously_loyal", "dormant"]
const cfg = { customers: { label: "Customers", color: "var(--chart-2)" } } satisfies ChartConfig

function cellColor(v: number) {
  const t = Math.min(1, v / 6)
  return `color-mix(in oklch, var(--chart-1) ${Math.round(10 + t * 80)}%, transparent)`
}

export function Retention({ d }: { d: Dash }) {
  const R = d.retention
  const seg = Object.fromEntries(R.segments.map((s) => [s.seg, s]))
  const atRisk = (seg.at_risk?.customers ?? 0) + (seg.previously_loyal?.customers ?? 0) + (seg.almost_lost?.customers ?? 0)
  const subsNet = R.subs30.reduce((a, s) => a + s[2], 0), subsOrders = R.subs30.reduce((a, s) => a + s[3], 0)
  const segData = ORDER.filter((k) => seg[k]).map((k) => ({ name: NAMES[k], customers: seg[k].customers }))
  const months = Array.from({ length: 11 }, (_, i) => i + 1)
  return (
    <div className="flex flex-col gap-4">
      <Grid>
        <Kpi label="Lifetime value" value={inr(R.ltv)} help={HELP.ltv} sub={`${num(R.buyers)} customers have bought so far`} />
        <Kpi label="Orders per customer" value={R.ordersPerBuyer.toFixed(2)} help="Average number of orders each customer has placed so far." />
        <Kpi label="At-risk customers" value={num(atRisk)} help="Customers in the At risk, Almost lost and Previously loyal groups. Best target for a win-back message." sub={`${num(seg.at_risk?.customers ?? 0)} at risk, ${num(seg.previously_loyal?.customers ?? 0)} previously loyal`} />
        <Kpi label="Dormant customers" value={num(seg.dormant?.customers ?? 0)} help={SEG_HELP.dormant} sub={`${(((seg.dormant?.customers ?? 0) / Math.max(1, R.buyers)) * 100).toFixed(0)}% of all customers`} />
      </Grid>
      <Panel title="Who comes back, by first-purchase month" help={HELP.heat} description="Each row is the group of customers who first bought that month. Each cell is the share of that group who ordered again N months later. Darker = more came back.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-separate border-spacing-1 text-xs">
            <thead><tr><th className="text-left font-medium text-muted-foreground">First bought</th><th className="text-right font-medium text-muted-foreground">Customers</th>{months.map((m) => <th key={m} className="font-medium text-muted-foreground">+{m} mo</th>)}</tr></thead>
            <tbody>
              {R.heat.map((h) => (
                <tr key={h.cohort}>
                  <td className="whitespace-nowrap pr-2">{h.cohort}</td>
                  <td className="pr-2 text-right tabular-nums">{num(h.size)}</td>
                  {h.cells.map((v, i) => <td key={i} className="h-8 min-w-12 rounded text-center tabular-nums" style={{ background: v === null ? "transparent" : cellColor(v) }}>{v === null ? "" : `${v.toFixed(1)}%`}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Typically 2–5% of a month&apos;s new customers buy again in any later month. Blank cells are months that haven&apos;t happened yet.</p>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Customer groups" description="Shopify's customer groups, based on how recently, how often and how much they buy">
          <ChartContainer config={cfg} className="aspect-auto h-72 w-full">
            <BarChart data={segData} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={110} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="customers" fill="var(--color-customers)" radius={4} isAnimationActive={false} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Group detail">
          <SimpleTable columns={["Group", "Customers", "Lifetime spend", "Days since last order"]} align={["left", "right", "right", "right"]}
            rows={ORDER.filter((k) => seg[k]).map((k) => [<span key={k} className="flex items-center gap-1">{NAMES[k]} <Info text={SEG_HELP[k]} /></span>, num(seg[k].customers), inr(seg[k].spend), num(seg[k].days)])} />
        </Panel>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Subscriptions, last 30 days" help="Prepaid subscription plans (12 monthly or 4 quarterly deliveries paid upfront)." description={`${inr(subsNet)} from ${subsOrders} subscription orders`}>
          <SimpleTable columns={["Product", "Plan", "Revenue", "Orders"]} align={["left", "left", "right", "right"]} rows={R.subs30.map((s) => [s[0], s[1], inr(s[2]), num(s[3])])} />
        </Panel>
        <Panel title="Customer groups by first-purchase month" description="Orders and spend so far by each month's new customers">
          <SimpleTable columns={["Month", "New customers", "Orders so far", "Orders each", "Spend each"]} align={["left", "right", "right", "right", "right"]}
            rows={R.cohorts.map((c) => [new Date(c.cohort + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "numeric" }), num(c.new), num(c.orders), (c.orders / c.new).toFixed(2), inr(c.spend / c.new)])} />
        </Panel>
      </div>
    </div>
  )
}
