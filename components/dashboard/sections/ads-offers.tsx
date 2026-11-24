"use client"

import { ExternalLinkIcon } from "lucide-react"
import { Estimate, Panel, SimpleTable, Tone } from "../kit"

function Src({ href, label = "source" }: { href?: string | null; label?: string }) {
  if (!href) return null
  return <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-muted-foreground underline-offset-2 hover:underline">{label}<ExternalLinkIcon className="size-3" /></a>
}
const fmt = (f: Record<string, number>) => Object.entries(f || {}).map(([k, v]) => `${k} ${v}`).join(" · ")

export function AdsOffers({ C }: { C: any }) {
  const A = C?.ao
  if (!A) return null
  const B = A.brands as any[]
  return (
    <div className="flex flex-col gap-4">
      <div className="pt-4">
        <h2 className="text-lg font-semibold tracking-tight">Ads &amp; Offers intel</h2>
        <p className="text-sm text-muted-foreground">What each competitor is advertising and offering right now. Checked {A.checked}. Every row links to its source; strategy lines and the playbook are our read of the evidence.</p>
      </div>

      <Panel title="Top patterns" description="What the market is doing across Meta, Google, sites and Amazon">
        <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm leading-relaxed">{A.patterns.map((p: string, i: number) => <li key={i}>{p}</li>)}</ol>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {B.map((b) => (
          <Panel key={b.k} title={b.brand} className={b.k === "dorje" ? "ring-2 ring-primary/40" : ""}
            description={<span className="flex flex-wrap items-center gap-2">
              <Tone tone={b.meta > 50 ? "success" : b.meta ? undefined : "warning"}>{b.meta ?? "—"} Meta ads</Tone>
              <Tone tone={Number(String(b.google30d).replace(/\D/g, "")) > 50 ? "success" : undefined}>{b.google30d ?? "—"} Google (30 d)</Tone>
              <Src href={b.metaSrc} label="Meta" /><Src href={b.googleSrc} label="Google" />
            </span>}>
            <div className="flex flex-col gap-2 text-sm">
              <p className="leading-relaxed">{b.strategy}</p>
              {b.examples?.length > 0 && <ul className="flex flex-col gap-1 border-l-2 pl-3 text-xs text-muted-foreground">
                {b.examples.map((e: any, i: number) => <li key={i}>“{e.text}” <Src href={e.url} label="ad" /></li>)}
              </ul>}
              <p className="text-xs text-muted-foreground">
                {b.last7 != null && b.meta ? `${b.last7} of ${b.sampled} sampled ads started in the last 7 days. ` : ""}
                {b.oldestDays != null ? `Oldest active ad running ${b.oldestDays} days (since ${b.oldest}). ` : ""}
                {fmt(b.formats) ? `Formats seen: ${fmt(b.formats)}.` : ""}
                {b.googleAdv && b.k === "dorje" ? ` Google advertiser on this domain: ${b.googleAdv}.` : ""}
              </p>
              {b.thumb && <a href={b.thumbUrl} target="_blank" rel="noreferrer" className="block overflow-hidden rounded-md border"><img src={b.thumb} alt={`${b.brand} ad`} className="w-full" /></a>}
            </div>
          </Panel>
        ))}
      </div>

      <Panel title="Live offers on their sites" description="Homepage banner, popups and cart seen with India store settings">
        <SimpleTable columns={["Brand", "Headline offer", "Free shipping / COD", "Email / WhatsApp capture", "Gifts & samples", "Loyalty / subs / other", "Source"]}
          rows={B.map((b) => [<span key="b" className={b.k === "dorje" ? "font-semibold" : ""}>{b.brand}</span>, ...b.offers.slice(0, 5), <Src key="s" href={b.offers[5]} label="site" />])} />
      </Panel>

      <Panel title="Angle matrix" help="How many of each brand's active ads (headlines plus the copy of sampled ads) match each angle's keywords. Shows direction, not exact shares. Green = 5 or more ads." description="Meta ads by angle, plus Google ads in the last 30 days">
        <SimpleTable columns={["Brand", "Meta ads", "Google 30 d", ...A.angleCols]} align={["left", "right", "right", ...A.angleCols.map(() => "right" as const)]}
          rows={B.map((b) => [<span key="b" className={b.k === "dorje" ? "font-semibold" : ""}>{b.brand}</span>, b.meta ?? "—", b.googleSrc ? <a key="g" href={b.googleSrc} target="_blank" rel="noreferrer" className="underline-offset-2 hover:underline">{b.google30d ?? "—"}</a> : "—",
            ...A.angleKeys.map((ks: string[], i: number) => { const n = ks.reduce((s: number, k: string) => s + (b.angles?.[k] || 0), 0); return n ? <Tone key={i} tone={n >= 5 ? "success" : undefined}>{n}</Tone> : "" })])} />
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Amazon.in deals on Darjeeling" description="Discount and deal badges on the search cards">
          <SimpleTable columns={["Brand", "What the card shows", ""]} rows={A.amz.map((a: string[]) => [a[0], <span key="t" className="text-xs">{a[1]}</span>, <Src key="s" href={a[2]} label="Amazon" />])} />
        </Panel>
        <Panel title="Gaps Dorje can use">
          <ul className="flex list-disc flex-col gap-2 pl-5 text-sm leading-relaxed">{A.gaps.map((g: string, i: number) => <li key={i}>{g}</li>)}</ul>
        </Panel>
      </div>

      <Panel title="Dorje ad & offer playbook" description="Ordered by expected impact. Budget shares and impacts are estimates to test, not forecasts.">
        <SimpleTable columns={["#", "Move", "What to run", "Budget", "Measure"]}
          rows={A.play.map((p: string[]) => [p[0], <span key="t" className="font-medium">{p[1]}</span>, p[2], <span key="b" className="flex flex-col items-start gap-1">{p[3]}{/estimate/i.test(p[3]) && <Estimate />}</span>, p[4]])} />
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{A.test}</p>
      </Panel>

      <Panel title="How the ads & offers check was done">
        <p className="text-sm leading-relaxed text-muted-foreground">{A.method}</p>
      </Panel>
    </div>
  )
}
