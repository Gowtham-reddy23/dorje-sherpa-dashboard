/** Shared between the Ask Dorje server functions (server/) and the chat UI. */
export type Fmt = "inr" | "num" | "pct" | "x" | "text"
export type ViewKpi = { label: string; value: string; delta?: number | null; goodUp?: boolean; sub?: string }
export type ViewChart = {
  kind: "line" | "bar"
  title?: string
  x: string
  series: { key: string; label: string }[]
  data: Record<string, string | number | null>[]
  format?: Fmt
}
export type ViewTable = { title?: string; columns: { key: string; label: string; format?: Fmt }[]; rows: Record<string, string | number | null>[] }
export type View = { title?: string; kpis?: ViewKpi[]; chart?: ViewChart; table?: ViewTable }
export type ToolOut = {
  /** Where the numbers come from (human readable). */
  source: string
  /** When the underlying data was last refreshed (IST). */
  asOf: string
  period?: string
  data?: unknown
  notes?: string[]
  /** Rendered as cards/charts/tables in the chat; not sent back to the model. */
  view?: View
  error?: string
}

export const STEP_LABEL: Record<string, string> = {
  getDataStatus: "Checking which data sources are connected",
  getKpis: "Looking at the headline numbers",
  getRevenue: "Looking at revenue",
  getMetaAds: "Looking at Meta ads",
  getAttribution: "Checking which channels get credit",
  getAbandoned: "Looking at unfinished checkouts",
  getRetention: "Looking at repeat customers",
  getWhatsApp: "Looking at WhatsApp (Zoko)",
  getSeoGeo: "Checking SEO and AI-search visibility",
  getInventoryAlerts: "Checking stock and alerts",
  getCompetitors: "Looking at competitors",
  getDecisions: "Reading the open decisions and plan",
  compute: "Doing the maths",
}
