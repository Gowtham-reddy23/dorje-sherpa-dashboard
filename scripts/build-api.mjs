// Bundles the Ask Dorje server functions (server/*.ts) into self-contained Vercel Node functions in api/ (no install step needed on Vercel).
import { build } from "esbuild"
import { rmSync, mkdirSync } from "node:fs"
rmSync("api", { recursive: true, force: true }); mkdirSync("api")
await build({
  entryPoints: { chat: "server/chat.ts", session: "server/session.ts" },
  outdir: "api", outExtension: { ".js": ".mjs" }, bundle: true, platform: "node", format: "esm", target: "node22",
  minify: true, legalComments: "none", logLevel: "info",
  banner: { js: "import { createRequire as __cr } from 'node:module'; const require = __cr(import.meta.url);" },
})
