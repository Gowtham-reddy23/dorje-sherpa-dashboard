"use client"

import { ExternalLinkIcon } from "lucide-react"
import { Estimate, Panel, SimpleTable, Tone } from "../kit"

function Src({ href, label = "source" }: { href?: string | null; label?: string }) {
  if (!href) return null
  return <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-xs text-muted-foreground underline-offset-2 hover:underline">{label}<ExternalLinkIcon className="size-3" /></a>
}
const mix = (l?: [string, number][], n = 4) => (l && l.length ? l.slice(0, n).map(([k, v]) => `${k} ${v}%`).join(", ") : "—")
const inr = (v: number) => "₹" + Math.round(v).toLocaleString("en-IN")
const num = (v: number) => Math.round(v).toLocaleString("en-IN")

export function AdTypesReach({ C }: { C: any }) {
  const A = C?.atr
  if (!A) return null
  const B = A.brands as any[]
  const O = A.own, T = O.total
  const max = Math.max(...B.map((b) => b.api || 0), 1)
  return (
    <div className="flex flex-col gap-4">
      <div className="pt-4">
        <h2 className="text-lg font-semibold tracking-tight">Ad types &amp; reach</h2>
        <p className="text-sm text-muted-foreground">What kinds of ads each brand runs, where, and how hard they push, plus every real reach, impression and spend number that is public. Checked {A.checked}. Dorje&apos;s own numbers come from our Meta account (read-only) and are the benchmark.</p>
      </div>

      <Panel title="Takeaways for Dorje" description="Our read of the numbers below">
        <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm leading-relaxed">{A.takeaways.map((t: string, i: number) => <li key={i}>{t}</li>)}</ol>
      </Panel>

      <Panel title="Dorje's own Meta results (benchmark)" description={`${O.period}. Actual numbers from our ad account, read-only.`}>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[[inr(T.amount_spent), "Spend"], [num(T.impressions), "Impressions"], [num(T.reach), "Reach (accounts)"], [T.frequency.toFixed(2), "Frequency"],
            [inr(T.cpm), "CPM"], [`${T.ctr}%`, "CTR (all clicks)"], [T.purchase_roas.toFixed(2), "ROAS"], [num(T.omni_purchase), "Purchases"]].map(([v, l]) => (
            <div key={l} className="rounded-lg border p-3"><div className="text-xl font-semibold tabular-nums">{v}</div><div className="text-xs text-muted-foreground">{l}</div></div>))}
        </div>
        <h3 className="mt-4 mb-1 text-sm font-medium">By format</h3>
        <SimpleTable columns={["Format", "Ads", "Spend", "Share", "Impressions", "CPM", "Link CTR", "Purchases", "ROAS"]} align={["left", "right", "right", "right", "right", "right", "right", "right", "right"]}
          rows={O.byFormat.map((f: any) => [f.k, f.n, inr(f.spend), `${f.share}%`, num(f.impr), f.cpm ? inr(f.cpm) : "—", `${f.ctr}%`, f.purch, f.roas])} />
        <h3 className="mt-4 mb-1 text-sm font-medium">By platform</h3>
        <SimpleTable columns={["Platform", "Spend", "Share", "Impressions", "CPM", "Link CTR", "Purchases", "ROAS"]} align={["left", "right", "right", "right", "right", "right", "right", "right"]}
          rows={O.byPlatform.filter((p: any) => p.spend >= 100).map((p: any) => [p.k.replace("_", " "), inr(p.spend), `${p.share}%`, num(p.impr), p.cpm ? inr(p.cpm) : "—", `${p.ctr}%`, p.purch, p.roas])} />
        <h3 className="mt-4 mb-1 text-sm font-medium">By placement</h3>
        <SimpleTable columns={["Placement", "Spend", "Impressions", "Reach", "Freq.", "CPM", "CTR", "Purchases", "ROAS"]} align={["left", "right", "right", "right", "right", "right", "right", "right", "right"]}
          rows={O.byPosition.map((p: any) => [p.k.replaceAll("_", " "), inr(p.spend), num(p.impr), num(p.reach), p.freq, inr(p.cpm), `${p.ctr}%`, p.purch, p.roas ?? "—"])} />
        <p className="mt-2 text-xs text-muted-foreground">{C.atrNote ?? "Format comes from ad names and creative type. ROAS by format is spend-weighted from each ad. CTA mix: " + O.cta.map(([k, v]: any) => `${k} ${v}`).join(", ") + "."}</p>
      </Panel>

      <Panel title="Ad pressure index" description={<span className="flex flex-wrap items-center gap-2"><Estimate /> Relative visible Meta activity in India. This is not reach.</span>}>
        <div className="flex flex-col gap-1.5">
          {B.map((b) => (
            <div key={b.b} className="grid grid-cols-[9rem_1fr_2.5rem] items-center gap-2 text-sm">
              <span className={b.b === "dorje" ? "font-semibold" : ""}>{b.name}</span>
              <div className="h-3 rounded bg-muted"><div className={"h-3 rounded " + (b.b === "dorje" ? "bg-primary" : "bg-primary/40")} style={{ width: `${(100 * (b.api || 0)) / max}%` }} /></div>
              <span className="text-right tabular-nums">{b.api}</span>
            </div>))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">{A.apiMethod}</p>
      </Panel>

      <Panel title="Real reach, impressions and spend (all that Meta publishes)" description="EU transparency data for ads these brands ran in Europe, and spend and impression ranges for ads Meta classed as political or social-issue">
        <SimpleTable columns={["Brand", "Ran", "Type", "Real numbers", "Who saw it", "Copy", "Ad"]}
          rows={B.flatMap((b) => b.real.map((r: any) => [b.name, r.dates, r.type,
            r.type === "EU" ? `Reach ${num(r.euReach)} accounts · ${r.countries.join(", ")}` : `Spend ${r.spend} · ${r.impr} impressions`,
            r.type === "EU" ? Object.entries(r.ageMix).sort((a: any, c: any) => c[1] - a[1]).slice(0, 2).map(([k, v]) => `${k} ${v}%`).join(", ") + ` · men ${r.genderMix.Male ?? 0}%` : `Audience ${r.aud}`,
            r.copy ?? "(older political/issue-tagged ad)", <Src key={r.id} href={r.url} label="ad" />]))} />
        <p className="mt-2 text-xs text-muted-foreground">No other tracked brand had EU ads (10 EU countries checked) or political/issue ads. India commercial ads have no public reach or spend.</p>
      </Panel>

      <Panel title="Ad types by brand" description="Share of the active ads represented by the cards Meta shows logged out">
        <SimpleTable columns={["Brand", "Format mix", "Multiple versions", "Ads per concept", "Shows prices", "Language", "Ads covered", "Source"]}
          rows={B.map((b) => [b.name, mix(b.formats, 3), b.multiPct != null ? `${b.multiPct}%` : "—", b.variantsPerConcept ?? "—", b.pricePct != null ? `${b.pricePct}%` : "—", mix(b.langs, 2), b.covered ? `${b.covered} of ${b.active}` : "—", <Src key={b.b} href={b.src} label="Ad Library" />])} />
      </Panel>

      <Panel title="Placements, CTAs and landing pages" description="Placements as shown on each ad's Ad Library card">
        <SimpleTable columns={["Brand", "Placements", "CTA buttons", "Landing"]}
          rows={B.map((b) => [b.name, mix(b.placements, 6), mix(b.ctas, 3), mix(b.landing, 3)])} />
      </Panel>

      <Panel title="Launch cadence and ad longevity" description="From start dates on the sampled cards">
        <SimpleTable columns={["Brand", "New in 7 days", "New in 28 days", "New per week (at least)", "Median age (days)", "Age mix"]} align={["left", "right", "right", "right", "right", "left"]}
          rows={B.map((b) => [b.name, b.new7 ?? "—", b.new28 ?? "—", b.perWeek ?? "—", b.medianDays ?? "—", mix(b.longevity, 4)])} />
      </Panel>

      <Panel title="Audience and traffic signals" description={<span className="flex flex-wrap items-center gap-2">Instagram followers (public profile) and Similarweb visits (October 2026) <Estimate /> for Similarweb, a third-party estimate</span>}>
        <SimpleTable columns={["Brand", "Instagram followers", "Posts", "Visits / month (Similarweb est.)", "Change vs Sept", "Paid share of search", "Top channel"]}
          rows={B.map((b) => [b.name, <span key="i" className="inline-flex items-center gap-1">{b.ig?.followers ?? "—"} <Src href={b.ig?.url} label="IG" /></span>, b.ig?.posts ?? "—",
            <span key="s" className="inline-flex items-center gap-1">{b.sw?.visits ?? "—"} <Src href={b.sw?.url} label="SW" /></span>, b.sw?.mom ?? "—", b.sw?.paidKw ?? "—", b.sw?.top ?? "—"])} />
      </Panel>

      <Panel title="What isn't public, and how this was measured">
        <ul className="flex list-disc flex-col gap-1.5 pl-5 text-xs text-muted-foreground">{A.limits.map((l: string, i: number) => <li key={i}>{l}</li>)}</ul>
        <div className="mt-2 flex flex-wrap gap-2"><Tone>Meta Ad Library</Tone><Tone>EU transparency</Tone><Tone>Instagram</Tone><Tone>Similarweb (estimate)</Tone><Tone>Our Meta account</Tone></div>
      </Panel>
    </div>
  )
}
