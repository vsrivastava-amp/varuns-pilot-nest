# AI-1474 — keyword GPC reclassification: release + run checklist

*(Created 2026-07-24. The durable todo for everything in flight on AI-1474. Update
statuses in place; move to runs/ when the whole effort closes. Full narrative:
`runs/2026-07-22-ai1474-scope.md`. Session slug: ai1474.)*

**Decision of record**: winner = **gemini-3-6-flash** (eval id 6). Golden-500: GPC
L1/L2/L3 = .928/.902/.897 (statistical tie w/ luna, both >> prior .845 L3); Chris's
17 dog examples 0/17 Cat Supplies (both); depth: gemini 91.0% L3+ vs luna 84.6% on
100 real keywords. Posted to ticket 2026-07-24 ~12:50 ET w/ Varun approval; **Dhaval APPROVED
15:42 ET: "$2.4k is fine. Go with the better resultz"** — pick + cost signed off.

## 1. Ship eval 6 = gemini to DEV (llm-evaluator-service)

- [x] Branch `feat-civ-eval-luna-gemini` validated locally (320 tests, golden battery, zero deploys)
- [x] Rebased onto main `ae16d88` (incl. hotfix PR #52), force-pushed `8736087`, build tag `1.0.287-feat-civ-eval-luna-gemini`
- [x] ~~dev/stage CD bumps of feature-branch image~~ **DECLINED by Varun 2026-07-24** — not needed; prod only needs the winning model. (Remote branches `feat-civ-eval-luna-gemini{,-stage}-image` on cd-deploy-configs to be deleted.)
- [x] **Trim branch to prod shape** → new branch `feat-civ-eval-6-gemini` (ae1da11, 307 tests pass): eval 6 = gemini-3-6-flash + registry entry + runtime fixes (invoker `normalize_content`, fence-tolerant parse — REQUIRED for gemini) + accuracy-script retry; eval 5 untouched (gpt-5-2); luna dropped. Old branch `feat-civ-eval-luna-gemini` kept intact on remote. Pushed to origin by Varun 2026-07-24.
- [x] **PIVOT 2026-07-24 (Sunil, DM C0BK693R20P): DEV-ONLY release.** "Better to run these in lower environments — dev or stage"; read from prod, write to dev/stage. → No prod deploy, no stage. Run hits dev service `dev-llm-evaluator-service.ric1.admarketplace.net` (`/v1/intent/civ`); dev gateway rate-limit increase already confirmed by experiment; gemini results land in DEV DynamoDB cache (prod cache untouched — fine, gold table is the deliverable).
- [x] ~~PR `feat-civ-eval-6-gemini` → main~~ SKIPPED per Varun 2026-07-24 — dev-only run needs no main merge; dev pod runs the feature-branch image directly (Yaarit precedent). Branch stays on remote; merge to main later only if gemini becomes permanent.
- [x] Dev CD bump DONE 2026-07-24: `dev-ric1` newTag → `1.0.288-feat-civ-eval-6-gemini` (PR merged by Varun; Argo auto-sync). Rollout verified behaviorally via smoke slice (gemini depth signature).
- [ ] Sync `llm_evals.civ_config` table row for eval 6 (dev)
- [x] Notebook api_url → dev endpoint DONE; plus ELB-hostname+Host-header DNS fallback (dev name absent from Databricks-visible DNS). NB: run on a CLASSIC cluster — serverless can't reach VPC-internal services (playbooks/databricks.md).
- [ ] ~~Find prod CD config / prod deploy / release comms~~ N/A for dev-only run (RELEASE ticket + comms: TBD if Varun still wants them for a dev-only change; skill TBD on prod CD repo stays open for future)

## 2. Full 2.23M-keyword run (Databricks notebook)

- [x] Smoke slice verified (run_id=smoke, 117 rows): 95.6% L3+, avg depth 2.96, 0 dog keywords in Cat Supplies, 4 legit NULLs.
- [x] **Full run COMPLETE 2026-07-27 ~18:35 ET** (was: IN FLIGHT since ~15:15 ET 2026-07-24: run_id=`gemini-full-1`, eval 6, dev endpoint, classic cluster. Table monitor `bo10owjte` (10-min polls: progress/STALL/COMPLETE). Emily got ~4h ETA via Slack.
- [ ] **Failure-NULL bug found ~16k in**: per-query `status: FAILURE` (rate-limit-type, 207 responses) were written as no-category NULLs (~43% marginal). Notebook FIXED (status/error-aware: failures ride 429 ladder, clean empties get 1 quick retry) + re-imported — but the RUNNING cell has the old code. On Varun's return: interrupt → Run All (resumes, same widgets). Then final mop-up pass `retry_empty=true` re-attempts all NULL keywords. **Check NULL rate before flipping BUILD_RELEASE_TABLE.**
- [x] Spot-checks GREEN 2026-07-27: coverage 2,422,273 >= 2,422,112 live universe; 0 dupes; 19.0% NULLs; 21/21 valid L1; Chris's 17 = 0 in Cat Supplies (~7 residual dog-kw misses in broad sweep, 0.05%, non-blocking)
- [ ] **DECISION 2026-07-24 (Varun, per ticket thread — Dhaval "we should not replace", Emily agreed): NO gold swap.** Publish eval-6 results as separate table `gold_adv_keyword_gpc_level_3_eval6` (same schema); gold untouched; Katie Ji repoints dashboard. Notebook endgame reworked: flip `BUILD_RELEASE_TABLE=True` → coverage gate → staging → sanity checks → atomic publish of the NEW table only. (Swap remains a one-liner later if wanted.)
- [x] **DONE 2026-07-27 (sent, msg link in run log): Ping Emily at 100% (Varun-directed 2026-07-27, exact wording agreed in-chat): Slack DM D0BFWRFDW1J with the RAW table path `adv_keyword_gpc_lvl_3_ai1474`. NO release-table flip — Varun: Emily doesn't need it; BUILD_RELEASE_TABLE stays parked unless asked.** Claude authorized to send as Varun on COMPLETE (in-chat direction, guardrail 8 satisfied).
- [ ] NB for the closing comment: ticket's public record is behind reality — last word says "full run pending rate limit increase"; it doesn't know about dev-only (Sunil, Slack) or the separate-table release. Closing comment should state: ran on dev, deliverable = `..._eval6` table, `gold_adv_keyword_gpc_level_3` untouched (per Dhaval's no-replace + Emily's agreement). Scope line in description says "Reprocess gold_..." — the separate table satisfies intent per thread consensus.

## 3. Parked / gated side-threads

- [x] **Eval-4 cache refresh — CLOSED 2026-07-28** (Varun: 3 stragglers fine to leave). Full story in `runs/2026-07-22-ai1474-scope.md`. Net: 2 full runs + diagnostic + targeted mop-up refreshed ~18k prod DynamoDB entries. Root cause of no-GPC responses: ~19% legit SUCCESS-empty (nano+v3 choosier than mini; cached correctly) + ~6% transient FAILURE 422 "invalid taxonomy values" (LLM hallucinates non-taxonomy GPC/IAB strings; never cached; retries fix — 126/129 known-stale resolved, 104 gained GPCs). Left open by choice: 3 queries (final-pass 429s) + est. ~1k un-enumerated 422s among the 16k without per-item records — harmless stale mini entries. Diag/mop-up tables: dev_amplify.elme_l3_keyword_categorization.civ_refresh_{diag,mopup}_ai1474; notebooks civ_refresh_diag / civ_refresh_mopup alongside the others.
- [x] ~~Dhaval objection window~~ CLOSED 2026-07-24 15:42 ET: approved ($2.4k fine, "go with the better resultz"). Jira monitor `b6yoaw6du` stays armed for thread activity.
- [ ] ITPM/OTPM ask w/ Sixuan (Databricks): dev increase confirmed live; prod outcome unknown — first run slice is the test
- [ ] Session cleanup: kill local uvicorn task `btfufgz54` (localhost:8000) when local testing done. ~~delete declined cd-deploy-configs remote branches~~ ✅ deleted 2026-07-24

## 4. Post-run cleanup (open)

- [ ] Revert dev HPA replicas 16→2 (both bumps) in cd-deploy-configs — batch job done, dev shouldn't hold 16 pods
- [ ] Optional: retry_empty mop-up of 460k NULLs (storm losses largely cache-recovered; sample first)
- [ ] Decide: merge feat-civ-eval-6-gemini to main or leave dev-only (dev pod pinned to branch image 1.0.288)
- [ ] AI-1474 closing comment + ticket transition (In Review); civ_config table row sync if keeping eval 6
