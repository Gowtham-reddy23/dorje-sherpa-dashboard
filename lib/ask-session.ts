"use client"
/** Ask Dorje server session: the passcode is checked server-side and exchanged for an HMAC-signed httpOnly cookie. */
export async function openAskSession(passcode: string): Promise<boolean> {
  try {
    const r = await fetch("/api/session", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ passcode }), credentials: "same-origin" })
    return r.ok
  } catch { return false }
}
export async function closeAskSession() {
  try { await fetch("/api/session", { method: "DELETE", credentials: "same-origin" }) } catch { /* ignore */ }
}
export const PASS_KEY = "dorje-founders-pass"
