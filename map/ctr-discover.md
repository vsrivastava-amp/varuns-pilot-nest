# CTR Discover / ctr-inference-service

Project map. Jira epic **AI-1140**. Slack **#proj-ctr-discover** (`C0B1Z59SBB3`), plus **#tmp-dsp-ctr-inference-service-adt** (`C0BLCSFTTH8`) for the DSP integration standup (15 min, Mon–Thu, set up by Neena 2026-07-29).

Not Varun's project. It is mapped here because it consumes `advertiser-ctr-service` (whose prod alerts land in `#prod-relevance-yield-alerts`) and because the DSP-to-AAS retargeting decision below is the same argument Dhaval is making on the pCIV side.

## Serving topology (Neena's diagram, 2026-08-03)

Source: Neena Sulakhe, `#proj-ctr-discover`, 2026-08-03 10:59:49 ET, message ts `1785769189.630719`, "high level diagram :" with `Screenshot 2026-08-03 at 10.59.07 AM.png` (file `F0BMKCH198V`). One 👍 as of 11:13. **This is Neena's drawing, not an independently verified topology.**

Transcribed to Mermaid by Varun, 2026-08-03. **The Mermaid below is the authoritative version of this diagram** — an earlier pass at reading the PNG directly got two labels wrong. Do not re-transcribe from the screenshot.

```mermaid
flowchart TB
    subgraph TOP[" "]
        direction LR
        DSP["DSP"]
        AAS["AAS"]
    end

    subgraph MIDDLE[" "]
        direction LR
        CTR["ctr-inference-service"]
        BASETEN["Baseten"]
    end

    subgraph BOTTOM[" "]
        direction LR
        ADV["advertiser-ctr-service"]

        subgraph FEAST_GROUP[" "]
            direction TB
            FEAST["feast-service"]
            CAFFEINATED(["caffeinated"])
        end

        DBX[("DBx")]
    end

    DSP --> AAS
    DSP --> CTR

    AAS -. "Future" .-> CTR

    CTR --> BASETEN
    CTR --> ADV
    CTR --> FEAST

    FEAST --- CAFFEINATED
    FEAST --> DBX

    REMOVE_NOTE["this will be removed<br/>in future"]
    REMOVE_NOTE -.- DSP
```

Read as: `ctr-inference-service` is the hub. It calls `advertiser-ctr-service`, `feast-service`, and Baseten. `feast-service` is caffeinated, meaning it fronts Databricks with a Caffeine cache, and DBx is drawn as the datastore.

**DSP carries the deprecation annotation, not the DSP-to-CTR edge.** "this will be removed in future" attaches to the **DSP node**, and DSP is the only node styled as deprecated. Today DSP calls both AAS and `ctr-inference-service`; the dotted "Future" edge runs AAS to `ctr-inference-service`. So the future path is AAS calling the service directly.

⚠️ What "removed" scopes to is not settled by the diagram. Attached to the node, it reads as DSP leaving this picture entirely. Dhaval's framing on the adjacent `#proj-ctr-discover` thread, 2026-07-29 19:46 ET, keeps DSP in play: "In an ideal world, this data flows through from AAS to DSP. AAS knows which query path it took so it the most deterministic info." Those two readings differ, and nothing here decides between them. Ask Neena before building on either.

`feast-service` corroborates elsewhere in the nest: `state/digest-2026-07-24.md` records AI-1370 as "Redis lag-features via **feast-store-library** working locally", Rama asked Steven Wu on 2026-07-20 for a "working Dev **Feature Store** API endpoint", and Steven filed **AI-1632** "Create Databricks Secrets Scope and Values for Feature Store - Stage" on 2026-08-03.

## Baseten is not a serving dependency, and the diagram's arrow to it is the open question

Inference runs **in process**, not on Baseten. Rama Mukkamalla decided this on 2026-07-07 and the AI-1370 comment history carries it end to end.

- **AI-1370 c169423, Rama, 2026-07-07 11:10 ET:** "Baseten: We will not be going to Baseten, considering the additional latency added and low latency SLA requirement of this service to be used by DSP"
- **c169513, 2026-07-08:** "Had meeting with team on pre processing for Inference Model and to get predictions within the Service **without using Baseten**."
- **c170342, 2026-07-20:** "Completed migration of python baseten new inference model code to this Service … We are using `onnxruntime` maven dependency." So the model moved into the JVM process.
- **The ticket's own AC does not mention Baseten:** "Service integrated with Feast, ELME CTR service and new Inference Model."

Baseten does survive in two narrower roles, which is the likely explanation for Neena's arrow:

1. **As the reference endpoint for output validation.** AI-1370 c170813, 2026-07-23, ToDo item: "Compare results from response with Baseten hosted endpoint." That is a correctness check against the incumbent, not a request path.
2. **Hosting the fine-tuned embedding model**, which is a different model on a different track — **AI-1267** "CI/CD to deploy fine tuned embedding model to Baseten" moved Blocked → In Review on 2026-08-02.

⚠️ So `CTR --> BASETEN` in the diagram is drawn as a solid current dependency, and the ticket says the serving path deliberately avoids Baseten. Ask Neena whether the arrow means the comparison path, the embedding model, or something that changed after 7/27. **Do not read it as "ctr-inference-service calls Baseten to get CTR predictions"** — the primary source says the opposite, on latency grounds.

AI-1370 itself is **Ready for QA**, assignee Rama, newest comment 2026-07-27.

## Contract and integration state (2026-08-03)

- **Owner split:** Rama Mukkamalla builds `ctr-inference-service`. Neena builds the `dsp-engine` integration. Stephen Ince owns the auction piece (**AS-13444**, "[dsp-engine] Enable new auction logic when experimenting with ctr-inference-service"). Lochan Mahajan has the QE work (**AS-12949**). Ankit Shah and Yaarit Even are the standing cc.
- **TDD:** `docs.google.com/document/d/1zK6yeqkAw6he2BoGgMQmKhjvDIYB95KIXRNxBnPupKI` — Neena added a field-mapping tab 2026-07-30 with open questions marked in red.
- **Neena is blocked on a shared library.** She asked Rama on 2026-07-28 for a `service-name-api-client`-convention jar carrying request, response and enum classes so `dsp-engine`, `ctr-inference-service` and the QE repo stay on one contract shape. Rama's ETA was 8/3. As of 7/31 11:56 she still needed it plus a sample curl for the new endpoint, and Saksham escalated on 7/31 11:22: "please prioritize this because AS changes are the long pole and will be the last thing which will be completed".
- **Response shape changes from R&Y's contract** (Neena, 2026-07-28): adds `requestId`, `productId`, `keywordId`; renames `advertiserCtrList` to `predictions`; moves `ctr` and `type` into a nested prediction object. No fields dropped.
- **`type` enum** is `ELME`, `LEGACY`, `CTR_INFERENCE`.
- **Ad type resolution is unsettled in a small way.** DSP sets `AdType` TEXT for tile ads too. Ankit's plan (7/30 16:34) is to pass it through unchanged and let the service ignore it, since the default Find flow does not need it. Rama confirmed Find tiles carry no experiment context.
- **Experimentation:** Yaarit asked Munjal Thakkar on 2026-07-29 for an Amplify config type named "Use CTR Realtime for Yield Auction", a simple enable/disable toggle, to A/B test the query-aware CTR model on non-caching Discover placements.

## Why this gates Vespa work

Neena, `#release-6129-vespa-group-topology` 2026-07-28: us-east moves to group topology only **after** the DSP-to-`ctr-inference-service` work completes, which she estimated at roughly end of the following week, later given as ~8/7. That sequencing is what Oren's Monday traffic shift and the AI-1386 rollout plan sit on top of.

## Related

- `map/aas.md` — the future caller.
- `map/vespa.md` — AI-1386 grouped topology, sequenced behind this work.
- `state/digest-2026-07-24.md` — AI-1370 status, the Baseten note above.
