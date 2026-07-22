# Databricks CLI playbook

*(Living reference. Absorbed from Varun's dbx-temp.md dump, 2026-07-21. Partial — more coming.)*

Working notes from the llm-evaluation-pipeline release (July 2026). Everything ran through the `databricks` CLI + SQL Statement Execution API — no UI needed except where noted.

## Auth & profiles (`~/.databrickscfg`)

| Profile | Workspace | Notes |
|---|---|---|
| `dbc-562d27e2-d74d` | dev `dbc-562d27e2-d74d.cloud.databricks.com` | The one that stays valid; `DEFAULT` and `vsrivastava_dev` had expired refresh tokens |
| `stage` | `dbc-303276b5-9802.cloud.databricks.com` | Created via `databricks auth login --host <host> --profile stage` (browser OAuth — user must run it) |
| (none) | prod `dbc-1b885e51-40bc.cloud.databricks.com` | No CLI access. But **dev auth can READ `prod_amplify`** via the shared metastore — all prod verification ran through the dev warehouse |

- `databricks auth describe --profile X` — check validity. Multiple profiles matching one host ⇒ every bundle command needs `-p`/`--profile`.

## Bundle deploys

- `scripts/deploy_dev.sh` (repo, untracked) wraps `bundle validate` + `bundle deploy`; env overrides: `PROFILE=<profile> TARGET=<dev|stage>`. It pins `DATABRICKS_TF_EXEC_PATH`/`DATABRICKS_TF_VERSION` to local terraform (dodges expired HashiCorp GPG key on CLI's own download).
- `scripts/deploy_dev.sh summary` → deployed job IDs/URLs.
- dev target = `mode: development`: syncs the **local working tree** (whatever branch is checked out) → jobs run exactly local code.

## SQL from the CLI

Helper at `scratchpad/sql.sh` — the pattern:

```bash
databricks api post /api/2.0/sql/statements --profile "$P" --json "$(jq -n \
  --arg wh "$WAREHOUSE" --arg s "$SQL" \
  '{warehouse_id:$wh, statement:$s, wait_timeout:"50s", disposition:"INLINE", format:"JSON_ARRAY"}')"
```

- Results: `.result.data_array`, errors: `.status.error.message`, state: `.status.state`.
- Warehouses: dev `634ea83b5df3a556` (PipelineDevelopers), stage `664db01689f76734`. List: `databricks warehouses list -p X`.

## Jobs

```bash
databricks jobs run-now <job_id> -p X --no-wait                     # trigger
databricks jobs run-now -p X --no-wait --json '{"job_id": N, "python_params": ["--start_date","2026-05-01",...]}'  # with params (job_id INSIDE json, no positional arg)
databricks jobs get-run <run_id> -p X | jq '.state'                 # poll
databricks jobs cancel-run <run_id> -p X --no-wait                  # continuous jobs: cancel = stop (they auto-restart if job stays unpaused... paused ones stay stopped)
databricks jobs list-runs --job-id N -p X --output json             # returns a bare ARRAY, not {runs:[...]}
databricks api get "/api/2.0/jobs/runs/get-output?run_id=<TASK run id>" -p X | jq -r '.logs // .error_trace'  # driver logs / traceback — use the TASK run_id from .tasks[0].run_id, not the job run_id
```

- Poll pattern: background `while` loop echoing state every 60–90s, exit on `TERMINATED|INTERNAL_ERROR`.
- Continuous jobs never terminate on success — poll for FAILED, verify output tables, then cancel.

## "Who uses this table?" forensics (system tables)

Dev-profile auth can read `system.*` via the shared metastore — answers usage questions no code grep can (proved out 2026-07-22, `runs/2026-07-22-prakash-intent-type.md`):

```sql
-- last reads + who/what (1yr retention; covers ALL Databricks reads incl. jobs/notebooks)
SELECT created_by, entity_type, entity_id, target_table_full_name, date(event_time) d, count(*)
FROM system.access.table_lineage
WHERE source_table_full_name = '<catalog.schema.table>' AND event_time > now() - INTERVAL 365 DAYS
GROUP BY ALL ORDER BY d DESC;

-- the actual SQL text (SQL-warehouse/serverless only, shorter retention)
SELECT executed_by, client_application, left(statement_text,180), max(end_time), count(*)
FROM system.query.history
WHERE statement_text ILIKE '%<table>%' AND start_time > now() - INTERVAL 30 DAYS
GROUP BY ALL ORDER BY 4 DESC;
```

- `created_by` numeric id? Resolve service principals: `databricks api get /api/2.0/preview/scim/v2/ServicePrincipals -p <profile>`. Unattributed bare-TABLE reads with no entity ≈ Catalog Explorer browsing, not a job.
- Backticked names dodge the ILIKE filter (`` `amp`.`intent_type` ``) — lineage catches what query.history misses, and cluster-based Spark jobs skip query.history entirely. Trust lineage for coverage, query.history for the statement text.
- Caveat: covers Databricks reads only — direct MySQL-side consumers need DB-team telemetry.

## Other

- `databricks fs ls/rm -r dbfs:/...` — checkpoint inspection/reset.
- `databricks repos create <url> bitbucketCloud --path /Repos/<user>/<name>`, `repos update <id> --branch <b>` — needs git-credentials in that workspace (`databricks git-credentials list`).
- `databricks workspace export <path>`, `workspace list`, `workspace get-status` — object types (FILE vs NOTEBOOK) matter.
- `DESCRIBE HISTORY <table>` via SQL — commit forensics (who wrote when; infer job cadence).

## Gotchas

- **zsh doesn't word-split unquoted vars** — `set -- $var` loops break; write explicit calls.
- **Sandbox blocks bare `curl`** (use `/usr/bin/curl` full path), and internal DNS (`*.admarketplace.net`) doesn't resolve from the sandbox — verify services via pipeline runs or ask user (VPN).
- `--json` flag on `jobs run-now` rejects positional job_id.
- Timestamps: user's machine is **Pacific time**; Databricks logs are UTC.