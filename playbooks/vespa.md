# Vespa / VSS playbook

*(Living reference. Started 2026-07-23, from the AI-1545 latency investigation.)*

## Traffic context (per Varun, 2026-07-23 — read before framing any latency finding)

VSS serves **low-latency, high-QPS mainline product-ad traffic** — the money-maker path, where DB latency runs ~20ms and every added millisecond is a real per-query and cluster-capacity cost. The Qwant/pCIV 3.0 flow is an **emerging avenue, not the main revenue driver** — don't conflate their latency budgets (the Qwant "~3s Flash Answer budget" in some digests applies to that conversational flow only). A filter shape that adds 40–120ms is a rounding error against 3s but a 3–8x regression against mainline VSS. The AI-1545-style concern is 3.0-style filters reaching the mainline path, not Qwant UX.

## Repos

- **`admarketplace-gh/vespa-search-service`** (VSS) — Spring service that fronts Vespa. Key classes: `VespaYqlQueryBuilder` (assembles YQL), `WhereNearestNeighborBuilder` (ANN annotations), `ProductAdConstraintsTranslator` (3.0 filters → YQL predicates), `ExperimentSearchConfigResolver` (experimentContext keys like `vespaYqlVersionProduct`).
- **`bitbucket.org/admarketplace/database-vespa`** — Vespa app package / schemas — **canonical; clone via SSH** (see `playbooks/bitbucket.md`). Product schema: `src/main/application/schemas/product_ad_green.sd` (cluster/schema `content_green.product_ad_green`). ⚠️ The `admarketplace-gh/database-vespa` GitHub copy is a stale migration snapshot (default branch `github_migration`, last push 2026-06-24) — reading it gives outdated tuning values. Full app-package digest: `map/vespa.md`.
- **`admarketplace-gh/ad-auction-service`** (AAS) — main caller; `docs/bruno/` has ready-made requests + stage env URLs. See `map/aas.md`.
- **`admarketplace-gh/locust-vector-performance-framework`** — John Exantus's load-test harness (the one AI-1545's description mentions).

## Endpoints (stage, RIC1)

- `https://stage-mercury-vespa-search-service.ric1.admarketplace.net`
  - 2.0: `POST /api/v1/search/product-ads/vector`
  - 3.0/discover: `POST /api/v1/discover/product-ads/vector`
- **Reachable from laptop, no auth, no VPN** (verified 2026-07-23). Be polite: sequential + sleep; it's a shared stage env.
- `enableDiagnostics: true` → response `diagnostics.<queryTerm>.databaseLatencyMillis` (Vespa-side DB time, excludes network) + `searchResultsSize`.

## Request shapes

- 2.0: `{"queryTerms":["<text>"], "requestId", "placementId", "limit", "enableDiagnostics", "filter":{"plaFeedIds":[...]}}`
- 3.0: `queryTerms:[{"query":"<text>","context":{plaFeedIds, brands, googleProductCategories, conditions, genders, ageGroups, currencyCodes, minPrice, maxPrice}}]`
- Test feeds used in AI-1545: `[4025,4122,4014,4004,4002,4028]`.

## Gotchas / mechanics (verified empirically 2026-07-23)

- **`testingParameters.yql` overrides the generated YQL** while bound params (`@plaFeedIds`, `@googleProductCategory0`, `@googleProductCategoriesNull`…) still bind from the request context — best tool for clause-level A/Bs against stage. Also accepts `rankingProfile`, `targetHits`, `approximate`, `distanceThreshold`.
- `totalTargetHits = max(limit, targetHits) × num content nodes` (`total-num-nodes-content-green`, prod default 14). **Stage behaves like ~2 nodes (~200 for limit 100)** — hand-built YQL copying prod's 1400 will not match native stage latency.
- 3.0 GPC filter is a hierarchical **prefix** match plus a **null sentinel** (`OR googleProductCategory IN ("")` — products with unset category also match; brand/condition/gender/ageGroup get the same `""`-appended sentinel in their exact `IN`). The GPC prefix+sentinel OR costs +40ms (dense category) to +120ms (sparse) per query, flat in targetHits; each branch alone is cheap. See `runs/2026-07-23-ai1545-vespa-latency.md`.
- Schema field-tuning asymmetry in `product_ad_green.sd`: `brand`/`condition`/`gender` = `fast-search` + `rank: filter`; `googleProductCategory` = `fast-search` only (**no rank: filter**); `price` = plain attribute (**no fast-search** — future latency landmine for price-range filters).
- Rank profile `product_ad_base`: approximate-threshold (filter matching less than that fraction of docs → exact search over the subset, often *faster* than unfiltered ANN — why brand filters measure ~7ms) and filter-first-threshold. Values on Bitbucket main 2026-07-23 (006b406): **0.01 / 0.115** (+ filter-first-exploration 0.008, post-filter-threshold 1.0) — the 0.015/0.3 cited earlier came from the stale GitHub copy/docs; re-read the .sd before tuning.
- Results below `minRankingScore` (0.5 cosine) are dropped (`rank-score-drop-limit: 0.0`) — a low `searchResultsSize` can mean relevance-dropped, not "no inventory".
- Setting `experimentContext` keys from outside (e.g. `vespaYqlVersionProduct`) did NOT take effect with plain-JSON guesses (`{"internal":{...}}`, flat map) — the experimentation-SDK wire format is something else; also AAS currently drops experimentContext on forward (AI-1566).
- Truncated-prefix detector: query GPC `"Apparel & Accessories > Sho"` — 100 hits ⇒ prefix matching active; ~0 hits ⇒ exact IN active. Cheap way to tell which YQL version/clause a server is running.

## Prod regime differences (verified 2026-07-27, Artem's prod-ric1 run @ AI-1545 c170901)

- **Stage filter-latency profiles do NOT transfer to prod — the slow slice reverses.** Same 1000 CIV requests both envs: stage GPC+brand = fastest shape (6.5ms avg; brand selectivity → exact-search regime); prod GPC+brand = SLOWEST (84ms avg, median 116, capped ~148). Prod GPC-alone 33ms, brand-alone 24.6 ≈ no-filter 21.9. The brand exact-search fast-path flip does not survive prod scale (~75M docs); the GPC×brand combination is what goes pathological. Never extrapolate a stage filter-latency measurement to prod.
- **Prod zero-ad 3.0 rows are SLOW** (44ms avg; GPC+brand zero-ad 73ms) unlike stage (11.8ms) — "found nothing fast" intuition is stage-only. Consequence: full-page-filtered and unfiltered averages roughly agree on prod (53 vs 45ms), so the 7/23 "filter keeps the slow subset" critique is stage-specific.
- **Prod VSS→Vespa timeout 150ms censors every AI-1545 prod stat**: observed max 148, 53/1000 rows bunched ≥130ms, 46 rows missing latency entirely (11 hard failures) and excluded from averages. Reported prod p95/p99 are floors, not estimates.
- CIV-derived samples carry **zero price/currency filters** (0/1000 both runs) — the two filters the 7/24 prod probe showed blow the 150ms timeout when combined. Any CIV-sample latency number understates real pCIV-traffic risk until price-carrying requests are measured.

## Root cause of the prod 3.0 slowdown (2026-07-27 session, offline-verified; regime labels pending live confirmation)

- **Two-key lock**: the pathology needs BOTH (a) a `brands` filter present and (b) a GPC value whose prefix matches >1 distinct category path in the corpus. Prod 1000-row decomposition: brand+multi-path GPC = 107ms avg / ~122 median; brand+leaf GPC = 25ms (even 4.2M-doc leaves like `Home & Garden > Decor > Rugs`); GPC-only multi-path = 35ms; brand-only = 25ms. Independent of brand size (Nike 847k docs ≈ nonexistent brands) and of result count (0-ad = 100-ad cost) → pure filter-evaluation cost.
- **Why brand is the trigger** (corpus stats, `prod_amplify.pla_gold.pla_feed_data_embeddings`, gte_amp active/non-blocked, 104.3M rows): unset-field populations — brand **0.96%**, condition 8.0%, GPC 9.7%, gender 26.5%, age 28.9%. Every sentinel-carrying clause estimates ≈ f(value)+unset-share; only brand's ~1% sits at/below `approximate-threshold 0.01` → the planner leaves the ANN fast path and evaluates the filter directly, where the multi-term GPC prefix OR (field has no rank:filter) costs 50–140ms. Large-sentinel filters (gender/age/condition) can't trigger the flip — matches GPC+cga measuring benign (~41ms).
- **Stage↔prod reversal explained**: the same flip happens on stage, but direct evaluation over stage's tiny corpus is fast (6.5ms) — the regime is invisible there. Corollary repeated: never tune filters from stage latency.
- Branch-dependence within multi-path (Clothing subcats ~139ms even at 36 docs/2 terms; Shoes 124; Electronics ~56) is NOT explained by docs-under-prefix or term count — open question for live probes/vendor (dictionary-range/posting-seek behavior suspected).
- Useful corpus facts: 9,008 distinct GPC strings; Apparel 14.0% of docs, Electronics 1.7%; test feeds [4025,4122,4014,4004,4002,4028] = 16.6% of corpus; in-stock 89.9%.
- **stage-UAT VSS (`vespa-search-service-stage-uat.ric1.admarketplace.net`, fronts the PROD-TEST Vespa app) is internal-only** (resolves to 10.x, unreachable off-VPN), unlike public stage-mercury. PROD-TEST probing requires VPN. Prod probing requires the runbook prod-testing policy: rate-limit + inform team + own PagerDuty.
- Analysis artifacts: `scratchpad ai1545-prod/` (analyze.py, brand_counts.tsv, gpc_counts.json); method + numbers in `runs/2026-07-27-ai1545-prod-numbers.md` (scrutiny) and the run log of this session.
