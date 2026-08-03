# Run — 2026-07-31 pCIV e2e latency testing

Session slug `pciv-latency-e2e`. Started 14:38 EDT. Varun brought in a prior session's
diagnosis-and-resolution report on pCIV e2e latency and asked me to get acquainted, then
time-boxed a laptop-direct upper-bound measurement.

## Acquaint pass

2026-07-31 — Read `playbooks/llm-eval-system.md` §Bedrock, `log/pciv-online-service.md`,
`tasks/pciv-online-deploy.md`, `state/digest-2026-07-31.md`, `tools/pciv/dev_eval_latency.py`,
and the service code in worktree `~/Documents/llm-evaluator-service-online-pciv`
(`feat-online-pciv`, HEAD `4c0cfe9`).
2026-07-31 — Credential probe per guardrail 5: `databricks auth describe -p dbc-562d27e2-d74d`
authenticated as Varun; `aws sts get-caller-identity --profile dev` returned the PowerUser SSO
role in 564079877134. Both live, so no auth gate this session.

## Assessment of the report (given to Varun in-chat)

2026-07-31 — Agreed with the core: eval 610 measures the wrong prompt, prompt caching is not
the lever, instrumentation plus persistent-client reuse is the right long-term ask.
2026-07-31 — Three corrections raised. (1) **Scope moved the same morning**: Dhaval 10:35 put
Flash out of scope, leaving France AI-Chat only, and Maxime's real budget via Norbert is 2 s
for chat — end to end including the France↔US round trip and ad selection, so the report's
"e2e p99 < 2 s" pass criterion is too generous for our hop. (2) **Two diagnostic branches were
already answerable by reading code, without the layer matrix** — see below. (3) The report's
§1–§3 all require a service change → push → CI → cd-deploy-configs PR → merge, which cannot
land against a same-day deadline; the direct-provider probe can.
2026-07-31 — Also flagged: the ">95% cache-hit rate" pass criterion conflates the DynamoDB
result cache with Mantle prompt caching, and "retire eval 610" is step zero rather than a
contingent §4 conclusion.

## Code reading that closed two of the report's branches

2026-07-31 — **Fresh client per request is confirmed, not hypothesis.**
`llm/utils/providers.py` `lru_cache` is on `_get_oauth_client` only, `maxsize=1`;
`get_chat_model` itself is uncached and `invoker_unstructured.py:176` /
`invoker_structured.py:209` call it per request via `asyncio.to_thread`. On the Mantle path
`_get_mantle_chat_model` calls `provide_token()` on **every** construction.
2026-07-31 — **`reasoning_effort` is correctly configured.** `models.json`
`gpt-5-6-luna-mantle` carries `"reasoning_effort": "none"` and `providers.py:121` forwards it
as `reasoning: {"effort": ...}` on the Responses path. What remained unverified was the wire
and the response — the probe settled both.

## Direct-Mantle probe (Varun approved the spend in-chat)

2026-07-31 — Script: scratchpad `mantle_direct_probe.py` (session 4ecb7d74). Raw HTTP to
`bedrock-mantle.us-east-1.api.aws`, no service, no LangChain. System prompt =
`pciv_extraction.txt` (11,266 B), user message = one French query per call, mirroring
`_format_message` at `max_group_size: 1`. Model params copied from `models.json`. Each model
measured two ways: a **persistent connection** with a reused bearer token, versus a **new
connection per request** with a fresh token each time (the service's current behaviour). 4
finalists interleaved, 3 warmups + 12 measured per model per way.
2026-07-31 — 108 calls, 96 measured, **zero failures**. Results and full caveats in
`state/mantle-direct-pciv-prompt-20260731.{md,jsonl}`.
2026-07-31 — Headline: **Luna is not slow — the 18k prompt was.** At the real ~3.3k pCIV
prompt Luna is p50 741 ms / p99 1,154 ms provider-side, against the 5.965 s p50 the 7/31 DBX
run produced on `civ_extraction.txt` at 18,183 tokens. Provider floor ranking: Qwen3-Next-80B
399 ms, Ministral 3 14B 486 ms, Gemma 4 31B 615 ms, Luna 741 ms (all p50).
2026-07-31 — Luna reported `reasoning_tokens: 0` on every call. Reasoning burn is ruled out.
2026-07-31 — **`provide_token()` costs ~545 ms p50 by itself**, paid per request today. Not
reusing the connection on top of that roughly doubles Luna's p95 (1,150 → 2,280 ms). A
persistent connection plus a cached token is worth ~550 ms at p50 and ~1.7 s at p95 on Luna.
This is the single biggest service-side lever and it is a code fix, not a provider problem.
2026-07-31 — Prompt caching is reliable only on Luna (3,332 of 3,334 tokens cached, 75–100%
hit rate). Gemma 4 implicit cache hit 0–17%, Qwen reported none, Ministral 0–50%. Do not model
open-weight cache savings as dependable.

## Gotchas found

2026-07-31 — `aws_bedrock_token_generator.provide_token()` raises
`ValueError: Region must be provided or set via the AWS_REGION environment variable` unless
`AWS_REGION` is set. `_get_mantle_chat_model` does an `os.environ.setdefault` before calling
it; any standalone script must do the same.
2026-07-31 — Qwen3-Next-80B returns very short replies on these queries (8–13 output tokens,
25 chars) because it answers `{"commercial": false}` for non-commercial French search terms.
Legitimate, but it makes its latency advantage partly an output-length artifact — do not
compare raw latency across models without also comparing output tokens.

## Label correction (Varun pushed on this, twice — he was right to)

2026-07-31 — He asked whether the persistent-connection numbers were real or manufactured.
They are real: a stopwatch around `client.post()` on actual HTTPS requests, 96 measured calls,
nothing estimated or extrapolated. But I had labelled the column `e2e`, which overstates it.
The timer covers serialization, network round trip, server prefill and generation, and reading
the full non-streamed body. It excludes bearer-token generation, the amortized TLS handshake,
and all service overhead, and it follows 3 excluded warmups that primed both the connection and
the prompt cache. Renamed the columns to "round trip", documented the exact span in the state
file and the script docstring, and noted that the JSONL keeps `e2e_ms` only for continuity with
`dev_eval_latency.py`.
2026-07-31 — Lesson for future sessions: my first two answers over-hedged instead of answering
the binary question he asked. He had to ask a third time to get "genuine, not manufactured."
Lead with the direct answer, then qualify.

## Wrap-up and next

2026-07-31 — Probe script promoted out of the session scratchpad to
`tools/pciv/mantle_direct_probe.py` with run instructions for both laptop and EC2, and a
three-tool orientation note added to `tools/pciv/README.md`. Durable findings folded into
`playbooks/llm-eval-system.md` §Bedrock.
2026-07-31 — **Varun's plan: Monday, run the same probe from a us-east-1 EC2** for the
in-network number. That also settles PrivateLink against the laptop baseline. Service-side run
still needs the finalists wired to `pciv_extraction.txt` in `pciv_online` (only 102 nano / 103
ministral-8b exist there; the 6xx finalists all sit in `civ_extraction` at 18k) — pair that
config change with the persistent-connection + cached-token fix in one commit, since both need
the same push → CI → overlay bump → merge cycle.
2026-07-31 — **Four commits sit unpushed**: the auto-mode classifier blocked `git push origin
main` on two attempts, including as a single non-compound command. Varun needs to push, or add
a Bash permission rule. Nothing in the working tree from this session is uncommitted; the
`--query` edit to `dev_eval_latency.py` is another session's and was left untouched.
## 2026-08-03 — the fix, three days later (same session, resumed)

2026-08-03 — Re-synced before touching anything. Nest was already level with origin; four commits
had landed today from another session (Monday digest, the AI-1542 ballparks draft, Varun's edits
to it, a map entry). Confirmed my Friday service commit `1aac587` was still unpushed and that
nothing in the nest recorded a fix existing — only the problem, at `playbooks/llm-eval-system.md`
line 94. So no duplicate work.
2026-08-03 — Varun posted the ballparks himself as AI-1542 **c171586** today, so that deliverable
is closed and I did not touch it. His five edits are already captured in `playbooks/jira.md` by the
session that drafted it.

### Root cause, sharper than Friday's number

2026-08-03 — `provide_token()` builds a **new `botocore.session.Session()` per call**, and the
expensive part is *resolving* the credentials, not the crypto. Timed: resolution ~740ms,
`Session().get_credentials()` ~3ms, the SigV4 presign ~0.1ms. Locally the resolution reads the SSO
cache; **under IRSA it is an `AssumeRoleWithWebIdentity` call to STS**, so uncached this put a real
network round trip on every inference request — plausibly worse in-pod than on the laptop where I
measured it.

### The fix

2026-08-03 — Commit `1aac587` on `feat-online-pciv`. Two caches. (1) The Mantle bearer token,
refreshed hourly well inside its 12h validity. (2) Chat models, keyed on provider, config, domain,
environment **and a digest of the credential** — the key design point, because both the Databricks
and Mantle clients bake their token in at construction, so keying on it means a rotation changes the
key and produces a fresh client instead of a stale one silently 401ing. Added `reset_model_cache()`
for tests and a `threading.Lock` on each cache, since `get_chat_model` is reached through
`asyncio.to_thread`.
2026-08-03 — Blast radius checked before writing: `get_chat_model` has exactly two callers,
`invoker_unstructured.py:176` and `invoker_structured.py:209`, both at the top of
`run_batch_*` — so once per API request, not per query. The offline batch path (group 40) already
amortized this cost across 40 queries; the online single-query path paid it in full every time.
That is why this barely shows up in offline civ and dominates online pCIV.
2026-08-03 — Verified live against Mantle through the service's own provider layer, not a
standalone script: repeat `get_chat_model` **545–740ms → 0.03ms**, and Luna warm requests settled at
**~636ms p50** (min 554, max 677) — at or slightly better than Friday's 741ms persistent-connection
floor. 486 tests pass, 9 new covering reuse, rotation, TTL expiry, region change, cache bounding,
and the unsupported-provider error path.
2026-08-03 — Push parked in `review/2026-08-03-ai1542-client-reuse-push.txt`. Pushing only triggers
a CI image build; deploying still needs a cd-deploy-configs tag-bump PR after it.
2026-08-03 — **Varun pushed it.** Verified `1aac587` is on `origin/feat-online-pciv`; executed review
draft deleted per the convention. Next in the deploy chain: get the CI image tag, then a
cd-deploy-configs tag-bump PR. Nothing is deployed yet — dev still runs `1.0.294-feat-online-pciv`,
which predates this fix, so any latency measured against dev right now is still the slow path.

### 2026-08-03 (pm) — Antonio's endpoint validated: correct, and bypassed

2026-08-03 — Varun ran `aws sso login --profile dev` in-session. Antonio asked whether the dev VPC
endpoint works. Answer: the endpoint is right, the DNS path around it is not.
2026-08-03 — Endpoint `vpce-088316a09b030fcfd` exists in `vpc-0317d6910f3add39a`, created 17:01 UTC
(13:01 EDT) today, state available, `PrivateDnsEnabled: true`, ENIs `10.9.173.80` (us-east-1a) and
`10.9.178.251` (us-east-1b), subnets `subnet-0a3cb949a8af631d2` and `subnet-05f1dc5d674c61d34`.
2026-08-03 — First probe looked like a flat failure: from two EKS workers the hostname still resolved
to Friday's exact three public addresses. Both workers turned out to sit in **the same two subnets as
the endpoint ENIs**, which ruled out placement and pointed at the resolver.
2026-08-03 — Cause: DHCP option set `dopt-004a4a58405411647` sets `domain-name-servers` to
`10.11.128.70` and `10.11.128.50` (corporate DNS, matching the `ric1.admarketplace.net` domain-name),
not AmazonProvidedDNS. Those servers do not serve the endpoint's private hosted zone. `enableDnsSupport`
on the VPC is `True`, so the Route 53 Resolver itself is fine — nothing queries it.
2026-08-03 — Proof, one worker, three resolvers, same name: `10.11.128.70` → public
`3.214.115.45`/`34.231.48.123`/`52.87.73.163`; `10.11.128.50` → the same three; **`10.11.144.2` (VPC
resolver) → private `10.9.173.80`/`10.9.178.251`**, exactly the endpoint ENIs. So private DNS works
and only the resolver choice is wrong.
2026-08-03 — **The lesson worth carrying: `PrivateDnsEnabled: true` only means the private hosted zone
was created.** It says nothing about whether your instances query a resolver that can see it. Check the
DHCP option set before concluding PrivateLink is live. Folded into `playbooks/llm-eval-system.md`.
2026-08-03 — Tooling gotcha: `dig` and `nslookup` are absent on these workers, and `getent hosts` only
uses the system resolver so it cannot compare resolvers. Wrote a raw-UDP DNS query in Python 3
(scratchpad `dnsq.py`), sanity-checked it locally against 8.8.8.8, then base64'd it into an SSM
`AWS-RunShellScript` command. All lookups read-only; the temp file was removed in the same command.
2026-08-03 — Secondary gap raised with Antonio: ENIs cover 1a/1b only, the VPC runs instances in 1c
too, and AWS offers this endpoint service in 1a/1b/1d. `eks-dev-use1-01` currently has nodes only in
1a/1b so nothing is broken today, but scaling into 1c means cross-AZ hops to the endpoint.
2026-08-03 — Reply drafted at `review/2026-08-03-infra3474-privatelink-dns-gap.txt`, awaiting Varun.
Deliberately does not pick the fix mechanism for Antonio — conditional forwarder on the corporate
servers versus a CoreDNS forward inside the cluster is his call.
2026-08-03 — **Consequence for measurement: an in-VPC latency run today would still traverse the public
path**, so it cannot show a PrivateLink benefit yet. Two ways forward that do not wait on the DNS fix:
force resolution to `10.9.173.80` and compare against the public address, or measure TCP+TLS handshake
time to each address, which costs nothing and isolates exactly the hop PrivateLink changes.

### The thing nobody has told Saksham

2026-08-03 — Per today's digest flag 2: Saksham fixed CIV at **1.1s** in the Friday thread at 11:59,
before the 700ms measurement landed at 15:12, and never restated the stack. AI-1542 c171586 reports
**provider round trips** and says so explicitly. The number that belongs in his budget slot is the
service-side one — ~1.5s p50 before this fix, ~636ms provider plus service overhead after. That
distinction has not reached him, and it is the difference between the 2s AI-Chat budget closing and
not closing.

2026-07-31 — AI-1542's Aug-1 deadline was NOT addressed this session. Varun did not ask for a
ticket comment and per the run history his exact wording must be approved before any outbound
write, so nothing was drafted. The numbers are ready to quote if he wants one Monday — with the
caveat that they are provider-only and laptop-origin.
