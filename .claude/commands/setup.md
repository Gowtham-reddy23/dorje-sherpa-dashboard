---
description: "Set me up: check tools and .env, install, connect official connectors, first data pull, run locally"
---
Run the **"Set me up"** runbook in CLAUDE.md (runbook 1), step by step. Follow the golden rules: never ask me to paste secrets into chat (I will put them in `.env` myself), read-only on every business system. Start with `bash scripts/env-status.sh`, get the dashboard running on sample data first (`pnpm install && pnpm dev`, passcode `sherpa-demo`), then connect real data one connector at a time using docs/SETUP.md. Finish with a checklist of what is connected and what is pending. $ARGUMENTS
