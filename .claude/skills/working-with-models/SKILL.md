---
name: working-with-models
description: Hands-on engineering practice for building with LLMs — measuring tokens for real, prompt-caching discipline, provider API gotchas, validating structured output, and changing prompts safely. Use when editing a prompt, integrating or debugging a model API call, measuring prompt size / cost / latency, or shipping any change to what a model consumes or produces. Companion to model-selection (which model, what it costs); this skill is how to work correctly with the one you picked.
---

# Working with models

## Token counts: measured, never estimated

A token count is a measurement, not an impression. Two acceptable sources:

1. **Usage from a real API call** with the exact assembled input —
   `usage.prompt_tokens` (OpenAI-style) / `input_tokens` (Anthropic). A
   nano-tier call costs a fraction of a cent; this is the default.
2. **The model family's tokenizer** on the assembled text:
   ```bash
   uv run --with tiktoken python -c "
   import tiktoken
   enc = tiktoken.get_encoding('o200k_base')   # gpt-4o/gpt-5 families; cl100k_base for gpt-4/3.5 era
   print(len(enc.encode(open('FILE').read())))"
   ```
   Anthropic's `count_tokens` endpoint is free and exact (claude-api skill).

Practice:
- **Count what the provider receives** — the fully assembled input (all
  concatenated prompt files, formatted delimiters, ~4 tok/message wrapper
  overhead), never a fragment of it. Reproduce the service's own prompt
  assembly or capture usage from a live call.
- **Deltas by subtraction only**: measure old, measure new, subtract. Small
  relative errors on totals become large errors on differences.
- **Counts are per-tokenizer facts.** The same text differs 10–20%+ across
  model families, most on structured content (ID lists, JSON, code).
  Re-measure per family; record tokenizer/model and date with any saved count.

## Prompt caching discipline

- Caching keys on an exact byte prefix: keep dynamic content (timestamps,
  user data, nonces) out of the system prompt; append variability at the end.
- Verify empirically, never assume: OpenAI reports
  `prompt_tokens_details.cached_tokens` (implicit caching, ≥1024-token
  prefix, 128-token increments); Anthropic needs `cache_control` markers and
  reports `cache_read_input_tokens`.
- Batch-test hit rates don't predict production: sparse interactive traffic
  falls outside cache TTL (~5–10 min) — measure both warm and cold paths.

## Provider API gotchas

- Newer OpenAI models reject `max_tokens` — send `max_completion_tokens`.
  Temperature support also varies by model. SDKs (langchain, official
  clients) paper over both; raw HTTP callers must handle them.
- Streaming: pass `stream_options: {"include_usage": true}`; usage arrives in
  the final chunk. Always capture `finish_reason` — `length` vs `stop`
  distinguishes truncation from completion, which no amount of output-parsing
  can.

## Structured output: validate as the consumer

- Parse model output exactly as the downstream code does — same delimiter
  handling, same JSON extraction — not with a friendlier parser of your own.
- Validate emitted IDs/enums against the same source-of-truth files the
  service loads at runtime.
- Track failure modes as **rates over a fixed input set** (missing delimiter,
  parse failure, invalid ID), not anecdotes; a few percent of silent failure
  is invisible in spot checks and very visible in production.

## Changing a prompt safely

- Baseline before touching anything: fixed query set, measured failure rates
  and latency percentiles on the current prompt.
- A/B old-vs-new on the same queries, arms interleaved to cancel provider
  drift; judge deltas against the measured noise floor (run same-vs-same
  first), not against intuition.
- Machine-generate what can be generated (lists, taxonomies) from a single
  source of truth, with a sync check runnable in CI; hand-edit only the
  editorial parts (rules, examples) — and keep the two in one commit.
