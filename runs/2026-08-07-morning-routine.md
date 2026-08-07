# Run: morning routine — 2026-08-07 (Friday)

- 2026-08-07 10:35–11:05 EDT — Morning routine, laptop session, slug `morning-routine`. Digest: `state/digest-2026-08-07.md`.

## Coverage

- 2026-08-07 — **Two-day window.** No digest ran 8/06, so deltas cover 2026-08-05 10:45 ET → 2026-08-07 10:40 ET (seam rule: 15 min behind Wednesday's ~11:00 cutoff; Slack ts 1785941100). JQL cutoff passed in ET per the 8/04 gotcha.
- 2026-08-07 — **Connector state at start: Gmail/Calendar/Drive up, Slack/Rovo/Datadog un-handshaken** (only `authenticate`/`complete_authentication` exposed for the latter). Because three connectors were live, this was the ordinary per-session handshake gap, not the 8/05 wrong-account failure — asked Varun for `/mcp` rather than for `/login`, and all three came up on the first try. Jira ran via curl throughout and was never blocked.
- 2026-08-07 — Legs run: Jira (curl, background subagent), Gmail, Calendar, Drive (contract doc read fresh with comments), Slack (anchors + threads + DM sweep + keyword search). Datadog connected but not needed — no prod-alert question arose this window.

## What the sweep found

- 2026-08-07 — **The headline is one stale line propagating into three artifacts.** DPR-3420's description still names `/v1/intent/pciv` as the endpoint; Gontarev took the path from there into a contract-doc comment and into `github.com/admarketplace-gh/online-pciv-spec` v0.2.0; the doc's §2 was then filled in with that path *and* the pre-rename dev host, after the 8/05 17:05 rename validation had established `/v1/intent/online-civ` on `dev-online-civ-service...` with the old host NXDOMAIN. Both teams generate clients from the spec tag. Varun is the one being asked to confirm §2.
- 2026-08-07 — **Two new `needs-human.md` entries filed**: Q-2026-08-07-01 (config key `pcivExtraction` vs `civExtraction` — verified directly against DPR-3420's `customfield_11292`, which still reads `key: pcivExtraction` with only the display name struck through, while the contract doc §3.2 now says `civExtraction`; the config has already shipped via RELEASE-6169) and Q-2026-08-07-02 (does SSP continue on query text alone for *all* online-CIV failure classes, not just timeout — Gontarev asked for an explicit decision on 8/05 and nobody has ruled; dev integration Aug 8, prod Aug 12).
- 2026-08-07 — Neither Q blocks a task this session was carrying, so nothing was parked. Both sit on the online-CIV hot path and were surfaced to Varun in-chat.

## Verification note (important)

- 2026-08-07 — **`playbooks/jira.md` line ~47 says credentialed curl is denied inside a subagent and fails *silently* with success-shaped output. That did not reproduce today.** The Jira subagent ran the curl `/search/jql` path end to end (168 issues, 2 pages, 195 per-issue comment fetches) and returned real data. Because the playbook flags this as a silent-failure mode, the main session spot-checked five of its specific claims before publishing — DPR-3420, AS-13435, INFRA-3507, INFRA-3508, AI-1659 — and status/assignee/summary matched on all five. Treat the gotcha as conditional, not universal, and keep spot-checking rather than trusting either way. Playbook updated.

## Playbook updates folded in

- `playbooks/morning-routine.md` — new anchor channel `#online-civ-service` C0BP2EL5HMW; the "new channel found only via keyword search" lesson; the un-handshaken-vs-wrong-account discriminator.
- `playbooks/jira.md` — subagent-curl gotcha qualified with today's counter-example and the spot-check discipline.

## Open items carried forward

- 2026-08-07 — Eight `review/` drafts still pending, oldest 7/28. Flagged to Varun in-chat; no disposition given this session, nothing executed or deleted.
- 2026-08-07 — Q-2026-07-31-01 (50K ARES/coverage run) and Q-2026-08-03-01 (France scope) both still open and unresolved; AI-1386 has now gone 7 days without acknowledging Varun's `ad_request.amp_datacenter_id` hedge.
