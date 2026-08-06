# SearchForge Business Value Review V1

**Date:** 2026-08-05  
**Lens:** Chinese-speaking California auto insurance broker office (Chen-style)  
**Evidence base:** Founder-validated Claim path + synthetic Accident Story pilot freeze  
**Rule:** No invented dollar savings. Separate demonstrated / likely / unproven.

---

## 1. What work does it reduce?

| Work today (office reality) | Product effect | Evidence class |
|----------------------------|----------------|----------------|
| Re-typing chaotic WeChat accident stories into notes | Guided AI draft + structured Must-Have fields | **Likely** (synthetic + Founder UX); not timed on real Chen cases |
| Chasing missing time / location / injury | ≤3 targeted follow-ups then confirm | **Demonstrated technical**; **likely** customer value |
| Re-asking known policy/vehicle facts | Known-customer prefill + confirm | **Demonstrated** (Stage 2 Founder phone) |
| Broker hunting “what’s next” on incomplete cases | Workbench next-action projection + Request More loop | **Demonstrated** (Stage 1) |
| Reconstructing “what customer said vs what we assumed” | Original / AI / confirmed Brief layers | **Demonstrated technical** |

---

## 2. What mistakes does it prevent?

| Mistake | Control | Evidence |
|---------|---------|----------|
| Treating AI draft as office truth | Confirm stamp + Brief labels | Unit + synthetic scorecard |
| Coercing unknown injury → “no” | Guardrail + golden + canary | Synthetic 0 violations |
| Duplicate / stranded active cases | One-active-case routing | Founder phone isolation |
| Accepting materials while Request More open | Accept block | Commit `91b20af` + Stage 1 |
| AI outage blocking intake | Kill switch + manual path | Rehearsal case 5 + safety tests |
| Logging raw accident text to traces | Redaction + clean pilot project | LangSmith evidence packs |

---

## 3. What becomes faster?

| Step | Faster how? | Measured? |
|------|-------------|-----------|
| First structured accident facts | Propose + guided questions vs blank form | Synthetic latency ~2–3s propose; **not** end-to-end office minutes |
| Broker first open → understand case | Brief layers + next action | Timing instrumentation exists; **no real Chen p50** |
| Missing-doc loops | Request More already shortens WeChat chaos | Founder-validated path; time-saved **unproven** |

---

## 4. What can be measured?

Already instrumented (synthetic-ready):

- `proposals_created`, fallbacks, timeouts, invalid outputs  
- Follow-up question count (≤3 gate)  
- Unknown-injury violations  
- Latency / p95  
- Completion after fallback  
- Broker first-opened timing (Real Usage Timing V1)

**Not yet measurable honestly:** dollars saved, hours/week saved, paid conversion, NPS, carrier cycle time.

Exporter: `scripts/export_accident_story_pilot_metrics.py` · support deployment-manifest fields.

---

## 5. What would make an office pay?

**Inference (not proven):**

| Payment driver | Why plausible | Proof needed |
|----------------|---------------|--------------|
| Fewer incomplete first messages | Less broker rework | ≥4/5 real cases complete without tech support |
| Fewer “AI lied / we assumed” disputes | Confirm layers | 0 unconfirmed-as-fact in real cases |
| Reliable when AI fails | Manual path | Real fallback used without abandoned claim |
| Fits WeChat habit | Mini Program already in channel | Chen staff actually use Start Claim |

**Unproven commercial assumptions:** willingness to pay monthly SaaS; preference vs free WeChat notes; multi-office expansion economics.

---

## 6. What remains too experimental?

- Live LLM accuracy on messy real dialect / mixed Chinese-English stories  
- Broker trust behavior under time pressure (may still copy AI draft)  
- LangSmith historical cleanup debt (non-blocking but messy for demos)  
- Any claim of Production readiness  
- Pricing, contracts, multi-office rollout

---

## 7. What evidence must come from five real cases?

From Go/No-Go thresholds (`ACCIDENT_STORY_FIVE_CASE_GO_NO_GO_V1.md`):

1. 0 unknown→no  
2. 0 unconfirmed AI shown as customer facts  
3. 0 new raw PII in traces  
4. ≤3 questions  
5. ≥4/5 complete without technical support  
6. Next action clear every case  
7. Qualitative: did broker time-to-first-understanding feel shorter? (founder’s judgment — not a dollar claim)

---

## 8. What should not be built until real feedback exists?

| Do not build yet | Why wait |
|------------------|----------|
| New AI vertical (renewal bot, coverage advisor) | Current wedge unproven commercially |
| Carrier auto-submit | Compliance + trust |
| Multi-tenant enterprise IAM / Stripe | Out of paid-pilot scope |
| Unbounded “office agent” that mutates lifecycle | Violates safety boundary that already works |
| More synthetic canaries without a decision | Freeze already sufficient for GO/NO-GO |
| Production Accident Story enablement | Explicitly gated |

---

## Separation summary

| Class | Contents |
|-------|----------|
| **Demonstrated technical value** | Deterministic Claim loop; Guided Intake UX; confirm layers; kill switch; golden/canary gates; durable metrics plumbing |
| **Likely customer value** | Less retyping; clearer missing asks; safer AI use; clearer broker next action |
| **Unproven commercial assumptions** | Paid conversion; hours saved; accuracy on real Chen traffic; expansion beyond one office |

**Bottom line:** The product is ready to **learn from ≤5 real restricted cases**, not ready to claim product-market fit or Production AI.
