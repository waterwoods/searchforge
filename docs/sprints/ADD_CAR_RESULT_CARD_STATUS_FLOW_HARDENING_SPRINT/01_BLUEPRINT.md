# ADD-CAR RESULT CARD + STATUS FLOW HARDENING — Blueprint

## Sprint goal

Harden the Add-Car post-submit (and pre-submit progress) surface so it reads as a **professional case card + status-driven workflow**, not a softened chat outcome.

## Why now

Add-Car is the strongest monetizable flow. Clearer case identity, status, recorded vs missing fields, next steps, office handoff, and same-case vs new-case boundaries reduce pilot risk and make client-pack replication easier.

## Scope

- Add-Car result card hierarchy and visual authority
- Status strip / labels using **existing** `TriageResult` fields (`quote_ready_status`, `lifecycle_status`, `collection_stage`, `handoff_ready`)
- Case reference (`case_id`) when present
- Office-side next step from `broker_next_step` when present
- Stronger boundary framing between same-case append and new issue

## Non-scope

- Backend triage rewrite, API redesign, CRM/platform expansion
- Broad homepage or non–Add-Car redesign

## Current problem (plain language)

The UI already separates “progress” and “handoff closure,” but status is still somewhat **tag-scattered** and the closure block still leans **chat-adjacent** in hierarchy. Brokers need a **single scan line** for state plus an **authoritative** structured block.

## Target outcome

One glance answers: **what case**, **what state**, **what’s recorded**, **what’s missing**, **what customer vs office does next**, and **how to continue vs start fresh**—without new backend semantics.
