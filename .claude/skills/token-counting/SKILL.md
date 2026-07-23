---
name: token-counting
description: Get token counts and prompt sizes RIGHT — measured, never guessed. Use whenever you are about to state, log, or compare a token count, prompt size, or token delta, or derive a cost/latency number from one — and ALWAYS before such a number leaves the nest (Slack draft, Jira ticket, client-facing doc, REVIEW.md). Companion to model-selection, which consumes these counts in its cost formula.
---

# Token counting: measure, don't guess

A guessed token count that reaches a person becomes a commitment. Incident that
created this skill (2026-07-23, pCIV demo): chars/4 estimated a prompt change
at **+800 tokens (~3.1k total)** and that number was told to a stakeholder;
the tokenizer said **+1,142 (3,563 total)** — the delta was 30% low, because
the added text was an ID-heavy category list, not prose. Never again.

## Hierarchy of evidence — use the highest rung you can reach

1. **Provider-reported usage** (ground truth): `usage.prompt_tokens` /
   `input_tokens` from one real API call with the exact assembled input, or
   gateway telemetry (`system.ai_gateway.usage`) for live workloads. One
   nano-model call costs a fraction of a cent — there is almost never a reason
   to skip this rung for anything outward-facing.
2. **Local tokenizer on the exact assembled text**:
   ```bash
   uv run --with tiktoken python -c "
   import tiktoken
   enc = tiktoken.get_encoding('o200k_base')   # gpt-4o/gpt-5 families; cl100k_base for gpt-4/3.5 era
   print(len(enc.encode(open('FILE').read())))"
   ```
   Anthropic models: the `count_tokens` API endpoint is free and exact (see
   claude-api skill). Post-cutoff model families: verify which encoding before
   trusting tiktoken.
3. **chars/4** — last resort, and it must travel with its label. Say
   "unverified chars/4 estimate, ±30%+" every time. It is calibrated on
   English prose (~4 chars/tok); structured text (ID lists, JSON, code,
   URLs, non-English) runs 2.5–3.5 chars/tok and the heuristic reads LOW.

## Rules

- **Count the assembled input, not the fragment.** System prompts are usually
  concatenations (the pCIV demo joins three files + a formatted delimiter);
  the API adds per-message overhead (~4 tok/message). Count what the provider
  actually receives — reproduce the exact assembly (e.g. mirror the service's
  own prompt-building code) or capture usage from a real call.
- **Never estimate a delta directly.** Measure old, measure new, subtract.
  Relative error amplifies on differences — today's 13% total-size error was a
  30% delta error.
- **Counts don't transfer across model families.** o200k vs Anthropic's
  tokenizer can differ 10–20%+ on the same text, worst on structured content.
  Re-measure per family; a "3.5k prompt" is a per-tokenizer fact.
- **Outward-facing numbers must be rung 1 or 2.** If a number is about to go
  into a Slack message, ticket, or client doc and it came from chars/4, stop
  and measure first. If you cannot measure yet (text doesn't exist), send a
  labeled range, plus what will pin it down and when.
- **A guessed number already went out and measurement disagrees?** Correct it
  proactively in the same channel, plainly, with the measured value — the
  stale number is calcifying into someone's spreadsheet right now.
- **Log measured counts with their context**: tokenizer/model, what was
  assembled, date. An undated or method-less count is a future guess.

## Cheap measurement patterns in this nest

- `tools/pciv/latency_harness.py` — streams one real request and records
  `prompt_tokens` (+ `cached_tokens`, so you also see cache behavior, which
  model-selection §3 needs). Pattern generalizes: any service's prompt can be
  assembled and fired once at a nano-tier model for exact usage.
- Databricks: `system.ai_gateway.usage` has per-request `input_tokens` /
  `token_details.cache_read_input_tokens` for anything already running
  (lags ~20–30 min; workspace IDs in model-selection).
- Cost math downstream of the count: use model-selection §3 — cached vs
  uncached input rates change the answer ~10× on our pipelines.
