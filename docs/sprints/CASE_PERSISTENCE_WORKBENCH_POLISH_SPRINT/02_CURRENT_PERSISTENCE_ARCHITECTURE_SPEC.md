# Current Persistence Architecture Spec

**Status:** As implemented in repo (documented 2026-03-20).  
**Classification:** **Lightweight local persistence** — JSON files + on-disk attachments, not a managed database layer.

## 1. Are cases persisted?

**Yes**, via `save_case()` in `case_store.py`, typically triggered from `POST /api/inbox/triage` when:

- `persist_case` is `true`, and  
- `handoff_ready` is `true` (avoids premature/duplicate cases across turns), **or**
- Talk-to-Agent shortcut path persists when `persist_case` is true.

Cases are **not** persisted for every triage call—only when the API request opts in and the workflow gate passes.

## 2. What exactly is persisted on a case?

### Core identity & timestamps

| Field | Notes |
|--------|--------|
| `case_id` | `case_` + hex |
| `created_at`, `updated_at` | UTC ISO strings |
| `case_status` | `new`, `reviewing`, `waiting_client`, … (validated set) |
| `source_text` | Merged conversation text (`[客户]` / `[系统]` style) |
| `case_messages` | Message-level history (role, text, sequence, ids, timestamps) |

### Triage / workflow (from triage result)

Required triage fields: `issue_category`, `urgency`, `broker_next_step`, `client_prep`, `client_reply_draft`, `manual_followup_needed`.

Optional / extended:

- `conversation_summary`, `secondary_issue_note`
- `collected_fields`, `still_needed_fields`
- `quote_ready_status` — persisted when value is one of `quote_ready` \| `almost_ready` \| `need_more`
- `handoff_ready`, `case_creation_suggested`, `human_confirmation_required`, `human_confirmation_fields`
- `collection_stage`, `follow_up_type`, `next_best_question`
- `lifecycle_status` — stored or derived for legacy rows
- `origin_session_id` — optional link to pre-handoff session

### Client / customer linkage

- `client_id` — optional; set on create or backfilled on append for legacy cases
- `customer_name`, `customer_phone` — from triage extraction on save/append; also updatable via `update_case_customer`
- `customer_email`, `policy_number`, `contact_note` — editable via customer patch API

### Broker operational fields

- `waiting_on`, `next_contact_by` — follow-up target + timing (`update_case_follow_up`)
- `case_notes` — broker notes (`add_case_note`), capped count
- `case_activity` — append-only style activity log (status changes, follow-up updates, notes, attachments), capped count

### Attachments

- `case_attachments` — array of metadata: `attachment_id`, `filename`, inferred `type`, `size_bytes`, `created_at`
- **File bytes** stored separately on disk (see below)

## 3. Where is it stored?

| Asset | Default path | Override env |
|--------|----------------|--------------|
| Case JSON (all cases in one file) | `{REPO_ROOT}/data/unified_intake_cases.json` | `UNIFIED_INTAKE_CASES_PATH` |
| Session JSON | `{REPO_ROOT}/data/unified_intake_sessions.json` | `UNIFIED_INTAKE_SESSIONS_PATH` |
| Attachment files | `{REPO_ROOT}/data/unified_intake_attachments/{case_id}/` | `UNIFIED_INTAKE_ATTACHMENTS_DIR` |

Writes use **atomic replace** (temp file + rename) for the JSON payloads.

### Limits (safety / demo)

- Max stored cases: **200** (new cases evict oldest by sort)
- Max notes / activity entries per case: capped in `_normalize_case`
- Max attachments per case: **10**; max size **10 MB**; allowed extensions: images + pdf

## 4. Append / follow-up persistence

`append_follow_up_message()`:

- Appends customer (and optional system) rows to `case_messages`
- Rebuilds `source_text` from messages
- Overwrites triage-derived fields from the **new** triage result (category, urgency, drafts, collected/still needed, quote_ready_status, workflow flags)
- Sets `lifecycle_status` to `office_followup` for append flow
- Preserves case identity; updates `client_id` if missing and provided
- Appends `case_activity` entry

## 5. In-progress sessions (separate from cases)

`session_store.py` persists **pre-handoff** turns + a **subset** of workflow state for refresh recovery. Cleared when a case is successfully created with the same `session_id`.

**Not** a second case store—ephemeral continuity only.

## 6. Type of persistence

| Aspect | Current |
|--------|---------|
| Durability | Single-server filesystem |
| Concurrency | Last-write-wins on whole JSON file |
| Query | Linear scan in process |
| Backup / HA | Operator responsibility |
| Compliance | No built-in retention, encryption, or PII partitioning |

This is appropriate for **local demo and founder trial**; it is **not** commercial multi-tenant storage.
