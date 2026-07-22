# PCIV Live Integration — Slack log (slack-claude owned)

Append-only. Date every line (YYYY-MM-DD). Source channel: #pub-onboarding-qwant-ai (C0AUE5JBTAP).
Posture per map/pciv-live-integration.md: monitor + summarize only; no outward action.

## 2026-07-21 — Qwant AI launch: channel digest

Read via workspace search (bot is not a member of the channel; search reaches it, direct fetch is refused).

**Launch timing:** Target mid-August. Earlier debate was Aug 10 vs Aug 24; Dhaval Shah argued for Aug 24 to launch in better shape given the back-and-forth. Claire Conklin's weekly-deliverables post frames the release as mid-Aug.

**This week's tracked deliverables (Claire Conklin, internal):**
- A/B test dashboard update — Jason Yin (green)
- Share working API to Qwant for testing — Norbert Tamas (green; due date to confirm)
- Schedule weekly standup with Qwant — Camille Baudou (yellow)
- Relevance + yield analysis plan — Dhaval Shah (RED/blocked: needs a defined timeline; Dhaval notes yield data won't exist until live, so near-term it's relevance-only)
- Data spec for how Qwant implements the API — Maxime (external, green)
- Ad-format decision by EOW — Amarachi Miller x Sacha

**Data Qwant can/can't send:** Claire's post recorded Qwant as confirming they CANNOT send region code (US only), locale, and time zone. Dhaval pushed back: he believes only region can't be sent; locale + time zone are important, easy, and not privacy-sensitive. Camille later relayed Qwant saying locale & time zone "should be fine." Net: region = no; locale/timezone = likely yes. This contradicts the earlier "done/cannot" line — worth Varun confirming.

**Commercial-intent filtering (open product tension):** Qwant's latest doc says if AMP returns product ads but Qwant validates the query intent as non-commercial, Qwant won't display them for now. Dhaval objects: (1) intent detection won't be 100% accurate, leaving money on the table; (2) an after-the-fact Qwant filter blocks AMP from having served a text ad instead. His preferred fix: Qwant shows what AMP returns, or the 3.0 API is updated so Qwant can request text ads for non-commercial queries. Open question to Brian Quirk: does AMP pay Qwant per ad request?

**France liquidity / relevance (today's live thread):** Dhaval flagged only 7 of 18 eligible advertisers are enabled in France (Qwant's majority traffic is FR) as potential low-hanging fruit for relevance. Camille: only advertisers with 1P tracking are eligible. Elisa Branson: many eligible FR advertisers require redirects, which Qwant doesn't allow, so they weren't set up; enabling them just for the ghost phase could skew coverage/relevance vs. what actually goes live. Brian Quirk: liquidity issues are KNOWN — focus on the endpoint and getting 3.0 installed; won't look at liquidity until 3.0 + ad formats are defined. Dhaval disagrees: liquidity can be parallel-pathed and shouldn't wait for 3.0 (argues 3.0 won't improve relevance since CIV isn't being extracted anyway).

**Text-ads relevance gap:** Text-ad relevancy with Qwant is notably worse than AMP's usual. Working theory (Dhaval): French keywords aren't set up in the system since France/French hasn't been a major market. George Jardine: some brands already have French KWs and he'll audit the EU accounts that have them. Action: update French KWs and track the dates to measure relevance impact before the mid-Aug release.

**Coverage vs relevance tradeoff:** Flagged as a decision needing product/eng + pub/business alignment, especially tricky under Qwant's "must call, must serve" contract.

**Experiments:** Amarachi Miller started experiment ID 38 "Qwant Ghost Relevance Test Extra Bucket 2" (today).

**People (reference):** Dhaval Shah (relevance/product push), Brian Quirk (3.0/endpoint priority), Claire Conklin (PM/tracker), Camille Baudou (Qwant liaison, French speaker), Amarachi Miller (experiments/ad format), George Jardine (French KW audit), Jason Yin (A/B dashboard), Norbert Tamas (API), Elisa Branson (advertiser setup). French speakers: Camille, Pauline, +1; no dedicated French CM. Channel ownership in flux (Steven Wu as of week of 2026-07-20 per map).

Reference: Qwant AI Project Tracker [Internal] (Google Sheet, linked in the channel).
