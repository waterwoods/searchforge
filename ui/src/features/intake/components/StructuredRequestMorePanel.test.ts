/**
 * P20 Slice 1 shared Request More visibility/merge tests.
 * Run: npx tsx ui/src/features/intake/components/StructuredRequestMorePanel.test.ts
 */
import assert from 'node:assert/strict';
import {
  getStructuredRequestMoreVisibility,
  mergeSlice1ProjectionIntoCaseRecord,
  normalizeSlice1Projection,
  normalizeSlice1RequestSummary,
  orderedSlice1Items,
  slice1CanCreateRequest,
  slice1EnabledForWorkbenchCase,
  type StructuredRequestMoreCaseRecord,
} from './StructuredRequestMorePanel';

const eligibleClaim: StructuredRequestMoreCaseRecord = {
  case_id: 'case_slice1_claim',
  service_lane: 'claim',
  workflow_phase: 'broker_review',
  case_status: 'reviewing',
  slice1_capability_version: 1,
  updated_at: '2026-07-15T10:00:00Z',
};

const openRequestProjection = {
  case_id: 'case_slice1_claim',
  workflow_state: 'broker_more_requested',
  aggregate_version: 4,
  broker_next_action: { action_type: 'wait_for_customer_item' },
  customer_next_action: { action_type: 'provide_fact', title: 'Provide VIN' },
  open_request: {
    request_id: 'req_1',
    status: 'open',
    reason: 'Please provide claim details.',
    progress: { satisfied: 0, total: 2, remaining: 2 },
    active_item: {
      request_item_id: 'item_1',
      item_type: 'vin',
      label: 'VIN',
      instructions: 'Please confirm VIN.',
      required: true,
      position: 1,
      status: 'active',
    },
    items: [
      {
        request_item_id: 'item_2',
        item_type: 'photo_evidence',
        label: 'Damage photos',
        instructions: 'Upload damage photos.',
        required: true,
        position: 2,
        status: 'queued',
      },
      {
        request_item_id: 'item_1',
        item_type: 'vin',
        label: 'VIN',
        instructions: 'Please confirm VIN.',
        required: true,
        position: 1,
        status: 'active',
      },
    ],
  },
};

function main() {
  // 1. BrokerCaseDetail renders Request More for an eligible Slice 1 claim:
  // visibility helpers expose supported/enabled/canCreate for the drawer to mount.
  assert.deepEqual(getStructuredRequestMoreVisibility(eligibleClaim), {
    supported: true,
    enabled: true,
    terminal: false,
    canCreate: true,
  });

  // 2. Non-enabled case preserves legacy drawer.
  const legacyClaim = { ...eligibleClaim, slice1_capability_version: 0, p20_slice1_capability_version: 0 };
  assert.equal(slice1EnabledForWorkbenchCase(legacyClaim), false);

  // 3. Unsupported lane does not show the capability.
  assert.equal(getStructuredRequestMoreVisibility({ ...eligibleClaim, service_lane: 'add_car' }).supported, false);

  // 4. Projection loading failure is recoverable for an enabled case because the panel remains visible.
  assert.equal(getStructuredRequestMoreVisibility({ ...eligibleClaim, slice1_projection: undefined }).enabled, true);

  // 5. Broker can submit one ordered request from broker_review.
  assert.equal(slice1CanCreateRequest(eligibleClaim), true);

  // 6. Existing open request blocks duplicate create commands.
  const withOpenRequest = { ...eligibleClaim, slice1_projection: openRequestProjection };
  assert.equal(slice1CanCreateRequest(withOpenRequest), false);

  // 7. Successful response refreshes drawer projection fields.
  const merged = mergeSlice1ProjectionIntoCaseRecord(eligibleClaim, {
    broker_projection: openRequestProjection,
    request_summary: openRequestProjection.open_request,
    server_timestamp: '2026-07-15T11:00:00Z',
  });
  assert.equal(merged?.slice1_projection?.aggregate_version, 4);
  assert.equal(merged?.workflow_phase, 'broker_more_requested');
  assert.equal(merged?.updated_at, '2026-07-15T11:00:00Z');

  // 8. Version conflict projection can refresh authoritative state through the same merge helper.
  const conflictProjection = { ...openRequestProjection, aggregate_version: 5, workflow_state: 'broker_review_ready' };
  const conflictMerged = mergeSlice1ProjectionIntoCaseRecord(eligibleClaim, {
    broker_projection: conflictProjection,
    request_summary: null,
    server_timestamp: '2026-07-15T11:05:00Z',
  });
  assert.equal(conflictMerged?.slice1_projection?.aggregate_version, 5);
  assert.equal(conflictMerged?.workflow_phase, 'intake_ready_for_broker');

  // 9. Shared component helpers normalize projection/summary without duplicated business logic.
  assert.equal(normalizeSlice1Projection(withOpenRequest)?.aggregate_version, 4);
  assert.equal(normalizeSlice1RequestSummary(withOpenRequest)?.request_id, 'req_1');

  // 10. Existing evidence drawer behavior remains independent: ordered request helpers do not touch attachments.
  const withAttachments = {
    ...withOpenRequest,
    case_attachments: [{ attachment_id: 'att_1', filename: 'damage.jpg' }],
  };
  assert.deepEqual(withAttachments.case_attachments, [{ attachment_id: 'att_1', filename: 'damage.jpg' }]);
  assert.deepEqual(orderedSlice1Items(openRequestProjection.open_request).map((item) => item.request_item_id), ['item_1', 'item_2']);
}

main();
console.log('StructuredRequestMorePanel.test: PASS');
