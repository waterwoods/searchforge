# Founder Demo / Inspection Notes

**Sprint:** In-Progress Conversation Persistence + Single Source of Truth

---

## 1. What Founder Should Inspect After This Sprint

1. **Refresh no longer loses everything**
   - Start a conversation in Customer Entry
   - Send 1–2 messages (e.g. add-car: "我想加新车报价" → "2025 Tesla Model Y")
   - Refresh the page (F5 or Cmd+R)
   - **Expected:** Conversation restores; turns visible; can continue

2. **workflow_state remains coherent**
   - After restore, check "下一步建议" / next_best_question
   - Check lifecycle_status tag (Collecting / Ready to save)
   - **Expected:** Matches last triage result

3. **Case creation still works cleanly**
   - Complete add-car flow to handoff
   - Click save / persist
   - **Expected:** Case appears in Broker Workbench; session cleared for next conversation

---

## 2. How to Verify Refresh No Longer Loses Everything

1. Open http://localhost:5173/demo (or deployed URL)
2. Customer Entry tab
3. Click "报价" or type "我想加新车报价"
4. Send; wait for reply
5. Type "2025 Tesla Model Y" (or similar)
6. Send; wait for reply
7. **Refresh page (F5)**
8. **Pass:** Conversation with both turns visible; can type and send another message
9. **Fail:** Empty conversation; turns lost

---

## 3. How to See Message + State + Case Coherence

- **Before handoff:** In-progress session has turns + workflow_state
- **After handoff:** Case has case_messages + workflow_state
- **Workbench:** Case card shows lifecycle_status, collection_stage from case record

---

*See: 01_SPRINT_BLUEPRINT.md*
