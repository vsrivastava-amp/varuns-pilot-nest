# LLM Eval Service / Pipeline

LLM evaluation service and pipeline; Varun is the primary context-holder. Release #6037 (shipped ~2026-07) was mostly refactors, so near-term work is post-release follow-ups, triage, and small fixes. This is the primary target for agent repo-work — highest ceiling of the four streams.

## Pointers

- Repos (both Bitbucket Cloud, local under `~/Documents/`):
  - `llm-evaluation-pipeline` — Databricks Asset Bundle, 5 jobs (`resources/workflows/*.yml`)
  - `llm-evaluator-service` — FastAPI on k8s; `{dev|stage}-llm-evaluator-service.ric1.admarketplace.net` (VPN only)
- System knowledge (config tables, pipeline mechanics, env quirks): `playbooks/llm-eval-system.md`
- Deploys: Databricks asset bundles via `scripts/deploy_dev.sh` (untracked in repo) — see `playbooks/databricks.md`
- Runs on Databricks dev/stage/prod workspaces (pointers in `map/experimentation-platform.md`)
- Jira board / epic: TBD (AI project; e.g. AI-1474 keyword-classification work touches this service)
- Slack: release channel (exact name TBD)
- Docs: TBD
- Owner: Varun

## Agent posture

- 2026-07-21: repo work (triage, small fixes) on dev branches only; PRs beyond dev → REVIEW.md.
