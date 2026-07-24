# 2026-07-24 — pciv-online build session (continuation of 2026-07-23-pciv-online-context)

Varun's next-steps list (in-session): new domain on llm-eval-service for online pciv (check branches first) · exact copy of offline civ initially · wire langchain↔bedrock + test · identify online-serving optimizations · use the pciv prompt from pciv-demo-service `dev-taxonomy-full-l2`.

## Done

- 2026-07-24 — Branch sweep: **no prior online-pciv work** on any origin branch of llm-evaluator-service (newest related: `feat-civ-eval-luna-gemini`, AI-1474). Built fresh off origin/main in a **git worktree** (`~/Documents/llm-evaluator-service-online-pciv`, branch `feat-online-pciv`) — the shared clone has another session's untracked eval CSVs on its checked-out branch; worktree avoids trampling it.
- 2026-07-24 — **`domains/pciv_online` built** (commit a7949d5): copy of civ_extraction at `/v1/intent/pciv` + conversation-shaped pCIV schema (type/topic/targets[]) + evals 101/102/103 (IDs ≥101 reserved — Dynamo cache key has no domain component) + pciv prompt from demo repo c139471 (delimiter protocol → JSON-only; content otherwise verbatim, Yaarit owns) + `bedrock` provider (ChatBedrockConverse) + cache_control-vs-Converse fix in both invokers + `scripts/pciv_online_smoke.py` + langchain-aws dep (requirements recompiled, pinned py3.13). **476 tests pass (74 new); app boots with both /intent/civ and /intent/pciv routes.**
- 2026-07-24 — Optimization candidates for AI-1542 logged (`log/pciv-online-service.md` 2026-07-24): prompt size (banked, 5×), client instance reuse (per-request TLS handshake today), reasoning_effort=minimal knob, tight max_tokens (Bedrock admission control), 2s timeout/no-retry, cache semantics per surface shape, in-network measurement.
- 2026-07-24 — Nest updated: checklist Phase B (`tasks/pciv-online-deploy.md`), log entry, playbook §Service internals + endpoint list, REVIEW.md push-approval entry.

## Blocked / pending Varun

- **Bedrock live smoke** (1 call, pennies — covered by "wire up + test"): needs `aws sso login --profile dev` (expired). Command staged in checklist Phase B. Also verifies the guessed `mistral.ministral-3-8b-instruct` model id.
- **Branch push** to Bitbucket: REVIEW.md 2026-07-24 entry (Bitbucket behavioral-read-only).
- Carry-overs from 7/23: Phase A app-name decision, AI-1538 description paste, integration-ticket drafts, ~$50 accuracy-run budget.

## Disposed

- 2026-07-24 — ✅ **Branch pushed by Varun** (`feat-online-pciv` → origin, commits a7949d5 + 50049ed; Bitbucket offered PR link `pull-requests/new?source=feat-online-pciv`). REVIEW.md entry cleared. CI builds a Docker tag `<ver>.<build#>-feat-online-pciv` on this push — usable as the image tag for the Phase A dev deployment.
- 2026-07-24 (cont.) — **App name decided by Varun: `online-pciv-service`**. Phase A artifacts built + validated locally: cd-deploy-configs `AI-1538-online-pciv` (overlay, 089e5a77a) + cd-releases `AI-1538-online-pciv` (Application yaml). Bedrock test-budget memo drafted (`review/2026-07-24-bedrock-test-budget.txt` — $50 = my ceiling estimate, honest math $25–40 full matrix). Pushes + memo pending Varun in REVIEW.md.
