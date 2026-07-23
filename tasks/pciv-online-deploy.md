# Online pCIV deployment checklist (AI-1538) — multi-session tracker

Started 2026-07-23. Owner: Varun (agent-assisted). Requirements are volatile — re-read `log/pciv-online-service.md` (esp. latest dated entries) before each session. Update checkboxes + add dated notes in place; this file is the cross-session state.

**Division of labor (2026-07-23, Varun↔Saksham):** Yaarit = input/output format + prompt optimization (orthogonal, don't block on it). Varun = get a new llm-eval-service deployment live in base form: dev now, stage/prod soon; Bedrock wired with *a* model (not the best model); rate limits worked with infra.

## Phase A — new dev deployment ("seems live")

Mechanism (verified 2026-07-23, see `playbooks/k8s-cd.md`): ArgoCD; `cd-deploy-configs` repo, **branch `master` = dev+stage overlays, branch `prod` = prod**; auto-sync is ON (`selfHeal: true`) — a merge to master deploys immediately. Application registration = yaml in `cd-releases` `dev/ric1/` (precedent: llm-evaluator-service's Application yamls live on unmerged branches `AI-1371`/`AI-1371-prod` — infra presumably applied them; confirm process with infra).

- [ ] **Decide app identity**: separate app name `pciv-online-service` (recommended: own Datadog service tag per Dhaval's 7/8 ask, own HPA/limits; same Docker image `admarketplace/llm-evaluator-service`) vs a variant overlay `llm-evaluator-service/dev-ric1-pciv-online`. Varun to confirm name.
- [ ] **cd-deploy-configs (on `master`, via feature branch + PR)**: create `apps/<app>/base/` + `apps/<app>/dev-ric1/` by copying `apps/llm-evaluator-service/{base,dev-ric1}` (source of copy: `git show origin/master:apps/llm-evaluator-service/dev-ric1/<file>`). Edit: app name/labels, `tags.datadoghq.com/service`, ingress hostname `dev-<app>.ric1.admarketplace.net` (ingressClassName `llm-eval`), config.conf (`DEPLOYMENT_ENVIRONMENT=dev`, DBX host dbc-562d27e2-d74d for now), image tag = current dev tag (1.0.266-* era; check latest).
- [ ] **Secrets/identity (infra dependency)**: deployment.yaml references `akeyless:/llm-evaluator-service/dev/ric1/databricks/*` + `serviceAccountName: wi-llm-evaluator-service` + imagePullSecret `docker-registry-access-token-ampdockercirw`. New app name ⇒ either reuse existing akeyless paths/SA (fastest; confirm allowed) or infra ticket for new paths + workload-identity SA (precedent: DBR-6025 created akeyless secret for pciv-demo prod).
- [ ] **cd-releases**: add `dev/ric1/dev-<app>.yaml` Application (copy `origin/AI-1371:dev/ric1/dev-llm-evaluator-service.yaml`; namespace `npe-argocd`, destination dev EKS `810C5935…eks.amazonaws.com`, path `apps/<app>/dev-ric1`, targetRevision HEAD). Confirm with infra who applies it (branch-only precedent suggests infra runs kubectl apply / argo app create).
- [ ] **Smoke**: `curl https://dev-<app>.ric1.admarketplace.net/health` (VPN), then `POST /v1/intent/civ` with evalId 2, 1 query. Datadog: service visible under new name.
- [ ] Guardrail note: prepare branches + PRs; **merges to master auto-deploy** — Varun merges (agent PRs go through REVIEW.md first).

## Phase B — Bedrock provider with *a* model

- [x] ~~gpt-5-nano not on Bedrock~~ **CORRECTED 2026-07-23 (Varun + online research)**: no nano/mini variants, but closed-weight **GPT-5.4 / 5.5 / 5.6 Sol-Terra-Luna ARE on Bedrock** via the **Bedrock Mantle** endpoint (`https://bedrock-mantle.us-east-1.api.aws/openai/v1`, OpenAI **Responses API only** — no Converse/InvokeModel/ChatCompletions; Bedrock API key auth; in-region us-east-1; **prompt caching w/ 90% cached-input discount**; OpenAI first-party pricing; standard tier only). My catalog sweep missed them because `list-foundation-models` + the price book only cover the bedrock-runtime surface — three gating layers: account grants / region / **API surface**.
- [ ] **Early-testing model recommendation (re-tempered 2026-07-23, Varun)**: Luna is the nano-*role* of the 5.6 family but **NOT nano-priced — $1/$6 per 1M vs gpt-5.4-nano's $0.20/$1.25 (5× both sides, OpenAI list)**; may be slower too (unmeasured). So: **early functional testing = DBX path with gpt-5-4-nano (evalId 2) — zero new code, cheapest**. Bedrock wiring is model-agnostic; Luna (evalId 6 on DBX already) is merely the cheapest *closed-weight OpenAI option on Bedrock/Mantle*, and whether in-network Bedrock-Luna beats out-of-network DBX-nano on latency at 5× cost is an AI-1540/1542 measurement, not an assumption. Converse-path alternates: `gpt-oss-20b` / `ministral-3b`.
- [ ] **Service code (dev branch on llm-evaluator-service)** — likely TWO provider paths: (a) `bedrock-mantle` = OpenAI-SDK-compatible client at the Mantle base_url (Responses API — langchain-openai `use_responses_api=True` or raw openai client; nearly identical to the existing DBX-gateway OpenAI-compat path) for GPT-5.x; (b) `bedrock` = `ChatBedrockConverse` (langchain-aws, SigV4) for OSS/Anthropic/Mistral/Nova. models.json entries with `us.` prefix rule for INFERENCE_PROFILE models. Both coexist with DBX path.
- [ ] **Mantle auth**: provision a **Bedrock API key** (new mechanism, distinct from SigV4/IRSA) — figure out creation + akeyless storage; check whether short-term keys derive from SigV4 creds (would let IRSA still be the root identity).
- [ ] **Local test**: run service locally with SSO creds (`aws sso login --profile dev`), civ eval config pointed at the Bedrock model, `scripts/civ_api_accuracy.py` smoke (few rows) — NOTE: Bedrock invocations cost money; Varun pre-approved ~$50 exploration budget? **Not yet — get explicit go before real runs** (his 7/23 instruction).
- [ ] **k8s AWS auth (infra dependency)**: pod needs bedrock:InvokeModel + bedrock:Converse* on us-east-1 — IRSA role bound to the app's service account (dev EKS is in us-east-1, account for dev EKS TBD — confirm whether cluster account = 564079877134 where Bedrock access is verified). Infra ticket.
- [ ] New eval config in civ domain (or new domain later, per Yaarit's format work): `max_group_size: 1`, tight timeout (start 5s?), `bypassCache` semantics reviewed for online use.

## Phase C — Bedrock rate limits (research + infra ask)

Mechanism (researched 2026-07-23, free API): **AWS Service Quotas, per-account × per-region × per-model**, separate **requests/min** and **tokens/min** quotas; `Adjustable: true` ⇒ raise via `aws service-quotas request-service-quota-increase`; `false` ⇒ AWS support case. Current dev-account (564079877134) us-east-1 defaults, pulled 7/23:
- Ministral 3B/8B: **10,000 RPM / 100M TPM** — covers 200 QPS (12k RPM is close; TPM fine: 200 QPS × 3.6k tok ≈ 43M TPM)
- Qwen3-32B: 10,000 RPM class
- Llama 4 Maverick/Scout (cross-region): **800 RPM / 600k TPM** — way under need (600k TPM ≈ 2.7 QPS at 3.6k tok!); TPM adjustable=true, RPM adjustable=false ⇒ support case
- Nova Micro: 4M TPM on-demand / 8M cross-region
**Deep-dive memo received 2026-07-23** (online research agent; verbatim: `state/bedrock-capacity-memo-20260723.md`). Headlines: 200 QPS needs 12k RPM / ~46M TPM, AWS wants 2–3× headroom forecast (24–36k RPM); **no published turnaround SLA or ceiling — submit asks immediately, involve the AWS account team, treat unapproved capacity as unavailable**; priority/standard/flex **share one quota pool** (priority = scheduling + "up to 25%" output-TPS, no P99 guarantee); Provisioned Throughput doesn't cover our OSS candidates (dead end for now; Reserved tier is the newer separate-capacity option); cross-region = capacity/overflow, not latency (can't pin destination — keep primary path single-region); quotas refresh on 60s cycles and **reserve `input + max_tokens` at admission ⇒ set tight max_tokens** (~400, not 4096/10k); 429=quota vs 503=capacity semantics; **caching correction: GPT-5.6 (Mantle) + Gemma 4 implicit also cached**, still nothing for Llama/Ministral/Mistral. Launch gates: quota/latency/throttling/fallback/cost — fold into AI-1542 acceptance criteria.

- [x] Rate-limit mechanism research (memo above closes it; Mantle quota increases go via AWS Support, not Service Quotas workflow)
- [ ] Re-pull quotas for the finalist model once AI-1540 picks; compute need = target QPS × 60 × tokens/req (use measured prompt tokens per `token-counting` skill); include the 2–3× headroom framing + memo's "strong request" field list in the ask
- [ ] Which AWS account do stage/prod EKS pods run in? Quotas are per-account — the increase must land in the serving account, not the laptop-dev one.
- [ ] **Quota gate check for Ministral at 200 QPS: 10k RPM default < 12k needed** — even the friendliest OSS quota needs an increase before launch-capable; Llama 4 Maverick (800 RPM) is out of the question without account-team action.
- [ ] Draft the infra/AWS ask (numbers + justification per memo's field list) → REVIEW.md (precedent: DBX rate-limit ask 2026-07-23). Kick off EARLY — no SLA on approvals.
- [ ] Client-side throttling design for the service: request+token limiters smoothed to RPM/60 & TPM/60, bounded queue, one deadline-aware retry max, shed-don't-amplify (memo §5 list → service requirements)

## Phase D — stage/prod (later)

- [ ] stage overlay on master (`stage-ric1`, DBX host 8321), prod overlay on `prod` branch via release PR (pattern: RELEASE-#### tickets, e.g. 586f23a96)
- [ ] prod akeyless paths + SA (infra), prod ingress via pub-nlb? (check — demo used INFRA-3421)
- [ ] AS-13402-style timeout wiring for the SSP→service hop once the integration ticket exists

## Session log

- 2026-07-23 — File created; mechanism research done (branches, argo, quota model, precedent yamls). Nothing deployed yet. Next concrete step: Varun confirms app name + whether to reuse akeyless/SA, then cut the cd-deploy-configs branch.

## Handoff brief — Bedrock rate-limit deep-dive (paste into an online Claude session)

> Hi! Context: adMarketplace is building a low-latency LLM extraction service (~100–200 QPS sustained, ~3.6k input + ~250 output tokens/request, P99 < 2s) on AWS Bedrock us-east-1, launching late Aug 2026. We've already pulled current Service Quotas (per-account/per-region/per-model, separate requests-per-min and tokens-per-min; e.g. Ministral 3B/8B = 10k RPM / 100M TPM; Llama 4 Maverick cross-region = 800 RPM / 600k TPM, TPM adjustable but RPM not). Please research from current AWS docs/announcements:
> 1. How Bedrock on-demand quota increases actually work in 2026: service-quotas API vs support case, typical turnaround, what justification AWS wants, hard ceilings people have hit.
> 2. Priority vs standard vs flex service tiers: do they have separate quotas? How is priority latency guaranteed?
> 3. Provisioned Throughput: current pricing model/commitment terms, when it beats on-demand for ~200 QPS sustained, which models support it (esp. open-source ones), latency benefits.
> 4. Cross-region inference profiles: how quotas apply (per profile vs per underlying region), latency implications of cross-region routing for a us-east-1 caller (we measured ~370–900ms round-trips for tiny calls).
> 5. Burst behavior/throttling semantics: token-bucket details, 429 handling best practice, and whether quota is enforced per-second or per-minute (matters for spiky ad traffic).
> 6. Any prompt-caching roadmap for open-source models on Bedrock (currently Nova/Anthropic only) — cost and prefill-latency implications.
> Deliverable: short memo with sources/dates; we'll fold it into our repo. Numbers we quote get re-verified against the quotas API before any infra ask.

- 2026-07-23 — Brief prepared; local mechanism research done (see Phase C). Online-session memo → fold results back into Phase C and `playbooks/llm-eval-system.md` §Bedrock.
