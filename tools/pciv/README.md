# pCIV latency A/B harness

Measures the latency impact of the GPC taxonomy/prompt expansion
(group DM C0BJPQHFFGC escalation; scope in `runs/2026-07-22-pciv-taxonomy-gap.md`).
Calls the provider's chat-completions API directly with the demo's assembled
system prompt — zero changes to `pciv-demo-service`.

## What it measures, per streamed request

- **ttft_ms** — time to first content token (this is where the +~800 prompt tokens land)
- **reply_done_ms** — time until `<<<PCIV_DELIM>>>` appears (user-visible reply complete)
- **total_ms** — full stream incl. pCIV JSON
- **cached_tokens / prompt_tokens** — true cache state of the sample, from usage

## Run

```sh
cd ~/pilots-nest/tools/pciv

# Noise floor (A vs A, current prompts) — do this first, once:
uv run --env-file ~/Documents/pciv-demo-service/.env python latency_harness.py \
  --arm-a ~/Documents/pciv-demo-service/prompts \
  --queries queries.txt --n 25 --mode both \
  --out ../../state/pciv-latency-noise-floor-$(date +%Y%m%d).jsonl

# Real A/B once the new prompts exist in a second checkout:
uv run --env-file ~/Documents/pciv-demo-service/.env python latency_harness.py \
  --arm-a ~/Documents/pciv-demo-service/prompts \
  --arm-b /path/to/new-checkout/prompts \
  --queries queries.txt --n 50 --mode both \
  --out ../../state/pciv-latency-ab-$(date +%Y%m%d).jsonl
```

Models: `--model gpt-5.4-nano` (default) / `gpt-5.4-mini`; add
`--provider openrouter --model mistralai/mistral-small-2603` for the Mistral arm
(different caching semantics — report separately).

## Design notes / caveats

- **Arms interleave** (A,B,A,B…) so provider-side drift cancels.
- **Warm mode** primes each arm's prefix once (unmeasured), then measures
  back-to-back. Expect `cached_tokens` ≈ prompt size rounded down to a
  128-token increment. OpenAI implicit-cache floor is 1024 tokens — both old
  (~2.2k) and new (~3k) prompts clear it.
- **Cold mode** prepends a per-request nonce line to the system prompt to bust
  the prefix cache (identical ~10-token overhead in both arms). Fast, but it
  measures cold *prefill*, not the exact production bytes. Expect
  `cached_tokens == 0`.
- Samples whose cache state contradicts the mode are mislabeled — filter on
  `cached_tokens` before comparing arms.
- Matches service params: temperature 0.3, max_tokens 10000, and main.py's
  exact `PROMPT_WITH_PCIV` assembly (chat + output_protocol + extraction).
- Results are JSONL, append-mode, one row per sample → drop in `state/`
  (disposable, date-stamped). Summary (p50/p95 per arm×mode) prints at the end.
- **Acceptance frame (proposed, Varun to ratify):** cold TTFT delta < ~100ms
  p50 and no p95 regression beyond the A-vs-A noise floor ⇒ "no material
  latency impact". Worse ⇒ revisit prompt format (grouped-by-L1 may compress).
- Second-order effect: expanded disambiguation rules may lengthen the *reply*
  segment — watch `reply_done_ms` and `completion_tokens_mean` deltas, not
  just TTFT.
