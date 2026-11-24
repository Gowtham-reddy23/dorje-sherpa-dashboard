"use client"

import * as React from "react"
import { FilterIcon, XIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { activeCount, EMPTY, type Attr, type Filters } from "@/lib/attr"
import { Info } from "./kit"

function Pick({ label, help, value, onChange, options }: { label: string; help: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  const id = React.useId()
  return (
    <label htmlFor={id} className="flex min-w-0 flex-col gap-1 text-xs text-muted-foreground">
      <span className="flex items-center gap-1">{label}<Info text={help} /></span>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}
        className="h-8 w-full min-w-0 rounded-md border bg-background px-2 text-sm text-foreground shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring/50">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  )
}
const idx = (arr: string[]) => arr.map((x, i) => [String(i), x] as [string, string]).sort((a, b) => a[1].localeCompare(b[1]))
const n = (v: string) => (v === "" ? null : Number(v))

export function FilterBar({ a, f, setF, applies }: { a: Attr; f: Filters; setF: (f: Filters) => void; applies: boolean }) {
  const c = activeCount(f)
  const set = (p: Partial<Filters>) => setF({ ...f, ...p })
  return (
    <div className={"rounded-xl border bg-card p-3 " + (applies ? "" : "opacity-60")}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm font-medium"><FilterIcon className="size-4" />Slice the orders {c > 0 && <span className="rounded-full bg-primary px-2 text-xs text-primary-foreground">{c} on</span>}</span>
        <div className="flex items-center gap-2">
          {!applies && <span className="text-xs text-muted-foreground">Filters apply to Overview, Revenue and Attribution (order-level data)</span>}
          {c > 0 && <Button variant="ghost" size="sm" onPress={() => setF({ ...EMPTY, model: f.model })}><XIcon /> Clear</Button>}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-8">
        <Pick label="Credit sale to" help="Last visit: the visit right before buying. First visit: how the customer first found us on this journey." value={f.model} onChange={(v) => set({ model: v as Filters["model"] })} options={[["last", "Last visit"], ["first", "First visit"]]} />
        <Pick label="Channel / source" help="Where the visit came from, worked out from the link tags (UTM) and the referring site Shopify recorded." value={f.channel === null ? "" : String(f.channel)} onChange={(v) => set({ channel: n(v) })} options={[["", "All channels"], ...idx(a.dims.ch)]} />
        <Pick label="Product group" help="Orders containing at least one item from this group. Groups come from product names." value={f.grp === null ? "" : String(f.grp)} onChange={(v) => set({ grp: n(v) })} options={[["", "All products"], ...idx(a.dims.grp)]} />
        <Pick label="Pack size" help="Orders containing at least one item of this pack size." value={f.pack === null ? "" : String(f.pack)} onChange={(v) => set({ pack: n(v) })} options={[["", "All sizes"], ...idx(a.dims.pack)]} />
        <Pick label="Customer" help="New = the customer's first ever order. Returning = they had ordered before." value={f.cust} onChange={(v) => set({ cust: v as Filters["cust"] })} options={[["all", "New + returning"], ["new", "New customers"], ["ret", "Returning customers"]]} />
        <Pick label="Offer used" help="Discount code entered at checkout, or a Buy-1-Get-1 offer item in the order." value={f.disc} onChange={(v) => set({ disc: v as Filters["disc"] })} options={[["all", "All orders"], ["any", "Any offer"], ["bogo", "Buy 1 Get 1"], ["code", "Discount code"], ["none", "No offer"]]} />
        <Pick label="State" help="Shipping state of the order." value={f.state === null ? "" : String(f.state)} onChange={(v) => set({ state: n(v) })} options={[["", "All states"], ...idx(a.dims.state)]} />
        <Pick label="Payment" help="How the customer paid. Razorpay includes Magic Checkout." value={f.pay === null ? "" : String(f.pay)} onChange={(v) => set({ pay: n(v) })} options={[["", "All payments"], ...idx(a.dims.pay)]} />
      </div>
    </div>
  )
}
