#!/usr/bin/env bash
# Shows which settings in .env are filled in, WITHOUT printing any values. Used by the "Set me up" runbook.
cd "$(dirname "$0")/.."
[ -f .env ] || { echo ".env not found -> run: cp .env.example .env   (then fill it in; the app still runs on SAMPLE data)"; exit 0; }
grep -E '^[A-Z0-9_]+=' .env.example | cut -d= -f1 | while read -r k; do
  v=$(grep -E "^$k=" .env | tail -1 | cut -d= -f2-)
  if [ -z "$v" ] || [[ "$v" == *XXXX* ]]; then echo "  [ ] $k"; else echo "  [x] $k"; fi
done
echo "Tools:"; for t in node pnpm python3 git vercel pipx gcloud; do command -v $t >/dev/null && echo "  [x] $t $($t --version 2>/dev/null | head -1)" || echo "  [ ] $t"; done
python3 -c "import cryptography" 2>/dev/null && echo "  [x] python cryptography" || echo "  [ ] python cryptography  (pip3 install -r refresh/requirements.txt)"
[ -f data/dashboard.json ] && echo "Data: REAL (data/dashboard.json, $(date -r data/dashboard.json '+%d %b %Y %H:%M'))" || echo "Data: SAMPLE (fabricated). Run the refresh for real data."
