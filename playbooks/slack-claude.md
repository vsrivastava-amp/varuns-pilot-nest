# Slack Claude playbook — RETIRED 2026-07-22

**Slack Claude is no longer part of the workflow** (Varun's decision, 2026-07-22 — see `log/nest--laptop.md`). Laptop sessions now have direct Slack access via the claude.ai Slack MCP with full Varun-level visibility, superseding everything below. All deposits landed before retirement (last applied: ca89703). Do not compose sweep asks or expect deposits. Kept as historical reference for the deposit-protocol design and the capability audit.

*(Living reference. Started 2026-07-21. Frozen 2026-07-22.)*

## Capabilities (self-audit relayed 2026-07-21 — re-verify occasionally)

- ✅ Read + write Slack (channels it's invited to, DMs; workspace-wide public search)
- ✅ **Artifact publish** — can publish HTML/Markdown to a claude.ai-hosted page with a shareable link. A real outward surface; good transport for long content.
- ✅ GitHub **read** — can clone/fetch the nest (github.com/vsrivastava-amp/varuns-pilot-nest)
- ✅ Local sandbox — can clone, edit, run git locally
- ❌ GitHub **write** — push is 403; GitHub MCP write tools (PRs/issues/comments) dead, account not linked. Admin action required (task in queue). **Never work around this by giving it credentials** — no PATs pasted into its session, ever (guardrail 3/4). The deposit protocol below moves *content*, not credentials.
- ❌ **HTTPS egress is a strict allowlist**: Anthropic, GitHub, AWS, GCP, pypi/npm only. Arbitrary APIs and webhooks (Slack webhooks, Atlassian, Datadog, Databricks hosts, example.com) 403 at the proxy. ⇒ **The plan's "credential-injected curl to other services" path is dead — all Jira/Datadog/Databricks API work is laptop-only, permanently.**
- ❌ Private channels / uninvited public channels
- DM mode rides Varun's OAuth → read-only by policy.

## The asymmetric bus

**Inbound (nest → Slack Claude): direct.** It pulls the repo itself. Fresh session ritual for it: clone/pull, read `CLAUDE.md`, read its relevant `map/` file.

**Outbound (Slack Claude → nest): patch deposits via Slack.** It cannot push, but it can post. Protocol:

1. In its sandbox: clone nest, make edits **following all nest conventions** (own files only: `log/*--slack.md`, `runs/*-slack.md`, `state/` files it owns).
2. Produce a unified diff: `git diff` (or `git format-patch` for multi-commit).
3. Post to the dev channel as a single message:

```
🪺 NEST DEPOSIT 2026-07-21
summary: <one line — what and why>
---
<verbatim `git diff` output>
```

4. Laptop session (or Varun pastes it into one) applies: save body → `git apply` → sanity-read the diff → commit as
   `<summary> (via slack-claude deposit)` → push.
5. Applying session reacts/notes back so Slack Claude knows it landed (until then, Slack Claude treats its deposit as un-landed and may re-post).

Rules for the applying session: read the diff before applying — deposits touch only Slack-Claude-owned files per the single-writer rule; anything touching `map/`, `PLAN.md`, `CLAUDE.md`, or playbooks is a *proposal* and goes to `REVIEW.md` instead of direct apply.

**Fallback for small facts** (no diff needed): plain message `🪺 NEST NOTE <date>: <fact>` — applying session appends it to the right log file, attributed.

**Long deposits** (big diffs, digests, channel summaries): publish as a claude.ai artifact (Markdown), post `🪺 NEST DEPOSIT <date> — <summary> — <artifact link>` in the channel. Applying session fetches the link, applies/files it. Avoids Slack message-length mangling of patch text.

## Sweep scope (how to task it)

- 2026-07-22 — Varun: don't scope sweeps to a fixed channel list. #pub-onboarding-qwant-ai is the known anchor, but plenty of other channels are likely relevant — when asking for a sweep, name the known anchors *and* explicitly invite it to search anything it judges relevant to Varun's four streams (workspace-wide search reaches public channels it isn't in). Ask it to name which channels it checked so useful ones get promoted into `map/` pointers over time.

## Current gaps / asks

- 2026-07-22 — Session-to-session capability variance is real: today's sweep session had no repo clone (so no diff-format deposit, no dedupe against the log) and reiterated it can't read #pub-onboarding-qwant-ai directly (search-index only). Treat non-diff NEST DEPOSIT blocks as *candidates*: applying session dedupes against the log before landing. Search-only sweeps can regress to stale versions of facts a fuller read already superseded (locale/tz, 2026-07-22 case) — check new lines against existing log entries.
- 2026-07-22 — **Access audit (laptop Slack MCP):** it sees everything Varun sees. Verified: direct history reads of public channels including #pub-onboarding-qwant-ai (C0AUE5JBTAP — Slack Claude is search-index-only there), private channels (#team-relevance-yield, C08GKCC9742), and search across group DMs and 1:1 DMs — including the Varun↔Slack Claude DM itself. ⇒ **New bus option:** laptop sessions can read NEST DEPOSIT messages directly from Slack (channel or DM) and apply them without Varun relaying. Deposit protocol below still describes content format; the human-paste step is now optional.
- 2026-07-22 — **Slack MCP on laptop Claude is LIVE** (claude.ai Slack connector; needs per-session `/mcp` handshake — see `playbooks/google.md` → session bridging gotcha). Verified read side: `slack_search_channels` works; also available: `slack_read_channel`, `slack_read_thread`, `slack_search_public_and_private`, user/profile lookups. **It rides Varun's OAuth ⇒ read-only by policy, same rule as DM mode** — `slack_send_message` would post *as Varun* (guardrail #2): never send; outbound drafts go to REVIEW.md. Morning sweeps can now run laptop-side with proper dedupe/thread reads; Slack Claude stays the in-workspace contributor. `playbooks/morning-routine.md` not yet updated for this.

- 2026-07-21 — Admin ask pending: GitHub write for the nest repo (would replace the deposit protocol with direct push).
- 2026-07-21 — Latency: deposits land only when a laptop session runs and someone relays. Acceptable at current volume.
