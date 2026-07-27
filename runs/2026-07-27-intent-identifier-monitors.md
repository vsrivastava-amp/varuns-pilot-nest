# 2026-07-27 — Intent Identifier prod monitors: two separate problems (session: ii-monitors)

- 2026-07-27 Provenance: findings pasted in-chat by Varun from an **earlier session's Datadog investigation**. Recorded here so the next session doesn't re-derive it. **Not independently verified by this session** — this session had no Datadog auth (the claude.ai Datadog MCP connector is present but unauthenticated; AGENTS.md still lists "Datadog keys" as pending). Re-derive the counts before quoting them anywhere outbound.
- 2026-07-27 Nothing about `intent-identifier-service`, monitor `238419175`, or monitor `238419172` existed anywhere in the nest before this file (grep across map/log/playbooks/runs/state came back empty). Nearest adjacent material: the Datadog→PagerDuty alert-review workflow in `playbooks/vespa.md` (§ alert channels), which is the flow to use for these monitors too.

## Problem 1 — SSP-side Intent Identifier timeouts (monitor 238419175)

- Monitor: https://app.datadoghq.com/monitors/238419175 — log count monitor, not a metric monitor. Matches `service:ssp-engine env:prod datacenter:ric1 status:error` + `"Unexpected error during intent identification"` + `HttpTimeoutException` + `IntentIdentifierControllerApi`. Fires at >5 matching events in a rolling 5-minute window.
- **It counts log lines, not unique requests, users, or share of traffic.** One alert episode can contain many timeout logs. Each log is generally SSP abandoning an Intent Identifier call after approximately 30 ms.
- Last-7-day shape (as of 2026-07-27 10:56 EDT): 18 alert episodes (was 17; another episode landed during the investigation), median episode approximately 5 min, longest approximately 20 min, approximately 4,394 matching timeout logs in the 7-day query window.
- Representative trace: SSP HTTP client times out at 30.20 ms → Intent Identifier finishes processing at 52–54 ms → server cannot return the response because SSP already closed the stream. **At least some requests complete just after SSP's deadline.**
- Recommended fixes (independent of each other, from the earlier report — none of these are actioned, and each is an outbound change needing a `review/` draft):
  1. Replicas 3 → 4, so three-pod capacity survives one pod restarting or going unready. Cuts the transient latency bumps from restart/scheduling/readiness events.
  2. SSP's Intent Identifier timeout 30 ms → approximately 60–75 ms. The sampled failure completed server-side at 52–54 ms. **Confirm the value against SSP's end-to-end request budget before deploying.**
  3. Do not retry `HttpTimeoutException` on the hot path (call path uses Resilience4j retry). A retry after the 30 ms deadline multiplies load exactly when the service is degraded. Fail open: return an empty/no-intent fallback and record a terminal-outcome metric.
- Measurement gotcha for after any of those changes: track the **rate**, not the log count — `SSP Intent Identifier timeouts / total SSP Intent Identifier calls`, grouped by region, SSP pod, and Intent Identifier pod.

## Problem 2 — p95 latency monitor is misconfigured (monitor 238419172)

- Monitor: https://app.datadoghq.com/monitors/238419172. Message claims "P95 latency exceeds 10 ms over the last five minutes". Query is `avg(last_5m):p95:trace.servlet.request{...} > 10`.
- **The metric unit is seconds**, so `> 10` means 10 seconds, not 10 ms. Normal p95 is approximately 15 ms, so a literal 10 ms threshold would be unusable and the actual 10-second threshold is effectively inert — this monitor cannot fire in practice.
- Second defect: `avg(last_5m):p95:` averages the approximately 10-second p95 buckets across five minutes. It is not one p95 over every request in the window. Any replacement message must describe it that way.
- Proposed replacement (early-warning monitor, top priority per the earlier report):

  ```
  avg(last_1m):p95:trace.servlet.request{
    env:prod,
    service:intent-identifier-service,
    span.kind:server,
    resource_name:post_/api/v1/identify-intents
  } > 0.020
  ```

  Recovery threshold `< 0.018`. Notification text: "The average of Intent Identifier's 10-second p95 latency measurements exceeded 20 ms during the last minute."
- Rationale: 20 ms warns before latency reaches SSP's approximately 30 ms deadline, while 238419175 stays the direct impact signal.

## Open / pending Varun

- **Is Datadog access live now?** AGENTS.md § Current status still says "Still pending: Datadog keys", but this report contains real Datadog query results. If a path exists (MCP handshake, API keys in `.env`, or Varun-run queries), it belongs in a playbook and in the status line. Filed as a question here rather than in `needs-human.md` because it is a capability fact, not a conflict.
- **Where does this service live in the nest?** `intent-identifier-service` has no `map/` file and no repo row in `playbooks/bitbucket.md`. If it is on the pCIV live path (SSP `/di` → intent identification), it likely belongs with `map/pciv-live-integration.md` and may attach to **AI-1542 (latency, Varun)** — unconfirmed, do not assume.
- **All three Problem-1 fixes and the Problem-2 monitor rewrite are outbound changes** (ssp-engine config, k8s replica count, a live prod monitor). Nothing was drafted or executed this session. Say the word and drafts go into `review/`.
