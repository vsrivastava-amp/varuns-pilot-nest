# Jira / Atlassian playbook

*(Living reference. Started 2026-07-21.)*

## Auth

- Site: `https://admarketplace.atlassian.net`
- Basic auth: `vsrivastava@admarketplace.com` + `ATLASSIAN_API_KEY` from `.env` in the nest root (gitignored — never commit).
- Token verified working 2026-07-21 (`/rest/api/3/myself` → 200). Token inherits Varun's full perms — **read-only is behavioral**: GETs freely; any POST/PUT (comments, transitions, ticket edits) goes through a `review/` draft first (or Varun's in-chat direction).

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
- Rides Varun's OAuth, same as the API token: **read-only is behavioral here too.** Write tools exist (`createJiraIssue`, `editJiraIssue`, `transitionJiraIssue`, `addCommentToJiraIssue`, Confluence page create/update) — all go through a `review/` draft first (or Varun's in-chat direction).
- Adds what the curl path didn't have wired up: `searchJiraIssuesUsingJql`, `getJiraIssue`, plus **Confluence** (`getConfluencePage`, `searchConfluenceUsingCql`) and Teamwork Graph context.
- curl path (above) remains the headless-safe option — MCP connectors need interactive auth and may be absent in cron runs.

## Landscape (2026-07-21 snapshot — re-derive, don't trust stale)

~40 projects visible. Ones that matter here: **AI** (Artificial Intelligence — PCIV core), **AS** (Ad Selection), **DPR** (Data Products & Reporting), **INFRA**, **PUB** (Publisher Onboarding), **DATABRICKS**, **RELEASE**.

## Comment threading (learned 2026-07-23)

- Jira Cloud **UI supports threaded replies** on issue comments. The **REST API does not** (as of 2026-07): no `parentId` on POST, and UI-made replies read back as flat comments (Atlassian RFC pending for API support). Rovo MCP's addCommentToJiraIssue is equally flat.
- Consequence: agent-posted "replies" = new comment + @mention of the person (ADF `mention` node with accountId). If true threading matters, Varun posts by hand in the UI.

## Writing style for ticket comments (Varun standard, 2026-07-27; refined in-chat 2026-07-27)

One standard — **ASD-STE100 sentence discipline** — run in two moods depending on the comment's job. The core rules always apply:
- Short sentences (~20 words max); one idea per sentence.
- Active voice; one word per concept (no synonym variation — "filter" stays "filter").
- No padding: content that lives in the dossier/run log stays there. Claim-to-evidence ratio 1:1 — every assertion personally verified.

**Handoff/status comments** (imperative mood): instructions and warnings only. Structure: `next steps:` then `footgun:`. No hedges, no questions. Worked example: AI-1542 c170926. Origin: Varun rejected a verbose draft — "I just want the exact footgun i raised, in simple text."

**Discussion comments on others' analyses** (indicative mood + questions): Varun frames this as "a conversational variant of STE-100" — same sentence mechanics, wider speech acts. Worked examples: AI-1545 c170698/c170757.
- Friendly direct opener ("Hey @Artem — dug through the CSVs"), cc whoever needs the thread.
- Structure: observation → why → evidence-in-passing → hand the thread back with questions.
- Calibrated hedges are correct, not vague: "looks concentrated" = observed, not causally confirmed. Mark epistemic status precisely.
- Ask the owner whether behavior is intended; do NOT enumerate fix directives on someone else's ticket.
- Short: 2–4 small paragraphs or a couple of numbered points. A table only if it earns its lines (Dhaval likes them).
- ⚠️ Do not apply the imperative/no-hedge register to discussion comments — a 2026-07-27 draft was rejected for exactly this ("The prod numbers are real. The cost has one specific shape." — wrong register for a peer's ticket).
