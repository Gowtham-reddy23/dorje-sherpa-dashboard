#!/usr/bin/env bash
# Ingest one full abandoned-checkout result (Shopify graphql_query output saved to a file).
# Usage: ./ingest_latest_ab.sh <result_file>
#    or: MCP_RESULTS_DIR=<folder where your agent saves tool results> ./ingest_latest_ab.sh   (picks the newest matching file from the last 10 min)
# The pages contain customer contact details: they stay in refresh/shopify/abandoned/ (git-ignored) and are never deployed.
set -euo pipefail
if [ $# -ge 1 ]; then f="$1"; else
  [ -n "${MCP_RESULTS_DIR:-}" ] || { echo "pass the result file, or set MCP_RESULTS_DIR"; exit 1; }
  f=$(find "$MCP_RESULTS_DIR" -maxdepth 2 -type f -mmin -10 -printf '%T@ %p\n' 2>/dev/null | sort -n | cut -d' ' -f2 | while read -r x; do grep -l '"abandonedCheckouts":{"pageInfo"' "$x" 2>/dev/null || true; done | tail -1)
fi
[ -n "$f" ] || { echo "no recent abandoned-checkout result found"; exit 1; }
python3 "$(dirname "$0")/ingest_abandoned.py" "$f"
