# 2026-07-27 — Intent Identifier prod monitors: two separate problems (session: ii-monitors)

- 2026-07-27 Provenance: findings originally pasted in-chat by Varun from an earlier session's Datadog investigation. **This session verified them directly against Datadog** (connector handshake completed by Varun mid-session). Everything below is first-hand unless marked otherwise. All timestamps **UTC** (Datadog); this machine is Pacific.
- 2026-07-27 Nothing about `intent-identifier-service` or either monitor existed in the nest before this file. Datadog access facts → `playbooks/datadog.md` (new).

## Monitor facts (verified, 2026-07-27)

Both monitors: created 2025-11-20 by **Ivan Trichev**, both **`managedBy:Terraform`**, both tagged
`service:intent-identifier-service`, both notify `@slack-prod-relevance-yield-alerts` +
`sysops@admarketplace.com` + `engine@admarketplace.com`. Both status OK at time of reading.

**`managedBy:Terraform` is the load-bearing detail for any fix** — these monitors are not
UI-editable in a durable way. A console edit gets reverted on the next apply. The fix path is a PR
against whatever Terraform module owns them (owner not yet identified — see Open below).

### 238419175 — "Intent Identifier Service - timeout logs" (`log alert`)

```
logs("service:(ssp-engine) env:prod datacenter:ric1 status:error
      \"Unexpected error during intent identification\"
      @stack_trace:(*HttpTimeoutException* *IntentIdentifierControllerApi*)")
  .index("*").rollup("count").last("5m") > 5
```

- Nuance the original report flattened: the two exception terms are **wildcard matches on the
  `@stack_trace` attribute**, not free-text message search. Reproducing the query without
  `@stack_trace:` and the `*`s gives different counts.
- Recovery at `<4` (per the message body). Counts **log lines** — not requests, users, or traffic share.

### 238419172 — "Intent Identifier Service - P95 Latency" (`query alert`)

```
avg(last_5m):p95:trace.servlet.request{env:prod,service:intent-identifier-service,
    span.kind:server,resource_name:post_/api/v1/identify-intents} > 10
```

- **The unit bug is confirmed.** The Datadog metric API returns `"unit":"seconds"` for this metric,
  so `> 10` is ten *seconds*. Message text claims `>10ms`; recovery text claims `<8ms`. Both are wrong
  by 1000×, and the monitor is effectively inert.
- Second defect confirmed: `avg(last_5m):p95:` averages Datadog's ~10-second p95 buckets across five
  minutes. It is not one p95 over the window's requests.

## Volume (verified)

7-day window ending 2026-07-27 ~17:00 UTC, monitor 238419175's exact query:

| Day (UTC) | Timeout logs |
|---|---|
| 07-20 | 734 |
| 07-21 | 510 |
| 07-22 | 611 |
| 07-23 | 751 |
| 07-24 | 133 |
| 07-25 | 77 |
| 07-26 | 679 |
| 07-27 | 898 (partial day) |
| **total** | **4,393** |

Matches the earlier report's ~4,394 (one-log boundary difference). **07-27 is the highest day in the
window and was not over when measured** — the trend is up, not flat.

### Alert episodes (verified via `search_datadog_events`)

**18 episodes, 36 transitions**, cleanly paired. Median duration **5 min**, longest **20 min**
(07-23 17:58→18:18). This confirms the earlier report's 18 / ~5 min / ~20 min exactly.
Episodes by day: 07-21 ×4, 07-22 ×2, 07-23 ×5, 07-24 ×1, **07-25 ×0**, 07-26 ×2, 07-27 ×4.

- **13 of 18 episodes lasted exactly 5 minutes** = the monitor's own evaluation window. Those are
  single-evaluation blips: count crossed 5, fell back immediately.
- **Duration is not a severity proxy.** The 07-27 14:50 burst (683 timeouts, ~9% of that minute's
  traffic) produced a 5-minute episode — the same duration as episodes containing six timeouts.
  Anyone triaging by episode length will mis-rank these.
- **The recovery message text is a third documentation defect.** The monitor says "recovered to
  normal levels (<4)"; the alert bodies show Datadog recovers at **≤5**. There is no separate
  recovery threshold configured.
- How to get this: `search_datadog_events(query="\"<monitor name>\"", from="now-7d",
  sort="timestamp")`. `monitor_id:<id>` returns nothing — query the **title string** instead.
  Watch for truncation: the first page silently capped at 30 of 36 events, which would have
  produced 15 episodes instead of 18. Check `<count>` against `<displayed_items>` and page with
  `start_at`.

## The correction: two distinct failure modes, and the p95 fix does not detect either burst

Per-hour and per-minute decomposition changes the picture the aggregate counts gave:

- **07-27 14:00 UTC hour = 692 logs, of which 683 landed in the single minute 14:50.** The rest of
  that hour is 1–2/min.
- **07-26 08:00 UTC hour = 581 logs**, same shape, burst minute 08:46.
- Every other hour in the week is ≤61, mostly single digits.

So the week is **two one-minute bursts plus a steady 1–2/min background drip**, not a diffuse problem.

Latency percentiles at those exact minutes (`trace.servlet.request`, seconds):

| | p95 baseline (7d) | p99 baseline (7d) | 07-26 08:46 | 07-27 14:50 |
|---|---|---|---|---|
| p95 | 0.0136–0.0157 | — | **0.0154** | **0.0178** |
| p99 | — | 0.0162–0.0201 | **0.0254** | **0.0254** |
| max | 0.0386–0.0571 typical | — | **6.087** | **0.410** |

**The proposed replacement monitor (`p95 … > 0.020`) would not have fired for either burst.** On
07-26 at 08:46, while 581 timeouts/hour were firing and one request took 6.09 seconds, p95 was
0.0154 — indistinguishable from baseline. On 07-27 at 14:50 p95 reached only 0.0178, still under
0.020. And `avg(last_5m)` dilutes a one-minute spike roughly 5×, pushing it further from any
threshold. p95 is the wrong percentile *and* `avg` is the wrong time aggregator for this failure.

What the numbers say instead:

- **Background drip** — baseline `max` runs 22–57 ms, i.e. **routinely above SSP's 30 ms deadline**.
  That is the mechanism behind the constant 1–2/min. The earlier report's fix #2 (raise the SSP
  timeout to 60–75 ms) targets exactly this and is well-aimed: it recovers the routine tail.
- **Bursts** — a multi-second stall (6.09 s on 07-26). **Raising the deadline to 75 ms cannot save a
  6-second request.** Only fix #1 (replicas 3→4) and fix #3 (fail open, do not retry
  `HttpTimeoutException`) address bursts. A 6-second stop-the-world on a service whose p50 is 4–5 ms
  reads like GC pause, pod restart, or thread-pool stall — not latency creep.
- Burst scale: 683 timeouts against ~7,500 req/min ≈ **9% of that minute's traffic**. Server-side
  hits dipped to 5,648 from ~7,500 in the same minute.
- `trace.servlet.request.errors` returned **no series** for this resource — consistent with the
  reported mechanism (SSP closes the stream; the server never gets to return, so nothing is recorded
  as a server-side error). The absence is itself evidence for the diagnosis.

### Revised recommendation for 238419172

Fixing the unit bug is right, but do not sell a p95 monitor as an early warning for the timeouts.
Two separate jobs:

1. **238419172 = sustained-regression detector.** `p95 > 0.020` is a defensible threshold on the
   data (7-day p95 max is 0.0157, so ~27% headroom, no expected noise) — as long as the message says
   what it means: "the average of Intent Identifier's ~10-second p95 latency measurements exceeded
   20 ms over the last minute." It will catch a real latency regression. It will not catch bursts.
2. **Burst detection needs p99 with `max`, not p95 with `avg`.** p99 reached 0.0254 in both bursts
   against a 0.0162–0.0201 baseline; something like `max(last_5m):p99:… > 0.023` catches both events
   with margin. Note the baseline already touches 0.0201, so a p99 threshold of 0.020 would be noisy
   — 0.023 is the workable floor.
3. **238419175 remains the only true impact signal.** Keep it. Rate-normalizing it
   (`timeouts / total calls`) is still the right measurement for judging any fix.

## Source-verified facts (ssp-engine master @ 1e3b192, read 2026-07-27)

Cloned to scratchpad per `playbooks/bitbucket.md`. These resolve hedges that the earlier report and
my first pass had to leave open.

- **The retry premise is confirmed, and it is worse than the report guessed.**
  `IntentIdentifierServiceConfiguration` builds the Resilience4j retry with
  `maxAttempts(retries + 1)` and **`waitDuration(Duration.ofSeconds(0))`** — zero backoff.
  `retryExceptions(IOException.class, IntentIdentifierServiceCallException.class)`, and
  `java.net.http.HttpTimeoutException extends IOException`, so **timeouts do retry**, immediately.
  `IntentFilter.isRetryable` independently returns true for any `IOException`.
- **Config defaults** (`application.yml`): `read-timeout-millis` **30** (env
  `APP_INTENT_IDENTIFIER_SERVICE_READ_TIMEOUT_MILLIS`, legacy
  `APP_INTENT_IDENTIFIER_SERVICE_TIMEOUT_MILLIS` honored as fallback "for one release cycle"),
  `connect-timeout-millis` **1000**, `retries` **1**. Prod may override via env; I did not read the
  deployed env, but the observed 30.20 ms abandon matches the default.
- **So 1 log line ≈ 2 abandoned calls.** `retries: 1` → `maxAttempts(2)`. `IntentFilter` logs
  "Unexpected error during intent identification" **once per request** from the outer catch, after
  both attempts fail. The 683 logs at 07-27 14:50 therefore represent ~1,366 calls into a stalled
  service. **The monitor undercounts load on the dependency by 2×.**
- **It does not currently fail open.** The catch returns
  `Validation.invalid(EnrichmentError.ErrorType.exception)`, an error result — not the empty/no-intent
  fallback the earlier report recommended. That fix is a real behavior change, not a no-op. How the
  caller treats `ErrorType.exception` is **not traced** — open.
- **A terminal-outcome metric already exists**, so the report's "record a terminal outcome metric" is
  already done. `MetricService.countIntentIdentifierError` increments **`sspEngine.intent.identifier.errors`**
  with a `kind:` tag, once per request. Kinds: `request_timeout`, `connect_timeout`, `stream_exhausted`
  ("too many concurrent streams"), `io_error`, `http_4xx`, `http_5xx`, `null_response`,
  `null_query_term_results`, `service_error`, `other`. Also `external.call` timing.
  **Verified live in Datadog**, 7d ric1: request_timeout 3,657 · stream_exhausted 341 ·
  connect_timeout 96 · io_error 31 · service_error 14. At 07-27 14:50, `kind:request_timeout` = **683**,
  matching the log count exactly. **The rate monitor is buildable today with no new instrumentation.**
- **The monitor's filter is an OR, and it over-matches.** `@stack_trace:(*A* *B*)` — the space inside
  the parentheses is OR, not AND. Proof: the monitor's own filter returns **4,393**; an explicit
  `@stack_trace:*HttpTimeoutException* AND @stack_trace:*IntentIdentifierControllerApi*` returns
  **3,681**; `*HttpTimeoutException*` alone also returns **3,681**. So ~712 logs (~16%) are
  non-timeout intent-identification failures counted by a monitor named "timeout logs".
- **Refuted hypothesis:** I guessed the 341 `stream_exhausted` errors were zero-backoff retries
  exhausting HTTP/2 streams during bursts. `kind:stream_exhausted` returned **no series** across the
  07-27 burst window. Not the burst mechanism. Left out of the draft.
- **Terraform module not found.** `admarketplace/terraform` exists but holds only ec2/kafka/LB
  resources across `ric1/` + `pdx1/` (no `datadog_monitor` anywhere in a depth-5 clone).
  `admarketplace/terraform-modules` also exists and is unexamined. Still open.

## Jira placement (verified 2026-07-27)

- **AI-1543 "Fix Intent Identifier Service - timeout logs alert"** — the home for Problem 1. Title is
  verbatim the monitor name. Assignee **Bhupesh Hada**, reporter Saksham Bhatla, status **Not
  Started**, **description empty, zero comments**. Varun redirected here from AI-1542 (in-chat
  2026-07-27).
- Epic **AI-1367 "ML/AI: Emerging OpEx Issues"** (In Progress) is explicitly the alert-hygiene epic:
  siblings are AI-1388 (SASS QPS anomaly alerts), AI-1424 (elme-yield alerts), AI-1427
  (advertiser-ctr-service alerts), AI-1559 (elme-yield monitoring gaps), AI-1315 (llm-evaluator
  logging gaps). Bhupesh already owns AI-1426 + AI-1429 in it — observability is the right lane.
- **Problem 2 (monitor 238419172) has NO ticket.** `text ~ "Intent Identifier"` across all projects
  returns nothing for a P95/latency alert. It needs one, and AI-1367 is the right epic.
- **Scoping risk worth Varun's/Saksham's attention**: AI-1543 is titled "fix the *alert*". The alert
  is accurate and is the only signal tracking real impact. If the ticket is executed as threshold
  tuning, both one-minute bursts get hidden. Raised as a question in the draft rather than asserted —
  it is Bhupesh's ticket.
- Prior art for verifying the retry premise: **AS-11453 "SSP Engine calls intent-identifier-service"**
  and **AS-11454** (both Done, Alexander Nikiforov) — that is where the 30 ms deadline and any retry
  behavior were implemented. **AS-11523** (Viktor Strokan, Done) sized prod hardware, so the 3-replica
  figure likely originates there.

## Disposition

- Jira comment draft for AI-1543 → `review/2026-07-27-ai1543-intent-identifier-monitors-jira.txt`
  (pending Varun). Written in the **discussion mood** per `playbooks/jira.md` — Bhupesh's ticket, so
  observations + questions, not fix directives. The three remediation candidates stay in this run file
  and in the full report; they are not pushed at the ticket owner.

## Open / pending Varun

- **Terraform owner unidentified.** Both monitors are `managedBy:Terraform`; I did not locate the
  module. Needs a repo search (candidates: an infra/terraform repo not yet in
  `playbooks/bitbucket.md`'s inventory) before any monitor change can be drafted.
- **Per-pod attribution unavailable from this metric.** `trace.servlet.request` carries no
  `pod_name` / `host` / `kube_pod_name` tags — all three return `N/A`. So I could **not** determine
  whether the 6.09 s stall hit one replica or all of them. That question decides how much fix #1
  (replicas 3→4) actually buys, so it matters. Needs APM spans (which carry pod tags) or k8s
  metrics — a follow-up, not a blocker on the other fixes.
- **Where this service belongs in the nest.** Still no `map/` file and no repo row in
  `playbooks/bitbucket.md`. If it is on the pCIV live path (SSP `/di` → intent identification) it
  likely belongs with `map/pciv-live-integration.md` and may attach to **AI-1542 (latency, Varun)** —
  unconfirmed, not assumed.
- **All fixes remain outbound and undrafted**: ssp-engine timeout config, k8s replica count, retry
  behavior, and a Terraform-managed prod monitor. Nothing was executed or drafted this session.
  Read-only throughout (monitor reads, log aggregations, metric queries).
