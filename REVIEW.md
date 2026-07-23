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
