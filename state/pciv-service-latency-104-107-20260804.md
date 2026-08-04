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

Follow-up probes (~14:05 EDT, all 8-token inputs): **the penalty covers the whole GPT-5.6 family** —
Luna 5.4–7.3s, **Terra 6.1s**, **Sol >30s (timed out)**. `store: false` no effect (5.5s; one earlier
store=false call hit a 65s ReadTimeout), `reasoning effort low` no effect (5.4s). Responses report
`service_tier: "default"`, `status: "completed"`; headers carry only request ids — no processing-time
or queue signals. Gemma 4 on the same `openai/v1` root but Chat Completions surface is unaffected, so
this is the closed-weight OpenAI family (or its Responses serving path), not the endpoint host.
Nothing on our side can fix it; it is AWS-conversation material and a re-probe-over-time question.

Round 3 (~15:15–15:30 EDT, Varun challenged "degraded" and then "user error"): the stall is a
**constant post-generation finalization wait, and user error is excluded**.
- Streaming timeline (tiny prompt): `response.created` 245ms, all output text delivered by 479ms,
  then silence until `response.completed` at 5,493ms. The model generates at Friday speed.
- The unchanged 7/31 floor script rerun (same laptop, same everything): Qwen 462 / Ministral 617 /
  Gemma 778 / **Luna 5,576ms with a 63ms spread over 8 calls** — a constant, not jitter.
- stdlib `http.client` (non-httpx stack): server sends ZERO bytes (no status line) until 5,575ms,
  Content-Length set. Nothing client-side can cause that.
- Parameter ablation: no reasoning / no temperature / no max_output_tokens / minimal `{model,input}`
  — all ~5.5–6.4s. No parameter left to blame.
- CoreDNS/PrivateLink hypothesis (Varun): refuted three ways — laptop repro never touches cluster
  DNS; all four models share the hostname/route and three are fast; service Luna was already ~5.8s
  Friday and this morning, before the 10:40 CoreDNS change.
- Residual unknown: everything ran in dev account 564079877134 — account-scoped slow pool vs global
  cannot be distinguished without a second account.
- **Workaround MEASURED (~15:35 EDT): streamed Luna at the real 3.3k prompt delivers full text in
  411–578ms** (first event 151–191ms); the finalization gap is ~5.0s at BOTH tiny and real sizes
  (n=3 each). Streamed Luna would sit between Qwen (473ms) and Ministral (657ms) through-service
  p50s. Service adoption = a streaming Responses invoker that stops at `output_text.done`;
  usage/cache metadata rides `completed`, so collect it async or drop it. Only worth building if
  AI-1540 picks Luna.
- **STALL ISOLATED TO MANTLE (~15:50 EDT, Varun's OpenAI key):** Luna on api.openai.com with the same
  payloads: non-streamed 1.3–2.4s (tiny AND real 3.3k, cache hits included), streamed text_done
  1.2–2.6s with a **105–134ms** finalization gap. OpenAI first-party finalizes normally; only
  Mantle's layer holds `completed` for ~5s. Fully attributable now: same model, same API, same
  payload, 100ms vs 5,000ms. Bonus finding: Mantle's streamed token delivery (~0.5s to full text)
  is FASTER than OpenAI direct from the laptop, so Mantle-streamed stays the best measured Luna
  configuration; the stall is the only defect. Also: the OpenAI key makes gpt-5.4-nano (the
  original preferred model, absent from Bedrock) directly testable — untested as of this entry.

## Quantiles split by cache hit vs miss (e2e ms; includes the errored calls, so 106 max=45.5s is the 500)

| eval | group | n | p50 | p95 | p99 | min | max |
|---|---|---|---|---|---|---|---|
| 104 Gemma | hit | 5 | 434 | 1,391 | 1,552 | 285 | 1,592 |
| 104 Gemma | miss | 45 | 725 | 5,388 | 7,067 | 410 | 7,980 |
| 105 Luna | hit | 47 | 5,702 | 6,315 | 7,119 | 5,514 | 7,641 |
| 105 Luna | miss | 3 | 5,633 | 6,201 | 6,252 | 5,576 | 6,264 |
| 106 Qwen | miss | 50 | 474 | 1,640 | 37,806 | 317 | 45,548 |
| 107 Ministral | hit | 36 | 639 | 841 | 940 | 151 | 971 |
| 107 Ministral | miss | 14 | 739 | 1,133 | 1,248 | 246 | 1,277 |

Readings: Gemma's ugly tail is entirely uncached prefill (hits are fast and tight, but only a 10%
hit rate); Luna's penalty is identical for hits and misses (more proof it is not cache-related);
Ministral's cache benefit is ~100ms at p50 and ~300ms at p99 with a clean tail either way; Qwen
never caches and its tail is the two provider-side events, not a distribution.
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

## From-laptop 18k `civ_extraction.txt` probes (~16:00–16:40 EDT, Varun-requested)

Persistent connection, non-streamed, 2 warmups + 8 measured, same 15 FR queries (ms):

| model | endpoint | p50 | p95 | p99 | cache hits |
|---|---|---|---|---|---|
| Qwen3-Next-80B | Mantle | 804 | 1,054 | 1,123 | 0/8 |
| Ministral 14B | Mantle | 857 | 3,769 | 4,748 | 5/8 |
| Luna | OpenAI direct | 1,735 | 6,868 | 8,129 | 8/8 |
| Gemma 4 31B | Mantle | 4,297 | 9,764 | 11,592 | 1/8 |
| Luna | Mantle | 5,684 | 5,709 | 5,710 | 4/8 |

- OpenAI-Luna row measured ~40min after the Mantle rows, fully cache-warm (18,171/18,184 cached
  every call) and still ranged 1,304–8,444ms. Mantle-Luna's 89ms total spread is the stall being
  the floor. OpenAI key = nest `.env` (see playbook "OpenAI direct" gateway section).
- Ministral p95/p99 = its 3 cache misses paying ~23.5k prefill; hits run 600–900ms.
- Gemma 18k p50 ~4.2s is prefill arithmetic (dense 31B vs Qwen's sparse A3B; matches 7/30's 4.52s);
  the one cache hit came back in 1,662ms.
- **Gemma CORRECTION (Varun caught it): the tail spikes are NOT prompt-size arithmetic and are new
  vs Friday.** Same 3.3k prompt: Friday p95 1,024 / worst ~1.8s; today 5/16 calls hit 1.8–4.9s
  (adjacent calls 6× apart, all cache misses ~4k tokens). Same phenomenon as the 7/28 screen
  (14s cold, 398ms→2.7s swings) — intermittent Mantle-side serving jitter that Friday's clean n=12
  window missed. Distinct from Luna's constant stall. Day's scorecard vs Friday: Qwen/Ministral
  stable, Luna stall constant, Gemma jitter returned — two independent provider-side defects.

Raw JSONL: `/tmp/pciv_dev_latency-1785862523.jsonl` on ML-TEAM-CLUSTER (ephemeral). Full
per-call lines in the DBX run output (run id above). 18k rows:
scratchpad `mantle_civ18k_20260804.jsonl` (session-ephemeral).
