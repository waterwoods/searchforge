# Constitution Enforcement

**Version:** V1 (P16-S)  
**Date:** 2026-06-01  
**Status:** Mandatory gate before sprint close or feature merge  
**Authority:** `CAPABILITY_MAP_V1.md`, `contracts/CAPABILITY_*.md`, Constitution V1

---

## Purpose

Every sprint must prove it improves a **capability contract** with **evidence** — not merely ship code, docs, or local PASS scores.

If this checklist fails, answer **"Why are we building it?"** before proceeding.

---

## Enforcement questions

Complete for every sprint. Copy into sprint FINAL_VERDICT or PR description.

### 1. Capability alignment

| # | Question | Answer |
|---|----------|--------|
| 1 | **Does this sprint improve a capability?** | ☐ Yes ☐ No |
| 2 | **Which capability?** (exactly one primary) | Cap ___ : _________________ |
| 3 | **Which contract?** | `contracts/CAPABILITY___*.md` |
| 4 | **What score changes?** | Pre: ___ → Post: ___ (Δ ___) |
| 5 | **What evidence exists?** | Link: _________________ |

### 2. User impact

| # | Question | Answer |
|---|----------|--------|
| 6 | **Would a user notice?** | ☐ Yes ☐ No — If No → **STOP** |
| 7 | **Which user?** | ☐ Founder ☐ Role C ☐ Broker ☐ Assistant ☐ Customer |
| 8 | **On which URL?** | ☐ Localhost ☐ Preview ☐ Production — *Localhost alone insufficient for user-facing sprint* |
| 9 | **Would a payer notice?** | ☐ Yes ☐ No ☐ N/A |
| 10 | **Would Chen Kui care?** | ☐ Yes ☐ No — If No → justify below |

### 3. Justification (required if any "No" above)

| # | Question | Answer |
|---|----------|--------|
| 11 | **Why are we building it?** | |
| 12 | **Is this infra/docs-only with deploy impact next sprint?** | ☐ Yes ☐ No |
| 13 | **Does it reduce a top-10 failure pattern?** | FP-___ : _________________ |

---

## Pass / Fail rules

### Pass

- Q1 = Yes
- Q2–Q5 filled with specific contract + evidence
- Q6 = Yes OR Q11 provides valid infra/foundation justification
- Q8 includes Preview or Production for user-facing work
- Q10 = Yes OR sprint is explicitly internal (P16-S style) with Q11 answer

### Fail

- Q1 = No and Q11 empty
- Q6 = No (user-facing sprint)
- Q8 = Localhost only for UI/capability sprint
- Q5 empty or "guardrail PASS" without deployed proof
- Sprint adds UI complexity without deletion budget (violates Contract Simplicity)

---

## Capability quick reference

| # | Capability | Trial-ready threshold | Current P16-R baseline |
|---|------------|----------------------|------------------------|
| 1 | Broker Front Door | 70+ on deployed URL | ~45 deploy / ~70 local |
| 2 | Urgent Message Triage | 80+ | ~85 |
| 3 | Structured Case Record | 70+ | ~72 |
| 4 | Customer Intake Collection | 65+ on share path | ~55 deploy |
| 5 | Case Lifecycle Management | 60+ | ~55 |
| 6 | Trial Conversion | 60+ with evidence | ~40 |
| 7 | Founder / Operator Control | 70+ with E2E log | ~65 |

**Rule from CAPABILITY_MAP_V1:** Every feature, bug fix, UI change, prompt change, or broker trial change must map to **one** capability contract.

---

## Anti-patterns (auto-fail)

| Anti-pattern | Example from P16 | Corrective action |
|--------------|------------------|-------------------|
| Local-only verdict | P16-O 78 local, 64 deployed | Require Preview grep proof |
| Engine sprint ignoring Cap 1 | Cap 2 guardrail PASS, Cap 1 tab wrong | Score all 7 caps |
| Docs sprint claiming payment ready | P16-K closed; invoice IDs empty | Separate doc-complete vs payment-ready |
| UI additions without deletions | P16-M TOP100 list grows | Deletion quota ≥ 3 items |
| Constitution conflict ignored | Add-Car copy on cancellation trial | Check CONSTITUTION_CONFLICT_REPORT |

---

## Sprint type templates

### Feature sprint

```
Cap: ___
Contract: CAPABILITY___
Score: ___ → ___
Evidence: Preview URL + screenshot + bundle hash
User notice: Yes — Broker on Preview
Chen Kui: Yes — Day 0 paste loop
```

### Deploy / parity sprint (P16-R style)

```
Cap: 7 (Founder/Operator) + 1 (Front Door)
Contract: CAPABILITY_07 + CAPABILITY_01
Score: Cap7 65→72, Cap1 45→55 (deployed)
Evidence: P16R_DEPLOYMENT_PARITY_AUDIT.md
User notice: Yes — if cold URL works
Chen Kui: Yes — only if SSO off
```

### Systems / docs sprint (P16-S style)

```
Cap: 7 (Founder/Operator)
Contract: CAPABILITY_07
Score: 65 → 75 (prevention infrastructure)
Evidence: This doc + FAILURE_PATTERN_LIBRARY.md
User notice: No — internal
Chen Kui: No — prevents future waste
Why: Reduce 250hrs historical deploy/reality waste
```

---

## Integration

| When | Action |
|------|--------|
| Sprint planning | Pick primary capability + target Δ |
| Mid-sprint | Re-check Q8 — deploy early, not sprint-end |
| Sprint close | Complete this form → POST_SPRINT_HEALTH_CHECK |
| Trial week | Q9 + Q10 mandatory Yes |

---

## Sign-off

| Field | Value |
|-------|-------|
| Sprint ID | |
| Primary capability | |
| Enforcement result | ☐ Pass ☐ Fail |
| Reviewer | |
| Date | |

---

*End of Constitution Enforcement V1 — P16-S*
