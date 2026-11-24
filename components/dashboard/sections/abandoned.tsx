"use client"

import * as React from "react"
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig } from "@/components/ui/chart"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { HELP, inr, num, pct, windows, type Dash } from "@/lib/dash"
import { getAB, type ABRow } from "@/lib/abandoned"
import { Estimate, Grid, Kpi, NotConnected, Panel, SimpleTable, Tone } from "../kit"
import { ZokoAbandoned } from "./whatsapp"

const cfg = { n: { label: "Unfinished checkouts", color: "var(--chart-4)" }, v: { label: "Sessions", color: "var(--chart-2)" } } satisfies ChartConfig
const wcfg = { lost: { label: "Not recovered", color: "var(--chart-1)" }, rec: { label: "Recovered", color: "var(--chart-4)" } } satisfies ChartConfig
const day = (s: string) => new Date(s + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" })
const rowsOf = (r: ABRow[]) => r.map((x) => [x.k, num(x.n), inr(x.value), pct(x.recPct)])
const toneOf = (t: string | null) => (t === "danger" ? "danger" : t === "warning" ? "warning" : undefined)

function Legacy({ d }: { d: Dash }) {
  // Older summary (kept when the deep-dive file is missing)
  const A = d.abandoned
  const rate = A.n ? A.recovered / A.n : 0
  return (
    <Grid>
      <Kpi label="Unfinished checkouts" value={num(A.n)} help={HELP.abandoned} sub={`${num(A.prior)} in the 30 days before`} />
      <Kpi label="Value left behind" value={inr(A.value)} help="Total value of the carts in unfinished checkouts." />
      <Kpi label="Recovered" value={pct(rate * 100)} help={HELP.recovery} sub={`${A.recovered} came back and paid`} />
      <Kpi label="Reachable" value={`${A.withContact}/${A.n}`} help="Unfinished checkouts where we have contact details." />
    </Grid>
  )
}

export function Abandoned({ d }: { d: Dash }) {
  const AB = getAB(d)
  const [range, setRange] = React.useState<"30" | "90">("30")
  const { cur } = windows(d, 30)
  const funnel = [{ name: "Visits", v: cur.ses }, { name: "Added to cart", v: cur.atc }, { name: "Reached checkout", v: cur.chk }, { name: "Paid", v: cur.done }]
  if (!AB) return <div className="flex flex-col gap-4"><Legacy d={d} /></div>
  const W = range === "30" ? AB.w30 : AB.w90
  const weeks = AB.weeks.map((w) => ({ label: day(w.w) + (w.partial ? "*" : ""), rec: w.rec, lost: w.n - w.rec }))
  const Z = AB.zokoFlow
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">Last {W.days} days ({day(W.since)} – {day(W.until)}). Updated {AB.asOf}. {W.junk ? `${W.junk} junk ₹0 checkouts left out.` : ""}</p>
        <ToggleGroup aria-label="Period" variant="outline" size="sm" spacing={0} selectionMode="single" disallowEmptySelection
          selectedKeys={[range]} onSelectionChange={(k) => { const v = [...k][0]; if (v) setRange(String(v) as "30" | "90") }}>
          <ToggleGroupItem id="30">30 days</ToggleGroupItem>
          <ToggleGroupItem id="90">90 days</ToggleGroupItem>
        </ToggleGroup>
      </div>
      <Grid>
        <Kpi label="Unfinished checkouts" value={num(W.n)} help={HELP.abandoned} sub={`${num(W.people)} people · ${inr(W.value)} in carts`} />
        <Kpi label="Came back and paid" value={pct(W.recPct)} help={HELP.recovery} sub={`${W.rec} checkouts · ${inr(W.recValue)}`} />
        <Kpi label="Left unpaid" value={inr(W.lost)} help="Cart value of unfinished checkouts that were never paid. Not all of this is winnable." sub={`About ${inr(W.perMonthLost)} a month · average cart ${inr(W.avg)}`} />
        <Kpi label="Reachable on WhatsApp" value={pct(W.zokoPct, 0)} help="Unfinished checkouts whose phone number matches a Zoko WhatsApp contact (last 10 digits)." sub={`Phone captured ${pct(W.phonePct, 0)} · email ${pct(W.emailPct, 0)}`} />
      </Grid>

      <Panel title="What we found" description="Read-only checks of Shopify, Zoko and Meta. Numbers update with each refresh.">
        <div className="flex flex-col divide-y">
          {AB.findings.map((f, i) => (
            <div key={i} className="flex flex-col gap-1 py-2.5 first:pt-0 last:pb-0">
              <div className="flex flex-wrap items-center gap-2 text-sm font-medium">{f.tone && <Tone tone={toneOf(f.tone)}>{f.tone === "danger" ? "Fix now" : "Fix soon"}</Tone>}{f.title}</div>
              <p className="text-sm text-muted-foreground">{f.detail}</p>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Unfinished checkouts per week" help="Monday-start weeks, last 90 days. * = week still in progress." description={AB.switch ? `Razorpay Magic Checkout from the week of ${day(AB.switch.date)}: ${AB.switch.pre.perWeek}/week before, ${AB.switch.post.perWeek}/week after` : undefined}>
          <ChartContainer config={wcfg} className="aspect-auto h-64 w-full">
            <BarChart data={weeks}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={16} />
              <YAxis tickLine={false} axisLine={false} width={32} allowDecimals={false} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Bar isAnimationActive={false} dataKey="rec" stackId="a" fill="var(--color-rec)" />
              <Bar isAnimationActive={false} dataKey="lost" stackId="a" fill="var(--color-lost)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ChartContainer>
        </Panel>
        <Panel title="Where visitors drop off" help="Website sessions in the last 30 days (Shopify). With Razorpay's pop-up, a shopper who closes it before typing a phone number never becomes a Shopify abandoned checkout." description={`${num(AB.funnel30.carts)} cart sessions, ${num(AB.funnel30.completed)} paid: ${num(AB.funnel30.cartNoOrder)} carts never became an order`}>
          <ChartContainer config={cfg} className="aspect-auto h-64 w-full">
            <BarChart data={funnel}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="name" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} width={48} />
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <Bar isAnimationActive={false} dataKey="v" fill="var(--color-v)" radius={4} />
            </BarChart>
          </ChartContainer>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Are the reminders firing?" help="Email: inferred from Shopify's record of each checkout. WhatsApp: read from Zoko for a sample of recent unfinished checkouts (GET only, nothing sent).">
          <div className="flex flex-col gap-3 text-sm">
            <div>
              <div className="flex items-center gap-2 font-medium"><Tone tone="warning">1 email</Tone> Shopify abandoned-checkout email</div>
              <p className="text-muted-foreground">About 10 hours after the checkout, for {pct(W.mail10hPct, 0)} of checkouts with an email (inferred). No second or third email seen. {pct(100 - W.emailPct, 0)} gave only a phone number.</p>
            </div>
            {Z ? (
              <div>
                <div className="flex items-center gap-2 font-medium"><Tone tone="danger">{pct(Z.failedPct, 0)} failing</Tone> Zoko WhatsApp reminder</div>
                <p className="text-muted-foreground">{Z.gotReminder} of {Z.checked} checked checkouts got a reminder: the same &ldquo;payment pending&rdquo; template twice ({Z.timing.filter((t) => t[1]).map((t) => `${t[0].toLowerCase()}: ${t[1]}`).join(", ")}). Of {Z.sends} sends, {pct(Z.deliveredPct, 0)} were delivered and {pct(Z.seenPct, 0)} read; {Z.fail131049} failed with error 131049 (Meta&apos;s cap on marketing messages per person). Checked {Z.checkedAt} IST.</p>
              </div>
            ) : null}
            <div>
              <div className="flex items-center gap-2 font-medium"><Tone>No data</Tone> Razorpay Magic Checkout</div>
              <p className="text-muted-foreground">{pct(W.rzpPct, 0)} of these checkouts went through Razorpay&apos;s pop-up. Its own drop-off steps and any cart-recovery messages are only in the Razorpay dashboard (not connected).</p>
            </div>
          </div>
        </Panel>
        <Panel title="Recovery opportunity" action={<Estimate />} description={AB.opp.note}>
          <SimpleTable columns={["If recovery reaches", "Extra orders a month", "Extra revenue a month"]} align={["left", "right", "right"]}
            rows={[["Today", `${pct(AB.opp.cur)} (${AB.w30.rec} orders)`, "—"], ...AB.opp.targets.map((t) => [pct(t.to, 0), num(t.extraOrders), inr(t.extraRevenue)])]} />
          <p className="mt-2 text-xs text-muted-foreground">Base: {AB.opp.baseN} unfinished checkouts a month at {inr(AB.opp.avg)} each. The bigger pool is the {num(AB.funnel30.cartNoOrder)} cart sessions a month that never order: each extra 1% of carts that turn into orders is about {inr(AB.funnel30.carts * 0.01 * AB.aov30)} a month (estimate).</p>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="By cart value" help="Cart value before shipping. Carts under ₹399 pay ₹50 shipping.">
          <SimpleTable columns={["Cart value", "Checkouts", "Value", "Recovered"]} align={["left", "right", "right", "right"]} rows={rowsOf(W.bands)} />
          <p className="mt-2 text-xs text-muted-foreground">Under ₹399: {W.under399} checkouts, {pct(W.under399FeePct, 0)} charged shipping, {pct(W.under399RecPct)} recovered. ₹399 and up: {pct(W.over399RecPct)} recovered ({pct(W.over399FeePct, 0)} still show a ₹50 charge).</p>
        </Panel>
        <Panel title="Most-abandoned products" help="A checkout counts once per product. Sold out = the variant is sold out today.">
          <SimpleTable columns={["Product", "Checkouts", "Value", "Recovered", "Sold out now"]} align={["left", "right", "right", "right", "right"]}
            rows={W.products.slice(0, 8).map((p) => [p.k, num(p.n), inr(p.value), pct(p.recPct), p.oos ? num(p.oos) : "—"])} />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="New vs returning" help="Returning = had at least one earlier order (Shopify order count today, minus this checkout if it was recovered).">
          <SimpleTable columns={["", "Checkouts", "Value", "Recovered"]} align={["left", "right", "right", "right"]} rows={rowsOf(W.newRet)} />
        </Panel>
        <Panel title="Contact captured" help="Email/phone on the checkout or customer record. Email consent is Shopify's email-marketing status.">
          <SimpleTable columns={["", "Checkouts", "Value", "Recovered"]} align={["left", "right", "right", "right"]} rows={rowsOf([...W.contact, ...W.emailState])} />
        </Panel>
        <Panel title="When checkouts are left" help="IST. Day of week and time of day the checkout started.">
          <SimpleTable columns={["", "Checkouts", "Value", "Recovered"]} align={["left", "right", "right", "right"]} rows={rowsOf([...W.hour, ...W.dow])} />
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="How long recovered buyers took" help="Time from starting the checkout to paying, recovered checkouts only.">
          <SimpleTable columns={["Came back within", "Checkouts"]} align={["left", "right"]} rows={W.lag.map((l) => [l.k, num(l.n)])} />
        </Panel>
        <Panel title="Where abandoners are" help="Shipping state on the checkout. — = no address yet.">
          <SimpleTable columns={["State", "Checkouts", "Value", "Recovered"]} align={["left", "right", "right", "right"]} rows={rowsOf(W.states)} />
        </Panel>
      </div>

      <Panel title="Action plan" action={<Estimate />} description={`Actions 1–2 together: about ${inr(AB.totalEst.low)}–${inr(AB.totalEst.high)} a month (estimate). Nothing here has been changed in the store, Zoko or ads.`}>
        <SimpleTable columns={["#", "Who", "What to do", "Impact (estimate)"]}
          rows={AB.actions.map((a) => [String(a.n), a.who, <div key={a.n} className="flex flex-col gap-1 whitespace-normal"><span>{a.what}</span>{a.copy && <span className="text-xs text-muted-foreground">Copy: {a.copy}</span>}</div>, <div key={"i" + a.n} className="flex flex-col gap-1 whitespace-normal"><span>{a.impact}</span><span className="text-xs text-muted-foreground">{a.basis}</span></div>])} />
        <p className="mt-2 text-xs text-muted-foreground">Keep any discount for the last step so customers don&apos;t learn to abandon on purpose. WhatsApp and email reminders need the customer&apos;s consent.</p>
      </Panel>

      {Z ? null : d.zoko ? <ZokoAbandoned z={d.zoko} /> : <NotConnected name="Zoko (WhatsApp)" what="Message delivery, clicks and recovered orders from WhatsApp reminders will show here once Zoko is connected." />}
    </div>
  )
}
