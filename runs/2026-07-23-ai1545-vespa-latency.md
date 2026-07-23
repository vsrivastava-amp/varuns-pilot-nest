# 2026-07-23 — AI-1545 Vespa latency investigation (session: ai1545-latency)

- 2026-07-23 Task (Varun, in-chat): investigate AI-1545 ("Vespa latency measurement: 3.0 vs 2.0", Artem Dippel, In Review) — how it was measured, what repo, rerun the analysis, explain why 3.0 got slower / whether that's reasonable.

## How Artem measured it (from ticket comments)

- **Run 1** (7/22): 100 rows of `civ_sample_data.csv`, adCount 10. 3.0 request **derived from the 2.0 response's first ad** (brand, GPC, price widened [0.5x,2x], gender, age, condition). Result: 3.0 *faster* (avg 10.5 vs 12.3ms).
- **Run 2** (7/23): 1000 rows, adCount 100, 3.0 request built **independently from CIV fields**, only rows where *both* sides returned a full page kept (177 survive). Result: 3.0 *slower* (avg 34.3 vs 22.2ms, p95 69 vs 31, p99 196 vs 36).
- Metric both times: VSS's self-reported `diagnostics[...].databaseLatencyMillis` (excludes network).
- **Harness code is not pushed anywhere** — Artem ran it locally against/inside `ad-auction-service` (it mirrors `ProductAdVectorSearchStep` and `DiscoverSearchRequestBuilder`, reads `docs/civ_sample_data.csv` + `docs/bruno/vss-discover-search.bru`, writes `target/vss-latency-results.csv`). No AI-1545 branch/PR in the repo. Input + all output CSVs are **attached to the Jira ticket** (that's the reproducible artifact).

## Rerun 1: re-analysis of Artem's raw attached data

Verified his summary numbers exactly (avg 22.19/34.34, p99 36/196). Decomposition of the 177-row filtered set by 3.0 request shape:

| 3.0 rows | n | avg ms | p95 ms |
|---|---|---|---|
| no filters at all | 40 | 22.5 | 31 |
| brand present | 38 | **11.9** | 18 |
| GPC present (no brand) | ~114 | **42.5** | 94 |

- Median paired diff is only **+2ms**; the mean/p99 gap is entirely the GPC-without-brand tail. Not a uniform "3.0 is 55% slower".
- All top-15 slowest rows: GPC present, brand absent. Slowest are sparse categories (Home & Garden \*: 144–219ms); apparel categories 26–53ms.
- Run 2's 3.0 requests never contained price or condition filters (0/1000). Brand only 38/177.
- Coverage flag: **600/1000 of the independent 3.0 requests returned 0 ads** (vs 293/1000 for 2.0) — relevant to AI-1556/AS-13384 pCIV-request work, arguably a bigger deal than latency.
- Run-1-vs-run-2 reconciliation: run 1's 3.0 requests carried brand+price from a real returned ad (66/100 rows) → hyper-selective filter → Vespa exact-search regime → 10.5ms, matching run 2's brand-present rows (11.9ms). The "reversal" is a filter-selectivity regime change, not noise.

## Rerun 2: live controlled experiment on stage VSS

`stage-mercury-vespa-search-service.ric1.admarketplace.net` is reachable, no auth. ~350 sequential requests total (25/condition, 50ms gaps). Feeds = Artem's [4025,4122,4014,4004,4002,4028], limit 100 unless noted.

| condition | avg ms | hits |
|---|---|---|
| 2.0 "shoes" | 21.0 | 100 |
| 3.0 "shoes" no filters | 18.5 | 100 |
| 3.0 "shoes" GPC Apparel>Shoes | **63.2** | 100 |
| 3.0 same, limit 10 | 60.2 | 10 |
| 3.0 "shoes" brand=Crocs | 6.8 | 3 |
| 3.0 "shoes" GPC+brand | 6.6 | 3 |
| 3.0 "shoes" genders=[female,unisex] | 20.7 | 100 |
| 3.0 "cookware set" no filters | 22.2 | 100 |
| 3.0 "cookware set" GPC H&G>Cookware | **138.1** | 100 |

Clause isolation via `testingParameters.yql` override (same request, hand-built YQL, prod field list):

| GPC where-clause variant ("shoes") | avg ms | hits |
|---|---|---|
| no GPC clause | ~23 (at stage tth) | 100 |
| `prefix` only | 23.2 | 100 |
| exact `contains` only | 22.3 | 100 |
| exact + `OR IN ("")` sentinel | 35.3 | 100 |
| **prefix + sentinel (= production clause)** | **63.3** | 100 |
| sentinel only | 20.4 | 8 |

Cookware (H&G): prefix-only → **~0 hits**, 6ms; sentinel-only → 100 hits, 23ms; prefix+sentinel → 140ms.
Sentinel-OR cost is flat in totalTargetHits (63ms at tth 200/400/1400) — fixed filter-evaluation cost, not ANN exploration. No-clause scales with tth (23→61ms at 200→1400), which is how stage native (~200 = 100×~2 nodes) vs my initial hardcoded 1400 (prod: 14 nodes × limit) was reconciled.

## Conclusion (the "why")

1. The 3.0 request shape itself costs nothing — unfiltered 3.0 ≈ 2.0 (even slightly faster).
2. The entire regression is the **GPC category clause**, and specifically the **null-sentinel OR** that `ProductAdConstraintsTranslator.addGpcClause` emits (`googleProductCategory contains ({prefix:true}...) OR googleProductCategory IN ("")` — "also match products with unset category"). Each branch alone is cheap; the OR defeats Vespa's filter fast-path: +40ms (dense category) to +120ms (sparse category) per query. Artem's p99=196ms rows are sparse categories.
3. Brand/gender/condition (exact IN, `rank: filter` + `fast-search` in `product_ad_green.sd`) are cheap; brand is so selective it flips Vespa below `approximate-threshold: 0.015` into exact search → *faster* than no filter. `googleProductCategory` notably **lacks `rank: filter`** in the schema; `price` lacks `fast-search` entirely (future landmine if price filters ship — run 2 never sent one).
4. **Semantic red flag**: for sparse categories the "full page of 100 ads" is satisfied ~100% by the sentinel branch, i.e. products with NO category set. The filter pays 6x latency while doing ~zero category targeting on exactly those queries. Whether unset-GPC products should match is a product decision — that's the real lever (drop/replace sentinel → GPC filtering becomes ~free AND strict).
5. Is it "reasonable"? The measurement is real and reproducible, but it's a fixable query-shape/schema issue, not an inherent 3.0 cost. Fix candidates: (a) decide sentinel semantics (e.g. dedicated `hasGpc` bool field with `rank:filter`, OR of two bitvector terms, instead of `IN ("")` on the string attr); (b) materialize ancestor category paths as an array field with exact IN instead of prefix; (c) add `rank: filter` to `googleProductCategory`; (d) revisit `filter-first-threshold: 0.3` tuning.

## Repos/pointers (folded into playbooks/vespa.md)

- VSS service: `admarketplace-gh/vespa-search-service` (YQL builders, constraint translator). Schemas: `admarketplace-gh/database-vespa` `apps/vector-search.default/.../product_ad_green.sd`. AAS callers: `admarketplace-gh/ad-auction-service` (see `map/aas.md` — parallel session, same day).
- Artifacts: raw CSVs + analysis scripts in session scratchpad (`ai1545/` — analyze.py, live_experiment.py, yql_ab.py); key numbers preserved above and in the REVIEW draft.

## Disposition

- 2026-07-23 Findings drafted as Jira comment for AI-1545 → `REVIEW.md` (outward-facing; Varun disposes).
- 2026-07-23 Not sent anywhere; no Jira/Slack writes. Stage VSS got ~350 read-only search requests (sequential, throttled).

## Follow-up investigations (afternoon, same session)

- 2026-07-23 Comment posted by Varun on AI-1545 11:45 ET (v4 draft, verbatim) → REVIEW entry disposed, txt deleted. Dhaval replied 12:20 ET: empty GPCs expected ("a reality for our PLA data"); exclude-contradictions filter intended but known-heavy — plan is to convert filters into **score penalties**. Dhaval also asked Artem what "full page of data" means + whether 3.0 sends >1 target (multi-target = parallel Vespa fan-out).
- 2026-07-23 **"Full page per row" vs 600/1000 zero-ads — no contradiction.** Artem never claims all rows return full pages; "full page" is his *selection criterion*: only rows where BOTH sides returned all 100 ads count toward the latency comparison. Verified: filtered CSV = exactly the 177/1000 rows with both adCounts=100 (iteration sets match); his published averages recompute over those 177 to the last decimal ("178 requests" header is an off-by-one). Our 600/1000 stat is from the unfiltered file — the excluded rows. Both true. Nuance: zero-ad 3.0 rows avg 11.8ms (fast), so the filter keeps the *slow* subset — the headline gap describes the 18% of rows where both sides found abundant inventory.
- 2026-07-23 **Prod-2.0-vs-stage-3.0 mixup ruled out.** Replayed 60 exact request bodies from his CSV against stage-mercury: recorded ad counts reproduce (2.0: 88% exact/95% bucket; 3.0: 97%/97%), residual diffs small + symmetric (feed churn over ~8h), and his 2.0 latency profile (avg 22.2, range 15-37) matches our stage 2.0 measurements (avg 21.0). Both sides ran on stage. Standing caveat (Varun): stage ≠ prod — smaller vector store, possibly different compute — so ALL ticket numbers are stage-only; prod-shadow question remains open.
- 2026-07-23 **Clarifying comment POSTED to AI-1545 as Varun** (comment 170757, 16:03 ET) via Rovo `addCommentToJiraIssue` — Varun explicitly directed the post in-chat ("you can post the draft"), with one edit: dropped "worth pinning for anyone reading the headline numbers" from the opener. Real @mention for Saksham Bhatla via ADF. Content: (1) headline avg/p99 covers only the 177/1000 full-page rows — across all 1000, sides average about the same (19 vs 21ms); (2) stage-only numbers, smaller vector store than prod — prod-shadow suggested. REVIEW entry disposed, txt deleted.
