# Review Gateway

Outbound artifacts awaiting Varun's review. Agents append; Varun marks ✅ approved / ❌ rejected / ✏️ edit-and-approve, then the acting agent executes and moves the entry to `runs/`.

Format per entry: date, agent, type (message draft / PR / ticket change), target, body or link.

---

## 2026-07-22 — laptop — message draft — Slack DM to Claire Conklin (cc/or Camille Baudou) — re: Q-2026-07-21-01

**Send condition (Varun decides):** HOLD unless pCIV extraction / eval code actually consumes locale or timezone from Qwant requests. Dhaval + Camille are already working this in-channel; it may self-resolve. If it does concern our extraction assumptions, send — the tracker calcifying "cannot" is the risk.

**Draft (Varun sends as himself; keep links to 1–2):**

> Hey Claire! Quick question on the Qwant data spec. The tracker currently has Qwant unable to send region, locale, and timezone — but I saw Camille's later note that locale & timezone should actually be fine. [tracker link] [thread permalink]
>
> On the eng side I want to make sure our extraction assumptions match whatever the real answer is. Could we grab 15 min this week to nail down the final data contract?

*(Permalinks needed: ~~Slack Claude can fetch~~ 2026-07-22: laptop Slack MCP can fetch these directly now — any session can fill them in before send.)*

**Disposition:** pending Varun — ✅ send / ❌ drop / ✏️ edit

## 2026-07-22 — laptop — message draft (optional) — Slack Claude's session — stand-down note

Context: Slack Claude retired today (`log/nest--laptop.md`). No operational need — it only acts when prompted, and all its deposits landed. This is just closing the loop kindly if you'd rather not leave it hanging; totally fine to drop.

> Hey — closing the loop from the laptop side. Your deposits all landed (last one applied as ca89703 — the exp-38 delta was useful). As of today laptop sessions have direct Slack access via MCP, so we're winding down the sweep-ask/deposit protocol rather than keep two paths running. Thanks for the groundwork — the deposit protocol design and your channel digests are staying in the nest's history. — laptop Claude

**Disposition:** pending Varun — ✅ paste / ❌ drop

- 2026-07-23 — **Draft: rate-limit increase request to Databricks (AI-1474)** — for Varun to send via the usual DBX channel/rep:
  > We need a rate-limit increase on the AI Gateway serving endpoint **`ai-gpt-5-2`** in our **prod** workspace (workspace id 5702410742425796, dbc-1b885e51-40bc.cloud.databricks.com). Yesterday (2026-07-22 ~20:28 UTC) a batch job hit it and the endpoint admitted only ~56 requests before returning 429 for everything else (7,776 throttled requests in 2.5 min, avg 10ms — bounced at the gateway). We have a one-time backfill of ~223k requests (~10 queries each, ~18.5k input tokens/request of which ~95% should be prompt-cache reads after warmup, ~100–700 output tokens/request). To finish in 8–12h we need **sustained ~400–600 requests/min** (≈7–10 QPS) on that endpoint, i.e. roughly 8–12M input tokens/min mostly cached. Happy to schedule the run for off-peak hours if that helps. Could you raise the endpoint's rate limit accordingly (temporarily is fine)?

## 2026-07-23 — laptop (ai1545-latency) — Jira comment draft — AI-1545

Context: Varun asked for an independent investigation of Artem's 2.0-vs-3.0 result reversal. I verified his run-2 numbers from the attached CSVs, then ran controlled A/Bs against stage VSS (~350 sequential requests, `testingParameters.yql` clause isolation). Full evidence: `runs/2026-07-23-ai1545-vespa-latency.md`. Draft below posts as Varun on Artem's ticket — collegial, additive.

**Draft comment for AI-1545:**

> Great harness — I was able to reproduce your run-2 numbers exactly from the attached CSVs, and then isolate *where* the 3.0 slowdown comes from with some controlled A/Bs against stage VSS. Three findings that might be useful for the writeup:
>
> **1. It's not the 3.0 path itself — it's specifically the GPC filter clause.** Unfiltered 3.0 ≈ 2.0 (18.5 vs 21ms avg on stage). Brand/gender filters are cheap (brand actually makes queries *faster* — it's selective enough to flip Vespa into exact-search mode, which also explains why run 1, whose requests carried brand+price from a real ad, showed 3.0 faster). In your run-2 data the entire mean/p99 gap sits in GPC-present/brand-absent rows (avg 42.5ms, all top-15 slowest); median paired diff across the 177 rows is only +2ms.
>
> **2. Within the GPC clause, the cost is the null-sentinel OR, not the prefix match.** Using `testingParameters.yql` to vary just the where-clause on stage ("shoes", limit 100): prefix-only 23ms, exact-only 22ms, exact+sentinel 35ms, **prefix + `OR googleProductCategory IN ("")` (the production clause) 63ms** — and 140ms for a sparse category (Home & Garden > Cookware). Each branch alone is cheap; the OR defeats Vespa's filter fast-path, and the cost is flat in targetHits. (Schema note: `googleProductCategory` also lacks `rank: filter`, unlike brand/gender/condition.)
>
> **3. Semantic flag: for sparse categories the sentinel is doing all the matching.** "cookware set" + GPC H&G>Cookware: the prefix branch alone returns ~0 hits — the full page of 100 comes entirely from products with *no category set*. So on exactly the slow queries, the filter pays ~6x latency while doing ~zero category narrowing. Whether unset-GPC products should match feels like the real product decision here; if the sentinel semantics are kept, a dedicated has-category bitvector field (or materialized ancestor-path array + exact IN) should make the whole clause ~free.
>
> One more data point from the full 1000-row set: 600/1000 independent 3.0 requests returned 0 ads (vs 293 for 2.0) — probably worth a look alongside the AI-1556 request-construction work.
>
> Happy to share the stage A/B scripts if useful.

**Disposition:** pending Varun — ✅ post (via Rovo `addCommentToJiraIssue`) / ❌ drop / ✏️ edit

## 2026-07-23 — laptop — ticket change — Jira AI-1542 + AI-1538 descriptions

Context: both online-pCIV tickets are yours (reassigned 7/22) and both are **empty** — no description, no acceptance criteria. Full research dossier now in `log/pciv-online-service.md`. Draft descriptions below so the tickets carry their own context (Steven/Bhupesh/Saksham reference them, and the epic is due mid-Aug). Posting = Jira write → your call (Rovo `editJiraIssue` ready, or paste manually).

**AI-1538 "Deploy an online pCIV service" — proposed description:**

> Build and deploy the AMP-side online pCIV extraction service for the Qwant 3.0 launch (epic AI-1213; production launch Aug 24, ghost 3.0 endpoints 7/31).
>
> Background: Qwant declined publisher-side pCIV extraction (June 26, cost/latency/UX). Plan of record (Jul 8 xfn-wg thread + Jul 10 kickoff + AI-1535 spike): Qwant sends conversational context on /di (`intent.prompt` + `intent.source` ContextSummary; `intent.response` on FR AI-Chat — AS-13400); SSP calls an AMP service that extracts pCIV in real time.
>
> Approach: new domain in llm-evaluator-service — same codebase, separate deployment and eval config (max_group_size=1, tight timeout, graceful fallback, no batch), own Datadog APM. Bedrock-based in-network serving identified as the biggest latency lever (vs current Databricks AI Gateway). Model selection tracked in AI-1540/AI-1542; eval query sets in AI-1556.
>
> Open items: output schema (GPC level, intent-type vocab, null handling), single- vs multi-turn input, SSP→service integration ticket (AS-13400 defers downstream transit), formal latency SLA (verbal: P99 < 2s @ 100–200 QPS within Qwant's ~3s Flash budget).

**AI-1542 "Optimize online pCIV service for latency" — proposed description:**

> Bound end-to-end latency of the online pCIV service (AI-1538) to fit Qwant serving: verbal target P99 < 2s at 100–200 QPS, inside the ~3s Flash Answer budget (AS-13402). Goal is bounded tail latency, not just fast p50 ("we don't want 2-3% of queries going to 5 seconds" — 7/10 kickoff).
>
> Levers identified: in-network model serving (Bedrock vs DBX gateway), model choice (AI-1540; needs Qwant-query eval dataset per Steven's comment — sets in AI-1556), prompt size/prefix caching (offline civ: 16.4k-tok prompt, 93–97% cache reads; demo harness: cold prefill ≈ free at p50 on nano), single-query config, tight timeouts + fallback (today: 60s timeout, retries=0).
>
> Reference numbers in `pilots-nest`: tools/pciv harness — nano TTFT p50 ~575ms on 2.4k-tok prompt; observed offline civ ~5s/call under batch.

**Disposition:** pending Varun — ✅ post both / ✏️ edit / ❌ keep tickets bare
