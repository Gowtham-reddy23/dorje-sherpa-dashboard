#!/usr/bin/env bash
# Scans the repo (git-tracked + untracked, not ignored) for things that must never be committed:
# tokens, API keys, OAuth secrets, emails, Indian phone numbers. Run before every commit/push: pnpm check:secrets
set -uo pipefail
cd "$(dirname "$0")/.."
FILES=$(git ls-files -co --exclude-standard 2>/dev/null || find . -type f -not -path './node_modules/*' -not -path './.git/*')
PAT='EAA[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|GOCSPX-[A-Za-z0-9_-]+|ya29\.[A-Za-z0-9_-]+|1//0[A-Za-z0-9_-]{20,}|shpat_[a-f0-9]{20,}|shpss_[a-f0-9]{20,}|vck_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|xox[abp]-[A-Za-z0-9-]+|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"client_secret"\s*:\s*"[^"]+"|apikey\s*[:=]\s*["'"'"'][A-Za-z0-9-]{16,}'
PII='[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|icloud|rediffmail)\.[a-z.]+|(\+91[ -]?)[6-9][0-9]{9}\b|\b[6-9][0-9]{9}\b'
hits=0
if command -v rg >/dev/null 2>&1; then SEARCH="rg -n --no-heading -e"; else SEARCH="grep -nHE -e"; fi
echo "$FILES" | grep -v -e '^pnpm-lock.yaml$' -e '^scripts/check-secrets.sh$' | while read -r f; do [ -f "$f" ] && echo "$f"; done > /tmp/.dorje-scan-files
if xargs $SEARCH "$PAT" < /tmp/.dorje-scan-files 2>/dev/null; then hits=1; fi
if grep -v -e '\.jpg$' /tmp/.dorje-scan-files | xargs $SEARCH "$PII" 2>/dev/null; then hits=1; fi
for f in .env .env.local .env.production data/dashboard.json public/data.enc.json; do
  git ls-files --error-unmatch "$f" >/dev/null 2>&1 && { echo "TRACKED (must not be): $f"; hits=1; }
done
rm -f /tmp/.dorje-scan-files
[ $hits -eq 0 ] && echo "check-secrets: clean" || { echo "check-secrets: FIX THE HITS ABOVE before committing"; exit 1; }
