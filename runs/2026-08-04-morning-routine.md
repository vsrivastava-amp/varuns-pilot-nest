# 2026-08-04 — morning-routine

Session slug: `morning-routine`. Laptop Claude, interactive. Varun in-chat: "gm claude, run morning routine!"

## What ran

2026-08-04 — Full v2 path. Both connectors probed healthy before use: Slack `slack_read_user_profile` → vsrivastava, Rovo `atlassianUserInfo` → Varun Srivastava (active). No fallback needed. GETs/reads only; zero writes to any external system.

2026-08-04 — Window: deltas since `state/digest-2026-08-03.md` (cut ~11:08 ET Monday), opened deliberately behind at **10:53 ET Monday = 14:53 UTC**, Slack cutoff ts 1785768780. The 15-minute backward overlap is the 7/31 gotcha and it earned its place today — Saksham's France-AI-mode scope message landed at 10:56 Monday, inside the seam, and would otherwise have been missed twice.

2026-08-04 — Legs: nest sync, Calendar (today + tomorrow, America/New_York), Gmail (`in:inbox newer_than:1d`), Slack (5 anchor channels + 2 newly found + 5 threads + DM sweep + keyword searches), Drive (API contract doc, Qwant PM tracker), Jira (background subagent, Rovo, GETs only). Deliverable: `state/digest-2026-08-04.md`.

2026-08-04 — Two subagents used. One for the Jira delta sweep (per the skill's invariant). One to digest two Slack search results that overflowed to tool-results files (`to:me` at 66k chars, `from:<@U06PLRMF94N>` at 60k). The overflow subagent flagged its own coverage gap — both searches returned exactly page 1 of 20 — so I closed the 10:53–11:31 Monday band with a bounded re-query (`before:1785771060`). Nothing work-relevant was in it, which makes "no human DM in the window besides Antonio and Keyla" a verified finding rather than an assumption.

## Nest sync anomaly

2026-08-04 — `git pull --rebase` **refused**: unstaged changes in the working tree from another session — `playbooks/jira.md` (a committed gotcha section deleted), `tools/pciv/dev_eval_latency.py` (a `--query` flag added), plus two deleted `review/` files from 8/3. Did not stash, commit, or touch any of it, per the concurrency rule. Verified via `git fetch` + `git rev-list --count HEAD..origin/main` = **0**, so nothing was actually missed and the refusal cost nothing. Flagged to Varun in-chat.

2026-08-04 — Consequence worth remembering: today's JQL-timezone gotcha belongs in `playbooks/jira.md` but that file was dirty, so it went into `playbooks/morning-routine.md` with a pointer note. Relocate once the other session lands. Committing my own hunk was not an option without also staging their deletion.

## Findings that changed the picture

2026-08-04 — **Yesterday's digest was wrong on three flags, all in Varun's favour.** Recording them because the failure mode is the same each time: *the artifact moved somewhere the previous sweep did not look.*
- Flag #1 (AI-1542's ballparks never posted) — they were posted at 11:11 Monday, **eleven minutes after that digest was cut**. The sweep was correct at its cutoff and stale on delivery.
- Flag #4 (INFRA-3474 ignored since Friday) — the endpoint was built off-ticket, Varun validated it and commented at 15:44 Monday, and Antonio then did the DNS fix **in DM**. The ticket's silence was real and meaningless.
- Flag about AI-1583 being Not Started — it moved to In Progress at 17:53 Monday.

2026-08-04 — The generalisable lesson, and it is the 8/03 "read Slack before concluding a Jira deliverable was missed" gotcha one turn deeper: **a quiet ticket is evidence about the ticket, not about the work.** Yesterday's digest already knew that rule and still applied it too narrowly — it checked Slack channels but not DMs, and it did not re-check the window it had just written about. Today's fix was the DM sweep plus the backward overlap. Both are now load-bearing, not optional.

2026-08-04 — **The infra thread is the live item.** Antonio implemented the third of three options Varun offered on INFRA-3474 (an inbound resolver endpoint), and the ENIs he reports — `10.9.173.80`, `10.9.178.251` — are exactly the pair Varun had already validated as correct in that comment. The `10.9.174.63` / `10.9.179.109` addresses from Varun's 16:56 DM were proposed *forward targets*, unreachable per commit `d1d645f`. So the fix matches the target rather than departing from it, and the re-test is likely to pass. Antonio's "Could you check again ?" has sat ~17 hours.

2026-08-04 — **The latency budget improved materially and nobody has restated it.** Oren, 12:00 Monday, with a TDD and a CDN latency dashboard behind it: "We should expect requests from Europe to take less than 250ms assuming we can maintain performance in Vespa." That halves Dhaval's 500 ms assumption, which yesterday's digest called the largest line item in the 2-second budget. The binding constraint moved to Vespa — and this morning's VSS cache finding (`now()` at millisecond granularity means the structured-CIV-with-filters path never caches) is exactly the Vespa-side risk that conditional now rests on. Those two facts live in different channels and nobody has put them next to each other.

2026-08-04 — Q-2026-08-03-01 is answered in substance by three independent sources but still has no decision record, so it stays open with an update rather than being closed. Filing the distinction explicitly because closing it on field changes alone would manufacture a decision nobody wrote down.

## Playbook updates

2026-08-04 — Folded into `playbooks/morning-routine.md`:
- `slack_search_channels` defaults to public channels only — **this is why 8/03 could not find `#proj-query-civ-extraction`** (it is private). The 8/03 gotcha's conclusion ("treat a failed channel search as ID unknown") was right for the wrong reason; the tool is fine, the default scope is not. Corrected in place.
- `oldest=` on `slack_read_channel` filters *parents*, so a thread started before the window is invisible no matter how live its replies are. The Fastly thread had 25 replies running to 18:22 and the anchor read showed none of it, because the parent was 82 minutes pre-cutoff. This bounds the 7/31 "read the `Thread: N replies` line" shortcut to threads started inside the window.
- Both broad Slack searches now overflow; use `include_context=false` or hand the file to a subagent.
- JQL date literals are account-timezone, not UTC. `comment ~ "Varun"` cannot match @mentions; `watcher = currentUser()` is the proxy.
- New channel IDs: `#proj-query-civ-extraction` C0AKBRDB5K2 (private), `#proj-scale-serving-and-tracking` C0B623CLQET, `#vespa-optimizations-xfn` C0BMYPZ2U8H, `#temp-amazon-rtd-september-30-demo` C0BMKEHU7E1. The middle two carry live CIV/Vespa latency traffic and are now in the anchor list for the duration of the 3.0 perf work.

## needs-human.md

2026-08-04 — Appended dated updates to three existing entries (Q-2026-08-03-01, Q-2026-07-31-01, Q-2026-07-30-01). No new entries filed; nothing surfaced today was a fresh conflict rather than movement on a known one. No entry marked resolved — none has a Varun answer.

## Not done / open

2026-08-04 — RELEASE-6156 unchecked, so the INFRA-3504 (`*.id.ampfeed.com`, Done) versus INFRA-3503 (`*.di.ampfeed.com`, Not Started) hostname discrepancy is unresolved. Every Slack message in the Fastly thread says `di`.

2026-08-04 — Pre-edit text of Varun's AI-1542 comment and Artem's AI-1601 comment is unrecoverable; Jira logs no changelog for comment edits. Everything quoted is post-edit.

2026-08-04 — Did not chase `review/` drafts from other sessions, per Varun's standing 7/27 direction. Noted in the digest only where a ticket fact independently established the same thing.

2026-08-04 — Did not surface the Qwant locale/timezone tracker correction (Q-2026-07-21-01). The PM tracker is readable and was updated Monday 14:31, but the truncated content snippet did not reach the tab where the locale/timezone claim lives, and a full spreadsheet read was out of proportion to a question whose technical half is already settled three times over.
