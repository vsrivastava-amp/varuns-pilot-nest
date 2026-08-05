# online-civ-service prod release — infra ticket drafts

Replaced 2026-08-05 (Varun's call): this file is now the three paste-ready Jira tickets, nothing
else. Prior checklist form is in git history (`git log -- tasks/pciv-prod-infra-checklist.md`).

Names assume the 2026-08-05 online-civ rename lands (prod uses NEW-name infra:
`wi-online-civ-service`, `online-civ-service/...` paths — dev alone keeps the old names). If the
rename is called off, swap back to `online-pciv-service`/`wi-online-pciv-service` throughout.

Placeholders: `<dc>` = prod datacenter tag (asked alongside account id, 2026-08-05); `<model>`,
`<N>` QPS, `<prod account>` = pending AI-1540 + business + Antonio. Antonio confirmed 2026-08-05:
no shared resources across accounts; file requests for everything. Per playbook: CC the manager on
prod-scoped access tickets to preempt the approval round-trip.

---

## Ticket 1 — file when prod account/dc answered

Title: Create secrets and service account for online-civ-service in prod EKS

We are extending online-civ-service (AI-1538, live in dev EKS ric1) to prod, same pattern as
llm-evaluator-service. The deployment configs ride the normal release PR flow; this ticket covers
the infra pieces, matching what INFRA-3474/INFRA-3475 set up for dev:

* Please create akeyless paths `online-civ-service/prod/<dc>/databricks/*` (DATABRICKS_ACCOUNT_ID,
  DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET) with the prod Databricks credentials — same
  values as `llm-evaluator-service/prod/<dc>/databricks/*`.
* Please create the workload-identity service account `wi-online-civ-service` in the prod cluster
  with the same Bedrock IAM policy as its dev counterpart (INFRA-3474): bedrock:InvokeModel,
  bedrock:Converse, bedrock:ConverseStream, bedrock-mantle:CallWithBearerToken, and
  bedrock-mantle:CreateInference, us-east-1.
* Please confirm the prod account has model access for the Bedrock models we call (in dev no extra
  grant was needed for Mantle, but that's per-account).
* We assume the global imagePullSecret `docker-registry-access-token-ampdockercirw` also applies in
  prod — flag if not.

Thanks!

---

## Ticket 2 — file when prod account/dc answered

Title: Bedrock Mantle interface endpoint + private DNS for the prod EKS VPC

online-civ-service calls bedrock-mantle.us-east-1.api.aws. In dev this needed three pieces before
traffic actually went private, so bundling them here for prod:

* Please create the Interface endpoint `com.amazonaws.us-east-1.bedrock-mantle` in the prod EKS VPC
  with Private DNS enabled, HTTPS allowed from the pod/node path, and an endpoint policy that
  permits the two bedrock-mantle actions.
* Please also wire the DNS path so workloads actually resolve the private addresses — in dev the
  fix was pointing the cluster's CoreDNS forward at the Route 53 inbound resolver (see INFRA-3474).
  Whatever the prod VPC's equivalent is, the endpoint isn't live until an in-cluster lookup returns
  the endpoint ENIs.
* AZ note from dev: the endpoint service offers us-east-1a/1b/1d. Please put ENIs in every one of
  those that overlaps prod subnets — in dev we only covered 1a/1b and the 1c nodes permanently
  cross AZs.

Happy to validate from our side as soon as it's in — we have a one-command check.

---

## Ticket 3 — file when model + QPS land (numbers pre-computed 2026-08-05 for 100 RPM: ~400-450k
input TPM gross, ~16-20B input tokens/month flat-rate; scale linearly for `<N>`)

Title: Bedrock Mantle quota increase for online-civ-service prod — <model>

We're launching online-civ-service at up to <N> QPS against <model id> on Bedrock Mantle,
us-east-1, account <prod account>. At ~4-4.5k input / ~20-60 output tokens per request that's
roughly <N x 60> RPM and <computed> input TPM, and AWS guidance is to request 2-3x headroom.
Mantle-cohort models don't appear in Service Quotas, so this goes through AWS Support — we have an
open thread with our account team (Darcis/Sushant) that this can ride. Could you file/own the
increase, or should we drive it through the account team directly?
