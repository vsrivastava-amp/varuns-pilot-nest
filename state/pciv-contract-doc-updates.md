# "SSP - Online pCIV: API Contract" — wanted doc updates (running list)

2026-08-05. Companion to the snapshot `state/pciv-api-contract-20260805.md`; code state as of llm-evaluator-service `505b517` on `feat-online-pciv`. Regenerate/extend as the doc or code moves; delete when the doc edit lands.

## §2 Endpoint (the blank Varun owns)

- **UPDATED 2026-08-05 (Varun's uniform online-civ call): `POST /v1/intent/online-civ`**, `Content-Type: application/json`.
- Dev host becomes `https://dev-online-civ-service.ric1.admarketplace.net` once the rename package deploys (until then the live dev service still serves `/v1/intent/pciv` on the old `dev-online-pciv-service` host). Reachable in-VPC only.
- Stage/prod hosts TBD (AI-1538 Phase D); will follow the `*-online-civ-service` pattern.
- Tell Yaarit: this supersedes her `civ_online` domain name too (now `online_civ`) — needs her nod, Varun relaying in person.

## Naming drift inside the doc

- §3.3 says "qt/response/source/context" → should read prompt/responseContent/source/additionalContext (§3.2's own names).
- §5 failure example echoes `"qt"` → `"prompt"`.
- Echo policy: code echoes `prompt` on every per-query result (success and failure); §4.1's success example shows no prompt echo while §5's failure example does. Make the doc consistent (suggest: document the echo).

## §4.1 example bugs

- `"errorMessage": null` → `"error": null` (§4.2 and §5 both say `error{code,message}`; code matches them).
- `"googleProductCategories": [123]` (ints) → path strings, e.g. `"Apparel & Accessories > Shoes"` (§4.3 is authoritative; ints are the LLM-side format, resolved server-side).
- Example omits the response's real top-level shape: `placementID` echo plus operational extras `requestId`/`evalId`/`summary` that the service returns (contract's §4.3 note already blesses intent-level extras; add a matching note for top-level ones or show them).

## §4.2 field table

- The `queries[].error` row is truncated mid-shape (`{"code": "422"` …) — finish it: `{"code": string, "message": string}`.

## §4.3 intent object

- **Open question (Yaarit):** prompt emits `type` (discovery/investigational/transactional/executional) and the service returns it as `pcivType`; the contract's intent table omits it. Add to the doc, or direct us to drop it from the response.
- "we can change the number of max targets": now enforced server-side at 5 (schema truncates). If the cap becomes per-placement config, document that.

## §3.2 request fields

- **Open question (Yaarit):** `experimentContext` appears in the §3.1 example but has no row in the fields table and no stated semantics. Code accepts and ignores it; placementID alone selects the config. Document what it's for (experimentation-platform variant selection?) or remove from the example.
- `placementID`: per-integration constants still TBD — the doc should eventually list the agreed constants. Internally, dev placements 101–503 map 1:1 onto the A0B eval configs (`placement_configs.json`).
- `bypassCache` is in the fields table but not the §3.1 example; also decide whether it's SSP-facing or internal-only.
- Worth one sentence in §3.3: the extraction cache keys on the full built conversation text — the same prompt with different responseContent/source is cached separately.

## Header / links

- Repo link points at branch `feat-online-pciv-qwant-prompt` and path `domains/pciv_online/` — both stale: integration branch is `feat-online-pciv`, path is `domains/civ_online/`.

## §5 error handling

- Could state the two request-level 4xx cases explicitly: unknown `placementID` → 400; malformed body → 422 (FastAPI validation).
