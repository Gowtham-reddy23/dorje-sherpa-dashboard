"use client"

import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis, Pie, PieChart, Cell } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import { HELP, inr, num, series, type Dash } from "@/lib/dash"
import { KpiGrid, rangeLabel } from "./overview"
import { Panel, SimpleTable } from "../kit"

const cfg = {
  rev: { label: "Revenue", color: "var(--chart-1)" }, ord: { label: "Orders", color: "var(--chart-2)" },
  aov: { label: "Average order", color: "var(--chart-4)" }, new: { label: "New customers", color: "var(--chart-2)" }, ret: { label: "Returning customers", color: "var(--chart-1)" },
} satisfies ChartConfig
const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)", "var(--muted-foreground)", "var(--ring)", "var(--border)"]

export function Revenue({ d, range }: { d: Dash; range: number }) {
  const s = series(d, range)
  const total12 = d.mix.reduce((a, m) => a + m[1], 0)
  const mixCfg = Object.fromEntries(d.mix.map((m, i) => [`m${i}`, { label: m[0], color: COLORS[i % COLORS.length] }])) as ChartConfig
  return (
    <div className="flex flex-col gap-4">
      <KpiGrid d={d} range={range} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Revenue and orders" help={HELP.revenue} description={`${rangeLabel(range)}, by ${s.bucket}`}>
          <ChartContainer config={cfg} className="aspect-auto h-64 w-full">
            <BarChart data={s.data}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={20} />
              <YAxis tickLine={false} axisLine={false} width={52} tickFormatter={(v) => inr(Number(v))} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="rev" fill="var(--color-rev)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Average order value" help={HELP.aov} description={`First orders average ${inr(d.aov.first)}, repeat orders ${inr(d.aov.repeat)} (last 12 months)`}>
          <ChartContainer config={cfg} className="aspect-auto h-64 w-full">
            <LineChart data={s.data}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={20} />
              <YAxis tickLine={false} axisLine={false} width={44} domain={["auto", "auto"]} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line dataKey="aov" stroke="var(--color-aov)" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartContainer>
        </Panel>
        <Panel title="New vs returning customers" help={`${HELP.new} ${HELP.ret}`} description={`${rangeLabel(range)}, by ${s.bucket}`}>
          <ChartContainer config={cfg} className="aspect-auto h-64 w-full">
            <BarChart data={s.data}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={20} />
              <YAxis tickLine={false} axisLine={false} width={36} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar dataKey="new" stackId="a" fill="var(--color-new)" />
              <Bar dataKey="ret" stackId="a" fill="var(--color-ret)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Product mix" description="Share of revenue by product group, last 12 months. Groups are from product names">
          <div className="grid items-center gap-4 sm:grid-cols-2">
            <ChartContainer config={mixCfg} className="aspect-square h-56 w-full">
              <PieChart>
                <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                <Pie data={d.mix.map((m, i) => ({ name: `m${i}`, value: m[1] }))} dataKey="value" nameKey="name" innerRadius={50}>
                  {d.mix.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
              </PieChart>
            </ChartContainer>
            <ul className="flex flex-col gap-1 text-sm">
              {d.mix.map((m, i) => (
                <li key={m[0]} className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2"><span className="size-2.5 rounded-sm" style={{ background: COLORS[i % COLORS.length] }} />{m[0]}</span>
                  <span className="tabular-nums text-muted-foreground">{((m[1] / total12) * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          </div>
        </Panel>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top products, last 30 days">
          <SimpleTable columns={["Product", "Revenue", "Orders"]} align={["left", "right", "right"]} rows={d.top30.map((p) => [p[0], inr(p[1]), num(p[2])])} />
        </Panel>
        <Panel title="Top products, last 12 months" description="BOGO = Buy-1-Get-1 clearance packs">
          <SimpleTable columns={["Product", "Revenue", "Orders"]} align={["left", "right", "right"]} rows={d.products12m.slice(0, 12).map((p) => [p[0], inr(p[1]), num(p[2])])} />
        </Panel>
      </div>
    </div>
  )
}
