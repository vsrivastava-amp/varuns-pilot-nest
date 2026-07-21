# pCIV Demo

pCIV demo environment, owned by Winston. Agent involvement is deliberately narrow: periodic dev-vs-prod drift summaries only — no code changes, no outreach.

## Pointers (unverified — fill in as confirmed)

- Repo: `pciv-demo-service` (Bitbucket — set up via INFRA-3422)
- Backend server config: DPR-3263; prod ingress via pub-nlb on RIC1 (INFRA-3421)
- Jira: demo work spans AI (e.g. AI-1531, two-shot functionality — Varun) and DPR
- Owner: Winston Wang

## Agent posture

- 2026-07-21: read-only. Output drift summaries to `state/`.
