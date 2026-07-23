# PCIV Live Integration

Live integration effort; ownership in flux (Steven Wu as of week of 2026-07-20). Activity is live in Slack #pub-onboarding-qwant-ai and Jira. Lowest agent ceiling: monitor, summarize, draft replies for review. **Varun's own attention goes here** — the agent's job is to keep him briefed, not to act.

## Pointers (verified 2026-07-23 — full context dossier in `log/pciv-online-service.md`)

- Slack: #pub-onboarding-qwant-ai (main), #proj-pciv-pub-integration-xfn-wg (arch decisions), #proj-amp-discover-3-0 (API), #team-relevance-yield
- Jira: no dedicated PCIV project — core work in **AI** (Artificial Intelligence), integration work in **AS** (Ad Selection, e.g. Qwant 3.0 API support), infra in **INFRA**. Query: `text ~ "PCIV" ORDER BY updated DESC`
- Anchor issues (2026-07-23): epic AI-1213 (Emerging Qwant support, due 8/15) → **AI-1538 (deploy online pCIV service, Varun)** + **AI-1542 (latency, Varun)** + AI-1540 (model eval, Steven Wu) + AI-1556 (query sets, Bhupesh); SSP side AS-13389 (ghost launch)/AS-13400 (payload spec); AI-1535 (live-path spike, Done — holds the architecture plan)
- Owner: **Varun** owns both build tickets since 2026-07-22 (Saksham reassigned AI-1538 Rama→Varun, AI-1542 Steven→Varun)
- Launch: Qwant 3.0 production launch **Aug 24** (decided 7/23); ghost 3.0 endpoints by 7/31

## Agent posture

- 2026-07-21: monitor + summarize only. All drafted replies → REVIEW.md, never sent directly.
