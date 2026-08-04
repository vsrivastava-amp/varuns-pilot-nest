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

## Open at session close

1. DNS re-verification (Varun runs the `!` SSM commands; then draft the Antonio confirmation reply).
2. Push draft above → CI tag → overlay bump cycle.
3. After deploy: the real-prompt finalist latency batches (evals 104–107, n≥50, `dev_eval_latency.py
   --eval-ids 104,105,106,107` from a classic DBX cluster) — the number AI-1542 actually needs.
4. Saksham's 1.1s CIV budget still uncorrected (see 2026-08-03 task-file entry) — needs Varun's call
   on how/where to restate the service-side number.
