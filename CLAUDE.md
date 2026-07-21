# Pilot's Nest — Agent Operating Manual

This repo is the shared memory system and inter-agent bus for automating Varun's work.
Every session: `git pull` first. The nest IS the continuity — assume your own context is ephemeral.

## Layout

- `PLAN.md` — the founding plan. Read it if you're new here.
- `map/` — one file per project. Near-static, highest value. Descriptions + pointers (repo paths, Jira IDs, Slack channels, owners). Human-reviewed; propose edits, don't freely rewrite.
- `log/` — append-only dated decision/context entries per project. Captures the *why* no source system stores. **Never edit in place, never delete lines.**
- `state/` — derived and disposable (digests, drift reports). Overwrite freely. Never trust past its date stamp.
- `runs/` — episodic record of what agents did + review outcomes. Compacted weekly.
- `playbooks/` — living reference docs for tools/procedures (CLI incantations, gotchas). Update in place as knowledge improves.
- `tasks/` — task queue, tagged by privilege tier: `no-auth` / `session` / `sudo`.
- `REVIEW.md` — outbound artifacts awaiting Varun's review (drafts, proposed PRs, ticket changes).
- `needs-sudo.md` — pre-staged sudo work, executed when a window opens.

## Conventions

- **Every line dated** (YYYY-MM-DD).
- **Single writer per file** — per-agent log files (`log/<project>--laptop.md`, `log/<project>--slack.md`) so pushes never conflict.
- **Cache interpretations, re-derive facts.** Never mirror Jira/git/Slack state into memory — fetch fresh via map pointers. Memory holds only what's expensive to re-derive.
- Laptop Claude is **nest steward** (weekly compaction, proposes map/ edits). Slack Claude is a contributor, never steward.
- Signals in Slack, state in git: after committing something notable, post a one-liner in the dev channel.

## Guardrails (non-negotiable)

1. Write access only to dev branches / dev channels. Prefer real permissions (branch protection, channel perms) over instructions.
2. **Never send messages as Varun** — drafts only, filed in `REVIEW.md` or posted for review.
3. **Never automate Okta/SSO. Never stash session tokens.** Auth stays human-gated.
4. Credentials live in OS keychain / env vars only — **never in this repo**.
5. Cheap credential probe before session-tier work (`aws sts get-caller-identity`, `databricks auth describe`, API ping). Dead credential → park the task, ping Varun. Never fail silently.
6. Outbound artifacts (messages, PRs beyond dev branches, ticket changes) go through the review gateway — land in `REVIEW.md`, keep working other tasks while they wait.
7. Ambiguous → park in review. Don't guess on anything outward-facing.
8. Slack Claude in DM mode (Varun's OAuth fallback) is read-only by policy.

## Privilege tiers for tasks

- `no-auth` — long-lived keys/tokens. Runs freely, any time.
- `session` — needs live SSO. Batch into post-Okta bursts.
- `sudo` — pre-stage in `needs-sudo.md`, execute when a window opens.
