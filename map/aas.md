# AAS — Ad Auction Service

*(map entry started 2026-07-23; facts below dated — re-derive anything time-sensitive)*

## What it is

New Java 25 / Spring WebFlux service that runs ad selection as a DAG of steps
(search → dedup → scoring/CTR → pricing → auction). **Goal state: AAS contains
the full auction** and becomes "the ad selection engine," absorbing
responsibilities from DSP-engine and sunsetting SASS (Shopping Ads Search
Service). **Current reality: the auction is split between AAS and DSP** — the
ownership boundary is mid-migration and movable per-request via experiment
config (`aasRoutingLevel`, strangler-fig cutover; see `docs/experiment-cutover.md`
in the repo).

- Lead: **Joseph Deferio** (146 commits + 38 as jdeferio-amp; away week of 7/20–7/24, back ~7/27)
- Other contributors: Artem Dippel (65+11 — Discover 3.0 / text ads), John Exantus (repo transfer + CI/CD, INFRA-3149)
- Team: Relevance & Yield (Slack #team-relevance-yield C08GKCC9742, private; Yaarit Even's channel)
- Org context deck ("AMP System Architecture & Team Boundaries", Norbert Tamas, May 2026):
  https://docs.google.com/presentation/d/1pSCgX6xAmGIJbqiCDEg_tXYzF4CDtmdRADnVT87FgB4

## Request flow

```
SSP (ssp-engine, /di) → DSP (dsp-engine) → AAS (POST /api/v1/ad-auctions)
                                            ├→ KVSS  (keyword-vector-search-service — text ads)
                                            ├→ VSS   (vespa-search-service — product vector search)
                                            ├→ Redis (ASIN/GTIN editorial lookups)
                                            ├→ [migrating] AdvertiserPricingService, AdvertiserCtrService
                                            └→ Kafka auction-xray → Databricks
```

SASS (wrapper over VSS + Redis caches) is being deprecated — AAS 2.0 product
path now goes direct-to-VSS. KVSS remains as-is behind AAS (its own map entry
now: [kvss.md](kvss.md) — from the 7/15–7/22 KT sessions; Vespa platform +
both search services: [vespa.md](vespa.md)). Auction math at
DSP (Discover 3.0, per 7/23 sync): `unifiedScore * CTR * CPC`.

## Repos & endpoints

| Thing | Where | Notes |
|---|---|---|
| Service | github.com/admarketplace-gh/**ad-auction-service** | GitHub (engines are on Bitbucket). Excellent docs: README, `docs/architecture-plan.md`, `docs/experiment-cutover.md`, `docs/architecture-diagrams.md`, `.ai/rules/` |
| API DTOs | github.com/admarketplace-gh/**ad-auction-service-api** | shared contract module |
| Java client | github.com/admarketplace-gh/**ad-auction-service-client** | embedded in DSP; auction contract on branch `AI-1516-auction-contract` |
| Upstream | bitbucket: `dsp-engine`, `ssp-engine`, `amp-discover-model` (ASR/ASV envelope) | DSP routing to AAS: dsp-engine PRs 795/798/818/836; branch AI-1539 |
| Stage | stage-ad-auction-service.ric1.admarketplace.net (Swagger at /webjars/swagger-ui) | prod since ~2026-06-17 |

## Two API generations flowing through AAS

1. **2.0 (legacy DSP contract)** — product + text ads. This is the migration
   track (milestones below): ramp traffic, then move CTR/pricing/auction in.
2. **Discover 3.0** — new `/di` API (SSP → DSP → AAS), pCIV intent payloads,
   unified text+product retrieval. Artem Dippel's track (AI-1435/1437/1513…).
   3.0 auction lives in AAS `DiscoverAuctionStep`/`DiscoverRankingStep`; the
   "unified retrieval score" puts text and product on one scale so DSP's
   auction can multiply it in regardless of ad type (Saksham thread 7/21,
   #proj-amp-discover-3-0).

## Milestones (Joseph, channel-creation msg 2026-05-13)

1. Product ads pass-through via FeatureFlag ramp ✅ (prod 6/17, traffic 6/22)
2. Text ads pass-through ✅ (7/02)
3. Migrate SASS features to AAS / remove SASS code in DSP — ~done (direct-to-VSS live 7/02)
4. Migrate product ads auction to AAS ⏳ (CTR/pricing/auction on stage)
5. Migrate text ads auction to AAS ⏳
6. Tiles auction in AAS — not started

## State as of 2026-07-23

- **Prod:** 2.0 product + text ads flowed through AAS at 100% exposure on 33%
  of traffic 7/13–7/17 (Product: Target 11/Exp 35; Text: Target 12/Exp 36).
  AAS there does **search only** (`aasRoutingLevel: "search"`); CTR/pricing/
  auction still DSP-side in prod.
- **Stage:** full migration deployed — AAS `0.2.412-ai-1518` + DSP
  `1.1.1097-AI-1539` run search+CTR+pricing+auction in AAS. Joseph retrofitted
  the DSP regression suite (qe-dsp-engine-api-tests, branch AI-1539, pipeline
  `run-aas-parity`): 98/98 passing 7/18.
- **Not merged:** CTR (PR #49 / AI-1517) and Auction (PR #50 / AI-1518) are
  open PRs on ad-auction-service; stage runs branch builds.
- **⚠️ Unexplained A/B win:** product-ads-through-AAS experiment showed
  +20% coverage, +5% CTR, +5% yield, +6-7% ARES vs control — for a supposed
  no-op re-architecture. Dhaval pressed for a cause; out-of-stock YQL filter
  ruled out (applies to both arms). Open question as of 7/21
  (#team-relevance-yield thread 1784393306.164469).

## Interim vs goal auction split (the crux)

- **Interim 3.0 flow (AI-1513 description, verbatim intent):** DSP does pricing
  first → calls AAS → AAS returns one merged product+text list ordered by
  relevance → DSP does CTR prediction → DSP does auction, and "must continue to
  respect the ordering of the ads in subsequent steps."
- **Goal (AI-1550/AI-1432):** CTR, pricing, and auction all move into AAS; DSP
  thins out. **Decided 2026-07-14 (AI-1519 comment): one-shot cutover** — DSP
  cedes pricing+CTR+auction together, not three phased cuts (refines the
  movable-boundary design in `docs/experiment-cutover.md`). Cutover *mechanism*
  (flagging, rollback, timing) still open — AI-1519 In Progress.
- Pricing wrinkle (AI-1516): in DSP today, pricing runs **before** product-ad
  search but **after** text-ad search — complicates the lift.
- ⚠️ "AAS as Request Conduit" (AI-1550 initiative title) is **defined nowhere**
  — the ticket is empty, no linked design doc anywhere in these tickets. The
  reading above is inferred from AI-1432's scope; confirm with Joseph/Saksham
  before treating as fact.

## Auction formula (read from code 2026-07-23)

**2.0 suggest auction** (prod formula lives in DSP; read here from the AAS
port on branch `AI-1518`, which carries explicit DSP-parity notes + 98/98
parity suite). Gate, both ad types: `useYield = discoverAuction=="yield"
experiment && any candidate has non-null CTR`.

- Yield mode, primary sort key — **identical formula for text and product**:
  `relevanceScore × CTR × advertiserBid(CPC)`, descending (`AuctionComparators.pricingScoreRanking`;
  null ctr/bid → back of list). `DEFAULT_CTR = 0.0011` fills missing CTRs.
- Differences are around the primary key:
  - **Text**: dedup (advertiser/brand) applies; tie-breakers CTR desc → bid desc; stamped TEXT_YIELD.
  - **Product**: **no dedup**; creativeYield enriched first from the *real* CTR
    (`(bid − payout) × ctr`, null if no real CTR); tie-breakers normalizedScore → creativeYield;
    optional per-queryTerm grouping (VECTOR_SEARCH_PRODUCT_ADS flag); stamped HIGH_YIELD.
  - **Score input differs**: product = Vespa vector score; text in DSP =
    elasticScore *or* keywordRelevanceScore chosen by keywordSource — AAS collapses
    text to the single KVSS vector score (flagged in code as a potential shadow-compare divergence).
- No-yield fallback (experiment off or zero CTR signal): text = score desc → bid desc;
  product = ctrType (ELME/DEFAULT ≻ LEGACY/null) → normalizedScore → creativeYield. Stamped RELEVANCE.

**Discover 3.0 in AAS** (main, live): no bids/CTR in AAS yet — pure relevance
rank on `normalizedScore`, uniform across types (`DiscoverRankingStep`):
- product: `floor(rawVespaScore × 1e6)` (SASS-era scale)
- text: `floor((a·rawKvssScore + b) × 1e6)`, defaults a=0.93, b=0; per-request
  overridable via experiment keys `kvssScoreLinearA/B` — this linear transform
  **is** the "unified retrieval score" from Saksham's 7/21 thread.
- Intent Adjacent (`placement.adCount` set): merge all targets, top adCount.
  Intent Inline: rank per target, top `target.adCount` (default 1).
- Economic auction for 3.0 stays DSP-side for now: `unifiedScore × CTR × CPC`
  (Pinkel sync note 7/23) — same shape as 2.0 with score := unified retrieval score.
- `DiscoverAuctionStep` is response assembly only ("bid and price resolution not yet wired").

## Build tracker (project-management view)

Norbert's **2026 Build Project Tracker** card "**Ad Auction Re-architecture**"
(Node: Relevance & Yield; **Build Accountable: Dhaval Shah + Norbert Tamas** —
distinct from eng TL Joseph Deferio; card updated 6/8/2026):
- Milestone TLs: M1–M4 **Joseph Deferio** (PL Amarachi Miller); **M5 "Ad Auction
  – DSP Redesign" TL Roberto Simoes** (⚫ not started). M5 = the DSP-thinning end
  state this map calls the goal split; tracker cites epics **AI-1172, AI-1175** on
  it — verify against the AI-1550/1432 hierarchy below, as the tracker's milestone
  numbering predates the 7/20–7/22 re-parenting.
- Tracker Z/A/B corroborates the goal state above (Z = "AAS has taken full
  ownership of search, CTR, pricing, and auction/reranking"; B = "DSP calls AAS
  without a feature flag, SASS deprecated").
- Tracker doc: `1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`. Card carries no
  Google-Doc/Confluence design link — matches the "design lives in repo `docs/`,
  not Jira" gotcha below.

## Key Jira (AI project = Relevance & Yield; AS = Ad Selection/engines)

Hierarchy: AI-1550 (Initiative, Saksham, created 7/20, empty — children
re-parented under it 7/22) ⊃ AI-1432, AI-1513, AI-1171, AI-1407.

- AI-1175 ✅ Launch AAS (selection only, 2.0). Saksham's 6/22 comment = post-launch roadmap: text ads → AAS→VSS direct → deprecate SASS
- AI-1432 epic: Migrate CTR/Pricing/Auction → AI-1516 (pricing; branches AI-1516[-blueprint|-pricing]), AI-1517 (CTR — empty shell ticket), AI-1518 (auction — empty shell) — all In Progress
- AI-1519 Decide cutover mechanism — decision recorded (one-shot), mechanism open
- AI-1407 Support Auction in AAS — Rejected 6/24 as **duplicate of AI-1432** (Dhaval)
- AI-1171 pCIV epic = 3.0 phase 1, product ads only; phase 2 = AI-1513 (3.0 text ads, priority Highest); AI-1435/1437 Discover 3.0 endpoint + contract (Ready for Release; arch diagram only exists as image attachment on AI-1435)
- AI-1491 Truncation at DSP instead of AAS — Blocked on DSP capacity; truncation stays in AAS for M1 (accepted tech debt)
- AI-1566 (Bug, 7/22): DSP→AAS drops experimentContext before KVSS/VSS. Likely cause: `ad-auction-service-client` 1.0.0.12 serializes context under `experimentContext.internal` while `ad-auction-service-api` expects `experimentContext` → deserializes empty. Explains Baseten→internal embedder misrouting 7/13–17; explicitly *not* the primary cause of the split after 7/17 (missing target-17 coverage on placements 5216/5280/5281). Related: AI-1392, AI-1479, AI-1173, `baseten-migration` label
- AI-1539 [DSP] routing mechanism + AAS workflow step chain

## Slack

- **#project-ad-auction-service** (C0B3HPAA1JA) — Joseph's consolidated channel, created 5/13. Read this first.
- **#proj-amp-discover-3-0** (C0ATZNKJCTG) — 3.0 releases (M1 ✅ 7/06, M2 ✅ ~7/09), SSP/DSP/AAS integration, QE findings (Narek)
- **#team-relevance-yield** (C08GKCC9742, private) — team channel; A/B results discussion
- Discover 3.0 external tech spec (Norbert Tamas):
  https://docs.google.com/document/d/1BgpjQCdppo-haIZvoiFgvdLoWMWnIZj5NwZouwg6eB8

## Gotchas

- Repo README's step table lags the branches — check open PRs before trusting "not yet".
- Jira status lags reality too (AI-1539 "Not Started" while its build is on stage; AI-1432 "Not Started" with children In Progress). Several key tickets are empty shells — the real design lives in the repo's `docs/` and Slack, **not** Jira (no Google Docs/Confluence linked from any core AAS ticket).
- AAS dedupe happens after Vespa fetch — AAS may return fewer ads than adCount (1.5× overfetch multiplier, Artem 6/30).
