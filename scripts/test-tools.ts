import { readFileSync } from "node:fs"
import { makeTools } from "../server/tools"
const d = JSON.parse(readFileSync("data/dashboard.json", "utf8"))
const t = makeTools(d) as any
const run = async (name: string, input: any) => { const o = await t[name].execute(input, { toolCallId: "x", messages: [] }); return o }
const out: any = {}
out.kpis7 = (await run("getKpis", { range: "7" })).data
out.kpis30 = (await run("getKpis", { range: "30" })).data
for (const b of ["trend", "channel", "campaign", "productGroup", "customerType", "topProducts", "productMix"]) out["rev_" + b] = (await run("getRevenue", { breakdown: b, range: "30" })).data
for (const v of ["campaigns", "formats", "placements", "summary"]) out["meta_" + v] = (await run("getMetaAds", { view: v, range: "30" })).data
out.attr = (await run("getAttribution", { range: "30" })).data
out.ab = (await run("getAbandoned", {})).data
for (const n of ["getRetention", "getWhatsApp", "getSeoGeo", "getInventoryAlerts", "getDecisions", "getDataStatus"]) out[n] = (await run(n, {})).data
for (const tp of ["summary", "prices", "teabags", "offers", "ads", "adTypes", "search", "amazon", "actions"]) out["comp_" + tp] = await run("getCompetitors", { topic: tp, brand: tp === "ads" ? "vahdam" : undefined })
out.compute = (await run("compute", { op: "pct_change", values: [{ label: "a", value: 155000 }, { label: "b", value: 108000 }] })).data
const sizes = Object.fromEntries(Object.entries(out).map(([k, v]) => [k, JSON.stringify(v).length]))
console.log(JSON.stringify(sizes))
console.log(JSON.stringify(out.kpis30), "\n", JSON.stringify(out.kpis7))
console.log(JSON.stringify(out.meta_summary), "\n", JSON.stringify(out.rev_channel).slice(0, 600), "\n", JSON.stringify(out.ab).slice(0, 500))
console.log(JSON.stringify(out.compute))
