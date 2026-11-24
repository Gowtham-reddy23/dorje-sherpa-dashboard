// Local test server: serves the static export (out/) and the bundled API functions (api/*.mjs) like Vercel does.
// ASK_MOCK=1 uses a scripted mock model (no AI Gateway credentials needed) to test the UI, tools, auth and streaming end to end.
import { createServer } from "node:http"
import { readFileSync, existsSync, statSync } from "node:fs"
import { join, extname } from "node:path"
import { randomBytes } from "node:crypto"
import { simulateReadableStream } from "ai"
import { MockLanguageModelV4 } from "ai/test"

const ROOT = process.cwd(), OUT = join(ROOT, "out"), PORT = Number(process.env.PORT || 3311)
// Load .env (real environment variables win). Never print values.
if (existsSync(join(ROOT, ".env"))) for (const line of readFileSync(join(ROOT, ".env"), "utf8").split(/\r?\n/)) {
  const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/)
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, "")
}
// Passcode: DASH_PASSCODE from your shell/.env; with sample data the demo passcode is used (see scripts/prepare-data.mjs).
process.env.DASH_PASSCODE ||= existsSync(join(ROOT, "data/dashboard.json")) ? "" : "sherpa-demo"
if (!process.env.DASH_PASSCODE) throw new Error("Set DASH_PASSCODE (the passcode your real data was encrypted with)")
process.env.SESSION_SECRET ||= randomBytes(32).toString("hex")
process.env.ASK_DATA_ORIGIN ||= `http://127.0.0.1:${PORT}`

if (process.env.ASK_MOCK) {
  const usage = { inputTokens: { total: 9000, noCache: 9000, cacheRead: undefined, cacheWrite: undefined }, outputTokens: { total: 300, text: 300, reasoning: undefined } }
  const text = (t: string) => {
    const parts = t.match(/[\s\S]{1,24}/g) || []
    return [{ type: "text-start", id: "t" }, ...parts.map((delta) => ({ type: "text-delta", id: "t", delta })), { type: "text-end", id: "t" }, { type: "finish", finishReason: { unified: "stop", raw: undefined }, usage }]
  }
  ;(globalThis as any).__ASK_TEST_MODEL = new MockLanguageModelV4({
    doStream: async ({ prompt }: any) => {
      const tools = prompt.filter((m: any) => m.role === "tool").length
      const q = JSON.stringify(prompt.filter((m: any) => m.role === "user").slice(-1))
      const call = (name: string, input: unknown) => ({ type: "tool-call", toolCallId: "c" + Math.random().toString(36).slice(2), toolName: name, input: JSON.stringify(input) })
      let chunks: any[]
      if (tools === 0 || (prompt[prompt.length - 1]?.role === "user")) {
        const calls = /vahdam/i.test(q) ? [call("getCompetitors", { topic: "prices", brand: "vahdam" })]
          : /campaign/i.test(q) ? [call("getMetaAds", { view: "campaigns", range: "30" })]
          : /abandon/i.test(q) ? [call("getAbandoned", { window: "30" })]
          : /this week/i.test(q) ? [call("getDecisions", {})]
          : [call("getKpis", { range: "7" }), call("getRevenue", { breakdown: "channel", range: "7" })]
        chunks = [...calls, { type: "finish", finishReason: { unified: "tool-calls", raw: undefined }, usage }]
      } else {
        chunks = text("**(Mock answer — local UI test, no model.)** Revenue last 7 days was **₹1.10L**, up 3% (source: getKpis, as of 13 Nov 2026, 12:03 IST).\n\n- Orders 142 vs 146\n- New customers 73 vs 72\n\nFOLLOWUPS: Which channel grew? | How is Meta doing? | What should we fix first?")
      }
      return { stream: simulateReadableStream({ chunks, chunkDelayInMs: 30 }) }
    },
  })
}

const chat = await import(join(ROOT, "api/chat.mjs")), session = await import(join(ROOT, "api/session.mjs"))
const TYPES: Record<string, string> = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".txt": "text/plain", ".woff2": "font/woff2" }

createServer(async (req, res) => {
  const url = new URL(req.url!, `http://${req.headers.host}`)
  if (url.pathname.startsWith("/api/")) {
    const mod = url.pathname === "/api/chat" ? chat : url.pathname === "/api/session" ? session : null
    const h = mod?.[req.method!]
    if (!h) { res.writeHead(405).end(); return }
    const body = req.method === "GET" || req.method === "HEAD" ? undefined : await new Promise<Buffer>((r) => { const c: Buffer[] = []; req.on("data", (d) => c.push(d)); req.on("end", () => r(Buffer.concat(c))) })
    const r: Response = await h(new Request(url, { method: req.method, headers: req.headers as any, body: body as any }))
    const headers: Record<string, string> = {}; r.headers.forEach((v, k) => { headers[k] = v })
    res.writeHead(r.status, headers)
    if (r.body) { const rd = r.body.getReader(); for (;;) { const { done, value } = await rd.read(); if (done) break; res.write(value) } }
    res.end(); return
  }
  let p = join(OUT, decodeURIComponent(url.pathname))
  if (existsSync(p) && statSync(p).isDirectory()) p = join(p, "index.html")
  if (!existsSync(p) && existsSync(p + ".html")) p += ".html"
  if (!existsSync(p)) { res.writeHead(404).end("not found"); return }
  res.writeHead(200, { "content-type": TYPES[extname(p)] || "application/octet-stream", "cache-control": "no-store" }).end(readFileSync(p))
}).listen(PORT, () => console.log(`dev server http://127.0.0.1:${PORT} mock=${Boolean(process.env.ASK_MOCK)}`))
