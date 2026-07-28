# Datadog playbook

*(Living reference. Started 2026-07-27.)*

## Auth — connector, not keys

Datadog is a **claude.ai MCP connector**, not an API-key integration. Nothing to
provision; nothing to put in `.env`. Same shape as Calendar/Gmail/Drive/Rovo
(`playbooks/google.md`):

- Server: `claudeai-proxy` at `https://mcp.datadoghq.com/api/unstable/mcp-server/mcp`.
- Varun runs `/mcp` in the session and selects **"claude.ai Datadog"**. OAuth in
  the browser. **Human-gated — never automate** (guardrail #3).
- Read-only by policy (guardrail #8). Monitor edits, mutes, and downtimes appear
  *as Varun* → `review/` drafts only, even though the tools may permit writes.

**The un-handshaken state looks like a missing capability.** Before the
handshake, the only exposed tools are `mcp__claude_ai_Datadog__authenticate` and
`…__complete_authentication`; calling `authenticate` just returns "Ask the user
to run /mcp and select 'claude.ai Datadog'". This burned one session
(2026-07-27) into recording "Datadog access pending" when the connector was
sitting right there. Ask for the handshake before concluding anything.

- Scope-checkbox gotcha (hit on the Google connectors 7/22, assume it applies
  here): consent can complete with permission boxes unticked, after which every
  call fails on auth scopes. Fix = disconnect/reconnect via `/mcp`, tick boxes.
- Tool schemas are deferred: `ToolSearch("+datadog monitor")` to load them.
- Headless/cron caveat: interactively-authenticated connectors may be absent in
  scheduled runs. Verify before a routine depends on Datadog.

## Alert review

The Datadog→PagerDuty alert-review workflow (which Slack channels carry the raw
stream vs. the incident stream, how to group warn→triggered→recovered into one
incident, how to tell *acknowledged* from *recovered* from *root-caused*) is
written up in **`playbooks/vespa.md`**. It is not Vespa-specific — use it for any
monitor. Move it here on the next steward pass.

## Monitor inventory (as encountered; extend as sessions touch more)

| ID | Name / signal | Notes |
|---|---|---|
| `238419175` | "Intent Identifier Service - timeout logs" | **Log-count** monitor (>5 events / rolling 5 min), not a metric monitor. Counts log lines, not requests or traffic share. Terms match `@stack_trace:(*…*)`, not free text. `managedBy:Terraform`. `runs/2026-07-27-intent-identifier-monitors.md` |
| `238419172` | "Intent Identifier Service - P95 Latency" | **Misconfigured** — message says 10 ms / recovery 8 ms, query says `> 10` on a *seconds* metric = 10 s, so it cannot fire. `managedBy:Terraform`. Also the wrong percentile for the burst it is meant to warn about — same run file. |
| `263399495` | Vespa Search Service timeouts | Worked example in `playbooks/vespa.md` (2026-07-24 RIC1/PDX1 incidents → `SUPPORT-808`). |

## Tool incantations (verified 2026-07-27, first working session)

Datadog is **UTC**; this machine is Pacific — say which in any write-up.

Skill discovery first, as the server instructs: `list_datadog_skills(query=…)` plus a
direct `load_datadog_skill`. Worth it — `datadog/logs` documents the
`extra_fields` → `extra_columns` translation that is otherwise pure trial and error.
Useful skills: `datadog/logs`, `datadog/incidents-and-alerting` (monitors live here,
despite the name), `generic` (query syntax across all data types).

- **Read a monitor by ID**: `search_datadog_monitors(query="id:238419175",
  include_tags=["*"])`. Returns the raw query, message, type, status, creator, and tags.
  `include_tags` must be an array — a bare `*` fails JSON parsing.
- **Count / aggregate logs**: `analyze_datadog_logs` with `filter` (Datadog query syntax)
  + `sql_query` (DDSQL over a virtual `logs` table). Time-bucket with
  `DATE_TRUNC('day'|'hour'|'minute', timestamp)`. **Never** add a `WHERE timestamp`
  clause — the table already holds only the `from`/`to` window. Aliases can't be reused
  in `GROUP BY`; repeat the full expression.
- **Raw logs / attribute discovery**: `search_datadog_logs` with `extra_fields:['*']`.
  Use `analyze_datadog_logs` for anything numeric.
- **Metrics**: `get_datadog_metric(queries=[…], raw_data=true, interval=60000)`.
  `raw_data=true` gives every point; without it you get 20 coarse bins that will hide a
  one-minute event. Multiple queries per call is fine and cheaper than several calls.
  The response includes the metric's `unit` — **read it** (see gotchas).
- **Grouping**: `by {tag}` inside the query string. A `scope` of `tag:N/A` in the response
  means the metric isn't tagged that way, not that the value is missing.
- **Monitor firing history** (episode counts + durations): `search_datadog_events(query="\"<exact
  monitor name>\"", from="now-7d", sort="timestamp")`. Events carry `[Triggered]` / `[Recovered]`
  titles; pair them in order to get episodes. **`monitor_id:<id>` matches nothing** — query the
  title string. Two traps: (a) the response **silently truncates** — compare `<count>` to
  `<displayed_items>` and page with `start_at`, or you will undercount episodes; (b) a big result
  spills to a file on disk, so parse it with grep/python rather than re-running with more tokens.

## Gotchas

- **Metric units are seconds.** `trace.servlet.request` p95 thresholds are
  seconds — `> 10` is ten seconds, not ten milliseconds. A 20 ms threshold is
  `> 0.020`. Misreading this produced monitor 238419172's inert threshold. The
  metric API returns `"unit":"seconds"` in the response — check it before you
  believe any threshold or monitor message.
- **`avg(last_5m):p95:` is not a 5-minute p95.** It averages Datadog's
  approximately 10-second p95 buckets across the window. Any monitor message
  must describe it that way, or on-call reads it as a true window p95.
- **`avg(last_Xm)` dilutes short spikes by roughly X.** A one-minute incident inside a
  five-minute average largely vanishes. For burst detection use `max(last_5m)`.
- **Percentile choice decides what you can see.** On intent-identifier, p95 stayed inside
  its normal band through a burst that timed out 683 requests in one minute and included a
  6-second request; p99 moved clearly. Check that the percentile you monitor actually
  responds to the incident you care about — verify against a known past incident before
  trusting a threshold.
- **Log-count monitors don't measure impact.** Episode counts and log counts both
  scale with traffic and with retry behavior. For impact, build a rate:
  `failures / total calls`, grouped by region and pod.
- **`managedBy:Terraform`** on a monitor means console edits get reverted on the next
  apply. Check the tag before proposing any monitor change; the fix is a Terraform PR.
- **APM trace metrics may carry no pod/host tags.** `trace.servlet.request` returns `N/A`
  for `pod_name`, `host`, and `kube_pod_name`, so you cannot attribute a latency spike to a
  replica from the metric alone — go to spans or k8s metrics for that.
- **Aggregate counts hide burst structure.** Always decompose by hour, then by minute,
  before characterizing a failure. A "4,393 logs/week, 18 episodes" problem turned out to be
  two one-minute events plus a low background drip — with different root causes and
  different fixes.
- **A space inside `@field:(a b)` is OR, not AND.** Verified 2026-07-27: monitor 238419175's
  `@stack_trace:(*HttpTimeoutException* *IntentIdentifierControllerApi*)` returns 4,393 logs, while
  the explicit `@stack_trace:*A* AND @stack_trace:*B*` returns 3,681. A monitor written this way
  counts more than its name implies. To check any monitor for this, re-run its filter with explicit
  `AND` and compare counts.
- **When APM spans are missing, k8s metrics often answer the same question.** `trace.*` metrics carry
  no pod tags and `search_datadog_spans` returned 0 spans for `intent-identifier-service`, so per-pod
  latency attribution was impossible. But `kubernetes.containers.restarts` and
  `kubernetes.memory.usage` grouped `by {pod_name}` worked, and pinned a latency burst to a pod restart
  at 1-minute resolution. Reach for `search_datadog_k8s_resources` (replica counts, restart counts,
  pod age) + `describe_datadog_k8s_resource` (limits/requests/QoS) before concluding a question is
  unanswerable.
- **`container.memory.oom_events` distinguishes an OOM kill from a liveness restart.** A pod pinned at
  99.2% of its memory limit that then restarts *looks* like an OOM kill and is not necessarily one —
  oom_events was 0 across the week. Check the metric before writing "OOMKilled" anywhere.
- **Check for an existing app metric before proposing new instrumentation.** `search_datadog_metrics`
  with `name_filter` found `sspEngine.intent.identifier.errors` (a per-request counter with a `kind:`
  tag) already live — which made a recommended "add a terminal outcome metric" redundant. App metrics
  are often prefixed by service (`sspEngine.`, `intent_identifier_service.`), so search the bare
  suffix, not the code constant.
