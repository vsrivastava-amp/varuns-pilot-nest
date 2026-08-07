# Needs Human

Varun's decision inbox. Conflicts, contradictions, and open decisions that only human conversation can resolve — the stuff his job actually consists of. Agents file here instead of silently picking a side; Varun resolves in the background and answers inline (one line is enough) or just tells any session.

**Lifecycle:** agent appends entry (status `open`) → Varun adds a `resolution:` line (status `answered`) → next steward session harvests: durable *why* → `log/`, changed facts → `map/`, then deletes the entry (git history keeps it). File short = inbox clean.

**Rules:** append at bottom; write only your own entries; this file is the one exception to single-writer (shared inbox — slack-claude contributes via deposits). Never mark another agent's entry resolved without a Varun answer.

**Hot-path rule (Varun, 2026-07-22):** if the open question sits on your current task's hot path, the task is blocked — *let it stay blocked*. Park it in the queue referencing the Q-entry. Don't build around the unknown or proceed on the likely answer; that manufactures a decision nobody made. Blocked-and-filed beats built-on-sand.

Entry template:

```
## Q-YYYY-MM-DD-<n> — <short title> (open)
- raised: <date>, <agent>
- project: <map file>
- conflict/decision: <the two sides, or the missing decision>
- why it matters: <what's blocked or what calcifies wrong>
- ask: <the one question, answerable in one line>
- resolution: (pending)
```

---

## Q-2026-07-21-01 — Qwant: can they send locale + timezone? (open)
- raised: 2026-07-21, slack-claude (digest), filed by laptop
- project: pciv-live-integration
- conflict/decision: Claire Conklin's tracker records Qwant as unable to send region, locale, AND timezone. Dhaval Shah pushed back (only region is truly impossible; locale/timezone are easy and not privacy-sensitive), and Camille Baudou later relayed Qwant saying locale & timezone "should be fine." Tracker and thread now disagree.
- why it matters: locale/timezone availability changes pCIV extraction and eval assumptions downstream; if the tracker's "cannot" calcifies, integration gets designed against the wrong constraint before the mid-Aug launch.
- ask: confirm with Claire/Camille what Qwant will actually send (locale? timezone?) and get the tracker corrected — then answer here.
- 2026-07-22 update: message draft parked in REVIEW.md with a HOLD-unless recommendation — Dhaval/Camille are already working this in-channel; only escalate if our extraction/eval code consumes these fields (Varun knows). Slack Claude monitoring for self-resolution.
- 2026-07-27 update: the Claire HOLD draft was retired in the REVIEW.md deprecation (git history keeps it). New evidence toward resolution: Norbert's 7/24 sandbox test request to the ghost endpoint includes `locale: en-US` AND a full `timezone` object — consistent with Camille's "should be fine"; the tracker correction is what remains.
- 2026-07-30 update: Stephen Ince's stage 3.0 test payload in #proj-amp-discover-3-0 (7/30 09:35 ET) again carries `locale: "en-US"` and `timezone: {name, offsetMinutes}`. Third independent confirmation. The technical question is effectively settled; only the tracker correction is open.
- resolution: (pending)

## Q-2026-07-30-01 — Which model does the online pCIV service actually ship with? (open)
- raised: 2026-07-30, morning-routine
- project: map/pciv-live-integration (AI-1538 / AI-1542 / AI-1576)
- conflict/decision: five different framings of the production model choice exist and no ticket reconciles them.
  1. `gpt-5.4-nano` — Saksham's 5-step DM work order (7/28), "quick-and-dirty latency check with nano".
  2. "GPT-Nano" — AI-1540.
  3. `Ministral 8B` — Varun's own AI-1538 comment.
  4. Four Bedrock candidates — Varun's DM to Yaarit 7/29 10:30 ET: Gemma 4 31B, GPT-5.6 Luna, Qwen3 Next 80B, Ministral 3 14B (with gpt-5.4-nano as a Databricks-only baseline, not on Bedrock).
  5. `gpt-5-4-nano` vs `gpt-5-mini` — Yaarit's AI-1576 comment (7/29 11:10 ET) registers evals 104/105 for exactly these two and says the production choice is "pending cost/latency/accuracy tradeoff discussion with Saksham/Dhaval". She measured nano ~1.0–1.2s vs mini ~2.1s, with mini "meaningfully better at GPC assignment on ambiguous/multi-item queries".
- why it matters: AI-1542's latency numbers are due to the business team **before Friday 2026-08-01** (Varun's own commitment; Qwant is OOO in August). Which models get benchmarked determines whether that deliverable answers the question anyone is actually asking. Benchmarking the Bedrock four while the real decision is nano-vs-mini would burn the deadline on the wrong comparison. INFRA-3474 has already attached Bedrock model-access agreements for framing 4's models specifically.
- ask: for the numbers due 8/1, is the comparison nano vs gpt-5-mini (Yaarit's framing), or the four Bedrock candidates, or both?
- 2026-08-04 update: the deliverable answered the question in practice without anyone deciding it. Varun's AI-1542 comment (8/3 11:11 ET) benchmarks the **four Bedrock candidates**, not Yaarit's nano-vs-mini framing: Qwen3-Next-80B 399 ms, Ministral 3 14B 486 ms, Gemma 4 31B 615 ms, GPT-5.6 Luna 741 ms (provider p50, 3.3k-token prompt). Qwen3 is now the fastest measured, which sharpens Dhaval's still-unanswered "How is Qwen3's accuracy?" — speed has stopped being the discriminator and accuracy has become it. gpt-5.4-nano via direct OpenAI remains only "Interested in trying". No ticket records a choice, and AI-1620's 14/Aug delivery date now sits in front of the decision.
- resolution: (pending)

## Q-2026-07-30-02 — What did “a certain regression needs to be made to main” mean for AI-1474? (answered)
- raised: 2026-07-30, ai1474-release-resume
- project: map/llm-eval-service (AI-1474)
- conflict/decision: Varun's 2026-07-29 handoff says Tribikram's latest PR means “a certain regression needs to be made to main.” Fresh Bitbucket history shows Tribikram's latest merged service PR is #44 (`9fa18ec`, AI-1361), already in main and the Gemini branch. The phrase could mean fixing/reverting a regression from that PR, or running a regression test before the AI-1474 merge.
- why it matters: the answer changes the service PR scope. The hot-path rule forbids changing or testing around the likely interpretation.
- ask: did you mean “run regression tests against current main,” or is there a specific Tribikram change that must be fixed/reverted?
- resolution: 2026-07-30 Varun confirmed that Tribikram's most recent PR to main, PR #44 / AI-1361, must be reverted. The corresponding Jira discussion is the decision record.

## Q-2026-07-31-01 — Does the grouped-topology plan include an offline ARES/coverage test, or not? (open)
- raised: 2026-07-31, morning-routine
- project: map/vespa (AI-1386)
- conflict/decision: Dhaval killed the offline test and Neena's current plan still contains it.
  - Dhaval, AI-1386 c171371, 2026-07-30 09:58 ET: "No need to run any offline ARES/coverage tests. A/B test will provide a lot more reliable results without any effort once we start the test. Let's please not talk about or debate the A/B test anymore - let's just start it."
  - Neena, AI-1386 c171462, 2026-07-31 09:38 ET, posted as her summary of "the latest plan of action" and explicitly asking Dhaval and Oren to correct her: "we run a ARES/coverage test offline for our 50K Superlinked queries (on prod or prod-test cluster)".
  - Dhaval replied to that comment at 10:07 ET (c171468) but answered only her question about making Vespa queries efficient. He did not correct the offline-test line. Oren replied at 10:27 ET (c171476) about traffic shifting and housekeeping. Neither confirmed nor withdrew the offline test.
- why it matters: the 50K Superlinked ARES/coverage run lands on Varun's side. It is the work item inside Neena's Option 2. Varun's 2026-07-30 digest recorded it as his, before anyone here had seen that Dhaval had already waved it off an hour earlier. Silence now reads as assent, and a 50K offline run is real effort spent against an explicit "no need".
- ask: is the offline ARES/coverage test on the 50K Superlinked queries in scope for Varun, or did Dhaval's 7/30 09:58 comment retire it?
- 2026-08-05 update: Dhaval answered the *capability* question warmly while the *scope* question stayed open. Saksham asked in `#team-relevance-yield` (8/04 16:54) whether Vespa staging results can be run through ARES and how involved it is; Dhaval replied 18:44: "Totally doable and not that difficult. Neena Sulakhe did something similar recently for grouped topology testing. No concerns on costs or processes afaik." That is the opposite tone from his 7/30 "No need to run any offline ARES/coverage tests", and it was said about the same mechanism, but it answers "can we" rather than "should Varun". AI-1386 still has zero new comments and the 50K run still lands on Varun by default. The ask below is unchanged.
- 2026-08-04 update: still nothing. AI-1386 gained zero comments in four days; its newest comment remains Varun's own 7/31 10:59 hedge on `ad_request.amp_datacenter_id`, which Neena and Oren have also never acknowledged. Saksham re-parented the ticket AI-1448 → AI-1637 at 17:50 on 8/3, moving it across initiatives (INFRA-3467 → AS-13433) with no comment; AI-1637 is empty scaffolding with two lines of description and zero comments. The 50K run still lands on Varun by default, and the re-parent makes the question easier to lose rather than easier to answer.
- resolution: (pending)

## Q-2026-08-03-01 — Is online CIV extraction still in scope for Qwant France, or was it dropped? (open)
- raised: 2026-08-03, morning-routine
- project: map/pciv-live-integration (AI-1538 / AI-1542 / AI-1620)
- conflict/decision: a Gong brief and Dhaval's standing scope disagree about whether the online service ships for France at all.
  - Gong brief for "Internal Call: Weekly Qwant Stand-up (1/2)", Aug 3, 13 min, posted to #gongtest 09:42 ET: "For France, online CIV extraction will not be used, and virtual building will be used as support but not enabled for now." Two lines later the same brief says: "If the one-second latency budget is not met, CIV extraction will be used if it matches the prompt."
  - Dhaval, #pub-onboarding-qwant-ai 2026-07-31 10:35 ET: "online CIV extraction for Flash answers is out of scope for Flash answers" — Flash out, France AI-Chat in. Norbert, 10:03 same day: "No, all requests send an LLM response. Just France AI-Chat."
  - Reliability caveat: the brief's attendee field reads "adMarketplace: Price Is Right +1", a conference-room name parsed as a person, and "Price" is then credited with every action item. Gong-brief unreliability is a standing playbook gotcha. The benign reading is Gong compressing the Flash-only exclusion into "France".
- why it matters: this is the hot path for the entire online pCIV stream. AI-1538 (deploy), AI-1542 (latency), AI-1618 and the Luna evaluation, the API contract doc Varun owes an endpoint for, and AS-13436/AS-13437 which Alexandr Gontarev has In Progress right now all assume France AI-Chat is the launch surface. If it was actually dropped, the 8/24 go-live work is aimed at nothing; if it was not, acting on the brief would stall a live integration.
- ask: on today's Qwant stand-up, was online CIV extraction dropped for France entirely, or only for Flash answers as decided on 7/30?
- 2026-08-05 update (scope widening, not narrowing): the France AI-Chat reading is now settled in practice, but a **second** surface has appeared. Dhaval's Qwant-package review in `#pub-onboarding-qwant-ai` (8/04 14:22) treats **Detailed Flash Answer** as an active integration needing its own placement ID, and Elisa Branson confirmed 16:47 that **two** new placement IDs are needed, "one for Qwant and one for Lilo", at a 4-day setup SLA. Lilo is a publisher name that has not appeared in this stream before. Flash answers were declared out of scope for online CIV on 7/31; a dedicated Detailed Flash Answer placement with a prompt-field debate about `prompt` vs the flash response suggests otherwise. Worth confirming which surfaces the online service is expected to serve before the placement configs get built.
- 2026-08-05 update: a fourth confirmation. Yaarit's new A/B ticket AI-1654 (In Progress, under AI-1620) opens its description with "Qwant's AI Chat surface, available only in France" and defines the experiment against the llm-evaluator-service online pCIV endpoint; she also filed DPR-3420 for a `pcivExtraction` experiment config. Work is now being built on the France-in-scope reading. Still no decision record anywhere.
- 2026-08-04 update: three independent sources now contradict the Gong brief, and the benign reading is well supported. (1) Saksham, `#pub-onboarding-qwant-ai` 2026-08-03 10:56 ET, cc'ing Varun: "we need to call the CIV service only for AI mode for FR" — plus Amarachi at 11:08 naming placements 5357 and 5359. (2) The API contract doc §1, edited 11:49 the same morning: "Primary use case today: Qwant's AI Chat surface, France only". (3) On AI-1620, 17:19–17:22 the same evening, Saksham narrowed scope to "Support Qwant launch only" and set Expected Delivery 14/Aug/26 with a green RAG, while **Dhaval personally raised priority to Highest** and assigned Amarachi as Product Lead — eight hours after the Gong brief. AI-1213 "Emerging Qwant launch support" closed Done in the same minute. Still filed as open because none of the three is a decision record: AI-1620 has no description and zero comments, so the direction is expressed only through fields.
- resolution: (pending)

## Q-2026-08-07-01 — Which experimentation-config key actually shipped: `pcivExtraction` or `civExtraction`? (open)
- raised: 2026-08-07, morning-routine
- project: map/pciv-live-integration (DPR-3420 / AI-1620 / contract doc)
- conflict/decision: two live artifacts define the key differently, and the config has already shipped.
  - **DPR-3420 Scope field** (`customfield_11292`, read fresh 2026-08-07): "Add new configuration type called ~~pCIV Extraction~~ CIV Extraction in the experimentation platform UI in Amplify **(key: pcivExtraction)**, with two possible values: Online V1 / online_v1, Off / off". Only the display name is struck through; the key line still reads `pcivExtraction`.
  - **Yaarit's instruction to Arman**, DPR-3420 c171873 (2026-08-05 11:06 ET): "please update the config name from 'pCIV Extraction' to 'CIV Extraction'. **All the rest stays the same.**" — consistent with the key NOT changing.
  - **Contract doc §3.2** (read from Drive 2026-08-07 10:42) documents the field as `experimentContext.config.civExtraction`, and Yaarit's doc comment says she "renamed pcivExtraction → civExtraction **to match DPR-3420**".
  - The ticket **summary** was also renamed to "…Experimentation Platform:civExtraction" (8/05 12:24).
  - It has shipped: Arman drove DPR-3420 Not Started → Done by 2026-08-06 09:40, and RELEASE-6169 "New Config type: CIV Extraction" is Released.
- why it matters: the llm-evaluator-service online CIV endpoint accepts `experimentContext` and the SSP routes traffic on this key (Gontarev, `#online-civ-service` 8/05 14:32: "Request mapping + gating — via the `civExtraction` experimentation config (DPR-3420); SSP reads the config and routes traffic accordingly"). If the doc, the SSP client, and Amplify disagree on the key, gating silently fails open or closed — and the openapi.yaml the SSP generates its Jackson client from is built from the doc's spelling. Prod SSP release is Aug 12.
- ask: what key was actually created in Amplify — `pcivExtraction` or `civExtraction`? Whichever it is, the other two artifacts need correcting to match.
- resolution: (pending)

## Q-2026-08-07-02 — Does the SSP continue on query text alone for ALL online-CIV failure classes? (open)
- raised: 2026-08-07, morning-routine
- project: map/pciv-live-integration (AI-1538 / AI-1620)
- conflict/decision: no decision record exists, and the SSP is asking for one before it builds.
  - Alexandr Gontarev, `#online-civ-service` 2026-08-05 14:32, under "Needs from your side": "Timeout/error behavior — needs an explicit decision: on timeout or extraction failure, does SSP continue the flow on the query text / publisher PCIV, or return no ads? Your timeout note suggested 'continue with just the QT' — we'd like that confirmed as the decision for all failure classes."
  - The only thing resembling a decision is Saksham's aside, `#online-civ-service` 2026-08-05 12:18: "Do set a relatively aggressive timeout (say 700ms) so that we can move on and complete the rest of the flow with just the QT if LLM is taking too long." That covers the timeout case only, and was phrased as a note to Gontarev rather than a ruling.
  - Gontarev has since baked 700ms in as a "working default, config-driven" and says he will validate the number against Varun's latency data.
- why it matters: "all failure classes" is broader than timeout — it covers 422 (LLM returned an out-of-taxonomy GPC/IAB value), 500 (LLM call failed or unparseable), and per-query FAILURE inside a 207 partial success, all of which the contract doc §5 already defines. Continue-on-failure and return-no-ads are opposite revenue behaviors on the Qwant launch surface. SSP dev integration is Aug 8 and the prod release Aug 12, so this gets decided by default if nobody rules.
- ask: on online-CIV timeout or any extraction failure, does SSP proceed with query text alone, or return no ads? Same answer for every failure class, or does 422/500 differ from timeout?
- resolution: (pending)
