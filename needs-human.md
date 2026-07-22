# Needs Human

Varun's decision inbox. Conflicts, contradictions, and open decisions that only human conversation can resolve — the stuff his job actually consists of. Agents file here instead of silently picking a side; Varun resolves in the background and answers inline (one line is enough) or just tells any session.

**Lifecycle:** agent appends entry (status `open`) → Varun adds a `resolution:` line (status `answered`) → next steward session harvests: durable *why* → `log/`, changed facts → `map/`, then deletes the entry (git history keeps it). File short = inbox clean.

**Rules:** append at bottom; write only your own entries; this file is the one exception to single-writer (shared inbox — slack-claude contributes via deposits). Never mark another agent's entry resolved without a Varun answer.

Entry template:

```
## Q-YYYY-MM-DD-<n> — <short title> (open)
- raised: <date>, <agent>
- project: <map file>
- conflict/decision: <the two sides, or the missing decision>
- why it matters: <what's blocked or what calcifies wrong>
- ask: <the one question, answerable in one line>
- resolution: (pending)
```

---

## Q-2026-07-21-01 — Qwant: can they send locale + timezone? (open)
- raised: 2026-07-21, slack-claude (digest), filed by laptop
- project: pciv-live-integration
- conflict/decision: Claire Conklin's tracker records Qwant as unable to send region, locale, AND timezone. Dhaval Shah pushed back (only region is truly impossible; locale/timezone are easy and not privacy-sensitive), and Camille Baudou later relayed Qwant saying locale & timezone "should be fine." Tracker and thread now disagree.
- why it matters: locale/timezone availability changes pCIV extraction and eval assumptions downstream; if the tracker's "cannot" calcifies, integration gets designed against the wrong constraint before the mid-Aug launch.
- ask: confirm with Claire/Camille what Qwant will actually send (locale? timezone?) and get the tracker corrected — then answer here.
- resolution: (pending)
