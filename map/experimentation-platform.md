# Experimentation Platform (A/B testing)

*(Enriched 2026-07-23 from source: `experimentation-platform-service` repo, `ad-auction-service` repo `docs/` + code, and the "Experimentation Platform Analysis" Databricks dashboard. Facts dated — re-derive time-sensitive bits.)*

adMarketplace's home-grown A/B platform. Three moving parts:
1. **experimentation-platform-service** — defines experiments/targets/buckets + config values (Bitbucket, MySQL schema `exp`).
2. **Eval SDK, embedded in consuming services** (dsp-engine, ad-auction-service) — does the actual request→bucket assignment and applies the chosen bucket's config.
3. **"Experimentation Platform Analysis" Databricks dashboard** — reads assignment + event data from `prod_amplify`, computes per-bucket metrics + significance vs a control.

- Owner: **Dhaval Shah** (Build Accountable); team Relevance & Yield. Slack **#proj-experimentation-platform**.
- Build tracker project "Experimentation Platform" (Relevance & Yield), status Done (M1 v1.0 + M2 Support Multiple Targets both Done). Doc `1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`.

## Domain model (how an experiment is defined)

Hierarchy: **DOMAIN → TARGET → EXPERIMENT → EXPERIMENT_BUCKET**, config via EAV (CONFIG → CONFIG_ATTRIBUTES → CONFIG_FIELD). MySQL schema `exp`, Liquibase migrations, entity names = table names (UPPER_CASE).

- **Domain**: `1=SSP`, `2=DSP`. Every target + config field belongs to one. Eval snapshot fetched per `domainId`.
- **Target**: `name`, `priority` (unique int, selection precedence), a baseline **Config**, and a **TargetFilter** (JsonLogic over `TargetFieldCode`: GEO/DEVICE/PUBLISHER/PLACEMENT/CITY/COUNTRY/REGION/PUBLISHER_TYPE; ops EQ/NEQ/IN/NOT_IN/LT/GT/LTE/GTE). AND-combined.
- **Experiment**: `name`, `hypothesis`, `percentExposed` (**0–100, the only traffic-allocation knob**), `numTreatments`, `startTimestamp`/`endTimestamp`. **Status is derived from timestamps** (UPCOMING / IN_PROGRESS / COMPLETED), not stored. On create, the service auto-makes **`control_1` + `control_2`** (both = baseline clone) plus **one bucket per treatment**. In UI responses `control_2` is hidden and `control_1` shown as `control`.
- **ExperimentBucket** (= the variant): `name` (`control_1`, `control_2`, `treatment_1`…), its own **Config** override. **No per-bucket weight field** — exposed traffic is split evenly by the SDK.
- Traffic-allocation guard: overlapping experiments on one target may not exceed **100% at any hour** (`America/New_York`); violation → HTTP 416 with conflicting ranges.

## Experiment variables (= "config fields")

A variable is a **CONFIG_FIELD**: `lookupKey` (camelCase, the external contract key), `dataType` (STRING / NUMBER / BOOL / *_LIST / FLOAT_INDEX_LIST), `allowedValues` (UI dropdown), `validationConfig` (JsonLogic, published to SDK). Target baseline + bucket overrides are CONFIG_ATTRIBUTES rows (JSON value) referencing a CONFIG_FIELD.

Seeded config fields (from migrations): `relevancyThresholdsText`, `relevancyThresholdsProduct` (FLOAT_INDEX_LIST — delivered as an **index-keyed map** `{"0":0.8,…}`, not an array), `embeddingModelProduct`/`embeddingModelText` (`gte`/`gte_amp`), `useIntentClassifier` (bool), Vespa fields (`vespaTargetHitsProduct`…), and **`aasRoutingLevelPA` / `aasRoutingLevelTA`** (dropdown `search`/`pricing`/`scoring`/`auction`, migration 048 — Product/Text ad AAS routing depth).

## Assignment / bucketing (deterministic, SDK-side)

The platform-service does **NOT** assign traffic — no hashing/salt/assignment table in that repo. It publishes a **hash contract** the SDK must follow:
`GET /api/v1/eval/config-snapshot?domainId=` returns `eval.v1` snapshot (targets w/ priority+JsonLogic filter+baseline config → active experiments w/ `percentExposed` → buckets w/ resolved config maps) plus:
- `hashContract = { algo: "md5", keyFormat: "{requestId}:{targetId}", encoding: "utf8" }`.

SDK: pick target (priority + filter match) → `md5(utf8("{requestId}:{targetId}"))` → decide exposure vs `percentExposed` → split exposed traffic across buckets → apply that bucket's config map. **Deterministic/sticky by (requestId, targetId).** Active-experiment window: `UTC_TIMESTAMP() BETWEEN start AND end`.

## How consumers apply variables (ad-auction-service, verified in code 2026-07-23)

Config arrives as `com.admarketplace.experimentation.sdk.ExperimentContext` = `(List assignments, Map<String,Object> mergedConfigs)`. AAS reads it through one class `ExperimentContextReader` (owns every key string; typed getters w/ Spring-property fallback). Wire shapes: legacy `AdAuctionRequest.experimentContext`; Discover 3.0 `asv.experimentContext.internal.mergedConfigs`.

**Only 4 keys are actually consumed in AAS today** (all search/scoring path):
| Key | Effect | Fallback |
|---|---|---|
| `usePostSearchDeduplication` | gates post-search product-ad dedup (disabled = pass-through, not skip — ranking depends on the step) | `product-ad-search.dedup.post-search-enabled` |
| `kvssScoreLinearA` | slope of linear transform on KVSS text-ad score before cross-type ranking | `0.93` |
| `kvssScoreLinearB` | intercept of same transform | `0` |
| `enableDiscoverTextSearch` | whether `DiscoverKeywordAdsSearchStep` runs at all | `kvss.discover.enabled` (false) |

`kvssScoreLinearA/B` are the "unified retrieval score" transform (`floor((a·raw+b)·1e6)`) that puts text ads on the product-ad scale in `DiscoverRankingStep`. Whole `ExperimentContext` is also forwarded to KVSS/VSS so they run their own experiments.

⚠️ **State gap (not a contradiction — current reality):** the platform-service *defines* `aasRoutingLevelPA/TA` config fields, but **ad-auction-service does not read `aasRoutingLevel` anywhere**. The movable AAS/DSP cut-line is **design-only** — `docs/experiment-cutover.md` (Joseph, 2026-06-03, Status: Design/not implemented) realizes it as `ExperimentConfig(experimentId, Set<AuctionPhase>)` gating steps via `appliesTo`, default = all phases enabled = today's behavior. `discoverAuction` is not a key (class names); `VECTOR_SEARCH_PRODUCT_ADS` is a dsp-engine flag, referenced in an AAS comment only.

## Analysis dashboard

"Experimentation Platform Analysis" — dev workspace `dbc-562d27e2-d74d`, dashboard id `01f13f460c811a41bf5e9cd29c0c648a`, owned by vsrivastava@. Pull the def: `databricks api get /api/2.0/lakeview/dashboards/<id> -p dbc-562d27e2-d74d` (`.serialized_dashboard` is JSON; datasets in `.datasets[].queryLines`).

- **Params:** `experiment_id`, `start_ts_est`, `end_ts_est` (+ `min_requests` on placement view). Timestamps are EST — SQL adds `INTERVAL '5 hours'` to hit UTC event tables; **start inclusive, end exclusive**.
- **Assignment join (the crux):** buckets from `prod_amplify.exp.experiment_bucket`; request→bucket from `prod_amplify.event_silver.ad_request.amp_targeting_assignment` (an **array** you `EXPLODE`, each elem carries `experiment_id` + `experiment_bucket_id`).
- **Reference = `control_1`, always.** Every other bucket compared individually vs control_1 (the "Pooled Summary" dataset name is a misnomer — no pooling).
- **6 datasets:** Aggregate Summary (31 metrics), Pooled Summary (15 metrics), Placement Level (per pub×placement, `min_requests` floor), ares_by_ad_type, Ad Format Comparison (product = `adv_product_id` populated, else text), Country Level (`usr_geo_country_code`). 4 pivot widgets on one page.
- **Metrics (~31):** requests, commercial/non-commercial classification, coverage, slot coverage, 4 CTR variants (clicks/req, clicked/responded, clicks/served, slot CTR), CVR, CPC, AOV, GMV, revenue, yield/req, yield/successful-req, eCPM, **ARES** relevance (mean+median), latency p50/p99.
- **Stats:** SE via delta-method / pooled-proportion formulas; **two-tailed p-value** from a normal-CDF rational approximation (Abramowitz-Stegun); `confidence=(1−p)·100`; `significant` = p<0.05. Deltas abs + relative.
- **Data sources:** `prod_amplify.event_silver.{ad_request,ad_response,click,impression,conversion}`, `prod_amplify.llm_evals.ad_relevance` (ARES 1–100 LLM judge; explode `ad_list_scores`), `ssp.{placement,publisher}`, `dsp.event_campaign_mapping` (conversion attribution, `is_primary=1`).

## Pointers

- Repos: `bitbucket.org/admarketplace/experimentation-platform-service` (schema `exp`, Confluence "Experimentation Platform Service SC237"); consumers ad-auction-service (`docs/experiment-cutover.md`) + dsp-engine.
- Databricks: dev `dbc-562d27e2-d74d` (warehouse `634ea83b5df3a556`), stage `dbc-303276b5-9802`, prod read via shared metastore (`prod_amplify`). CLI mechanics: `playbooks/databricks.md`.

## Agent posture

- Read-only status pulls, batched post-Okta. Anomalies → `state/` + dev channel.
- See the unexplained product-ads-through-AAS A/B win (+20% coverage / +5% CTR / +5% yield / +6–7% ARES for a no-op re-arch) in `map/aas.md` — open question, Dhaval pressing for cause.
