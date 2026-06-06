# Stage 1 Service Record Database Blueprint

## 1. Document purpose

This document defines the Stage 1 database blueprint. The goal is not to build a full CRM, and not to build the full data backbone for a fully automated insurance platform. The goal is:

**to create a stable, clear, extensible Service Record data system for Stage 1 of Unified Intake.**

This system must support:

- receiving customer input
- turning input into formal service records
- storing structured extraction results
- storing current state and state history
- supporting office handoff
- preparing the foundation for Stage 2 and Stage 3

---

## 2. Stage 1 database goal

Stage 1 database design serves one core purpose:

**turn messy, fragmented, conversational customer input into an operable, trackable, handoff-friendly service record asset.**

The database focus is **not**:

- pricing engine execution
- underwriting execution
- billing
- full CRM customer profiling
- complete office operating system scope

The database focus **is**:

- who sent this
- what they sent
- what it became after structuring
- what the current state is
- what is still missing
- what the office should do next
- how the record evolves over time

---

## 3. Core database design principles

### Principle 1: Record-first

The main object is not the message and not the chat thread. The main object is:

**service_record / case**

Every Add-Car request, billing question, material submission, or policy-change request is fundamentally a service record.

### Principle 2: State-first

The business process should not be driven only by chat text. The process backbone must be:

- current state
- next-action ownership
- state-transition history

The database must clearly store:

- current state
- state history
- who is currently responsible
- what the current next action is

### Principle 3: Message-retained

Raw messages must not be discarded. They are:

- evidence
- audit trail
- correction context
- future training / optimization material

So raw messages must be preserved, but they are not the main object. They are supporting evidence attached to the service record.

### Principle 4: Structured data is a core asset

Structured extraction output is one of the most valuable assets in this product. The database must persist this structured result, not leave it only in memory or transient UI state.

### Principle 5: Simple first, extensible later

Stage 1 should not begin as a full insurance CRM. It should begin as the minimum viable record system, while still leaving a clean path to Stage 2 and Stage 3.

---

## 4. Recommended database direction

### 4.1 Current recommended primary database: Postgres

The best primary database for Stage 1 is:

**Postgres**

Why:

- mainstream
- stable
- transactional
- well suited for service records, state, history, and office actions
- supports JSONB for evolving structured payloads
- can continue to scale with the system without forcing an early rewrite

### 4.2 Role of other database types

**Vector database**

In the future, vector databases may be useful for:

- similar case retrieval
- knowledge retrieval
- semantic search

But a vector database is **not** the main Stage 1 record system.

**Graph database**

Graph databases may be relevant only if the product later develops truly complex entity-relationship modeling needs. Stage 1 does not need graph DB as the primary backbone.

### 4.3 Summary

**For Stage 1, make Postgres strong first. Do not make the database layer prematurely complicated.**

---

## 5. Core data objects for Stage 1

### 5.1 Customers

Represents the customer identity layer.

Minimum purpose:

- know who this customer is
- link one customer to multiple service records
- retain minimal contact identity

Suggested core fields:

- customer_id
- display_name
- phone
- email (optional)
- wechat_id (optional)
- preferred_language (optional)
- created_at
- updated_at

### 5.2 Service records

This is the most important table or object.

Each business request should be represented as a service record.

Suggested core fields:

- record_id / case_id
- customer_id
- issue_type
- title / short_summary
- current_status
- current_owner
- current_next_action
- current_waiting_on
- intake_channel
- client_id
- created_at
- updated_at
- closed_at (optional)

This object answers:

- what is this case
- what stage is it in
- who owns it now
- what happens next

### 5.3 Record messages

Stores the raw messages associated with a record.

Suggested core fields:

- message_id
- record_id
- sender_type (customer / system / office)
- message_text
- source_channel (portal / wechat / manual / imported)
- raw_payload (optional)
- created_at

This object answers:

- what was actually said
- what did the system or office reply
- what is the raw trace behind the structured record

### 5.4 Structured record data

Stores the structured extraction output.

Recommendation: use **JSONB first** rather than over-normalizing too early.

Suggested core fields:

- record_id
- structured_payload (JSONB)
- completeness_level
- quote_readiness
- missing_fields_summary
- extracted_at
- updated_at

This object answers:

- what has already been collected
- what is still missing
- whether this record is ready to continue / ready to quote

### 5.5 State history

Stores the state-transition history.

This is extremely important because the product is moving toward state-driven flow.

Suggested core fields:

- state_event_id
- record_id
- from_status
- to_status
- triggered_by
- reason
- snapshot_note (optional)
- created_at

This object answers:

- how the record got to its current state
- what triggered the transition
- why the case is where it is now

### 5.6 Office actions / handoff notes

Stores office actions, handoff notes, and internal follow-up information.

Suggested core fields:

- action_id
- record_id
- action_type
- note_text
- next_step_note
- actor
- created_at

This object answers:

- what the office has done
- what the office plans to do next
- who received the handoff
- how the case is being followed internally

---

## 6. Recommended modeling strategy

### Relational tables + JSONB hybrid model

Stage 1 should not be fully relationalized, and should not be fully JSON-only either.

The recommended strategy is:

**Use relational structure for:**

- customers
- service_records
- record_messages
- state_history
- office_actions

**Use JSONB for:**

- evolving structured extraction payloads
- fields that are still changing quickly

Benefits:

- core relationships stay stable
- structured data stays flexible
- schema does not thrash while the product evolves
- stable fields can later be extracted from JSONB into dedicated columns if needed

---

## 7. Stage 1 state model requirements

Even though Stage 1 is not yet a complete workflow engine, the database must treat state as a first-class concept.

At minimum:

### Current state must be queryable directly

It must not live only inside a generic JSON payload.

### State history must be traceable

There must be more than just a current status field.

### State must connect to responsibility and next action

At minimum, the system should be able to represent ideas such as:

- waiting on customer
- waiting for more information
- ready to quote
- handed to office
- office processing
- follow-up needed

---

## 8. Relationship to Stage 2 and Stage 3

This database is not a throwaway artifact. It must support later product stages.

### Support for Stage 2

Stage 2 quote-preparation automation depends on:

- structured data
- completeness
- missing fields
- state history
- office next steps

### Support for Stage 3

Stage 3 internal-system / quote-API connection depends on:

- stable record_id
- reliable service record model
- current status
- quote-ready structured data
- office action trace

So Stage 1 DB design is not a temporary table set. It is the foundation of the future process backbone.

---

## 9. Migration strategy

### Do not replace everything at once

The current JSON-based persistence or interim persistence should not be ripped out immediately.

Recommended migration steps:

**Step 1: Define schema**

Define the minimum viable service-record schema first.

**Step 2: Dual-write**

New records continue to use the current logic, while also being written into Postgres.

**Step 3: Gradually switch reads**

After enough confidence and validation, gradually move read paths and workbench views onto Postgres-backed records.

### Migration principle

**Gentle migration beats big-bang replacement.**

---

## 10. What Stage 1 should not do

Stage 1 should **not**:

- design a full CRM
- create dozens of highly normalized business tables
- over-split fields too early
- prematurely optimize for full multi-tenant platform complexity
- use graph DB as the main system
- use vector DB as the record backbone
- try to solve all future data problems immediately

---

## 11. Success criteria

This DB blueprint is correct if it enables the product to do the following:

1. Every Add-Car request can become a formal service record
2. Raw input, structured output, state, and office actions can all be traced
3. Customer side, result card, and workbench can increasingly operate around the same record
4. Stage 2 quote-prep logic can build on this model
5. The second and third client do not require reinventing the data backbone

---

## 12. Current overall judgment

### One-line judgment

**Stage 1 should build a Postgres-centered Service Record System—not a full insurance CRM—so that record, state, message, structured data, and office action become true operational assets that can later support automation and scale.**
