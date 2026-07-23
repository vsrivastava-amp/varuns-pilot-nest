# 2026-07-23 — A/B testing / experimentation platform context sweep

Session slug: `expctx`. Varun asked for broad context on how we run A/B experiments
(experiment variables, the A/B platform, the analysis dashboard).

## What I did

- Pulled the "Experimentation Platform Analysis" Databricks dashboard def
  (`/api/2.0/lakeview/dashboards/01f13f460c811a41bf5e9cd29c0c648a` on dev profile),
  read all 6 dataset SQLs → analysis methodology.
- Cloned + explored (Explore agents, scratchpad) `experimentation-platform-service`
  (Bitbucket) and `ad-auction-service` (GitHub) for the definition side and the
  consumption side.

## Output

- Rewrote `map/experimentation-platform.md` (was a thin stub) → full stack: domain
  model, config-field/EAV variables, md5 hash contract + SDK-side assignment,
  AAS's 4 live keys, dashboard metrics/stats/sources.
- Corrected `map/aas.md` line 13: `aasRoutingLevel` cut-line is **design-only**,
  not consumed in AAS code.

## Findings worth remembering

- Platform-service = definitions only (MySQL `exp`); **assignment is SDK-side**,
  deterministic `md5(utf8("{requestId}:{targetId}"))` vs `percentExposed`.
- `control_1` is always the analysis reference bucket. Assignment recorded in
  `event_silver.ad_request.amp_targeting_assignment` (array, explode).
- Dashboard p-values = normal-CDF rational approx, sig at p<0.05, ref control_1.
- **State gap:** platform defines `aasRoutingLevelPA/TA` config fields; AAS reads
  only `usePostSearchDeduplication`, `kvssScoreLinearA`, `kvssScoreLinearB`,
  `enableDiscoverTextSearch`. Cut-line routing unimplemented (design doc only).
- Ties to the open unexplained product-ads-through-AAS A/B win (map/aas.md).
