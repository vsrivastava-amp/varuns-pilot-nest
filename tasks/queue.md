# Task Queue

Tagged by privilege tier: `no-auth` / `session` / `sudo`. Dated on entry. Move to `runs/` when done.

## no-auth

- 2026-07-21 — Phase 0 access map: verify each row of the PLAN.md table (hypothesis → fact), record results in `state/access-map.md`
- 2026-07-21 — Set up Atlassian MCP (or API token) for Jira read access; smoke-test against PCIV board
- 2026-07-21 — ✅ DONE: nest repo live at github.com/vsrivastava-amp/varuns-pilot-nest
- 2026-07-21 — ✅ MOSTLY DONE: Slack Claude capability audit → results in `playbooks/slack-claude.md`. Remaining: confirm it can actually clone the nest repo (read is claimed working, unverified against this specific repo); observed session lifetime
- 2026-07-21 — Admin ask: GitHub write access for Slack Claude (account not linked; push 403). Until then: patch-deposit protocol per `playbooks/slack-claude.md`
- 2026-07-21 — Draft Slack Claude's nest-protocol briefing (canvas/pinned msg for dev channel): pull ritual, deposit format, single-writer rule

## session

- 2026-07-21 — Databricks: confirm auth mechanism (`databricks auth describe`), list eval/experimentation jobs & dashboards
- 2026-07-21 — Pilot catch-up digest (read-only) → `state/digest-YYYY-MM-DD.md`

## sudo

(none — see needs-sudo.md)
