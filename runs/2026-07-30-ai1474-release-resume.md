# 2026-07-30 — AI-1474 release resume

- 2026-07-30 — Resumed `tasks/ai-1474-release.md` at Varun's direction. Synced the nest (`git pull --rebase`: already current), reviewed the queue, task handoff, llm-eval map, Bitbucket/Jira/Databricks/k8s playbooks, and the repository release-process skill.
- 2026-07-30 — Flagged all pre-existing `review/` items to Varun in chat. Left unrelated drafts and untracked Qwant sample artifacts untouched.
- 2026-07-30 — Refreshed Bitbucket refs for `llm-evaluator-service` and `cd-deploy-configs`. Preserved substantial user-owned untracked files in both local clones and made no edits in either checkout.
- 2026-07-30 — Fresh service history: `origin/main` remains `ae16d88`; `origin/feat-civ-eval-6-gemini` remains `ae1da11`; branch is 0 commits behind and 1 ahead. Tribikram's latest merged service work is PR #44 / `9fa18ec` from 2026-07-21, already contained in both main and the Gemini branch.
- 2026-07-30 — Validated the exact remote Gemini commit from an isolated `/private/tmp` archive. Python 3.13.1 test result: 307 passed in 1.44 seconds.
- 2026-07-30 — Fresh Jira AI-1474 status is In Review. Dhaval's latest direction remains: merge the code to main, deploy main to prod, accept 0.03% residual rate-limit losses, and avoid waiting long enough to create merge conflicts.
- 2026-07-30 — Fresh config audit: prod image is `1.0.286-main`; dev image is `1.0.288-feat-civ-eval-6-gemini`; stage image is `1.0.286-main`. Main maps CIV eval 6 to `gpt-5-mini`; the feature branch maps eval 6 to `gemini-3-6-flash`.
- 2026-07-30 — Cache safety finding: CIV DynamoDB keys hash only eval ID and normalized query. The invalidate endpoint accepts enumerated queries only; it has no full-eval namespace purge. A prod deploy that reuses eval 6 can silently serve old mini cache entries as Gemini results unless the team chooses a complete cache migration.
- 2026-07-30 — Drafted the eval-ID/cache/civ_config/prod-capacity question for the existing Sunil+Yaarit group DM in `review/2026-07-30-ai1474-sunil-config-dm.txt`. No Slack write performed.
- 2026-07-30 — Databricks credential probe failed: configured profiles `DEFAULT`, `dbc-562d27e2-d74d`, `vsrivastava_dev`, and `stage` are all invalid; no prod profile exists. Parked the 762-row retry and live `civ_config` inspection/write until Varun re-authenticates.
- 2026-07-30 — Dev HPA downshift PR remains unmerged: `origin/master` still has min/max 16/16; branch `origin/feat-ai1474-dev-replicas-down-to-8` has 8/8.
- 2026-07-30 — Release-process stop point: no RELEASE ticket, release announcement, service PR, prod CD PR, cache mutation, or deployment created. These would encode the unresolved eval-ID/cache choice. Prod CD still requires peer approval and a manual Varun merge.
- 2026-07-30 — Filed `Q-2026-07-30-02` for Varun's ambiguous Tribikram instruction and released the queue claim per the hot-path rule.
