# Vespa / VSS playbook

*(Living reference. Started 2026-07-23, from the AI-1545 latency investigation.)*

## Traffic context (per Varun, 2026-07-23 — read before framing any latency finding)

VSS serves **low-latency, high-QPS mainline product-ad traffic** — the money-maker path, where DB latency runs ~20ms and every added millisecond is a real per-query and cluster-capacity cost. The Qwant/pCIV 3.0 flow is an **emerging avenue, not the main revenue driver** — don't conflate their latency budgets (the Qwant "~3s Flash Answer budget" in some digests applies to that conversational flow only). A filter shape that adds 40–120ms is a rounding error against 3s but a 3–8x regression against mainline VSS. The AI-1545-style concern is 3.0-style filters reaching the mainline path, not Qwant UX.

## Repos

- **`admarketplace-gh/vespa-search-service`** (VSS) — Spring service that fronts Vespa. Key classes: `VespaYqlQueryBuilder` (assembles YQL), `WhereNearestNeighborBuilder` (ANN annotations), `ProductAdConstraintsTranslator` (3.0 filters → YQL predicates), `ExperimentSearchConfigResolver` (experimentContext keys like `vespaYqlVersionProduct`).
- **`admarketplace-gh/database-vespa`** — Vespa app packages / schemas. Product schema: `apps/vector-search.default/src/main/application/schemas/product_ad_green.sd` (cluster/schema `content_green.product_ad_green`).
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
- Rank profile `product_ad_base`: `approximate-threshold: 0.015` (filter matching <1.5% of docs → exact search over the subset, often *faster* than unfiltered ANN — why brand filters measure ~7ms), `filter-first-threshold: 0.3`.
- Results below `minRankingScore` (0.5 cosine) are dropped (`rank-score-drop-limit: 0.0`) — a low `searchResultsSize` can mean relevance-dropped, not "no inventory".
- Setting `experimentContext` keys from outside (e.g. `vespaYqlVersionProduct`) did NOT take effect with plain-JSON guesses (`{"internal":{...}}`, flat map) — the experimentation-SDK wire format is something else; also AAS currently drops experimentContext on forward (AI-1566).
- Truncated-prefix detector: query GPC `"Apparel & Accessories > Sho"` — 100 hits ⇒ prefix matching active; ~0 hits ⇒ exact IN active. Cheap way to tell which YQL version/clause a server is running.
