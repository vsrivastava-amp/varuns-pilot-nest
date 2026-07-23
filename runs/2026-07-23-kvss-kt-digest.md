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

## Verification pass (same day, Varun-prompted: "jira + slack could double-check")
- Cross-checked the KT-seeded map against authoritative sources via Rovo + Slack MCP:
  - Confluence **SC227** (KVSS service/runbook page) + **TDD "Text Ads Vector Search"**
    (Roberto Simoes, Google Doc, Jira **SRS-1570**, project **SRS = Search Relevancy Squad**).
  - Slack sweep (subagent, 2 large dumps) — mostly noise (snyk/gong), but confirmed
    BRAND→EXACT / NON_BRAND→VECTOR + `keyword_ad` schema in #proj-amp-discover-3-0
    (Artem Dippel 7/01), and surfaced Databricks tables (`brand_keyword`, `intent_type`,
    `query_term_expansion`, `model_relevancy_threshold`, `vector_search_profile`).
- **Key correction:** legacy text-ad engine is **Elasticsearch, not Solr** (my original
  "Solar = Solr" caveat was wrong). Fixed in the map with citations.
- **Big overlap discovered:** a concurrent session shipped `map/vespa.md` (commit 8e4d95a)
  with repo-verified KVSS internals — far deeper than mine on endpoints/schema/thresholds.
  Reframed kvss.md as the semantics/history/doc-source view and pointed repo internals
  to vespa.md rather than duplicating. Added: canonical doc pointers (SC227/TDD/SRS),
  Kafka feed contract (`ric1.audience-keyword-targeting-embeddings`, status semantics),
  fuller request/response field list, brand-path & query-expansion design lineage,
  California Roll (WF-16732) for the publisher-lever deprecation.
- Endpoint discrepancy flagged (Confluence `/api/v1/search/text-ads/vector` vs vespa.md
  repo-read `/api/v1/search`) — left as a note, did not edit vespa.md (other session's file).

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
