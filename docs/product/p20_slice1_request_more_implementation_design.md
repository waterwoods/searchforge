# P20 Slice 1 — Broker Request More → Customer Continue

**Status:** implementation design only  
**Date:** 2026-07-15  
**Scope:** one broker-owned, ordered request group on an existing Claim case, customer completion of its items, and return to broker review.  
**Decision:** use a narrow Slice 1 command service and durable companion tables. Do not convert the existing Claim flow to general event sourcing in this slice.

## 1. Current implementation trace

### A. Broker Request More

There is no current structured Broker Request More path. This is confirmed by the absence of a Request More route or Workbench action and by the current phase/evidence code:

| File | Symbol / current responsibility | Limitation | Slice 1 disposition |
|---|---|---|---|
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | `BrokerWorkbenchTab`, `handleStatusChange`, `handleBrokerConfirm` | Can change mutable workbench status, confirm, upload, append notes, and render Claim brief/timeline; it has no structured request editor or stale-version mutation. | Change |
| `ui/src/api/inboxTriage.ts` | `getSavedCase`, `updateSavedCaseStatus`, `markClaimBrokerDone` | Workbench API client has no request-more command or version contract. | Change |
| `services/fiqa_api/routes/inbox_triage.py` | `GET /cases/{case_id}`, `POST /cases/{case_id}/broker-done` | Office access is enforced for existing case commands, but no Request More endpoint exists. | Change |
| `services/fiqa_api/inbox_triage/case_store.py` | `update_claim_workflow_state` | Directly writes mutable `claim_phase` / guided state after a load; no expected-version check or transition validator. | Wrap; do not use for Slice 1 mutations |
| `services/fiqa_api/inbox_triage/case_store.py` | `build_claim_timeline_event`, `append_claim_timeline_event` | Adds a JSON event then separately persists a case; deduplication is only message, photo, basics, start, and broker-done specific, and the list is capped at 50. | Reuse only for legacy display adapter; do not use as Slice 1 canonical write |
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | `enrich_claim_for_workbench`, `build_claim_case_brief` | Builds useful brief, evidence checklist, and timestamp-sorted timeline from mutable case data. It does not project an open request group or broker action. | Change |
| `services/fiqa_api/inbox_triage/workbench_enrichment.py` | `enrich_cases_for_workbench` | Applies Claim display enrichment before Workbench responses. | Change |

Current broker completion (`mark_claim_broker_done`) is intentionally not reused: it can finish a Claim and sends an End Card, while Slice 1 must return an active case to broker review.

### B. Customer Continue

The Mini Program consumes the H5 Claim task contract, not a broker-request contract:

| File | Symbol / current responsibility | Limitation | Slice 1 disposition |
|---|---|---|---|
| `services/fiqa_api/routes/h5_task_intake.py` | `GET /api/h5/tasks/{token}/intake`, fields PATCH, submit POST | Token authorization and basic field/submit routes exist, but no case version, active request item, or request-aware submission endpoint. | Change |
| `services/fiqa_api/inbox_triage/h5_task_intake.py` | `build_customer_task_contract`, `intake_info_for_token` | Produces contract version `0` from legacy intake state. `next_action` is still derived from `_current_step`, submit readiness, and mutable state. | Change via additive v1 projection |
| `services/fiqa_api/inbox_triage/h5_task_intake.py` | `patch_intake_fields`, `submit_intake_form` | Performs several separate writes (facts, collected fields, timeline, H5 state / phase); field dedup is a bounded value hash and submit dedup is a bounded intent list. | Keep for legacy intake; route Slice 1 requests to command service |
| `services/fiqa_api/routes/h5_task_upload.py` | `POST /api/h5/tasks/{token}/upload` | Validates task token and forwards stable upload intent, but upload first writes storage then performs multiple mutable case writes. | Reuse storage validation/upload adapter; wrap final request-item binding in command service |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | `ingest_h5_slot_upload` | Finds a prior attachment by `h5_upload_id`; this is useful narrow retry protection but not case command replay, request-item validation, or content/binding deduplication. | Change |
| `miniapp/services/taskApi.ts` | `getTask`, `saveFields`, `uploadPhoto`, `submitTask` | Has stable upload and submit intents, but no command ID, expected version, active request-item submission, or replay/conflict result handling. | Change |
| `miniapp/behaviors/taskPage.ts` | `loadTask`, `retryLoadTask`, `saveAndReturn` | Has request sequence stale-response protection and bounded retry, but no page-alive guard and no task-load single-flight across all pages. | Change |
| `miniapp/pages/task-home/task-home.ts` | `onShow`, `onPrimaryAction` | Renders the task projection but unconditionally reloads on every show and routes from legacy section assumptions. | Change |
| `miniapp/pages/photos/photos.ts` | `startPhotoPageRefresh`, upload/reconciliation state | Strongest existing lifecycle implementation: single-flight load, generation guard, page-destroy guard, pending upload reconciliation, and per-item feedback. | Reuse patterns |
| `miniapp/utils/resolveTaskViewModel.ts` / `miniapp/utils/taskMapping.ts` | `resolveTaskViewModel`, `resolveNextAction` | Uses server contract when present but retains client inference and post-submit supplement route selection as authority/fallback. | Change; server v1 action wins for Slice 1 |

Current customer evidence is broker-visible after persistence: Claim Workbench enrichment returns the brief, evidence summary, attachment list, and current JSON timeline. It is not synchronized by an aggregate version.

### C. Resume and retry

The current Mini Program preserves launch token and submit intent in storage, reloads server data on task page `onShow`, and the Photos page guards old responses and destroyed pages. It does not persist a server command outcome, identify a request item, or protect every generic task page from late `setData`. Upload retry is keyed by `h5_upload_id`; submit retry by `submit_intent_id`; neither protects the new broker/customer transition as one atomic business operation.

## 2. Slice 1 domain contract

### Aggregate and identities

`case_id` remains the aggregate identity. Add these Slice-1-only objects:

| Object | Required fields |
|---|---|
| `RequestMoreCommand` | `command_id`, `correlation_id`, `idempotency_key`, `case_id`, authenticated `broker_id`, `requested_items`, `reason`, `expected_state_version`, `submitted_at` |
| `RequestItem` | `request_item_id`, `request_id`, `item_type`, `label`, `instructions`, `required`, `position`, `status`, `created_at`, `satisfied_at`, `satisfied_by_event_id` |
| `CustomerSubmissionCommand` | `command_id`, `correlation_id`, `idempotency_key`, `case_id`, `active_request_item_id`, `expected_state_version`, `client_draft_id`, `submitted_at`, and exactly one typed fact payload or evidence reference |
| `Slice1CommandResult` | `outcome` (`accepted`, `replayed`, `conflict`, `rejected`), original event IDs when replayed, `aggregate_version`, customer and broker projections, customer-safe error code |
| `Slice1CaseProjection` | canonical Slice 1 state, `aggregate_version`, one `customer_next_action`, one `broker_next_action`, open request summary, queued/received items, latest visible events |

Canonical request-item statuses are `queued`, `active`, `in_progress`, `satisfied`, `withdrawn`, and `superseded`. A request group is `open`, `completed`, `withdrawn`, or `superseded`; only one open group may exist per case.

Ordering is immutable for already satisfied items. Active selection is the lowest `position` open required item; ties are rejected. Queued items are returned in position order with `actionable: false`. A request can be amended only while open: it may add/reorder unsatisfied items and may supersede a not-started item; it must not silently mutate an accepted item. Withdrawal marks open unsatisfied items withdrawn and selects broker review. A terminal case rejects Slice 1 mutations without changing state.

Ownership: broker creates, amends, and withdraws request groups; customer may start or satisfy only the active item; system computes projections; AI may draft copy but never submits a command.

## 3. Minimum state transitions

| Actor / command | Precondition and state before | Canonical event | State after / customer Next Action | Broker result |
|---|---|---|---|---|
| Broker `RequestMoreCommand` | authorized broker; `broker_reviewing`; no open group; expected version matches | `broker_request_more_created` | `broker_more_requested`; primary is first active item | waiting for customer |
| Customer `StartRequestItem` (optional explicit command, otherwise first submit performs it) | customer task token authorizes case; open group; active item; version matches | `customer_continue_started` | `customer_continuing`; primary remains that item | customer responding |
| Customer `CustomerSubmissionCommand` when another item remains | active request item matches; typed payload/evidence validates; version matches | `field_saved` or `evidence_received`, then `customer_request_item_satisfied` | `customer_continuing`; next ordered item becomes active and is the sole primary action | waiting for next customer item |
| Customer `CustomerSubmissionCommand` when final item is satisfied | same as above | `field_saved` or `evidence_received`, then `supplement_submitted` | `broker_review_ready`; customer action is wait for broker review | start/restart review |
| Broker `AmendRequestMore` | authorized; open group; expected version matches; no item is `in_progress` unless amendment does not change it | `broker_request_more_amended` | state remains `broker_more_requested` or `customer_continuing`; recompute active item | amend result is visible |
| Broker `WithdrawRequestMore` | authorized; open group; expected version matches | `broker_request_more_withdrawn` | `broker_review_ready`; wait for broker review | start/restart review |

Stale conditional commands return `409 conflict` and the current projection; they append no business event. A same-key retry returns its stored result unchanged. A customer request for a queued, withdrawn, superseded, or nonmatching item is `422 request_item_not_active`. A partial upload is retained as an unbound upload attempt where existing upload policy permits, but cannot satisfy the item until the typed submission command validates; its primary action remains the current item. If a broker amendment wins while a customer is responding, the customer command conflicts and reloads; if customer completion wins, broker must rehydrate and make a new meaningful request. Terminal state returns `409 case_not_active`; no customer retry can reopen it.

## 4. Canonical Slice 1 timeline events

Each accepted command has one primary business outcome. A customer submit may append `submitted` and `satisfied` as an atomic event pair because receipt of evidence and satisfaction of a request item are distinct durable facts.

| Event | Actor / visibility | Required payload and identity |
|---|---|---|
| `broker_request_more_created` | broker / customer_and_broker | `request_id`, ordered item snapshots, customer-safe reason; identity `case:broker_request_more_created:broker:request_id` |
| `broker_request_more_amended` | broker / customer_and_broker | request ID, amendment number, added/reordered/superseded item IDs; identity `case:broker_request_more_amended:broker:request_id:amendment_no` |
| `broker_request_more_withdrawn` | broker / customer_and_broker | request ID, reason, withdrawn item IDs; identity `case:broker_request_more_withdrawn:broker:request_id` |
| `customer_continue_started` | customer / customer_and_broker | request ID, active item ID, client draft marker; identity `case:customer_continue_started:customer:request_id:command_id` |
| `customer_request_item_satisfied` | system on accepted customer command / customer_and_broker | request ID, item ID, `satisfied_by_event_id`; identity derives from accepted submission command |
| `field_saved` or `evidence_received` | customer / customer_and_broker | request ID, item ID, fact value hash or attachment IDs, client draft ID; identity follows the canonical field/evidence event contract |
| `supplement_submitted` | customer / customer_and_broker | request ID, final item ID, all accepted request item IDs; identity `case:supplement_submitted:customer:request_id:command_id` |

Every event also carries server-assigned `event_id`, `command_id`, `correlation_id`, `case_id`, `sequence_number`, `aggregate_version`, `state_before`, `state_after`, server acceptance timestamp, actor identity, and idempotency key. Customer event payload never exposes internal authorization or operational diagnostics.

## 5. Command acceptance and storage design

Choose **B — add a Slice 1 command service around existing storage**.

It is safer than enhancing unrelated direct writes (option A), because all Slice 1 mutations cross one serializing boundary; it is much smaller and reversible compared with a generic command/event platform (option C). Existing H5 intake, uploads, and Workbench commands continue unchanged. Slice 1 creates its own versioned event/outcome records and adapts the existing mutable case projection after acceptance.

### Atomic acceptance

Inside one Postgres transaction:

1. Authenticate actor and load `service_records` row `FOR UPDATE`.
2. Lookup `(case_id, actor_identity, idempotency_key)` in a command-outcome ledger. Return the exact stored response for any replay.
3. Read the Slice 1 aggregate row and compare `expected_state_version`.
4. Validate legal state, one-open-request invariant, active item ownership, and typed payload/evidence binding.
5. Insert ordered canonical event row(s), request/item updates, and command outcome.
6. Update the Slice 1 aggregate state/version and materialized customer/broker projection in the same transaction.
7. Update the legacy case JSON projection (`claim_phase`, request summary, and legacy display timeline adapter) only as a derived compatibility write in that transaction.
8. Return authoritative projection and version.

The initial implementation may retain a compact customer-visible Slice 1 event summary in legacy `claim_timeline`, but it must not rely on the capped list for source of truth. The canonical tables are retained; the current 50-event cap remains a legacy display limitation only. A failed transaction rolls back all Slice 1 rows and projection mutation. A compensating rollback is unnecessary; disabling the flag stops new commands while read projections remain intact.

Required tables are: `claim_slice1_aggregates` (case ID, state, version, active request ID, timestamps), `claim_request_groups`, `claim_request_items`, `claim_slice1_events`, and `claim_slice1_command_outcomes`. Add unique constraints for `(case_id, open_request_marker)`, `(case_id, sequence_number)`, `(case_id, actor_identity, idempotency_key)`, accepted `command_id`, and `(request_id, position)`. Evidence bytes remain in current attachment storage; request-item bindings reference attachment IDs. Content-hash canonical evidence deduplication is deferred to Slice 4.

## 6. Server-owned Next Action

`GET /api/h5/tasks/{token}/intake` gains additive `task_contract_v1` / `slice1_projection`; old contract v0 remains available.

```text
CustomerNextAction {
  action_type: provide_fact | provide_evidence | wait_for_broker_review | contact_broker
  request_id, request_item_id, title, instructions, required_input,
  status, ordering, allowed_actions, version, last_updated_at
}
```

The projector uses: terminal state first; then open Slice 1 request; then current legacy task projection. For an open request, the first non-satisfied non-withdrawn item in server position order is the only primary action. Queued items appear as read-only “coming next.” After final satisfaction, the customer action is `wait_for_broker_review`. The client must neither choose an item nor replace an open request action with `resolveNextAction`.

`BrokerNextAction` returns `create_request`, `wait_for_customer_item`, `review_customer_response`, or `none`, plus the same case version and request progress. Both projections are generated in the same command transaction and returned from the same aggregate version.

## 7. Mini Program design

Add a focused generic request-item page rather than altering all base intake pages:

| Path | Responsibility / state | Primary and lifecycle behavior |
|---|---|---|
| `miniapp/pages/task-home/task-home.ts` | Render server primary action and queued request summary. | Route Slice 1 action to request-item page; no supplement action sheet when an open request exists. `onShow` reconciles after a completed initialization. |
| `miniapp/pages/request-item/request-item.ts` (new) | Render exactly the active item; `pageState`, `task`, `nextAction`, `draft`, `draftId`, `commandId`, `submitState`, `errorState`; upload slots keep item-level status. | One submit CTA; immediate busy/local-preview feedback; submit same command ID after timeout; accepted/replay/conflict replaces local state with response; queued items are display-only. |
| `miniapp/behaviors/taskPage.ts` | Shared authoritative load and lifecycle guard. | Add single-flight load promise, page-alive/unload guard, request generation for every load, and `rehydrateAuthoritativeTask`; keep current safe defaults and bounded retry. |
| `miniapp/services/taskApi.ts` / `miniapp/types/task.ts` | Add v1 projection and request command client types. | Send command and idempotency headers, expected version, client draft ID; distinguish accepted/replayed/conflict/rejected/expired. |
| `miniapp/utils/resolveTaskViewModel.ts` / `miniapp/utils/taskMapping.ts` | Prefer Slice 1 server action. | Map only server-request action to new route; legacy inference remains solely for old/no-capability cases. |
| `miniapp/app.json` | Register new page. | Add request-item route; no unrelated navigation changes. |

First render has complete JSON-serializable defaults: empty strings/arrays/objects, `pageState: loading`, no undefined WXML binding. `onLoad` parses nothing beyond current server task context and owns first load. First `onShow` awaits that load; later `onShow` rehydrates server truth once. Pull-to-refresh is reconciliation only. `onHide` stores only policy-safe draft text, IDs, and selected-file metadata; `onUnload` invalidates generation and releases local handles. No raw unconfirmed file is asserted as received.

Submission and upload use separate page/item loading. A tap immediately disables that item/CTA and shows progress; confirmation happens only after command response and subsequent projection read-back. Transport timeout retains the same command ID and draft. Retry is shown only while no acceptance result is known. Conflict clears stale request UI and presents the returned server Next Action. Invalid/expired token clears launch token and shows contact guidance. All async branches use `finally`; no page reaches a white screen.

This incorporates Interaction Constitution rules 1–16, especially first-render defaults, one initialization owner, state separation, timeout termination, stale/destroyed-page guards, stable intents, server-authoritative draft reconciliation, and Preview/phone preflight.

## 8. Broker Workbench design

On a Claim in `broker_reviewing`, show one compact “Request more” action above the existing brief. The modal requires one or more structured items (`type`, label, instructions, required); drag/order controls assign positions. Submit sends the expected projection version and disables duplicate submission. The returned projection replaces local `currentCase`.

For an open request group, show the request reason, ordered list, active/queued/satisfied state, latest customer receipt, and one broker next action. “Amend” is the same request group, not another request. “Withdraw request” requires a reason. The action is disabled while stale/loading; a conflict refreshes the case and asks the broker to review current progress before issuing a new command. When all items are satisfied, Workbench displays `broker_review_ready` and “Review customer response,” with the receipt and canonical event list.

## 9. Compatibility strategy

Use a **feature flag plus case-level capability version and dual read**, not bulk migration or uncontrolled dual write.

* New/explicitly enabled Claim cases receive `slice1_capability_version: 1`; old cases retain current H5/Workbench behavior.
* Reads first use the Slice 1 projection when capability version is 1, otherwise use existing `claim_phase`, H5 contract v0, evidence gallery, and timeline.
* The command service writes canonical Slice 1 tables and a small compatible case summary. Legacy fields remain read-compatible but are never the authority for enabled cases.
* Existing free-text notes and legacy timeline remain visible as `legacy` history; no history conversion is required.
* Existing attachments can be selected as evidence only after explicit binding to the active item; partially uploaded evidence remains unbound and is never falsely marked satisfied.
* `active_case_id` / token selection continues unchanged; the token identifies the same case and receives its capability projection.
* Older Mini Program clients receive v0-compatible wait/continue copy and must not be enabled for structured request submission until the additive v1 client capability is available.

## 10. API contract

| Endpoint | Authorization / request | Success and retry |
|---|---|---|
| `POST /api/inbox/cases/{case_id}/request-more` | office/broker access; `RequestMoreCommand` | 201 accepted or 200 replay; 409 version conflict with projection; 422 validation |
| `PATCH /api/inbox/cases/{case_id}/request-more/{request_id}` | broker and expected version; ordered amendment | accepted/replay/conflict response |
| `POST /api/inbox/cases/{case_id}/request-more/{request_id}/withdraw` | broker and expected version | accepted/replay/conflict response |
| `GET /api/h5/tasks/{token}/intake` | existing signed task token | v0 plus additive Slice 1 projection / authoritative version |
| `POST /api/h5/tasks/{token}/request-items/{item_id}/submit` | token case/user binding; `CustomerSubmissionCommand` | 200 accepted/replayed; 409 conflict; 422 wrong/incomplete item; 403 expired/unauthorized |
| `POST /api/h5/tasks/{token}/resume` | token | no mutation required for normal resume; returns authoritative projection. Optional system audit is deferred. |

All mutation responses include `outcome`, `command_id`, `correlation_id`, idempotency key, event IDs, `aggregate_version`, customer action, broker action (broker-only), and request summary. Request command IDs are client-generated UUIDs; server persists outcomes for accepted, conflict, and rejected commands so retries receive the same result.

## 11. Test matrix

| Area | Focused coverage |
|---|---|
| Domain | ordered selection; exactly one active item; queued display; all-satisfied review return; stale version; replay; amendment; withdrawal; terminal rejection; customer/broker simultaneous completion/amendment |
| API | office/customer authorization; command outcome replay; version conflict contains current projection; invalid item/type; duplicate submission; authoritative action/version; transaction rollback |
| Mini Program | first-render defaults; single-flight load; stale response ignored; timeout cleanup; double tap; background/foreground; next-day resume; expired session; destroyed page; server beats stale draft; queued items non-actionable |
| Workbench | create request; ordered/amend/withdraw; disabled duplicate action; customer progress and receipt; return to review; stale broker refresh |
| End to end | broker requests VIN; customer submits VIN; broker requests VIN then insurance card; timeout then retry; next-day resume; broker amendment while customer is active; duplicate customer submit yields one business event/task |

## 12. Release and rollback

Deploy tables/migrations first, then command service and read projection behind `P20_SLICE1_REQUEST_MORE`, then Workbench entry, then Mini Program client capability, and finally case-level enablement for test cases. The default remains off.

Observe command outcomes, transaction errors, accepted/replayed/conflict/rejected counts, command latency, request completion rate, broker-request-to-completion time, resume success, customer/broker projection-version mismatch, and duplicate business-event count. Alert on any mismatch, duplicate event, missing command outcome, data write failure, or customer blank/recoverable-error rate above agreed release thresholds.

Rollback disables new Workbench entry and v1 customer CTA, while read APIs keep rendering accepted Slice 1 projections and legacy timeline summaries. Do not delete command/event/request data. If an enabled case needs recovery, keep it read-only under the Slice 1 projection and use a forward-fix; do not revert it to inferred legacy state. No-data-loss is required for accepted requests, submissions, attachments, and command receipts.

## 13. File-by-file implementation plan

| File | Intended change / risk / required tests |
|---|---|
| `services/fiqa_api/db/schema/migrations/00x_p20_slice1_request_more.sql` (new) | Canonical aggregate, request, item, event, and outcome tables plus uniqueness/indexes. **High:** transaction and migration correctness. Integration migration, unique/replay/concurrency tests. |
| `services/fiqa_api/db/service_record_repository.py` | Add transactional Slice 1 repository methods using `FOR UPDATE`; do not alter generic append semantics. **High:** aggregate serialization. Transaction rollback/concurrency tests. |
| `services/fiqa_api/inbox_triage/p20_slice1_command_service.py` (new) | `accept_request_more`, `amend`, `withdraw`, `submit_request_item`, projector and legal transition validator. **High:** source of truth. Full domain transition suite. |
| `services/fiqa_api/inbox_triage/case_store.py` | Add a compatibility projection helper only; do not route Slice 1 through `append_claim_timeline_event`. **Medium:** legacy drift. Enabled-case projection tests. |
| `services/fiqa_api/routes/inbox_triage.py` | Add broker Request More/amend/withdraw models and routes, office auth, conflict mappings. **High:** authorization and response contract. API authorization/replay tests. |
| `services/fiqa_api/routes/h5_task_intake.py` | Add request-item submit/resume endpoints with token authorization. **High:** customer/case binding. Token and wrong-item API tests. |
| `services/fiqa_api/inbox_triage/h5_task_intake.py` | Extend `build_customer_task_contract` / `intake_info_for_token` with v1 projection selection. **Medium:** old client compatibility. v0/v1 fixture tests. |
| `services/fiqa_api/inbox_triage/h5_task_upload.py` | Expose a safe attachment-binding handoff for request-item evidence; retain existing byte/storage validation. **High:** evidence receipt semantics. Timeout/retry/read-back tests. |
| `services/fiqa_api/inbox_triage/claim_workbench_display.py` | Project Slice 1 request progress, broker action, and canonical event ordering. **Medium:** truth/copy parity. Projection contract tests. |
| `services/fiqa_api/inbox_triage/workbench_enrichment.py` | Include Slice 1 projections in enabled Claim case responses. **Low:** response compatibility. Workbench payload tests. |
| `ui/src/api/inboxTriage.ts` | Add types and request-more client methods. **Low:** API typing. Contract tests. |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Add request modal, progress display, version conflict rehydrate, and single-flight action flags. **Medium:** stale UI. Component/action integration tests. |
| `ui/src/features/intake/components/ClaimCaseBriefPanel.tsx` | Display active/queued/satisfied request summary and timeline receipt. **Low:** rendering. Old/no-projection render tests. |
| `miniapp/app.json` | Register request-item page. **Low:** component/route gate. DevTools compile. |
| `miniapp/types/task.ts` | Add additive v1 projection/command response types. **Low:** old contract compile. Type/fixture tests. |
| `miniapp/services/taskApi.ts` | Add submit/resume command methods and outcome parsing. **Medium:** intent reuse. Timeout/replay/conflict tests. |
| `miniapp/behaviors/taskPage.ts` | Add page-alive and single-flight task rehydration. **Medium:** shared regression surface. Lifecycle/stale/destroyed-page tests. |
| `miniapp/utils/resolveTaskViewModel.ts` / `miniapp/utils/taskMapping.ts` | Server action has precedence for enabled cases; legacy inference only otherwise. **High:** one-primary-action invariant. V0/v1 routing tests. |
| `miniapp/pages/task-home/task-home.ts` | Render one primary action and non-actionable queue. **Medium:** client authority regression. CTA/foreground tests. |
| `miniapp/pages/request-item/*` (new) | Typed fact/evidence UI, draft/retry/read-back states. **High:** mobile reliability. All applicable Reliability Gate tests and device QA. |
| `tests/test_p20_slice1_command_service.py`, `tests/test_p20_slice1_api.py`, `miniapp/tests/requestItemPage.test.ts`, Workbench tests (new) | Focused behavior and contract suites. **High:** gates release. Matrix above. |

## 14. Explicit non-goals

* Full event-sourcing conversion, historic timeline migration, or removal of the existing 50-event legacy display list.
* General CAS for non-Slice-1 commands.
* Content-hash canonical evidence deduplication, duplicate-attempt lineage, OCR, and media-gallery redesign.
* Terminal supplement, reopen/reactivation, broker confirmation redesign, carrier filing, coverage, fault, payment, or AI-owned action.
* Bulk migration of legacy free-text requests or forcing older Mini Program clients into a new workflow.

## 15. Open decisions

1. Approve the exact broker authorization identity exposed by the current office access layer for immutable event actor identity.
2. Approve customer-safe Chinese labels/instructions and allowed Slice 1 item types (recommended first set: `vin`, `policy_or_insurance_card`, `free_text`, `photo_evidence`).
3. Approve local unconfirmed-file retention/reselection policy for session expiry (WBL-018); default is metadata only, no raw-file persistence.
4. Confirm that an evidence upload is only satisfied by an explicit request-item submission/binding, not upload alone.
5. Set production retention duration for command outcomes and Slice 1 event records; recommended: retain for case lifetime.

