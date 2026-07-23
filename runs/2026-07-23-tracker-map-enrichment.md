# 2026-07-23 — Enrich maps with Build Tracker context

Session slug: tracker-map-enrichment

## What

Varun shared the "2026 Build Project Tracker – NT" Google Doc
(`1oVcSyWvEqWZ30Ved_7cTrdf5AU1EFG0Mjo7K5pszEUk`, owner Norbert Tamas, ~430K chars,
"Last Update 6/3/26" header but cards maintained through 7/20–7/24). Digested it
via subagent (extract saved to scratchpad `tracker.md`), then folded the stable,
additive facts into existing `map/` entries.

## Principle applied

Tracker header is 6/3; several maps already carry fresher live status (re-derived
from Jira/Slack/code). So per CLAUDE.md ("cache interpretations, re-derive facts";
map = per-project pointers) I added the tracker only as a **source pointer** + the
stable facts it uniquely holds — Build-Accountable owners, milestone/TL structure,
project Slack channels, strategy/spec doc links — and did **not** overwrite any
map's current-state section with the tracker's older milestone status.

## Edits (all dated 2026-07-23)

- `map/aas.md` — new "Build tracker" section: card "Ad Auction Re-architecture",
  Build Accountable Dhaval + Norbert (vs eng TL Joseph), **M5 DSP-redesign TL
  Roberto Simoes**, epics AI-1172/1175 flagged to verify against the re-parented
  AI-1550/1432 hierarchy.
- `map/pciv-live-integration.md` — Qwant is Relevance Quality Upgrade **M7** (TL
  Saksham); reconciled tracker "contract Aug 15" vs nest "launch Aug 24" (not a
  conflict — signature target vs go-live); added contract-gated artifact sharing,
  risk list, 3 CIV next-step paths.
- `map/llm-eval-service.md` — ARES = eval half of Relevance Quality Upgrade;
  **Varun TL of M4 ARES v1.1 Text Ads (Done)**; filled "release channel TBD" with
  #proj-automated-relevance-eval-service et al.
- `map/experimentation-platform.md` — filled Owner TBD → Dhaval Shah; status Done;
  Slack #proj-experimentation-platform.
- `map/kvss.md` — added PM-view pointer: project "Text Ads – Positive Keywords"
  (Norbert, #proj-positive-keywords), the delivery side of the KVSS transition.
- `map/org-chart.md` — new "Project ownership (from Build Tracker)" cross-ref
  block; centralizes tracker + resource-allocation sheet + Gantt folder links and
  the 50/25/25 allocation model.

## Notes / follow-ups

- Tracker's AAS milestone epics (AI-1172/1175 on M5) predate the 7/20–7/22 Jira
  re-parenting under AI-1550 — left as "verify," not asserted.
- No new conflicts surfaced for `needs-human.md`. No outbound artifacts.
- Not covered (no existing map): Ranking & Pricing – AMP Discover card (CTR model
  on Baseten, ELME 3.0, epics AI-1140/1141) and 3rd Party Feeds card. If either
  gets a map later, tracker has rich card detail in scratchpad `tracker.md`.
