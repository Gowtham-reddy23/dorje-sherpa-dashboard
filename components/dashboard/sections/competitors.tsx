"use client"

import { Bar, BarChart, CartesianGrid, LabelList, XAxis, YAxis } from "recharts"
import { ExternalLinkIcon } from "lucide-react"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import type { Dash } from "@/lib/dash"
import { Estimate, Panel, SimpleTable, Tone } from "../kit"
import { AdsOffers } from "./ads-offers"
import { AdTypesReach } from "./ad-types-reach"

const inr = (n: number | null | undefined) => (n == null ? "—" : "₹" + Math.round(n).toLocaleString("en-IN"))
const cfg = { ff: { label: "First Flush ₹/100 g", color: "var(--chart-1)" }, sf: { label: "Second Flush ₹/100 g", color: "var(--chart-3)" } } satisfies ChartConfig
const bcfg = { perBag: { label: "₹ per teabag", color: "var(--chart-2)" } } satisfies ChartConfig

function Src({ href, label = "source" }: { href: string; label?: string }) {
  return <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-muted-foreground underline-offset-2 hover:underline">{label}<ExternalLinkIcon className="size-3" /></a>
}
const range = (min?: number | null, max?: number | null) => (min == null ? "" : min === max ? "" : `${inr(min)}–${inr(max)}`)

export function Competitors({ d }: { d: Dash }) {
  const C = d.comp
  if (!C) return <p className="text-sm text-muted-foreground">Competitor data not loaded.</p>
  const chart = C.price.filter((p: any) => p.ff || p.sf).map((p: any) => ({ brand: p.brand.replace(" Teas", "").replace("Tea Culture of the World", "Tea Culture").replace("VAHDAM India", "Vahdam").replace("Teabox India", "Teabox"), ff: p.ff, sf: p.sf, me: p.k === "dorje" }))
  const bags = [...C.bags].sort((a: any, b: any) => a.perBag - b.perBag).map((b: any) => ({ brand: b.brand.replace(" Teas", "").replace("Tea Culture of the World", "Tea Culture").replace("VAHDAM India", "Vahdam").replace("Teabox India", "Teabox"), perBag: b.perBag }))
  return (
    <div className="flex flex-col gap-4">
      <Panel title="What the competitor check says" description={`Checked ${C.checked} (prices ${C.pricesChecked}). Public data only: competitor websites, Meta Ad Library, Google and Amazon.in.`}>
        <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm leading-relaxed">{C.findings.map((f: string, i: number) => <li key={i}>{f}</li>)}</ol>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-3" title="Price per 100 g, loose-leaf Darjeeling" help="Median across all pack sizes each store sells (subscriptions, teabags, gift boxes and multi-packs left out). Kaahu (₹1,998–8,396/100 g) is off the chart." description="Lower bar = cheaper. Dorje is the first row.">
          <ChartContainer config={cfg} className="aspect-auto h-80 w-full">
            <BarChart data={chart} layout="vertical" margin={{ left: 8, right: 48 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={(v) => inr(Number(v))} />
              <YAxis type="category" dataKey="brand" interval={0} tickLine={false} axisLine={false} width={92} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar isAnimationActive={false} dataKey="ff" fill="var(--color-ff)" radius={3}><LabelList dataKey="ff" position="right" className="fill-foreground text-[10px]" formatter={(v: any) => (v ? inr(v) : "")} /></Bar>
              <Bar isAnimationActive={false} dataKey="sf" fill="var(--color-sf)" radius={3}><LabelList dataKey="sf" position="right" className="fill-foreground text-[10px]" formatter={(v: any) => (v ? inr(v) : "")} /></Bar>
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel className="xl:col-span-2" title="Price per teabag (herbal/flavoured boxes)" help="Box price ÷ number of bags, median of each store's herbal or flavoured teabag boxes on its own website." description="Dorje's site price is ₹360 for 15 and ₹640 for 30 pyramid bags.">
          <ChartContainer config={bcfg} className="aspect-auto h-80 w-full">
            <BarChart data={bags} layout="vertical" margin={{ left: 8, right: 40 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" tickLine={false} axisLine={false} tickFormatter={(v) => "₹" + v} />
              <YAxis type="category" dataKey="brand" interval={0} tickLine={false} axisLine={false} width={92} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar isAnimationActive={false} dataKey="perBag" fill="var(--color-perBag)" radius={3}><LabelList dataKey="perBag" position="right" className="fill-foreground text-[10px]" formatter={(v: any) => "₹" + v} /></Bar>
            </BarChart>
          </ChartContainer>
        </Panel>
      </div>

      <Panel title="Price table" description="₹ per 100 g, median (range). From each store's public product list.">
        <SimpleTable columns={["Brand", "First Flush", "Second Flush", "Pack sizes (g)", "On sale", "Out of stock", "Wellness loose ₹/100 g", "Source"]} align={["left", "right", "right", "left", "right", "right", "right", "left"]}
          rows={C.price.map((p: any) => {
            const b = C.bags.find((x: any) => x.k === p.k)
            return [<span key="b" className={p.k === "dorje" ? "font-semibold" : ""}>{p.brand}</span>,
              <span key="f">{p.k === "kaahu" ? "₹1,998–8,396" : inr(p.ff)}<span className="block text-xs text-muted-foreground">{range(p.ffMin, p.ffMax)}</span></span>,
              <span key="s">{inr(p.sf)}<span className="block text-xs text-muted-foreground">{range(p.sfMin, p.sfMax)}</span></span>,
              (p.packs || []).join(", "), p.onSale == null ? "—" : p.onSale + "%", p.oos == null ? "—" : p.oos + "%", (b?.herbalN ?? 0) >= 3 ? inr(b?.herbal100) : "—", <Src key="src" href={p.src} />]
          })} />
      </Panel>

      <Panel title="Offers, shipping, returns and trust" description="From each store's homepage, product page and shipping/refund policy pages; ratings as shown on the page.">
        <SimpleTable columns={["Brand", "Free shipping / COD", "Returns", "Offers & capture", "Checkout", "Reviews (site)", "Amazon.in", "Sources"]}
          rows={C.offers.map((o: any) => [<span key="b" className={o.k === "dorje" ? "font-semibold" : ""}>{o.brand}<span className="block text-xs text-muted-foreground">{o.type}</span></span>,
            o.ship, o.returns, <span key="o">{o.offers}<span className="block text-xs text-muted-foreground">Capture: {o.capture}</span></span>, o.checkout, o.rating, o.amazon,
            <span key="s" className="flex flex-col gap-0.5">{["shipping", "returns", "site", "rating", "amazon"].map((l, i) => <Src key={l} href={o.src[i]} label={l} />)}</span>])} />
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Meta ads running now (India)" help="Meta Ad Library's estimated count of active ads reaching India for each brand's Facebook page. A brand with 0 had no ads found by a name search." description={`Ad Library, checked ${C.checked}`}>
          <SimpleTable columns={["Brand", "Active ads", "Main angles", ""]} align={["left", "right", "left", "left"]}
            rows={C.ads.map((a: any) => [<span key="b" className={a.k === "dorje" ? "font-semibold" : ""}>{a.brand}</span>, a.active ?? "—", a.angles, <Src key="s" href={a.src} label="ads" />])} />
        </Panel>
        <Panel title="Google search (India settings)" help="google.com with India settings (gl=in), logged out, from a non-India server, so local results can differ. 'AI answer cites' lists brands named in the visible part of Google's AI Overview." description="Dorje's position in the organic top 10">
          <SimpleTable columns={["Search", "Dorje", "Top 5 results", "AI answer cites"]} align={["left", "right", "left", "left"]}
            rows={C.search.map((s: any) => [<a key="q" href={s.src} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">{s.q}</a>,
              s.dorje ? <Tone key="p" tone={s.dorje <= 3 ? "success" : "warning"}>#{s.dorje}</Tone> : <Tone key="p" tone="danger">Not top 10</Tone>,
              <span key="t" className="text-xs">{s.top.join(" · ")}</span>, s.aio ? (s.cited?.length ? s.cited.join(", ") : "No brand named") : "No AI answer"])} />
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Amazon.in search: who shows up" description={`Position of each brand's first card (S = sponsored), checked ${C.checked}`}>
          <SimpleTable columns={["Search", "Top brands", "Dorje"]} rows={C.amazonSerp.map((a: any) => [<a key="q" href={a.url} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">{a.q}</a>, <span key="t" className="text-xs">{a.top}</span>, a.dorje])} />
        </Panel>
        <Panel title="Same Dorje item: Amazon vs dorjeteas.com" description={<span>Price on the Amazon search card vs the site&apos;s one-time price. <Src href={C.amazonVsSiteSrc[0]} label="Amazon" /> <Src href={C.amazonVsSiteSrc[1]} label="site" /></span>}>
          <SimpleTable columns={["Item", "Amazon", "Site", "Amazon is cheaper by"]} align={["left", "right", "right", "right"]}
            rows={C.amazonVsSite.map((a: any) => [a.item, "₹" + a.amazon.toFixed(2).replace(".00", ""), inr(a.site), <Tone key="g" tone={a.gap >= 30 ? "danger" : "warning"}>{a.gap}%</Tone>])} />
        </Panel>
      </div>

      <Panel title="Where Dorje wins and loses">
        <SimpleTable columns={["Area", "", "Evidence"]} rows={C.win.map((w: string[]) => [w[0], <Tone key="t" tone={w[1] === "Win" ? "success" : w[1] === "Lose" ? "danger" : undefined}>{w[1]}</Tone>, w[2]])} />
      </Panel>

      <Panel title="What to do, in order">
        <SimpleTable columns={["#", "Action", "Why", "What to do", "Expected impact", "Owner"]}
          rows={C.actions.map((a: any) => [a.n, <span key="t" className="font-medium">{a.title}</span>, a.why, a.do, <span key="i" className="flex flex-col items-start gap-1">{a.impact}{a.est && <Estimate />}</span>, a.owner])} />
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Catalogue vs live site prices" description="Dorje's printed catalogue compared with dorjeteas.com today">
          <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm">{C.mismatch.map((m: string, i: number) => <li key={i}>{m}</li>)}</ul>
        </Panel>
        <Panel title="How this was measured">
          <p className="text-sm leading-relaxed text-muted-foreground">{C.method} Prices are re-checked weekly.</p>
        </Panel>
      </div>
      <AdsOffers C={C} />
      <AdTypesReach C={C} />
    </div>
  )
}
