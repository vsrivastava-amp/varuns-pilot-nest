# online-pciv-service prod release — infra source of truth

Created 2026-08-05. Owner: Varun. Scope: **only the things infra must do** to get
`online-pciv-service` servable in prod. Our-side work (overlays, release tickets, code) is listed at
the bottom only to bound the scope. Update statuses in place; this file is the tracker.

Context for prioritization (2026-08-05, Varun ↔ Saksham): ship with one model, switch later.
Leaning Qwen3-Next-80B or Gemma 4 31B. **Both are served via Bedrock Mantle, so every Mantle item
below is on the critical path regardless of which one wins.** Qwen also exists on the plain
bedrock-runtime surface as a fallback path; Gemma is Mantle-only.

## The proven dev pattern (what prod mirrors)

Dev works end-to-end as of 2026-08-04: SA `wi-online-pciv-service` (IRSA), akeyless paths
`online-pciv-service/dev/ric1/databricks/*`, Bedrock+Mantle IAM (INFRA-3474/3475), Mantle
PrivateLink endpoint + cluster DNS forward (INFRA-3474 follow-ups), image via cd-deploy-configs
master overlay. Each prod ask below is "same as dev, in the prod account/cluster".

## Infra asks

### 0. Name the prod account + cluster (BLOCKS EVERYTHING BELOW)
- [~] **ASKED 2026-08-05 ~12:20 EDT — Varun DM'd Antonio.** Awaiting answer; asks 1–3 fire on it
  (conversational ticket texts prepared 2026-08-05, in chat).
- Original question: Which AWS account and EKS cluster/datacenter do prod pods run in? Bedrock quotas, IAM, and
  the PrivateLink endpoint are all per-account and per-VPC, so no other ask can be filed precisely
  until this is answered. (Dev = 564079877134 / eks-dev-use1-01 / ric1. Open since the July quota
  research.) Also confirm the prod cluster region is us-east-1 — Mantle is in-region us-east-1 only,
  and all latency numbers assume no cross-region hop.

### 1. Service account + Bedrock IAM in prod
- [ ] Workload-identity SA `wi-online-pciv-service` in the prod cluster, IAM policy same as dev
  (INFRA-3474): `bedrock:InvokeModel`, `bedrock:Converse`, `bedrock:ConverseStream`,
  `bedrock-mantle:CallWithBearerToken`, `bedrock-mantle:CreateInference`, us-east-1.
  Lesson from dev: the two bedrock-mantle actions are independently required; missing
  `CreateInference` produces HTTP 401 only at inference time.
- [ ] Confirm model access in the prod account. In dev, Mantle needed no per-model access grant
  (bearer token off the account identity just worked), but that is per-account — one smoke call
  confirms it. Runtime-surface models follow the INFRA-2973 lesson: IAM alone is not enough if the
  account lacks the model-access agreement.

### 2. Secrets (akeyless) in prod
- [ ] Paths `online-pciv-service/prod/<dc>/databricks/*` (DATABRICKS_ACCOUNT_ID,
  DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET), values populated — mirror of what INFRA-3475 did
  for dev. Open input: which Databricks workspace prod should point at (dev overlay uses host
  dbc-562d27e2-d74d; stage precedent is dbc-303276b5-9802; prod host unconfirmed).
- [ ] imagePullSecret: dev reuses global `docker-registry-access-token-ampdockercirw`; confirm the
  same secret exists/applies in the prod cluster.
- Lesson from dev: "path created" is not "values populated" — validation is one eval call through
  the service, not an akeyless listing.

### 3. Mantle PrivateLink + DNS in the prod VPC
- [ ] Interface endpoint `com.amazonaws.us-east-1.bedrock-mantle` in the prod VPC, Private DNS
  enabled, HTTPS allowed from the pod/node path, endpoint policy allowing the Mantle actions.
- [ ] The DNS story that goes with it: `PrivateDnsEnabled: true` only creates the private zone. In
  dev, workloads kept resolving the public IPs until the cluster's CoreDNS forward was pointed at
  the (recreated) inbound resolver. Prod needs the equivalent wiring for its own VPC/DNS setup,
  plus a from-a-worker verification (`tools/pciv/dns_resolver_probe.py`).
- [ ] AZ coverage check: AWS offers this endpoint service in us-east-1a/1b/1d. Dev only covered
  1a/1b and also runs nodes in 1c (which permanently cross AZs). For prod, put ENIs in every AZ the
  service offers that overlaps prod subnets, and know which node AZs will cross.

### 4. Rate limits / capacity in the prod account (KICK OFF EARLY — no SLA on approvals)
- [ ] Quota increases for the chosen model, filed in the prod account. Mantle-cohort models do not
  appear in the Service Quotas console; increases go through AWS Support (account team engaged —
  Varun's 2026-08-05 email thread with Darcis/Sushant is the live channel).
- [ ] Numbers to put in the ask once QPS target and model are final: need = QPS x 60 x
  tokens-per-request (current shape ~4k in / ~15-50 out), with the 2-3x headroom framing from the
  July capacity memo (`state/bedrock-capacity-memo-20260723.md`). At 200 QPS and today's prompt
  that is roughly 12k RPM / ~50M input TPM before headroom.
- [ ] Treat unapproved capacity as unavailable (memo rule). If the ask stalls, the launch gate
  stalls with it.

### 5. Prod ingress / network path for callers
- [ ] How does SSP reach the service in prod — in-cluster service DNS, internal LB, or public NLB?
  Dev uses ingress `dev-online-pciv-service.ric1.admarketplace.net` (ingressClassName `llm-eval`);
  the demo-service precedent for public exposure was INFRA-3421 (pub-nlb). The SSP integration
  owner decides the required path; infra provisions it. Timeout wiring on the SSP side (AS-13402
  pattern) is not infra's, but the LB idle-timeout settings are.

### 6. DynamoDB cache access in prod
- [ ] The service reads/writes the civ_label DynamoDB cache. Confirm the prod table exists (or
  which table prod should use) and that the prod SA's role carries the same DynamoDB permissions
  dev has. (2026-08-05: cache keys now carry the domain via `service._CACHE_DOMAIN` after the
  eval-config restructure, so the old cross-domain eval-id collision worry is retired; env
  separation across a shared table is still worth confirming.)

## Stage (decide, then maybe mirror)

Varun's own note (2026-08-04): stage "seems somewhat optional for doing this very quickly."
If stage happens, the asks are 1+2 mirrored to stage — already drafted and parked in
`review/2026-07-29-ai1538-stage-infra-jira.txt` (SA + secrets; endpoint/DNS for the stage VPC would
need adding). If stage is skipped, delete that draft and the stage-rollout package.

## Not infra — ours (scope boundary, not a checklist)

Prod overlay on the cd-deploy-configs `prod` branch via RELEASE-ticket flow with peer-approved PR;
cd-releases Application yaml for prod; image promotion; Datadog monitors/SLOs on the new service
tag (the tail-by-hour monitoring the Gemma jitter demands); model/eval config choices; client-side
throttling per the capacity memo; Saksham/SSP integration contract.

## Open questions that gate the asks

| question | gates | owner |
|---|---|---|
| Prod AWS account + cluster + DC | every ask above | infra (one Slack question) |
| Final model (Qwen vs Gemma) | ask 4 numbers only | Varun/Dhaval (AI-1540) |
| Target QPS for launch | ask 4 numbers | Varun/Saksham/business |
| Prod Databricks workspace | ask 2 values | Varun |
| SSP -> service network path | ask 5 | SSP owner + Varun |
| Stage: yes/no | whether stage asks fire | Varun |

Sequencing: ask 0 is one question and unblocks filing 1+2+3 immediately (they are
decision-free mirrors of dev). Ask 4 needs the QPS + model answers but should be drafted now and
filed the day they land. Asks 5-6 ride their owners' decisions.
