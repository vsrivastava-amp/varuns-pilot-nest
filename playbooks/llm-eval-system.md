# LLM Eval System playbook (pipeline + evaluator service)

*(Living reference. Seeded 2026-07-21 from Varun's saved notes — state as of the eval-config-split release, completed 2026-07-21. Deploy/CLI mechanics live in `playbooks/databricks.md`; this file is the system knowledge.)*

## The two systems

- **llm-evaluation-pipeline** (`~/Documents/llm-evaluation-pipeline`, Bitbucket): Databricks Asset Bundle, 5 jobs defined in `resources/workflows/*.yml`. Deployed per-target via `databricks.yml` (dev/stage/prod = separate workspaces). Catalog = `{ENV}_amplify` (`src/main/python/utils/env.py`).
- **llm-evaluator-service** (`~/Documents/llm-evaluator-service`, Bitbucket): FastAPI on k8s. CI (bitbucket-pipelines) builds Docker tag `<ver>.<build#>-<branch>` on every push; deployment = separate CD deploy-config repo (not local; Varun updates it). Endpoints: `/v1/relevancy/evaluate-ads`, `/v1/intent/civ`, `/health`. URLs: `{dev|stage}-llm-evaluator-service.ric1.admarketplace.net` (VPN only — unreachable from the sandbox, see databricks playbook gotchas).

## Config tables (the July 2026 refactor)

`llm_evals.eval_config` (single table keyed by `domain`) was split into **`llm_evals.relevancy_config`** and **`llm_evals.civ_config`** in all three catalogs. Schema: `eval_id, is_active, created/modified_timestamp, model_id, prompt_path, max_group_size`.

- **Pipeline readers only use `eval_id` + `is_active`**; model/prompt/group-size columns are documentation for downstream consumers.
- **Source of truth for those metadata columns = the service's `src/main/python/domains/<domain>/eval_configs.json`** — the old eval_config had drifted (claimed civ ran gpt-5-mini; service actually runs gpt-5-4-nano). Keep table rows in sync when service config changes.
- Contents (all envs, as of 2026-07-21): relevancy `(1, active, gpt-5-mini, hybrid_prompt_v1.txt, 50)`; civ `(1, inactive, DUMMY - NOT USED — placeholder agreed with Sunil)` + `(2, active, gpt-5-4-nano, civ_extraction.txt, 40)`. Service also defines civ eval_ids 3/4/5 — deliberately not in the table (only active configs get rows).
- Service-side civ eval configs on origin/main (2026-07-22): `2 = gpt-5-4-nano, civ_extraction.txt, b40/c20` · `3 = gpt-5-4-nano, civ_extraction_v2.txt (query_objective prompt, PR #47 by Yaarit, 2026-07-15), b40/c20` · `4 = gpt-5-mini, b10/c10` · `5 = gpt-5-2, b10/c10`. 4 and 5 reuse `civ_extraction.txt`.
- Old `eval_config` left in place as rollback insurance.

## Service internals worth knowing (learned 2026-07-22, AI-1474 scoping)

- **The civ "cache" is DynamoDB in the service** (`persistence/dynamodb_repo.py`, table `civ_label` via `CIV_TABLE_NAME`). Cache key = `sha256("<evalId>|<lower(trim(qt))>")` — **namespaced by eval_id**, so a new eval_id starts with a clean cache; old misclassifications can't leak in. Busting options: `bypassCache: true` per request (still writes results back), `DISABLE_CACHE=true` env (kills reads+writes), `POST /v1/intent/civ/invalidate-cache` (delete by evalId+qt). Cache hits are re-validated against current pydantic/taxonomies; schema-valid-but-wrong entries survive.
- **Model registry** = `llm/config/models.json` (the allow-list of `model_id`s; provider=databricks AI gateway, OAuth). Endpoint resolved per-domain via `domain_endpoint_name` — civ passes `domain="civ"`; models without a `"civ"` key fall back to `default` (e.g. `gpt-5-2` → `ai-gpt-5-2`). New eval config = one entry in `domains/<domain>/eval_configs.json` (+prompt file if new) + model present in models.json + **redeploy** (configs are `@lru_cache`d at process start). `evalId` is an unvalidated int in the request schema; unknown ids fail deep in llm.py as KeyError.
- **Prompt caching is real and huge**: the civ system prompt (~16.4k tok — embeds full GPC tree with IDs + IAB taxonomy) is resent per LLM call; OpenAI-side auto prefix caching (≥1024 tok) gives **93–97% of input tokens as cache reads** (verified in `system.ai_gateway.usage.token_details.cache_read_input_tokens`). The `cache_control: ephemeral` block in `invoker_unstructured.py` is Anthropic-style and a no-op for OpenAI models. Cost estimates that ignore this run ~10× high.
- **Observed civ latency** ≈ 5s/LLM-call (gateway telemetry, nano and mini alike).
- Civ LLM returns integer GPC leaf IDs; `llm.py` resolves them to path strings via `resources/gpc_taxonomy.json`; `validation.py` drops paths not in `taxonomy.en-US.txt`.

## Cost / usage telemetry

- `system.ai_gateway.usage` — per-request tokens (incl. cache read/write, reasoning), latency, status per endpoint. Workspace ids: dev `4731856320192987`, stage `1602623610650144`, prod `5702410742425796`.
- Dashboard "AI Gateway Endpoint Cost Attribution" (dev workspace, dashboardsv3 id `01f138e4b0c318dc984558506661d5d0`) — tokens by endpoint + $ via `system.billing.usage` × `system.billing.list_prices`, keyed by `usage_metadata.endpoint_name` where `billing_origin_product='MODEL_SERVING'`.

## Pipeline mechanics

- **Ares (relevance)**: scheduled batch. Lower bound = `pipeline_metadata.data_pipeline_offset` row (`pipeline_name='ad_relevance_evaluation'`) taken **verbatim** — nothing floors it. No row ⇒ defaults to `now()-20min`. Run unions retry-eligible rows from `ad_relevance_failures`, and the committed offset = max over that union (can move the offset *backward*). Row requires non-null `batch_id` (use `'0'` when seeding).
- **Civ**: continuous streaming, `startingVersion: latest`, checkpoint at `/llm_evaluation_pipeline/ad_civ_extraction_pipeline/checkpoint/<env>/ad_civ_extraction`. Stale checkpoint ⇒ huge catch-up; delete `offsets/commits/metadata` to reset (dev has a teammate's `sjain-local` dir alongside — preserve). **Civ backfill** job takes `--start_date/--end_date`, anti-joins `ad_request_civ` (only unevaluated rows), and is the reliable way to test civ e2e.
- Writers `MERGE INTO` — output tables must pre-exist (`ad_request_civ`, `ad_request_civ_failures` were created in stage from dev DDL during this release).
- A few % retriable failures per run is normal (handled by failure-retries job).

## Environment quirks

- **dev**: `event_silver.ad_request` is effectively dead (no writes since 2026-05-12) — streams see nothing; test via backfill over historical dates. Small backfill dates: check eligible-row counts first (most days ≈ 1M rows ⇒ hours; some days ≈ dozens).
- **stage**: data is a trickle (~50 civ-eligible rows/day, batchy). Stage had never run the pipeline before this release. Personal-user limitations found: can't create `/Repos/data_engineering` (admin needed), can't bind runtime SP `run_as` (needs `servicePrincipal.user` on `Databricks_sp_llm_evaluation_pipeline`), cluster-create was granted mid-release. **Running job code from a personal Git folder hit a spurious `ImportError` (partial module load) — serving from the bundle's default `root_path/files` fixed it.** Local-only `databricks.yml` stage overrides (root_path + run_as user) exist uncommitted — do NOT commit.
- **prod**: live, continuously running. Never clear the waterline or checkpoint there. Table DDL/DML goes through infra tickets (Varun has read-only via dev auth). Prod deploy trigger post-merge was never fully documented — fallback: deployer runs `bundle deploy -t prod` from clean main.
- Bundle deploys as personal user run jobs `run_as` that user; stage/prod normally use runtime SP `ff268f10-…` via CI SP `sp_bitbucket_dbx_deployer` (`01e12f4f-…`).

## Release verification pattern that worked

Seed/clear waterline → run job → check: new rows in `llm_evals.ad_relevance` / `ad_request_civ` filtered by `modified_timestamp > run start`, grouped by `eval_id` (must match config table), failures table flat, waterline advanced. Local tests: `PYTHONPATH=src/main/python:src/test/python .venv/bin/python -m pytest src/test/python` with `JAVA_HOME=/opt/homebrew/opt/openjdk@21/...` and `PYSPARK_PYTHON=$PWD/.venv/bin/python` (421 tests).
