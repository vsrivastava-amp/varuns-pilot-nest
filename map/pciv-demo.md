# pCIV Demo

pCIV demo environment, owned by Winston. Agent involvement is deliberately narrow: periodic dev-vs-prod drift summaries only — no code changes, no outreach.

## Pointers (unverified — fill in as confirmed)

- Repo: `pciv-demo-service` (Bitbucket — set up via INFRA-3422)
- Local clones (verified 2026-07-22): `~/Documents/pciv-demo-service`; client-facing zip contents at `~/Desktop/external-pciv-demo` (+ copies " 2", " 3" — all identical). Taxonomy: `taxonomy/gpc_taxonomy.json`; extraction prompt: `prompts/pciv_extraction.txt`
- Full GPC taxonomy source of truth: `llm-evaluator-service/src/main/python/domains/civ_extraction/resources/gpc_taxonomy.json` (5595 entries, all levels)
- Open issue 2026-07-22: demo taxonomy non-exhaustive (Qwant escalation, group DM C0BJPQHFFGC) — see `runs/2026-07-22-pciv-taxonomy-gap.md` + queue
- Backend server config: DPR-3263; prod ingress via pub-nlb on RIC1 (INFRA-3421)
- Jira: demo work spans AI (e.g. AI-1531, two-shot functionality — Varun) and DPR
- Owner: Winston Wang

## Agent posture

- 2026-07-21: read-only. Output drift summaries to `state/`.
