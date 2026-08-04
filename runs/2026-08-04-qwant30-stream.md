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
