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

## Second path: Atlassian Rovo MCP (2026-07-22)

- claude.ai "Atlassian Rovo" connector, live on laptop sessions after a per-session `/mcp` handshake (see `playbooks/google.md` → session bridging gotcha). Verified via `atlassianUserInfo` → Varun's account, active.
- Rides Varun's OAuth, same as the API token: **read-only is behavioral here too.** Write tools exist (`createJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, Confluence page create/update) — all go through REVIEW.md first.
- Adds what the curl path didn't have wired up: `searchJiraIssuesUsingJql`, `getJiraIssue`, plus **Confluence** (`getConfluencePage`, `searchConfluenceUsingCql`) and Teamwork Graph context.
- curl path (above) remains the headless-safe option — MCP connectors need interactive auth and may be absent in cron runs.

## Landscape (2026-07-21 snapshot — re-derive, don't trust stale)

~40 projects visible. Ones that matter here: **AI** (Artificial Intelligence — PCIV core), **AS** (Ad Selection), **DPR** (Data Products & Reporting), **INFRA**, **PUB** (Publisher Onboarding), **DATABRICKS**, **RELEASE**.

## Comment threading (learned 2026-07-23)

- Jira Cloud **UI supports threaded replies** on issue comments. The **REST API does not** (as of 2026-07): no `parentId` on POST, and UI-made replies read back as flat comments (Atlassian RFC pending for API support). Rovo MCP's addCommentToJiraIssue is equally flat.
- Consequence: agent-posted "replies" = new comment + @mention of the person (ADF `mention` node with accountId). If true threading matters, Varun posts by hand in the UI.
