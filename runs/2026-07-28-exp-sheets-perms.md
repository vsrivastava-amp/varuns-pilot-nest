# 2026-07-28 — exp-sheets: permissions scouting for Databricks→Google Sheets experiment reporting

Session slug: exp-sheets. Context: Varun wants the "Experimentation Platform Analysis" dashboard's pivots replaced/augmented by an auto-refreshing, annotatable Google Sheet, pushed by a **scheduled Databricks job** (preferred over the official Sheets connector after discussion — more control, per-experiment tab fan-out, we own the plumbing).

## Architecture (agreed direction)

Scheduled Databricks job (dev workspace, serverless) runs the 6 dashboard dataset queries → writes ranges in place to a Google Sheet via Sheets API (`gspread`), SA JSON key in a Databricks secret scope. In-place `values.update` preserves comments/notes/conditional formatting → annotations survive refreshes.

## Verified today (hands-on, dev workspace `dbc-562d27e2-d74d`)

- 2026-07-28 — Serverless egress to Google APIs: ✅ one-off `jobs submit` run (run_id 767233135907258) hit `sheets.googleapis.com` + `www.googleapis.com` → HTTP 200. Playbook updated.
- 2026-07-28 — Secret scope create/delete: ✅ (`exp-sheets-egress-test` created+deleted).
- 2026-07-28 — Job submit/schedule, workspace import: ✅ (no new perms needed).
- Table access: the 6 queries already run as Varun on the dev warehouse (dashboard is his) — `prod_amplify.*` via shared metastore. No ask.

## The one real ask (Google side)

GCP **service account + Sheets API + JSON key** (or workload identity federation if security prefers keyless). Route discovered via Slack/Jira archaeology:

- Precedent: Stephen Ince asked #security-general (2026-02-23) for an SA for LLM→Google Docs automation → **INFRA-3015**, assignee Bilal Hassan (security, under Artem Kazantsev / Kfir Shay org).
- ⚠️ **INFRA-3015 is still Not Started 5 months later** (created 2026-02-24, updated 2026-07-14). Expect the same queue for ours; a ping/piggyback on Stephen's ticket may help both.
- A GCP project already exists: `project-ssp-placement-caps` (from INFRA-3015). So this is "add SA to existing GCP footprint", not "stand up GCP".
- Secondary check on the ticket: Workspace sharing policy must allow sharing a sheet to `*.iam.gserviceaccount.com`.

Draft filed: `review/2026-07-28-exp-sheets-gcp-sa-jira.txt` (INFRA ticket, models Stephen's; offers WIF alternative; asks the sharing-policy question).

## Fallbacks if the SA ask stalls (fully automated, zero new permissions)

1. **Apps Script pull**: time-triggered Apps Script inside the Sheet calls Databricks SQL Statement Execution API (dev warehouse `634ea83b5df3a556`) with a Databricks token in Script Properties. Varun can mint the token himself. No GCP, no admin. Weaker secret posture (token in Script Properties) but read-only-scoped token limits blast radius.
2. Official Databricks Sheets connector (Marketplace add-on): manual-refresh mode needs no admin; *scheduled* refresh needs a metastore admin to create a UC connection + Google admin to allow the add-on.

## Optional hardening (not blockers)

- Databricks service principal to own the job (survives Varun's account; workspace-admin ask).
- Key rotation cadence for the SA JSON key; or WIF to avoid keys entirely.

## Next steps

- Varun disposes the review/ draft (file INFRA ticket).
- Meanwhile buildable with zero asks: numeric rewrite of the 6 dataset SQLs + the job skeleton + sheet template; SA key slots in last. (Also: dashboard SQL has an EST bug — fixed `INTERVAL '5 hours'` ≠ EDT; fix when touching the SQL.)
