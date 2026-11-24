#!/usr/bin/env bash
# Dorje Sherpa — data refresh. READ-ONLY everywhere (Shopify, Meta, Zoko, public web). See CLAUDE.md -> "Refresh data".
#
# Before this script (Claude does these with the Shopify connector, read-only):
#   Step 1  : `python3 refresh/shopify_queries.py` prints the ShopifyQL / GraphQL reads. Run each with the Shopify connector
#             (run-analytics-query / graphql_query), save the result to a file, then `python3 refresh/ingest.py <name> <file>`.
#   Step 1b : order pages for Attribution (ORDERS section of shopify_queries.py) -> `python3 refresh/ingest_orders.py <files>`.
#   Step 1c : order phone pages for the Zoko join -> `python3 refresh/ingest_phones.py <files>` (phones stay local, git-ignored).
#   Step 1d : abandoned-checkout pages (ABANDONED_Q, 90 days, 100/page) -> `./refresh/ingest_latest_ab.sh <file>` per page.
# Then run this script. It pulls Meta (Graph API, META_ACCESS_TOKEN), Zoko (GET only, ZOKO_API_KEY), crawls SEO/GEO,
# and rebuilds data/dashboard.json + public/data.enc.json (encrypted with DASH_PASSCODE). Finally `pnpm build`.
#
# Env: ZOKO_PAGES=0 skips the slow Zoko contact pull (1 call / 5 min, 2,000 contacts per call).
#      SKIP_BUILD=1 skips `pnpm build`.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p shopify zoko competitors
python3 pull_meta_seo.py      # Meta account + campaigns + SEO/GEO crawl -> meta_seo.json
python3 pull_attr_meta.py     # Meta id map + monthly campaign results -> meta_attr.json
python3 pull_zoko.py --customers --max-pages "${ZOKO_PAGES:-25}" || echo 'zoko pull skipped (no ZOKO_API_KEY?)'
python3 build_zoko.py || echo 'zoko build skipped'                  # aggregates only, no PII -> zoko.json
python3 pull_zoko_abandoned.py --days 45 --max 40 || echo 'zoko abandoned check skipped'
python3 build_abandoned.py || echo 'abandoned build skipped (no abandoned pages ingested?)'   # -> abandoned.json (aggregates)
python3 build_attr.py || echo 'attribution build skipped (no order pages ingested?)'          # -> attr.json + attr_summary.json
python3 build_competitors.py || echo 'competitors build skipped (run the weekly competitor pull first)'  # -> competitors.json
python3 build.py              # -> data.json
python3 founders.py           # -> founders.json (plain-English verdict, decisions)
python3 pull_app_meta.py      # 2-year daily Meta series + campaign tables -> meta_app.json
python3 build_app_data.py     # -> ../data/dashboard.json (local only) + ../public/data.enc.json (encrypted)
if [ -z "${SKIP_BUILD:-}" ]; then (cd .. && pnpm build); fi
echo "Refresh done. Run 'pnpm dev' (or 'pnpm preview') to look at it, or deploy (CLAUDE.md -> Deploy to Vercel)."
