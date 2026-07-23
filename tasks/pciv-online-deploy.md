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

- [ ] ⚠️ **Flag (decision needed)**: Varun said "stick with a gpt nano model for early testing" — **gpt-5-nano is NOT on Bedrock** (verified 2026-07-23; OpenAI on Bedrock = gpt-oss open-weights only). Recommendation: functional testing of the new deployment via the existing DBX path with `gpt-5-4-nano` (zero new code), and wire the Bedrock provider with **`openai.gpt-oss-20b`** (nearest OpenAI-family nano-analogue, $0.07/$0.30 per 1M, 10k-RPM-class quotas) or `mistral.ministral-3b`. Final model comes from AI-1540 eval later — provider code is model-agnostic.
- [ ] **Service code (dev branch on llm-evaluator-service)**: add `bedrock` provider alongside databricks in `llm/utils/providers.py` + `llm/config/models.json` entries (`model_provider: "bedrock"`, region us-east-1, model ids incl. `us.` prefix rule for INFERENCE_PROFILE models). Langchain `ChatBedrockConverse` (langchain-aws) — coexists with DBX path (Dhaval 7/14). Respect existing per-domain endpoint mapping shape.
- [ ] **Local test**: run service locally with SSO creds (`aws sso login --profile dev`), civ eval config pointed at the Bedrock model, `scripts/civ_api_accuracy.py` smoke (few rows) — NOTE: Bedrock invocations cost money; Varun pre-approved ~$50 exploration budget? **Not yet — get explicit go before real runs** (his 7/23 instruction).
- [ ] **k8s AWS auth (infra dependency)**: pod needs bedrock:InvokeModel + bedrock:Converse* on us-east-1 — IRSA role bound to the app's service account (dev EKS is in us-east-1, account for dev EKS TBD — confirm whether cluster account = 564079877134 where Bedrock access is verified). Infra ticket.
- [ ] New eval config in civ domain (or new domain later, per Yaarit's format work): `max_group_size: 1`, tight timeout (start 5s?), `bypassCache` semantics reviewed for online use.

## Phase C — Bedrock rate limits (research + infra ask)

Mechanism (researched 2026-07-23, free API): **AWS Service Quotas, per-account × per-region × per-model**, separate **requests/min** and **tokens/min** quotas; `Adjustable: true` ⇒ raise via `aws service-quotas request-service-quota-increase`; `false` ⇒ AWS support case. Current dev-account (564079877134) us-east-1 defaults, pulled 7/23:
- Ministral 3B/8B: **10,000 RPM / 100M TPM** — covers 200 QPS (12k RPM is close; TPM fine: 200 QPS × 3.6k tok ≈ 43M TPM)
- Qwen3-32B: 10,000 RPM class
- Llama 4 Maverick/Scout (cross-region): **800 RPM / 600k TPM** — way under need (600k TPM ≈ 2.7 QPS at 3.6k tok!); TPM adjustable=true, RPM adjustable=false ⇒ support case
- Nova Micro: 4M TPM on-demand / 8M cross-region
- [ ] Re-pull quotas for the finalist model once AI-1540 picks; compute need = target QPS × 60 × tokens/req (use measured prompt tokens per `token-counting` skill)
- [ ] Which AWS account do stage/prod EKS pods run in? Quotas are per-account — the increase must land in the serving account, not the laptop-dev one.
- [ ] Draft the infra/AWS ask (numbers + justification) → REVIEW.md (precedent: DBX rate-limit ask 2026-07-23)
- [ ] Check `priority` tier quotas separately if we go latency-prioritized (separate price + possibly separate limits)

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
