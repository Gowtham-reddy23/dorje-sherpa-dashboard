---
description: "Refresh all dashboard data (read-only pulls, rebuild, build)"
---
Run the **"Refresh data"** runbook in CLAUDE.md (runbook 2). Shopify via the official Shopify connector (read tools only) or `python3 refresh/shopify_api.py` if a read-only token is set; then `ZOKO_PAGES=0 bash refresh/refresh.sh` (or full Zoko pull if I say "full"). Report the refresh time in IST, data-through date, and the 3 biggest changes. Do not deploy unless I say so. $ARGUMENTS
