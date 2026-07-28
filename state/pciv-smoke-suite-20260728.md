# AI-1538 candidate roster — tiny-call round-robin smoke (2026-07-28)

*(Derived artifact; laptop → us-east-1, dev account 564079877134, Varun's SSO session.
n=10/model, round-robin order, ~92 calls total, cost ≪ $1. Tiny calls (12–40 in / 2–16 out
tokens) measure round-trip + scheduling floor ONLY — NOT prefill/decode at real prompt sizes.
Real ranking waits on the 3k-token-prompt soak from dev. Raw: scratchpad
`smoke_suite_results.jsonl`, session 3f03f639.)*

| model | surface | n | min | med | p90 | max (ms) |
|---|---|---|---|---|---|---|
| mistral.magistral-small-2509 | runtime | 10 | 221 | 241 | 312 | 312 |
| mistral.ministral-3-14b-instruct | runtime | 10 | 207 | 237 | 354 | 354 |
| qwen.qwen3-next-80b-a3b | runtime | 10 | 171 | 236 | 354 | 354 |
| qwen.qwen3-32b-v1:0 | runtime | 10 | 205 | 252 | 671 | 671 |
| zai.glm-4.7-flash | runtime | 10 | 194 | 251 | 979 | 979 |
| google.gemma-4-31b | mantle | 10 | 259 | 374 | 1105 | 1105 |
| openai.gpt-5.6-luna (reasoning none) | mantle | 10 | 447 | 519 | 775 | 775 |
| deepseek.v3.2 | runtime | 10 | 209 | 351 | 6208 | 6208 |
| qwen.qwen3-vl-235b-a22b | runtime | 9 (1×5xx) | 323 | 759 | 4360 | 4360 |

Observations:
- Everything sits in a ~200–500ms median band at tiny-call size; differences here are floors, not verdicts.
- Tightest tails: magistral-small, ministral-14b, qwen3-next-80b (max ≤354ms over 10 calls each).
- Luna: highest floor (~450ms) but very consistent; the only one whose min ≈ p90.
- Flakiest: qwen3-vl-235b (med 759, one InternalServerException) and deepseek.v3.2 (one 6.2s outlier) — big-model tail risk visible even at n=10.
- Gemma 4 settled vs. this morning's 14s first-touch: today min 259 / med 374 — consistent with brief first-touch queueing on Mantle, not a per-customer warmup.
- Varun's exact asks `qwen.qwen3-235b-a22b-2507` and `deepseek.v3.1` are NOT reachable in this account/region on any surface (runtime catalog absent; Mantle Responses AND Chat Completions both reject) — nearest live versions measured instead.

Mantle mechanics (AWS scaling-throughput-best-practices, fetched 2026-07-28):
- bedrock-mantle is shared multi-tenant serverless. No per-customer deployment, no dedicated
  instance, no customer-owned warmup. Advanced scheduling/work-queueing; requests may briefly
  queue when in-flight load is high (503 = capacity, 429 = quota).
- Quota philosophy differs by endpoint: bedrock-runtime = classic per-account per-model RPM/TPM
  quotas (Service Quotas console). bedrock-mantle non-Claude models = **no per-customer or
  per-model TPM limit** — fair-share scheduling instead; higher initial throughput.
- "Ramp" = available throughput for YOUR account scales with sustained usage. Documented
  procedure: start at target RPM → on 503s halve → hold steady state ~15 min → +50% → repeat.
  Ramp rates not adjustable. Plan 2–3× peak with the account team for launch.
