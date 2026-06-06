# In-Progress Persistence Design Spec

**Purpose:** Define what gets stored before handoff, when, and how recovery works.

---

## 1. What Gets Stored Before Handoff

| Field | Description |
|-------|-------------|
| session_id | Client-generated UUID; key for lookup |
| turns | Array of { role, text } (customer/system); system turns include triageResult snapshot |
| workflow_state | Subset of triage result: handoff_ready, lifecycle_status, collection_stage, collected_fields, still_needed_fields, next_best_question, etc. |
| updated_at | ISO timestamp of last update |

---

## 2. When It Gets Stored

| Event | Action |
|-------|--------|
| Triage returns, session_id provided, no case_id in response | Save/update in-progress session with (turns + new customer + new system, workflow_state) |
| Triage returns, case persisted (case_id in response) | Do NOT save to in-progress store; case is canonical |
| User clicks "New" or case persisted | Frontend clears session_id; backend may optionally delete session (deferred) |

**Rule:** Persist on every triage response when session_id is provided and result does NOT include case_id.

---

## 3. Session / Conversation / Case Relationship

| Identity | When | Storage |
|----------|------|---------|
| session_id | Before handoff | In-progress session store |
| conversation_id | Echo of session_id when no case | Response only; not stored |
| case_id | After handoff when persist_case + handoff_ready | Case store |

**Rule:** In-progress session and case are mutually exclusive for a given thread. Once case is created, session is obsolete (frontend clears session_id).

---

## 4. In-Progress Conversation Recovery

1. **Frontend on mount:** If session_id exists in localStorage, call GET /api/inbox/session/{session_id}.
2. **Backend:** Return { turns, workflow_state } or 404.
3. **Frontend:** If 200, restore turns and latest workflow_state into React state; show conversation.
4. **If 404:** Treat as new session; clear localStorage session_id (optional).

---

## 5. What Remains Lightweight

- JSON file store (data/unified_intake_sessions.json)
- Max ~50 in-progress sessions; evict oldest by updated_at
- No TTL; no replication; no auth
- Session cleanup on case creation: optional (orphaned sessions are harmless)

---

## 6. Storage Schema

```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "turns": [
        { "role": "customer", "text": "..." },
        { "role": "system", "text": "...", "triageResult": { "handoff_ready": false, ... } }
      ],
      "workflow_state": {
        "handoff_ready": false,
        "lifecycle_status": "collecting",
        "collection_stage": "collecting",
        "collected_fields": [],
        "still_needed_fields": ["year", "model"],
        "next_best_question": "..."
      },
      "updated_at": "2026-03-16T12:00:00Z"
    }
  ]
}
```

---

*See: 03_SINGLE_SOURCE_OF_TRUTH_CONTRACT_SPEC.md*
