# 2026-07-27 — AI-1545 prod run scrutiny (session: ai1545-prod)

- 2026-07-27 Task (Varun, in-chat): Artem's prod Vespa numbers landed 7:33 ET (comment 170901: 3.0 avg 53.2ms / p99 140 vs 2.0 avg 22.95 / p99 39, over 233/1000 full-page rows). Varun suspects same flaws as stage runs (biased dataset etc. — his comments 170698/170757). Verify.

## Method

Downloaded ticket attachments 77371 (prod full 1000-row CSV), 77372 (prod filtered), 77312 (stage 7/23 full — comparison baseline), 77277 (CIV input). Re-ran the 7/23 shape decomposition (scratchpad `ai1545-prod/analyze.py`). Verified Artem's published numbers reproduce exactly (avg 22.95/53.20, p99 38.5/138.7 ≈ his 39/140).

## Findings — the prod numbers are largely REAL; the stage-era critiques do NOT carry over

1. **Clean A/B vs stage**: same 1000 CIV rows, identical request-shape mix (GPC 212, GPC+brand 279, brand 143, none 281 … exact match stage↔prod). Same requests, different environment.
2. **The slow slice REVERSED between stage and prod.** Stage: GPC-without-brand was slow (40–53ms), GPC+brand was the *fastest* shape (6.5ms — brand selectivity → exact-search regime). Prod: **GPC+brand is the slowest shape** — avg 84ms, median 116ms, p95 139ms (filtered subset: avg 118, median 127); GPC-alone is only 33ms (cheaper than stage's 40); brand-alone 24.6ms ≈ no-filter 21.9ms. The brand fast-path flip did not survive prod scale; the GPC×brand *combination* is pathological there.
3. **Varun's stage critique ("filter keeps the slow subset; zero-ad rows are fast") no longer explains the gap.** On prod, zero-ad 3.0 rows are NOT fast: avg 44.4ms (GPC+brand zero-ad rows: 73ms) vs stage's 11.8ms. Unfiltered 1000-row averages: 3.0 45.0 vs 2.0 23.0 — same ~2x as the filtered set (53.2 vs 22.95). The full-page filter now only mildly overstates (it slightly *under*-weights GPC+brand: 19% of filtered vs 28% of population). Median paired diff moved too: +12ms prod vs +2ms stage.
4. **Censoring: the prod numbers UNDERSTATE the tail.** Prod VSS→Vespa timeout = 150ms; observed max = 148; 53 rows ≥130ms bunched at the cap; 46/1000 3.0 rows have no latency at all (vs 36 for 2.0) incl. 11 hard failures — timeouts excluded from every average. True p95/p99 > reported.
5. **Remaining dataset-bias critiques that DO still stand** (both directions):
   - CIV-derived sample sends **zero price/currency filters** (0/1000, same as stage). Artem's 7/24 prod probe showed GPC-or-currency + price combos blow through 150ms. Real pCIV traffic will carry price ranges → this run likely *understates* real-traffic risk.
   - Filter-shape mix (59% GPC, 45% brand) is an artifact of CIV extraction, not measured pCIV traffic mix — the traffic-weighted average is unknown.
   - Still measures single Vespa query DB latency; 3.0 fans out per intentTarget in AAS (Dhaval's e2e-via-SSP point stands).
6. Coverage gap persists: 511/1000 3.0 rows return 0 ads (vs 208 for 2.0) — prod slightly better than stage's 600, still the bigger product issue (feeds AI-1556/AS-13384).
7. **Cause is still fixable query shape, not inherent 3.0 cost**: repo re-verified today — `ProductAdConstraintsTranslator.translate` wraps brands/conditions/genders/ageGroups in `withNullSentinel` (`IN (…,"" )`), GPC gets prefix+`OR IN ("")`; currency/availability/price get no sentinel. Unfiltered-3.0 ≈ 2.0 on rows with no filters (21.9 vs ~23ms) on prod too.

## Disposition

- Assessment delivered to Varun in-chat; no Jira/Slack writes, no ticket comment drafted yet (Varun deciding).
- Read-only session: Jira attachment GETs + GitHub clone of vespa-search-service to scratchpad. No requests sent to any VSS/Vespa environment.
- playbooks/vespa.md updated with prod regime-reversal + censoring gotchas.
