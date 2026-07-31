# Run — 2026-07-31 pCIV e2e latency testing

Session slug `pciv-latency-e2e`. Started 14:38 EDT. Varun brought in a prior session's
diagnosis-and-resolution report on pCIV e2e latency and asked me to get acquainted, then
time-boxed a laptop-direct upper-bound measurement.

## Acquaint pass

2026-07-31 — Read `playbooks/llm-eval-system.md` §Bedrock, `log/pciv-online-service.md`,
`tasks/pciv-online-deploy.md`, `state/digest-2026-07-31.md`, `tools/pciv/dev_eval_latency.py`,
and the service code in worktree `~/Documents/llm-evaluator-service-online-pciv`
(`feat-online-pciv`, HEAD `4c0cfe9`).
2026-07-31 — Credential probe per guardrail 5: `databricks auth describe -p dbc-562d27e2-d74d`
authenticated as Varun; `aws sts get-caller-identity --profile dev` returned the PowerUser SSO
role in 564079877134. Both live, so no auth gate this session.

## Assessment of the report (given to Varun in-chat)

2026-07-31 — Agreed with the core: eval 610 measures the wrong prompt, prompt caching is not
the lever, instrumentation plus persistent-client reuse is the right long-term ask.
2026-07-31 — Three corrections raised. (1) **Scope moved the same morning**: Dhaval 10:35 put
Flash out of scope, leaving France AI-Chat only, and Maxime's real budget via Norbert is 2 s
for chat — end to end including the France↔US round trip and ad selection, so the report's
"e2e p99 < 2 s" pass criterion is too generous for our hop. (2) **Two diagnostic branches were
already answerable by reading code, without the layer matrix** — see below. (3) The report's
§1–§3 all require a service change → push → CI → cd-deploy-configs PR → merge, which cannot
land against a same-day deadline; the direct-provider probe can.
2026-07-31 — Also flagged: the ">95% cache-hit rate" pass criterion conflates the DynamoDB
result cache with Mantle prompt caching, and "retire eval 610" is step zero rather than a
contingent §4 conclusion.

## Code reading that closed two of the report's branches

2026-07-31 — **Fresh client per request is confirmed, not hypothesis.**
`llm/utils/providers.py` `lru_cache` is on `_get_oauth_client` only, `maxsize=1`;
`get_chat_model` itself is uncached and `invoker_unstructured.py:176` /
`invoker_structured.py:209` call it per request via `asyncio.to_thread`. On the Mantle path
`_get_mantle_chat_model` calls `provide_token()` on **every** construction.
2026-07-31 — **`reasoning_effort` is correctly configured.** `models.json`
`gpt-5-6-luna-mantle` carries `"reasoning_effort": "none"` and `providers.py:121` forwards it
as `reasoning: {"effort": ...}` on the Responses path. What remained unverified was the wire
and the response — the probe settled both.

## Direct-Mantle probe (Varun approved the spend in-chat)

2026-07-31 — Script: scratchpad `mantle_direct_probe.py` (session 4ecb7d74). Raw HTTP to
`bedrock-mantle.us-east-1.api.aws`, no service, no LangChain. System prompt =
`pciv_extraction.txt` (11,266 B), user message = one French query per call, mirroring
`_format_message` at `max_group_size: 1`. Model params copied from `models.json`. Two arms:
persistent client + reused token, versus fresh client + fresh token per request (the service's
current behaviour). 4 finalists interleaved, 3 warmups + 12 measured per model per arm.
2026-07-31 — 108 calls, 96 measured, **zero failures**. Results and full caveats in
`state/mantle-direct-pciv-prompt-20260731.{md,jsonl}`.
2026-07-31 — Headline: **Luna is not slow — the 18k prompt was.** At the real ~3.3k pCIV
prompt Luna is p50 741 ms / p99 1,154 ms provider-side, against the 5.965 s p50 the 7/31 DBX
run produced on `civ_extraction.txt` at 18,183 tokens. Provider floor ranking: Qwen3-Next-80B
399 ms, Ministral 3 14B 486 ms, Gemma 4 31B 615 ms, Luna 741 ms (all p50).
2026-07-31 — Luna reported `reasoning_tokens: 0` on every call. Reasoning burn is ruled out.
2026-07-31 — **`provide_token()` costs ~545 ms p50 by itself**, paid per request today. Losing
connection reuse on top of that roughly doubles Luna's p95 (1,150 → 2,280 ms). Persistent
client + cached token is worth ~550 ms at p50 and ~1.7 s at p95 on Luna. This is the single
biggest service-side lever and it is a code fix, not a provider problem.
2026-07-31 — Prompt caching is reliable only on Luna (3,332 of 3,334 tokens cached, 75–100%
hit rate). Gemma 4 implicit cache hit 0–17%, Qwen reported none, Ministral 0–50%. Do not model
open-weight cache savings as dependable.

## Gotchas found

2026-07-31 — `aws_bedrock_token_generator.provide_token()` raises
`ValueError: Region must be provided or set via the AWS_REGION environment variable` unless
`AWS_REGION` is set. `_get_mantle_chat_model` does an `os.environ.setdefault` before calling
it; any standalone script must do the same.
2026-07-31 — Qwen3-Next-80B returns very short replies on these queries (8–13 output tokens,
25 chars) because it answers `{"commercial": false}` for non-commercial French search terms.
Legitimate, but it makes its latency advantage partly an output-length artifact — do not
compare raw latency across models without also comparing output tokens.

## Next

2026-07-31 — Varun's call: DBX path or a temporary EC2/pod in the dev VPC for the in-network
number. Either way the service-side run still needs the finalists wired to
`pciv_extraction.txt` in `pciv_online` (currently only 102 nano / 103 ministral-8b; the 6xx
finalists all sit in `civ_extraction` at 18k).
