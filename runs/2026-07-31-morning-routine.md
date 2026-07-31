# Run — 2026-07-31 morning routine

2026-07-31 — Session slug `morning-routine`. Invoked via `/morning-routine` at 10:41 EDT. Machine clock verified EDT via `date` (CLAUDE.md still says Pacific — the 7/23 gotcha stands).
2026-07-31 — Nest sync: `git pull --rebase` reported up to date. `git log --oneline -15` reviewed. Queue, `needs-human.md` and `review/` skimmed. Last digest was `state/digest-2026-07-30.md` at 10:26, so the delta cutoff is 2026-07-30 14:00 UTC = 10:00 ET, Slack ts 1785420000.
2026-07-31 — Connector probe: Slack `slack_read_user_profile` and Rovo `atlassianUserInfo` both returned Varun's account. Full v2 path, no fallback. Note Rovo's extended profile still reads job title "Machine Learning Intern" while Slack reads "ML Engineer".
2026-07-31 — Calendar swept for today and tomorrow with explicit `timeZone: America/New_York`. Two events today, nothing Saturday.
2026-07-31 — Gmail swept with `in:inbox newer_than:1d`, 30-thread estimate. Jira notification mail used only as pointers; state re-derived from Jira.
2026-07-31 — Slack swept: both anchor channels read directly, then every thread with replies newer than the cutoff. Keyword searches on `pCIV`, `Qwant`, `latency`, plus `to:me`. `to:me after:2026-07-30` returned only bot DMs (Jira, Lattice, Google Calendar), which is how the "no human DM since cutoff" claim was verified rather than assumed. That also confirms Sunil has not answered the AI-1474 eval-config question.
2026-07-31 — Channels read beyond the two anchors: `#proj-amp-discover-3-0` (C0ATZNKJCTG), `#proj-query-civ-extraction` (C0AKBRDB5K2), `#issue-sezzle-investigation-20260729` (C0BLGGT2TGT), `#prod-relevance-yield-alerts` (C0B22A0CG74).
2026-07-31 — Jira leg ran as a background subagent per the playbook. It reported full pagination coverage: AI delta 77 issues, INFRA paginated to exhaustion plus a bounded-window query, cross-checked with `created >=` and `status changed after`. Its method notes are folded into `playbooks/jira.md`.
2026-07-31 — Drive: read Yaarit's "SSP - Online pCIV Extraction: API Contract" (file id `11oVe4pk68Dg3qjmlJfuMYcScaweLwrxSpBMI02Ak1_Y`), shared 7/30 14:47 with edit access, last modified 10:29 today. Found two internal contradictions — `queries[].qt` in the field table versus `queries[].prompt`/`response` in the request shape, and a response `evalId` documented as echoed from a request that carries `placementID` instead. Recorded in the digest, not edited: the doc is Yaarit's and agents do not write to it.

## Deliverables

2026-07-31 — `state/digest-2026-07-31.md` written and committed. 13 attention flags, ordered by consequence.
2026-07-31 — `needs-human.md`: filed **Q-2026-07-31-01** (AI-1386 offline ARES/coverage test). Commit `7fcc1ea`.
2026-07-31 — `review/2026-07-31-luna-offline-civ-ares-jira.txt`: Varun-requested ticket draft, evaluate `gpt-5-6-luna` for offline CIV and ARES. Commit `f39c0e4`. **Awaiting his disposition — not filed.**

## The seam miss, and why it matters

2026-07-31 — Dhaval's most directive AI-1386 comment (c171371) was created 7/30 09:58:25, which is 95 seconds before yesterday's 10:00 cutoff. Yesterday's digest was cut at ~10:05 and captured Oren's 09:03 comment but not this one. Today's window started at the cutoff, so it would have been missed twice. It surfaced only because a subagent was asked for verbatim quotes in the 09:00–10:00 band.
2026-07-31 — The content is consequential: "No need to run any offline ARES/coverage tests." Yesterday's digest had recorded Neena's Option 2 offline ARES/coverage run as work landing on Varun, unaware it had already been waved off an hour earlier. Neena then re-proposed the same test at 09:38 today and asked Dhaval and Oren to correct her; Dhaval replied at 10:07 on a different question and left that line alone.
2026-07-31 — Fix folded into `playbooks/morning-routine.md`: overlap the Jira window ~15 minutes behind the previous cutoff rather than starting exactly at it.

## Corrections to the subagent's report

2026-07-31 — The subagent reported `review/2026-07-30-infra3474-validation-green.txt` as untracked. It is committed (`6a16e09`, another session). Verified via `git status --short`. Do not act on another session's drafts regardless (Varun, in-chat 2026-07-27).
2026-07-31 — The subagent reported the credentialed curl path in `playbooks/jira.md` as unusable under the auto-mode classifier. That is true inside a subagent context but **not** in the main session: three `/usr/bin/curl -u "...:$ATLASSIAN_API_KEY"` calls ran clean here today. Recorded with that scope rather than as a blanket claim.

## New issues filed since the cutoff (15)

| Key | Created | Reporter → Assignee | Status | Summary |
|---|---|---|---|---|
| AI-1600 | 7/30 10:46 | Steven Wu → Rajasekhar Cheruku | Done | Valkey instance for online feature store, stage |
| AI-1601 | 7/30 11:01 | Artem → Tribikram | Not Started | Sample of pciv to verify merged product+text ads retrieval |
| AI-1602 | 7/30 11:07 | Artem → Artem | Not Started | Test suite validating AAS merged text/product ads retrieval |
| AI-1603 | 7/30 11:32 | Varun → Varun | Not Started | Set up recurring keyword GPC reclassification |
| AI-1604 | 7/30 11:33 | Varun → Varun | Not Started | Investigate prompt caching and providers for online pCIV |
| AI-1605 | 7/30 11:34 | Varun → Varun | Not Started | Online pCIV rate-limit increase and client-side throttling |
| INFRA-3476 | 7/30 12:14 | Dan Casey → Dan Casey | Not Started | Public DNS workflow and provider DR (epic) |
| AI-1606 | 7/30 12:21 | Oren → Saksham | Not Started | Memory leak in the intent-identifier-service |
| INFRA-3477 | 7/30 14:03 | Pun Tong → Pun Tong | Done | Add eks-dev-ric1-01 cluster to Argo CD |
| INFRA-3478 | 7/30 16:31 | Kfir Shay → Oren | Not Started | Core metrics dashboard improvement |
| AI-1607 | 7/30 17:01 | Alexandr Gontarev → Artem | Ready for Release | AAS release with amp-discover-model 1.2.35 |
| AI-1608 | 7/30 20:14 | Yaarit → Yaarit | Rejected | elme-yield prod-ric1 memory bump |
| AI-1609 | 7/30 22:07 | Joseph → Aliaksandr | In Progress | Set overfetch boundaries for AAS |
| INFRA-3479 | 7/31 05:26 | Artem → unassigned | Not Started | Vespa console access for Aliaksandr Ikonnikau |
| AI-1610 | 7/31 10:36 | Bhupesh → Bhupesh | Not Started | Relevancy/perf testing for enriching input queries with civ fields |

## Bulk-noise bands filtered

2026-07-31 — AI: 7/31 09:43:56.9–09:43:59.8, 49 issues in 2.9 seconds. Saksham's sprint roll. Every one has its newest comment before the cutoff and 13 have zero comments ever. Because the band overwrote `updated` on every anchor, the subagent comment-checked all 49 individually rather than trusting timestamps — that is how AI-1267's real 10:49 comment was separated out.
2026-07-31 — INFRA: 7/30 15:17:15–15:23:39, 45+ issues, board grooming plus a 12-ticket rejection sweep. All 12 rejected tickets have zero comments ever, so nothing explains the sweep. **INFRA-3250 "move to group topology in prod" is one of them**, rejected the same afternoon Oren committed to the Monday traffic shift. Probably housekeeping in favour of AI-1386, but unrecorded either way.
2026-07-31 — AI-1584/1585/1586/1587 reassigned to Aliaksandr Ikonnikau 7/30 22:12:51–22:13:59. Real ownership change, no discussion.

## Grounding done for the Luna ticket draft

2026-07-31 — Read `~/Documents/llm-evaluator-service` (checkout sits on branch `feat-civ-eval-6-gemini`) and `origin/main`. Facts used in the draft: civ eval 2 active = `gpt-5-4-nano` / `civ_extraction.txt` / b40 / c20; relevancy eval 1 active = `gpt-5-mini` / `hybrid_prompt_v1.txt` / group 50 / concurrency 80; `origin/main` civ eval ids are 2–6 with 6 = `gemini-3-6-flash`, so 7 is next free; relevancy has only eval 1, so 2 is next free.
2026-07-31 — `llm/config/models.json` has **no** `gpt-5-6-luna` entry. Registry keys present: gpt-5-mini, gpt-5-4-nano, gpt-5-nano, gpt-5-2, gemini-3-6-flash, haiku-4.5, sonnet-4.5, gemma-3-12b, gemini-2.5-pro. So Luna needs a registry entry, not just an eval config.
2026-07-31 — Per-domain wrapper naming confirmed from the registry: `gemini-3-6-flash` carries `{default: ai-gemini-3-6-flash, civ: civ-gemini-3-6-flash}` and `gpt-5-mini` carries `{default, relevancy: ares-gpt-5-mini, civ: civ-gpt-5-mini}`. So Luna needs `civ-gpt-5-6-luna` and `ares-gpt-5-6-luna`, and whether INFRA-3462 creates the domain wrappers or only the default is an open question for Pun rather than an assumption.
2026-07-31 — INFRA-3462 verified live: In Review, Pun Tong, last updated 7/30 15:18 (a sprint-field edit). It gates the ticket.
2026-07-31 — Duplicate check: JQL `(text ~ "luna" OR text ~ "gpt-5.6") AND project in (AI, INFRA)` returned only AI-1538, AI-1474 and INFRA-3462. No existing Luna evaluation ticket.
2026-07-31 — AI-1474's parent is AI-1473 "ML/AI: Emerging Business Issues", used as the suggested placement.
2026-07-31 — The 80% price-cut figure is attributed to Dhaval in the draft rather than asserted, and confirming Luna's real list price is an acceptance criterion.

## Notes for the next session

2026-07-31 — AI-1542's deadline is today and the Mantle blocker is gone. The finalist latency run needs `pciv_extraction.txt` (~3.6k prompt) rather than `civ_extraction.txt` (18–23k), and n>=50 per eval. This morning's four Mantle samples are functional evidence only.
2026-07-31 — INFRA-3456 scaled the CIV DynamoDB table back to baseline on 7/30 (read 694 RCUs, write 434 WCUs). Check this before any AI-1474 retry pass at volume.
2026-07-31 — Three independent signals now point at GPC handling as the bottleneck rather than taxonomy coverage: Dhaval on Vespa indexing/querying, Saksham proposing GPC leave the L2 filter, and the 7/29 spec cut reducing GPC to bare ids. The queue's taxonomy-expansion task was scoped against the old premise and should be re-checked before it starts.
