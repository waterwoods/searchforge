/**
 * P20 Capability 3A/3B — H5 QR landing decision tests.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/claim-h5/h5ClaimLanding.test.ts
 */
import assert from 'node:assert/strict';
import type { H5ClaimIntakeInfo } from '@/api/h5ClaimIntake';
import { mapH5ClaimError } from '@/api/h5ClaimIntake';
import type { Slice1NextAction, Slice1Projection } from '@/api/inboxTriage';
import {
  customerUiLeaksCaseId,
  isActiveRequestItemAction,
  resolveCustomerQaMarker,
  resolveH5ClaimLanding,
} from './h5ClaimLanding';

function vinAction(overrides: Partial<Slice1NextAction> = {}): Slice1NextAction {
  return {
    action_type: 'provide_fact',
    request_id: 'req_1',
    request_item_id: 'item_vin_1',
    title: '补充车辆 VIN',
    instructions: '陈总需要这项资料继续处理',
    required_input: 'vin',
    status: 'active',
    ordering: { position: 1, total: 1 },
    allowed_actions: ['submit_request_item'],
    version: 2,
    ...overrides,
  };
}

function baseInfo(overrides: Partial<H5ClaimIntakeInfo> = {}): H5ClaimIntakeInfo {
  return {
    lane: 'claim',
    flow: 'claim_intake_form',
    case_id: 'case_d3187eb826f4',
    title: '我的报案',
    safety_copy: 'safety',
    steps: ['start', 'injury', 'done'],
    current_step: 'start',
    completed_count: 0,
    step_total: 4,
    submitted: false,
    phase: 'collecting',
    key_facts: {},
    missing_info: [
      { field: 'accident_datetime', label: '事故时间' },
      { field: 'accident_location', label: '事故地点' },
    ],
    dashboard_summary: {
      title: '我的报案',
      subtitle: '请补充资料',
      status: '资料收集中',
      received: [],
      missing: ['事故时间', '事故地点', '事故经过', '车辆信息'],
      next_action: '继续填写',
      primary_cta: '继续填写资料',
      secondary_cta: '返回微信',
      submitted_supplement_allowed: false,
      warning: 'disclaimer',
    },
    is_test: false,
    slice1_projection_error: false,
    customer_qa_marker: null,
    ...overrides,
  };
}

function withVinProjection(info?: Partial<H5ClaimIntakeInfo>): H5ClaimIntakeInfo {
  const action = vinAction();
  const projection: Slice1Projection = {
    case_id: 'case_d3187eb826f4',
    workflow_state: 'broker_more_requested',
    aggregate_version: 2,
    customer_next_action: action,
    request_progress: { satisfied: 0, total: 1, remaining: 1 },
    open_request: {
      request_id: 'req_1',
      status: 'open',
      progress: { satisfied: 0, total: 1, remaining: 1 },
      active_item: {
        request_item_id: 'item_vin_1',
        item_type: 'vin',
        label: '补充车辆 VIN',
        instructions: '陈总需要这项资料继续处理',
        required: true,
        position: 1,
        status: 'active',
        actionable: true,
      },
    },
  };
  return baseInfo({
    slice1_projection: projection,
    task_contract_v1: {
      contract_version: '1',
      next_action: action,
      request_progress: { satisfied: 0, total: 1, remaining: 1 },
    },
    ...info,
  });
}

test('free_text active item → unsupported_request_item landing', () => {
  const action: Slice1NextAction = {
    ...vinAction(),
    title: 'Vehicle year / make / model',
    required_input: 'free_text',
  };
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: baseInfo({
      slice1_projection: {
        case_id: 'case_d3187eb826f4',
        workflow_state: 'broker_more_requested',
        aggregate_version: 2,
        customer_next_action: action,
        request_progress: { satisfied: 0, total: 2, remaining: 2 },
      },
      task_contract_v1: { next_action: action },
    }),
  });
  assert.equal(decision.kind, 'unsupported_request_item');
  assert.equal(decision.errorMessage, 'customer_submit_not_supported');
  assert.equal(decision.progress.total, 2);
});

test('mapH5ClaimError surfaces customer_submit_not_supported', () => {
  assert.match(mapH5ClaimError('customer_submit_not_supported'), /微信/);
});

test('active VIN task → direct request-item landing', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: withVinProjection({ is_test: true, customer_qa_marker: 'TEST · Cap3A VIN QA' }),
  });
  assert.equal(decision.kind, 'request_item');
  assert.equal(decision.itemType, 'vin');
  assert.equal(decision.title, '补充车辆 VIN');
  assert.equal(decision.instructions, '陈总需要这项资料继续处理');
  assert.equal(decision.progress.satisfied, 0);
  assert.equal(decision.progress.total, 1);
  assert.equal(decision.qaMarker, 'TEST · Cap3A VIN QA');
});

test('no active task after Cap 3B submit → submitted_waiting (not overview)', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: baseInfo({
      is_test: true,
      slice1_projection: {
        case_id: 'case_d3187eb826f4',
        workflow_state: 'broker_review_ready',
        aggregate_version: 3,
        customer_next_action: {
          action_type: 'wait_for_broker_review',
          title: '资料已收到',
          instructions: '陈总正在审核中。',
          request_item_id: null,
        },
        request_progress: { satisfied: 1, total: 1, remaining: 0 },
      },
    }),
  });
  assert.equal(decision.kind, 'submitted_waiting');
  assert.equal(decision.title, '资料已收到');
  assert.equal(decision.instructions, '陈总正在审核中。');
  assert.equal(decision.qaMarker, 'TEST · Cap3B Review QA');
  assert.notEqual(decision.kind, 'overview');
});

test('projection error → retry UI (never silent overview)', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: baseInfo({
      slice1_projection_error: true,
      is_test: true,
      customer_qa_marker: 'QA Test Claim',
    }),
  });
  assert.equal(decision.kind, 'projection_error');
  assert.equal(decision.retryable, true);
  assert.notEqual(decision.kind, 'overview');
});

test('invalid/expired token → safe error', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: 'invalid_or_expired_task_link',
    info: null,
  });
  assert.equal(decision.kind, 'token_error');
  assert.equal(decision.retryable, false);
});

test('network load error → retry UI', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: 'network_error',
    info: null,
  });
  assert.equal(decision.kind, 'load_error');
  assert.equal(decision.retryable, true);
});

test('TEST marker visible only for QA claim', () => {
  const qa = resolveCustomerQaMarker(
    withVinProjection({ is_test: true, customer_qa_marker: 'TEST · Cap3A VIN QA' }),
  );
  assert.equal(qa, 'TEST · Cap3A VIN QA');

  const prod = resolveCustomerQaMarker(withVinProjection({ is_test: false, customer_qa_marker: null }));
  assert.equal(prod, null);

  const inferred = resolveCustomerQaMarker(withVinProjection({ is_test: true, customer_qa_marker: null }));
  assert.equal(inferred, 'TEST · Cap3A VIN QA');
});

test('raw case ID must not appear in customer-facing landing copy', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: withVinProjection({ is_test: true, customer_qa_marker: 'TEST · Cap3A VIN QA' }),
  });
  const caseId = 'case_d3187eb826f4';
  assert.equal(customerUiLeaksCaseId(decision.title, caseId), false);
  assert.equal(customerUiLeaksCaseId(decision.instructions, caseId), false);
  assert.equal(customerUiLeaksCaseId(decision.qaMarker || '', caseId), false);
  assert.equal(customerUiLeaksCaseId(`bad ${caseId}`, caseId), true);
});

test('refresh preserves direct task landing (deterministic from projection)', () => {
  const info = withVinProjection({ is_test: true, customer_qa_marker: 'TEST · Cap3A VIN QA' });
  const first = resolveH5ClaimLanding({ loading: false, loadError: null, info });
  const refreshed = resolveH5ClaimLanding({ loading: false, loadError: null, info: { ...info } });
  assert.equal(first.kind, 'request_item');
  assert.equal(refreshed.kind, 'request_item');
  assert.equal(first.nextAction?.request_item_id, refreshed.nextAction?.request_item_id);
  assert.equal(first.title, refreshed.title);
});

test('duplicate routing prevented: same active item stays request_item', () => {
  const info = withVinProjection();
  const a = resolveH5ClaimLanding({ loading: false, loadError: null, info });
  const b = resolveH5ClaimLanding({ loading: false, loadError: null, info });
  assert.equal(a.kind, 'request_item');
  assert.equal(b.kind, 'request_item');
  assert.equal(a.nextAction?.request_item_id, b.nextAction?.request_item_id);
  assert.equal(isActiveRequestItemAction(a.nextAction), true);
});

test('contact_broker / missing request_item_id does not hijack landing', () => {
  const decision = resolveH5ClaimLanding({
    loading: false,
    loadError: null,
    info: baseInfo({
      slice1_projection: {
        case_id: 'case_d3187eb826f4',
        workflow_state: 'idle',
        aggregate_version: 0,
        customer_next_action: {
          action_type: 'contact_broker',
          title: '请联系陈总办公室',
          request_item_id: null,
        },
      },
    }),
  });
  assert.equal(decision.kind, 'overview');
});

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (err) {
    console.error(`not ok - ${name}`);
    throw err;
  }
}

console.log('h5ClaimLanding.test: PASS');
