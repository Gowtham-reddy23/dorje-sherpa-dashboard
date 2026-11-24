import type { Dash } from "./dash"

export type AttrRow = [string, number, number, number, number, number, number, number, number, number, number, number, number, number]
export type Attr = {
  keys: string[]; rows: AttrRow[]
  dims: { ch: string[]; camp: string[]; state: string[]; grp: string[]; pack: string[]; sales: string[]; pay: string[] }
  codes: [string, number][]; metaMonthly: [string, string, number, number, number][]; cancelled: number; total: number
}
export const R = { date: 0, rev: 1, first: 2, last: 3, campLast: 4, new: 5, disc: 6, state: 7, grp: 8, pack: 9, sales: 10, pay: 11, journey: 12, campFirst: 13 } as const

export type Filters = {
  channel: number | null; model: "last" | "first"; grp: number | null; pack: number | null
  cust: "all" | "new" | "ret"; disc: "all" | "code" | "bogo" | "any" | "none"; state: number | null; pay: number | null
}
export const EMPTY: Filters = { channel: null, model: "last", grp: null, pack: null, cust: "all", disc: "all", state: null, pay: null }
export const activeCount = (f: Filters) =>
  [f.channel, f.grp, f.pack, f.state, f.pay].filter((x) => x !== null).length + (f.cust !== "all" ? 1 : 0) + (f.disc !== "all" ? 1 : 0)

const addDays = (iso: string, n: number) => { const d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10) }
/** [from, to] inclusive ISO dates for the last `range` days ending at endDate, and the period before it. */
export function dateWindow(end: string, range: number) {
  return { from: addDays(end, -(range - 1)), to: end, pFrom: addDays(end, -(2 * range - 1)), pTo: addDays(end, -range) }
}

export function match(r: AttrRow, f: Filters, ignore: (keyof Filters)[] = []) {
  const ig = (k: keyof Filters) => ignore.includes(k)
  if (!ig("channel") && f.channel !== null && r[f.model === "last" ? R.last : R.first] !== f.channel) return false
  if (!ig("grp") && f.grp !== null && !(r[R.grp] & (1 << f.grp))) return false
  if (!ig("pack") && f.pack !== null && !(r[R.pack] & (1 << f.pack))) return false
  if (!ig("cust") && f.cust === "new" && r[R.new] !== 1) return false
  if (!ig("cust") && f.cust === "ret" && r[R.new] !== 0) return false
  if (!ig("disc")) {
    const d = r[R.disc]
    if (f.disc === "code" && !(d & 1)) return false
    if (f.disc === "bogo" && !(d & 2)) return false
    if (f.disc === "any" && !d) return false
    if (f.disc === "none" && d) return false
  }
  if (!ig("state") && f.state !== null && r[R.state] !== f.state) return false
  if (!ig("pay") && f.pay !== null && r[R.pay] !== f.pay) return false
  return true
}

export function select(a: Attr, from: string, to: string, f: Filters, ignore: (keyof Filters)[] = []) {
  return a.rows.filter((r) => r[R.date] >= from && r[R.date] <= to && match(r, f, ignore))
}

export type Agg = { orders: number; rev: number; aov: number; newC: number; ret: number; newPct: number; journey: number }
export function agg(rows: AttrRow[]): Agg {
  let rev = 0, newC = 0, ret = 0, j = 0
  for (const r of rows) { rev += r[R.rev]; if (r[R.new] === 1) newC++; else if (r[R.new] === 0) ret++; j += r[R.journey] }
  const n = rows.length
  return { orders: n, rev, aov: n ? rev / n : 0, newC, ret, newPct: n ? (newC / n) * 100 : 0, journey: n ? (j / n) * 100 : 0 }
}

/** Group rows by a key function; returns sorted by revenue desc. */
export function groupBy(rows: AttrRow[], key: (r: AttrRow) => number | number[], label: (i: number) => string) {
  const m = new Map<number, { orders: number; rev: number; newC: number; disc: number }>()
  for (const r of rows) {
    const ks = key(r); for (const k of Array.isArray(ks) ? ks : [ks]) {
      if (k < 0) continue
      const x = m.get(k) ?? { orders: 0, rev: 0, newC: 0, disc: 0 }
      x.orders++; x.rev += r[R.rev]; if (r[R.new] === 1) x.newC++; if (r[R.disc]) x.disc++
      m.set(k, x)
    }
  }
  return [...m.entries()].map(([k, v]) => ({ key: k, name: label(k), ...v, aov: v.orders ? v.rev / v.orders : 0, newPct: v.orders ? (v.newC / v.orders) * 100 : 0 })).sort((a, b) => b.rev - a.rev)
}
export const bits = (mask: number) => { const out: number[] = []; for (let i = 0; i < 31; i++) if (mask & (1 << i)) out.push(i); return out }

export const UNKNOWN = ["Direct", "Unknown source", "Unknown (no visit data)"]

/** Meta-reported purchases/value per campaign for months overlapping [from, to]. */
export function metaReported(a: Attr, from: string, to: string) {
  const m = new Map<string, { spend: number; purchases: number; value: number }>()
  for (const [mon, name, spend, p, v] of a.metaMonthly) {
    if (mon < from.slice(0, 7) || mon > to.slice(0, 7)) continue
    const x = m.get(name) ?? { spend: 0, purchases: 0, value: 0 }
    x.spend += spend; x.purchases += p; x.value += v; m.set(name, x)
  }
  return m
}
/** Month-aligned window so Meta monthly numbers and Shopify orders cover the same days. */
export function monthWindow(a: Attr, end: string, range: number) {
  const months = Math.max(1, Math.round(range / 30))
  const e = new Date(end + "T00:00:00Z"); const lastFull = new Date(Date.UTC(e.getUTCFullYear(), e.getUTCMonth(), 0))
  const full = e.getUTCDate() === new Date(Date.UTC(e.getUTCFullYear(), e.getUTCMonth() + 1, 0)).getUTCDate()
  const toD = full ? e : lastFull
  const fromD = new Date(Date.UTC(toD.getUTCFullYear(), toD.getUTCMonth() - months + 1, 1))
  return { from: fromD.toISOString().slice(0, 10), to: toD.toISOString().slice(0, 10), months }
}

export function toCsv(cols: { key: string; label: string }[], rows: Record<string, unknown>[]) {
  const esc = (v: unknown) => { const s = v === null || v === undefined ? "" : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s }
  return [cols.map((c) => esc(c.label)).join(","), ...rows.map((r) => cols.map((c) => esc(r[c.key])).join(","))].join("\n")
}
export function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob(["\ufeff" + text], { type: "text/csv;charset=utf-8" }))
  const a = document.createElement("a"); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
export const getAttr = (d: Dash) => (d as Dash & { attr?: Attr }).attr
