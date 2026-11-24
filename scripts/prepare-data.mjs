// Prepares public/data.enc.json (the encrypted dataset the dashboard and Ask Dorje read) before `pnpm dev` / `pnpm build`.
//  - Real data: if data/dashboard.json exists (written by refresh/build_app_data.py; git-ignored), it is encrypted with DASH_PASSCODE.
//  - Sample data: otherwise sample-data/dashboard.sample.json (FABRICATED demo numbers) is encrypted with the demo passcode
//    "sherpa-demo" (override with DEMO_PASSCODE) so the app works with no connectors and no secrets.
// Same format as refresh/build_app_data.py and lib/dash.ts decrypt(): AES-256-GCM, key = PBKDF2-SHA256(passcode, 250k rounds).
import { readFileSync, writeFileSync, existsSync, mkdirSync, rmSync, statSync } from "node:fs"
import { webcrypto as crypto } from "node:crypto"

// Minimal .env loader (no dependency). Real environment variables win.
if (existsSync(".env")) for (const line of readFileSync(".env", "utf8").split(/\r?\n/)) {
  const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/)
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, "")
}

const REAL = "data/dashboard.json", SAMPLE = "sample-data/dashboard.sample.json", OUT = "public/data.enc.json", FLAG = "public/sample-mode.json"
mkdirSync("public", { recursive: true })
const real = existsSync(REAL)
let pass = real ? process.env.DASH_PASSCODE?.trim() : (process.env.DEMO_PASSCODE?.trim() || "sherpa-demo")
if (real && !pass) {
  if (existsSync(OUT) && statSync(OUT).mtimeMs >= statSync(REAL).mtimeMs) { console.log("prepare-data: real data already encrypted (no DASH_PASSCODE set, keeping public/data.enc.json)"); process.exit(0) }
  console.error("prepare-data: data/dashboard.json exists but DASH_PASSCODE is not set. Add it to .env (see .env.example)."); process.exit(1)
}
const raw = readFileSync(real ? REAL : SAMPLE)
const salt = crypto.getRandomValues(new Uint8Array(16)), iv = crypto.getRandomValues(new Uint8Array(12)), n = 250000
const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pass), "PBKDF2", false, ["deriveKey"])
const key = await crypto.subtle.deriveKey({ name: "PBKDF2", salt, iterations: n, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["encrypt"])
const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, raw))
const b64 = (u) => Buffer.from(u).toString("base64")
writeFileSync(OUT, JSON.stringify({ s: b64(salt), i: b64(iv), c: b64(ct), n }))
if (real) rmSync(FLAG, { force: true })
else writeFileSync(FLAG, JSON.stringify({ sample: true, passcode: pass, note: "Sample data mode: fabricated demo numbers. Run the refresh (CLAUDE.md) for real data." }))
console.log(`prepare-data: ${real ? "REAL data (data/dashboard.json)" : "SAMPLE data (fabricated) — demo passcode: " + pass} -> ${OUT} (${Math.round(ct.length / 1024)} KB)`)
