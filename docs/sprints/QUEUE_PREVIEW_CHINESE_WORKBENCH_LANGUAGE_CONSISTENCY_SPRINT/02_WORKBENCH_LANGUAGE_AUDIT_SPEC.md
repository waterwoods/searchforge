# Workbench Language Audit Spec

**Sprint:** Queue Preview Chinese + Workbench Language Consistency Sprint  
**Created:** 2026-03-20

---

## Audit scope

| Area | Location | Status |
|------|----------|--------|
| Queue readiness label | `getQueueReadinessLabel()` | English: Ready to act, Needs more info, Quote-ready, etc. |
| Compact queue preview | `getCompactQueuePreview()` | English: Collected:, Missing:, Premium concern, etc. |
| Case focus (inferCaseFocusFromText) | Tag on cards | Mix: 联系人工 (OK), Add car quote, Claim intake (English) |
| Structured field labels | `humanizeStructuredField()` → ADD_CAR, RENEWAL, CLAIM, MISSING_DOC | All English |
| Case report one-liner | `getCaseReportOneLiner()` | English: Ready for handoff, Collecting |
| Draft readiness | `getDraftReadinessLabel()` | English: Edit before sending, Ready for quick broker review |
| Copy case snapshot | `handleCopyCaseSnapshot()` | English: Case:, Next move:, Collected:, Still needed:, Draft: |
| Category display | `CATEGORY_DISPLAY_LABELS` | Mix: 联系人工 (OK), Cancellation risk, Missing document (English) |
| Section headers | Case detail | 已收集, 还缺, 您的下一步, 跟进 — already Chinese |
| Due tags | `getFollowUpDueTag()` | 已逾期, 今日到期, 明日到期 — already Chinese |
| Attention state labels | `getCaseAttentionState()` | 已结案, 立即处理, 待您处理, 尽快跟进 — already Chinese |
| Status legend | Queue card area | 可行动, 需更多信息 — Chinese; getQueueReadinessLabel returns English (inconsistent) |
| Message strings | message.success/error | Mix: some English (Case saved, Follow-up plan saved) |
| Example labels | CUSTOMER_ENTRY_EXAMPLES, QUICK_FILL_EXAMPLES | English (internal/demo use — lower priority) |

## Biggest inconsistency

Queue preview and readiness labels: status legend uses Chinese (可行动, 需更多信息) but `getQueueReadinessLabel` returns English (Ready to act, Needs more info). Cards show both; mixed vocab feels unfinished.

## Biggest broker-facing weakness

Compact queue preview on each card: "Collected: Year, Make/Model · Missing: VIN" — all English. Broker sees this first when scanning the queue.

## Biggest internal/demo wording trace

- "Case saved to recent cases", "Case marked ...", "Follow-up plan saved" — English success messages
- Copy-case-snapshot output: Case:, Next move:, Collected:, Still needed:, Draft: — English when pasted into notes/email

---

*Part of Queue Preview Chinese + Workbench Language Consistency Sprint*
