"use client"

import { inr, num, type Dash } from "@/lib/dash"
import { Grid, Kpi, Panel, SimpleTable, Tone } from "../kit"

export function Inventory({ d }: { d: Dash }) {
  const I = d.inventory
  return (
    <div className="flex flex-col gap-4">
      <Grid>
        <Kpi label="Price errors live" value={num(I.priceErrors.length)} help="Variants whose price looks wrong compared with similar plans." />
        <Kpi label="Sold-out items" value={num(I.oos.length)} help="Product sizes or plans that customers can't buy right now." sub={`of ${num(I.variants)} items across ${I.activeProducts} live products`} />
        <Kpi label="Open alerts" value={num(d.alerts.length)} help="Problems found in the latest refresh, ranked by urgency." />
      </Grid>
      <Panel title="Price errors">
        <SimpleTable columns={["Product", "Option", "Price now", "Listed 'was' price", "Problem"]} align={["left", "left", "right", "right", "left"]}
          rows={I.priceErrors.map((p) => [p.product, p.variant, inr(p.price), inr(p.compareAt), p.issue])} />
      </Panel>
      <Panel title="Sold out" description="Sorted by the product's revenue over the last 12 months, so the costliest gaps are on top">
        <SimpleTable columns={["Product", "Option", "Price", "Product revenue, 12 months"]} align={["left", "left", "right", "right"]}
          rows={I.oos.map((o) => [o[0], o[1], inr(o[2]), o[4] ? inr(o[4]) : "–"])} />
      </Panel>
      <Panel title="All alerts">
        <ul className="flex flex-col divide-y">
          {d.alerts.map((a) => (
            <li key={a.title} className="flex flex-col gap-1 py-2.5 sm:flex-row sm:items-start sm:gap-3">
              <div className="flex shrink-0 items-center gap-2"><Tone tone={a.status.tone}>{a.status.label}</Tone><span className="w-20 text-xs text-muted-foreground">{a.lead}</span></div>
              <div><div className="font-medium">{a.title}</div><div className="text-sm text-muted-foreground">{a.detail}</div></div>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
