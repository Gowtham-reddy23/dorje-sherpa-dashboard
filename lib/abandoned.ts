/** Abandoned-checkout deep-dive, built by refresh/build_abandoned.py (aggregates only). */
export type ABRow = { k: string; n: number; value: number; rec: number; recPct: number }
export type ABWin = {
  days: number; since: string; until: string; n: number; people: number; value: number; avg: number; median: number
  rec: number; recPct: number; recValue: number; lost: number; perMonthN: number; perMonthLost: number; junk: number
  under399: number; under399Pct: number; under399FeePct: number; under399RecPct: number; over399FeePct: number; over399RecPct: number
  bands: ABRow[]; products: { k: string; n: number; value: number; rec: number; oos: number; sub: number; recPct: number }[]
  variants: { p: string; v: string; n: number }[]; oosCheckouts: number; oosPct: number; subCheckouts: number; subPct: number; subRecPct: number
  newRet: ABRow[]; contact: ABRow[]; emailState: ABRow[]; zoko: number; zokoPct: number; phonePct: number; emailPct: number; mail10hPct: number
  shipCharged: number; shipChargedPct: number; shipRecPct: number; shipFreeRecPct: number; near499: number; near499Pct: number
  withDiscount: number; rzpPct: number; codPct: number; lag: { k: string; n: number }[]; dow: ABRow[]; hour: ABRow[]; states: ABRow[]
}
export type ABDeep = {
  asOf: string; w30: ABWin; w90: ABWin; aov30: number
  weeks: { w: string; n: number; rec: number; recPct: number; value: number; rzpPct: number; carts: number; checkouts: number; completed: number; cartToOrder: number; partial: boolean }[]
  switch?: { date: string; pre: Record<string, number>; post: Record<string, number> }
  funnel30: { sessions: number; carts: number; checkouts: number; completed: number; cartNoOrder: number }
  zokoFlow?: { checkedAt: string; checked: number; gotReminder: number; templates: [string, number][]; sends: number; timing: [string, number][]; medianFirstH: number; stepsPer: [number, number][]; status: [string, number][]; failedPct: number; seenPct: number; deliveredPct: number; fail131049: number; recovered: number }
  opp: { baseN: number; avg: number; cur: number; targets: { to: number; extraOrders: number; extraRevenue: number }[]; note: string }
  findings: { title: string; detail: string; tone: string | null }[]
  actions: { n: number; who: string; what: string; copy: string; impact: string; basis: string }[]
  totalEst: { low: number; high: number; note: string }
}
export const getAB = (d: unknown) => (d as { abDeep?: ABDeep }).abDeep
