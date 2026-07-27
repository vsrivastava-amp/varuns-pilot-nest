# Vespa @ adMarketplace — context map

*Created 2026-07-23. Vespa is the vector-search backend behind both ad-retrieval paths (product + text). This map covers the platform, the two service repos, ownership, and where the living knowledge sits. Facts age fast here — re-derive anything load-bearing.*

*Companions: [kvss.md](kvss.md) — KVSS deep-dive from the 7/15–7/22 KT sessions (match-type semantics, intent routing, feed path); `playbooks/vespa.md` — stage endpoints, request shapes, empirical gotchas (testingParameters.yql overrides, schema field-tuning asymmetries) from the AI-1545 investigation.*

## What it is

Vector search over ad inventory, hosted on **Vespa Cloud** (managed, vendor = Vespa.ai team — direct Slack access, see channels below).

- Tenant `admarketplace`, application **`vector-search`** (prod: aws-us-east-1c + us-west-2); second app **`vector-search-test`** for load/scale experiments.
- Console: https://console.vespa-cloud.com/tenant/admarketplace/application/vector-search/prod/instance
- Two datasets, historically one content cluster: `product_ad` (~75M docs) + text-ads keywords (~30k). Coupling is a known pain (see Text Ads SPIR below).
- Embeddings: 768-dim GTE-family — `gte_amp` (product) / `gte` (text) — query-side via EGS→embedder-service (see Embedding layer section), write-side pre-computed in Databricks. Cosine similarity, single-phase ranking with `minRankingScore` cutoff. The finetuned-embedding-model project introduced the second content cluster + MySQL model registry (see Model Embedding Transitioning doc).
- Deploy guard: `block-change revision=false mon-fri 5-22 America/New_York` — self-initiated releases go out overnight/weekends.

## Services & repos

| Piece | What | Where |
|---|---|---|
| VSS (vespa-search-service) | Product-ads ANN search; called by AAS/SASS | github.com/admarketplace-gh/vespa-search-service (canonical was bitbucket.org/admarketplace/vespa-search-service; deployment migrating to GitHub — AI-1494 In Review, AI-1496/1497 queued) |
| KVSS (keyword-vector-search-service) | Text-ads search: intent-classified exact vs vector; hybrid NN+lexical | github.com/admarketplace-gh/keyword-vector-search-service |
| database-vespa | The Vespa app package (services.xml, schemas, rank profiles, DedupSearcher) | **Canonical: bitbucket.org/admarketplace/database-vespa** (main→prod, dev→dev; active PRs through 7/22). GitHub copy exists but is a stale migration snapshot (default branch `github_migration`, last push 6/24) — don't read it. Layout: `src/main/application/…` |
| locust-vector-performance-framework | John Exantus's load-test harness (used by AI-1545) | github.com/admarketplace-gh/locust-vector-performance-framework |
| vespa-feed-service (VFS-feed) | Kafka→Vespa feeder, **both doc types** (product + a legacy text-ads feeder); "-green" = same image, env-pointed at content_green | bitbucket.org/admarketplace/vespa-feed-service (migration INFRA-3343 Not Started) |
| keyword-vector-feed-service (KVFS) | Newer reactive (Reactor-Kafka) keyword feeder → content_keywords; supersedes VFS's text path | bitbucket.org/admarketplace/keyword-vector-feed-service |
| embedding-gateway-service (EGS) | **Java 21** gateway: Redis-cluster embedding cache + vendor routing (internal vs Baseten) | bitbucket.org/admarketplace/embedding-gateway-service (repo-verified 7/27) |
| embedder-service | **Python/FastAPI** inference — in-process HF models, ONNX/torch, GPU; one model per deployment; quiet since 2025-12 | bitbucket.org/admarketplace/embedder-service |
| keyword-matching-vespa-poc | 2025 POC incl. custom Java Searcher (CTR re-rank experiment) | bitbucket.org/admarketplace/keyword-matching-vespa-poc |
| vespa-search-service-api-client | The shared caller contract — **not hand-written Java**: one OpenAPI spec (`openapi/spec.yaml`), Java generated at build (native java.net.http client, no retries, no default timeouts) | github.com/admarketplace-gh/vespa-search-service-api-client (repo-verified 7/27, see contract notes below) |
| model_registry (MySQL) | Model config for VSS: namespace/schema, rankProfile, thresholds per model; cron-refreshed 5min | Aurora MySQL (stage: `stage-aurora-mysql.cluster-….us-east-1.rds…/model_registry`) |
| cd-deploy-configs | ArgoCD kustomize configs — **the deployed env values** (`apps/<service>/<env>/config.conf`) | github.com/admarketplace-gh/cd-deploy-configs — dev/stage only for VSS+KVSS; **prod configs still in legacy Bitbucket pipeline** (AI-1497) |

**⚠️ Neither service repo contains the Vespa app package.** No `.sd` schemas, `services.xml`, rank expressions, or HNSW config in either — all of that lives in **`database-vespa`** (see its section below). VSS's only `.sd` is an integration-test probe that explicitly defers to database-vespa. Any ANN/ranking-tuning question bottoms out there. The two *service* repos migrated Bitbucket→GitHub; database-vespa has not (its GitHub copy is stale). *Deployment* migration is separate and in flight (AI-1494/1496/1497).

## VSS internals (repo-verified 2026-07-23)

Spring Boot, Java 25, port 8217, package `com.adm.vespa_search_service` (yes — same package root as KVSS). "VSS 1.1.105" = pom base 1.1 + GitHub run number, not semver.

- **Endpoints**: `POST /api/v1/search/product-ads/vector`, `.../exact` (minScore forced 0.0), and `POST /api/v1/discover/product-ads/vector` (Discover 3.0 request shape, per-term filters). Discover is fully wired despite `docs/discover-3.0-searchconfig-refactor.md` claiming it's a reverted stub — repo doc is stale.
- **Schema**: `content_green.product_ad_green` (via model-registry, with fallback). ~35 returned fields (plaId, title, price/salePrice family, brand, GPC, gtin/asin, availability…). Tensor: `documentVector`, query `queryTermVector`, 768-dim, cell type FLOAT16 (config: INT8/BIT possible), hex-encoded on the wire.
- **Rank profiles**: `product_ad_vector` / `product_ad_exact`; selection = testingParameters override → model-registry → default. **rawVespaScore = raw Vespa relevance = cosine similarity** (`ProductAdMapper`); the ×1e6 floor is AAS-side.
- **YQL**: `nearestNeighbor` + `plaFeedId IN`, per-term constraint clauses (brand, GPC hierarchical-prefix — or exact IN when `vespaYqlVersionProduct==1`, condition, gender w/ unisex expansion, ageGroup, currency, availability, price-or-salePrice range w/ date window), all bound params (injection-safe). Always injects in-stock availability filter (`in stock/in_stock/In Stock`) — the "full-page filter".
- **Diversity/dedup**: grouping `all(group(plaFeedId) max(N) each(max(overfetch)…))`, diversity-depth 3, overfetch +25%; dedup via search chain `product_ads` + dedupParams (only when `vespaDeduplicationFieldsProduct` experiment config set), dedup-multiplier 2. (The 1.5× multiplier in map/aas.md is AAS-side, pre-request; VSS's own are 1.25/2.0.)
- **Tuning defaults**: results-limit 20, target-hits 20 (request limit overrides when larger), totalTargetHits = targetHits × 14 (`total-num-nodes-content-green`), minTargetHits 120, relevancy-threshold 0.5, all timeouts 5000ms. Caches: query-vector (Caffeine 10k), vespa-result (6k / 5min), model-registry (5min cron).
- **⚠️ No 2.0-vs-3.0 query-path toggle exists in VSS.** The only version knob is GPC exact-vs-prefix. AI-1545's "2.0 vs 3.0" latency comparison is a request-shape/AAS-side distinction (per-term fan-out: one Discover request → N parallel Vespa queries), not a VSS code path.
- Embedding model for products: **`gte_amp`** via EGS `POST /api/v1/embedding/batch`. Stage-UAT env (cd-deploy-configs): EGS timeout **50ms**, query-term timeout **150ms**, Vespa pool 30 conns / connect 250ms, vector-result-cache 12000/5min, and `APP_PROFILE_AB_TESTING_*` bucket knobs (10k buckets, treatment 1.0). Stage-UAT points at the **second Vespa Cloud app** (`c277b960.a3a43ed2.z.vespa-app.cloud`, labeled "PROD-TEST" = vector-search-test).
- Deploy: Docker (amp-java corretto-25) → JFrog → ArgoCD (`cd-deploy-configs` reusable workflow), envs dev-ric1/stage-ric1, prod via dispatch; hosts `vespa-search-service-{dev,stage}-http.ric1…`, prod `prod-vespa-search-service.{ric1,pdx1}`. Datadog via StatsD. Design doc: Confluence "Vespa Search Service - SC217".

## KVSS internals (repo-verified 2026-07-23)

*Semantics/product-behavior view (match types, intent routing, feed path, KT recordings): [kvss.md](kvss.md). This section is the repo-code view.*

Same stack/port (8217), package also `com.adm.vespa_search_service`. Owner by commit volume: Roberto Simoes. README is just a Jira link (SRS-1570) — knowledge lives in Jira (SRS-/AS-) + KT docs.

- **Endpoint**: single `POST /api/v1/search`. Request `VectorSearchRequest` from api-client 1.0.75: queryTerms map, `filter.audienceIds`, `allowConquesting`, per-request targetHits/limit/timeout/minScore\*, testingParameters (yql, rankingProfile, approximate…).
- **Schema**: `content_keywords.keyword_ad`. Modes (`SearchApiType`): EXACT → index `keyword_attribute`, profile `keyword_ad_native`; VECTOR → index `keyword`, profile **`keyword_ad_vector_mt_threshold`**; VECTOR_LEGACY → profile `keyword_ad_vector`.
- **YQL (vector)**: `(nearestNeighbor(documentVector,queryTermVector) OR {defaultIndex:'keyword'} userInput(@queryTermText)) AND audienceId IN (…) AND !(keywordTypeId = 3)` — hybrid ANN + lexical OR; keywordTypeId 3 = competitor keywords, excluded unless `allowConquesting` (conquesting enabled AS-12358/12536).
- **Score** = raw Vespa relevance = cosine (`KeywordAdsMapper`) — this is AAS's `rawKvssScore` before the a=0.93 linear transform.
- **Thresholds** (two coexisting systems — easy to confuse): legacy `relevancy-thresholds` by word-count (0.7→0.6) feeding `minRankingScore` (VECTOR_LEGACY); current `keyword-thresholds` per word-bucket exact/phrase/broad (e.g. one-word 0.88/0.72/0.72; six-plus 0.85/0.70/0.70) feeding `minScoreExact/Phrase/Broad` (VECTOR).
- **Tuning — RESOLVED 2026-07-27 via cd-deploy-configs stage env** (`apps/keyword-vector-search-service/stage-ric1-gh/config.conf`): deployed values are **targetHits 500, timeout 0.05s (50ms), softtimeout 0.6, results-limit 1000, maxHits 20000, Vespa connect 150ms, EGS timeout 500ms** — the KT2 numbers exactly; the repo's committed 5000/0.5s are dev fallbacks. Word-bucket thresholds deployed: exact 0.88→0.85 (1→6+ words), phrase 0.74–0.76→0.72, broad 0.70→0.60. ⚠️ These are *stage* values; **prod deploy config is NOT in cd-deploy-configs yet** (no prod dir; AI-1497 Not Started — prod lives in the legacy Bitbucket pipeline). KT2 presenter asserted the same values for prod.
- Embedding model for text: **`gte`** (vs product's `gte_amp`), 768-dim, via same EGS; float32→bfloat16→hex on the wire; Caffeine query-vector cache; `experimentContext` forwarded to EGS so experiments can swap embedders (recent work, RELEASE-6109-adjacent).
- Multi-term parallel fan-out supported (16/64 executor) but not used in prod (per KT2).
- Curiosity: KVSS's test fixture `vespa_response.json` contains PLA/product docs with `coverage.documents ≈ 146M` over 8 nodes — copied from the product side; don't trust fixtures as ground truth for either corpus size.

## database-vespa internals (app package, repo-verified 2026-07-23 @ main 006b406)

The ground truth for everything Vespa-side. Bitbucket Pipelines: build on push, **manual "Deploy to PROD" gate** (Vespa CLI `vespa prod deploy`, app `admarketplace.vector-search.default`, `VESPA_APPLICATION` var for multi-app); rollback = re-trigger an older run's deploy step. `main`→prod, `dev` branch→dev instance.

**Topology (`services.xml`)** — four clusters:
- `default` (query container, 2vcpu/8GB, autoscale 2–8/region): search chains — `product_ads` chain adds **`com.adm.searcher.DedupSearcher`**, a custom Java searcher in this repo that dedups grouped hits by `dedupParams` (no-op when absent; this is VSS's dedup search chain). Threadpool 200, queue 5.
- `default-write` (feed container, 2vcpu/8GB local, 2–8): document-api + document-processing.
- `content_green` (product): min-redundancy 2, coverage-policy node, 8vcpu/**64GB**/474GB arm64 local. **West = grouped (2 groups × 7); East = still flat (count 14, 1 group)** — the group-topology migration is visible mid-flight in the file. Feeding concurrency 0.3, 2 request-threads persearch.
- `content_keywords` (text): min-redundancy 1, 4vcpu/8GB/237GB arm64, **2 groups × 6 in both regions** (already grouped). Feeding concurrency 0.6.

**Deployment (`deployment.xml`)**: prod endpoints are **private-link only** (zone endpoints disabled; AWS acct 292586329439) — explains the `*.z.vespa-app.cloud` mTLS endpoint in the services. Rollout order: **us-west-2a → 20min delay → us-east-1c**. `block-change` blocks revisions AND maintenance mon–fri 5–22 ET.

**Schemas** (only two are deployed; `product_ad.sd`, `pla_original.sd`, `pla_finetuned.sd` sit in the tree unreferenced by services.xml — decommissioned generations, all also 768-dim):
- `product_ad_green.sd`: `documentVector tensor<bfloat16>(d[768])`, distance-metric **angular**, HNSW **max-links-per-node 128, neighbors-to-explore-at-insert 1024** (heavy/high-recall graph). Rank profile `product_ad_vector` inherits `product_ad_base`: first-phase `if (cosine() <= query(minRankingScore), -1, cosine())`, `cosine() = cos(distance(field, documentVector))`, match-features cosine. Tuning @ main: **approximate-threshold 0.01, filter-first-threshold 0.115, filter-first-exploration 0.008, post-filter-threshold 1.0** — note older docs (rank-profile research, playbooks/vespa.md pre-correction) quote 0.015/0.3; values moved. Field tuning: brand/condition/gender/ageGroup/availability/plaFeedId/currency/country/language = fast-search + rank:filter; **googleProductCategory = fast-search only (no rank:filter)**; price/salePrice = plain attribute (no fast-search).
- `keyword_ad.sd`: HNSW **max-links 32, explore-at-insert 512** (lighter than product). `keyword` field = index + **enable-bm25**; synthetic `keyword_attribute` = `input keyword | attribute`, fast-search, **match: exact** (the brand-exact path). Profiles: `keyword_ad_vector` (legacy, global minRankingScore), `keyword_ad_native` (`nativeRank(keyword)` — the exact-search profile), **`keyword_ad_vector_mt_threshold`** — per-document cutoff `if (cosine() < matchTypeThreshold(), -1, cosine())` where `matchTypeThreshold()` picks by the *stored* `keywordMatchType` attribute. Schema-default thresholds: **exact 0.85 / phrase 0.80 / broad 0.70** — a third value-set alongside KT2's (0.88/0.74/0.70) and KVSS's committed word-buckets; the *effective* values are whatever KVSS sends per request, schema defaults apply only when omitted. approximate-threshold 0.01, filter-first-threshold 0.3.

## Feed path — the write side (repo-verified 2026-07-27)

```
Amplify/publisher catalogs → MySQL/RDS → Databricks (batch; embeddings computed HERE, upstream of Kafka)
  → Kafka topics:
      ric1.shopping-ads.pla-feed-data-embeddings        (product, keyed by plaId)
      ric1.audience-keyword-targeting-embeddings        (keywords; batchId fields = Databricks provenance)
  → feed service (validate 768-dim + hex-encode bfloat16) → vespa-feed-client (HTTP/2 mTLS) → Vespa
```

- **Embeddings are pre-computed upstream** — neither feed service calls EGS or the model registry; they only validate `embeddings.length == 768` (hardcoded) and convert float32→bfloat16 hex. The write-side embedding job is the Databricks/embedding-batch-service leg (per the Text Ads SPIR), *not* these services. Query-side (EGS) and ingest-side embedding are fully separate code paths — a model change must be coordinated across both (that's what the model registry is for).
- **Two feeders, one topic overlap**: `vespa-feed-service` (Spring Kafka, batch, Igor Lapay/Neena) contains BOTH the product feeder and a text-ads feeder on the *same topic + DLQ* that `keyword-vector-feed-service` (reactive, HTTP/2-tuned `connectionsPerEndpoint 4 × maxStreamPerConnection 256`, Yauheni Dzmitryieu/Roberto, SRS Jira) consumes. KVFS is the deliberate successor for keywords (richer validation/retry/error catalog, targets `content_keywords`/`keyword_ad`); VFS's text feeder defaults disabled. Verify which is live in prod before touching keyword feeding.
- **Deletes are state-driven, no TTL**: product `active==0 || is_blocked==1` ⇒ Vespa `remove`; keyword `keywordStatusId != 1` ⇒ remove. If upstream stops emitting a product, **its doc persists indefinitely** (relevant to Feb 2026 "PLA not updated" incident class).
- **Full puts only** — no partial updates. Doc IDs: `default:<schema>:<plaId|keywordId>`. Failures → per-type DLQ topics (`vespa-feed-service-product-ads-dlq`, `…keyword-targeting-embeddings-dead-letter-queue`); KVFS adds reactive backoff retry (3 attempts, Datadog alert past threshold 10). VFS relies on manual-ack redelivery only.
- Throughput: KVFS has the tuned HTTP/2 client; **VFS (the product/green path) uses unconfigured client defaults + blocking `parallelStream().join()`** — first place to look re: the ~6K FPS ceiling.
- KVFS carries a full local Vespa app for integration tests (`docker/vespa/…/keyword_ad.sd` — mirrors the real schema incl. HNSW 32/512).

## Embedding layer — query side (repo-verified 2026-07-27)

*(Corrects the runbook's "Redis + Python" one-liner: that conflated two services.)*

```
VSS/KVSS → EGS (Java 21 gateway, Redis-cluster cache) → embedder-service (Python/FastAPI, HF weights in-process)
                                              └→ Baseten (OpenAI-compatible /v1/embeddings) when experiment says so
```

- **EGS** (`POST /api/v1/embedding/batch` — README's plural "embeddings" path is wrong): virtual threads; Redis Cluster (Lettuce) cache — key `embed:{profileKey}:{keyVersion}:{sha256(text::profileKey)}` under prefix `embeddings::`, **TTL 7d** (dev 2d), MGET batch reads, async write-back, probabilistic TTL refresh; `GET /cache/stats` + `/cache/modelProfiles` for introspection. No-identifier requests silently default to profileKey **`gte`**.
- **Vendor routing is experimentContext-ONLY**: `mergedConfigs["modelDeploymentPlatform"] = baseten|internal` (default internal). The model registry never routes to Baseten — a Baseten URL in the registry only logs a warning. Model-aware Baseten endpoints (PR #33, 7/2026): `gte_amp` → `BASETEN_FINETUNED_PRODUCT_ADS_MODEL` URL, else `BASETEN_BASE_URL`; `gte_amp`-with-unset-URL is rejected, not misrouted. Parity gotcha: internal embedder 400s on model-name mismatch, **Baseten ignores the model field entirely** (one deployment = one model).
- **embedder-service** ("Text2Vec"): FastAPI/Hypercorn, **one model per process** (alias enforced, 400 on mismatch) — that's why multiple deployments exist (`dev-embedder-service-green` etc.). Alias map: `gte` → `Alibaba-NLP/gte-multilingual-base`, **`gte_amp` → `admarketplace/gte-finetune-12-03-2025`** (private HF, Dec 2025), plus unused `bge_m3`/`e5`/`qwen3`. ONNX Runtime session pool (default 2; README says 10 for live query) or torch; GPU-first (CUDA 12.6 image); mean-pool + L2-normalize; token-aware sub-batching at 4096 tokens (the real batch limiter). **Repo quiet since 2025-12-11** — matches the SPIR's "embedder-service must persist until text-ads next steps defined".
- **model_registry (Aurora MySQL, read-only consumers; no DDL in any repo)**: `VECTOR_SEARCH_PROFILE` (MODEL_ID, QUERY_EMBEDDING_SERVICE_ID, **INGEST_EMBEDDING_SERVICE_ID**, SEARCH_TARGET_ID, RANK_PROFILE) + `VECTOR_SEARCH_DEPLOYMENT` (SEARCH_TYPE, IS_ACTIVE, IS_PRIMARY_PROFILE) + `MODEL`, `EMBEDDING_SERVICE`, `SEARCH_TARGET`, `MODEL_RELEVANCY_THRESHOLD` (per word-count). The query/ingest service split in PROFILE is the registry's answer to the two embedding paths.
- **Latent risks flagged in code review**: 768 dims are asserted only by the *feed* services — the query path would pass a wrong-dim model through until Vespa rejects; no query/document prefixes are applied anywhere (fine for gte/gte_amp, would break `e5`/`qwen3` if ever enabled); EGS logs full request text at INFO (PII/verbosity).
- Owners: EGS — Stephen Ince, Rama Mukkamalla, Andrey Ruzin, Neeraj Ramkumar (Baseten work). embedder-service — Benjamin Luckow, Stephen Ince, Joseph Deferio.

## The caller contract (api-client, repo-verified 2026-07-27 @ main 61f2b5c, 6/24)

- **KVSS and VSS run divergent contracts, not just versions.** KVSS pins **1.0.75** (last Bitbucket-era tag, 4/27) — the old rich shape: `queryTerms` as `map<term,IntentType>`, `minScoreExact/Phrase/Broad`, `filter.audienceIds`, `allowConquesting`, plus the keyword DTOs (`KeywordVectorSearchResponse`/`KeywordMatchResponse`). The GitHub-era **1.1.x** line (VSS; version = `1.1.<CI run#>`, **no git tags**) trimmed all keyword types and `IntentType` out and added the Discover shape. A 1.0.75 caller can't see Discover types; a 1.1.x caller lost the keyword types.
- 1.1.x spec defines only ONE operation (`POST /api/v1/search/product-ads/vector`). **`DiscoverSearchRequest` (3.0: `queryTerms[]` of `{query, context}`) is a schema with no wired endpoint** — VSS implements `/discover/product-ads/vector` in code, the shared spec lags. Also: `countryCodes`/`languages` appear in the Discover *example* but aren't declared in `QueryTermRequestContext` (incomplete port).
- `QueryTermRequestContext` (per-term 3.0 filters): plaFeedIds, brands (exact IN), googleProductCategories ("prefix match up to two levels"), conditions, genders, ageGroups, currencyCodes, minPrice/maxPrice (spans price *and* salePrice).
- Diagnostics contract is rich: per-term `databaseLatencyMillis`, `searchResultsSize`, effective thresholds, `searchCoverage` (%/totalDocuments/candidatesFound/degraded), Vespa errors, and even `queryTermVectorHex/Floats` — useful for latency/debug work (AI-1542/1545).
- `ExperimentContext` is externally mapped to `com.admarketplace.experimentation.sdk.ExperimentContext` (dep `experimentation-platform-model`), not defined in-spec.
- AI-1546's `qt` user-prompt support is **not** in the shared spec yet (main unchanged since 6/24; the work is In Review elsewhere). Publishing: JFrog via GitHub Actions; owners: Kanan Mehdizade (1.0.x era), Joseph Deferio (Discover), Igor Lapay (diagnostics/testing params).

## Ranking posture (as of 2026-07)

Both services: retrieval signal == ranking signal (cosine retrieves and ranks; single-phase with threshold cutoff, `rank-score-drop-limit: 0`; current tuning values in the database-vespa section above). Acknowledged wasted headroom; second-phase / LTR / hybrid BM25 scoring are explored in the rank-profile research + hybrid POC docs, not in prod. Corpus size quoted variously as 70M/75M/146M docs and 8 vs 14 content nodes across docs of different vintages — re-derive from the Vespa console, don't cite these.

## Ownership (recurring, from Jira + Slack, 2026-07)

- **Oren Forer** — infra-side Vespa lead (latency epic INFRA-3016, topology in prod, connection pooling, test clusters, feed throughput).
- **Neena Sulakhe** — topology/deployment/indexing (RELEASE-6129, AI-1386, AI-1448 resiliency epic); created #vespa-changes.
- **Joseph Deferio** — VSS/KVSS service internals (connection pooling analysis, query sanitization, Text Ads SPIR, on-call runbook).
- **Artem Dippel** — AI-team Vespa engineer (AI-1545 latency 3.0-vs-2.0, AI-1494 github migration, AI-1546 qt support).
- **Sean Moriarty** — cluster ops (content blue/green, rightsizing SPIR, DR doc). **Ivan Trichev** — creds/mTLS/Datadog. **Arman Arakelyan** — experimentation-platform Vespa configs. **Roberto Simoes** — KVSS KT sessions, mock service. **Bhupesh Hada** — testing framework. **Disha Nikam** — embedding relevance epic AI-1439. **Saksham Bhatla** — ramping up (AMP Discover initiative AI-1551).

## Active workstreams (2026-07-23 — will stale fast)

1. **Flat → group topology migration** — in flight THIS WEEK (RELEASE-6129 In Progress; dev comparison running; prod-west next). Channels #vespa-grouped-topology, #release-6129-vespa-group-topology.
2. **AI-1545 latency 2.0 vs 3.0** — In Review, result REVERSED on rerun (7/23: 3.0 avg 34.3ms vs 22.2, p99 196 vs 36; first run showed opposite). Root cause isolated by a nest session 7/23: the 3.0 GPC hierarchical-prefix + null-sentinel OR clause costs +40–120ms/query (`runs/2026-07-23-ai1545-vespa-latency.md`, `playbooks/vespa.md`). Feeds AI-1542. Distrust any cached latency claim.
3. **Bitbucket → GitHub deployment migration** — AI-1494 (In Review) then AI-1496/1497, INFRA-3343 for feed service. Explains the dual bitbucket/github repo presence.
4. **LON1 region** — INFRA-3410 + INFRA-3458 (private link), both unassigned, bumped 7/22. Presumably Qwant/EU-driven.
5. **Vespa search strategy testing framework** (Bhupesh) — offline dev-instance + ARES grading + canary A/B; AI-1340 (online multi-strategy testing) Done.
6. **Embedding model transition** — epic AI-1439; second content cluster + model registry; text-ads left on old GTE cluster (SPIR decision pending).
7. **SOLR → Vespa** (Amplify, WF-16565) — separate consumer stream, Not Started.

## Ops & monitoring

- Datadog: **vespa-cloud-service-dashboard** (`43c-s3g-tae`); vespa-feed-service dashboard (`f4p-upr-ehg`); VSS logs `service:vespa-search-service* env:prod`; alerts land in #prod-relevance-yield-alerts and #devops_alerts_npe (noisy — Datadog bot). Vespa Cloud-native metrics NOT yet in Datadog (asked 7/23, open).
- Runbook: "Relevance & Yield On-call Runbook" (Google Doc, jdeferio) — VSS-timeout triage: VSS latency high + Vespa CPU normal → VSS is the culprit (common signature).
- Incident history (channels): timeouts 5/02 + 5/11, latency 2/18 + ric1 3/13, discrepancy 1/28, PLA-not-updated 2/26, maxHits 6/18 (Vespa-initiated upgrade broke app; postmortem in #ext channel 6/30), latency spike 7/12 (vendor ticket SUPPORT-781).
- Known gotchas: Yahoo queries ending `.`/`...` are illegal Vespa syntax (sanitization added, AS-12642); VSS rides java.net.http.HttpClient's default connection pool over h1.1 (INFRA-3380 open); feed throughput ceiling ~6K FPS after container-cluster tuning (Oren, 6/10); indexing changes cost ~5-6% memory, rolled east/west with traffic shift.

## Slack channels

- **#vespa-changes** (C0APXKGB2D6) — main internal coordination.
- **#ext-admarketplace-vespa** (C091NJML1AB, private) — vendor channel; Vespa team (Kristian Aune, Jon Bratseth, Eirik Nygaard, Gleb Sizov) answers directly; office hours Wed 10:00 ET, 30min.
- **#proj-vespa-cicd**, **#adbot-agent-vespa-releases** (bot: upstream Vespa release notes), plus per-release/incident channels (search "vespa" in channel names).

## Key documents (Google Drive)

| Doc | Author | Why it matters |
|---|---|---|
| Vespa Rank Profile Research (`1eDdKPfty0izL84ZZFCQWMi-WHwkdF6jeHAKzasBrJ3w`) | Varun | A-B-Z plan for ranking: current single-phase cosine → phased ranking/hybrid. Cited by merge plan. |
| Merging Text and Product Ads Meeting Notes (`1v6jOgG6uF4WSEhjrjeAYz46LwkOhfbBsSmawlY0UsFg`) | Varun/Deferio/Yaarit | Source of the a·kvssScore+b unified-score plan in map/aas.md; Sept target = CIV-feature neural weighting; Z = true auction model. |
| Text Ads in Vespa — SPIR (`1MmcIYuQ5q4BQUtw7X1x3hiTYQeUPZvxPj1quhVNeDg0`) | Deferio | Text/product coupling problem; cluster-separation options; embedder-service constraint. |
| Vespa search strategy testing framework (`1vncvgcJO-NKyJMrmSlnQCLpDCx7ZoP0tM3WaakazUyY`) | Bhupesh | Offline+online experiment framework design, ARES grading, canary. |
| Ranking within Vespa (`18i8v-eR4_dW9-_4JM03CAx_NgvSNkEDU-8v8PrYqlYA`) | Neena | Ranking-phase primer w/ our numbers (8 content nodes, targetHits 100 → 800 candidates); LTR options; Searcher POC. |
| POC — Hybrid Search & Ranking Profiles (`19t78pScxV6rEJ9VaXmU0Uwhg0WzUyIKYgYy99CQ9yow`) | Roberto | Hybrid ANN+BM25 POC results. |
| R&Y On-call Runbook (`1DYYLJSctsSrAC_uBlUN3pHsLXKjpyAVzd78STJPdyhc`) | Deferio | VSS/KVSS/EGS triage flows; prod-testing policy. |
| SPIR: Vespa Rightsizing (`1gDYSDM0Mj7kkXLJigjYzB5-VU41tnKbvuH6UOo_HWXk`) | Moriarty | Cluster sizing rationale. |
| Vector Search Disaster Recovery (`1yCYuzHb6cfK2nxnWJRhtk8Fe-0gGhx3C5ZpkgyCxRiM`) | Moriarty | DR posture. |
| Model Embedding Transitioning in AMP Vector Search (`1mOhRRWSW7l64N2Ltrm0TDpkn5oFHBEyp-DW6vl0oRuQ`) | Deferio | Dual-cluster / model-registry transition mechanics. |
| KVSS KT2 notes 7/20 (`1Fl8l8tbKAvWlw9_aPYY_hz_XMMLvzBAZkpK5qClnLFE`) | Gemini/Roberto | KVSS mechanics (thresholds, timeouts, fields). KT3 planned: feeder, schema, dashboards. |
| Diversification and deduplication of query results (`1fkipJBPj7US3JGkaa4Uz8VO2ZT3bFU-v383Q2CVXGPY`) | Neena | Result diversity/dedup design. |
| Vendor-POC era (2025): Test Queries, Vector Search Vendor POC Relevance, Search Vector Algo Results | swu/akharlamov/Varun | How Vespa was chosen; historical relevance baselines. |

## Jira anchors

Epics/umbrellas: **INFRA-3016** (low-latency master epic, Oren) · INFRA-3287 (workstreams 5/26) · AI-1448 (deploy resiliency, Neena) · AI-1439 (embedding relevance, Disha) · AI-1347 (creative-group filtering deprecation, Deferio) · WF-16565 (SOLR removal) · AI-1551 (AMP Discover initiative, Saksham). Note: JQL `text ~ "vespa"` returns 50+ tickets touched in the last 10 days alone — always re-query, don't trust this list past its date.

## Cross-refs

- `map/aas.md` — how VSS/KVSS scores flow into the auction (rawVespaScore ×1e6; kvss linear a=0.93 transform; 2.0 vs 3.0 ranking split).
- AI-1542 (Varun's latency work) consumes AI-1545 results.
