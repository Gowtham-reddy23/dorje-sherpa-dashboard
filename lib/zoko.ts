export type ZSeg = { buyers: number; revenue: number; orders: number; repeatRate: number; revPerBuyer: number }
export type Zoko = {
  asOf: string
  templates: {
    total: number; active: number; types: [string, number][]; languages: [string, number][]
    categories: [string, number, number][]
    abandoned: { id: string; active: boolean; type: string }[]; abandonedExists: boolean; abandonedActive: boolean
    lifecycle: Record<string, string[]>
  }
  customers: {
    total: number; fetched: number; complete: boolean; coveragePct: number; contactableNow: number; recency: [string, number][]
    newPerMonth: [string, number][]; newPerMonthNote: string; lastInboundMonth: [string, number][]; withPhone: number
  }
  join: {
    buyers: number; buyersWithPhone: number; reachable: number; reachablePct: number
    revenueReachable: number; revenueReachablePct: number; revenueAll: number; segments: Record<string, ZSeg>; note: string
  }
  messageSample: null | {
    contacts: number; messages: number; outgoing: number; checked: number; delivered: number; read: number; failed: number
    statuses: [string, number][]; repliedPct: number; tags: [string, number][]; tagged: number
    failReasons: [string, number][]; statusByType: Record<string, Record<string, number>>
    sources: [string, number][]; sentByType: [string, number][]; abandonedSent: number; abandonedLast: string | null; note: string
  }
  gaps: string[]
}
