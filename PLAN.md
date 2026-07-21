# Handoff: Work Automation — "Pilot's Nest"

*(Founding plan, checked in 2026-07-21. Treat as the constitution; amend via reviewed commits.)*

## Context

Goal: automate the manual gaps in Varun's day job (ML infra / LLM eval pipelines at an ad-tech company). Agents do routine work; Varun reviews in batches. Claude Code is sanctioned and widely used at the company. Binding constraints are **access walls**: Okta SSO daily (manual, by design), sudo only on request, per-app auth.

Two agent surfaces:
- **Laptop Claude Code** — works local clones + cloud APIs. Gateway for Bitbucket, Databricks, Datadog, AWS, and anything needing Varun's session.
- **Slack Claude** (company's managed Claude-in-Slack) — ephemeral admin-provisioned container with dedicated Slack + GitHub tooling (including claimed GitHub push access), other services via credential-injected curl. Gateway for Slack and granted GitHub repos.

## Architecture: the nest

A single **GitHub repo of plain markdown** ("the nest") is both the memory system and the inter-agent bus. No databases, no bespoke tooling — files in git are greppable, diffable, reviewable as commits, and forward-compatible with Claude Code memory features.

**Bus principle:** agents never talk directly. They share state through the repo. Slack Claude pushes what it learns; laptop Claude pulls it, and vice versa. Every fresh session (both are ephemeral) starts with `git pull` — the nest IS the continuity.

### Memory layers (different lifecycles)

1. **`map/`** — one file per project, near-static, highest value. Three-sentence description + pointers: repo paths, Jira board/epic IDs, Slack channel names, doc URLs, owners. Changes ~monthly, human-reviewed.
2. **`log/`** — append-only dated decision/context entries per project ("chose X over Y because Z", "Steven owns PCIV as of July"). Captures the *why* no source system stores. Never edited in place.
3. **`state/`** — derived, disposable, regenerated: daily digest, sprint summaries, branch-drift reports. Overwritten freely; never trusted past its date stamp.
4. **`runs/`** — episodic: what agents did, review outcomes. Audit trail; compacted weekly.

**Anti-staleness principle: cache interpretations, re-derive facts.** Never mirror Jira/git/Slack state into memory — fetch fresh via map pointers. Memory holds only what's expensive to re-derive.

**Conventions:** every line dated; single-writer-per-file (per-agent log files) so no merge conflicts; laptop Claude is nest steward (weekly compaction: distill runs/ and log/, propose map/ edits, Varun reviews the diff — ~5 min/wk). Slack Claude is a contributor, never steward (sessions get reclaimed).

### Claude Code wiring
- Global `~/.claude/CLAUDE.md`: guardrails + nest location.
- Each project clone's `CLAUDE.md`: `@`-imports its nest map file + recent log entries.
- Skills for recurring procedures (digest, review filing). A "context scout" subagent follows map pointers across Jira/Slack/docs and returns synthesis, keeping junk out of the main context window.
- Signals in Slack, state in git: when Slack Claude commits something, it posts a one-liner in the dev channel.

## Operating model

- **Task queue by privilege tier**: `no-auth` / `session` (live SSO) / `sudo`. No-auth runs freely; session work batches into post-Okta bursts; sudo work pre-staged in `needs-sudo.md`, executed when a window opens.
- **Auth-aware**: cheap credential probe before each task (`aws sts get-caller-identity`, `databricks auth describe`, API ping). Dead → park task, ping Varun. Never fail silently.
- **Review gateway**: outbound artifacts (messages, PRs beyond dev branches, ticket changes) land in `REVIEW.md` or dev channel. Agent keeps working other tasks while items await review.

### Guardrails (CLAUDE.md + real permissions where possible)
- Write access only to dev branches/channels; enforce via branch protection & channel perms, not just instructions
- Never send messages as Varun — drafts only
- Never automate Okta/SSO or stash session tokens; auth stays human-gated
- Slack Claude DM-mode (Varun's OAuth fallback) is **read-only by policy** — writes only on admin-scoped channel credentials, so nothing it does is indistinguishable from Varun
- Ambiguous → park in review

## Phase 0 research (do first)

For each app: what runs on a long-lived key (`no-auth`)? What needs daily SSO (`session`)? What needs sudo, and can it convert to temp/scoped access? Sanctioned path over hacky path, always.

| App | Need | Mechanism | Tier (verify) |
|---|---|---|---|
| Databricks dev | r/w | CLI OAuth U2M profile (rides SSO); PAT scoped to dev if allowed; official MCP server | session → no-auth w/ PAT |
| Datadog | read | API + app key, read-only scopes | no-auth |
| Jira/Atlassian | read | API token + official Atlassian MCP (Jira+Confluence). Token inherits full perms — read-only is behavioral | no-auth |
| Slack | read + drafts | **Slack Claude** (sanctioned). Laptop needs no Slack API — Slack Claude deposits into nest. Fallback: self-serve Slack app w/ bot token, if org allows installs | sanctioned |
| GitHub | r/w | Laptop: existing auth. Slack Claude: admin-granted scope — **must include nest repo** | no-auth |
| Bitbucket | r/w | Laptop only (app password / SSH) | no-auth |
| AWS | occasional read | `aws sso login` profile | session |
| Calendar | read | Google Calendar MCP | no-auth after OAuth |
| Okta | gate | Manual daily, Okta Verify. Session lifetime (12/24h?) sets burst schedule. Chrome extension operates *inside* the authed browser for UI-only tasks — never automates login | human |

**Sudo:** inventory last month's actual sudo needs; move what's possible to user-space (venvs, rootless docker, user systemd); ask about standing group membership / temp-elevation process; remainder lives in `needs-sudo.md` pre-staged for windows.

### Slack Claude capability audit (10 min, do via DM + a channel)
Confirmed so far: public-channel search workspace-wide; read channels it's `/invite`d to + the DM; user/group lookup; post/react in threads; canvases/bookmarks/pins. Cannot read private channels or uninvited public ones; falls back to Varun's OAuth in DM.
Still to verify:
1. List actually-visible GitHub repos via API (not claims); confirm **push** by test-committing to a scratch repo
2. Can the nest repo be added to its grant? (Admin ask if needed)
3. `curl` Jira/Confluence/Datadog/Databricks → report 200 vs 401, in DM *and* channel mode (credential sets differ)
4. Write posture: open PRs? Post to channel vs thread-only?
5. Observed session lifetime + disk allowance
Skip platform introspection (/proc etc.) — changes no decisions, bad look on monitored infra.

## Work streams (from OOO handoff msg)

1. **LLM Eval Service/Pipeline** — Varun is context-holder; release #6037 was mostly refactors. Highest ceiling: post-release follow-ups, triage, small fixes. Primary repo-work target.
2. **pCIV demo** — Winston owns. Agent: periodic dev-vs-prod drift summaries only.
3. **Experimentation Platform** — Databricks dashboards. Pull status, flag anomalies (session tier).
4. **PCIV Live Integration** — ownership in flux (Steven Wu this wk), live in #pub-onboarding-qwant-ai + Jira. Lowest ceiling: monitor, summarize, draft replies for review. **Varun's own attention goes here.**

## Pilot (read-only, before any write access)

**Catch-up digest** covering the OOO week:
- git history across eval-service repos (laptop)
- release channel + #pub-onboarding-qwant-ai (Slack Claude → nest)
- Jira PCIV board activity (laptop, Atlassian MCP)
- Databricks job/dashboard status (laptop, session tier)

Output → `state/digest-YYYY-MM-DD.md` + a proposed task queue tagged by tier. Tests every pipe with zero write risk; output seeds the real queue.

## Session deliverables, in order
1. Create nest repo + skeleton: `map/ log/ state/ runs/ tasks/ REVIEW.md needs-sudo.md CLAUDE.md` (guardrails), MCP config w/ exact scopes. Seed `map/` from the four work streams above.
2. Access map completed (table above, hypotheses → facts). Credentials in OS keychain / env only — never in repo.
3. Slack Claude audit run; nest repo added to its grant; pin its nest-protocol instructions (where files live, what it deposits, single-writer rule) as a canvas in the dev channel.
4. Pilot digest, if pipes are live.

## Operating style

Iterative, as things come up. Each session: do real work, and leave the nest a little stronger — more infrastructure, better maps, fresher logs. Every session we learn a bit more.
