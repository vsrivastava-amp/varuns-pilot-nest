# k8s CD playbook (ArgoCD via cd-deploy-configs + cd-releases)

*(Living reference. Started 2026-07-23 while planning the pciv-online dev deployment.)*

Two Bitbucket repos, both cloned under `~/Documents/`:

## cd-deploy-configs — the manifests (kustomize)

- Layout: `apps/<app>/base/` (Deployment/Service/Ingress templates) + `apps/<app>/<env>-<dc>[-<feature>]/` overlays (kustomization + config.conf envs + image tag pin).
- **Branch = environment**: `master` holds dev-ric1 + stage-ric1 overlays; `prod` branch holds prod-ric1. A local checkout may be sitting on `prod` — check `git branch --show-current` before concluding an overlay "doesn't exist"; read other branches via `git show origin/master:apps/<app>/…`.
- **Auto-sync is ON** (Application `syncPolicy.automated` + selfHeal): merging to the tracked branch deploys within minutes. Deploy = PR that bumps `images[].newTag` in the overlay's kustomization.yaml (see history: "Update llm-evaluator-service dev-ric1 image to …").
- Common per-app wiring (from llm-evaluator-service): secrets as `akeyless:/<app>/<env>/<dc>/…` env values (akeyless/enabled annotation), `serviceAccountName: wi-<app>` (workload identity), imagePullSecret `docker-registry-access-token-ampdockercirw`, Datadog labels `tags.datadoghq.com/{env,service}`, ingress via external-dns hostname `<env>-<app>.ric1.admarketplace.net` (VPN-only), ingressClassName per app family (`llm-eval`).

## cd-releases — the ArgoCD Application registry

- Layout: `<env>/<dc>/<env>-<app>.yaml` ArgoCD `Application` CRs; `DECOM/` subdir = stop running. Dev apps: `namespace: npe-argocd`, destination dev EKS `https://810C5935E63AEA0039E695BACDEA9D4B.gr7.us-east-1.eks.amazonaws.com`, `targetRevision: HEAD` of cd-deploy-configs, path to the overlay.
- Gotcha: an app can be running without its Application yaml on master — llm-evaluator-service's live in unmerged branches `AI-1371` (dev+stage) / `AI-1371-prod` (prod). Registration is evidently applied out-of-band by infra; confirm the process before assuming a master merge registers an app.
- `ignoreDifferences` on /spec/replicas + HPA managedFields — keep when copying, or Argo fights the HPA.

## Gotchas

- llm-evaluator-service dev/stage/prod URLs: `{dev|stage}-llm-evaluator-service.ric1.admarketplace.net` (VPN only; unreachable from sandboxed shells).
- Image tags: `<ver>.<build>-<branch>` from the service repo's bitbucket-pipelines CI on every push — dev overlays can pin feature-branch tags (e.g. `1.0.266-feat-civ-eval-id-3`).
- Agent guardrail: merges auto-deploy ⇒ agents prepare feature branches/PRs only; humans merge. PRs beyond dev branches → REVIEW.md.
