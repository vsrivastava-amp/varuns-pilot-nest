# Task Queue

Tagged by privilege tier: `no-auth` / `session` / `sudo`. Dated on entry. Move to `runs/` when done.

## no-auth

- 2026-07-21 — Phase 0 access map: verify each row of the PLAN.md table (hypothesis → fact), record results in `state/access-map.md`
- 2026-07-21 — Set up Atlassian MCP (or API token) for Jira read access; smoke-test against PCIV board
- 2026-07-21 — ✅ DONE: nest repo live at github.com/vsrivastava-amp/varuns-pilot-nest
- 2026-07-21 — ✅ DONE: Slack Claude capability audit → `playbooks/slack-claude.md`. Clone/read of nest repo confirmed 2026-07-21; first patch deposit applied same day. Remaining curiosity (non-blocking): observed session lifetime
- 2026-07-21 — ~~Admin ask: GitHub write access for Slack Claude~~ 2026-07-22: OBSOLETE — Slack Claude retired (see `log/nest--laptop.md`); withdraw the admin ask if filed
- 2026-07-21 — ~~Draft Slack Claude's nest-protocol briefing~~ 2026-07-22: OBSOLETE — Slack Claude retired

## session

- 2026-07-22 — **pCIV demo GPC taxonomy fix** (Qwant client escalation, group DM C0BJPQHFFGC): expand `gpc_taxonomy.json` 75→213 entries (21 L1 + 192 L2 from eval-service full taxonomy) AND rework `prompts/pciv_extraction.txt` GPC section (66 ids → full L2, incl. disambiguations) **in sync** — they're already mismatched (66 vs 75). Analysis + token impact done: `runs/2026-07-22-pciv-taxonomy-gap.md`. Token-answer draft for Dhaval in REVIEW.md. Implementation blocked on Varun/Yaarit design call (prompt format, regression testing) — demo repo posture is read-only for agents.
- 2026-07-21 — Databricks: confirm auth mechanism (`databricks auth describe`), list eval/experimentation jobs & dashboards
- 2026-07-21 — Pilot catch-up digest (read-only) → `state/digest-YYYY-MM-DD.md`. ⏳ partial: Slack leg done by slack-claude 2026-07-21 (`log/pciv-live-integration--slack.md`); Jira leg done 2026-07-22 morning-routine (`state/digest-2026-07-22.md`); remaining legs: git history, Databricks job status

## sudo

(none — see needs-sudo.md)
- 2026-07-23 — ~~**Bedrock roster + access sweep**~~ ✅ done 2026-07-23 (SSO login by Varun in-session): access verified end-to-end, roster snapshot in `playbooks/llm-eval-system.md` §Bedrock. Headline: NO gpt-5 family on Bedrock (only gpt-oss); Llama4/Qwen3/DeepSeek/GLM/Mistral/Anthropic all invocable.
- 2026-07-23 — ~~Verify Bitbucket read access~~ ✅ done 2026-07-23 same-day: no token needed — laptop already had a dedicated SSH key (`~/.ssh/bitbucket` via ssh config). `playbooks/bitbucket.md` written; dsp-engine cloned + 2.0 auction formula verified against source (map/aas.md updated).
