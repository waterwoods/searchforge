/**
 * P20 Capability 3B — H5 request-item submit client helpers.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/api/h5ClaimIntake.cap3b.test.ts
 */
import assert from 'node:assert/strict';
import {
  applySlice1ProjectionToIntake,
  mapH5ClaimError,
  type H5ClaimIntakeInfo,
} from './h5ClaimIntake';
import type { Slice1Projection } from './inboxTriage';

function baseInfo(): H5ClaimIntakeInfo {
  return {
    lane: 'claim',
    flow: 'claim_intake_form',
    case_id: 'case_cap3b',
    title: '我的报案',
    safety_copy: 'safety',
    steps: ['start'],
    current_step: 'start',
    completed_count: 0,
    step_total: 1,
    submitted: false,
    phase: 'collecting',
    key_facts: {},
    missing_info: [],
    slice1_projection: {
      case_id: 'case_cap3b',
      workflow_state: 'broker_more_requested',
      aggregate_version: 2,
      customer_next_action: {
        action_type: 'provide_fact',
        request_item_id: 'item_vin',
        required_input: 'vin',
        title: '补充车辆 VIN',
      },
    },
    task_contract_v1: {
      workflow_state: 'broker_more_requested',
      aggregate_version: 2,
    },
  };
}

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (err) {
    console.error(`not ok - ${name}`);
    throw err;
  }
}

test('applySlice1ProjectionToIntake merges Cap 3B receipt into intake info', () => {
  const projection: Slice1Projection = {
    case_id: 'case_cap3b',
    workflow_state: 'broker_review_ready',
    aggregate_version: 5,
    customer_next_action: {
      action_type: 'wait_for_broker_review',
      title: '资料已收到',
      instructions: '陈总正在审核中。',
      request_item_id: null,
    },
    broker_next_action: {
      action_type: 'review_customer_response',
      status: 'review_ready',
    },
    request_progress: { satisfied: 1, total: 1, remaining: 0 },
    server_timestamp: '2026-07-15T12:00:00Z',
  };
  const merged = applySlice1ProjectionToIntake(baseInfo(), projection);
  assert.equal(merged.slice1_projection_error, false);
  assert.equal(merged.slice1_projection?.workflow_state, 'broker_review_ready');
  assert.equal(merged.slice1_projection?.aggregate_version, 5);
  assert.equal(merged.task_contract_v1?.workflow_state, 'broker_review_ready');
  assert.equal(merged.task_contract_v1?.aggregate_version, 5);
  assert.equal(merged.task_contract_v1?.next_action?.action_type, 'wait_for_broker_review');
  assert.equal(merged.task_contract_v1?.server_timestamp, '2026-07-15T12:00:00Z');
});

test('mapH5ClaimError surfaces Cap 3B validation and conflict codes', () => {
  assert.match(mapH5ClaimError('vin_invalid'), /VIN/);
  assert.match(mapH5ClaimError('version_conflict'), /刷新/);
  assert.match(mapH5ClaimError('network_error'), /网络/);
  assert.match(mapH5ClaimError('customer_submit_not_supported'), /微信/);
});

console.log('h5ClaimIntake.cap3b.test: PASS');
