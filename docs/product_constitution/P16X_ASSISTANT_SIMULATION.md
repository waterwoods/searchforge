# P16-X Phase 3 — Office Assistant Simulation

**Date:** 2026-06-01  
**Persona:** Office assistant — 50+ WeChat threads/day; executes broker instructions; no engineering context  
**Method:** Deployed Preview queue + reopen + append path audit  
**URL:** https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake

---

## Question 1 — Can the assistant use this for an active case?

**Conditionally yes — only if the broker opens the case from the queue first.**

| Workflow step | Works? | Notes |
|---------------|--------|-------|
| See today's queue | ⚠️ Partial |「待处理」list loads; English preview text on demo rows |
| Open existing case | ✅ | Click queue row → detail scrolls into view |
| Read 下一步 + draft | ✅ | Three-step glance readable when expanded |
| Copy draft to WeChat | ✅ | 复制客户草稿 |
| Append client reply | ✅ **only after reopen** |「追加客户补充」card appears when `caseView === reopened` |
| Change status (new → waiting → done) | ⚠️ Hidden |「状态」in kebab menu — easy to miss |
| Start fresh case while one open | ⚠️ Confusing | Must「清空」first; conflicting hints |

**Active case usability:** **58 / 100** — engine supports it; UI trains against it.

---

## Question 2 — What information is still missing?

### For the assistant to work a case end-to-end

| Missing | Impact |
|---------|--------|
| **Customer name / phone on glance** | Must read full thread or guess |
| **Which WeChat thread** this case maps to | No CRM link (by design) — but no「备注：张先生」field prominent |
| **Sent / not sent** flag | Assistant cannot mark「已发草稿给客户」 |
| **Waiting on whom** | `waiting_on` exists in data; not prominent in product_only glance |
| **Chinese broker_next_step** | English action line on live demo cases |
| **Follow-up entry on first persist** | Append block absent until queue reopen — biggest operational gap |
| **Mobile layout proof** | Assistant often on phone next to WeChat |
| **15-min training script** | Not in product; not in trial pack UI |
| **Morning ritual cue** | No「X 件需今天处理」sticky summary in product_only |

### For the broker to delegate

| Missing | Impact |
|---------|--------|
| Assignment / ownership | Not built (OK for v1) |
|「处理这条」checklist | Only free-text draft |
| Audit trail visible to assistant | Activity collapsed under tags |

---

## Day-in-the-life simulation

**8:30 AM — broker asks assistant to chase missing SR-22 doc**

1. Assistant opens Preview URL ✅  
2. Scrolls to queue — sees 12+ rows, many similar English lines ⚠️  
3. Clicks correct case — detail opens ✅  
4. Copies draft, sends in WeChat ✅  
5. Client replies with photo description — assistant returns to browser ❌  
6. Does **not** see「追加客户补充」because she never left the detail view from step 3… **Actually:** if she stayed on reopened case, append **is** visible. If she pasted a **new** message in top box instead, system may create duplicate case ❌  
7. Broker angry — assistant reverts to WeChat-only by Day 3 ❌  

**Adoption without mandate:** **Low**  
**Adoption with broker mandate + 15-min training:** **Medium**

---

## Assistant composite

| Dimension | Score |
|-----------|-------|
| Queue scan | 55 |
| Active case handoff | 58 |
| Follow-up continuity | 42 |
| Status / close hygiene | 35 |
| Self-serve onboarding | 30 |
| **Overall assistant (deployed)** | **44 / 100** |

**$99 tier evidence:** Not ready. Assistant ROI depends on follow-up loop — currently broken for untrained users.

---

*End of P16-X Phase 3 — Office Assistant Simulation*
