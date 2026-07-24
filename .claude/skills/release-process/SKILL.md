---
name: release-process
description: How to run a release of an adMarketplace app (llm-evaluator-service etc.) — dev/stage rollout, RELEASE Jira ticket, release Slack channel + announcement, CD deploy-config update with peer-approved PR for prod, closing comms. Use when Varun says "let's do a release", "ship this", "deploy to prod", or a merged change needs to reach an environment.
---

# Release process (adMarketplace apps)

*(Seeded 2026-07-24 from Varun's walkthrough, using Yaarit's civ-prompt-fix release as the worked example. Sections marked TBD get filled in as Varun supplies details — update in place.)*

Reference example throughout: RELEASE-6132 / `#release-6132-civ-prompt-fix-v3` / llm-evaluator-service eval-id-6 release (2026-07-23).

## The steps, in order

### 1. Dev and stage releases first — via CD deploy configs
Roll the new build through dev and stage before any prod motion. Mechanics (learned 2026-07-24 from Yaarit's PRs #7215–7217 + Varun's walkthrough):

1. **Push the feature branch** to the app repo. Every push runs the default pipeline (init → tests → docker build/push).
2. **Grab the build tag**: `<MAJOR_VER>.<BITBUCKET_BUILD_NUMBER>-<branch>` where MAJOR_VER = `version` in `pyproject.toml` (llm-evaluator-service: `1.0`). Image lands at Docker Hub `admarketplace/<repo-slug>:<tag>` (private — anon tag listing 404s; classifier blocks credential probes, so get the build number from the Pipelines UI via Varun).
3. **Bump cd-deploy-configs** (llm-evaluator-service lives in the **Bitbucket** CD repo, `bitbucket.org/admarketplace/cd-deploy-configs`): edit `apps/<app>/<env>/kustomization.yaml` → `images: [- name: admarketplace/<app>, newTag: <tag>]`. Envs for llm-evaluator-service: `dev-ric1`, `stage-ric1` (plus `base/`, `datadog-base-deployment/`).
4. **One PR per env bump**, branch naming per Yaarit: `feat-<slug>-image` (dev), `feat-<slug>-stage-image` (stage). PR title/commit: `Deploy <app> <tag> to <env>`. Dev/stage PRs are self-mergeable by the requester; prod is gated (step 4 below).
5. Merge to cd-deploy-configs main triggers the deploy (Argo-style sync). Validate on dev before promoting the same image to stage.

Gotcha: main can move under your branch (e.g. a hotfix) between validation and deploy — rebase and re-push before grabbing the tag, so the deployed image includes everything on main. The rebuild changes the build number, so always take the tag from the **latest** green pipeline run.

### 2. Create a RELEASE ticket in Jira
- Project **RELEASE**, issue type **Release** (example: RELEASE-6132).
- Summary pattern: `Release <component / change> (<key identifier>)` — e.g. "Release CIV Extraction commercial/partial-query prompt fix (eval id 4)".
- Description: what the release fixes/adds, then a **components being released** list — per repo, the concrete artifacts changing (files, config ids, prompts) and any id/semantics changes reviewers must know.
- Agent may create via Jira API with Varun's approval (precedent: INFRA-3462).

### 3. Release channel + announcement
- Create a Slack channel named `#release-<ticket number>-<short-slug>` (example: `#release-6132-civ-prompt-fix-v3`).
- Post an announcement in **#releases** (channel id `C0218RBRGCS`) linking the ticket + channel; "usually a bit more descriptive, varies by release" — describe what's shipping and when.
- Agent drafts these; sending/creating via Slack MCP rides Varun's OAuth → only on his explicit in-chat direction (guardrail 8), otherwise he posts.

### 4. Update CD deploy configs for prod (the gated step)
- CI (bitbucket-pipelines) builds a Docker tag `<version>.<build#>-<branch>` on every push — the release = pointing the CD deploy config at the new tag.
- **Two CD deploy-config repos exist: one on Bitbucket, one on GitHub. Each app belongs to exactly one.** `llm-evaluator-service` → **Bitbucket** `cd-deploy-configs`, config at `apps/llm-evaluator-service/<env>/kustomization.yaml`. TBD: prod env directory name (only `dev-ric1`/`stage-ric1` existed as of 2026-07-24 — prod config location unconfirmed).
- Prod flow, strictly: **(1)** open a PR with the new tag → **(2)** peer approval from another engineer/manager with project context → **(3) Varun merges manually.** The agent never merges prod CD configs; drafting the PR is fine.

### 5. Close the loop
- Update the RELEASE ticket (status + verification notes).
- Send a wrap-up message in the release channel.

## Gotchas / context

- Service configs are `@lru_cache`d at process start — a config-only change still needs a redeploy to take effect (see `playbooks/llm-eval-system.md`).
- Eval-id semantics can change between dev/stage validation and prod release (Yaarit validated as id 6, shipped as id 4 per team request, moving gpt-5-mini to 6) — read the RELEASE ticket description for id swaps before assuming continuity, and check the **DynamoDB civ cache namespace implications** of any id reuse (cache keys embed the eval id; a reused id inherits the old id's cached answers).
- Prior release working notes: `playbooks/llm-eval-system.md` "Release verification pattern that worked" (waterline seed → run → verify by eval_id → failures flat).
- Keep `llm_evals.relevancy_config` / `civ_config` table rows in sync with the service's eval_configs.json as part of the release.
