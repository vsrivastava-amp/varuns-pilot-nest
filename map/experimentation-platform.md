# Experimentation Platform

Experimentation platform surfaced through Databricks dashboards. Agent job: pull status, flag anomalies. Session-tier work (Databricks auth rides SSO until/unless a dev-scoped PAT is approved).

## Pointers

- Databricks dev workspace: `dbc-562d27e2-d74d.cloud.databricks.com` — CLI profile `dbc-562d27e2-d74d` (the one that stays valid)
- Stage workspace: `dbc-303276b5-9802.cloud.databricks.com` — profile `stage`
- Prod workspace: `dbc-1b885e51-40bc.cloud.databricks.com` — **no CLI access**, but dev auth reads `prod_amplify` via shared metastore
- SQL warehouses: dev `634ea83b5df3a556` (PipelineDevelopers), stage `664db01689f76734`
- CLI mechanics: see `playbooks/databricks.md`
- Dashboards / jobs of interest: TBD
- Owner: TBD

## Agent posture

- 2026-07-21: read-only status pulls, batched into post-Okta bursts. Anomalies flagged in `state/` + dev channel.
