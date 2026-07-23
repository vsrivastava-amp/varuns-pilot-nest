# KVSS — Keyword Vector Search Service

*(map entry started 2026-07-23 from the 3 "KVSS - KT" sessions; facts dated —
re-derive anything time-sensitive. Source = Gemini auto-notes, which mangle
several names — see "Transcription caveats" at the bottom before trusting a
term.)*

## What it is

Semantic **vector search for text ads**, replacing the legacy lexical search
(Solr). Part of the "Positive Keywords" project revamping the text-ad search
flow. Sits **behind AAS on the text-ad path** (`AAS → KVSS`; product ads go
`AAS → VSS`, a separate service) — see [aas.md](aas.md). Backed by Vespa.

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

## Request / response contract

**Request** carries: query terms, intent classification (brand/non-brand),
conquesting flag, **audience ID** (= ad group in Amplify) for filtering, and
optional **diagnostics** flag.

**Response is metadata, NOT creatives** — KVSS returns `{keyword ID, ad
group / audience ID, score}`. The DSP then enriches, selects a creative from the
ad group (precedence hierarchy for destination URLs), and does the final
ad-serving decision (auction etc.). **Dedup happens in the DSP** (picks best
keyword by cosine-similarity score), not in KVSS.

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
The **feed service is a clone of the (product) Vespa feed service** on a
different cluster + document set. Validates messages are well-formed and carry
minimum required attributes; reported **no processing errors yet** as of KT3.

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

## Publisher lever deprecation (a real decision, KT1)

The team **removed publisher-side match-type levers** — deemed an unnecessary
feature. Match type is now driven **exclusively by advertiser-side definitions**
(via the threshold model above). Worth remembering as a settled design choice.

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

- **Embedding model was never covered** across the three sessions (flagged for
  follow-up in KT1 and never reached). Also outstanding for a future session:
  full Vespa **schema** walk-through and **data dashboards** (KT2/KT3 next-steps).
- Code example contrasting `keyword` vs `keyword attribute` fields (KT2 owed).
- **2.1 API default settings** for publisher ad requests when both product &
  text ads are involved (KT1 group action).
- Design doc + policy-keywords doc to be distributed (KT1 action) — **not yet
  landed anywhere in the nest**; grab it if it surfaces.

## Transcription caveats (Gemini mis-hears — do not propagate)

- **"Solar" = Solr** (the legacy lexical engine being replaced).
- **"Vaspuff" = Vespa.**
- **"Digital Signal Processing (DSP)" = Demand-Side Platform** (`dsp-engine`).
- **"Service Selection Platform (SSP)"** — Gemini's expansion; the real term is
  **Supply-Side Platform** (`ssp-engine`).
- **"KVS" = KVSS** (used interchangeably in KT3).
