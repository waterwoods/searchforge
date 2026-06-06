# Future Commercial Storage Recommendation Spec

**Intent:** Describe a **pilot-ready** target that a broker office can trust more than a single JSON file, without over-building into full CRM.

## Recommended primary database

**PostgreSQL** (managed: RDS, Cloud SQL, AlloyDB, etc.)

**Why**

- Relational model fits **cases**, **messages**, **notes**, **activity**, **follow-up state**, and **tenant/client** metadata.
- ACID transactions and row-level locking replace “rewrite entire JSON file.”
- Standard tooling for backups, point-in-time recovery, and read replicas.

### Suggested core tables (logical)

- `organizations` / `clients` — Chen Kui as row one; future multi-broker as expansion
- `cases` — stable `case_id`, status, lifecycle, quote_ready_status, urgency, linkage fields, timestamps
- `case_messages` — FK to case, sequence, role, text, created_at
- `case_notes` — FK to case, body, author (nullable until auth), created_at
- `case_activity` — append-only audit-style events
- `case_follow_up` — `waiting_on`, `next_contact_by`, updated_at (or columns on `cases` if kept simple)

## Recommended object / file storage

**S3-compatible object storage** (GCS, S3, Azure Blob) for **attachment bytes**.

**Why**

- Binary payloads do not belong in hot DB rows at scale.
- Virus scan, lifecycle policies, and presigned URLs are easier.
- Keeps DB backups smaller and faster.

### Metadata stays in DB

Store `attachment_id`, `storage_key`, `filename`, `content_type`, `size_bytes`, `created_at`, `case_id`, optional `sha256`.

## What goes where

| Data | DB | Object store |
|------|----|----------------|
| Case header + workflow fields | Yes | No |
| Message text | Yes | No |
| Broker notes & activity | Yes | No |
| Follow-up fields | Yes | No |
| Attachment metadata | Yes | Pointer only |
| Attachment file bytes | No | Yes |
| Large pasted blobs (future) | Optional external | Prefer object store if large |

## Migration path from current JSON

1. **Dual-write**: new cases to Postgres + legacy JSON (or one-time import job).
2. **Import script**: read `unified_intake_cases.json`, insert cases/messages/notes/activity; copy files from `unified_intake_attachments/` to bucket.
3. **Cut reads** to Postgres; retire JSON after validation window.
4. **Sessions**: move to Redis or short-TTL Postgres rows if refresh recovery must survive horizontal scale.

## Non-goals for first commercial increment

- Full CRM, policy admin, commissions
- Customer-facing auth (unless pilot explicitly requires)
- Real-time sync to WeChat/email (integrate later)

## Security baseline (pilot)

- Encrypt bucket at rest; TLS in transit
- Per-tenant row policy (even if single tenant today)
- Audit log for case open/export (lightweight)
- Retention policy aligned with broker’s PII policy
