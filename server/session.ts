import { checkPasscode, clearCookie, configured, ip, json, limited, makeSession, sameOrigin, setCookie, verify } from "./auth"

/** GET: is the browser signed in for Ask Dorje? POST {passcode}: sign in (sets an HMAC-signed httpOnly cookie). DELETE: sign out. */
export async function GET(req: Request) {
  return json({ ok: Boolean(verify(req)), configured: configured() })
}
export async function POST(req: Request) {
  if (!configured()) return json({ ok: false, error: "not configured" }, 503)
  if (!sameOrigin(req)) return json({ ok: false }, 403)
  if (limited("p:" + ip(req), 10, 10 * 60 * 1000)) return json({ ok: false, error: "Too many attempts" }, 429)
  let p: unknown
  try { p = ((await req.json()) as { passcode?: unknown }).passcode } catch { return json({ ok: false }, 400) }
  if (!checkPasscode(p)) return json({ ok: false }, 401)
  const s = makeSession()
  return json({ ok: true }, 200, { "set-cookie": setCookie(req, s.value) })
}
export async function DELETE(req: Request) {
  return json({ ok: true }, 200, { "set-cookie": clearCookie(req) })
}
