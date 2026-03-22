# Founder Inspection Notes — Add-Car Commercial Flow Hardening

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** What founder should inspect; Vercel tests; "good enough to show as flagship."

---

## 1. What Founder Should Inspect After Sprint

| Area | What to Check |
|------|---------------|
| **First-scan clarity** | Open add-car case; understand in 3–5 seconds? |
| **Quote-ready visibility** | Tag above fold on case and queue card? |
| **Contact visibility** | Name, phone or "needed" above fold? |
| **Attachment visibility** | Materials received / optional above fold? |
| **broker_next_step** | "Run quote for {vehicle}. Confirm delivery/driver. Confirm name/phone."? |
| **Correction** | "不是X5，是X3" → collected shows X3? |
| **No redundant ask** | Never ask for field already provided |

---

## 2. Exact Vercel Test Cases (4–6)

| # | Input | Expected |
|---|-------|----------|
| 1 | 加车 2024 Tesla Model Y → 90210 下周提车 | Handoff T2; summary has year, model, zip, delivery; broker_next_step mentions vehicle |
| 2 | 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么 | Answer garaging; handoff T2 |
| 3 | 加车 2021 Honda → 不是这个 是 2024 Tesla Model Y → 90210 下周提车 | Handoff T3; collected shows 2024 Tesla; correction badge |
| 4 | 加车 2024 Tesla Model Y → 90210 下周提车 → 对了 是我老婆开 | Ask driver T2; handoff T3 with driver |
| 5 | 想加车 顺便 coverage 可以调吗 | Answer coverage briefly; collect add-car; no handoff T1 (need vehicle) |
| 6 | 加车 2024 X5 90210 下周提车 我开 | Handoff T1; full info; broker sees contact needed if no name/phone |

---

## 3. Add-Car + Contact Test Cases

| # | Test | Expected |
|---|------|----------|
| 7 | Add-car + "我叫张三 555-1234" in chat | Contact extracted; broker sees name, phone |
| 8 | Add-car quote-ready, no name/phone | broker_next_step says "Confirm name and phone for follow-up" |

---

## 4. Add-Car + Attachment Test Cases

| # | Test | Expected |
|---|------|----------|
| 9 | Add-car + upload registration | "Quote-ready · Materials received"; attachment in case detail |
| 10 | Add-car chat-only, no upload | "Quote-ready · Registration/dec page optional" |

---

## 5. Queue Card Scan Test

| # | Test | Expected |
|---|------|----------|
| 11 | Load founder demo queue; scan add-car cards | Quote-ready tag visible; contact status visible; attachment badge when present |
| 12 | Open add-car case | All key signals above fold; no scrolling to find broker_next_step |

---

## 6. What "Good Enough to Show as Flagship" Looks Like

- **No awkward moments** — No "please provide more context" for clear add-car
- **Broker receives useful case** — Concrete vehicle, zip, delivery/driver; contact when collected
- **broker_next_step tells broker exactly what to do** — Run quote, confirm delivery/driver, confirm name/phone
- **Corrections and late details captured** — Same case; latest wins
- **Side questions answered** — Garaging, coverage before handoff
- **3–5 second scan** — Broker understands without deep reading
- **Queue cards informative** — Can prioritize without opening every case

---

## 7. What to Watch For

| Risk | Mitigation |
|------|------------|
| Overcrowded UI | Keep above-fold minimal; secondary below |
| Vague broker_next_step | "Run quote for {vehicle}" not "Review and act" |
| Buried signals | Correction, contact, attachment must be visible |
| Scope creep | No OCR, no carrier, no mandatory attachment |

---

## 8. Pre-Demo Checklist

- [ ] guardrail_inbox_triage.sh PASS
- [ ] run_handoff_timing_simulations.py PASS
- [ ] demo_quick_validate.sh PASS
- [ ] 4–6 Vercel test cases pass
- [ ] Add-car case opens with all signals above fold
- [ ] broker_next_step feels like real office instruction

---

*See also: 07_ACCEPTANCE_COMMERCIAL_HARDENING_CRITERIA.md, docs/STANDARD_SCENARIO_PACKAGE.md*
