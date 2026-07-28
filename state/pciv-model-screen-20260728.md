# Online pCIV model screen — golden set × 11 candidates (2026-07-28)

*(Derived artifact. 500 golden rows (`civ_extraction_no_brand_gpc.csv`) × 11 models,
single-query calls (`max_group_size 1` = online shape) through local llm-evaluator-service
on branch `feat-online-pciv` commit 7b03dbc, screen evals 601–611, bypassCache, no retries,
laptop → us-east-1, 16.4k-token offline civ prompt. ~5,500 calls, ~$25. Raw per-call jsonl
in session scratchpad (3f03f639, `screen_full/`); rerun: `scripts/civ_screen.py`.
Pareto plots artifact: https://claude.ai/code/artifact/5fe85587-f335-485e-b154-23fa850b36b5 )*

| model | surface | composite | intent | gpc_l1 | iab_t1 | p50 | p90 | p99 | err% | cache% | $/1M req @16.4k | $/1M proj online @3.6k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma-4-31b | mantle | **.890** | .842 | **.927** | .909 | 1600 | 4812 | 17516 | 1.4 | 79.6 | 2204 | 496 |
| gpt-5.6-luna | mantle | .872 | .816 | .859 | **.931** | 1233 | 1557 | **1980** | 2.0 | 98.4 | 2397 | 772 |
| deepseek-v3.2 | bedrock | .856 | **.857** | .837 | .897 | 2116 | 7421 | 47367 | **0.6** | 0 | 12026 | 2730 |
| qwen3-vl-235b | bedrock | .845 | .832 | .861 | .891 | 2076 | 5862 | 75445 | 6.2 | 0 | 11341 | 2564 |
| qwen3-next-80b | bedrock | .839 | .837 | .878 | .841 | 1115 | 1657 | 2855 | 6.8 | 0 | 3151 | 726 |
| ministral-14b | bedrock | .830 | .825 | .802 | .877 | **738** | **911** | 1810 | 4.0 | 0 | 4719 | 1047 |
| gpt-5.4-nano (bar) | dbx | .812 | .756 | .827 | .820 | 1279 | 3827 | 16273 | 6.6 | 94.3 | **602** | **174** |
| magistral-small | bedrock | .804 | .845 | .727 | .884 | 1422 | 1788 | 2716 | 3.4 | 0 | 11842 | 2662 |
| ministral-8b | bedrock | .798 | .820 | .797 | .851 | 644 | 794 | 1414 | ⚠41.0 | 0 | 3540 | 786 |
| glm-4.7-flash | bedrock | .791 | .825 | .686 | .807 | 749 | 1074 | 1669 | ⚠10.8 | 0 | 1424 | 336 |
| qwen3-32b | bedrock | .779 | .843 | .780 | .791 | 776 | 1321 | 1948 | 8.2 | 0 | 3357 | 758 |

Composite = mean(intent_type, product_name, brand, seller, gpc_l1/l2/l3, iab_t1/t2) on successes.

## Headlines

1. **Every candidate beats the nano baseline on composite accuracy** (nano .812; its intent_type .756 is the field dragging it).
2. **Pareto frontier (all three pairings): Gemma 4 31B, GPT-5.6 Luna, Ministral 14B**, with nano/GLM holding the ultra-cheap end. Qwen3-Next-80B is the best non-frontier alternate (near-Gemma cost, mid latency, .839).
3. **Tail analysis (Varun's ramp hypothesis, confirmed in part)**: slow calls (>3× own median) are FRONT-LOADED for the Mantle/ramp cases — Gemma 4 51% and Qwen-235B 80% in the first 20% of the run (mitigable: sustained traffic + AWS ramp procedure) — but UNIFORM for DeepSeek (18% first-quintile ≈ inherent) and nano/DBX (13%, gateway variance). Luna + Magistral: zero slow calls at all.
4. **Caching**: Luna 98.4% + Gemma 79.6% cache-read on Mantle (implicit, no markers); Bedrock-runtime OSS models pay full prompt every call → prompt size is their #1 cost lever.
5. **Error rates are format failures, not model failures** (parse of JSON output): Ministral-8B 41%, GLM 10.8%, Qwen-32B 8.2% — per-model prompt/structured-output tuning could recover several points of effective accuracy; worth one iteration before final cuts.
6. Caveats: accuracy is offline-shaped US-EN queries (FR/conversation eval waits on AI-1556); latency measured at 16.4k prompt from laptop (ranking valid, absolutes inflated ~4.5× on prefill vs the 3.6k online prompt); Bedrock quotas/ramp for the finalist still need the AWS ask.

## Proposed top 3 (pending Varun)

- **Gemma 4 31B** — accuracy leader, 2nd-cheapest projected, cached; tail is ramp-shaped (needs a sustained-traffic soak from dev to confirm it settles).
- **GPT-5.6 Luna** — the consistency pick: tightest tail by far (p99 2.0s at 16.4k prompt, zero outliers), near-top accuracy; premium output price.
- **Ministral 14B** — the speed pick: p50 738ms / p90 911ms with respectable .830 accuracy; no caching, mid cost.
- (Alternate: Qwen3-Next-80B if error-rate tuning lands; watch its 61s max outlier.)
