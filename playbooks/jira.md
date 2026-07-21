# Jira / Atlassian playbook

*(Living reference. Started 2026-07-21.)*

## Auth

- Site: `https://admarketplace.atlassian.net`
- Basic auth: `vsrivastava@admarketplace.com` + `ATLASSIAN_API_KEY` from `.env` in the nest root (gitignored — never commit).
- Token verified working 2026-07-21 (`/rest/api/3/myself` → 200). Token inherits Varun's full perms — **read-only is behavioral**: GETs freely; any POST/PUT (comments, transitions, ticket edits) goes through REVIEW.md first.

## Patterns

```bash
set -a && source .env && set +a
AUTH="vsrivastava@admarketplace.com:$ATLASSIAN_API_KEY"
BASE="https://admarketplace.atlassian.net/rest/api/3"

/usr/bin/curl -s -u "$AUTH" "$BASE/project/search?maxResults=100"   # projects
/usr/bin/curl -s -u "$AUTH" -G "$BASE/search/jql" \
  --data-urlencode 'jql=text ~ "PCIV" ORDER BY updated DESC' \
  --data-urlencode 'fields=summary,project,status,assignee,updated' # issue search
/usr/bin/curl -s -u "$AUTH" "$BASE/issue/AI-1542?fields=summary,description,comment"  # one issue
```

- Use `/search/jql` (GET with `--data-urlencode`), the modern endpoint — the old `/search` is deprecated.
- `/usr/bin/curl` full path (sandbox blocks bare `curl` — same gotcha as Databricks).

## Landscape (2026-07-21 snapshot — re-derive, don't trust stale)

~40 projects visible. Ones that matter here: **AI** (Artificial Intelligence — PCIV core), **AS** (Ad Selection), **DPR** (Data Products & Reporting), **INFRA**, **PUB** (Publisher Onboarding), **DATABRICKS**, **RELEASE**.
