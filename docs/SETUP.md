# Setup guide

Everything here can be done by Claude for you ("Set me up"). This page is the reference for each step.
**Rule for every key or token: paste it into the `.env` file on your computer — never into chat, email or GitHub.**
`.env` is created with `cp .env.example .env`; Claude opens it for you. `bash scripts/env-status.sh` shows what is filled in
(it never prints the values).

Contents: 1 Tools · 2 Run locally · 3 Passcode · 4 Shopify · 5 Meta Ads · 6 Zoko · 7 Google Ads · 8 Vercel + Ask Dorje ·
9 Refreshing data · 10 Claude Desktop · 11 Troubleshooting · 12 Connector reference

---

## 1. Tools (one time)
| Tool | Why | Install |
|---|---|---|
| Claude Code | Runs the playbook | `curl -fsSL https://claude.ai/install.sh \| bash` (macOS/Linux) — Windows: claude.com/claude-code |
| Node.js 22+ and pnpm | The dashboard | nodejs.org (LTS), then `corepack enable && corepack prepare pnpm@latest --activate` |
| Python 3.10+ | Data refresh scripts | python.org (macOS: `xcode-select --install` also works), then `pip3 install -r refresh/requirements.txt` |
| Git | Getting/updating the code | git-scm.com (macOS: comes with Xcode tools) |
| Vercel CLI (optional) | Putting your copy online | `npm i -g vercel` then `vercel login` |
| pipx + gcloud (optional) | Google Ads connector | `brew install pipx google-cloud-sdk` (macOS) |
| Google Chrome (optional) | Weekly competitor scans | already installed on most computers; set `CHROME_PATH` in `.env` if it isn't found |

## 2. Run the dashboard on your computer
```
pnpm install
pnpm dev            # opens on http://localhost:3000
```
- With no data connected, it shows **SAMPLE (fabricated) data**. Passcode: `sherpa-demo`. A yellow "SAMPLE DATA" badge is shown.
- After a real refresh (section 9) it shows your real data; unlock it with **your** `DASH_PASSCODE`.
- `pnpm dev` does not run the Ask Dorje chat server (the tab shows a notice). To try the chat locally:
  `pnpm preview` (mock answers, no AI cost, http://127.0.0.1:3311) or `pnpm build && pnpm preview:live` with `AI_GATEWAY_API_KEY` set (real answers).

## 3. Passcode and session secret
In `.env`:
- `DASH_PASSCODE=` a long phrase only the founders know (e.g. four random words). It encrypts the data; share it privately.
- `SESSION_SECRET=` paste the output of `openssl rand -hex 32` (Claude can run it and write it into `.env` without showing it).
If you change the passcode later: refresh (section 9), redeploy, and update `DASH_PASSCODE` on Vercel too.

## 4. Shopify (read-only)
**Preferred — Shopify's official connector for Claude** (no token to manage):
1. In Claude (claude.ai or the desktop app): Settings → Connectors → browse → **Shopify** → Connect.
2. Sign in to the Dorje Teas Shopify admin and approve. Approve **read** access; you can decline anything that writes.
3. In Claude Code, run `/mcp` — the Shopify connector from your Claude account should be listed (connectors added at claude.ai
   are available in Claude Code when you are logged in with the same account — **verify** on your machine).
4. Claude uses only `run-analytics-query` (ShopifyQL) and `graphql_query`. It never uses `graphql_mutation`, `update-product`,
   `set-inventory`, `create-discount` or theme tools (CLAUDE.md golden rule 1).

**Fallback — direct Admin API with a read-only token** (for unattended refreshes):
1. Shopify admin → Settings → Apps and sales channels → Develop apps → Create an app "Dorje Sherpa (read-only)".
2. Configure Admin API scopes: `read_orders`, `read_all_orders`, `read_products`, `read_customers`, `read_reports`, `read_checkouts`,
   `read_inventory`. **No write scopes.**
3. Install the app → reveal the Admin API access token once → paste into `.env` as `SHOPIFY_ADMIN_TOKEN=`;
   set `SHOPIFY_STORE_DOMAIN=<store>.myshopify.com`.
4. Test: `python3 refresh/shopify_api.py --only analytics`. (ShopifyQL via the Admin API needs a recent API version — **verify**;
   change `SHOPIFY_API_VERSION` if Shopify reports an error.)
Note: Shopify asks merchants not to wire AI tools to raw tokens; this token is only for our own scripts, Claude uses the connector.

## 5. Meta Ads (read-only)
**For the refresh scripts (Graph Marketing API):**
1. developers.facebook.com → My Apps → your Dorje app (or create one, type Business) → add the **Marketing API** product.
2. Best: Meta Business Settings → Users → **System users** → add a system user (Employee role) → assign the Dorje ad account with
   **View performance** only → Generate token for the app with the **`ads_read`** permission (and `read_insights`). It does not expire.
   (Quick test alternative: Graph API Explorer user token with `ads_read`, then exchange for a 60-day token.)
3. `.env`: `META_ACCESS_TOKEN=` and `META_AD_ACCOUNT_ID=act_<number>` (Ads Manager → account dropdown shows the number).
4. Test: `python3 refresh/pull_meta_seo.py` writes `refresh/meta_seo.json`.

**For Claude (official Meta Ads MCP, `https://mcp.facebook.com/ads`, already in `.mcp.json`):** in Claude Code run `/mcp` →
meta-ads → Authenticate → log in with Facebook and pick the Dorje ad account. Business owners can set **ads MCP server rules** in
Meta Business settings to block budget/campaign changes by AI agents — recommended (read-only).

## 6. Zoko WhatsApp (read-only, direct API)
1. Zoko dashboard → Settings → **API / Developer** (exact menu name may differ — **verify**) → copy the API key.
2. `.env`: `ZOKO_API_KEY=`.
3. Test: `python3 refresh/pull_zoko.py` (templates only, fast). The full contact pull is slow by design: Zoko allows 1 contact-list
   call per 5 minutes (2,000 contacts per call) → about 1.5 hours. Use `ZOKO_PAGES=0` for quick refreshes.
4. The scripts only send **GET** requests (header `apikey`, base `https://chat.zoko.io/v2`). They never send messages, change tags
   or delete anything. Contact lists stay in `refresh/zoko/` on your computer (git-ignored); the dashboard gets aggregates only.

## 7. Google Ads (status: blocked on Google's approval)
The official connector is Google's **google-ads-mcp** (github.com/googleads/google-ads-mcp, read-only reporting). It is already
in `.mcp.json` (`pipx run --spec google-ads-mcp==0.0.6 google-ads-mcp`). It needs a Google Cloud project whose Google Ads API
access level is **Explorer** or higher. On 24 Nov 2026 Google **refused Explorer access** for the current project, so live
reads fail with `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION`.

To unblock:
1. Google Cloud console → Billing → link a **paid** billing account to the project (Free Trial projects are usually refused; the API
   itself is free). Ideally use a project owned by the Dorje business Google account.
2. APIs & Services → Google Ads API → Overview → Access level → **Apply** for Explorer. Use case: "Read-only reporting on our own
   Google Ads account for an internal dashboard; no account management; no third-party clients."
3. When approved: create a Desktop OAuth client (APIs & Services → Credentials) and download its JSON (keep it OUTSIDE the repo), then
   ```
   gcloud auth application-default login \
     --scopes=https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
     --client-id-file=/path/outside/repo/client.json
   ```
4. `.env`: `GOOGLE_CLOUD_PROJECT=`, `GOOGLE_APPLICATION_CREDENTIALS=` (the path printed by gcloud), `GOOGLE_ADS_CUSTOMER_ID=`
   (10 digits, no dashes), `GOOGLE_ADS_LOGIN_CUSTOMER_ID=` only if you use a manager account. Restart Claude Code; `/mcp` shows google-ads.
   (Google retired developer tokens on 9 Sep 2026; the Cloud project's access level is what counts.)

**Fallback today — scheduled report to Google Sheets:** Google Ads → Reports → create a campaign report (date, campaign, cost,
impressions, clicks, conversions, conversion value) → Schedule → daily → Google Sheets. Put the sheet's id in
`GOOGLE_ADS_REPORT_SHEET_ID=`, and connect Claude's official Google Drive connector (Settings → Connectors) so Claude can read it
for "/ads". Adding Google spend into MER/CAC needs a small code change (runbook 10) once data flows.

## 8. Put your own copy online (Vercel) and switch on Ask Dorje
1. `pnpm build` → `python3 scripts/stage_deploy.py` → `cd vercel-deploy && vercel deploy --prod`.
   First time: create a new project (e.g. `dorje-sherpa`), Framework **Other**, no build command, no output directory.
   (Or let Claude use the official Vercel MCP, `https://mcp.vercel.com`, already in `.mcp.json` — authenticate with `/mcp`.)
2. Vercel → project → Settings → Environment Variables (Production, mark **Sensitive**):
   `DASH_PASSCODE` (same as `.env`; `sherpa-demo` if you deployed sample data), `SESSION_SECRET`, optional `ASK_DORJE_MODEL`.
   Redeploy after adding them.
3. **Ask Dorje needs AI Gateway credit:** Vercel dashboard → **AI Gateway** → add a credit card (vercel.com/<team>/~/ai). The deployed
   function authenticates with the project's OIDC token automatically — no API key needed on Vercel.
4. Optional custom domain: project → Settings → Domains.
5. Check: the site shows the passcode screen, and `curl -s -o /dev/null -w "%{http_code}" -X POST https://<your-url>/api/chat` → `401`.
Privacy: only encrypted data is uploaded (`stage_deploy.py` refuses plain data or `.env`), pages are `noindex`, and the chat cannot
change anything. Don't connect the GitHub repo for automatic Vercel builds — the repo has no real data, so the site would show the sample.

## 9. Refreshing data
- **With Claude (recommended):** say "Refresh the data" or `/refresh`. Claude runs the Shopify reads with the connector, then
  `bash refresh/refresh.sh` (Meta + SEO/GEO + Zoko + rebuild + `pnpm build`).
- **Without Claude (needs the Shopify token from section 4):**
  ```
  python3 refresh/shopify_api.py && ZOKO_PAGES=0 bash refresh/refresh.sh
  ```
- **Every 3 hours (current cadence):** ask Claude to set up a scheduled job on your computer (macOS launchd / cron), e.g.
  `0 */3 * * * cd ~/dorje-sherpa-dashboard && python3 refresh/shopify_api.py && ZOKO_PAGES=0 bash refresh/refresh.sh >> refresh.log 2>&1`
  and, only if you want it to publish automatically, `&& python3 scripts/stage_deploy.py && (cd vercel-deploy && vercel deploy --prod --yes)`.
  Run the full Zoko contact pull and the competitor check (`/competitors`) weekly.

## 10. Using Claude Desktop instead of Claude Code
Claude Code is best because it can run the scripts. With the desktop app you have two options:
- **Code tab in Claude Desktop** (if your app shows it): choose this folder — it is the same Claude Code, `CLAUDE.md` and the
  `/commands` work the same way.
- **Chat only:** Settings → Connectors → add **Shopify**, **Vercel**, and a custom connector with URL `https://mcp.facebook.com/ads`
  (Meta Ads). Then create a Project, upload `CLAUDE.md` and `docs/PLAYBOOK-GROWTH.md` as project knowledge, and ask questions
  ("Give me today's brief from Shopify and Meta"). It can read live data but cannot run the dashboard or the refresh scripts.
  For Google Ads in the desktop app, add to `claude_desktop_config.json` (macOS `~/Library/Application Support/Claude/`,
  Windows `%APPDATA%\Claude\`):
  ```json
  { "mcpServers": { "google-ads": { "command": "pipx", "args": ["run", "--spec", "google-ads-mcp==0.0.6", "google-ads-mcp"],
      "env": { "GOOGLE_CLOUD_PROJECT": "<project id>", "GOOGLE_APPLICATION_CREDENTIALS": "<path to ADC json>" } } } }
  ```

## 11. Troubleshooting
| Problem | Fix |
|---|---|
| "That passcode didn't work" | Sample data → `sherpa-demo`. Real data → the `DASH_PASSCODE` that was in `.env` when you last refreshed |
| `prepare-data: ... DASH_PASSCODE is not set` | Add `DASH_PASSCODE` to `.env` (real data exists in `data/`) |
| Ask Dorje: "switched off in this copy" | Expected under `pnpm dev`. Use `pnpm preview`, or the deployed site |
| Ask Dorje: "needs a card on file for AI Gateway" | Add a card in Vercel → AI Gateway |
| `Missing META_ACCESS_TOKEN` (or another name) | Fill that line in `.env` (sections 4–7) |
| Meta `(#200) permissions` error | The token lacks `ads_read` or the system user isn't assigned to the ad account |
| Zoko `429` / slow | Normal rate limit (1 contact call per 5 min). Use `ZOKO_PAGES=0` |
| Google Ads `CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION` | Section 7 — Explorer access not approved yet; use the Sheets fallback |
| Next.js build stops with a security notice | Re-run the build; then ask Claude to upgrade Next.js (`pnpm dlx next upgrade`), test, and commit |

## 12. Connector reference (official sources)
| Connector | Official source | Status in this repo |
|---|---|---|
| Shopify connector for Claude | help.shopify.com → "Shopify connector for Claude" (endpoint managed by Claude/Shopify) | Via Claude account connectors — **verify** it shows in Claude Code `/mcp` |
| Shopify Admin GraphQL API | shopify.dev/docs/api/admin-graphql | `refresh/shopify_api.py` (read-only token) — ShopifyQL field shape **verify** |
| Meta Ads MCP | developers.facebook.com/documentation/mcp → `https://mcp.facebook.com/ads` | In `.mcp.json` (OAuth) |
| Meta Marketing API | Graph API v21.0 `act_<id>/insights` | `refresh/pull_meta_seo.py` etc. |
| Google Ads MCP | github.com/googleads/google-ads-mcp (PyPI `google-ads-mcp`, v0.0.6 at time of writing) | In `.mcp.json`; blocked on Explorer access |
| Vercel MCP | vercel.com/docs/mcp → `https://mcp.vercel.com` | In `.mcp.json` (OAuth) |
| Zoko REST API | `https://chat.zoko.io/v2`, header `apikey` | `refresh/zoko_api.py` (GET only); key location in dashboard **verify** |
