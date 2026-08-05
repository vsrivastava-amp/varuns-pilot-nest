# 2026-08-04 — qwant30-stream: first look at live 3.0 ghost traffic

2026-08-04 Trigger: Dhaval standup followup (screenshot) + Saksham's ask (relayed in-chat by Varun; Slack MCP not handshaken this session, Slack-in-Chrome behind Okta — stopped per guardrail #3): "look at 3.0 queries from Qwant across different geos and placements. Understand anecdotally what kind of data we are getting in SSP and what that means for us."

2026-08-04 What was done (all read-only, dev profile → shared metastore, warehouse 634ea83b5df3a556):
- Confirmed the 3.0 ghost stream is queryable in `prod_amplify.event_silver.ad_request` (`version='3.0'`, `intent` variant populated on 100% of rows, fresh to within minutes of query time).
- Mapped numeric `pub_placement_id` → placement slugs via `prod_amplify.ssp.placement.id` (join key is `id`, not `media_placement_id`).
- Profiled field presence, commerciality, source types, snippet coverage per placement × geo (aggregates in `log/pciv-online-service.md` 2026-08-04 entry).
- Stratified sample of 90 payloads → `~/Documents/qwant_30_intent_samples_20260804.csv` (kept out of git, real user queries; delivered to Varun in-chat).

2026-08-04 Open items filed/flagged:
- No `user` object in any logged payload (doc promised geo/locale/tz/device). Sent-but-not-logged vs not-sent is unresolved — checking ssp-engine (Bitbucket, read-only) would settle it. Peripheral to this task; noted in log, not yet in needs-human.
- `source.summary` is a templated title list, not an LLM flash answer — the contested "flash answer text on Flash" field is effectively still absent.

2026-08-04 Disposition: findings reported in-chat; no outbound drafts created this session (Saksham reply, if wanted, to be drafted on Varun's direction).

2026-08-04 Follow-up (Varun-directed): one-level breakdown CSV over ALL version-3.0 rows (8.23M, 2026-07-06 → 2026-08-04 19:19 UTC) → `~/Documents/qwant_30_onelevel_breakdowns_20260706-20260804.csv` (18 dims, tall format). Notables: real ghost ramp began 7/30 (a day before the 7/31 plan; trickle since 7/6); `amp_ad_request_status_id` uniformly 1200; brand 1337 / publisher 1276 ≈ 100%. More CSVs to follow on Varun's spec (two-level cuts explicitly deferred).

2026-08-05 Follow-up 2 (Varun-directed): random 5000-row query sample, publisher 1276, full 3.0 window → `~/Documents/qwant_30_query_sample_5000_20260805.csv` (same dim columns as the breakdowns CSV + `amp_ad_request_id` for join-back; prompts truncated at 500 chars; untracked — real user queries). Sample mix tracks population (81.7% Qwant Flash). NEW FACT: `usr_search_term` is NULL on every 3.0 row — the query text lives only in `intent:prompt` (the 7/24 FR sample worked because it drew on 2.x traffic). Any query analysis on 3.0 must read the variant.

2026-08-05 Follow-up 3 (Varun-directed): per-surface edition of the one-level breakdowns → `~/Documents/qwant_30_onelevel_breakdowns_by_surface_20260706-20260804.csv` (surface × 17 dims, tall, pct within surface×dimension; geo_region top-25 per surface; placement dim dropped as identical to surface). Window capped at the original file's max ts for reconciliation — totals differ by 16 rows of 8.23M (late ingestion between runs). Per-surface reads: chat surfaces are 100% has_response, ~50/50 web_search vs no-source; Detailed Flash (serp+commerciality on chat placements) is only ~1.1% of Qwant chat-placement volume over the window.
