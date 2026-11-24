"use client"

import * as React from "react"
import { Chat, useChat } from "@ai-sdk/react"
import { DefaultChatTransport, type UIMessage } from "ai"
import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"
import { ArrowUpIcon, CheckIcon, CircleAlertIcon, CopyIcon, DownloadIcon, LoaderCircleIcon, MessageCircleIcon, RotateCcwIcon, SparklesIcon, SquareIcon, XIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { inr, num } from "@/lib/dash"
import { STEP_LABEL, type Fmt, type ToolOut, type View } from "@/lib/ask-types"
import { openAskSession, PASS_KEY } from "@/lib/ask-session"
import { Delta } from "./kit"
import { cn } from "@/lib/utils"

export const STARTERS = [
  "Why did revenue drop last week?",
  "Which Meta campaign should I cut?",
  "How are abandoned carts trending?",
  "How do we compare with Vahdam on price?",
  "What should we do this week?",
]

/* ---------- chat instance (shared by the Ask tab and the floating panel) ---------- */
type ToolPart = { type: string; toolCallId: string; state: string; input?: Record<string, unknown>; output?: ToolOut; errorText?: string }

function stripViews(messages: UIMessage[]): UIMessage[] {
  return messages.slice(-12).map((m) => ({
    ...m,
    parts: m.parts.filter((p) => p.type !== "reasoning").map((p) => {
      const tp = p as unknown as ToolPart
      if (tp.type.startsWith("tool-") && tp.output && typeof tp.output === "object") {
        const { view: _v, ...rest } = tp.output; void _v
        return { ...p, output: rest } as typeof p
      }
      return p
    }),
  }))
}

export function useAskChat() {
  const [chat] = React.useState(() => new Chat<UIMessage>({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      credentials: "same-origin",
      prepareSendMessagesRequest: ({ messages, id }) => ({ body: { id, messages: stripViews(messages) } }),
      // If the server session is missing or expired, re-open it with the passcode this tab unlocked with, then retry once.
      fetch: async (input, init) => {
        const res = await fetch(input, init)
        if (res.status !== 401) return res
        const p = sessionStorage.getItem(PASS_KEY)
        if (!p || !(await openAskSession(p))) return res
        return fetch(input, init)
      },
    }),
  }))
  return chat
}
export type AskChat = ReturnType<typeof useAskChat>

/* ---------- formatting ---------- */
const fmt = (v: unknown, f?: Fmt): string => {
  if (v === null || v === undefined || v === "") return "—"
  if (typeof v !== "number") return typeof v === "object" ? JSON.stringify(v) : String(v)
  switch (f) {
    case "inr": return inr(v)
    case "num": return num(v)
    case "pct": return `${v.toFixed(1)}%`
    case "x": return v.toFixed(2)
    default: return Number.isInteger(v) ? num(v) : String(v)
  }
}
const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"]
const FOLLOW = /\n?\s*FOLLOWUPS?:\s*(.+)\s*$/i
export function splitFollowups(text: string): { body: string; followups: string[] } {
  const m = text.match(FOLLOW)
  if (!m) return { body: text.replace(/\n?\s*FOLLOWUPS?:?\s*$/i, ""), followups: [] }
  return { body: text.slice(0, m.index).trimEnd(), followups: m[1].split("|").map((s) => s.trim()).filter(Boolean).slice(0, 3) }
}

/* ---------- tiny markdown (bold, italics, lists, headings, paragraphs) ---------- */
function inline(s: string, key: string): React.ReactNode[] {
  const out: React.ReactNode[] = []
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`)/g
  let last = 0, i = 0, m: RegExpExecArray | null
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(s.slice(last, m.index))
    const t = m[0]
    if (t.startsWith("**")) out.push(<strong key={key + i++} className="font-semibold">{t.slice(2, -2)}</strong>)
    else if (t.startsWith("`")) out.push(<code key={key + i++} className="rounded bg-muted px-1 text-[0.85em]">{t.slice(1, -1)}</code>)
    else out.push(<em key={key + i++}>{t.slice(1, -1)}</em>)
    last = m.index + t.length
  }
  if (last < s.length) out.push(s.slice(last))
  return out
}
function Markdown({ text }: { text: string }) {
  const lines = text.split("\n")
  const blocks: React.ReactNode[] = []
  let list: { ordered: boolean; items: string[] } | null = null
  let para: string[] = []
  const flushPara = () => { if (para.length) { blocks.push(<p key={"p" + blocks.length} className="leading-relaxed">{inline(para.join(" "), "p" + blocks.length)}</p>); para = [] } }
  const flushList = () => {
    if (!list) return
    const L = list.ordered ? "ol" : "ul"
    blocks.push(<L key={"l" + blocks.length} className={cn("flex flex-col gap-1 pl-5", list.ordered ? "list-decimal" : "list-disc")}>{list.items.map((it, i) => <li key={i} className="leading-relaxed">{inline(it, "li" + i)}</li>)}</L>)
    list = null
  }
  for (const raw of lines) {
    const l = raw.trimEnd()
    const ul = l.match(/^\s*[-*•]\s+(.*)$/), ol = l.match(/^\s*\d+[.)]\s+(.*)$/), h = l.match(/^#{1,4}\s+(.*)$/)
    if (ul || ol) { flushPara(); const ordered = Boolean(ol); if (!list || list.ordered !== ordered) { flushList(); list = { ordered, items: [] } } list.items.push((ul || ol)![1]); continue }
    if (h) { flushPara(); flushList(); blocks.push(<p key={"h" + blocks.length} className="font-semibold">{inline(h[1], "h" + blocks.length)}</p>); continue }
    if (!l.trim()) { flushPara(); flushList(); continue }
    if (list && /^\s{2,}/.test(raw)) { list.items[list.items.length - 1] += " " + l.trim(); continue }
    flushList(); para.push(l.trim())
  }
  flushPara(); flushList()
  return <div className="flex flex-col gap-2 text-sm">{blocks}</div>
}

/* ---------- generative UI ---------- */
function ViewChart({ c }: { c: NonNullable<View["chart"]> }) {
  const cfg = Object.fromEntries(c.series.map((s, i) => [s.key, { label: s.label, color: COLORS[i % COLORS.length] }])) as ChartConfig
  const tick = (v: unknown) => (c.format === "inr" ? inr(Number(v)) : c.format === "pct" ? `${v}%` : String(v))
  const many = c.data.length > 6
  const common = (
    <>
      <CartesianGrid vertical={false} />
      <XAxis dataKey={c.x} tickLine={false} axisLine={false} minTickGap={12} interval={many ? "preserveStartEnd" : 0} tickFormatter={(v) => String(v).length > 14 ? String(v).slice(0, 13) + "…" : String(v)} fontSize={11} />
      <YAxis tickLine={false} axisLine={false} width={52} tickFormatter={tick} fontSize={11} />
      <ChartTooltip content={<ChartTooltipContent />} />
      {c.series.length > 1 && <ChartLegend content={<ChartLegendContent />} />}
    </>
  )
  return (
    <div className="flex flex-col gap-1">
      {c.title && <p className="text-xs font-medium text-muted-foreground">{c.title}</p>}
      <ChartContainer config={cfg} className="aspect-auto h-52 w-full">
        {c.kind === "line" ? (
          <LineChart data={c.data} margin={{ left: 0, right: 8, top: 4 }}>
            {common}
            {c.series.map((s) => <Line key={s.key} dataKey={s.key} type="monotone" stroke={`var(--color-${s.key})`} strokeWidth={2} dot={false} />)}
          </LineChart>
        ) : (
          <BarChart data={c.data} margin={{ left: 0, right: 8, top: 4 }}>
            {common}
            {c.series.map((s) => <Bar key={s.key} dataKey={s.key} fill={`var(--color-${s.key})`} radius={4} />)}
          </BarChart>
        )}
      </ChartContainer>
    </div>
  )
}
function ViewTable({ t }: { t: NonNullable<View["table"]> }) {
  const [all, setAll] = React.useState(false)
  const rows = all ? t.rows : t.rows.slice(0, 8)
  return (
    <div className="flex flex-col gap-1">
      {t.title && <p className="text-xs font-medium text-muted-foreground">{t.title}</p>}
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-xs">
          <thead className="bg-muted/50"><tr>{t.columns.map((c) => <th key={c.key} className={cn("px-2 py-1.5 text-left font-medium whitespace-nowrap", c.format && c.format !== "text" && "text-right")}>{c.label}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i} className="border-t">{t.columns.map((c) => <td key={c.key} className={cn("px-2 py-1.5 align-top", c.format && c.format !== "text" ? "text-right tabular-nums whitespace-nowrap" : "min-w-32")}>{fmt(r[c.key], c.format)}</td>)}</tr>)}</tbody>
        </table>
      </div>
      {t.rows.length > 8 && <button type="button" className="self-start text-xs text-muted-foreground underline" onClick={() => setAll(!all)}>{all ? "Show fewer" : `Show all ${t.rows.length} rows`}</button>}
    </div>
  )
}
export function ViewBlock({ v }: { v: View }) {
  return (
    <div className="flex flex-col gap-3">
      {v.kpis && v.kpis.length > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {v.kpis.map((k) => (
            <div key={k.label} className="flex flex-col gap-0.5 rounded-lg border bg-card p-2.5">
              <span className="text-[11px] text-muted-foreground">{k.label}</span>
              <span className="text-lg font-semibold tabular-nums">{k.value}</span>
              {k.delta !== undefined && <Delta value={k.delta ?? null} goodUp={k.goodUp} suffix="vs before" />}
              {k.sub && <span className="text-[11px] text-muted-foreground">{k.sub}</span>}
            </div>
          ))}
        </div>
      )}
      {v.chart && v.chart.data.length > 0 && <ViewChart c={v.chart} />}
      {v.table && v.table.rows.length > 0 && <ViewTable t={v.table} />}
    </div>
  )
}

const describeInput = (i?: Record<string, unknown>) => {
  if (!i) return ""
  const bits: string[] = []
  if (i.range) bits.push(i.range === "365" ? "12 months" : `${i.range} days`)
  if (i.window) bits.push(`${i.window} days`)
  for (const k of ["breakdown", "view", "topic", "brand", "credit", "op"]) if (i[k]) bits.push(String(i[k]))
  return bits.join(" · ")
}

function ToolStep({ p }: { p: ToolPart }) {
  const name = p.type.slice(5)
  const running = p.state === "input-streaming" || p.state === "input-available"
  const failed = p.state === "output-error" || Boolean(p.output?.error)
  return (
    <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
      {running ? <LoaderCircleIcon className="size-3.5 shrink-0 animate-spin text-primary" /> : failed ? <CircleAlertIcon className="size-3.5 shrink-0 text-amber-600" /> : <CheckIcon className="size-3.5 shrink-0 text-emerald-600" />}
      <span className={cn("shrink-0 font-medium text-foreground", running && "animate-pulse")}>{STEP_LABEL[name] ?? name}{running ? "…" : ""}</span>
      {describeInput(p.input) && <span className="truncate">{describeInput(p.input)}</span>}
      {failed && <span className="truncate text-amber-700 dark:text-amber-300">{p.output?.error ?? p.errorText ?? "failed"}</span>}
    </div>
  )
}

function Evidence({ parts }: { parts: ToolPart[] }) {
  const [more, setMore] = React.useState(false)
  const items = parts.filter((p) => p.output?.view && !p.output.error)
  if (!items.length) return null
  const shown = more ? items : items.slice(0, 2)
  return (
    <div className="flex flex-col gap-3">
      {shown.map((p) => (
        <Card key={p.toolCallId} size="sm" className="gap-2">
          <CardContent className="flex flex-col gap-2">
            {p.output!.view!.title && <p className="text-xs font-medium text-muted-foreground">{p.output!.view!.title}</p>}
            <ViewBlock v={p.output!.view!} />
            <p className="text-[11px] text-muted-foreground">Source: {p.output!.source} · As of {p.output!.asOf}{p.output!.period ? ` · ${p.output!.period}` : ""}</p>
          </CardContent>
        </Card>
      ))}
      {items.length > 2 && <button type="button" className="self-start text-xs text-muted-foreground underline" onClick={() => setMore(!more)}>{more ? "Show fewer charts" : `Show ${items.length - 2} more chart${items.length - 2 > 1 ? "s" : ""} and tables`}</button>}
    </div>
  )
}

/* ---------- export / copy ---------- */
function messageText(m: UIMessage) {
  const text = m.parts.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("\n")
  return m.role === "assistant" ? splitFollowups(text).body : text
}
function messageSources(m: UIMessage) {
  return m.parts.filter((p) => p.type.startsWith("tool-")).map((p) => (p as unknown as ToolPart).output).filter(Boolean).map((o) => `- ${o!.source} (as of ${o!.asOf}${o!.period ? `; ${o!.period}` : ""})`)
}
function viewMd(v?: View) {
  if (!v) return ""
  let s = ""
  if (v.kpis) s += v.kpis.map((k) => `- ${k.label}: ${k.value}${k.delta != null ? ` (${k.delta > 0 ? "+" : ""}${k.delta.toFixed(0)}%)` : ""}`).join("\n") + "\n"
  if (v.table) s += "\n| " + v.table.columns.map((c) => c.label).join(" | ") + " |\n|" + v.table.columns.map(() => "---").join("|") + "|\n" + v.table.rows.map((r) => "| " + v.table!.columns.map((c) => fmt(r[c.key], c.format).replace(/\|/g, "/")).join(" | ") + " |").join("\n") + "\n"
  return s
}
function exportMd(messages: UIMessage[]) {
  const out = [`# Ask Dorje — ${new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST`, ""]
  for (const m of messages) {
    if (m.role === "user") out.push(`## Q: ${messageText(m)}`, "")
    else {
      out.push(messageText(m), "")
      for (const p of m.parts) if (p.type.startsWith("tool-")) { const o = (p as unknown as ToolPart).output; if (o?.view) out.push(viewMd(o.view)) }
      const src = messageSources(m); if (src.length) out.push("Sources:", ...src, "")
    }
  }
  const url = URL.createObjectURL(new Blob([out.join("\n")], { type: "text/markdown;charset=utf-8" }))
  const a = document.createElement("a"); a.href = url; a.download = `ask-dorje-${new Date().toISOString().slice(0, 10)}.md`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function CopyBtn({ m }: { m: UIMessage }) {
  const [ok, setOk] = React.useState(false)
  return (
    <Button variant="ghost" size="xs" onPress={async () => { const src = messageSources(m); await navigator.clipboard.writeText(messageText(m) + (src.length ? "\n\nSources:\n" + src.join("\n") : "")); setOk(true); setTimeout(() => setOk(false), 1500) }}>
      {ok ? <CheckIcon /> : <CopyIcon />} {ok ? "Copied" : "Copy"}
    </Button>
  )
}

/* ---------- is the Ask Dorje server available? (not under `pnpm dev`, or before DASH_PASSCODE/SESSION_SECRET/AI Gateway are set) ---------- */
function useAskAvailable() {
  const [state, setState] = React.useState<"checking" | "ok" | "off" | "unconfigured">("checking")
  React.useEffect(() => {
    let live = true
    fetch("/api/session", { credentials: "same-origin", cache: "no-store" })
      .then(async (r) => {
        if (!r.ok || !(r.headers.get("content-type") || "").includes("json")) return "off" as const
        const j = (await r.json()) as { configured?: boolean }
        return j.configured ? ("ok" as const) : ("unconfigured" as const)
      })
      .catch(() => "off" as const)
      .then((s) => { if (live) setState(s) })
    return () => { live = false }
  }, [])
  return state
}

/* ---------- the chat ---------- */
export function AskChatView({ chat, compact = false, autoFocus = false }: { chat: AskChat; compact?: boolean; autoFocus?: boolean }) {
  const { messages, sendMessage, status, error, stop, regenerate, setMessages, clearError } = useChat({ chat, throttle: 50 })
  const [input, setInput] = React.useState("")
  const endRef = React.useRef<HTMLDivElement>(null)
  const busy = status === "submitted" || status === "streaming"
  const avail = useAskAvailable()

  React.useEffect(() => { endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" }) }, [messages, status])


  const ask = (q: string) => { const t = q.trim(); if (!t || busy) return; setInput(""); void sendMessage({ text: t }) }
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant")
  const followups = lastAssistant && !busy ? splitFollowups(lastAssistant.parts.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("\n")).followups : []
  const errMsg = error ? (() => { try { const j = JSON.parse(error.message); return j.error ?? error.message } catch { return error.message } })() : ""

  return (
    <div className={cn("flex min-h-0 flex-1 flex-col", compact ? "gap-3" : "gap-4")}>
      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className={cn("flex flex-col gap-4", compact ? "pt-2" : "pt-6")}>
            <div className="flex flex-col gap-1">
              <h2 className="flex items-center gap-2 text-lg font-semibold"><SparklesIcon className="size-5 text-primary" /> Ask Dorje</h2>
              <p className="text-sm text-muted-foreground">Ask anything about sales, ads, customers, carts, SEO or competitors. Answers come only from this dashboard&apos;s live data (Shopify, Meta, Zoko, public competitor checks), with the source and time under every number. Read-only: it can&apos;t change anything. Google Ads and Amazon aren&apos;t connected yet.</p>
            </div>
            {(avail === "off" || avail === "unconfigured") && (
              <Card size="sm" className="border-amber-500/40">
                <CardContent className="flex items-start gap-2 text-sm">
                  <CircleAlertIcon className="mt-0.5 size-4 shrink-0 text-amber-600" />
                  <span>{avail === "off"
                    ? "Ask Dorje is switched off in this copy: the chat server isn't running here (for example under `pnpm dev`). The rest of the dashboard works. To try it locally run `pnpm preview` (mock answers), or deploy to Vercel with AI Gateway (docs/SETUP.md)."
                    : "Ask Dorje isn't set up on this server yet: DASH_PASSCODE and SESSION_SECRET need to be set, and AI Gateway needs a card on the Vercel account (docs/SETUP.md)."}</span>
                </CardContent>
              </Card>
            )}
            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Try one</span>
              <div className="flex flex-wrap gap-2">
                {STARTERS.map((q) => <Button key={q} variant="outline" size="sm" className="h-auto py-1.5 text-left whitespace-normal" onPress={() => ask(q)}>{q}</Button>)}
              </div>
            </div>
          </div>
        )}
        {messages.map((m, mi) => m.role === "user" ? (
          <div key={m.id} className="ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm text-primary-foreground">{messageText(m)}</div>
        ) : (
          <div key={m.id} className="flex flex-col gap-3">
            {(() => {
              const tools = m.parts.filter((p) => p.type.startsWith("tool-")) as unknown as ToolPart[]
              const body = splitFollowups(m.parts.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("\n\n")).body
              const live = busy && mi === messages.length - 1
              return (
                <>
                  {tools.length > 0 && (
                    <div className="flex flex-col gap-1.5 rounded-lg border border-dashed px-3 py-2">
                      <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{live && !body ? "Working on it" : `Checked ${tools.length} data source${tools.length > 1 ? "s" : ""}`}</span>
                      {tools.map((p) => <ToolStep key={p.toolCallId} p={p} />)}
                    </div>
                  )}
                  {body.trim() && <Markdown text={body} />}
                  {!live && <Evidence parts={tools} />}
                  {!live && body.trim() && <div className="-ml-2 flex items-center gap-1"><CopyBtn m={m} /></div>}
                </>
              )
            })()}
          </div>
        ))}
        {status === "submitted" && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><LoaderCircleIcon className="size-3.5 animate-spin text-primary" /> Thinking…</div>
        )}
        {error && (
          <Card size="sm" className="border-amber-500/40">
            <CardContent className="flex flex-col gap-2 text-sm">
              <span className="flex items-center gap-2"><CircleAlertIcon className="size-4 text-amber-600" />
                {/unauthori[sz]ed/i.test(errMsg) ? "Your session ended. Lock and unlock the dashboard with the passcode, then ask again." : errMsg || "Something went wrong."}
              </span>
              <Button size="sm" variant="outline" className="self-start" onPress={() => { clearError(); void regenerate() }}><RotateCcwIcon /> Try again</Button>
            </CardContent>
          </Card>
        )}
        {followups.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {followups.map((q) => <Button key={q} variant="secondary" size="sm" className="h-auto py-1.5 text-left whitespace-normal" onPress={() => ask(q)}>{q}</Button>)}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="flex flex-col gap-2" onSubmit={(e) => { e.preventDefault(); ask(input) }}>
        <div className="flex items-end gap-2 rounded-xl border bg-card p-2 focus-within:ring-3 focus-within:ring-ring/50">
          <textarea
            aria-label="Ask a question" placeholder="Ask about revenue, ads, carts, competitors…" rows={1} maxLength={2000} autoFocus={autoFocus}
            value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(input) } }}
            className="max-h-40 min-h-9 flex-1 resize-none bg-transparent px-1.5 py-1.5 text-base outline-none placeholder:text-muted-foreground md:text-sm"
          />
          {busy
            ? <Button type="button" size="icon-sm" variant="outline" aria-label="Stop" onPress={() => void stop()}><SquareIcon /></Button>
            : <Button type="submit" size="icon-sm" aria-label="Send" isDisabled={!input.trim()}><ArrowUpIcon /></Button>}
        </div>
        <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
          <span>Answers use dashboard data only and can be wrong; check the sources shown. Estimates are labelled.</span>
          {messages.length > 0 && (
            <span className="flex shrink-0 gap-1">
              <Button variant="ghost" size="xs" onPress={() => exportMd(messages)} isDisabled={busy}><DownloadIcon /> Export</Button>
              <Button variant="ghost" size="xs" onPress={() => { void stop(); setMessages([]); clearError() }}><RotateCcwIcon /> New chat</Button>
            </span>
          )}
        </div>
      </form>
    </div>
  )
}

export function AskTab({ chat }: { chat: AskChat }) {
  return (
    <div className="mx-auto flex h-[calc(100svh-15rem)] min-h-[32rem] w-full max-w-3xl flex-col">
      <AskChatView chat={chat} />
    </div>
  )
}

export function AskFloating({ chat, hidden }: { chat: AskChat; hidden: boolean }) {
  const [open, setOpen] = React.useState(false)
  React.useEffect(() => {
    if (!open) return
    const k = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false) }
    window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k)
  }, [open])
  if (hidden) return null
  return (
    <>
      {!open && (
        <Button className="fixed right-4 bottom-4 z-40 h-11 rounded-full px-4 shadow-lg" onPress={() => setOpen(true)} aria-label="Ask Dorje">
          <MessageCircleIcon /> Ask Dorje
        </Button>
      )}
      {open && (
        <div role="dialog" aria-label="Ask Dorje" className="fixed inset-0 z-50 flex flex-col bg-background p-3 sm:inset-auto sm:right-4 sm:bottom-4 sm:h-[min(44rem,calc(100svh-2rem))] sm:w-[28rem] sm:rounded-2xl sm:border sm:shadow-2xl">
          <div className="flex items-center justify-between pb-2">
            <span className="flex items-center gap-2 text-sm font-semibold"><SparklesIcon className="size-4 text-primary" /> Ask Dorje <Badge variant="outline">Read-only</Badge></span>
            <Button variant="ghost" size="icon-sm" aria-label="Close" onPress={() => setOpen(false)}><XIcon /></Button>
          </div>
          <AskChatView chat={chat} compact autoFocus />
        </div>
      )}
    </>
  )
}
