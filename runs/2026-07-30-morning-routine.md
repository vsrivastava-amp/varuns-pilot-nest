# Run — 2026-07-30 morning-routine

Session slug: `morning-routine`. Machine clock verified `Thu Jul 30 09:53:31 EDT 2026` (EDT, not Pacific as CLAUDE.md still says — the 2026-07-23 gotcha still holds).

## What ran

Full v2 path — both connector families probed healthy before sweeping, per playbook preflight:
- Slack `slack_read_user_profile` → vsrivastava, ML Engineer. Alive.
- Rovo `atlassianUserInfo` → account active. Alive.
- No fallback needed; nothing omitted from the digest for access reasons.

Delta window: since `state/digest-2026-07-29.md` (~10:40 ET Wed = 14:40 UTC). Slack cutoff ts `1785333000`.

Legs: Calendar (today + tomorrow, `timeZone` passed explicitly), Gmail (`in:inbox newer_than:1d`), Jira (Rovo, GETs only), Slack (both anchor channels + three keyword/DM searches + four follow-up channel reads).

Output: `state/digest-2026-07-30.md`.

## Findings worth carrying forward

**The headline is a new direct ask of Varun on AI-1386** — Oren Forer wants a relevancy comparison of us-west (grouped topology) against us-east (flat), one week post-launch, and routed it through Neena rather than to Varun directly. Two complications landed on top of it before the sweep even ran: Dhaval disputes that region is a valid cut for relevancy at all ("we can look at trends since group topology launch though"), and Oren confirmed this morning that grouped topology also sits on upgraded silicon (graviton3 → graviton4, ~30% expected query-performance gain if CPU-bound). So the requested comparison currently confounds topology, targetHits, and hardware. Flagged all three separately in the digest rather than as one flag with parentheticals — the 2026-07-27 flag-phrasing gotcha.

**AI-1542's business-team deadline is tomorrow (Friday 8/1)** and the ticket has not moved since 7/28. That deadline is Varun's own commitment recorded in a 7/27 comment, not something anyone chased him on, so it was at real risk of being invisible on a Thursday morning.

**The 3.0 intent-object spec was cut yesterday afternoon** (Norbert, `#proj-amp-discover-3-0`): `categories[].name`, `categories[].path`, `iabct31`, `product.ids[]`, `product.attributes.age.value/range/text`, `targets[].placement_ids` all removed. This narrows the pCIV output contract to bare GPC ids and bears directly on the parked nest task to expand `gpc_taxonomy.json` 75→213 in sync with the prompt GPC section, which was scoped against id+name. Did NOT act on it — that task is claimed/blocked elsewhere and the demo repo is read-only for agents. Surfaced it in the digest as a gap and pointed at today's 1:00 PM sync as the place to confirm.

**New: Sezzle incident channel** `#issue-sezzle-investigation-20260729` (C0BLGGT2TGT), opened 7/29 12:26 ET by Pinkel. Six filed defects against 3.0 API filters; Saksham's working root cause is inefficient querying causing timeouts. Dhaval's post-mortem question explicitly names Artem's latency-comparison test as something that should have caught it, which touches Varun's latency methodology. Live again this morning with a feed data-quality find: 36,474 active products with gender/title-gender mismatch.

## needs-human.md

Filed **Q-2026-07-30-01 — which model does the online pCIV service actually ship with?** Five live framings (Saksham's nano, AI-1540's "GPT-Nano", Varun's Ministral 8B, the four Bedrock candidates DM'd to Yaarit, and Yaarit's AI-1576 nano-vs-gpt-5-mini with evals 104/105 already registered). Two prior digests noted this was "one word from a needs-human entry"; AI-1576 made it a fifth framing and the 8/1 deadline made it load-bearing, so it got filed rather than noted again. **Peripheral to this task** (the digest didn't depend on the answer), so per the hot-path rule it was filed and the run continued — no build work was done around the unknown.

Also appended a third-confirmation update to **Q-2026-07-21-01** (Qwant locale/timezone): Stephen's stage payload this morning carries both fields again. Technical question looks settled; only Claire's tracker correction is open. Left the entry open — closing it is Varun's call, and it's another agent's entry.

## Not done / left alone

- Did **not** RSVP anything on the calendar, comment on AI-1386, or answer Norbert's fallback-logic validation ask. All outward-facing; guardrails 1/2/6/8.
- Did **not** enumerate other sessions' pending `review/` drafts (Varun's standing preference); noted only that the 7/29 ai1538 set bears on today's 1:00 PM sync.
- AI-1588's stated "P99 < 2s" target contradicts Varun's own AI-1542 comment saying no target is agreed. Surfaced as a carryover gap; not edited — both are Varun's own tickets and picking one would manufacture the decision.

## Sprint-planning tickets — Jira WRITES performed (Varun-directed in-chat)

Varun asked in-chat during sprint planning for backlog candidates from `tasks/`, then directed "just go ahead and file the tickets." That in-chat direction is the approval (morning-routine gotcha 2026-07-22); logging the writes here as required. All three created in project AI, type per line, assigned to Varun, status Not Started:

- **AI-1603** — Set up recurring keyword GPC reclassification (Story)
- **AI-1604** — Investigate prompt caching and providers for online pCIV (Spike)
- **AI-1605** — Online pCIV rate-limit increase and client-side throttling (Task)

Drafts deleted from `review/` on filing, per convention.

**Varun edited all three in Jira same-day (titles above are HIS final versions, not the drafted ones).** Re-fetched 11:55 to keep this record accurate. AI-1603 untouched. AI-1604 title shortened, body unchanged. **AI-1605 body trimmed to the quota half only** — the entire client-side-throttling section was removed, along with the AI-1598 justification and the `564079877134` account reference, while the title still says "and client-side throttling." Flagged the title/body mismatch to him in-chat; not corrected by me, since trimming may have been deliberate and the ticket is his. If the throttling scope is meant to survive, it currently exists in no ticket body anywhere.

Grouping rationale (his constraint was "at most 3-4 new tickets, fold the rest"): Bedrock prompt caching and the OpenAI us-east question merged into one spike (AI-1604) because both answer "how do we make the serving hop fast." The rate-limit increase was deliberately split OUT of that spike into AI-1605 — it is an external ask with no approval SLA and must not sit behind an investigation. Client-side throttling folded into AI-1605 as the mitigation for the same constraint, justified by AI-1598 (llm-evaluator-service failing on rate limiting; online pCIV runs the same image).

**Pushed back on one fold and Varun did not object:** he suggested folding the regular-cadence ask into AI-1474. AI-1474 is In Review with a closing comment already drafted, so new ongoing scope folded there dies at close. Filed as separate AI-1603 instead, with the reasoning stated in the ticket body.

Folded, no new ticket: stage/prod infra → AI-1538 scope (the stage INFRA ask is already drafted at `review/2026-07-29-ai1538-stage-infra-jira.txt` and gates the rollout PRs — merging overlays first crash-loops pods on missing secrets). AI-1474 in-progress work → update on AI-1474. SSP→pCIV integration → Varun explicitly deferred; not his to own.

⚠️ **Not done, left for Varun**: no formal Jira issue links were created between the new tickets and their parents (AI-1474 / AI-1588 / AI-1538). Bodies reference the keys as text only. Flagged to him in-chat.

## MCP gotcha — createJiraIssue timeouts (2026-07-30)

`createJiraIssue` via Rovo is slow enough to blow the 120s tool timeout and get backgrounded, then abort at 300s idle. **Two of three calls did this, and neither had actually created anything** — but a client-side abort is NOT proof the server didn't commit the write. Sequence that avoided duplicates:

1. Call times out → do NOT retry blind.
2. `searchJiraIssuesUsingJql` with `reporter = currentUser() AND created >= -2h` to see what actually landed.
3. If the background task is still *running* (not failed), `TaskStop` it first — otherwise a late success duplicates the retry.
4. Retry, then re-verify with `searchResultMode: "count"`.

Retries on the second attempt returned in normal time, so the slowness looks transient rather than inherent.

## Playbook updates

Two gotchas folded into `playbooks/morning-routine.md`:
- The broad `project in (AI, INFRA)` Jira sweep overflows context even *without* `comment` in fields (139k chars for 28 issues on a ~1-day window). The 2026-07-22 gotcha said omitting `comment` was enough; it isn't. Updated with the working shape: narrow key-list query inline for status, subagent for the saved overflow file plus per-anchor comment fetches.
- `Read` refused `playbooks/morning-routine.md` twice this session as an unchanged duplicate when it had never been read in-session. `cat` via Bash worked. Noted so the next session doesn't lose time to it.
