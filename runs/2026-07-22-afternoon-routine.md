# Run — 2026-07-22 afternoon — first all-connector morning-routine (slug: afternoon-routine)

- 2026-07-22 — Session also: connected all 5 claude.ai MCP connectors (smoke tests passed), wrote playbooks/google.md, morning-routine v2, retired Slack Claude (Varun's call — 7d68e26).
- 2026-07-22 — Ran routine v2 afternoon delta: Calendar + Gmail + Slack direct; Jira via Rovo JQL. Output appended to state/digest-2026-07-22.md (PM section).
- 2026-07-22 — Gotcha (folded into morning-routine.md): Rovo `searchJiraIssuesUsingJql` with `comment` in fields over ~20 issues overflows context (138k chars) — result auto-saved to file; digested via subagent. Either drop `comment` from the sweep and fetch per-anchor, or plan the subagent step.
- 2026-07-22 — Concurrency: another session active in tree (unstaged tasks/queue.md); committed surgically (state/digest, runs/, playbook), no pull --rebase possible over dirty tree — pushed if remote allowed, else left local (see git).
- 2026-07-22 — Not covered: Databricks job status, git-history leg of catch-up digest (still open in queue). Q-2026-07-21-01 (locale/tz): no new movement observed.
