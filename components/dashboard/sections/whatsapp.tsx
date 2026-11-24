"use client"

import * as React from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { inr, num, pct } from "@/lib/dash"
import type { Zoko } from "@/lib/zoko"
import { Estimate, Grid, Kpi, Panel, SimpleTable, Tone } from "../kit"

const cfg = { n: { label: "Contacts", color: "var(--chart-2)" } } satisfies ChartConfig
const mon = (m: string) => new Date(m + "-01T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" })

/** Coverage note shown while the contact download is still partial. */
function Partial({ z }: { z: Zoko }) {
  if (z.customers.complete) return null
  return <p className="text-xs text-amber-700 dark:text-amber-300">Partial: {num(z.customers.fetched)} of {num(z.customers.total)} WhatsApp contacts downloaded ({pct(z.customers.coveragePct, 0)}). Zoko allows 2,000 contacts per request, one request every 5 minutes and 10,000 per sort order, so contact-based numbers are a lower bound.</p>
}

export function ZokoSummary({ z }: { z: Zoko }) {
  const J = z.join, T = z.templates
  return (
    <Panel title="WhatsApp (Zoko)" description={`Connected (read-only) · as of ${z.asOf}`} action={z.customers.complete ? <Tone tone="success">Live</Tone> : <Estimate />}>
      <p className="text-sm">{num(z.customers.total)} WhatsApp contacts. {pct(J.reachablePct, 0)} of last-12-month buyers are in Zoko. Abandoned-cart template: {T.abandonedExists ? (T.abandonedActive ? "exists and approved" : "exists, not approved") : "missing"}.</p>
    </Panel>
  )
}

export function ZokoAbandoned({ z }: { z: Zoko }) {
  const T = z.templates
  return (
    <Panel title="WhatsApp reminders in Zoko" help="Read from Zoko's template list. 'Approved' means WhatsApp approved the template; the API can't tell us whether the automation that sends it is switched on." description={`As of ${z.asOf}`}>
      <div className="flex flex-col gap-2 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          {T.abandonedExists ? <Tone tone="success">Abandoned-cart template approved</Tone> : <Tone tone="danger">No abandoned-cart template</Tone>}
          <span className="text-muted-foreground">{T.abandoned.length} reminder templates: {T.abandoned.map((t) => t.id).join(", ")}</span>
        </div>
        <p className="text-xs text-muted-foreground">Delivery, clicks and recovered orders per reminder are not available from the Zoko API. Check the automation is on inside Zoko, then compare unfinished checkouts above before and after.</p>
      </div>
    </Panel>
  )
}

export function WhatsAppSection({ z }: { z: Zoko }) {
  const J = z.join, C = z.customers, T = z.templates
  const S = J.segments
  const segRows = Object.entries(S)
  const eng = S["In Zoko, has messaged you"], quiet = S["In Zoko, never messaged"], out = S["Not in Zoko"]
  const newM = C.newPerMonth.map(([m, n]) => ({ m: mon(m), n }))
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold">WhatsApp (Zoko)</h2>
        <p className="text-sm text-muted-foreground">Read-only connection to Zoko, as of {z.asOf}. Contacts are matched to Shopify buyers by phone number (last 10 digits). Buyer numbers cover the last 12 months.</p>
        <Partial z={z} />
      </div>
      <Grid>
        <Kpi label="WhatsApp contacts" value={num(C.total)} help="Everyone in Zoko on the WhatsApp channel." sub={`${num(C.contactableNow)} can get a free-form message right now (replied in the last 24 hours)`} />
        <Kpi label="Buyers reachable on WhatsApp" value={pct(J.reachablePct, 0)} help="Share of customers who ordered in the last 12 months whose phone number is a Zoko contact." sub={`${num(J.reachable)} of ${num(J.buyers)} buyers`} />
        <Kpi label="Revenue from Zoko contacts" value={inr(J.revenueReachable)} help="Last-12-month order value from buyers who are Zoko contacts. This is not revenue caused by WhatsApp; see the Attribution tab for orders that came through WhatsApp links." sub={`${pct(J.revenueReachablePct, 0)} of buyer revenue`} />
        <Kpi label="Repeat rate: messaged you vs not" value={eng && eng.buyers ? `${pct(eng.repeatRate, 0)} vs ${pct(out.repeatRate, 0)}` : "—"} help="Share of buyers with 2+ orders in 12 months. 'Messaged you' = the contact has sent at least one WhatsApp message to Dorje. Compared with buyers not in Zoko." sub={quiet ? `Zoko contacts who never messaged: ${pct(quiet.repeatRate, 0)}` : undefined} />
      </Grid>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Buyers by WhatsApp status" help="Correlation, not cause: people who message a brand are often already loyal." description="Last 12 months, Shopify orders matched to Zoko contacts">
          <SimpleTable columns={["Group", "Buyers", "Revenue", "Per buyer", "Repeat rate"]} align={["left", "right", "right", "right", "right"]}
            rows={segRows.map(([k, s]) => [k, num(s.buyers), inr(s.revenue), inr(s.revPerBuyer), pct(s.repeatRate, 0)])} />
          <p className="mt-2 text-xs text-muted-foreground">{J.note}</p>
        </Panel>
        <Panel title="When contacts last messaged you" help="From Zoko's 'last incoming message' time for each contact." description={`${num(C.fetched)} contacts`}>
          <SimpleTable columns={["Last message from the customer", "Contacts", "Share"]} align={["left", "right", "right"]}
            rows={C.recency.map(([k, n]) => [k, num(n), pct(C.fetched ? (n / C.fetched) * 100 : 0, 0)])} />
        </Panel>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="New WhatsApp contacts per month" action={C.complete ? undefined : <Estimate />} description={C.newPerMonthNote + (C.complete ? "" : " Partial until all contacts are downloaded.")}>
          <ChartContainer config={cfg} className="aspect-auto h-56 w-full">
            <BarChart data={newM} margin={{ left: 0, right: 8 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="m" tickLine={false} axisLine={false} fontSize={11} />
              <YAxis tickLine={false} axisLine={false} width={40} fontSize={11} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="n" fill="var(--color-n)" radius={3} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Message templates" help="All templates in Zoko, grouped by their name and text. 'Approved' means WhatsApp approved it for sending; it doesn't mean an automation is using it." description={`${num(T.total)} templates, ${num(T.active)} approved`}>
          <SimpleTable columns={["Type", "Templates", "Approved"]} align={["left", "right", "right"]} rows={T.categories.map(([c, n, a]) => [c, num(n), num(a)])} />
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
            {T.abandonedExists ? <Tone tone="success">Abandoned-cart reminder: approved</Tone> : <Tone tone="danger">No abandoned-cart reminder</Tone>}
            {(T.lifecycle["Reorder reminder"] || []).length ? <Tone tone="success">Reorder reminder: approved</Tone> : <Tone tone="warning">No reorder reminder</Tone>}
          </div>
        </Panel>
      </div>
      {z.messageSample && <MessageSample m={z.messageSample} />}
      <Panel title="What Zoko's API can't show yet">
        <ul className="list-disc pl-5 text-sm text-muted-foreground">{z.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
      </Panel>
    </div>
  )
}

function MessageSample({ m }: { m: NonNullable<Zoko["messageSample"]> }) {
  const rate = (r: Record<string, number> | undefined) => {
    const t = r ? Object.values(r).reduce((a, b) => a + b, 0) : 0
    if (!r || !t) return ["—", "—", "—", "0"]
    const seen = (r.seen || 0) + (r.read || 0), del = seen + (r.delivered || 0)
    return [pct((del / t) * 100, 0), pct((seen / t) * 100, 0), pct(((r.failed || 0) / t) * 100, 0), num(t)]
  }
  const out = m.sources.reduce((a, [, n]) => a + n, 0) || 1
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Message delivery (sample)" action={<Estimate />} description={m.note}>
        <SimpleTable columns={["Sent by", "Share of sent", "Delivered", "Read", "Failed", "Checked"]} align={["left", "right", "right", "right", "right", "right"]}
          rows={[...m.sources.map(([k, n]) => [k, pct((n / out) * 100, 0), ...rate(m.statusByType[k])]),
                 ["All checked", "", pct(m.delivered, 0), pct(m.read, 0), pct(m.failed, 0), num(m.checked)]]} />
        {m.failReasons.length > 0 && <p className="mt-2 text-xs text-muted-foreground">Main failure reason: {m.failReasons[0][0]} ({num(m.failReasons[0][1])} of {num(m.checked)} checked). Code 131049 is WhatsApp holding back marketing messages to people who get too many or don&apos;t engage.</p>}
      </Panel>
      <Panel title="What the sample shows" action={<Estimate />} description={`${num(m.contacts)} contacts, ${num(m.messages)} messages`}>
        <SimpleTable columns={["Measure", "Value"]} align={["left", "right"]} rows={[
          ["Messages that are broadcasts", pct(((m.sources.find(([k]) => k === "Broadcast")?.[1] || 0) / out) * 100, 0)],
          ["Contacts who wrote back at least once", pct(m.repliedPct, 0)],
          ["Abandoned-cart reminders seen in the sample", m.abandonedSent ? `${num(m.abandonedSent)} (latest ${m.abandonedLast})` : "None"],
          ["Contacts with any tag", pct(m.tagged, 0)],
          ...m.sentByType.slice(0, 5).map(([k, n]) => [`Sent: ${k}`, num(n)] as [string, string]),
        ]} />
      </Panel>
    </div>
  )
}
