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
- 2026-07-23 — **Bedrock roster + access sweep** (feeds AI-1540/AI-1542 model choice + Bedrock-vs-DBX decision): needs Varun to run `aws sso login --profile dev` first (human-gated). Then `/model-selection` §1b: list models + inference profiles in us-east-1, check model-access grants, answer "is gpt-5-family on Bedrock?", record roster snapshot in playbooks/llm-eval-system.md. `session`-tier.
- 2026-07-23 [session] Verify Bitbucket read access once Varun adds token to .env (BITBUCKET_API_TOKEN or Bitbucket-scoped ATLASSIAN_API_KEY); then write playbooks/bitbucket.md (auth, clone pattern, repo inventory: dsp-engine, ssp-engine, amp-discover-model, experimentation-platform-service, qe-dsp-engine-api-tests) + update CLAUDE.md status. Context: runs/2026-07-23-aas-context.md; first use = read DSP auction/pricing source (AS half of map/aas.md formula).
