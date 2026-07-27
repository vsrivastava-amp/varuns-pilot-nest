# review/ — outbound draft gateway (canonical as of 2026-07-27)

One bare file per draft: **exactly what gets pasted/executed, nothing else** — so `cat review/<file>.txt` shows it and copies trivially. Replaces the old REVIEW.md index (deprecated 2026-07-27, Varun-directed; see git history for its final state).

Conventions:
- Name: `YYYY-MM-DD-<slug>.txt` (date = creation). `ls` sorts into a queue.
- Bodies stay bare. No frontmatter, no metadata. A leading `#`-comment block is OK only for action asks (commands to run on approval) where context is safety-critical.
- **Context lives in the creating session's `runs/` entry** (and git log) — write it there, not here.
- **Dispositions happen in-chat with Varun.** There is no disposition file. Every session flags pending drafts to Varun (session-start ritual + a harness hook on Varun's laptop surfaces `ls review/` each turn).
- On ✅ sent/executed or ❌ dropped: acting agent logs one line in its `runs/` file and **deletes the draft**. Git history keeps everything.
- Sensitive handoff staging (e.g. real-user-query CSVs) may sit here **git-untracked** — never commit those; check `git status` before adding.
