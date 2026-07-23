# Review Gateway

Outbound artifacts awaiting Varun's review. Agents append; Varun marks ✅ approved / ❌ rejected / ✏️ edit-and-approve, then the acting agent executes and moves the entry to `runs/`.

Format per entry: date, agent, type (message draft / PR / ticket change), target, context, disposition — **but the draft body itself goes in its own plain-text file under `review/`** (Varun's preference, 2026-07-23: one `.txt` per response, exactly what gets pasted, nothing else — so `cat review/<file>.txt` shows it and copies trivially). Entry here links the path. Delete the `.txt` when the entry is disposed.

---

## 2026-07-23 — laptop — message draft — group DM C0BJPQHFFGC — GPC fix status + Winston cc

Context: Varun-directed (in-session): status reply now instead of the full bundle; tag Winston; say we're ready for the updated bundle. Regression PASS details in `runs/2026-07-22-pciv-taxonomy-gap.md`. Corrects the earlier ~3k/+800 token estimate to measured 3,563/+1,142. Branch `dev-taxonomy-full-l2` pushed to Bitbucket (PR not opened yet).

Body: `review/2026-07-23-gpc-fix-status-groupdm.txt`

⚠️ Winston is NOT a member of this group DM — the mention will render but won't notify him. Consider a separate DM to him or moving to a channel thread.
Open item (pre-merge): full L2 list includes Mature (773:Erotic|780:Weapons) — currently IN the branch; strip via one-line generator exclusion if desired.

**Disposition:** pending Varun — ✅ send / ❌ drop / ✏️ edit

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

Context: Varun asked for an independent investigation of Artem's 2.0-vs-3.0 result reversal. I verified his run-2 numbers from the attached CSVs, then ran controlled A/Bs against stage VSS. Full evidence: `runs/2026-07-23-ai1545-vespa-latency.md`.

Plain-language background for Varun (not part of the comment): many products in the Vespa index have no category set. When a 3.0 request filters by category, VSS deliberately generates "category starts with X **OR category is empty**" so those uncategorized products aren't excluded. Measured on stage: each half of that OR alone is fast (~20-23ms), but the combined OR — what production sends — is 63ms for a common category and 140ms for a rare one. And for rare categories the "starts with X" half matches ~nothing, so the whole returned page is uncategorized products: the slowest queries pay the most for a filter doing the least. This also explains the run-1/run-2 reversal: run 1's requests carried a brand filter (from a real ad), and narrow brand filters take a different, fast path in Vespa; run 2's were mostly category-without-brand — the slow shape.

**Draft comment** (v3 — scoped to what Varun can honestly own; no Vespa-internals claims): `review/2026-07-23-ai1545-jira-comment.txt`

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

## 2026-07-23 — laptop — ticket change — UPDATE on AI-1542/AI-1538 descriptions

Varun approved in-session ("super important to get in tickets"). **AI-1542: posted ✅** (via Rovo, 11:28 ET). **AI-1538: BLOCKED** — permission classifier denied the write 3× (Rovo ×2, curl ×1). Draft below stands, ready to paste into https://admarketplace.atlassian.net/browse/AI-1538 — or grant the permission and any session can post it. Entry for AI-1542 retired.

## 2026-07-23 — laptop — ticket creation drafts — the 2 missing integration tickets (Varun-directed: "this needs to be 1 or 2 integration tickets")

Context: AS-13400 accepts+logs `intent.*` but explicitly defers downstream transit; no ticket anywhere covers SSP actually *calling* the online pCIV service or consuming its output. Where extraction sits in the serving chain is undocumented. Recommend filing both under **AS-13384** (the empty "Update 3.0 API - Qwant Support integrate with pCIV" epic — this is literally its purpose), linked to AI-1213/AI-1538. They touch Pinkel's team's backlog, so best posted after a heads-up to Saksham/Pinkel (or in standup).

**Ticket 1 — "SSP: invoke online pCIV extraction from /di intent context" (project AS, epic AS-13384)**

> When /di receives Qwant 3.0 `intent` context (prompt + source ContextSummary + optional response — AS-13400), SSP should call the online pCIV service (AI-1538) to derive the CIV (chat.commerciality/type/topic + targets[]) that Qwant does not send.
>
> Decisions this ticket must land (currently written down nowhere):
> 1. **Blocking vs async**: does the ad request wait for extraction (must fit Qwant's ~3s Flash budget alongside SSP→DSP→AAS→VSS — see AS-13402, which does not yet inventory a pCIV hop), or is extraction async (fire-and-cache; current request falls back to prompt-as-qt per AI-1546, later requests in the chat/session benefit)?
> 2. Timeout + fallback semantics: extraction failure/timeout must never block ad serving — degrade to the AI-1546 qt fallback chain.
> 3. Payload mapping: `intent.*` → service request (incl. which surfaces call it — Flash may be prompt-only at launch per 7/17).
> 4. Caching key: session/chat-scoped reuse of extractions (chat.id / session.id are optional fields).
>
> Dependencies: AI-1538 (service exists), AS-13400 (fields accepted). Owner: SSP team (Pinkel) with AI team (Varun) on the service side.

**Ticket 2 — "Consume online pCIV output in retrieval/auction + launch A/B" (project AS or under AI-1171, judgment call)**

> Wire the online-pCIV service's extracted CIV into ad selection: qt selection for Vespa (interacts with AI-1546 fallback chains), GPC/category + price/brand matching in AAS (AI-1171 phase-1 scope), commerciality filter. Includes the launch A/B Dhaval proposed 7/17: extraction-on vs raw-prompt-as-qt, so the relevance lift of online extraction is measured from day one (experiment framework per exp-38 precedent).
>
> Dependencies: Ticket 1, AI-1546 (in review), AI-1171. Success criteria: extracted CIV measurably changes retrieval for ghost traffic; A/B dashboards show both arms.

**Disposition:** pending Varun — ✅ create both as drafted (say where) / ✏️ edit / ❌
