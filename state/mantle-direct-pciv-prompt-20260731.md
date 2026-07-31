# Direct Mantle latency at the real pCIV prompt — 2026-07-31

Raw rows: `state/mantle-direct-pciv-prompt-20260731.jsonl` (108 calls, 96 measured, 0 failures).

**What this is.** Laptop → `bedrock-mantle.us-east-1.api.aws`, no service in the path (no
FastAPI, no LangChain, no DynamoDB). System prompt = `domains/pciv_online/prompts/pciv_extraction.txt`
(11,266 B), user message = one French Qwant query, matching `_format_message` at
`max_group_size: 1`. Model params mirror `llm/config/models.json` exactly (max_tokens 2000,
Luna `reasoning.effort=none` + Responses API, others Chat Completions). Every model was
measured two ways, 12 measured samples each, 3 warmups, models interleaved. Queries: random
sample of `review/qwant_fr_queries_sample_20260724.csv`, ≥2 words, seed 1538. The two ways are
the `connection` field in the JSONL, values `persistent` and `fresh`.

**Upper bound, not a benchmark.** Laptop→us-east-1 adds WAN the EKS pod won't pay, so real
in-network provider latency is at or below these numbers.

## Persistent connection — one reused connection, one bearer token (the provider floor)

| Model | p50 | p95 | p99 | min | input tok | output tok | cache hit |
|---|---|---|---|---|---|---|---|
| Qwen3-Next-80B | **399 ms** | 471 | 490 | 315 | 3,998 | 8 | 0% |
| Ministral 3 14B | **486 ms** | 620 | 666 | 179 | 4,183 | 49 | 17% |
| Gemma 4 31B | **615 ms** | 1,024 | 1,119 | 410 | 4,064 | 14 | 17% |
| GPT-5.6 Luna | **741 ms** | 1,150 | 1,154 | 519 | 3,334 | 39 | 75% |

## New connection per request — plus a fresh bearer token each time (what the service does today)

`e2e` excludes token generation; `total` adds the measured `provide_token()` cost.

| Model | e2e p50 | e2e p95 | tokengen p50 | **total p50** | **total p95** | **total p99** |
|---|---|---|---|---|---|---|
| Ministral 3 14B | 475 | 843 | 544 | **973** | 1,410 | 1,448 |
| Qwen3-Next-80B | 403 | 995 | 577 | **1,014** | 1,596 | 1,672 |
| Gemma 4 31B | 587 | 1,025 | 546 | **1,116** | 1,669 | 1,789 |
| GPT-5.6 Luna | 857 | 2,280 | 555 | **1,500** | 2,835 | 3,293 |

## Findings

1. **Luna is not slow. The 18k prompt was slow.** At the real ~3.3k pCIV prompt Luna is
   p50 741 ms / p99 1,154 ms provider-side. The 7/31 DBX diagnostic's p50 5.965 s came from
   `civ_extraction.txt` at 18,183 tokens. Prompt size, not the model, produced that number.
   Eval 610 is retired as a latency benchmark.
2. **`reasoning_effort: none` is live on the wire.** Every Luna response reported
   `reasoning_tokens: 0`. The report's "verify what is transmitted" branch is closed —
   config, provider code, and provider response all agree. Reasoning burn is not our problem.
3. **Opening a new connection and minting a new token per request is a real tax, and it lands
   on the tail.** `provide_token()` costs **~545 ms p50** on its own and the service calls it
   on every request, because `providers.get_chat_model` is not cached and
   `invoker_unstructured.py:176` builds a fresh model per call. Beyond that fixed cost, not
   reusing the connection roughly doubles Luna's p95 (1,150 → 2,280 ms). A persistent
   connection plus a cached token is worth **~550 ms at p50 and ~1.7 s at p95** on Luna.
4. **Prompt caching works well only for Luna.** Luna cached 3,332 of 3,334 input tokens,
   75–100% hit rate. Gemma 4's implicit cache hit 0–17% and Qwen reported no cached tokens at
   all. Ministral was erratic (0–50%). Do not model open-weight cache savings as reliable.
4b. **But at 3.3k tokens the cache buys almost no latency.** Splitting Luna's
   persistent-connection runs by cache state: hits p50 710 ms (n=9, range 519–1,145), misses
   p50 772 ms (n=3, range
   618–1,156) — ~60 ms apart with near-total overlap. n=3 on the miss side makes the exact
   delta soft, not the direction. Corroborated by the other three finalists, which barely
   cached at all (Qwen 0/24, Gemma 2/24, Ministral 8/24) and are still faster than Luna.
   At 3.3k, prefill is cheap enough that caching is a **cost** optimization, not a latency
   one. The quoted 1,500 ms Luna total is fully cached (12/12 hits) and would move ~60 ms if
   the cache were cold. It decomposes as ~545 ms token generation + ~850 ms provider round
   trip, and that round trip is mostly WAN plus generating ~40 output tokens.
   ⚠️ This holds at 3.3k. If Yaarit's AI-Chat contract pushes input to 8–10k with the LLM
   response included, prefill re-enters the picture and caching matters again — and Luna is
   the only finalist whose cache can be relied on.
5. **Output is small across the board** (8–49 tokens), so `max_tokens: 2000` is not costing
   latency. It still over-reserves against Mantle admission control — the capacity memo's
   tight-`max_tokens` point stands for throughput, not for latency.

## Caveats before anyone quotes these

- Laptop origin. In-network EKS should be faster; that is the next measurement.
- The inputs are bare French **search terms**, not AI-Chat payloads. Real AI-Chat carries the
  LLM response, so production input will exceed 3.3–4.2k tokens and these numbers will move.
- n=12 per cell. Enough for a ballpark, not for a defensible p99.
- Provider only. Service overhead (FastAPI, DynamoDB lookup, parse/validate) is not included.
