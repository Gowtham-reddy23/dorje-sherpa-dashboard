import { decrypt, type Dash } from "../lib/dash"

let cache: { at: number; data: Dash } | null = null
const TTL = 5 * 60 * 1000

/** Loads the same encrypted dataset the dashboard uses (public/data.enc.json, rebuilt by every refresh) and decrypts it server-side. */
export async function loadData(req: Request): Promise<Dash> {
  if (cache && Date.now() - cache.at < TTL) return cache.data
  const pass = process.env.DASH_PASSCODE?.trim()
  if (!pass) throw new Error("DASH_PASSCODE not configured")
  const origin = process.env.ASK_DATA_ORIGIN || new URL(req.url).origin
  const res = await fetch(new URL("/data.enc.json", origin), { cache: "no-store" })
  if (!res.ok) throw new Error(`data fetch ${res.status}`)
  const data = await decrypt(await res.json(), pass)
  cache = { at: Date.now(), data }
  return data
}
