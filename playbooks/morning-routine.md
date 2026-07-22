# Morning routine playbook

*(Living reference. Started 2026-07-22 from the first live run. Invocable as `/morning-routine` in Claude Code — the skill points here.)*

Goal: by the time Varun finishes coffee, he has (a) a Jira digest with attention flags, (b) a pasteable sweep ask for Slack Claude, and (c) once Slack Claude responds, one integrated digest in `state/`.

## Steps

1. **Nest sync** (the standard 60-second ritual): `git pull --rebase`, `git log --oneline -15`, skim `tasks/queue.md`, `REVIEW.md`, `needs-human.md`. Note the date of the most recent digest in `state/` and the most recent `log/*--slack.md` entry — sweeps ask for *deltas since then*, not re-coverage.

2. **Compose the Slack Claude sweep ask** (Varun pastes it; we never send). Per `playbooks/slack-claude.md`:
   - Confirm any of its deposits that landed since its last session (commit hash) — it treats deposits as un-landed until acked.
   - Ask for deltas since the last digest date: known anchors (#pub-onboarding-qwant-ai) **plus open-ended scope** — anything it judges relevant to Varun's four streams; ask it to name the channels it checked (promote good ones to `map/`).
   - Anything mentioning Varun; anything urgent-looking.
   - Remind: deposit via 🪺 NEST DEPOSIT / NEST NOTE / artifact link; a laptop session is live to apply.

3. **Jira sweep** — background subagent, GETs only, per `playbooks/jira.md`:
   - Probe `/myself` first; dead credential → park and tell Varun (guardrail 5).
   - Sweeps: `text ~ "PCIV"` and `text ~ "Qwant"` updated in last ~3 days; anchor issues from `map/*.md` (individually, with recent comments); `assignee = currentUser()` and `reporter = currentUser()` updated in last week; `project = AI` updated since yesterday.
   - Known noise: bulk operations stamp identical `updated` timestamps across many issues (e.g. sprint rolls) — filter unless comments/status actually changed.
   - Output: digest by stream, **attention flags first** (commitments coming due, things waiting on Varun, incoming asks).

4. **Deliver** the Jira digest + sweep message in chat. Lead with attention flags.

5. **Integrate** when Varun pastes Slack Claude's response: apply any deposit (per `playbooks/slack-claude.md` rules — own-files only, proposals to REVIEW.md), then write the merged Slack+Jira digest to `state/digest-YYYY-MM-DD.md`, commit, push.

6. **Close out**: run log in `runs/YYYY-MM-DD-<slug>.md`; fold any new gotchas into the relevant playbook; surface conflicts/decisions to `needs-human.md`.

## Gotchas learned

- 2026-07-22 — Jira bulk-update noise: ~20 AI issues shared one `updated` timestamp (2026-07-21 19:47 UTC); real activity means new comments or transitions, not timestamps.
- 2026-07-22 — Verify agent paraphrases against source before Varun acts on them (re-fetch the actual comment thread for anything that drives a decision).
- 2026-07-22 — Jira writes (transitions etc.) are OK when Varun directs them in-chat — that *is* the approval; log the write in the run file. Agent-initiated writes still go through `REVIEW.md`.
