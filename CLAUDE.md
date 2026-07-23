# Pilot's Nest — Agent Operating Manual

You are one of **many concurrent Claude sessions** spawned in this directory, each usually working a distinct problem. This repo ("the nest") is the shared memory and the bus between all of them — laptop sessions and the company's Slack Claude. It is a **work in progress**: the architecture is settling, conventions may shift, and PLAN.md is the founding intent, not settled law.

## Start here (60 seconds, every session)

1. `git pull --rebase` — another session or Slack Claude may have pushed minutes ago.
2. `git log --oneline -15` — what's been built recently. **Much may already exist; check before you build.**
3. Skim `tasks/queue.md` (open work + claims) and `REVIEW.md` (pending human review).
4. If your task touches a project, read its `map/` file. If it touches a tool (Databricks, Jira…), read its `playbooks/` file — the curl/CLI incantations and gotchas are already solved there.

Rule of thumb: **infrastructure probably exists; facts are probably stale.** Reuse the first, re-derive the second.

## Layout

| Path | What | Lifecycle |
|---|---|---|
| `PLAN.md` | Founding plan / constitution | Amend via reviewed commits |
| `map/` | Per-project pointers (repos, Jira keys, channels, owners) | Near-static, human-reviewed |
| `log/` | Dated decision/context entries — the *why* nothing else stores | Append-only, never edit past lines |
| `state/` | Derived artifacts (digests, drift reports) | Disposable; distrust past its date stamp |
| `runs/` | What each session did + review outcomes | One file per session; compacted weekly |
| `playbooks/` | Living how-to docs per tool (auth, CLI patterns, gotchas) | Update in place as knowledge improves |
| `tasks/queue.md` | Open work, tagged `no-auth` / `session` / `sudo` | Claim before working (below) |
| `REVIEW.md` | Outbound drafts awaiting Varun (entry = metadata + pointer; body lives as one bare `.txt` per draft in `review/`, so Varun can `cat`/copy it) | Append; Varun disposes |
| `needs-human.md` | Varun's decision inbox: conflicts/decisions only human conversation resolves | Append entry; Varun answers inline; steward harvests to log/map |
| `needs-sudo.md` | Pre-staged sudo work for elevation windows | Staged commands, ready to paste |

## Concurrency discipline (many sessions, one clone, one git index)

- **Claim your task**: before starting queue work, append `⏳ claimed <date> <short-session-slug>` to its line in `tasks/queue.md` and commit. If a task is claimed and fresh (<1 day), leave it alone.
- **Write to your own files.** Runs go to `runs/YYYY-MM-DD-<slug>.md` (pick a unique slug for your session). Log entries: fine to append to shared per-project log files, but expect rebase conflicts — they're append-only, so resolution is always "keep both".
- **Commit surgically**: `git add <your specific files>` — never `git add -A`/`git commit -a`; another session's half-finished work may be sitting in the tree.
- **Push promptly**: small scoped commits, `git pull --rebase` immediately before each push. State shared via git beats state assumed via memory.
- `state/` collisions: last writer wins, by design — regenerate rather than merge.

## Conventions

- Every line you write in `log/`, `tasks/`, `runs/`, `REVIEW.md` starts with a date (YYYY-MM-DD).
- **Cache interpretations, re-derive facts.** Never mirror Jira/git/Slack state into the nest — fetch fresh via map pointers. The nest holds only what's expensive to re-derive.
- **Sources disagree, or a needed decision doesn't exist yet? Never silently pick a side.** File it in `needs-human.md` (template inside). Then check where the unknown sits:
  - **On your task's hot path** (the outcome changes what you'd build/write/conclude): **the task is blocked — let it stay blocked.** Park it in the queue referencing the Q-entry and release your claim. Do NOT build around the unknown, scaffold both branches, or proceed on the "likely" answer — work built on an undecided assumption calcifies into a de-facto decision nobody made.
  - **Peripheral** to your task: file it and continue; note the entry in your run log.
  Surfacing conflicts crisply is one of the most valuable things you can do — resolving them is Varun's actual job.
- Timestamps: this machine is Pacific; Databricks/most APIs are UTC. Say which.
- Learned a new incantation, gotcha, or auth fact? Fold it into the relevant `playbooks/` file before you finish — that's how the next session skips your pain.
- Laptop Claude is nest steward (weekly compaction, proposes `map/` edits for Varun's review). (Slack Claude retired 2026-07-22 — laptop sessions read Slack directly via MCP.)
- Signals in Slack, state in git: notable commits get a one-liner in the dev channel (via Varun, or Varun-directed send).

## Guardrails (non-negotiable)

1. Write access only to dev branches / dev channels. Prefer real permissions over instructions.
2. **Never send messages as Varun** — drafts only, into `REVIEW.md`.
3. **Never automate Okta/SSO. Never stash session tokens.** Auth stays human-gated.
4. Credentials live in `.env` (gitignored) / OS keychain / env vars — **never committed**. Check `git status` before commit if you touched anything credential-adjacent.
5. Probe credentials before session-tier work (`databricks auth describe -p <profile>`, Jira `/myself` ping, `aws sts get-caller-identity`). Dead → park the task, tell Varun. Never fail silently.
6. Outbound artifacts (messages, PRs beyond dev branches, Jira writes) go through `REVIEW.md`. Keep working other tasks while they wait.
7. Ambiguous → park in `REVIEW.md` with your best-guess draft. Don't guess on anything outward-facing.
8. claude.ai MCP connectors (Slack, Gmail, Calendar, Drive, Rovo) ride Varun's OAuth — **read-only by policy**. Any send/write via them appears *as Varun*: never, unless Varun explicitly directs it in-chat (that direction is the approval; log it in your run file).

## Current status (update when it changes)

- 2026-07-21 — Bootstrap phase. Live: nest repo (github.com/vsrivastava-amp/varuns-pilot-nest), Jira API (see `playbooks/jira.md`), Databricks CLI dev profile (see `playbooks/databricks.md`). Pending: Slack Claude access to this repo (Varun verifying), Datadog keys, pilot digest.
- 2026-07-22 — claude.ai MCP connectors live on laptop sessions: Calendar, Gmail, Drive, Atlassian Rovo, Slack (per-session `/mcp` handshake required — see `playbooks/google.md`). **Slack Claude retired** (see `log/nest--laptop.md`); morning routine v2 runs all sweeps laptop-side (`playbooks/morning-routine.md`). Still pending: Datadog keys.
- 2026-07-23 — Bitbucket read access live: laptop SSH key covers all `bitbucket.org/admarketplace` repos (dsp-engine, ssp-engine, …) — clone-to-scratchpad freely, see `playbooks/bitbucket.md`. Varun OK'd local clones for exploration (in-chat 2026-07-23).
