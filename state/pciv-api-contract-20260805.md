# SSP - Online pCIV Extraction: API Contract (WIP) — snapshot 2026-08-05

Provenance: pasted by Varun in-chat 2026-08-05 (gdoc connector down; doc shared by Yaarit, title "SSP - Online pCIV: API Contract (WIP)"). This is a dated copy of a WIP doc — re-read the live gdoc when the connector returns; distrust past this date. Table formatting flattened by the paste; field tables reconstructed below from the pasted rows.

pCIV repo pointer (from doc): https://bitbucket.org/admarketplace/llm-evaluator-service/src/feat-online-pciv-qwant-prompt/src/main/python/domains/pciv_online/
(NB: names branch `feat-online-pciv-qwant-prompt` — our deploy chain to date is on `feat-online-pciv`. See log 2026-08-05.)

## 1. Purpose

The SSP calls this service in real time with a user query (and, when available, the publisher's own LLM response and search context) and gets back a structured Context & Intent Vector (pCIV): commercial intent and up to 5 commercial targets (max targets changeable).

Primary use case today: Qwant's AI Chat surface, France only — the query always arrives with the publisher's own LLM response attached.

## 2. Endpoint

*(blank in doc: "Varun Srivastava please add")*

## 3. Request

### 3.1 Shape

```json
{
  "placementID": 1234,
  "queries": [
    {
      "adRequestId": 11111,
      "prompt": "Quelles sont les meilleures activités à faire à Annecy ?",
      "responseContent": "Voici une sélection des meilleures activités à faire à Annecy, adaptées à différents...",
      "source": null,
      "additionalContext": null
    }
  ],
  "experimentContext": {
    "config": {
      "pcivExtraction": "online_v1"
    }
  }
}
```

### 3.2 Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| placementID | int | yes | Selects which model + prompt config to run. A pre-agreed constant per integration, not something the SSP computes. |
| queries | array (min 1) | yes | The SSP sends one query per request for now (the array/batching support exists for potential future use) |
| queries[].adRequestId | int | yes | Caller-supplied request ID, echoed back unchanged so the SSP can match results to its own ad request. |
| queries[].prompt | string | yes | The user's query/prompt. |
| queries[].responseContent | string | no | The publisher's LLM response text, when available. Present for the AI Chat / France use case; absent for plain Flash Answer. |
| queries[].source | object | no | SERP/web-search context, when available. `source.summary`: string. `source.items[]`: array of `{title, description, snippets[]}`. |
| queries[].additionalContext | string | no | Open-ended escape hatch for publisher-specific input not yet covered by qt/response/source (e.g. a future input shape). Sanitized and appended into the conversation text the same way as the other fields — lets new publishers send additional context without a schema change. |
| bypassCache | bool | no (default false) | If true, skips the extraction cache and always calls the LLM. |

### 3.3 How these get combined

We build the conversation text sent to the LLM server-side from qt/response/source/context ("user: …\nassistant: …\nsource: …"), rather than requiring the SSP to pre-format a single string. This also means literal role-prefix substrings a user might type (e.g. a query containing the text "assistant:") can't be mistaken for a real turn boundary — we control the exact construction and neutralize those patterns before concatenating. context is the hybrid escape hatch: qt/response/source stay structured for the input shapes we know about today, and context absorbs anything a future publisher sends that doesn't fit those yet — it goes through the same construction and sanitization as the rest, not a separate path.

## 4. Response

### 4.1 Shape (real example)

```json
{
  "queries": [
    {
      "adRequestId": 11111,
      "status": "SUCCESS",
      "errorMessage": null,
      "intent": {
        "commercialIntent": true,
        "topic": "Nike men's running shoes under $150 at Macy's",
        "targets": [
          {
            "googleProductCategories": [123],
            "sellerNames": ["Macy's"],
            "priceMin": null,
            "priceMax": 150.0,
            "priceTarget": 150.0,
            "priceCurrency": "USD",
            "productName": "running shoes",
            "brand": "Nike",
            "gender": "male",
            "ageGroup": null,
            "condition": null
          }
        ]
      }
    },
    {
      "adRequestId": 33333,
      "status": "SUCCESS",
      "errorMessage": null,
      "intent": {
        "commercialIntent": false,
        "topic": null,
        "targets": null
      }
    }
  ]
}
```

(targets[] entries above are shown with null fields omitted for readability, however the real response includes every field on every target, null or not.)

### 4.2 Top-level / per-query fields

| Field | Type | Notes |
|---|---|---|
| placementID | int | Echoed back from the request. |
| queries[].adRequestId | int | Echoed back unchanged from the request. |
| queries[].status | "SUCCESS" \| "FAILURE" | Per-query status — a batch can be partial-success. |
| queries[].error | object \| null | Present only when status is "FAILURE". Shape: `{"code": "422"` *(row truncated in doc/paste)* |
| queries[].intent | object \| null | The extracted pCIV — see 4.3. |

### 4.3 intent (pCIV) object

| Field | Type | Notes |
|---|---|---|
| commercialIntent | bool | true if the query has any commercial relevance. If false, every field below is null. |
| topic | string \| null | One-line (≤10 word) summary of the query. |
| targets | array \| null | Up to 5 commercial targets. null when commercialIntent is false. |
| targets[].googleProductCategories | array of string \| null | Full taxonomy path strings (e.g. "Apparel & Accessories > Shoes"), not numeric IDs — resolved server-side from the LLM's integer output before being returned. Can contain more than one path when a product genuinely spans categories. |
| targets[].sellerNames | array of string \| null | Only populated when the user explicitly named a store. |
| targets[].priceMin / priceMax / priceTarget | number \| null | From "under $X" / "over $X" / "around $X" phrasing. |
| targets[].priceCurrency | string \| null | e.g. "USD". |
| targets[].productName | string \| null | Product type/model, brand and condition words stripped. |
| targets[].brand | string \| null | Explicit or confidently inferred. |
| targets[].gender | "male" \| "female" \| "unisex" \| null | Only from explicit query wording. |
| targets[].ageGroup | "newborn" \| "infant" \| "toddler" \| "kids" \| "adult" \| null | Only from explicit query wording. |
| targets[].condition | "new" \| "used" \| "refurbished" \| "open_box" \| "collectible" \| null | Never defaults to "new" — only set when stated. |

A handful of other fields (intentType, queryObjective, iabCategories, language, partialQuery, and several top-level flat fields) will always be null/false for this prompt — the response schema is shared with other prompt shapes this service also runs. Treat them as not applicable, not a bug.

## 5. Error handling

| HTTP status | Meaning |
|---|---|
| 200 | All queries in the batch succeeded. |
| 207 | Partial success — check each queries[].status individually. |
| 4xx | Request-level validation error (malformed body). |

Per-query failure shape:

```json
{
  "adRequestId": 44444,
  "qt": "...",
  "intent": null,
  "status": "FAILURE",
  "error": { "code": "422", "message": "LLM returned invalid taxonomy values for: gpc" }
}
```

422 = the LLM returned a GPC/IAB value outside the supported taxonomy. 500 = the LLM call failed or the response couldn't be parsed.
