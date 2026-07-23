# AWS Bedrock capacity and latency memo (online research agent, via Varun)

*(Derived artifact, received 2026-07-23. Verbatim memo below; conclusions folded into `tasks/pciv-online-deploy.md` Phase C and `log/pciv-online-service.md`. Re-verify numbers against the quotas API / account team before any infra ask is sent.)*

---

**Research snapshot:** July 23, 2026
**Target workload:** 100–200 sustained QPS in `us-east-1`, approximately 3,600 input and 250 output tokens per request, P99 below two seconds, late-August 2026 launch.

## Executive summary

The workload translates to:

* **6,000–12,000 requests per minute**
* **23.1M–46.2M raw tokens per minute**
* At 200 QPS over a 30-day month: **518.4M requests, 1.866T input tokens, and 129.6B output tokens**

Those token figures are before model-specific output-token multipliers, reservation of `max_tokens`, retries, and traffic headroom. AWS recommends forecasting roughly **2–3× peak throughput**, which would imply a planning envelope of approximately **24,000–36,000 RPM and 92.4M–138.6M raw TPM** at the 200-QPS peak.

The main findings are:

1. **Quota approval remains model- and capacity-specific.** Adjustable quotas use Service Quotas; non-adjustable quotas require AWS Support or the account team. AWS publishes neither approval turnaround SLAs nor hard maximum approval ceilings.
2. **Priority, Standard, and Flex share the same on-demand RPM/TPM pool.** Priority changes scheduling priority, not the quota envelope, and AWS does not publish a hard P99 or TTFT guarantee.
3. **Provisioned Throughput is currently not a practical path for the named open-weight models in `us-east-1`.** The published support matrix does not include Llama 4 Maverick, Ministral 3B/8B, GPT-OSS, or Qwen.
4. **Cross-region inference provides a separate, larger model-level quota pool and better capacity availability, but it can materially increase latency.** AWS does not provide a route-specific latency ceiling or let callers pin a destination region.
5. **Bedrock documents minute-scale quotas and a 60-second refresh cycle, but not a formal token-bucket size or per-second enforcement algorithm.** Client-side smoothing is therefore required.
6. The premise that caching is limited to Nova and Anthropic is now outdated: AWS also documents caching for **OpenAI GPT-5.6** and automatic implicit caching for **Gemma 4 on Bedrock Mantle**. No public Llama, Mistral, or Ministral caching roadmap was found.

## 1. On-demand quota increases

For quotas marked **Adjustable: Yes**, increases can be submitted through the Service Quotas console or the `RequestServiceQuotaIncrease` API. AWS notes that small requests may be approved automatically, while larger requests are routed for manual review. There is no published processing-time SLA, and AWS may approve, partially approve, or deny a request.

For quotas marked **Adjustable: No**, the Service Quotas API is not the escalation mechanism. Current Bedrock documentation says customers may still submit the Support Center limit-increase form for consideration. This is relevant to quotas such as the published 800-RPM Llama 4 Maverick cross-region limit and the 10,000-RPM Ministral limits: "not adjustable" means not self-service adjustable, not that AWS publicly promises never to grant an exception. Approval remains discretionary.

Bedrock Mantle is a special case: quotas may appear in Service Quotas, but AWS currently instructs customers to request increases through AWS Support rather than through the Service Quotas increase workflow.

A strong request should include:

* Exact model ID, source region, and inference mode
* Current and requested RPM, input TPM, output TPM, and any daily-token quota
* Sustained, peak, and burst distributions—not just average QPS
* Launch date and phased load-test schedule
* Expected `max_tokens`, retry rate, and model-specific output-token multiplier
* Existing throttling error codes, request IDs, CloudWatch graphs, and timestamps
* Business impact and available fallback models or regions

AWS explicitly recommends involving the account team for throughput forecasting and supplying traffic patterns, errors, request IDs, and the scaling timeline.

**Turnaround and hard ceilings:** AWS does not publish a "typical" Bedrock quota-increase turnaround or a maximum approvable quota. Consequently, neither should be placed on the launch critical path without written account-team confirmation. Submit the request immediately and treat any value above the currently reported quota as unavailable until approved and load-tested.

## 2. Priority, Standard, Flex, and Reserved tiers

**Priority, Standard, and Flex share the account's on-demand quota.** They do not provide separate RPM or TPM pools. Reserved service-tier capacity is separate.

* **Priority:** Requests are scheduled ahead of Standard and Flex requests and incur premium pricing. AWS announced that most supported models can see **up to 25% better output-token-per-second latency** than Standard. "Up to" is not a P99, TTFT, or end-to-end latency guarantee.
* **Standard:** Default on-demand behavior.
* **Flex:** Discounted, lower-priority execution with longer and less predictable processing time; unsuitable for the synchronous P99 target.
* **Reserved service tier:** A separate token-capacity reservation with one- or three-month terms, monthly billing, and Standard-tier overflow. It should not be confused with legacy Provisioned Throughput.

Applications can request a tier per invocation and inspect the resolved tier in Bedrock telemetry. Priority should therefore be benchmarked with both requested and resolved tier recorded.

**Conclusion:** Priority can reduce contention and output-generation latency, but it cannot solve an insufficient RPM/TPM quota, and public AWS material does not guarantee sub-two-second P99 latency.

## 3. Provisioned Throughput

AWS documentation now distinguishes token-based Provisioned Throughput from the older **Model Unit** purchasing path. Under the documented Model Unit path:

* Billing is hourly.
* Price depends on the model, number of Model Units, and commitment.
* Available terms are no commitment, one month, or six months.
* Billing continues until the provisioned resource is deleted.
* Exact throughput per Model Unit and model-specific pricing may require the console, Support, or the account team.

Provisioned Throughput primarily provides dedicated, predictable capacity and protection from shared on-demand contention. AWS does not publish a general numerical TTFT or P99 improvement, so it should not be assumed to make an intrinsically slow model meet the latency target.

The current support matrix is the limiting factor. The published list does **not** show Provisioned Throughput support for:

* Llama 4 Maverick or Scout
* Ministral 3B or 8B
* GPT-OSS
* Qwen
* Current open-weight Mistral families

Meta support is limited to older Llama 3.1/3.2 entries and is listed in `us-west-2`, not as a capacity option for the named models in `us-east-1`.

Provisioned Throughput also cannot be combined with a cross-region inference profile.

A precise cost break-even cannot be derived from public documentation because both Model Unit capacity and purchasable pricing are model-specific. The comparison is:

`Monthly on-demand cost = 2,592,000 × QPS × (3,600 × input price + 250 × output price) / 1,000,000`

versus:

`Monthly PT cost = approximately 730 × hourly unit price × required units`

At 200 continuously utilized QPS, utilization is high enough that dedicated capacity would merit pricing analysis **if the selected model supported it**. For the named OSS candidates, model availability currently resolves the question before economics do.

## 4. Cross-region inference profiles

Cross-region inference quotas are associated with the **model and source region/inference-profile class**, rather than being the sum of the ordinary on-demand quotas in all possible destination regions. Global profiles have their own quotas, managed from the source region. Creating multiple application inference profiles around the same underlying model does not appear to create independent quota pools; AWS describes quota scope at the model-and-region level, not per application profile.

The source region accepts the request and Bedrock selects an eligible destination region according to available capacity. Traffic travels over the AWS global network and the response returns through the source region. Customers cannot pin an individual destination from a cross-region profile.

AWS explicitly notes that cross-region routing can increase response time. It does not publish a maximum routing penalty or region-specific P99.

The observed **370–900 ms** round-trip range for tiny requests is therefore plausible and operationally important: it consumes 18–45% of a two-second end-to-end budget before substantial generation, queueing, application processing, or retries. Cross-region inference should be treated as:

* A capacity, availability, and overflow mechanism
* Not a latency guarantee
* Something that must be tested separately by profile and service tier

For the primary low-latency path, a single-region Priority invocation is preferable when its approved quota and capacity are sufficient. Cross-region inference is better positioned as controlled overflow or failover, subject to its own measured P99.

## 5. Burst behavior and throttling

Bedrock quotas are expressed per minute, and AWS guidance describes quota replenishment on a **60-second cycle**. AWS also documents some short-burst capacity, but does not publish a formal token-bucket depth, refill granularity, or hidden per-second ceiling. A system should therefore not assume it can consume an entire minute's allocation instantaneously.

Runtime quota accounting can initially reserve:

`input tokens + requested max_tokens`

The reservation is adjusted as generation proceeds. Some model families also apply output-token "burndown" multipliers; AWS currently documents higher multipliers for several Anthropic model generations, while most other models remain 1:1. Cache-write tokens count toward quota, while supported cache-read tokens may be excluded.

This makes a tight `max_tokens` setting important. For an expected 250-token extraction response, a 4,096-token maximum unnecessarily consumes projected quota and can trigger avoidable throttling.

Error semantics:

* **HTTP 429 / `ThrottlingException`:** The account/model quota is being exceeded.
* **HTTP 503 / `ServiceUnavailableException`:** Bedrock lacks immediate regional or model capacity despite the account remaining within quota.

AWS recommends exponential backoff with jitter for transient capacity errors and gradual traffic ramping—approximately holding a level for 15 minutes before increasing it by 50%. Sustained 503s require rate reduction, queueing, another region/profile, or another model rather than unlimited retries.

For the proposed service:

1. Maintain separate local request and projected-token limiters.
2. Smooth against approximately `RPM / 60` and `TPM / 60`, with a deliberately bounded burst allowance.
3. Reserve `input + max_tokens × model multiplier` before admission.
4. Reconcile reservations against actual usage afterward.
5. Place a short bounded queue ahead of Bedrock.
6. For the two-second P99 path, permit at most one deadline-aware retry or immediate model/profile failover.
7. Shed low-value traffic rather than allowing retries to amplify overload.
8. Load-test traffic ramps, minute boundaries, and simultaneous RPM/TPM exhaustion.

## 6. Prompt caching for open models

The "Nova and Anthropic only" assumption is no longer current. As of July 2026, AWS documentation includes prompt-caching support for:

* Anthropic Claude models
* Amazon Nova models
* OpenAI GPT-5.6
* Gemma 4 on Bedrock Mantle, using automatic implicit caching

Gemma 4 implicit caching applies automatically across Standard, Priority, and Flex requests. AWS says matching cached prefixes can reduce latency, but does not guarantee a cache hit.

No public AWS roadmap or announcement was found for prompt caching on Llama 4, Ministral, or the wider Mistral open-model families. Capacity and cost planning should therefore treat caching as unavailable for those models until the model documentation or pricing page explicitly says otherwise.

Caching benefits only the repeated prefix. For this extraction workload, likely reusable material includes the system prompt, schema, examples, and tool definitions; the unique ad/query payload will still require prefill. Cache-read pricing, cache-write pricing, minimum cacheable prefix length, and TTL vary by model. For supported Claude models, AWS documents that eligible cache hits can also avoid rate-limit deductions.

Cross-region routing can reduce cache locality and generate cache writes in more than one destination region, weakening both latency and cost benefits.

## Launch recommendation

Before selecting a model, apply these gates:

1. **Quota gate:** Approved capacity of at least 12,000 RPM and 46.2M effective TPM, with a target request closer to 24,000–36,000 RPM and 92.4M–138.6M TPM after AWS-recommended headroom. Increase TPM further for output-token multipliers.
2. **Latency gate:** P99 measured at intended concurrency, output length, service tier, and inference profile—not on tiny or serial calls.
3. **Throttling gate:** Verify behavior at sustained load, burst load, and minute-window boundaries.
4. **Fallback gate:** Maintain a second model or inference profile with an independently adequate quota pool.
5. **Cost gate:** Price with actual cache-hit rate, Priority premium, retries, and output-token accounting rather than nominal token prices alone.

For the current examples, Ministral's 10,000-RPM default falls below the 12,000-RPM sustained requirement at 200 QPS, while Llama 4 Maverick's 800-RPM cross-region default is orders of magnitude too small. Neither should be treated as launch-capable at 200 QPS until AWS has approved and validated materially higher capacity.

### Primary AWS material and dates

* Bedrock Priority and Flex service-tier announcement — **November 18, 2025**.
* Bedrock Reserved service-tier announcement — **November 26, 2025**.
* Service Quotas visibility for Bedrock Mantle — **May 27, 2026**.
* Gemma 4 on Bedrock Mantle, including implicit caching — **June 2026**.
* Bedrock runtime quotas, Provisioned Throughput, cross-region inference, scaling, and prompt-caching documentation — accessed **July 23, 2026**.
