# Gap Analysis Spec

**Purpose:** Tie gaps to **product goals** and **commercial consequences** — not generic advice.

**Assessment date:** 2026-03-25

---

## 1. Sellability gaps

| Gap | Tied to goals | Why it hurts sales |
|-----|---------------|-------------------|
| First-screen does not always read as a **narrow intake product** | 2, 12 | Broker judges in seconds; dense workbench-adjacent UI can trigger “too complex / internal tool.” |
| **Pilot logistics** (production URL alignment) not fully proven | 8 | Hard to run a paid pilot smoothly if deploy path is fuzzy — undermines “professional service.” |
| **Semantic inconsistency** on flagship add-car edge (`quote_ready` vs `still_needed`) | 3, 4 | A broker who catches one wrong chip may distrust the whole card. |

---

## 2. Broker credibility gaps

| Gap | Tied to goals | Why it hurts trust |
|-----|---------------|-------------------|
| **LLM/rule brittleness** + mandatory human review not always visible in UI | 5 | If the UI feels “authoritative,” brokers may forward drafts without the mental model the team holds internally. |
| **Wrong-office risk** when client pack incomplete (silent fallback to default client) | 5, 6 | Credibility disaster if second broker sees Chen-specific tone. |
| **Engine-resident customer-visible strings** on some branches | 6, 10 | Breaks the story that “voice is client-owned everywhere.” |

---

## 3. Hot-plug / same-industry replication gaps

| Gap | Tied to goals | Notes |
|-----|---------------|--------|
| Default `chen_kui` + Chen-flavored `DEFAULT_UI_COPY` | 6, 10 | Fine for first broker; must be documented for second. |
| Industry `markers.json` historically broker-specific tokens | 6, 10 | Drill report flagged; partially addressed (`转接人工` fallback) — **audit remaining tokens**. |
| Add-car rules + soft-route inbox shared, not per-client | 6 | Acceptable if honest; limits “voice-only” swaps. |
| Stitched / branch strings still partially in `triage.py` per drill | 6 | Ongoing externalization debt. |

---

## 4. Engineering stability gaps

| Gap | Tied to goals | Notes |
|-----|---------------|--------|
| **Single-file JSON** case store | 7 | Appropriate for pilot if ops understand backup/limits; not a “stability bug” if scoped honestly. |
| Large monolithic UI module | 12 | Increases regression risk and slows safe iteration — **process** gap more than runtime fragility. |
| Dependency on LLM availability for “best” outputs | 5, 9 | Guardrails often use `LLM_GENERATION_ENABLED=0` — good — but live pilot may run with LLM on; monitor drift. |

---

## 5. What can wait (explicit)

| Item | Why wait |
|------|----------|
| Multi-tenant auth, Stripe | Out of scope per paid pilot goal |
| Full CRM / inbox connectors | Explicit non-goals; would violate simplicity (12) |
| OCR | Deferred in standard package |
| “Perfect” second-broker voice on every rare branch | Diminishing returns before first paid testimonial |
| Enterprise database migration | Only after pilot proves paste workflow value |

---

## 6. Gap → goal matrix (compressed)

| Gap theme | Goals impacted |
|-----------|----------------|
| Customer-facing clarity / portal feel | 2, 12 |
| Case card truthfulness | 3, 4 |
| Client isolation / wrong-office | 5, 6, 10 |
| Pilot operations / deploy evidence | 8 |
| Narrative oversell vs build | 1, 11, 12 |

---

*End of gap analysis spec*
