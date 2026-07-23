---
name: model-selection
description: Choose an LLM for a workload on the Databricks gateway or AWS Bedrock, estimate its real cost (prompt-caching-aware), compare recency/capability, and keep the nest knowledge base current on available models. Use when picking or comparing models, pricing a batch/pipeline job, answering "what's the newest model we can use", or when a model decision lands on a Jira ticket.
---

# Model selection, pricing, and roster upkeep

adMarketplace serves LLMs through the **Databricks model gateway** (AI Gateway / Foundation Model APIs). Company context lives in `playbooks/llm-eval-system.md` ("Model gateway / registry" + "Cost / usage telemetry" sections) — read it first; update it last.

## 1. Enumerate what's actually available

Never assume from memory — new frontier models land on the gateway within days of release, usually past your training cutoff.

```bash
databricks api get "/api/2.0/serving-endpoints" -p dbc-562d27e2-d74d \
  | jq -r '.endpoints[] | select(.config.served_entities[0].external_model // .task // "" | . == "FOUNDATION_MODEL_API" or . == "") | [.name, .creation_timestamp] | @tsv'
```

- `FOUNDATION_MODEL_API` endpoints named `databricks-<model>` are the pay-per-token catalog; sort by `creation_timestamp` for recency.
- The eval service calls separate **named wrapper endpoints** (`ai-*`, `civ-*`, `ares-*`) mapped in `llm-evaluator-service`'s `llm/config/models.json`. A model on the catalog is NOT automatically usable by the service — it needs a models.json entry + eval config + deploy.
- Dev roster may lead prod. Verify prod (workspace `5702410742425796`) before promising a model; laptop CLI has no prod access — check via the prod UI or ask Varun.

## 1b. AWS Bedrock path (second gateway — in-network candidate for online/low-latency serving)

Chosen direction for the online pCIV service (Jul 10 kickoff: "Bedrock over Databricks" — in-network, same us-east region as serving). Laptop has AWS CLI profiles (`dev`, `sandbox`, `stage`, `ML_Role`, `prod`) but they're **SSO-based and expire**: probe with `aws sts get-caller-identity --profile dev`; if expired, ask Varun to run `aws sso login --profile <profile>` (auth is human-gated — never automate SSO). Status 2026-07-23: all profiles expired, roster sweep pending first login.

Once live:

```bash
aws bedrock list-foundation-models --profile dev --region us-east-1 \
  | jq -r '.modelSummaries[] | [.modelId, .providerName, (.inferenceTypesSupported|join(",")), .modelLifecycle.status] | @tsv'
# smoke-test access + rough latency (3-token call, pennies):
aws bedrock-runtime converse --profile dev --region us-east-1 --model-id "$MODEL" \
  --messages '[{"role":"user","content":[{"text":"hi"}]}]' --inference-config '{"maxTokens":3}' \
  | jq '{ok:(.output!=null), latencyMs:.metrics.latencyMs, usage}'
```

- `inferenceTypesSupported=INFERENCE_PROFILE` ⇒ call as `us.<modelId>` (cross-region profile), bare modelId 400s. The laptop's aws-cli 2.16.3 lacks `bedrock list-inference-profiles` — the `us.` prefix convention works without it.
- Verified 2026-07-23: dev account (564079877134) has broad model-access grants — Meta/Mistral/Anthropic/Qwen all invocable, no INFRA ask needed. Roster snapshot: `playbooks/llm-eval-system.md` §Bedrock.
- ⚠️ **`list-foundation-models` covers only the bedrock-runtime surface.** Closed-weight OpenAI frontier models (GPT-5.4/5.5/5.6 Sol/Terra/Luna) are served via the separate **Bedrock Mantle** endpoint (OpenAI Responses API, Bedrock API key auth, 90% cached-input discount, OpenAI list pricing, standard tier only) and appear in neither the catalog call nor the AmazonBedrock price book. Always also check https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards-openai.html before declaring a model absent. Three gating layers: account grants / region / API surface.
- Pricing: AWS Bedrock pricing page per provider; cached-input pricing exists for some providers (verify per model). Same cost formula as §3.
- Integration: the eval service is langchain-based; Bedrock coexists with the DBX path (`ChatBedrockConverse`) — "equally easy… can coexist in the same code base" (Dhaval, 7/14). A Bedrock model still needs a models.json-style entry + eval config in the service.
- Open question to resolve on first sweep: are OpenAI gpt-5-family models available on Bedrock at all (AI-1535 flagged "needs investigation"), or is Bedrock effectively Anthropic/Meta/Mistral/Amazon-family — which would couple the Bedrock-vs-DBX choice to the model choice.

## 2. Get current pricing — never from memory

- Databricks charges **≈ official provider list prices** (OpenAI/Anthropic/Google). DBX's own pricing pages lag — go to the provider's site.
- Use WebSearch for post-cutoff models ("<model> API pricing per million tokens <current month/year>"). Cross-check two sources; capture **input, output, AND cached-input** rates. For Anthropic models, the claude-api skill has authoritative current pricing.
- Typical cached-input discount: OpenAI 90% off (auto prefix caching ≥1024 tokens), Anthropic ~90% off on reads (requires cache_control markers — the eval service already sends them), Gemini implicit caching (verify current discount).
- Note intro/promo pricing windows and their end dates.

## 3. Cost a workload — caching changes everything

Estimates that ignore prompt caching run ~10× high on our pipelines (huge shared system prompts, e.g. the 16.4k-token civ prompt resent per call).

**Empirical inputs beat assumptions.** Pull real telemetry from `system.ai_gateway.usage` (per-request `input_tokens`, `output_tokens`, `token_details.cache_read_input_tokens`, `latency_ms`, `status_code`). Workspace IDs: dev `4731856320192987`, stage `1602623610650144`, prod `5702410742425796`. Observed on civ workloads: **93–97% of input tokens are cache reads**. Note the table lags ~20–30 min.

Formula per run:

```
calls        = items / group_size            (service chunks by eval-config max_group_size)
input_tokens = calls × tokens_per_call       (system prompt dominates)
input_cost   = input_tokens × (cache_share × cached_rate + (1-cache_share) × input_rate)
output_cost  = items × out_tokens_per_item × output_rate     (output is NEVER cached — it usually dominates)
```

Because input is ~95% cached, **output price drives the model ranking**. Give ranges when output-per-item is unmeasured; a small pilot (10–20k items) yields exact `tokensUsed` and latency — prefer that before quoting numbers on a ticket.

**Rate limits gate feasibility, not just cost**: most wrapper endpoints are throttled near zero (as of 2026-07 only the gpt-5-mini and gpt-5-4-nano wrappers have real capacity). Check historical successful-requests-per-minute in the telemetry before promising a runtime; increases go through Databricks (ask template precedent: REVIEW.md 2026-07-23).

## 4. Compare capability honestly

- Sources: artificialanalysis.ai (intelligence index + model-vs-model pages), docsbot.ai/models/compare, provider announcements. WebSearch "<model A> vs <model B> benchmark".
- Caveats to state: index scores are often measured at high reasoning effort (inflates latency vs our short calls); benchmark deltas on general tasks are a **proxy** for task-specific accuracy — a golden-set or pilot run is the real test; a newer model's cheapest tier may be *less* capable than an older flagship (check the head-to-head, don't assume by date).
- Rough current tiering heuristic: within a family, price tier ≈ capability tier; across families, check the index.

## 5. Fold findings back into the nest (always)

- Update `playbooks/llm-eval-system.md` → "Model gateway / registry": refresh the dated roster snapshot (newest endpoints + dates), pricing notes worth keeping (with as-of dates), rate-limit reality.
- Facts are perishable: **date every snapshot**; re-derive rather than trust entries older than ~a month.
- Commit surgically and push (nest conventions in CLAUDE.md).

## Output shape for decisions

When the result feeds a ticket/decision, produce a compact table: model · released · list price in/out (+cached) · est. cost per run (range + assumptions) · gateway availability (dev/prod) · rate-limit status · capability note. Lead with a recommendation and the single biggest caveat.
