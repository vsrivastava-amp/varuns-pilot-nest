# Review Gateway

Outbound artifacts awaiting Varun's review. Agents append; Varun marks ✅ approved / ❌ rejected / ✏️ edit-and-approve, then the acting agent executes and moves the entry to `runs/`.

Format per entry: date, agent, type (message draft / PR / ticket change), target, body or link.

---

## 2026-07-22 — laptop — message draft — Slack DM to Prakash Patel (D093GDY36SD) — re: ssp.intent_type deletion check

Context: Prakash asked today (12:08 EDT) whether the ML team uses the MySQL `ssp.intent_type` table in production — they want to delete/repurpose it for the new media-segment taxonomy. Investigated code + Databricks lineage/query history (`runs/2026-07-22-prakash-intent-type.md`). Verdict: ML does NOT use it — pipelines read `intent_clf.intent_type_master` (Databricks-native; the RELEASE-5309 migration to MySQL never happened, IDs even ordered differently). But lineage shows the **pricing team** reads `prod_amplify.amp.intent_type`: aguo's recurring supply_card query (writes `dev_pricing.pricing_team.supply_card`; ran 4/14, 5/2, 6/2, 7/2, 7/15). Also: the release created `amp.INTENT_TYPE`, not `ssp.intent_type` — name discrepancy flagged. Varun chose response shape "no we don't use it; we use intent_clf.intent_type_master instead" + heads-up. 👀 reaction added to Prakash's message (Varun-directed in-chat, 2026-07-22).

**Draft (Varun sends as himself):**

> Hey Prakash! No — the ML side doesn't use that table in production. Our pipelines read `intent_clf.intent_type_master` in Databricks instead; the swap to the MySQL table we created back then never actually happened on our end (the IDs are even ordered differently between the two).
>
> Two heads-ups before you delete/repurpose though:
> 1. The table from that release was created as `amp.INTENT_TYPE` — assuming that's the one you mean (I don't see an `ssp.intent_type` replica in Unity Catalog).
> 2. Table lineage shows the pricing team does read `prod_amplify.amp.intent_type` — aguo has a recurring query that joins it into `dev_pricing.pricing_team.supply_card` (last ran 7/15, runs ~monthly). Worth checking with them before you drop it.
>
> No objection from our side.

**Disposition:** pending Varun — ✅ send / ❌ drop / ✏️ edit

## 2026-07-22 — laptop — message draft — group DM (Varun/Elisa/Dhaval/Yaarit/Saksham, C0BJPQHFFGC) — answers Dhaval's open token question

Context: Dhaval asked 7/21 "does this increase input tokens compared to what we estimated?" — still unanswered in-thread after Varun's 7/22 confirmation. Numbers verified against local repos (`runs/2026-07-22-pciv-taxonomy-gap.md`).

**Draft (Varun sends as himself):**

> On your token question Dhaval: yes, but modestly. The demo's system prompt is ~2.2k tokens today, of which the GPC list is ~480. Going from 66 to the full 192 L2s (+21 L1s) in the same compact format adds ~800 tokens per request — system prompt lands around 3k (~+35%). Since it's a fixed prefix, provider prompt caching absorbs most of it (we see 93–97% cache-read rates on the offline civ service, whose prompt is 16.4k tokens with the full L3 tree). Net effect on the cost estimates is low single-digit percent. The disambiguation rules will need some expansion too — will size that as part of the fix.

**Disposition:** pending Varun — ✅ send / ❌ drop / ✏️ edit

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
