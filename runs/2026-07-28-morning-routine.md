# Run — 2026-07-28 morning routine

Session slug: `morning-routine`. Machine clock verified EDT via `date` (10:22 ET at start).

## What ran

- 2026-07-28 — Nest sync: local HEAD already equal to `origin/main` (2282292), so `git pull --rebase` was unnecessary. The pull did error first on unstaged changes (four `review/` deletions from another session, plus stray `.DS_Store` files). Left untouched — not this session's work, and no rebase was needed once HEAD was confirmed current.
- 2026-07-28 — Connector preflight: Slack `slack_read_user_profile` → vsrivastava, Rovo `atlassianUserInfo` → Varun Srivastava, both active. v2 path ran (no fallback needed).
- 2026-07-28 — Cutoff for all sweeps: **2026-07-27 11:00 ET / 15:00 UTC** (epoch 1785164400), the write time of `state/digest-2026-07-27.md`.
- 2026-07-28 — Legs run laptop-side: Calendar (today + tomorrow, plus a `fullText=Sprint` sweep out to 8/8 to pin the re-cut ceremony series), Gmail (`in:inbox newer_than:1d`), Slack (2 anchor channels + group DM + 3 DMs + 4 keyword searches + 3 thread reads), Jira (background subagent, GETs only).
- 2026-07-28 — Deliverable: `state/digest-2026-07-28.md`, attention flags first.

## Jira sweep coverage (subagent, GETs only)

All sweeps paginated to completion; both auth paths probed healthy. `project = AI` since cutoff ran as two ET slices after the timezone bug below was caught (33 issues total). `assignee/reporter = currentUser()` over the last week (9 issues). `text ~ "PCIV"` (13) and `text ~ "Qwant"` (12) since 7/27. All 15 carried anchors checked individually. 54 issue keys extracted from `map/*.md`; the 17 non-AI keys queried by key, zero moved. No sweep failed or was truncated.

## Verification done before flagging

- **AI-1538 blocked by AI-1576** — re-fetched AI-1576 from source myself rather than trusting the subagent's paraphrase (per the 2026-07-22 gotcha). Confirmed: link type `Blocks`, inward "is blocked by", AI-1576 assignee + reporter Yaarit Even, status Not Started, created 7/27 11:11:58 ET, final AC "Prompt + contract doc shared with Varun/AI-1538." Also confirmed the ticket puts service build/deploy explicitly out of its own scope, which is why the digest says the AI-1538 build can continue while the ticket cannot close.
- **Subagent's "possible conflict" (7/31 vs Aug 24) was a false positive** — checked against `map/pciv-live-integration.md` and `log/pciv-online-service.md`: 7/31 is the Qwant ghost-endpoint go-live, Aug 24 is production go-live, and the nest has recorded both since 7/23. No `needs-human.md` entry filed. Worth noting the pattern: a subagent seeing one date on a ticket and a different date in yesterday's digest will read it as a contradiction unless it reads `map/` first.
- **Aug 24 and the vector-search FF** both grepped against the nest before being called new. Aug 24: already recorded (not news, kept out of flags). Vector-search FF enablement: absent from the nest, so genuinely new → flag 8.

## Deltas that closed yesterday's flags

- Yesterday flag 1 (Saksham waiting on scope answer): **closed** — Varun answered in DM 7/27 11:07 ET with the full three-part scope note.
- Yesterday carryover "Elisa's L2s/json question still unanswered": **stale, corrected in today's digest** — Varun answered it 7/24 10:39 ET in group DM C0BJPQHFFGC with `gpc_taxonomy_L1_L2.json` attached.
- Yesterday flag 9 (AI-1546 status mismatch): resolved by Artem's overnight sweep, AI-1546 now Done.

## Open / for Varun

- Two decision-shaped items surfaced and deliberately **not** filed in `needs-human.md` — neither blocks a task this session was building, and filing is Varun's call: (1) three unreconciled model assumptions on the online pCIV path (Saksham's gpt-5.4-nano, AI-1540's GPT-Nano, Varun's own Bedrock Ministral 8B in c170943, plus AI-1576's ~4k prompt budget); (2) the eval-id 4/6 collision between `tasks/ai-1474-release.md` and Yaarit's AI-1570 swap.
- Q-2026-07-21-01 unchanged, no movement.
- `AI-1583` (Saksham, this morning) covers the same GPC prefix-matching mechanism as Varun's AI-1545 comment from 17 hours earlier, with no link to AI-1545. Flagged, not acted on.

## Playbook updates folded in

- `playbooks/jira.md` — new "JQL / Rovo gotchas" section: bare JQL datetimes resolve in the **account timezone, not UTC** (this silently dropped a 4-hour band on the first sweep run, caught by the subagent and re-sliced); `searchJiraIssuesUsingJql` ignores the `fields` allowlist entirely, not just for `comment`.
- `playbooks/morning-routine.md` — new gotcha: a near-silent anchor channel means go read the active threads, not that the day was quiet. Records the anchor-read → keyword-search → per-`thread_ts` sequence, and that `oldest` on `slack_read_thread` does not reliably filter replies.

## Not done

- Did not touch other sessions' pending `review/` drafts (Varun, in-chat 2026-07-27: do not worry about drafts not pertaining to this session). This session produced no outbound drafts.
- Did not sweep `#platform-alerts` / `#prod-relevance-yield-alerts` for overnight incidents. Out of the routine's scope, but worth considering now that Varun is on ELME Level 1 from 7/29.
