# KVSS — Keyword Vector Search Service

*(map entry started 2026-07-23 from the 3 "KVSS - KT" sessions; facts dated —
re-derive anything time-sensitive. Source = Gemini auto-notes, which mangle
several names — see "Transcription caveats" at the bottom before trusting a
term.)*

## What it is

Semantic **vector search for text ads**, added **alongside** the legacy lexical
keyword-matching flow (the "Keyword Matching Service," **Elasticsearch**-backed —
*not* Solr; see corrected caveat at bottom). Sits **behind AAS on the text-ad
path** (`AAS → KVSS`; product ads go `AAS → VSS`, a separate service) — see
[aas.md](aas.md). Backed by Vespa — **repo-code internals (endpoints, schema,
rank profiles, thresholds, YQL) live in [vespa.md](vespa.md)**; this entry is the
semantics / product-behavior / history view.

**Canonical sources** (prefer these over the KT Gemini-notes this entry was seeded from):
- Confluence **"Keyword vector search service (KVSS) - SC227"** (Technology space) —
  service/runbook page: prod/stage/dev hosts, live curl example, dependency risks.
- **TDD "Text Ads Vector Search"** by **Roberto Simoes** (Google Doc
  `1iQD9iLIxLcFgoS-DYi11VqWR3OIBGbIcr7eC7rqovng`), tracked under Jira **SRS-1570**
  (project **SRS = "Search Relevancy Squad"** — KVSS's Jira home). Reporter of the
  SRS build tickets was contractor Yauheni Dzmitryieu (now deactivated).
- Requirements: "AMP Discover — Pub GTM & Ad Selection Ideal State" (Norbert Tamas, 2025-09-30).
- Repos are **Bitbucket** (per SC227): `keyword-vector-search-service`,
  `qe-kvss-performance-test`; Vespa app package (schema `keyword_ad.sd`) in
  `database-vespa`. (vespa.md notes a Bitbucket→GitHub migration in flight.)
- **Build tracker** PM view = project "**Text Ads – Positive Keywords**" (Norbert
  Tamas, Theme: Ad Selection; card 7/2/2026): M0 Retail Brand Intent Dictionary →
  M1 Match Type Semantics Redesign → M2 Data Migration & Cleanup → M3 Service
  Decommissioning, **all Done**. Slack **#proj-positive-keywords**. Doc
  `1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`. (This is the lexical→semantic
  transition the KT sessions below describe, from the delivery side.)

The core idea: keywords are embedded into vectors; an incoming query is matched
by vector similarity, and **relevance-score thresholds** decide which *match
type* (broad / phrase / exact) a candidate qualifies for — replacing the old
publisher-configured match-type levers.

## Two search paths (intent decides)

Intent classification (done upstream, at SSP/Intent Classifier) routes each query:

- **Brand intent → exact search.** Bypasses vector search entirely; does a
  character-by-character string match against a **brand-keyword DB**,
  case-insensitive. Implemented as a Vespa `attribute`-field match (no
  tokenization) — the presenter stressed this is technically a *"keyword
  attribute search," not "exact match"* (exact is a match *type*, a different
  axis). Strictness is deliberate: a **typo in a brand name is NOT corrected to
  the brand** — it falls through to vector/non-brand search, so only correctly
  typed brand queries serve brand ads.
- **Non-brand intent → vector search.** Tolerant of typos/variation; uses the
  hybrid recall + thresholds below.

## Match-type thresholds (KT2 values are authoritative)

Vespa applies thresholds in a **"ranking profile" that FILTERS** (drops
candidates below the min relevance for their assigned match type) — it does
**not** reorder results.

| Match type | Threshold (KT2, 7/20) |
|---|---|
| Broad  | **0.70** |
| Phrase | **0.74** |
| Exact  | **0.88** |

(KT1 quoted "7 / 8" on a 0–10 feel for broad/phrase — treat as illustrative;
the 0.70/0.74/0.88 decimals from KT2 are the real defaults.) Thresholds are
**per-query configurable**; code applies them via an if/else and **defaults to
broad** when the site/KVS passes none. Primary implementation fn:
`keyword attribute base`.

- 2026-07-23 (repo check, see [vespa.md](vespa.md)): the *committed*
  `application.yml` defaults differ from the KT2 numbers — thresholds are
  per-word-count buckets (e.g. one-word exact/phrase/broad 0.88/0.72/0.72,
  six-plus 0.85/0.70/0.70), targetHits default **5000** (KT2 said 500), search
  timeout **0.5s** (KT2 said 50ms). Likely prod env-var overrides vs repo
  defaults — verify against deployment config before relying on either set.
- 2026-07-23 (app-package check): a *third* value-set exists — schema-level
  defaults in database-vespa `keyword_ad.sd` (`keyword_ad_base` inputs):
  exact **0.85** / phrase **0.80** / broad **0.70**. These apply only when KVSS
  omits `minScoreExact/Phrase/Broad` from the request; the effective values are
  whatever KVSS sends. Mechanism confirmed in-schema: `matchTypeThreshold()`
  filters per-document by the stored `keywordMatchType` attribute (drop, not
  reorder — as KT2 described).

## Request / response contract

Endpoint (Confluence SC227 live curl, mirrors VSS's `/product-ads/vector`):
**`POST /api/v1/search/text-ads/vector`**. *(vespa.md's repo read lists the base
as `/api/v1/search` — treat the `/text-ads/vector` sub-path as the callable one;
reconcile against the controller if it matters.)*

**Request** (per TDD): `queryTerms[]` (searched in parallel), optional `requestId`
(trace id SSP/DSP→KVSS), `limit` (text ads per QT, **default 20**),
`filter.audienceIds[]` (= ad groups in Amplify), `enableDiagnostics` (default
false). The runtime request has since grown intent/brand fields and
`allowConquesting` (see vespa.md `VectorSearchRequest`).

**Response is keyword-level metadata, NOT ad creatives.** `keywordMatchings[]`,
each: `audienceId`, `score` (raw cosine), `keywordId`, `keyword`, `keywordType`
(e.g. `"vector"`), `keywordMatchType` (`broad`/`phrase`/`exact`), `queryTerm`,
`destinationUrl`, `mobileDestinationUrl`, `useUtm`. Plus per-QT `diagnostics`
(`databaseLatencyMillis`, `searchResultsSize`). The DSP enriches from this,
selects a creative from the ad group, and runs the final auction. **Dedup happens
in the DSP** (best keyword by cosine score), not in KVSS.

- **Conquesting** (bidding on competitor keywords): ignored **by default**;
  only honored when the placement has the feature enabled. Publisher-level flag
  `allow_conquesting` defaults **false**.
- SSP-side result props: **`results_PA`** (product ads) vs **`results_TA`**
  (text ads). API versions **1.0 / 2.0 / 2.1 default these differently** —
  KT1 flagged reviewing the 2.1 defaults for placements serving *both* product
  and text ads (open item).
- Other config seen: `use_UTM` (URL building).
- **Diagnostics flag** output: result size, search coverage, total candidate
  counts, and **mean scores broken out by broad / phrase / exact**.

## Vespa mechanics (the meat of KT2 + KT3)

- **`index` vs `attribute` fields.** `keyword` field → `index`: tokenized,
  BM25 / token-based (broad, fuzzy-tolerant). `keyword attribute` field →
  synthetic `attribute`: **no tokenization**, string-equality optimized — the
  one used for strict brand matching. *(KT2 next-step: get a code example of
  each — may be clarified in a later session.)*
- **full search vs fast search.** Full = scan all docs. Fast = hash-map-like
  lookup of similar keys, skips unnecessary segments — faster but needs a
  precise 1:1 match.
- **Hybrid recall (vector path).** Combines **nearest-neighbor + lexical**
  search to maximize recall. NN depth (`targetHits`) = **500**; NN alone
  doesn't return 100% of ads, so the lexical/embedding leg catches the misses.
  Both result sets are ranked by vector-score similarity. `targetHits` = how
  deep Vespa searches.
- **Timeouts.** Default **50 ms (0.05 s)**. **Soft timeout** enabled for text
  ads: at 50 ms Vespa returns whatever it has rather than waiting for full
  recall. **`softTimeoutFactor = 0.6`** in prod → 60% of the budget to query
  processing, 40% to ranking; tune if timeouts/ranking-failures spike.
- **max hits** is no longer settable via URL — now lives in **Vespa schema
  profiles** (was previously adjustable on the fly).
- **Query building.** Exact search → lexical YQL against the string-equality
  index field + its ranking profile. Vector search → vector query + a ranking
  profile carrying the match-type thresholds. Audience-ID and
  competitor/conquesting filters apply to both.
- **Parallelism.** Code supports parallel processing of multiple query terms in
  one request (e.g. separate brand + non-brand calls) — **not used in
  production** currently.

## Architecture & data flow

**Feed (keyword ingest):**
```
Campaign managers → Amplify (upload keywords) → MySQL → replicate → Databricks
   → Kafka → Vector Feed Service → Vespa
```
The **feed service (KVFS / keyword-vector-feed-service)** is a clone of the
product Vespa feed service — a second consumer on a different cluster + document
set. Validates messages are well-formed and carry minimum required attributes;
reported **no processing errors yet** as of KT3.

- **Kafka topic:** `ric1.audience-keyword-targeting-embeddings` (from SRS-1684).
- **Message contract** (TDD): key = `id`; value carries `audience_id`, `keyword`,
  `keyword_type_id`, `keyword_match_type_id`, `keyword_status_id`,
  `destination_url`, `mobile_destination_url`, `use_utm`, `batch_id`, timestamps,
  and the `embeddings[]` vector. **`keyword_status_id`: 1 → upsert into Vespa; 0
  or 2 → delete.** Only a dedicated `keyword_type` (vector-eligible) is pulled
  into this stream; the legacy Elasticsearch indexer ignores it.
- Embedding is generated at ingest by the **embedding service (EGS)** — text uses
  model **`gte`** (768-dim); see vespa.md for the embedder details.

**Request path:**
```
SSP: query expansion + intent classification
   → brand?  → KVSS exact (keyword-attribute) search
   → else    → KVSS vector search
KVSS API entry = "API v1 search" → builds a context, picks API type
   (vector vs exact) from the intent classification
```

**KVSS ⟂ VSS decoupling.** KVSS (text keywords) and **VSS** (product vector
search) were split into **separate services** — different concerns, clusters,
schemas, independent scaling, blast-radius isolation — despite both calling
Vespa. They once shared model objects under deadline pressure; since decoupled,
shared/duplicated code addressed.

**Intent Classifier Service** (upstream of KVSS) now does **three things**:
(1) commercial vs non-commercial intent, (2) **partial query expansion** (typo
→ corrected term *before* search), (3) **brand intent**. It uses a predefined
table of brands + common mistypes. Built originally for **text-ad placements**;
per the presenter it currently applies to text ads, **not** product-ad
placements. KVSS receives an already sanitized/expanded/labeled query and does
**no further classification** — it just runs the exact search and filters by
DSP-provided audience IDs.

**Design lineage (why the notes and the TDD disagree).** The Nov-2025 TDD
described an earlier phase: brand intent stayed in the **existing Redis flow**
(vector ran only when Redis missed), and there was **no query expansion**
("treat the tokens provided as full query terms"). By the Jul-2026 KT sessions —
and confirmed in Slack (Artem Dippel, #proj-amp-discover-3-0, 7/01: *"KVSS
requires the caller to pass IntentType per query term … BRAND → EXACT search,
NON_BRAND → VECTOR search"*) — brand handling and partial expansion had moved
into the Intent Classifier + KVSS exact path. So KT reflects the current state;
the TDD reflects the MVP it grew out of. Backing tables exist in Databricks
(`amp` schema: `brand_keyword`, `intent_type`, `query_term_expansion`;
`model_registry` schema: `model_relevancy_threshold`, `vector_search_profile`).

## Publisher lever deprecation (a real decision, KT1)

The team **removed publisher-side match-type levers** — deemed an unnecessary
feature. Match type is now driven **exclusively by advertiser-side definitions**
(via the threshold model above). The Amplify/SSP side of this is tracked as
**"Proj California Roll"** (WF-16732: *"Deprecate Keyword Type Placement Config
in SSP,"* P0). Worth remembering as a settled design choice.

## The KT sessions

Presenter is anonymized by Gemini as *"Someone in Price is Right (CHQ, 11)"* —
a single consistent presenter across all three, from **Ankit Shah's team**
(Pinkel Gurung → Ankit Shah branch; the team owning KVSS: Roberto Simoes,
Neena Sulakhe, + Kanan Mehdizade). **Don't assert who the presenter is** — the
notes don't say.

| Session | Date | Organizer | Recording | Covered |
|---|---|---|---|---|
| KT1 | Jul 15 | Pinkel Gurung | [rec](https://drive.google.com/file/d/1aYe1xd2Iz8lrrw5IXzMcyZ7TSJu2Tbyz/view) | overview, match types, brand constraints, pub-lever deprecation, data flow, diagnostics. **Varun did not attend.** |
| KT2 | Jul 20 | Roberto Simoes | [rec](https://drive.google.com/file/d/1ZYdUliKAGeX8u0jKTlGt_80XwDajIHzt/view) | request structure, perf params + thresholds, API context/parallelism, Vespa query building, hybrid recall, index-vs-attribute fields, soft timeout, KVSS/VSS decoupling |
| KT3 | Jul 22 | Kanan Mehdizade | [rec](https://drive.google.com/file/d/1p_fXcoVz2f7MhbdMogG7Wmpra8WBIcvS/view) | attribute indexing, full-vs-fast search, brand/non-brand rationale, Intent Classifier Service, brand-keyword DB, code arch + thresholds, feed service |

Gemini notes docs: [KT1](https://docs.google.com/document/d/17DNfoYmR5kLAxeVWjlP1m0G1kfHZZDACLhx5MPU83P0/edit) ·
[KT2](https://docs.google.com/document/d/1Fl8l8tbKAvWlw9_aPYY_hz_XMMLvzBAZkpK5qClnLFE/edit) ·
[KT3](https://docs.google.com/document/d/1wVgkQk0my11FHIWDzjY-DErx87wyiea6AkUV3P9v2Pg/edit)

## Open items / not-yet-covered

- **Embedding model was never covered** in the sessions, but the TDD + repo
  answer it: text uses **`gte`** (768-dim float16 `documentVector`) via EGS — see
  vespa.md. Still outstanding for a future session: full Vespa **schema**
  walk-through and **data dashboards** (KT2/KT3 next-steps).
- Code example contrasting `keyword` vs `keyword attribute` fields (KT2 owed).
- **2.1 API default settings** for publisher ad requests when both product &
  text ads are involved (KT1 group action).
- Design doc + policy-keywords doc to be distributed (KT1 action) — **not yet
  landed anywhere in the nest**; grab it if it surfaces.

## Transcription caveats (Gemini mis-hears — do not propagate)

- **"Solar" ≠ Solr — the legacy text-ad keyword engine is Elasticsearch.** The
  Keyword Matching Service (Confluence SC85) and the TDD's "current state" are
  Elasticsearch-backed (consistent with the `elasticScore` signal noted in
  aas.md). "Solar" is a Gemini mis-hear (or the presenter loosely saying "Solr").
  A *separate* Amplify Solr→Vespa migration does exist (WF-16565, per vespa.md) —
  but that is not the KVSS-replaced path. Treat KVSS's legacy as **Elasticsearch**.
- **"Vaspuff" = Vespa.**
- **"Digital Signal Processing (DSP)" = Demand-Side Platform** (`dsp-engine`).
- **"Service Selection Platform (SSP)"** — Gemini's expansion; the real term is
  **Supply-Side Platform** (`ssp-engine`).
- **"KVS" = KVSS** (used interchangeably in KT3).
