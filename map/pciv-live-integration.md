# PCIV Live Integration

Live integration effort; ownership in flux (Steven Wu as of week of 2026-07-20). Activity is live in Slack #pub-onboarding-qwant-ai and Jira. Lowest agent ceiling: monitor, summarize, draft replies for review. **Varun's own attention goes here** — the agent's job is to keep him briefed, not to act.

## Pointers (verified 2026-07-23 — full context dossier in `log/pciv-online-service.md`)

- Slack: #pub-onboarding-qwant-ai (main), #proj-pciv-pub-integration-xfn-wg (arch decisions), #proj-amp-discover-3-0 (API), #team-relevance-yield
- Jira: no dedicated PCIV project — core work in **AI** (Artificial Intelligence), integration work in **AS** (Ad Selection, e.g. Qwant 3.0 API support), infra in **INFRA**. Query: `text ~ "PCIV" ORDER BY updated DESC`
- Anchor issues (2026-07-23): epic AI-1213 (Emerging Qwant support, due 8/15) → **AI-1538 (deploy online pCIV service, Varun)** + **AI-1542 (latency, Varun)** + AI-1540 (model eval, Steven Wu) + AI-1556 (query sets, Bhupesh); SSP side AS-13389 (ghost launch)/AS-13400 (payload spec); AI-1535 (live-path spike, Done — holds the architecture plan)
- Owner: **Varun** owns both build tickets since 2026-07-22 (Saksham reassigned AI-1538 Rama→Varun, AI-1542 Steven→Varun)
- Launch: Qwant 3.0 production launch **Aug 24** (decided 7/23); ghost 3.0 endpoints by 7/31

## Build tracker context (2026-07-23)

This effort is the serving side of tracker project **Relevance Quality Upgrade →
Milestone 7 "Qwant (French/German) Relevance"** (TL **Saksham Bhatla**, PL Amarachi
Miller, status 🟡; card updated 6/8/2026). Owners differ by layer: Saksham is the
milestone TL, **Varun owns the online-pCIV build tickets** (AI-1538/1542).

- **Dates aren't in conflict:** tracker "contract date **Aug 15**" = Qwant
  contract-signature target; nest "**Aug 24** launch" = production go-live (ghost
  3.0 endpoints by 7/31). Sharing the prepared PCIV artifacts (Implementation
  Guide, Prompt Breakdown, refined 2-shot prompt) is **gated on contract
  signature** per Supply-team guidance.
- Tracker **risks** (verbatim intent): relevancy-score improvement is written into
  the Qwant contract; low relevancy/CTR risks deal points; **low PLA demand
  liquidity + PLA category bias in EU** creates the impression of lower relevance;
  latency too high; token cost too high. Latency dependency: Fastly backbone (Kfir
  Shay).
- Tracker **next-step paths** for CIV extraction: (1) Qwant does it in-house;
  (2) AMP supports them with the 2-shot prompt (integration doc + sample code
  already provided); (3) unlikely — "2.1 API with just user query."
- Decision-point doc: "Qwant / AMP – Ad Integration – NT – 20260717".
- Tracker doc: `1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`.

## Agent posture

- 2026-07-21: monitor + summarize only. All drafted replies → REVIEW.md, never sent directly.
