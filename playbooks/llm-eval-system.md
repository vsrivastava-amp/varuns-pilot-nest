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
- **Local dev auth (undocumented in the README — trips new setups):** running the service locally against the dev AI Gateway needs `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` — a **service principal, not a personal PAT** (`providers.py` hard-requires it). The team's **shared dev SP** lives in **Keeper: record "ml-llm-dev DBx OAuth [DEV]"** (Varun shares it per-person); drop the two values into your local `.env`. It's already scoped to the dev gateway, so no need to mint a new one. If a fresh SP is ever needed, gateway SPs/endpoints are provisioned by **infra (Pun Tong)**. (Surfaced 2026-07-23 when Yaarit hit this on a new laptop.)

## Model gateway / registry (how models get onto the eval service)

- The eval service runs on the **Databricks model gateway** (AI Gateway / Foundation Model APIs). Two layers:
  1. **Foundation model catalog**: `databricks-<model>` pay-per-token endpoints (FOUNDATION_MODEL_API). Browse: UI `/ml/ai-gateway` per workspace, or CLI `databricks api get /api/2.0/serving-endpoints -p <profile>` (filter `FOUNDATION_MODEL_API`; `creation_timestamp` reveals recency). Dev had 49 endpoints on 2026-07-23; newest: gemini-3-6-flash + gemini-3-5-flash-lite (added 2026-07-21), inkling (07-15), gpt-5-6-luna/terra/sol (07-09), claude-sonnet-5 (06-30), glm-5-2 (06-23), claude-fable-5 (06-09). Databricks tracks frontier releases within days-weeks.
  2. **Named wrapper endpoints** the service actually calls (`ai-gpt-5-2`, `civ-gpt-5-mini`, `ares-gpt-5-mini`…), mapped per-domain in the service's `llm/config/models.json`. Created by **infra (Pun)** — but infra cannot set rate limits.
- **Rate limits are per WORKSPACE per MODEL, in tokens** (ITPM = input tokens/min, OTPM = output tokens/min) — not per-endpoint, not per-request. Set by **Databricks** (contact: Sixuan He, external Slack channel; they can query current limits per workspace/model). Snapshot 2026-07 (prod 5702410742425796): gpt-5-mini 150M/20M, gpt-5-4-nano 90M/6M; dev: mini 40M/4M, nano 20M/2M; un-negotiated models default tiny (haiku-4.5 = 1M/0.1M everywhere; gpt-5-2 effectively unusable → the 429 storms). **Sizing**: rpm × tokens-per-request must fit ITPM; evidence suggests ITPM counts cache-read tokens (nano's observed ~100M tok/min peak ≈ its 90M ITPM) — confirm with Databricks. Capacity ask flow: (1) Pun creates endpoints, (2) Databricks sets model ITPM/OTPM (ask template: REVIEW.md 2026-07-23 v3).
- **Pricing**: Databricks charges *pretty close* to the official provider list prices (OpenAI/Anthropic/Google). DBX's own pages lag: https://www.databricks.com/product/pricing/model-serving and https://www.databricks.com/product/pricing/foundation-model-serving. For OpenAI-family models, check openai.com model pricing directly and assume ≈parity. Empirical per-run cost: measure via `system.ai_gateway.usage` token counts (see telemetry below) × provider list price.
- Prod's endpoint roster can lag dev's — verify in the prod workspace UI before promising a model.

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

## AWS Bedrock (second gateway — verified 2026-07-23)

- **Access confirmed end-to-end** on the `dev` profile (account 564079877134, PowerUserAccess via SSO, us-east-1): `bedrock-runtime converse` returns tokens for Meta, Mistral, Anthropic, Qwen with no extra grant work. Auth: `aws sso login --profile dev` (human-gated, expires); probe with `aws sts get-caller-identity --profile dev`.
- **Catalog snapshot 2026-07-23** (121 models, 17 providers; regen: `/model-selection` §1b): on the **bedrock-runtime surface** (InvokeModel/Converse), OpenAI = open-weight `gpt-oss-120b/20b` (+safeguard) only.
- **CORRECTION 2026-07-23 (Varun/online research): closed-weight GPT-5.4, GPT-5.5, and GPT-5.6 Sol/Terra/Luna ARE on Bedrock** — but behind the separate **Bedrock Mantle** endpoint (OpenAI **Responses API only**: `https://bedrock-mantle.us-east-1.api.aws/openai/v1`, auth via Bedrock API key; no InvokeModel/Converse/ChatCompletions). GA (5.6 family Jul 9 2026), us-east-1 in-region, **prompt caching with 90% cached-input discount**, pricing = OpenAI first-party rates (NOT in the AWS Price List API — quote from openai.com). **Standard tier only** (no priority/flex/cross-region). No nano/mini variants: **Luna ≈ nano-role, Terra ≈ mini-role**, Sol = flagship. Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html
- **Three gating layers when checking "is X on Bedrock":** (1) account model-access grants, (2) region, (3) **API surface** — `list-foundation-models` and the AmazonBedrock price book only cover bedrock-runtime; Mantle-served frontier models are invisible to both. Check the OpenAI model-cards docs page too.
  - Open-source highlights: `meta.llama4-maverick-17b / llama4-scout-17b` (INFERENCE_PROFILE → call as `us.<modelId>`), `qwen.qwen3-32b / qwen3-next-80b-a3b`, `deepseek.v3.2`, `zai.glm-5 / glm-4.7-flash`, `moonshotai.kimi-k2.5`, `minimax.minimax-m2.5`, `mistral.ministral-3-{3b,8b,14b}` / `magistral-small-2509` / `mistral-large-3-675b`.
  - Anthropic current: `claude-fable-5`, `opus-4-8`, `sonnet-5`, `sonnet-4-6`, `haiku-4-5` (all INFERENCE_PROFILE → `us.` prefix).
  - Note: Qwant runs Mistral-small; `ministral-3-*` on Bedrock enables like-for-like extraction-quality comparison.
- **First latency taste** (laptop → us-east-1, 3-token converse, single sample — NOT a benchmark): ministral-3-8b 370ms, qwen3-32b 373ms, haiku-4-5 904ms (us. profile), llama4-maverick OK. In-network from RIC1 should match or beat this.
- Gotchas: laptop CLI is `aws-cli/2.16.3` (June 2024) — **lacks `bedrock list-inference-profiles`**; use the `us.<modelId>` convention for INFERENCE_PROFILE models, or upgrade the CLI. `INFERENCE_TYPE` per model in `list-foundation-models` output tells you which need the prefix.
