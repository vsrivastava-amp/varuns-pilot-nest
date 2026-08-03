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

### JQL / Rovo gotchas (learned 2026-07-28, delta sweep)

- **Bare datetimes in JQL resolve in the account timezone, not UTC.** `updated >= "2026-07-27 15:00"` means 15:00 **ET** for Varun's account. A sweep written against a UTC cutoff silently drops the 11:00–15:00 ET band and looks like a quiet window. Convert the cutoff to ET first, or use relative syntax (`-4h`). Cross-check: a sweep that returns nothing on a normal workday is a bug signal, not a quiet day.
- **`searchJiraIssuesUsingJql` ignores the `fields` allowlist** and returns full `description`, `project`, and avatar blobs regardless of what you ask for. ~15 issues overflows the tool-result cap. Either accept the spill-to-file and digest it, or use the curl `/search/jql` path where `fields=` is honored (much cheaper). This is the same overflow noted for `comment` on 2026-07-22, but it is not limited to `comment` — the allowlist simply does not work.
- Pattern that works for a delta sweep: light JQL for the moved-issue list, then `getJiraIssue` per issue that actually moved. Confirm anchors are unmoved rather than assuming it, and say which you confirmed.

### Sweep coverage gotchas (2026-07-31)

- **A spill-to-file result can be a *partial* page with `hasNextPage: true`.** The 7/30 run recorded "`hasNextPage` false, so no pagination gap" and that reads as general reassurance — it is not, it was true only of that query. INFRA needed 4+ pages at ~15 issues each today, and **INFRA-3476 was invisible** until a separate `created >=` count (15) failed to reconcile with the assembled list (14). Always `jq '.issues.pageInfo'` on the saved file, and cross-check new issues with an independent `created >=` count.
- **Bound the query to skip a bulk band** instead of paginating through it: `updated >= "<cutoff>" AND updated <= "<band start>"`. That returned 5 rows inline today and closed a gap in one call.
- **`status changed after "<cutoff>"` is clean JQL** for the transition list, one call for both projects.
- **A bulk band overwrites `updated` on every anchor issue**, so after one you cannot use timestamps to tell movement from field writes. Comment-check each issue in the band individually. Today's 49-issue sprint roll (7/31 09:43:56–59) hid AI-1267's real 10:49 comment behind it.
- **Credentialed curl is denied inside a subagent context.** A subagent's `curl -u "...:$ATLASSIAN_API_KEY"` was refused by the auto-mode classifier, and the script variant failed *silently* with success-shaped output and zero files written — the dangerous failure mode. The same calls run clean in the main session, so this is the classifier reacting to credentials on a subagent's command line, not a network block. Give subagents the Rovo MCP path, or have the main session run the curl.

### `createJiraIssue` timeouts — don't retry blind (2026-07-30)

`createJiraIssue` via Rovo frequently exceeds the 120s tool timeout, gets backgrounded, then aborts at 300s idle. **A client-side abort is NOT proof the write didn't land** — retrying blind duplicates tickets. Sequence that worked:

1. On timeout, run `searchJiraIssuesUsingJql` with `reporter = currentUser() AND created >= -2h` to see what actually exists.
2. If the background task is still *running* rather than failed, `TaskStop` it before retrying — otherwise a late success duplicates your retry.
3. Retry, then confirm with `searchResultMode: "count"`.

Observed 2 of 3 calls timing out, both genuinely uncommitted; retries returned in normal time, so the slowness looks transient rather than inherent.

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

**Handoff/status comments** (imperative mood): instructions and warnings only. Structure: `next steps:` then, *only when there is one worth the lines*, `footgun:`. No hedges, no questions. Worked example: AI-1542 c170926. Origin: Varun rejected a verbose draft — "I just want the exact footgun i raised, in simple text."

⚠️ **A `footgun:` section is optional, not part of the template** (Varun, in-chat 2026-07-31: "we *do not* need to include footguns in every comment (its just ocassionally helpful)"). Include one when a specific trap will cost the reader real time and they cannot reasonably foresee it. Otherwise leave it out. A ticket that manufactures footguns to fill the slot reads as padding, which is the thing STE-100 discipline exists to prevent. When a would-be footgun is really a dependency ("X has no rate limit yet"), state it as a dependency in the description instead of a warning.

## Writing ticket bodies (Varun standard, 2026-07-31)

Same sentence mechanics as comments, but **pitch a new ticket general and high level, not as a step-by-step plan.** Varun rejected a ~600-word draft as "*insanely* verbose" and asked for "way more *general* and high level, rather than a super granular step by step plan."

- Say what changed in the world, what should be measured or built, and what "done" looks like. Roughly: 2 short paragraphs plus 3-ish acceptance criteria.
- **Do not enumerate implementation steps.** No "add entry to models.json, then add eval id 7, then redeploy". The assignee knows the codebase; a numbered work plan pre-empts their judgment and rots the moment the code moves.
- Ground the ticket in verified facts anyway — read the configs, check the blocking ticket, confirm it is not a duplicate. That work belongs in the run log, not in the ticket body. **Verify deeply, write shallowly.**
- Keep only the specifics a reader cannot derive: the blocking ticket key, the current models or values being compared against, a link to the source conversation.

**Discussion comments on others' analyses** (indicative mood + questions): Varun frames this as "a conversational variant of STE-100" — same sentence mechanics, wider speech acts. Worked examples: AI-1545 c170698/c170757.
- Friendly direct opener ("Hey @Artem — dug through the CSVs"), cc whoever needs the thread.
- Structure: observation → why → evidence-in-passing → hand the thread back with questions.
- Calibrated hedges are correct, not vague: "looks concentrated" = observed, not causally confirmed. Mark epistemic status precisely.
- Ask the owner whether behavior is intended; do NOT enumerate fix directives on someone else's ticket.
- Short: 2–4 small paragraphs or a couple of numbered points. A table only if it earns its lines (Dhaval likes them).
- ⚠️ Do not apply the imperative/no-hedge register to discussion comments — a 2026-07-27 draft was rejected for exactly this ("The prod numbers are real. The cost has one specific shape." — wrong register for a peer's ticket).

**Punctuation and sentence shape (Varun, 2026-07-27, post-AI-1545 c170983):**
- Em dashes are discouraged unless really needed. Colons as rhetorical setup ("The slowdown has one specific shape:", "The decision this points at:") are a weird pattern — replace with subject-verb-object sentences ("The slowdown happens only when …", "This points at a decision about …").
- Stick to "typical high school English constructions". Do not do rhetorically interesting things. Punctuation serves a specific role, not emphasis.
- Turn hedges into facts before drafting (measure the number, read the deployed config) or cut them; hedge only genuinely unconfirmed inference. No referential language ("same question as before, sharper now") — restate the actual question so the comment is self-contained.
- Editing lenses that produced the accepted AI-1545 comment: (1) what is extraneous, (2) what is hedged that we can resolve ourselves, (3) what is referential that should be said outright.

**Headings and list intros must say the thing (Varun, 2026-07-28, on the AI-1543 draft):**
- The referential ban applies to **every heading and list intro**, not just sentences. Varun rejected "Four changes the data points at, independent of each other" and "One unrelated thing on the same service" as "extreme[ly] referential" — both point back at surrounding text instead of stating content. His instruction: **"try to say the thing."**
- A heading must be a self-contained statement a scanner can read alone. Fixes applied: → "Replicas, the memory limit, the read timeout and the retry are four separate changes"; → "The P95 latency monitor on this service cannot fire, for an unrelated reason"; → "sspEngine.intent.identifier.errors already counts failures once per request"; → "The monitor counts log lines, and its filter is an OR".
- Same trap in list bullets: lead with the subject, not a verb aimed at the reader. "A fourth replica keeps three warm pods serving through a restart" beats "Add a replica, 3 to 4." The declarative form also avoids issuing directives on someone else's ticket.
- Watch these tells: "this", "these", "the two", "any of this", "one thing", "it all", and any heading that is a bare label ("What the monitor measures") rather than a claim.

## INFRA request conventions (board-studied 2026-07-28, 50 recent tickets + precedents)

- **Task** issue type, **no labels, no components, assignee EMPTY** (infra triages + self-assigns; frequent: Pun Tong, Ivan Trichev, Antonio Flores Perez, Oren Forer). Turnaround same-day–4d when well-specified (INFRA-3462 next-day).
- Structure: 1–2 sentences context → enumerated asks with **exact identifiers** (SA names, akeyless paths in `app/env/dc/KEY` form, full IAM action lists, Bitbucket links to the exact file). "Same setup pattern as <existing app>" is phrasing infra responds well to. Conversational politeness normal.
- Anti-patterns (observed to cost days): vague permission verbs (enumerate actions, not "read/write"), env ambiguity (say "dev EKS ric1" up front), grab-bag multi-ask tickets (INFRA-866: 18 months). Prod-scoped access asks need a manager-approval comment; dev-scoped skip it; CC'ing the manager preempts the round-trip.
- **Bedrock-specific (INFRA-2973 lesson): IAM actions alone are insufficient** — the account's model access agreement / marketplace subscription must also be enabled per model; ask infra to confirm it explicitly.
- No general infra-request Slack channel exists (searched 2026-07-28) — infra works from the board; nudge path is a DM (Pun Tong for llm-eval-adjacent infra).

### "Not Started" does not mean "not backlogged" (2026-08-03)

Backlog membership lives in the **sprint field**, not `status`. A ticket pulled out of the active sprint keeps `status: Not Started`, so status alone is never evidence that a promised backlog move did not happen. A 2026-08-03 digest flagged AI-1603 as "said he would move it to backlog, still Not Started" and Varun had in fact already moved it. Check `sprint` (or the board) before writing any flag about backlog placement, and do not treat `Not Started` as a hygiene finding on its own.

### Read this file before drafting any Jira text (2026-08-03)

A morning-routine session drafted an AI-1542 comment without reading this playbook and produced ~600 words in the shape of a run-log entry: a "Measurement setup." label heading, two overlapping tables, and a closing caveats block. Varun's response was that it "violates almost every convention." The rewrite that worked was ~230 words, one table carrying both the provider floor and the as-deployed numbers, and `next steps:` at the end.

The failure was procedural, not stylistic ignorance — the style section above already said all of it. Two rules that carry the most weight when a comment reports measurements:

- **Measurement setup and caveats belong in the run log, not the comment.** One sentence of method is enough (origin, sample count, prompt size). A reader who needs the rest opens the attached raw rows.
- **Merge tables.** Two tables with a shared key are one table with more columns. Overlapping tables read as a dump rather than a finding.
