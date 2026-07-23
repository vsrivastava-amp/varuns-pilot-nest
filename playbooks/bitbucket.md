# Bitbucket playbook

*(Living reference. Started 2026-07-23.)*

## Auth — already solved, nothing to provision

Varun's laptop has a dedicated Bitbucket SSH key wired up:
`~/.ssh/config` → `Host bitbucket.org` → `IdentityFile ~/.ssh/bitbucket`,
`AddKeysToAgent yes`. Plain git-over-SSH just works:

```bash
git ls-remote git@bitbucket.org:admarketplace/dsp-engine.git HEAD   # access probe
git clone --depth 50 git@bitbucket.org:admarketplace/<repo>.git     # shallow is plenty for reading
```

- Clone into the **session scratchpad**, never into the nest.
- Read-only is behavioral (the key is Varun's, full perms) — same rule as
  Jira/Rovo: no pushes, no PR writes; outbound goes through REVIEW.md.
- Verified 2026-07-23 (dsp-engine cloned, source read).

## Gotchas

- **Don't probe the Bitbucket REST API with credentials** — sourcing `.env`
  and curling `api.bitbucket.org` with a token got blocked by the permission
  classifier (2026-07-23). Unnecessary anyway: git-over-SSH covers reading.
  If API access is ever really needed (PR comments, pipelines API), ask Varun
  to run the probe via `!` or add a settings allowlist rule first.
- Bitbucket web URLs in Slack (`bitbucket.org/admarketplace/...`) need Varun's
  browser session — for PR *content*, clone and `git log`/`git diff` the branch
  instead.

## Repo inventory (engines & platform live here; AAS lives on GitHub)

| Repo | What |
|---|---|
| `dsp-engine` | DSP — owns 2.0 auction/pricing/CTR today; AAS routing (`com.adm.dsp.adauction`, `workflow/auction`) |
| `ssp-engine` | SSP — `/di` endpoint, Discover 3.0 front door |
| `amp-discover-model` | ASR/ASV envelope contract (Discover 3.0) |
| `experimentation-platform-service` | targets/experiments config (AAS routing gates) |
| `qe-dsp-engine-api-tests` | DSP regression suite; branch `AI-1539` = AAS-parity pipeline |
| `dsp-engine-data-logging-model-lib` | DSP Kafka logging models |

GitHub org (`admarketplace-gh`): ad-auction-service{,-api,-client}, ctr-inference-service — see `map/aas.md`.
