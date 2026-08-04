# Finalists through the service at the real pciv prompt — 2026-08-04 ~13:00 EDT

First end-to-end numbers for AI-1542 at the ~3.3k `pciv_extraction.txt` prompt. DBX run
`357322702087907` on ML-TEAM-CLUSTER → `https://dev-online-pciv-service.ric1.admarketplace.net/v1/intent/pciv`,
image `1.0.297-feat-online-pciv` (eval 104 existing at all proves the rollout), evals interleaved,
n=50 measured + 3 warmups each, bypassCache, the same 15 FR queries as the 7/31 provider-floor run.
e2e = caller wall time from the DBX cluster (in-VPC); proc = server-reported processingMs.
Post-INFRA-3474 fix, so pods reach Mantle over PrivateLink.

| eval | model | e2e p50 | e2e p95 | e2e p99 | proc p50 | ok | cache hit | 7/31 provider floor p50 |
|---|---|---|---|---|---|---|---|---|
| 106 | Qwen3-Next-80B | 473ms | 1,020ms | 16.5s* | 458ms | 49/50 | 0% | 399ms |
| 107 | Ministral 14B | 657ms | 982ms | 1,168ms | 640ms | 50/50 | 72% | 486ms |
| 104 | Gemma 4 31B | 707ms | 5,294ms | 6,963ms | 690ms | 50/50 | 10% | 615ms |
| 105 | GPT-5.6 Luna | 5,702ms | 6,349ms | 7,085ms | 5,686ms | 50/50 | 94% | 741ms (**stale, see below**) |

\* the one Qwen error: Mantle-side HTTP 500 after 45.5s; plus one clean 29.7s outlier. Gemma also
had one 60s-timeout warmup — both models carry provider-side tail risk. Ministral's tail is clean.

## Luna's 741ms floor is dead: Mantle currently adds a flat ~5.5s to every Luna request

Bisected laptop-side after the run (all with reasoning effort none, reasoning_tokens 0, warm
persistent connection):
- service langchain path, 3.3k prompt: 5.5–6.5s
- raw httpx, langchain's exact payload: ~6.0s
- raw httpx, the 7/31 probe's exact payload: ~5.5s (same call that measured 741ms on 7/31)
- raw httpx, **8-token input, 6 tokens out: ~5.5s**

Flat per-request penalty, independent of prompt size, cache state, payload shape, transport, SDK.
Provider-side change between 7/31 15:12 EDT and 8/4 13:00 EDT (7/28 tiny smoke was 574ms).
Consequences:
- Luna is disqualified for a 2s budget while this holds. Re-probe before concluding anything
  permanent — could be Mantle ramp/scheduling ("standard tier only" has no latency guarantee).
- This morning's "client-reuse fix delivered no saving" comparison (eval 610, 18k, 5,828 vs
  Friday's 5,965) is contaminated: if the flat penalty was already active this morning, both the
  fix's saving and the 18k inference are hidden inside a Luna-specific constant. The fix's
  in-cluster proof now comes from the OTHER models instead (below).

## The client-reuse fix is proven in-cluster

Service e2e minus provider floor at the same prompt+queries: Qwen +74ms, Ministral +171ms,
Gemma +92ms (p50 vs p50; includes FastAPI, Dynamo bypass check, parse/validate, GPC resolution,
plus floor-vs-service network differences). The 1.0.294-era per-request token mint (~545ms laptop,
unknown in-cluster) is gone; e2e−proc is 15–18ms.

## Cache facts (Mantle, implicit)

- Ministral 14B now reports cached input tokens (72% hit, ~4,160 of ~4,183) — the 7/23 memo's
  "nothing for Ministral" is stale.
- Gemma 4 cached only 10% despite byte-identical prefixes; Qwen 0%; Luna 94%.
- tokens_out means: Qwen 14, Gemma 17, Luna 40, Ministral 52.

Raw JSONL: `/tmp/pciv_dev_latency-1785862523.jsonl` on ML-TEAM-CLUSTER (ephemeral). Full
per-call lines in the DBX run output (run id above).
