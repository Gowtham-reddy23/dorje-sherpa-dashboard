"use client"

import { CheckIcon, XIcon } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { HELP, type Dash } from "@/lib/dash"
import { Panel, SimpleTable, Tone, Info } from "../kit"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function Score({ label, value, help, note }: { label: string; value: number; help: string; note: string }) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardDescription className="flex items-center gap-1.5">{label} <Info text={help} /></CardDescription>
        <CardTitle className="text-3xl tabular-nums">{value}<span className="text-base text-muted-foreground">/100</span></CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <Progress value={value} aria-label={label} />
        <span className="text-xs text-muted-foreground">{note}</span>
      </CardContent>
    </Card>
  )
}
const ok = (b: boolean) => (b ? <CheckIcon className="size-4 text-emerald-600" aria-label="OK" /> : <XIcon className="size-4 text-red-600" aria-label="Problem" />)

export function Seo({ d }: { d: Dash }) {
  const S = d.seo
  const site = [
    ["Sitemap (list of pages for Google)", S.site.sitemap_ok],
    ["robots.txt points to the sitemap", S.site.robots_has_sitemap],
    ["AI crawlers allowed (ChatGPT, Perplexity, Google AI)", S.site.ai_bots_blocked.length === 0],
    ["llms.txt file exists (guide for AI tools)", S.site.llms_txt],
    ["llms.txt has brand facts (estate, flushes, prices)", S.site.llms_has_brand_facts],
  ] as [string, boolean][]
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 md:grid-cols-3">
        <Score label="Search basics score" value={S.score} help={HELP.seo} note={`Average of ${S.pages.length} key pages`} />
        <Score label="AI-search readiness" value={S.geo} help={HELP.geo} note="Sitemap, crawler access, llms.txt and brand facts" />
        <Panel title="Site-level checks">
          <ul className="flex flex-col gap-1.5 text-sm">{site.map(([l, v]) => <li key={l} className="flex items-center gap-2">{ok(v)}{l}</li>)}</ul>
        </Panel>
      </div>
      <Panel title="Key pages" description="Targets: title 50–60 characters, description 140–155, exactly one main heading, product details marked up for Google, image descriptions on every image">
        <SimpleTable
          columns={["Page", "Score", "Title length", "Description length", "Main heading", "Structured data", "Images missing text", "Page weight"]}
          align={["left", "right", "right", "right", "left", "left", "right", "right"]}
          rows={S.pages.map((p) => [
            <span key={p.path} className="font-mono text-xs">{p.path}</span>,
            <Tone key="s" tone={p.score < 40 ? "danger" : p.score < 70 ? "warning" : "success"}>{p.score}</Tone>,
            <span key="t" className={p.titleLen < 30 || p.titleLen > 65 ? "text-red-600" : ""}>{p.titleLen}</span>,
            <span key="dl" className={p.descLen < 70 || p.descLen > 160 ? "text-red-600" : ""}>{p.descLen}</span>,
            p.h1 === 1 ? "OK" : p.h1 > 1 ? `${p.h1} headings` : p.h1Empty ? "Empty" : "Missing",
            p.schema.length ? p.schema.join(", ") : "None",
            `${p.noAlt} of ${p.imgs}`,
            `${p.kb} KB`,
          ])}
        />
      </Panel>
      <Panel title="Fixes, ranked by impact">
        <SimpleTable columns={["#", "Fix", "Evidence", "Impact"]} rows={S.fixes.map((f) => [f[0], f[1], f[2], <Tone key="i" tone={f[3] === "High" ? "danger" : f[3] === "Medium" ? "warning" : undefined}>{f[3]}</Tone>])} />
      </Panel>
    </div>
  )
}
