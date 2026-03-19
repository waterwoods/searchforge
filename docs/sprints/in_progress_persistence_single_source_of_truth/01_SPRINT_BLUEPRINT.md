# In-Progress Conversation Persistence + Single Source of Truth — Sprint Blueprint

**Sprint name:** In-Progress Conversation Persistence + Single Source of Truth Sprint  
**Created:** 2026-03-16  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why In-Progress Persistence Matters Now

The product has:
- Stronger session continuity (session_id in localStorage)
- Stronger workflow_state (lifecycle_status, collection_stage, etc.)
- Clearer lifecycle_status
- Better UI visibility

**The biggest remaining weakness:** In-progress conversation turns are lost on refresh.  
Turns live only in React state. session_id survives in localStorage, but there is no way to restore turns. Backend does not store pre-handoff turns.

The founder and reviewer agree: **this is the single most important remaining backbone gap.**

---

## 2. Current Persistence Gap

| Data | Ephemeral | Durable |
|------|-----------|---------|
| session_id | localStorage (survives refresh) | — |
| conversation_turns | React state only | — |
| turns (Customer Entry) | React state | — |
| case_id, case_messages, workflow_state | — | JSON case store |

**Impact:** Multi-turn flows (e.g. add-car) lose all context on refresh before handoff.

---

## 3. Why This Is the Highest-Value Next Step

1. **Refresh resilience:** Users can refresh mid-conversation without losing work.
2. **Single source of truth:** workflow_state stored alongside turns; frontend/backend/workbench rely on same state.
3. **Case creation remains downstream:** Handoff is not the only persistence moment.
4. **Lightweight:** No full database migration; JSON file store like case_store.

---

## 4. What This Sprint Will Do

1. **Persist in-progress conversation turns before handoff**
2. **Persist workflow_state alongside in-progress turns**
3. **Make session/case/message relationship clearer and more durable**
4. **Strengthen single source of truth** so frontend, backend, and workbench rely on the same state object

---

## 5. What This Sprint Will NOT Do

- No unrelated features
- No giant infrastructure or auth work
- No full database migration
- No enterprise-grade perfection (TTL, replication, etc.)

---

## 6. Target System Outcome

When user sends a message:
1. Message is stored
2. Current workflow_state is stored
3. Session/conversation identity remains stable
4. Refresh can recover conversation state more reliably
5. Case creation/handoff remains downstream of this, not the only persistence moment

---

*See: 02_IN_PROGRESS_PERSISTENCE_DESIGN_SPEC.md, 03_SINGLE_SOURCE_OF_TRUTH_CONTRACT_SPEC.md*
