---
name: morning-routine
description: Varun's daily kickoff — nest sync, compose Slack Claude sweep ask, background Jira sweep, digest with attention flags, integrate Slack deposit when it arrives. Use when Varun says "morning routine", "gm, get started", or similar at the start of a fresh session.
---

Read `playbooks/morning-routine.md` in the nest root and execute it step by step. It is the canonical, living procedure — follow it over anything remembered from prior sessions, and fold improvements back into it when a run teaches something new.

Key invariants (details in the playbook):
- Sweeps ask for deltas since the last digest, not re-coverage.
- The Slack Claude message is composed for Varun to paste — never sent directly.
- Jira sweep runs as a background subagent, GETs only, credential probed first.
- Deliverable ordering: attention flags first, then per-stream detail.
