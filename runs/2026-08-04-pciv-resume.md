# 2026-08-04 — pciv-online resume: DNS fix landed upstream, evals 104–107 built

Session slug: `pciv-resume`. Task: `tasks/pciv-online-deploy.md` (AI-1538/AI-1542).

## State validation (session start, ~10:48 EDT)

- 2026-08-04 — Nest in sync with origin. Dev running `1.0.296-feat-online-pciv` (verified by prior
  session ~1h earlier; not re-verified). AWS dev SSO alive (`sts get-caller-identity` green), Jira
  token alive.
- 2026-08-04 — **INFRA-3474: Antonio replied at 10:40 EDT (comment 171731)** — recreated the Route 53
  Resolver inbound endpoint, repointed the cluster CoreDNS forward rule at the new resolver IPs
  (replacing the unreachable-from-corporate `10.11.144.2` design), validated in-cluster that
  `bedrock-mantle.us-east-1.api.aws` → `10.9.173.80` / `10.9.178.251` (the vpce ENIs). He asks us to
  re-check. NOTE: his fix is at the CoreDNS layer, not the corporate-DNS forward the parked draft
  asked for — the draft was superseded and disposed (Varun in-chat), commit 23998a1.
- 2026-08-04 — `dns_resolver_probe.py` reference values are now partially stale: the inbound resolver
  endpoint was RECREATED, so `10.9.174.63/10.9.179.109` are likely dead IPs; and the layer that
  matters for pods is now CoreDNS (cluster svc IP `172.20.0.10`, service CIDR `172.20.0.0/16` per
  `eks describe-cluster`). Update the docstring after re-verification.
- 2026-08-04 — **Gotcha: auto-mode classifier hard-blocks `aws ssm send-command`** (both compound and
  minimal forms) — agent cannot run the DNS probe on a worker. Handed Varun paste-ready `!` commands
  in-chat (probe corporate DNS + 10.11.144.2 + 172.20.0.10 from worker `i-044723c43204060ef`; old
  worker `i-0545f7a171eb0da30` from the 7/31 log no longer exists). Verification pending his run.

## Tree cleanup (Varun rulings in-chat)

- 2026-08-04 — `--query` flag in `tools/pciv/dev_eval_latency.py`: **landed** (64dc52c) — run
  `1049315117947128` depends on it.
- 2026-08-04 — Unstaged deletion of the "additional asks" lesson in `playbooks/jira.md`: **accidental
  per Varun — restored** via checkout. (Origin of the deletion unknown; possibly a stray editor
  action. No session claimed it.)
- 2026-08-04 — Superseded draft `review/2026-08-03-infra3474-forward-wrong-target.txt` deleted (23998a1).
- Still untouched: `worktrees/AI-1538-luna-latency` leftover worktree, Varun's own
  `pciv-online-human-notes.md`, `.DS_Store` strays.

## Evals 104–107 BUILT (Varun's go, in-chat — the twice-asked question is now answered)

- 2026-08-04 — `llm-evaluator-service` worktree, branch `feat-online-pciv`, commit **a0f7e08** on top
  of origin-synced `1aac587`: four entries in `domains/pciv_online/eval_configs.json` pairing each
  Mantle finalist with `pciv_extraction.txt` (~3.3k tok): **104 gemma-4-31b, 105 gpt-5.6-luna,
  106 qwen3-next-80b, 107 ministral-3-14b** (mirrors civ_extraction 609/610/612/613; domain
  conventions: max_group_size 1, max_concurrency 10). Config-only — models.json already had all four
  ids. 486 tests pass; loader smoke resolves all four eval→model chains.
- 2026-08-04 — Push parked in `review/2026-08-04-ai1538-evals-104-107-push.txt`. Deploy chain after
  push: CI image (`1.0.<build>-feat-online-pciv`) → cd-deploy-configs dev overlay tag bump → PR →
  Varun merges (master selfHeal auto-deploys).

## DNS fix VERIFIED (2026-08-04 ~12:10 EDT)

- Varun ran the probe via `!` (worker `i-0c9a6e664cbb1ec53`; first pick `i-044723c43204060ef`
  was running but not SSM-registered — InvalidInstanceId; the SSM-managed list comes from
  `describe-instance-information`, folded into the tool docstring). Results:
  corporate 10.11.128.70/.50 → public 3.214.115.45/34.231.48.123/52.87.73.163 (unchanged, host-level
  only); VPC resolver 10.11.144.2 → private; **CoreDNS 172.20.0.10 → private 10.9.173.80/10.9.178.251
  (ttl 30s) — the pod path, Antonio's fix confirmed.**
- Varun's SSO re-login and settings check dead-end first: the SSM block is the Claude Code classifier,
  not AWS auth; he chose `!`-relay over adding an ssm allow rule.
- Confirmation reply drafted: `review/2026-08-04-infra3474-dns-verified.txt` (discussion register, no
  method narration per the 2026-08-03 lesson).
- Evals 104–107 push executed by Varun ~11:50 EDT; draft disposed. CI build for a0f7e08 in flight.
- Saksham budget item: Varun in-chat — wait for more end-to-end results before restating the stack.

## 1.0.297 deployed; the deadline run happened (2026-08-04 ~12:15–13:30 EDT)

- Antonio reply: Varun answered in Slack himself; Jira draft disposed unposted.
- CI tag `1.0.297-feat-online-pciv` from Varun; overlay bump `AI-1538-image-1.0.297` (a6a7728ed)
  built in a temp worktree, pushed+merged by Varun ~12:17; temp worktree and local branch removed.
- Rollout verified WITHOUT Datadog or kubectl: eval 104 exists only in 1.0.297, and it served —
  kubectl path is dead anyway (SSO role not aws-auth-mapped: "server has asked for the client to
  provide credentials" after update-kubeconfig; Datadog MCP needed a /mcp handshake we skipped).
- DBX run `357322702087907` (ML-TEAM-CLUSTER, started from TERMINATED ~18min): evals 104–107,
  n=50+3 warmups each, the floor run's 15 FR queries. Results + laptop bisect in
  `state/pciv-service-latency-104-107-20260804.md`. Headline: Qwen 473 / Ministral 657 / Gemma 707
  (bad tail) / **Luna 5,702ms — flat ~5.5s per-request Mantle penalty, provider-side, new since
  7/31; reproduced at 8 input tokens**. Bisect chain: service langchain → raw httpx langchain
  payload → raw httpx probe payload → tiny prompt; all ~5.5–6s; reasoning_tokens 0 throughout.
- Bisect cost: ~11 Luna calls + 200-call run ≈ <$1.50 total, inside the 7/23 exploration budget.

## Open at session close

1. Luna penalty: re-probe later today/tomorrow (persistence unknown); if it holds, it belongs in
   any AWS/account-team conversation — flat 5.5s on standard tier, no SLA.
2. This morning's "client-reuse fix showed no saving" entry needs the caveat propagated wherever
   it was quoted (the fix IS proven via Qwen/Ministral/Gemma deltas).
3. Numbers → AI-1542 comms: Varun's call on wording/when (ballparks were due ~Aug 1).
4. Saksham budget restatement still deferred until Varun wants more e2e results in hand.
3. After deploy: the real-prompt finalist latency batches (evals 104–107, n≥50, `dev_eval_latency.py
   --eval-ids 104,105,106,107` from a classic DBX cluster) — the number AI-1542 actually needs.
4. Saksham's 1.1s CIV budget still uncorrected (see 2026-08-03 task-file entry) — needs Varun's call
   on how/where to restate the service-side number.
