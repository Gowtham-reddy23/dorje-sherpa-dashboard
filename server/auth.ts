import { createHmac, randomBytes, timingSafeEqual, createHash } from "node:crypto"

export const COOKIE = "dj_ask"
const TTL_S = 12 * 60 * 60

const b64u = (b: Buffer) => b.toString("base64url")
const secret = () => {
  const s = process.env.SESSION_SECRET?.trim()
  if (!s || s.length < 32) return null
  return s
}
export const configured = () => Boolean(secret() && process.env.DASH_PASSCODE)

export function checkPasscode(p: unknown): boolean {
  const want = process.env.DASH_PASSCODE?.trim()
  if (!want || typeof p !== "string" || p.length > 200) return false
  const a = createHash("sha256").update(p.trim()).digest(), b = createHash("sha256").update(want).digest()
  return timingSafeEqual(a, b)
}

function sign(payload: string) {
  return b64u(createHmac("sha256", secret()!).update(payload).digest())
}

export function makeSession(): { value: string; id: string } {
  const exp = Math.floor(Date.now() / 1000) + TTL_S
  const id = b64u(randomBytes(12))
  const payload = `v1.${exp}.${id}`
  return { value: `${payload}.${sign(payload)}`, id }
}

export function readCookie(req: Request, name = COOKIE): string | null {
  const h = req.headers.get("cookie") || ""
  for (const part of h.split(/;\s*/)) {
    const i = part.indexOf("=")
    if (i > 0 && part.slice(0, i) === name) return decodeURIComponent(part.slice(i + 1))
  }
  return null
}

/** Returns the session id when the request carries a valid, unexpired signed cookie. */
export function verify(req: Request): string | null {
  if (!secret()) return null
  const v = readCookie(req)
  if (!v) return null
  const parts = v.split(".")
  if (parts.length !== 4 || parts[0] !== "v1") return null
  const [ver, exp, id, sig] = parts
  const want = Buffer.from(sign(`${ver}.${exp}.${id}`)), got = Buffer.from(sig)
  if (want.length !== got.length || !timingSafeEqual(want, got)) return null
  if (!(Number(exp) > Date.now() / 1000)) return null
  return id
}

const secure = (req: Request) => new URL(req.url).protocol === "https:"
export function setCookie(req: Request, value: string) {
  return `${COOKIE}=${encodeURIComponent(value)}; Path=/api; HttpOnly; SameSite=Strict; Max-Age=${TTL_S}${secure(req) ? "; Secure" : ""}`
}
export function clearCookie(req: Request) {
  return `${COOKIE}=; Path=/api; HttpOnly; SameSite=Strict; Max-Age=0${secure(req) ? "; Secure" : ""}`
}

/** Same-origin check for state-changing calls (defence in depth on top of SameSite=Strict). */
export function sameOrigin(req: Request) {
  const o = req.headers.get("origin")
  if (!o) return true
  try { return new URL(o).host === (req.headers.get("x-forwarded-host") || req.headers.get("host") || new URL(req.url).host) } catch { return false }
}

export const ip = (req: Request) => (req.headers.get("x-real-ip") || req.headers.get("x-forwarded-for") || "local").split(",")[0].trim()

/** Small in-memory sliding-window limiter. Per function instance, so it is a modest best-effort cap. */
const hits = new Map<string, number[]>()
export function limited(key: string, max: number, windowMs: number): boolean {
  const now = Date.now()
  const arr = (hits.get(key) || []).filter((t) => now - t < windowMs)
  if (arr.length >= max) { hits.set(key, arr); return true }
  arr.push(now); hits.set(key, arr)
  if (hits.size > 5000) for (const [k, v] of hits) if (!v.some((t) => now - t < windowMs)) hits.delete(k)
  return false
}

export const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...headers } })
