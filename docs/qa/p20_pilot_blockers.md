# P20 Pilot Blockers — Chen Kui Mini Program

**Sprint:** P20 Stabilization & Freeze (2026-07-13)  
**Date:** 2026-07-13  
**Source:** Stabilization review of A2b–A2d/e, Product Polish P1–P4c, post-submit supplement, component gates, Workbench vehicle render.  
**Update rule:** After manual DevTools QA, move items between severities and set **Current Status** from checklist/bug log. Do not invent PASS from automation alone.

Related:

- [`p20_devtools_walkthrough_checklist.md`](./p20_devtools_walkthrough_checklist.md)
- [`p20_bug_record_template.md`](./p20_bug_record_template.md)

---

## Critical

### C1 — Full manual DevTools walkthrough not yet executed

| Field | Content |
|-------|---------|
| **Description** | End-to-end customer journey (Entry → Task Home → Story → Basics → Photos → Review → Receipt) has automated coverage and HTTP smoke paths, but the first complete **human** WeChat DevTools checklist has not been signed off. |
| **Impact** | Unknown UI/nav/toast/device quirks can block Chen Kui dry-run; readiness cannot honestly claim QA Environment green. |
| **Suggested Fix** | Execute [`p20_devtools_walkthrough_checklist.md`](./p20_devtools_walkthrough_checklist.md); record FAILs in bug template; attach screenshots. |
| **Current Status** | **Open** — checklist created; all PASS unchecked. |

### C2 — HTTPS + WeChat合法域名 not ready for real phone

| Field | Content |
|-------|---------|
| **Description** | Default / typical DevTools path uses `http://127.0.0.1:8001` with「不校验合法域名」. Real-device pilot requires HTTPS API host + Mini Program request/upload domain whitelist. |
| **Impact** | Phone preview/pilot customers cannot reliably call API or upload photos; blocks Chen Kui on-device dry-run. |
| **Suggested Fix** | Ops: stand up HTTPS pilot API; whitelist domains in MP console; set pilot `apiBaseUrl` (never phone `127.0.0.1`). |
| **Current Status** | **Open** — out of P4a code scope; known ops blocker. |

---

## High

### H1 — Healthy Task Home lacks always-visible「联系陈总」

| Field | Content |
|-------|---------|
| **Description** | Contact broker is wired on error chrome / shell recovery. On a healthy Task Home, customer may have no always-visible contact control without first hitting an error. |
| **Impact** | Recovery story incomplete when customer is confused but not in error state; weaker trust for broker-assisted pilot. |
| **Suggested Fix** | Add secondary/tertiary「联系陈总」on healthy hub bound to existing `onContactBroker` (no new component). |
| **Current Status** | **Open** — noted in P3 polish; not implemented in P4a (QA prep only). |

### H2 — Experience / pilot config not frozen

| Field | Content |
|-------|---------|
| **Description** | Mini Program still reads as prototype: local overrides, `devTaskToken`, localhost defaults possible; no tagged “experience build” freeze for Chen Kui. |
| **Impact** | Risk of shipping wrong base URL / leftover diagnostic config into a live walkthrough. |
| **Suggested Fix** | Freeze pilot config: known token issuance path, strip prototype-only diagnostics, document exact DevTools + API pair for rehearsal. |
| **Current Status** | **Open**. |

### H3 — Real-device / LAN API path unproven

| Field | Content |
|-------|---------|
| **Description** | Phone / 真机调试 against WSL2 `127.0.0.1` fails; LAN IP or Cloud HTTPS path must be verified for photo upload + full journey. |
| **Impact** | Founder cannot rehearse the path Chen Kui’s customer will use. |
| **Suggested Fix** | Document and test `apiBaseUrl` = LAN or Cloud HTTPS; one end-to-end photo upload on real Wi-Fi. |
| **Current Status** | **Open**. |

### H4 — Chen Kui operator reply script missing

| Field | Content |
|-------|---------|
| **Description** | When customer taps「联系陈总」, modal tells them to message 陈总 in WeChat — broker-side reply script / ops path not packaged for rehearsal. |
| **Impact** | Customer reaches broker and may get inconsistent guidance; pilot feels unfinished. |
| **Suggested Fix** | One-page Chen Kui dry-run script (what customer sees + what broker replies). |
| **Current Status** | **Open**. |

### H5 — Review missing items had no edit path

| Field | Content |
|-------|---------|
| **Description** | Review showed missing labels such as「是否有人受伤」「是否报警」but rows were not tappable and「返回我的资料」was the only escape — a High UX dead end. |
| **Impact** | Customer sees what is missing but cannot reach Basics to fix it without leaving Review blindly. |
| **Suggested Fix** | Tappable missing rows + one shared recovery CTA「去补充基本资料」via `resolveMissingItemNav` / `resolveSupplementAction`; refresh on `onShow`. |
| **Expected** | Clear navigation to the relevant page (Basics for injury/police). |
| **Current Status** | **Fixed in code / Manual DevTools verification required** — see `docs/evidence/p20_review_missing_item_edit_path_hotfix_2026_07_13.md`. |

### H6 — Submitted customer actions were repetitive and overlapping

| Field | Content |
|-------|---------|
| **Description** | Submitted Task Home/Receipt exposed overlapping actions (`继续补充资料` / `补充或修改资料` / `继续补充照片` / view variants), increasing cognitive load. |
| **Impact** | Customer uncertainty after formal submit; duplicate CTA surface risks wrong tap path during pilot. |
| **Suggested Fix** | Consolidate submitted flow to one primary CTA `补充或修改资料` with unified action sheet (Story/Basics/Vehicle/Photos), plus one secondary action only. |
| **Expected** | One primary CTA per submitted page, no duplicate supplement buttons, no second formal submit. |
| **Current Status** | **Fixed in code / Manual DevTools verification required** — see `docs/evidence/p20_pilot_ux_consolidation_vehicle_visibility_2026_07_13.md`. |

### H7 — Frontend allows supplement but backend PATCH rejected submitted cases

| Field | Content |
|-------|---------|
| **Description** | Mini Program correctly routed submitted cases to Story/Basics/Photos, but backend `PATCH /api/h5/tasks/{token}/fields` returned `409 already_submitted`, blocking post-submit text supplement. |
| **Impact** | Customer can reach supplement page but save fails; high-severity product mismatch and dead-end risk. |
| **Suggested Fix** | Keep one-time submit idempotent; allow a strict post-submit customer field allowlist on existing PATCH endpoint; write explicit supplement provenance + timeline delta (before/after). |
| **Expected** | Submitted state remains submitted; supplement save succeeds for allowed fields; non-allowed fields rejected; no duplicate formal submit. |
| **Current Status** | **Fixed in code / Manual DevTools verification required** — see `docs/evidence/p20_post_submit_customer_supplement_backend_hotfix_2026_07_13.md`. |

### H9 — Mini Program component Gate 3 (real DevTools compile) not signed

| Field | Content |
|-------|---------|
| **Description** | Gate 1 (file completeness) and Gate 2 (`usingComponents` path/casing) pass via `npm run test:component-gates`. Gate 3 — Founder WeChat DevTools full compile with no `component not found` / `module ... is not defined`, plus visible unified「补充或修改资料」— was **not** re-verified on this freeze for the new A2b–A2d/e components. |
| **Impact** | Experience-version upload can still regress at compile/runtime despite unit tests and Gate1/2 automation. |
| **Suggested Fix** | Clear cache → full compile in DevTools; open Entry/Task Home/Review/Receipt; confirm no component/module errors; confirm unified supplement CTA. |
| **Expected** | Gate1/2 automated green; Gate3 human-signed before experience upload. |
| **Current Status** | **Open** — Gate1/2 PASS on 2026-07-13 freeze; Gate3 **not marked PASS** (do not fabricate). See `docs/evidence/p20_stabilization_freeze_2026_07_13.md`. |

---

## Medium

### M4 — Broker vehicle fields: code path PASS, real browser visibility unclear

| Field | Content |
|-------|---------|
| **Description** | Backend persistence and Broker API projection for `own_vehicle_info` / `other_party_plate` / `other_party_info` PASS in tests. Workbench `ClaimCaseBriefPanel` now renders explicit `车辆与对方` section. Real browser Workbench visibility on a live case remains **unclear** — not marked resolved. |
| **Impact** | Broker may still fail the 10-second vehicle scan in Pilot despite correct data path; treat as manual verification debt. |
| **Suggested Fix** | Open one real claim with vehicle facts in Workbench; confirm 我方车辆 / 对方车牌 / 对方信息 above the fold (or `暂未提供`). Do not redesign in freeze sprint. |
| **Expected** | Real browser case visibly shows the three fields. |
| **Current Status** | **Open — Medium.** Persistence PASS · API PASS · render code implemented · browser visibility **manual / unclear**. |

### M1 — Network failure path not proven in DevTools

| Field | Content |
|-------|---------|
| **Description** | Mapped Chinese network errors exist in code/tests; forcing unreachable base URL in DevTools is still TODO. |
| **Impact** | Possible regression of engineer-facing copy or dead ends under real offline conditions. |
| **Suggested Fix** | Checklist edge X4: unreachable API → Chinese only + Retry + 联系陈总. |
| **Current Status** | **Open** — automation PASS; manual TODO. |

### M2 — Expired / invalid token path not proven live

| Field | Content |
|-------|---------|
| **Description** | Code maps `invalid_or_expired_task_link` to non-retryable contact guidance; live DevTools fixture run still TODO. |
| **Impact** | Customer could loop on Retry instead of contacting broker if wiring drifts. |
| **Suggested Fix** | Checklist edge X5 with expired token fixture. |
| **Current Status** | **Open** — automation PASS; manual TODO. |

### M3 — Basics multi-PATCH partial-save risk (known)

| Field | Content |
|-------|---------|
| **Description** | Basics save may still issue sequential patches; mid-failure can leave partial server confirmation (mitigated in tests with preserve-on-fail UX). |
| **Impact** | Confusing hub state / follow-up with broker if mid-fail during pilot. |
| **Suggested Fix** | Track A/B: single section-group save when contract allows; until then, confirm fail UX in DevTools. |
| **Current Status** | **Accepted risk for first DevTools gate** — watch during walkthrough. |

---

## Low

### L1 — Photos defer wording differs from Story/Basics

| Field | Content |
|-------|---------|
| **Description** | Story/Basics secondary「稍后再填」; Photos secondary「返回我的资料」. |
| **Impact** | Minor wording inconsistency; hub escape vs postpone may confuse pedantic review only. |
| **Suggested Fix** | Keep unless customers confuse; optional unify later. |
| **Current Status** | **Accepted** for first pilot. |

### L2 — Entry and Task Home share nav title「事故资料」

| Field | Content |
|-------|---------|
| **Description** | Both pages use nav title **事故资料**; card distinguishes hub as **我的事故资料**. |
| **Impact** | Low cognitive cost; optional Entry「正在打开资料」. |
| **Suggested Fix** | Optional polish only after Critical/High clear. |
| **Current Status** | **Accepted**. |

### L3 — Review success toast may be brief before redirect

| Field | Content |
|-------|---------|
| **Description** | 「提交成功」toast (~1.2s) then navigate to Receipt; slow devices may miss toast. |
| **Impact** | Low — Receipt hero still confirms success. |
| **Suggested Fix** | Optional delay; or rely on Receipt. |
| **Current Status** | **Accepted** — verify on target device once. |

---

## Pilot Readiness Score

Scores are for the **2026-07-13 stabilization freeze** (code + automated gates). Manual DevTools walkthrough and Gate 3 remain open. Automated Mini Program tests: **118 PASS**. Component gates: Gate1/Gate2 **PASS**. Python: `test_p19m1_mini_program_logic` **23 PASS**, `test_p20_track_b_backend_foundation` **8 PASS**, `test_h5_claim_intake_form` **20 PASS**, `test_p19h3a_claim_workbench_visibility` **8 PASS**.

| Dimension | Score (0–100) | Deduction explanation |
|-----------|--------------:|------------------------|
| **Architecture** | 90 | Shared `taskPage` + Task UI kit (status/progress/choice/photo) + Workbench vehicle section coherent (−10: prototype AppID/config surface; no production auth). |
| **Customer Journey** | 82 | Unified post-submit「补充或修改资料」+ backend allowlist (−18: no signed manual DevTools walkthrough; device path unproven). |
| **UX** | 84 | Duplicate post-submit CTAs removed (−16: healthy Task Home contact gap; vehicle browser visibility Medium). |
| **Reliability** | 84 | Supplement provenance/timeline + API/PG parity (−16: network/expiry not manually proven; Basics multi-PATCH residual). |
| **Testing** | 90 | 118 miniapp + focused backend/API/workbench tests green; Gate1/2 automated (−10: Gate3 + checklist unchecked). |
| **QA Environment** | 42 | DevTools + localhost path documented (−58: no completed walkthrough; HTTPS/合法域名/真机 LAN path still missing). |
| **Experience Version** | 72 | Freeze commit + Gate1/2 green (−28: Gate3 unsigned; freeze tag / HTTPS / device readiness open). |
| **Chen Kui Pilot** | 58 | Code path ready for next HTTPS QA sprint (−42: C1/C2, H1–H4, Gate3, vehicle browser Medium). |
| **Overall Score** | **77 / 100** | Stabilization freeze improves reviewability; still capped by Gate3 + manual QA + environment blockers. |

### Why not higher

- Manual DevTools checklist is prepared but **zero PASS** (C1).
- Component **Gate 3** not signed for this freeze (H9).
- Real-phone HTTPS/domain still blocking (C2 / H3).
- Broker rehearsal script + config freeze incomplete (H2, H4).
- Healthy hub contact still a High UX gap (H1).
- Vehicle browser visibility remains Medium (M4).

### Why not lower

- Journey architecture and automated regression are solid (**118** MP tests).
- Gate1/2 component automation green; post-submit supplement backend allowlist tested.
- Blockers catalogued — freeze is a reviewable commit, not invented PASS.

### Scoring note

Freeze raises Testing/Architecture slightly vs pre-freeze **76**. After Founder Gate3 + clean walkthrough, expect ~**82**; after HTTPS + device + healthy-hub contact + config freeze, target ≥**90**.

---

## Exit criteria for “Manual QA ready”

| Criterion | Met? |
|-----------|------|
| Walkthrough checklist exists with Entry→Receipt rows | Yes |
| Bug template exists with required columns | Yes |
| Blockers grouped Critical→Low with Description / Impact / Suggested Fix / Status | Yes |
| Readiness table updated with deductions | Yes |
| Automated tests green | Yes (see sprint return) |
| Human marked checklist PASS | **No** — next sprint action |
