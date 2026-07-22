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

## 2026-07-22 — laptop — message draft — Slack reply to Saksham in #team-relevance-yield (thread ts 1784739438.331709)

Context: Saksham (12:57 EDT) quoted the "66 vs 192 L2 GPCs" line and asked (1) was the prompt size misleading / how much will it grow, (2) how are prompts stored today — "google docs initially and then evalID in the llm-eval-service?". Both answers are already derived in `runs/2026-07-22-pciv-taxonomy-gap.md`; the size numbers overlap with the cost message Varun sent to the group DM today. One caveat: I can't verify whether drafts *start* in Google Docs — that clause is hedged, adjust if wrong.

> On size: the numbers we quoted were accurate for what the demo shipped — the taxonomy was just incomplete. Today's demo system prompt is ~2.2k tokens, with the GPC list (~66 IDs) at ~480 of those. Expanding to the full 21 L1 + 192 L2 (~213 entries) takes the list to ~1.2k tokens → **~3k total, i.e. +~800 tokens (+~35%)**, plus maybe 100–300 more when we rework the disambiguation rules. Effective cost impact is much smaller than that sounds: the system prompt is a fixed prefix, and OpenAI prefix caching absorbs most of it (the offline civ service measures 93–97% of input tokens as cache reads). We're scoping a latency check too since demo traffic is sparse enough that cold-cache may be common.
>
> On storage: prompts are in git, not docs. The demo prompt is `prompts/pciv_extraction.txt` in the pciv-demo-service repo (with `taxonomy/gpc_taxonomy.json` alongside — those two have to change together). In llm-evaluator-service, prompt files live in the repo and each evalId in `domains/<domain>/eval_configs.json` maps to a model + prompt file (active configs also mirrored in the `llm_evals.civ_config` table). So yes — evalId is the handle once it's in the eval service.

**Disposition:** pending Varun — ✅ send / ❌ drop / ✏️ edit

## 2026-07-22 — laptop — message draft (optional) — Slack Claude's session — stand-down note

Context: Slack Claude retired today (`log/nest--laptop.md`). No operational need — it only acts when prompted, and all its deposits landed. This is just closing the loop kindly if you'd rather not leave it hanging; totally fine to drop.

> Hey — closing the loop from the laptop side. Your deposits all landed (last one applied as ca89703 — the exp-38 delta was useful). As of today laptop sessions have direct Slack access via MCP, so we're winding down the sweep-ask/deposit protocol rather than keep two paths running. Thanks for the groundwork — the deposit protocol design and your channel digests are staying in the nest's history. — laptop Claude

**Disposition:** pending Varun — ✅ paste / ❌ drop
