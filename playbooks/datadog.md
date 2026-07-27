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
| `238419175` | SSP → Intent Identifier `HttpTimeoutException` | **Log-count** monitor (>5 events / rolling 5 min), not a metric monitor. Counts log lines, not requests or traffic share. `runs/2026-07-27-intent-identifier-monitors.md` |
| `238419172` | Intent Identifier p95 latency | **Misconfigured** — message says 10 ms, query says `> 10` on a *seconds* metric = 10 s, effectively inert. Same run file. |
| `263399495` | Vespa Search Service timeouts | Worked example in `playbooks/vespa.md` (2026-07-24 RIC1/PDX1 incidents → `SUPPORT-808`). |

## Gotchas

- **Metric units are seconds.** `trace.servlet.request` p95 thresholds are
  seconds — `> 10` is ten seconds, not ten milliseconds. A 20 ms threshold is
  `> 0.020`. Misreading this produced monitor 238419172's inert threshold.
- **`avg(last_5m):p95:` is not a 5-minute p95.** It averages Datadog's
  approximately 10-second p95 buckets across the window. Any monitor message
  must describe it that way, or on-call reads it as a true window p95.
- **Log-count monitors don't measure impact.** Episode counts and log counts both
  scale with traffic and with retry behavior. For impact, build a rate:
  `failures / total calls`, grouped by region and pod.

## Tool incantations

*(Pending — fill in after the first successful handshake + smoke test. Record the
actual tool names, how to query logs vs. metrics, monitor read/history calls, and
whatever time-window arguments they take. UTC: Datadog is UTC, this machine is
Pacific — say which in any write-up.)*
