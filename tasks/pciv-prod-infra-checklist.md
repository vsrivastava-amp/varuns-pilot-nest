# online-civ-service stage + prod — infra ticket drafts

Replaced 2026-08-05 (Varun's call): this file is now the three paste-ready Jira tickets, nothing
else. Prior checklist form is in git history (`git log -- tasks/pciv-prod-infra-checklist.md`).
2026-08-05 (later, Varun in-chat): each ticket asks for BOTH stage and prod. **Tickets 1 and 2 are
FILED: INFRA-3507 and INFRA-3508** (both Not Started, unassigned per INFRA convention, linked to
each other and to AI-1538). Ticket 3 (quota) still waits on the model pick and the QPS target.
Lesson recorded: exact account ids and VPC/subnet ids are NOT needed to file — say "stage EKS" /
"prod EKS" and ask infra to report ids back. Do not block a request on facts infra already owns.

Names assume the 2026-08-05 online-civ rename lands (stage and prod use NEW-name infra:
`wi-online-civ-service`, `online-civ-service/...` paths — dev alone keeps the old
`wi-online-pciv-service` names). If the rename is called off, swap back throughout.

Placeholders: `<dc>` = prod datacenter tag (asked alongside account id, 2026-08-05); `<model>`,
`<N>` QPS, `<prod account>` = pending AI-1540 + business + Antonio. Antonio confirmed 2026-08-05:
no shared resources across accounts; file requests for everything. Per playbook: CC the manager on
prod-scoped access tickets to preempt the approval round-trip.

---

## Ticket 1 — FILED 2026-08-05 as INFRA-3507 (Varun-directed in-chat; stage+prod, no exact ids needed — infra knows their inventory; asks them to report the prod path and the stage/prod account ids back). Text below is the filed version's source; the live ticket is authoritative.

Title: Create secrets and service account for online-civ-service in stage and prod EKS

We are extending online-civ-service (AI-1538, live in dev EKS ric1) to stage and prod, same
pattern as llm-evaluator-service. The deployment configs ride the normal PR/release flow; this
ticket covers the infra pieces, matching what INFRA-3474/INFRA-3475 set up for dev:

Stage (EKS ric1, same cluster as stage-llm-evaluator-service):

* Please create akeyless paths `online-civ-service/stage/ric1/databricks/*` (DATABRICKS_ACCOUNT_ID,
  DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET) with the stage Databricks credentials — same
  values as `llm-evaluator-service/stage/ric1/databricks/*`.
* Please create the workload-identity service account `wi-online-civ-service` in the stage cluster
  with the same Bedrock IAM policy as the dev counterpart from INFRA-3474 (`wi-online-pciv-service`):
  bedrock:InvokeModel, bedrock:Converse, bedrock:ConverseStream,
  bedrock-mantle:CallWithBearerToken, and bedrock-mantle:CreateInference, us-east-1.

Prod:

* Please create akeyless paths `online-civ-service/prod/<dc>/databricks/*` (same three keys) with
  the prod Databricks credentials — same values as `llm-evaluator-service/prod/<dc>/databricks/*`.
* Please create the workload-identity service account `wi-online-civ-service` in the prod cluster,
  same Bedrock IAM policy as above.
* Please confirm the prod account has model access for the Bedrock models we call (in dev no extra
  grant was needed for Mantle, but that's per-account).

We assume the global imagePullSecret `docker-registry-access-token-ampdockercirw` also applies in
stage and prod — flag if not.

Thanks!

---

## Ticket 2 — FILED 2026-08-05 as INFRA-3508 (stage+prod VPCs; linked to 3507 and AI-1538).

Title: Bedrock Mantle interface endpoint + private DNS for the stage and prod EKS VPCs

online-civ-service calls bedrock-mantle.us-east-1.api.aws. In dev this needed three pieces before
traffic actually went private, so bundling them here — please apply the same set to BOTH the stage
EKS VPC and the prod EKS VPC (each VPC needs its own endpoint; dev's covers neither):

* Please create the Interface endpoint `com.amazonaws.us-east-1.bedrock-mantle` in each VPC with
  Private DNS enabled, HTTPS allowed from the pod/node path, and an endpoint policy that permits
  the two bedrock-mantle actions.
* Please also wire the DNS path so workloads actually resolve the private addresses — in dev the
  fix was pointing the cluster's CoreDNS forward at the Route 53 inbound resolver (see INFRA-3474).
  Whatever each VPC's equivalent is, the endpoint isn't live until an in-cluster lookup returns
  the endpoint ENIs.
* AZ note from dev: the endpoint service offers us-east-1a/1b/1d. Please put ENIs in every one of
  those that overlaps each cluster's subnets — in dev we only covered 1a/1b and the 1c nodes
  permanently cross AZs.

Happy to validate from our side as soon as each is in — we have a one-command check.

---

## Ticket 3 — file when model + QPS land (numbers pre-computed 2026-08-05 for 100 RPM: ~400-450k
input TPM gross, ~16-20B input tokens/month flat-rate; scale linearly for `<N>`)

Title: Bedrock Mantle quota increase for online-civ-service — <model>, prod (+ stage if separate account)

We're launching online-civ-service at up to <N> QPS against <model id> on Bedrock Mantle,
us-east-1, account <prod account>. At ~4-4.5k input / ~20-60 output tokens per request that's
roughly <N x 60> RPM and <computed> input TPM, and AWS guidance is to request 2-3x headroom.
Mantle-cohort models don't appear in Service Quotas, so this goes through AWS Support — we have an
open thread with our account team (Darcis/Sushant) that this can ride. Could you file/own the
increase, or should we drive it through the account team directly?

Stage note: quotas are per-account. If stage pods run in the prod account, the increase above
covers stage too; if stage has its own account, its default quotas should carry test-scale
traffic — we'll flag separately if stage load tests need a bump. (Which account each environment's
EKS runs in is part of the account/dc question in Tickets 1-2.)
