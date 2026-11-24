# Dorje Sherpa 🏔️ — the Dorje Teas growth dashboard, run by Claude

**What it is:** one private dashboard that shows how Dorje Teas is doing — sales, ads, customers, unfinished checkouts,
WhatsApp, SEO and competitors — plus **Claude as your growth analyst**. You ask in plain English; Claude refreshes the
data, explains what changed and suggests what to do. It never changes your store, ads or WhatsApp unless you say "yes".

## What you can do with it
- **See the business at a glance** — revenue, orders, new vs returning customers, ad spend and return, by day, week or month.
- **Ask questions** — "Why did revenue drop last week?", "Which Meta campaign should I cut?", "How do we compare with Vahdam?"
- **Get a daily brief** — what moved, why, and the top 3 actions.
- **Recover lost carts** — see how much money is left in unfinished checkouts and the plan to win it back.
- **Watch competitors** — their prices, offers and ads, and how Amazon prices compare with ours.
- **Decide** — every recommendation comes as a clear decision for you to approve.

Tabs in the dashboard: Overview · Ask Dorje ✦ · Revenue & Orders · Acquisition · Attribution · Retention · Abandoned checkouts ·
SEO & GEO · Competitors · Inventory & Alerts · Decisions · 30/60/90 plan.

## 10-minute quick start
You need a Mac or Windows computer and a Claude account (Pro or Max).

1. **Install Claude Code** (recommended) — open the Terminal app and paste:
   `curl -fsSL https://claude.ai/install.sh | bash` (Windows: see [claude.com/claude-code](https://claude.com/claude-code)).
   *Prefer an app?* Claude Desktop works too — see "Using Claude Desktop" in [docs/SETUP.md](docs/SETUP.md).
2. **Get the code** — in Terminal:
   ```
   git clone https://github.com/Gowtham-reddy23/dorje-sherpa-dashboard.git
   cd dorje-sherpa-dashboard
   claude
   ```
   (The repo is private: sign in to GitHub when asked, or ask Gowtham to add you.)
3. **Paste this one prompt** into Claude:
   > Set me up. I'm the CEO of Dorje Teas and not technical — explain each step simply, install what's needed, show me the
   > dashboard on sample data first, then help me connect our real Shopify, Meta and Zoko data. Never change anything live.
4. Claude installs everything and opens the dashboard at **http://localhost:3000**. Until real data is connected it shows
   **sample (made-up) numbers** — the passcode for the sample is `sherpa-demo`.
5. When Claude asks for keys (Meta, Zoko…), it tells you where to find them. **Paste them into the `.env` file it opens for you —
   never into the chat.**

## Things to say to Claude (or type the short command)
| Say | Or type | What happens |
|---|---|---|
| "Set me up" | `/setup` | Installs, connects data, runs the dashboard |
| "Refresh the data" | `/refresh` | Pulls fresh numbers (read-only) |
| "Give me today's brief" | `/brief` | What moved, why, what to do |
| "Why did revenue change last week?" | `/why-revenue` | Breaks the change down |
| "Review abandoned carts" | `/abandoned` | Lost-cart money and the recovery plan |
| "How are our ads doing?" | `/ads` | Meta (and Google when connected), with suggested changes for approval |
| "Check competitors" | `/competitors` | Prices, offers, ads, Amazon gap |
| "Check our SEO" | `/seo` | Google + AI-search health and fixes |
| "Put it online" | `/deploy` | Publishes your private copy on Vercel (asks first) |
| "Add a chart for …" | `/add-chart` | Adds something new to the dashboard |

## Safe by design
- **Read-only**: Shopify, Meta, Google Ads and Zoko are only read. Any change needs your explicit "yes".
- **Private**: data is encrypted with your passcode; customer details never leave your computer and are never put in GitHub.
- **Official connections only**: Shopify's, Meta's, Google's and Vercel's own connectors, and Zoko's own API.

## What's connected today
Shopify ✅ · Meta Ads ✅ · Zoko WhatsApp ✅ · Google Ads ⏳ (waiting for Google to approve API access — a Google Sheets report
works meanwhile) · Amazon ⏳ (credentials pending).

## More
- [docs/SETUP.md](docs/SETUP.md) — step-by-step for every connector, running locally, putting it online, switching on Ask Dorje.
- [docs/PLAYBOOK-GROWTH.md](docs/PLAYBOOK-GROWTH.md) — the growth plan: decisions waiting for approval.
- [CLAUDE.md](CLAUDE.md) — the playbook Claude follows (rules, runbooks, KPI definitions).

*Screenshots (optional, add later): `docs/img/overview.png`, `docs/img/ask-dorje.png`, `docs/img/abandoned.png`.*
