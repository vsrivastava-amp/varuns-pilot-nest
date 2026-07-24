# AI-1474 — keyword GPC reclassification: release + run checklist

*(Created 2026-07-24. The durable todo for everything in flight on AI-1474. Update
statuses in place; move to runs/ when the whole effort closes. Full narrative:
`runs/2026-07-22-ai1474-scope.md`. Session slug: ai1474.)*

**Decision of record**: winner = **gemini-3-6-flash** (eval id 6). Golden-500: GPC
L1/L2/L3 = .928/.902/.897 (statistical tie w/ luna, both >> prior .845 L3); Chris's
17 dog examples 0/17 Cat Supplies (both); depth: gemini 91.0% L3+ vs luna 84.6% on
100 real keywords. Posted to ticket 2026-07-24 ~12:50 ET w/ Varun approval; Dhaval
objection window open (Jira monitor `b6yoaw6du`).

## 1. Ship eval 6 = gemini to prod (llm-evaluator-service)

- [x] Branch `feat-civ-eval-luna-gemini` validated locally (320 tests, golden battery, zero deploys)
- [x] Rebased onto main `ae16d88` (incl. hotfix PR #52), force-pushed `8736087`, build tag `1.0.287-feat-civ-eval-luna-gemini`
- [x] ~~dev/stage CD bumps of feature-branch image~~ **DECLINED by Varun 2026-07-24** — not needed; prod only needs the winning model. (Remote branches `feat-civ-eval-luna-gemini{,-stage}-image` on cd-deploy-configs to be deleted.)
- [x] **Trim branch to prod shape** → new branch `feat-civ-eval-6-gemini` (ae1da11, 307 tests pass): eval 6 = gemini-3-6-flash + registry entry + runtime fixes (invoker `normalize_content`, fence-tolerant parse — REQUIRED for gemini) + accuracy-script retry; eval 5 untouched (gpt-5-2); luna dropped. Old branch `feat-civ-eval-luna-gemini` kept intact on remote. Awaiting Varun push.
- [ ] PR to llm-evaluator-service main; peer approver w/ context (Yaarit natural) — **flag in PR: id 6 repointed gpt-5-mini → gemini-3-6-flash**; Varun merges
- [ ] After merge: main build → dev/stage CD bumps w/ the main tag (`apps/llm-evaluator-service/{dev-ric1,stage-ric1}/kustomization.yaml` in Bitbucket cd-deploy-configs — see release-process skill)
- [ ] **Find prod CD config** — not in Bitbucket cd-deploy-configs (only dev/stage dirs exist); likely the GitHub CD repo. Fill release-process skill TBD.
- [ ] Prod deploy: PR + peer approval + Varun manual merge. Gate: prod pods healthy post Yaarit-hotfix.
- [ ] Release comms per skill: RELEASE ticket, `#release-<num>-<slug>` channel, #releases announcement
- [ ] Sync `llm_evals.civ_config` table row for eval 6 at release time
- [ ] **Cache check before run**: prod now serves ids up to 6 (Yaarit's release, 6=mini) — verify nothing cached under prod DynamoDB namespace 6 (or invalidate) before gemini traffic, else repointed id inherits mini answers

## 2. Full 2.23M-keyword run (Databricks notebook)

- [ ] Run `L3_categorization_v2` (dev ws, `/Users/vsrivastava@admarketplace.com/AI-1474_keyword_gpc_reclassification/`), eval_id=6, prod api_url. First slice doubles as **prod rate-limit verification** (dev increase confirmed by experiment; prod unverified). Est. $2–4k, resumable.
- [ ] Spot-check raw table (incl. `CHRIS_EXAMPLES` FAIL query — none under Cat Supplies)
- [ ] Flip `REBUILD_GOLD=True`: coverage gate → staging table → sanity checks → DEEP CLONE backup (`gold_adv_keyword_gpc_level_3_eval2_backup`) → atomic `CREATE OR REPLACE`
- [ ] Comment on AI-1474 + **ping Emily** when gold table swapped (she bumps Katie Ji for Tableau/BI refresh)

## 3. Parked / gated side-threads

- [ ] **Eval-4 cache refresh** (18,071 prod DynamoDB entries from Tue mini pilot): notebook `cache_refresh_eval4` ready; **gates: Sunil/Yaarit LGTM in Slack DM C0BK693R20P + prod pods healthy + Yaarit release confirmed staying**
- [ ] Dhaval objection window on gemini pick — monitor `b6yoaw6du` watching ticket; proceed if quiet
- [ ] ITPM/OTPM ask w/ Sixuan (Databricks): dev increase confirmed live; prod outcome unknown — first run slice is the test
- [ ] Session cleanup: kill local uvicorn task `btfufgz54` (localhost:8000) when local testing done. ~~delete declined cd-deploy-configs remote branches~~ ✅ deleted 2026-07-24
