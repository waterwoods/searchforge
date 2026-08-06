# SearchForge Next AI Wedge Decision V1

**Date:** 2026-08-05  
**Constraint:** No major rewrite. Reuse catalog assets. Prefer evidence over features.  
**Context:** Accident Story restricted pilot is `READY FOR FOUNDER GO/NO-GO`; Chen activation **not** executed.

### Immediate vs next wedge

| Horizon | Action | Type |
|---------|--------|------|
| **Now (not a new build)** | Founder GO/HOLD/NO-GO → ≤5 real QA cases if GO | Evidence gathering on **current** wedge |
| **NEXT PRIMARY WEDGE** | Choose one adjacent AI workflow below | Build only after real feedback signals |

---

## Scoring method

Scores 1–5. Higher is better except **operational risk**, **compliance risk**, and **founder effort** where higher = worse (more costly).  
**Composite** = sum of “good” dimensions − risk/effort dimensions (max theoretical shown for ranking only).

Good (+): pain, WTP, time-to-pilot, reuse, differentiation, FDE portfolio, recurring revenue  
Bad (−): ops risk, compliance risk, founder effort  

---

## Option A — Broker-controlled missing-document follow-up drafting

**Idea:** When broker sends Request More, AI drafts customer-facing ask + checklist; broker edits/sends; customer continuation unchanged.

| Dimension | Score | Note |
|-----------|------:|------|
| Immediate customer pain | 5 | Daily WeChat chase is the office grind |
| Willingness to pay | 4 | Direct labor reduction story |
| Time to pilot | 4 | Request More + Mini Program already Founder-validated |
| Reuse of current assets | 5 | Confirm layers, flags, metrics, timeline, gates |
| Differentiation | 4 | Human-in-loop follow-up agent, not chatbot toy |
| Operational risk | 2 | Stays inside existing commands |
| Compliance risk | 2 | No coverage advice if copy is request-only |
| Founder effort | 3 | Needs Chen wording review |
| FDE portfolio value | 5 | Classic Applied AI “assist don’t decide” |
| Potential recurring revenue | 4 | Sticky daily workflow |
| **Composite (good−bad)** | **24** | 5+4+4+5+4+5+4 − (2+2+3) |

---

## Option B — Office daily next-action assistant

**Idea:** End-of-day / queue view: ranked cases with suggested next broker action from projection + gaps (still broker-confirmed).

| Dimension | Score | Note |
|-----------|------:|------|
| Immediate customer pain | 4 | Queue anxiety is real |
| Willingness to pay | 3 | Valuable but easier to dismiss as “fancy list” |
| Time to pilot | 3 | Needs careful UX; projections exist |
| Reuse of current assets | 4 | Next-action projection + metrics |
| Differentiation | 3 | Many dashboards exist |
| Operational risk | 3 | Wrong ranking could mis-prioritize |
| Compliance risk | 2 | If no legal advice |
| Founder effort | 3 | Broker trust calibration |
| FDE portfolio value | 4 | Ops-copilot narrative |
| Potential recurring revenue | 3 | Nice-to-have vs must-have |
| **Composite** | **17** | 4+3+3+4+3+4+3 − (3+2+3) |

---

## Option C — Inbound WeChat message triage → case draft

**Idea:** Paste/forward inbound WeChat → classify intent → draft case / route (add-car vs claim vs service).

| Dimension | Score | Note |
|-----------|------:|------|
| Immediate customer pain | 4 | Inbox chaos is real |
| Willingness to pay | 3 | Overlaps with existing triage demo history |
| Time to pilot | 2 | Large `triage.py` surface; scope risk |
| Reuse of current assets | 3 | Triage engine exists but is heavyweight |
| Differentiation | 3 | Crowded “AI inbox” category |
| Operational risk | 4 | Mis-route creates office fire drills |
| Compliance risk | 3 | Intent errors → wrong advice path |
| Founder effort | 4 | Easy to reopen sprawling engine |
| FDE portfolio value | 3 | Less clean than bounded LangGraph story |
| Potential recurring revenue | 3 | |
| **Composite** | **10** | 4+3+2+3+3+3+3 − (4+3+4) |

---

## Other ideas considered (not top three)

| Idea | Disposition |
|------|-------------|
| Claim evidence package assembly for carriers | Postpone — compliance + incomplete media AI |
| Renewal / policy-service workflow | Postpone — no Accident Story learning yet |
| Customer document understanding (VIN/PDF AI) | Partial OCR path exists; postpone as primary wedge |
| Broker outbound communication drafting (general) | Fold into Option A specifically for Request More |

---

## Recommendation

### NEXT PRIMARY WEDGE

**Broker-controlled missing-document follow-up drafting (Option A)**

**Why:** Highest reuse of the proven confirm / Request More / kill-switch / metrics stack; maps to daily office pain; lowest rewrite pressure; strongest FDE “bounded assistive AI” story after Accident Story.

**Do not start coding Option A until:** Founder has a GO/HOLD/NO-GO outcome and at least initial real-case signal (even HOLD with qualitative feedback counts). Building A before learning from Accident Story risks parallel unfinished wedges.

### Secondary experiment

**Office daily next-action assistant (Option B)** — thin, read-only suggestions on existing projections; no new lifecycle mutations. Useful portfolio demo if Option A slips.

### Postpone

**Inbound WeChat full triage rewrite (Option C)** and renewal/carrier-package AI — high sprawl, weaker differentiation, higher mis-route risk.

---

## Anti-goals for the next wedge

- No new agent framework  
- No Production flag for Accident Story without real evidence  
- No coverage/liability generation  
- No synthetic-only “success” declared as commercial win  

---

## Decision log (Founder fills)

| Field | Value |
|-------|-------|
| Date | |
| Agree with primary wedge A? | Yes / No / Modify |
| Accident Story GO/HOLD/NO-GO | |
| Earliest build start for A | After N real cases / After HOLD retrospective |
