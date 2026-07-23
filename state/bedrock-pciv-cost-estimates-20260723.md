# Bedrock pricing × online pCIV — cost estimates (2026-07-23)

*(Derived artifact. Source: AWS Price List API, us-east-1, service AmazonBedrock, pulled 2026-07-23 (`bedrock-prices-useast1-20260723.csv`, 875 rows). Regenerate rather than trust after ~a month.)*

## The structural finding

**Prompt-cache-read pricing exists ONLY for Amazon Nova (and Anthropic) on Bedrock. None of the open-source models (Llama 4, Qwen3, DeepSeek, GLM, Kimi, MiniMax, Ministral, gpt-oss) have a cache-read rate** → every request pays full input price on the fixed system prompt. This is the opposite of our DBX/OpenAI reality (93–97% of input at ~10% price). Cost comparisons vs gpt-5-nano MUST account for this.

Bedrock has three on-demand tiers: **standard**, **flex** (~50% off, latency-tolerant — irrelevant for online), **priority** (~1.75×, latency-prioritized — possibly the honest tier for a P99-bound service). Batch tier exists for some (offline-relevant only).

## Cost table (per-request workload assumption: 3,563-tok system prompt [measured, demo v2] + ~60 tok query/context + 250 tok output [ASSUMPTION — verify against golden-set runs])

| model | $/1M in | $/1M out | $ per 1M req (std) | priority | $/mo @60M req |
|---|---|---|---|---|---|
| Nova Micro (95% cached) | 0.035 | 0.14 | **$73** | n/a | $4.4k |
| Nova Lite (95% cached) | 0.06 | 0.24 | **$125** | n/a | $7.5k |
| gpt-oss-20b | 0.07 | 0.30 | $329 | $575 | $19.7k |
| GLM 4.7 Flash | 0.07 | 0.40 | $354 | $619 | $21.2k |
| Ministral 3B | 0.10 | 0.10 | $387 | $658 | $23.2k |
| Ministral 8B | 0.15 | 0.15 | $581 | $1,007 | $34.9k |
| Qwen3 32B | 0.15 | 0.60 | $693 | $1,214 | $41.6k |
| gpt-oss-120b | 0.15 | 0.60 | $693 | $1,214 | $41.6k |
| Ministral 14B | 0.20 | 0.20 | $775 | $1,356 | $46.5k |
| Llama 4 Scout | 0.17 | 0.66 | $781 | n/a | $46.9k |
| Llama 4 Maverick | 0.24 | 0.97 | $1,112 | n/a | $66.7k |
| MiniMax M2.5 | 0.30 | 1.20 | $1,387 | $2,427 | $83.2k |
| Magistral Small / Mistral Large 3 | 0.50 | 1.50 | $2,186 | $3,846 | $131k |
| DeepSeek v3.2 | 0.62 | 1.85 | $2,709 | $4,740 | $163k |
| GLM 4.7 | 0.60 | 2.20 | $2,724 | $4,767 | $163k |
| Kimi K2.5 | 0.60 | 3.00 | $2,924 | $5,117 | $175k |
| GLM 5 | 1.00 | 3.20 | $4,423 | $7,740 | $265k |

(Qwen3 Next 80B A3B is flex/priority-only in the price book — no standard on-demand rate.)

## Calibration & scenarios

- **Empirical comparator**: offline civ on gpt-5-4-nano via DBX = ~$3k/mo at ~85M queries/mo with a **16.4k**-token prompt ⇒ ≈ **$35 per 1M requests**, thanks to caching. Bedrock OSS at a 3.6k prompt is **10–125× that per request**.
- 60M req/mo = ALL ~2M/day Qwant ghost queries hitting extraction — worst case. Realistic reducers: DynamoDB result cache on distinct queries (AI-1540 resizing: **900K distinct** vs 2.5M ⇒ ~0.36× multiplier on cache-miss economics), Flash possibly prompt-only at launch, extraction maybe only on commercial-flagged queries.
- **Prompt size is THE lever on Bedrock**: input dominates every OSS row (≥80% of cost). The online prompt is not yet designed — demo=3,563 tok (L2 GPC), offline=16.4k (L3+IAB); the slimmed pub prompt precedent was ~1.6k. Halving the prompt ≈ halving Bedrock cost. (Conversely on DBX-with-caching, prompt size barely matters for cost.)
- Anthropic current-gen rows are missing/stale in the price API here — Bedrock charges ≈ Anthropic list (Haiku 4.5: $1/$5 per 1M, cache read ~$0.10) ⇒ ~$4.9k/1M req uncached-prompt equivalent… with cache ≈ $1.7k/1M req std. Cross-check on aws.amazon.com/bedrock/pricing before quoting externally.
- All numbers exclude the choice of *where the service runs* (same either way) and assume us-east-1 on-demand.

## CORRECTION (same day, 2026-07-23)

The "structural finding" above is right for the **bedrock-runtime** surface only. Closed-weight **GPT-5.4/5.5/5.6 (Sol/Terra/Luna) ARE on Bedrock** via the separate **Mantle** endpoint (Responses API, Bedrock API key) with **prompt caching at 90% cached-input discount** and OpenAI first-party pricing — none of which appears in the AWS Price List API used here. A cached Luna/Terra column would land near the DBX-nano cost class, not in the uncached-OSS band above. See `state/bedrock-capacity-memo-20260723.md` §6 + `log/pciv-online-service.md` correction entry. Also per that memo: Gemma 4 on Mantle has automatic implicit caching; Llama/Ministral/Mistral remain uncached.
