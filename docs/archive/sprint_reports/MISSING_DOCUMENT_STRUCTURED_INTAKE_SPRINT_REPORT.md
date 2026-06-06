# Missing Document Structured Intake Sprint Report

## 1. Stages completed

- **Stage 1 — Define selective structured intake:** Completed. Schema defined.
- **Stage 2 — Implement backend structured fields:** Completed. `_missing_document_structured_fields` added.
- **Stage 3 — Expand Broker Workbench UI:** Completed. `MISSING_DOC_FIELD_LABELS` added; existing Collected/Still needed chips render for missing_document.
- **Stage 4 — Customer + Broker simulation:** Completed via existing guardrail (MT9, MT10, LC-D1, LC-D2, document_chase pack).
- **Stage 5 — Identify high-value issues:** Completed. No blocking issues; extraction covers main cases.
- **Stage 6 — Improvement loop 1:** Skipped. First pass sufficient.
- **Stage 7 — Optional improvement loop 2:** Skipped.
- **Stage 8 — Founder demo proof:** Completed. Documented in cheat sheet and walkthroughs.
- **Stage 9 — Regression + safety:** Completed. API test assertions added; guardrail passes.
- **Stage 10 — Audit:** Completed. Accept verdict.

## 2. Structured-intake targets

**What was structured:**

| Field type | Purpose |
|------------|---------|
| `requested_<item>` | What documents are being requested (declaration_page, garaging_proof, driver_license, questionnaire) |
| `customer_says_sent_<item>` | What the customer claims they already sent |
| `already_sent_claimed` | Boolean flag when customer says they sent something |
| `underwriting_followup` | Context when UW/escrow/follow-up context present |
| Still needed: `<item>` | Items requested but not yet sent |
| Still needed: `verify_carrier_received` | When customer claims sent but office must verify with carrier |

**Why these fields matter:** Broker can quickly see: (1) what docs are in play, (2) what customer claims to have sent, (3) what still needs verification or resend.

**What was intentionally left unstructured:** Emotional filler, apology text, irrelevant background chatter. No OCR, no file upload parsing.

## 3. UI / backend / product changes made

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | `_extract_missing_doc_status`: normalized keys (declaration_page, garaging_proof, driver_license, questionnaire), added questionnaire. `_missing_document_structured_fields`: new function. `_build_conversation_summary`: humanize for missing_doc. `triage_conversation`: add missing_document branch for collected/still_needed. |
| `services/fiqa_api/routes/inbox_triage.py` | Import `_missing_document_structured_fields`. Add `elif result.get("issue_category") == "missing_document"` branch for single-message triage. |
| `ui/src/pages/UnifiedIntakePage.tsx` | `MISSING_DOC_FIELD_LABELS`: human-readable labels for requested_*, customer_says_sent_*, underwriting_followup, verify_carrier_received. `humanizeStructuredField`: include MISSING_DOC_FIELD_LABELS. |
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | Document missing_document structured fields. |
| `scripts/test_inbox_triage_api.py` | Assert collected_fields and still_needed_fields for missing_document persisted case. |

## 4. Validation and improvement loops

**What was tested:**
- Scenario pack: 49/49 passed
- Multi-turn: MT9, MT10, LC-D1, LC-D2, document_chase pack
- Guardrail: PASS
- UI build: success

**Issues found:** None blocking. Document-confusion cases (e.g. "这两个到底是什么？") route to customer_question, not missing_document; no structured fields for those. Intentional—we structure only missing_document.

**Fixes made:** None required after first pass.

## 5. Product proof strength

- **Structured broker usability:** Improved. Broker sees Collected/Still needed chips for missing_document cases.
- **Missing-document usefulness:** More useful. Broker can scan requested items, customer-says-sent, and verify step at a glance.
- **Sellability:** Stronger. Document chase is a repetitive office task; structured intake reduces mental load.

## 6. Validation summary

| Check | Result |
|-------|--------|
| `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | 49/49 passed |
| `bash scripts/guardrail_inbox_triage.sh` | PASS |
| `npm run build` | Success |
| `scripts/test_inbox_triage_api.py` | Pass (restart server to pick up new route) |

**Note:** Restart backend (`bash scripts/run_demo_local.sh` or equivalent) to pick up missing_document structured fields in the API.

## 7. Business / platform value

- **Broker mental load:** Reduced. One scan shows: requested docs, customer-says-sent, still needed, verify step.
- **Document-chase work:** Less repetitive. Fewer "what did they say they sent?" re-reads.
- **Platform story:** Clearer. Four flows now structured: add-car, renewal, claim, missing-document.

## 8. Remaining blocker(s)

1. None. Restart server to verify API returns structured fields.

## 9. Recommended next step

Restart backend to pick up changes, then run `PYTHONPATH=. python3 scripts/test_inbox_triage_api.py` to confirm persisted-case flow includes missing_document structured fields.

---

## 10. 中文或中英混合宏观总结

- **本次扩展：** Structured workbench 扩到了 missing_document / 缺材料 / UW follow-up。经纪人现在可以一眼看到：**请求了什么材料**、**客户说哪些已经发了**、**还缺哪些**、**是否需要跟 carrier 核对**。
- **经纪人一眼能多看到：** Collected 芯片（Requested: Declaration page, Customer says sent: Declaration page, Customer claims already sent, UW follow-up）和 Still needed 芯片（Garaging proof 或 Verify carrier received）。
- **更像真实业务：** UW follow up、客户说上周发过了、dec page + garaging proof 这类 case 现在有结构化展示，比之前只有 free-text summary 更清晰。
- **还缺：** OCR、文件上传、inbox sync 仍不在 scope；document confusion（问「这是什么意思」）的 case 仍是 customer_question，没有 structured fields。
- **对陈奎和以后客户：** 减少重复追材料时的 mental load，让缺材料追件变成更可操作的业务处理，而不是纯文本堆砌。

---

## 11. Practical missing-document cheat sheet

| What gets structured | Broker sees first | Still remains manual | Retrieval may help |
|---------------------|-------------------|----------------------|--------------------|
| Requested items (dec page, garaging proof, DL, questionnaire) | Collected chips | Verify with carrier | Document explanation (declaration page, garaging proof 是什么) |
| Customer says sent | Customer says sent: X | Resend if needed | — |
| Still needed | Still needed chips | Chase client or carrier | — |
| Verify carrier received | When customer claims sent | Call/check carrier portal | — |

---

## 12. Broker-value summary

| Strength | Cases |
|----------|-------|
| **Strongest** | UW follow up - need dec page + garaging proof. 客户说上周发过了；Underwriting requested DL. Client says already sent |
| **Acceptable** | 需要驾照 copy 客户说上周寄了；declaration page 我上周就发了，怎么还在追？ |
| **Weak** | Document confusion (garaging proof 是什么) — category 是 customer_question，无 structured fields |

---

## 13. Live proof walkthroughs

### 1. Clean missing-document case

**Customer message:** `UW follow up - need dec page + garaging proof. 客户说上周发过了`

**Broker sees now:**
- Collected: Requested: Declaration page, Requested: Garaging proof, Customer says sent: Declaration page, Customer says sent: Garaging proof, Customer claims already sent, UW follow-up
- Still needed: Verify carrier received

**What changed:** Before: only conversation_summary. Now: structured chips.

**Demo-strong:** Yes.

---

### 2. Declaration page "already sent" case

**Customer message:** `Underwriting requested driver's license copy. Client says "I already sent it last week."`

**Broker sees now:**
- Collected: Requested: Driver license, Customer says sent: Driver license, Customer claims already sent, UW follow-up
- Still needed: Verify carrier received

**What changed:** Before: free-text. Now: structured chips.

**Demo-strong:** Yes.

---

### 3. Garaging proof confusion case

**Customer message:** `他们又要我补 declaration page 和 garaging proof，这两个到底是什么？`

**Broker sees now:** Category: customer_question. No structured fields (document confusion, not missing_document).

**What changed:** Retrieval can still explain document meaning; structured intake not applied here.

**Demo-strong:** For retrieval explanation, not for structured missing-doc.

---

### 4. Mixed-language missing-document case

**Customer message:** `需要驾照 copy 客户说上周寄了`

**Broker sees now:**
- Collected: Requested: Driver license, Customer says sent: Driver license, Customer claims already sent
- Still needed: Verify carrier received

**What changed:** Before: free-text. Now: structured chips.

**Demo-strong:** Yes.

---

### 5. Control non-structured case

**Customer message:** `客户问：这个英文 notice 说 payment failed，我现在怎么办？`

**Broker sees now:** Category: payment_lapse_expiration. No collected_fields / still_needed_fields (not missing_document).

**What changed:** No change. Fallback to conversation_summary.

**Demo-strong:** N/A for missing-doc.

---

*End of report*
