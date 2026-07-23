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

## Build tracker context (2026-07-23)

ARES (Automated Relevance Evaluation Service) is the eval half of tracker project
**Relevance Quality Upgrade (Vector Matching & CIV Extraction)** (Build Accountable
**Dhaval Shah**):
- **M1 ARES v1.0 – Done**; **M4 ARES v1.1 – Text Ads — TL Varun, ✅ Done** (PL
  Amarachi Miller). The eval-pipeline CI/CD ("LLM Evaluation Pipeline") shipped as
  **RELEASE-6001 (06/04)** under Tech Debt Reduction M6 (Databricks CI/CD).
- Project Slack (fills the "release channel TBD" above):
  **#proj-automated-relevance-eval-service**, plus #proj-query-civ-extraction,
  #proj-intent-identification, #proj-pla-feed-audit.
- In the tracker's ML-Systems appendix this is the "**Relevancy evaluation
  [Offline; Online]**" service; "Online" (real-time relevance in prod) is the
  north-star piece not yet built.
- Tracker doc: `1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`.

## Agent posture

- 2026-07-21: repo work (triage, small fixes) on dev branches only; PRs beyond dev → REVIEW.md.
