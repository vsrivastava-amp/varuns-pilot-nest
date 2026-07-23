# 2026-07-23 — KVSS KT sessions → map/kvss.md

**Session slug:** kvss-kt-digest

## Task
Varun asked to digest the 3 "KVSS - KT" knowledge-transfer sessions (Google Docs,
Gemini auto-notes) into the nest knowledge base.

## What I did
- Read all 3 KT Gemini-notes docs (KT1 Jul 15, KT2 Jul 20, KT3 Jul 22) via Drive MCP.
- Confirmed KVSS had **no** dedicated map entry — only appeared as a downstream
  box in `map/aas.md`. Created **`map/kvss.md`** consolidating all three sessions:
  two search paths (brand→exact-attribute / non-brand→vector), match-type
  thresholds (0.70/0.74/0.88), request/response contract, Vespa mechanics
  (index vs attribute, full vs fast, hybrid recall, soft timeout 50ms/0.6),
  feed data flow (Amplify→MySQL→Databricks→Kafka→Feed Service→Vespa), Intent
  Classifier Service's 3 functions, KVSS/VSS decoupling, publisher-lever
  deprecation decision.
- Cross-linked `map/aas.md` → `map/kvss.md`.

## Notes for next session
- Flagged Gemini transcription errors in the map (Solr not "Solar", Vespa not
  "Vaspuff", DSP = Demand-Side Platform, SSP = Supply-Side Platform). These are
  in the source docs — anyone re-reading the raw notes will hit them.
- **Embedding model never covered** across the 3 sessions; a KT4 (Vespa schema
  + dashboards + embedding model) is implied but not yet scheduled/dated.
- Design doc + policy-keywords doc promised in KT1 have not surfaced in the nest
  — grab if seen.
- No conflicts / needs-human items: read-only digest, nothing outward-facing.
- Presenter is Gemini-anonymized ("Someone in Price is Right"); left unattributed
  in the map (likely Ankit Shah's team — did not assert).
