"use client"

import * as React from "react"
import { LockIcon, MoonIcon, SunIcon } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import type { Dash } from "@/lib/dash"
import { Overview } from "./sections/overview"
import { Revenue } from "./sections/revenue"
import { Acquisition } from "./sections/acquisition"
import { Retention } from "./sections/retention"
import { Abandoned } from "./sections/abandoned"
import { Seo } from "./sections/seo"
import { Inventory } from "./sections/inventory"
import { Decisions } from "./sections/decisions"
import { Plan } from "./sections/plan"
import { Competitors } from "./sections/competitors"
import { Attribution, FilteredStrip } from "./sections/attribution"
import { FilterBar } from "./filters"
import { activeCount, EMPTY, getAttr, type Filters } from "@/lib/attr"
import { AskFloating, AskTab, useAskChat } from "./ask"

const TABS = [
  ["overview", "Overview"], ["ask", "Ask Dorje ✦"], ["revenue", "Revenue & Orders"], ["acquisition", "Acquisition"], ["attribution", "Attribution"], ["retention", "Retention"],
  ["abandoned", "Abandoned checkouts"], ["seo", "SEO & GEO"], ["competitors", "Competitors"], ["inventory", "Inventory & Alerts"], ["decisions", "Decisions"], ["plan", "30/60/90 plan"],
] as const
const RANGES = [7, 30, 90, 365]

export function App({ data, onLock }: { data: Dash; onLock: () => void }) {
  const [range, setRange] = React.useState(30)
  const [tab, setTab] = React.useState<string>("overview")
  const [f, setF] = React.useState<Filters>(EMPTY)
  const attr = getAttr(data)
  const askChat = useAskChat()
  const nf = activeCount(f)
  const { resolvedTheme, setTheme } = useTheme()
  React.useEffect(() => {
    const h = window.location.hash.replace("#", "")
    if (TABS.some(([k]) => k === h)) setTab(h)
  }, [])
  const end = new Date(data.endDate + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })
  const ranged = ["overview", "revenue", "acquisition", "attribution"].includes(tab)
  const sliced = ["overview", "revenue", "attribution"].includes(tab)

  return (
    <div className="mx-auto flex min-h-svh max-w-7xl flex-col gap-4 p-3 md:p-6">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold md:text-2xl">Dorje Teas — Founders Dashboard{(data as { sample?: boolean }).sample && <span className="rounded-md bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-300">SAMPLE DATA</span>}</h1>
          <p className="text-sm text-muted-foreground">Last updated {data.updated} · Data through {end} · Shopify, Meta and Zoko WhatsApp (live, read-only) · Google Ads and Amazon not connected yet</p>
        </div>
        <div className="flex items-center gap-2">
          <ToggleGroup aria-label="Date range" variant="outline" size="sm" spacing={0} selectionMode="single" disallowEmptySelection
            selectedKeys={new Set([String(range)])} onSelectionChange={(k) => { const v = [...k][0]; if (v) setRange(Number(v)) }}
            className={ranged ? "" : "opacity-50"}>
            {RANGES.map((r) => <ToggleGroupItem key={r} id={String(r)}>{r === 365 ? "1 year" : `${r} days`}</ToggleGroupItem>)}
          </ToggleGroup>
          <Button variant="outline" size="icon-sm" aria-label="Toggle dark mode" onPress={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}>
            {resolvedTheme === "dark" ? <SunIcon /> : <MoonIcon />}
          </Button>
          <Button variant="outline" size="icon-sm" aria-label="Lock" onPress={onLock}><LockIcon /></Button>
        </div>
      </header>
      {!ranged && tab !== "ask" && <p className="-mt-2 text-xs text-muted-foreground">The date range applies to Overview, Revenue, Acquisition and Attribution. Other tabs show their own fixed periods.</p>}
      {attr && tab !== "ask" && <FilterBar a={attr} f={f} setF={setF} applies={sliced} />}
      <Tabs selectedKey={tab} onSelectionChange={(k) => { setTab(String(k)); history.replaceState(null, "", "#" + String(k)) }}>
        <div className="-mx-3 overflow-x-auto px-3 md:mx-0 md:px-0">
          <TabsList aria-label="Sections" className="w-max">
            {TABS.map(([k, l]) => <TabsTrigger key={k} id={k}>{l}</TabsTrigger>)}
          </TabsList>
        </div>
        <TabsContent id="overview" className="flex flex-col gap-4 pt-4">{attr && <FilteredStrip d={data} a={attr} range={range} f={f} active={nf} />}<Overview d={data} range={range} /></TabsContent>
        <TabsContent id="ask" className="pt-4"><AskTab chat={askChat} /></TabsContent>
        <TabsContent id="revenue" className="flex flex-col gap-4 pt-4">{attr && <FilteredStrip d={data} a={attr} range={range} f={f} active={nf} />}<Revenue d={data} range={range} /></TabsContent>
        <TabsContent id="acquisition" className="pt-4"><Acquisition d={data} range={range} /></TabsContent>
        <TabsContent id="attribution" className="pt-4">{attr ? <Attribution d={data} a={attr} range={range} f={f} /> : <p className="text-sm text-muted-foreground">Attribution data not loaded.</p>}</TabsContent>
        <TabsContent id="retention" className="pt-4"><Retention d={data} /></TabsContent>
        <TabsContent id="abandoned" className="pt-4"><Abandoned d={data} /></TabsContent>
        <TabsContent id="seo" className="pt-4"><Seo d={data} /></TabsContent>
        <TabsContent id="competitors" className="pt-4"><Competitors d={data} /></TabsContent>
        <TabsContent id="inventory" className="pt-4"><Inventory d={data} /></TabsContent>
        <TabsContent id="decisions" className="pt-4"><Decisions d={data} /></TabsContent>
        <TabsContent id="plan" className="pt-4"><Plan d={data} /></TabsContent>
      </Tabs>
      <AskFloating chat={askChat} hidden={tab === "ask"} />
      <footer className="mt-auto pt-6 text-xs text-muted-foreground">Real data only. Anything marked “Estimate” is a projection from our own numbers. Meta-reported figures use Meta&apos;s own attribution and tend to over-count.</footer>
    </div>
  )
}
