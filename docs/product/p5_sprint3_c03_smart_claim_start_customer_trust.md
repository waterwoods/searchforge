# P5 Sprint 3 — C03 Smart Claim Start · Gate 2 Customer Trust

**Status:** Implementation complete — **awaiting Founder Preview review**  
**Date:** 2026-07-25  
**Capability:** C03 Smart Claim Start (presentation only)  
**Governing law:** `docs/product/p5_master_execution_plan.md` · `docs/product/p20_product_north_star.md` · Cap 03 contract  
**Consumes:** C01 `LookupResult` + C02 `PrefillResult` (frozen — not redesigned)

---

## One objective / Out of scope

**ONE OBJECTIVE**

Translate Lookup + Prefill into the simplest Start Claim experience so a first-time customer feels:

> “They already know me. I can immediately tell my story.”

**OUT OF SCOPE (hard stop)**

- AMS / CRM / EZLynx / Epic  
- Notification / Timeline / Broker Brief  
- Redesign of C01 Lookup or C02 Prefill  
- Expanding Start Claim Must Haves  
- Customer-facing flag ON in pilot (QA Preview only after Founder GO)

---

# 1. Working C03 implementation

## Call chain (locked)

```text
Workflow V2 (c03_start_entry)
        ↓  lookup_customer (C01)
LookupResult
        ↓  prefill_from_lookup (C02)
PrefillResult
        ↓  build_smart_claim_start_plan (C03)
SmartClaimStartPlan
        ↓
Mini Program smart-claim-start-panel + start-claim form
```

## Code map

| Layer | Path | Owns |
|-------|------|------|
| **Workflow** | `…/workflow_v2/c03_start_entry.py` | When to call C03; trust invariants summary |
| **Capability plan** | `…/smart_claim_start/engine.py` | Modes, chips, soft notices, CTAs, screens |
| **HTTP / MP wire** | `…/smart_claim_start/service.py` + route | Cap 01→02→03 response |
| **MP UI state** | `miniapp/utils/smartClaimStartPlan.ts` | Plan → UI (blank escape, soft confirms) |
| **MP panel** | `miniapp/components/smart-claim-start-panel/*` | Trust copy + CTAs |
| **MP page** | `miniapp/pages/start-claim/*` | Accident form lands under plan |
| **Tests** | `tests/test_p5_sprint3_c03_smart_claim_start.py` | Trust + boundaries |
| **Sim** | `scripts/simulate_p5_sprint3_c03_smart_claim_start.py` | Founder PASS report |

## Commands (PASS on 2026-07-25)

```bash
P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 -m pytest \
  tests/test_p5_sprint3_c03_smart_claim_start.py \
  tests/test_p4_capability_03_smart_claim_start.py \
  tests/test_p4_integration_01_smart_claim_start_wiring.py -q

P4_CUSTOMER_LOOKUP_MOCK=1 PYTHONPATH=. python3 \
  scripts/simulate_p5_sprint3_c03_smart_claim_start.py

cd miniapp && node --import tsx --test tests/smartClaimStartPlan.test.ts
cd miniapp && npm run build:gate
```

**Result:** pytest green · P5 sim `RESULT: PASS` · MP tests 12/12 · **Build Gate PASSED**  
Flags remain **OFF** by default (`smartClaimStartEnabled: false`, Lookup mock OFF in pilot).

---

# 2. Customer journey walkthrough

| Path | Mode | What the customer sees | Next action |
|------|------|------------------------|-------------|
| **Unambiguous** (S3) | `MATCHED_KNOWN` | Chip strip “办公室已了解您” + headline **今天发生了什么？** — no chooser, no confirm quiz | Cursor on accident story |
| **Multi-vehicle** (S2) | `MATCHED_CONFIRM_VEHICLE` | One question: 哪辆车出险？ → then story | One tap, continue |
| **Stale policy** (S4) | `MATCHED_CONFIRM_POLICY` | Friendly notice: 保单我们会再核对 — **仍可先报案** | Story available immediately |
| **Lookup down / not found** (S5/S6) | `BLANK_DEGRADE` | Same Pilot blank form. No error wall. No fake identity. | Tell the story |
| **Ambiguous** | `CONTACT_BROKER` | Primary **联系陈总** + secondary **仍要先报案** | Never trapped |
| **Active case** (S1) | `CONTINUE_ACTIVE` | Continue current case only | No second create |

### Founder Reality Walk (Preview checklist)

1. Cold open → shell before network (Nav Gate)  
2. `?entry=form&scs=S3` → chips + story in one breath  
3. `scs=S2` → one vehicle decision → story  
4. `scs=S4` → never reads as “不能报案”  
5. `scs=S5` / `S6` / network fail → blank Pilot form  
6. Ambiguous → Contact **and** blank escape  
7. Submit → Waiting with 陈总 · Home still usable  

---

# 3. Before / After comparison

| Moment | Before (P4 wire / quiz tone) | After (Sprint 3 Customer Trust) |
|--------|------------------------------|----------------------------------|
| Matched single vehicle | “请确认以下信息” + known_context gate feel | “办公室已了解您” chips; no gate screen; lands on story |
| Stale policy | Required confirm; “联系陈总更新保单” could trap | Soft notice; `required_before_accident=False`; always continue |
| Ambiguous | Contact only — dead end for stressed customer | Contact + **仍要先报案** blank escape |
| Copy | Confirm / quiz language | Human office language; no confidence / classifier / adapter |
| Fetch fail | Legacy form (ok) | Explicit silent Pilot blank copy — no technical error |

**Effort (matched path):** ~4 accident inputs (story / time / location / injury). Photos optional.

---

# 4. Customer Trust review

Every screen challenged against:

| Question | Matched (S3) | Multi (S2) | Stale (S4) | Blank (S5/S6) | Ambiguous |
|----------|--------------|------------|------------|---------------|-----------|
| Do I trust this? | Yes — chips, no jargon | Yes — clear one choice | Yes — office will recheck | Yes — calm blank | Yes — two honest options |
| Can I start talking immediately? | Yes | After one tap | Yes | Yes | Via blank escape |
| Do I understand the next step? | 今天发生了什么？ | Pick vehicle → story | Story now | Story now | Contact or story |
| Am I proving my identity? | **No** | **No** | **No** | **No** | Optional contact only |

If any cell had been “proving identity,” that screen was redesigned in this sprint.

**Never exposed to customer:** confidence scores, lookup score, classifier, adapter, policy matching jargon, CRM language, OpenID / person_link / mock IDs.

---

# 5. Founder Challenge report

| Challenge | Verdict | Action taken |
|-----------|---------|--------------|
| Can the confirm-quiz screen disappear? | **Yes** for unambiguous match | Removed `known_context` gate from `MATCHED_KNOWN` screens |
| Can the stale contact trap disappear? | **Yes** | Soft notice only; accident never gated |
| Can ambiguous dead-end disappear? | **Yes** | Secondary **仍要先报案** + MP blank escape |
| Can copy get shorter / more human? | **Yes** | “办公室已了解您。只需告诉我们今天的事故。” |
| Can this become more like Chen’s office? | **Closer** | Named 陈总 CTAs; chips as context, not software confirm |
| Should AMS chooser appear? | **No** | Hard ban — stay in C03 presentation |

**Redesign verdict:** Keep Cap 01/02 contracts frozen. All trust gains live in C03 presentation + Mini Program render. Do not merge C01+C02+C03 into a God capability.

---

# 6. Before Chen’s first demo — change list

| # | Item | Owner | Priority |
|---|------|-------|----------|
| 1 | Founder Reality Walk on **physical Preview** (S2, S3, S5, S6, Ambiguous) | Andy | **P0 before flag ON** |
| 2 | QA only: `P4_CUSTOMER_LOOKUP_MOCK=1` + `smartClaimStartEnabled: true` in local/Preview | Ops | P0 for Preview |
| 3 | Keep both flags **OFF** in pilot until Gate 2 GO recorded | Ops | P0 |
| 4 | Confirm WeChat domain whitelist for QA API host (Build Gate note) | Ops | P0 |
| 5 | Optional: auto-focus accident textarea after matched chips paint | C03 polish | P1 |
| 6 | Do **not** start AMS / Notification / Timeline from demo pressure | Scope | Hard ban |
| 7 | Trust Harden sprint (Sprint 4) after Gate 2 GO — copy variants + Golden QA | Next | After GO |

---

## Architecture / scorecard

| Dimension | Result |
|-----------|--------|
| Reliability | **PASS** — complete plan every path; fail-open blank |
| Simplicity | **PASS** — one decision max before story (vehicle only) |
| Smoothness | **PASS** — unambiguous = chips → story; no quiz |
| Business Value | **PASS** — “easier than calling” path exists |
| Scope Control | **PASS** — C03 only; no AMS / C01 / C02 redesign |

| Gate | Status |
|------|--------|
| Mini Program Build Gate | **PASS** |
| Form Gate (no Must Have expansion) | **PASS** (unchanged Must Haves) |
| Customer-facing flag in pilot | **OFF** (intentional) |
| Gate 2 Customer Trust | **Candidate** — needs Founder Preview GO |

---

## GO / NO GO

| GO | NO GO |
|----|-------|
| Founder Preview: almost no time proving who I am; story is the work; never trapped | Quiz on unambiguous match; ambiguous dead-end; stale “不能报案”; flag ON in pilot without Preview GO |

**This sprint stops for Founder review. Do not authorize AMS or Trust Harden from momentum.**

---

## Future ideas (record only)

- Auto-focus story field on matched paint  
- Voice-first default when chips already filled  
- Household multi-driver soft chip (“不是我开的”) after Pilot evidence  
- Real AMS adapter behind Cap 01 only — never inside C03
