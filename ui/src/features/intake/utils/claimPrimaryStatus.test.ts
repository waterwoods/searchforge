/**
 * Claim Workbench — single primary next-action precedence.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/utils/claimPrimaryStatus.test.ts
 */
import assert from 'node:assert/strict';
import test from 'node:test';

import type { SavedCase } from '@/api/inboxTriage';
import {
  resolveBrokerHeaderFields,
} from '@/features/intake/components/BrokerHeader.tsx';
import {
  CLAIM_PRIMARY_STATUS,
  resolveClaimPrimaryStatus,
  requestMoreOwnsPrimaryStatus,
} from './claimPrimaryStatus.ts';
import { resolveCurrentActionLabel } from './workbenchFindability.ts';

function claimCase(partial: Partial<SavedCase> & { case_id: string }): SavedCase {
  return {
    case_status: 'new',
    created_at: '2026-07-31T00:00:00Z',
    updated_at: '2026-07-31T00:10:00Z',
    source_text: '',
    service_lane: 'claim',
    ...partial,
  } as SavedCase;
}

const CAP2_FACTS = {
  accident_description: '刮蹭',
  accident_datetime: '今天',
  accident_location: 'Irvine',
  injury_status: 'no',
};

test('1. Fresh Cap2-complete → only 建议确认资料已齐', () => {
  const c = claimCase({
    case_id: 'case_cap2_fresh',
    known_facts: CAP2_FACTS,
    claim_case_brief: {
      can_accept_office_materials: true,
      office_materials_ready_suggestion: '建议确认资料已齐',
      missing_info: [
        { key: 'vin', label: 'VIN', severity: 'optional' },
      ],
    },
    workbench_list: {
      broker_next_action_label: '客户补充中，必要时再 Request More',
    },
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'suggest_accept');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.suggestAccept);
  assert.equal(resolveCurrentActionLabel(c), CLAIM_PRIMARY_STATUS.suggestAccept);
  assert.equal(requestMoreOwnsPrimaryStatus(c), false);
});

test('2. Customer supplement awaiting review → only 等待办公室审核', () => {
  const c = claimCase({
    case_id: 'case_review',
    known_facts: CAP2_FACTS,
    claim_case_brief: {
      can_accept_office_materials: true,
      office_materials_ready_suggestion: '建议确认资料已齐',
    },
    p20_slice1_projection: {
      workflow_state: 'broker_review_ready',
      broker_next_action: {
        action_type: 'review_customer_response',
        status: 'review_ready',
      },
      open_request: {
        progress: { total: 1, satisfied: 1 },
        items: [{ status: 'satisfied', item_type: 'vin', label: 'VIN' }],
      },
    } as SavedCase['p20_slice1_projection'],
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'waiting_office_review');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.waitingOfficeReview);
  assert.equal(resolveCurrentActionLabel(c), CLAIM_PRIMARY_STATUS.waitingOfficeReview);
  assert.equal(requestMoreOwnsPrimaryStatus(c), true);
  // Cap2-complete must not surface as a second primary.
  assert.notEqual(primary.label, CLAIM_PRIMARY_STATUS.suggestAccept);
});

test('3. Open Request More → only 等待客户补充', () => {
  const c = claimCase({
    case_id: 'case_open_rm',
    waiting_on: 'client',
    office_materials_accepted_at: '2026-07-31T18:00:00Z',
    display_status: '办公室处理中',
    known_facts: CAP2_FACTS,
    claim_case_brief: { can_accept_office_materials: false },
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'waiting_customer');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.waitingCustomer);
  assert.equal(resolveCurrentActionLabel(c), CLAIM_PRIMARY_STATUS.waitingCustomer);
});

test('4. Broker office acceptance → only 办公室处理中', () => {
  const c = claimCase({
    case_id: 'case_office',
    office_materials_accepted_at: '2026-07-31T18:00:00Z',
    known_facts: CAP2_FACTS,
    claim_case_brief: {
      can_accept_office_materials: false,
      office_materials_accepted_at: '2026-07-31T18:00:00Z',
      office_materials_ready_suggestion: '建议确认资料已齐',
    },
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'office_processing');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.officeProcessing);
  assert.equal(resolveCurrentActionLabel(c), CLAIM_PRIMARY_STATUS.officeProcessing);
  assert.notEqual(primary.label, CLAIM_PRIMARY_STATUS.suggestAccept);
});

test('5. Optional gaps never produce required-missing primary', () => {
  const c = claimCase({
    case_id: 'case_optional',
    known_facts: CAP2_FACTS,
    claim_case_brief: {
      can_accept_office_materials: true,
      missing_info: [
        { key: 'other_party', label: '对方信息', severity: 'optional' },
        { key: 'vin', label: 'VIN', severity: 'optional' },
      ],
      next_best_question: '建议确认资料已齐',
    },
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'suggest_accept');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.suggestAccept);
  assert.equal(primary.label.includes('还缺'), false);
  assert.equal(primary.label.includes('对方信息'), false);
});

test('6. Stale legacy multi-field case resolves to exactly one primary', () => {
  const c = claimCase({
    case_id: 'case_stale_dual',
    display_status: '理赔 · 记录中',
    waiting_on: 'broker',
    known_facts: CAP2_FACTS,
    claim_case_brief: {
      can_accept_office_materials: true,
      office_materials_ready_suggestion: '建议确认资料已齐',
      next_best_question: '建议确认资料已齐',
    },
    customer_access: {
      request_sent: true,
      access_ready: true,
      simple_status: 'Ready for Review',
      progress: { total_count: 1, satisfied_count: 1 },
    } as SavedCase['customer_access'],
    workbench_list: {
      broker_next_action_label: '客户补充中，必要时再 Request More',
      customer_current_action_label: '等待经纪人',
    },
    p20_slice1_projection: {
      workflow_state: 'broker_review_ready',
      broker_next_action: {
        action_type: 'review_customer_response',
        status: 'review_ready',
      },
      open_request: {
        progress: { total: 1, satisfied: 1 },
        items: [{ status: 'satisfied', item_type: 'policy_or_insurance_card', label: '保险卡' }],
      },
    } as SavedCase['p20_slice1_projection'],
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'waiting_office_review');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.waitingOfficeReview);
  // Exactly one label — not Cap2 accept and not English Request More residue.
  assert.equal(primary.label === CLAIM_PRIMARY_STATUS.suggestAccept, false);
  assert.equal(primary.label.includes('Request More'), false);
  assert.equal(primary.label.includes('等待经纪人'), false);
});

test('7. Queue, header and Brief next-action agree', () => {
  const c = claimCase({
    case_id: 'case_agree',
    customer_name: '陈明',
    known_facts: { ...CAP2_FACTS, own_vehicle_info: '2020 Toyota Camry' },
    primary_vehicle_summary: '2020 Toyota Camry',
    claim_case_brief: { can_accept_office_materials: true },
    p20_slice1_projection: {
      workflow_state: 'broker_review_ready',
      open_request: {
        progress: { total: 1, satisfied: 1 },
        items: [{ status: 'satisfied', item_type: 'vin', label: 'VIN' }],
      },
    } as SavedCase['p20_slice1_projection'],
  });
  const primary = resolveClaimPrimaryStatus(c);
  const queue = resolveCurrentActionLabel(c);
  const header = resolveBrokerHeaderFields(c).currentNextAction;
  assert.equal(queue, primary.label);
  assert.equal(header, primary.label);
  assert.equal(queue, CLAIM_PRIMARY_STATUS.waitingOfficeReview);
});

test('closed / history is terminal primary', () => {
  const c = claimCase({
    case_id: 'case_closed',
    case_status: 'closed',
    known_facts: CAP2_FACTS,
    claim_case_brief: { can_accept_office_materials: true },
    waiting_on: 'client',
  });
  const primary = resolveClaimPrimaryStatus(c);
  assert.equal(primary.key, 'closed');
  assert.equal(primary.label, CLAIM_PRIMARY_STATUS.closed);
});

console.log('claimPrimaryStatus.test.ts: all assertions queued under node:test');
