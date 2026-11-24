import { createAgentUIStreamResponse, type UIMessage } from "ai"
import { json, limited, sameOrigin, verify, configured } from "./auth"
import { loadData } from "./data"
import { makeAgent } from "./agent"

export const maxDuration = 60

export async function POST(req: Request): Promise<Response> {
  if (!configured()) return json({ error: "Ask Dorje is not configured on the server." }, 503)
  const sid = verify(req)
  if (!sid) return json({ error: "Unauthorized" }, 401)
  if (!sameOrigin(req)) return json({ error: "Bad origin" }, 403)
  if (limited("s:" + sid, 15, 10 * 60 * 1000) || limited("g", 300, 60 * 60 * 1000)) return json({ error: "Too many questions in a short time. Please wait a few minutes." }, 429)

  const raw = await req.text()
  if (raw.length > 300_000) return json({ error: "Conversation too long. Start a new chat." }, 413)
  let body: { messages?: UIMessage[] }
  try { body = JSON.parse(raw) } catch { return json({ error: "Bad request" }, 400) }
  const msgs = Array.isArray(body.messages) ? body.messages.slice(-12) : []
  const last = msgs[msgs.length - 1]
  if (!last || last.role !== "user") return json({ error: "Bad request" }, 400)
  const text = last.parts?.filter((p) => p.type === "text").map((p) => (p as { text: string }).text).join("") ?? ""
  if (!text.trim() || text.length > 2000) return json({ error: "Question is empty or too long (max 2,000 characters)." }, 400)

  let data
  try { data = await loadData(req) } catch (e) {
    console.error("ask: data load failed", (e as Error).message)
    return json({ error: "Couldn't load the dashboard data. Try again shortly." }, 502)
  }
  const testModel = (globalThis as { __ASK_TEST_MODEL?: unknown }).__ASK_TEST_MODEL
  const agent = makeAgent(data, testModel as never)
  return createAgentUIStreamResponse({
    agent,
    uiMessages: msgs,
    abortSignal: req.signal,
    headers: { "cache-control": "no-store" },
    onStepEnd: ({ usage, toolCalls }) => {
      console.log("ask: step", JSON.stringify({ in: usage?.inputTokens, out: usage?.outputTokens, tools: toolCalls?.map((t) => t.toolName) }))
    },
    onError: (e: unknown) => {
      const m = e instanceof Error ? e.message : String(e)
      console.error("ask: stream error", m)
      if (/credit card|customer_verification/i.test(m)) return "Ask Dorje isn't switched on yet: the Vercel account needs a card on file for AI Gateway. Ask the admin to add it."
      if (/credit|insufficient|payment|budget/i.test(m)) return "The AI service is out of credits on the Vercel account (AI Gateway). Ask the admin to top up."
      if (/auth|oidc|api key|unauthor/i.test(m)) return "The AI service isn't authorised on the server yet (AI Gateway). Ask the admin."
      return "Something went wrong while answering. Please try again."
    },
  })
}
