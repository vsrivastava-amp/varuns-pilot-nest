# AI-1474 — keyword GPC reclassification: release + run checklist

*(Created 2026-07-24. The durable todo for everything in flight on AI-1474. Update
statuses in place; move to runs/ when the whole effort closes. Full narrative:
`runs/2026-07-22-ai1474-scope.md`. Session slug: ai1474.)*

**Decision of record**: winner = **gemini-3-6-flash** (eval id 6). Golden-500: GPC
L1/L2/L3 = .928/.902/.897 (statistical tie w/ luna, both >> prior .845 L3); Chris's
17 dog examples 0/17 Cat Supplies (both); depth: gemini 91.0% L3+ vs luna 84.6% on
100 real keywords. Posted to ticket 2026-07-24 ~12:50 ET w/ Varun approval; Dhaval
objection window open (Jira monitor `b6yoaw6du`).

## 1. Ship eval 6 = gemini to DEV (llm-evaluator-service)

- [x] Branch `feat-civ-eval-luna-gemini` validated locally (320 tests, golden battery, zero deploys)
- [x] Rebased onto main `ae16d88` (incl. hotfix PR #52), force-pushed `8736087`, build tag `1.0.287-feat-civ-eval-luna-gemini`
- [x] ~~dev/stage CD bumps of feature-branch image~~ **DECLINED by Varun 2026-07-24** — not needed; prod only needs the winning model. (Remote branches `feat-civ-eval-luna-gemini{,-stage}-image` on cd-deploy-configs to be deleted.)
- [x] **Trim branch to prod shape** → new branch `feat-civ-eval-6-gemini` (ae1da11, 307 tests pass): eval 6 = gemini-3-6-flash + registry entry + runtime fixes (invoker `normalize_content`, fence-tolerant parse — REQUIRED for gemini) + accuracy-script retry; eval 5 untouched (gpt-5-2); luna dropped. Old branch `feat-civ-eval-luna-gemini` kept intact on remote. Pushed to origin by Varun 2026-07-24.
- [x] **PIVOT 2026-07-24 (Sunil, DM C0BK693R20P): DEV-ONLY release.** "Better to run these in lower environments — dev or stage"; read from prod, write to dev/stage. → No prod deploy, no stage. Run hits dev service `dev-llm-evaluator-service.ric1.admarketplace.net` (`/v1/intent/civ`); dev gateway rate-limit increase already confirmed by experiment; gemini results land in DEV DynamoDB cache (prod cache untouched — fine, gold table is the deliverable).
- [x] ~~PR `feat-civ-eval-6-gemini` → main~~ SKIPPED per Varun 2026-07-24 — dev-only run needs no main merge; dev pod runs the feature-branch image directly (Yaarit precedent). Branch stays on remote; merge to main later only if gemini becomes permanent.
- [ ] Dev CD bump: `apps/llm-evaluator-service/dev-ric1/kustomization.yaml` newTag → build of the trimmed branch (need build # from pipeline; or post-merge main build)
- [ ] Sync `llm_evals.civ_config` table row for eval 6 (dev)
- [ ] Update notebook `L3_categorization_v2` api_url widget → dev civ endpoint
- [ ] ~~Find prod CD config / prod deploy / release comms~~ N/A for dev-only run (RELEASE ticket + comms: TBD if Varun still wants them for a dev-only change; skill TBD on prod CD repo stays open for future)

## 2. Full 2.23M-keyword run (Databricks notebook)

- [ ] Run `L3_categorization_v2` (dev ws, `/Users/vsrivastava@admarketplace.com/AI-1474_keyword_gpc_reclassification/`), eval_id=6, **dev api_url**. Est. $2–4k, resumable; dev gateway rate-limit increase already verified.
- [ ] Spot-check raw table (incl. `CHRIS_EXAMPLES` FAIL query — none under Cat Supplies)
- [ ] Flip `REBUILD_GOLD=True`: coverage gate → staging table → sanity checks → DEEP CLONE backup (`gold_adv_keyword_gpc_level_3_eval2_backup`) → atomic `CREATE OR REPLACE`
- [ ] Comment on AI-1474 + **ping Emily** when gold table swapped (she bumps Katie Ji for Tableau/BI refresh)

## 3. Parked / gated side-threads

- [ ] **Eval-4 cache refresh** (18,071 prod DynamoDB entries from Tue mini pilot): notebook `cache_refresh_eval4` ready; **gates: Sunil/Yaarit LGTM in Slack DM C0BK693R20P + prod pods healthy + Yaarit release confirmed staying**. 2026-07-24: Sunil conditional LGTM (13:53 ET) pending bypassCache verification — verified in code (skips read only; save = unconditional put_item, same on origin/main), reply draft in REVIEW. Yaarit not yet replied.
- [ ] Dhaval objection window on gemini pick — monitor `b6yoaw6du` watching ticket; proceed if quiet
- [ ] ITPM/OTPM ask w/ Sixuan (Databricks): dev increase confirmed live; prod outcome unknown — first run slice is the test
- [ ] Session cleanup: kill local uvicorn task `btfufgz54` (localhost:8000) when local testing done. ~~delete declined cd-deploy-configs remote branches~~ ✅ deleted 2026-07-24
