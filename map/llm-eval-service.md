# LLM Eval Service / Pipeline

LLM evaluation service and pipeline; Varun is the primary context-holder. Release #6037 (shipped ~2026-07) was mostly refactors, so near-term work is post-release follow-ups, triage, and small fixes. This is the primary target for agent repo-work — highest ceiling of the four streams.

## Pointers

- Repo: `llm-evaluation-pipeline` (Bitbucket Cloud); local clone path TBD
- Deploys: Databricks asset bundles via `scripts/deploy_dev.sh` (untracked in repo) — see `playbooks/databricks.md`
- Runs on Databricks dev/stage workspaces (pointers in `map/experimentation-platform.md`)
- Jira board / epic: TBD
- Slack: release channel (exact name TBD)
- Docs: TBD
- Owner: Varun

## Agent posture

- 2026-07-21: repo work (triage, small fixes) on dev branches only; PRs beyond dev → REVIEW.md.
