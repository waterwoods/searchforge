/**
 * P3-B Slice 1 — Workbench findability helpers.
 */
import assert from 'node:assert/strict';
import test from 'node:test';

import type { SavedCase } from '@/api/inboxTriage';
import {
  defaultTestFilterForEnv,
  formatRelativeUpdated,
  isChenDemoCase,
  matchesWorkbenchFilters,
  matchesWorkbenchSearch,
  resolveCaseRef,
  resolveCurrentActionLabel,
  resolveFindabilityCustomerName,
  resolveIsTestCase,
  resolveQaLabel,
} from './workbenchFindability.ts';

function caseRow(partial: Partial<SavedCase> & { case_id: string }): SavedCase {
  return {
    case_status: 'new',
    created_at: '2026-07-23T00:00:00Z',
    updated_at: '2026-07-23T00:10:00Z',
    source_text: '',
    ...partial,
  } as SavedCase;
}

test('resolveCaseRef prefers workbench_list.case_ref', () => {
  const c = caseRow({
    case_id: 'case_deadbeef001',
    case_ref: 'CLM-0009',
    workbench_list: { case_ref: 'CLM-1028' },
  });
  assert.equal(resolveCaseRef(c), 'CLM-1028');
});

test('customer display never uses manufactured QA Customer as primary identity', () => {
  const c = caseRow({
    case_id: 'case_abc',
    customer_name: 'QA Customer',
    person_link_key: 'plk_xxzzab12',
    workbench_test: true,
  } as SavedCase);
  assert.equal(resolveFindabilityCustomerName(c), '微信客户 · ab12');
});

test('never surfaces wx_ or openid-like strings as primary name', () => {
  const c = caseRow({
    case_id: 'case_leak',
    customer_name: 'wx_abcdef1234567890',
    person_link_key: 'wx_suffix_ab12',
    customer_phone: '6265558888',
  } as SavedCase);
  const name = resolveFindabilityCustomerName(c);
  assert.equal(name, '微信客户 · ab12');
  assert.equal(name.includes('wx_'), false);
});

test('remark name beats real name; real name beats wecom nickname', () => {
  const withRemark = caseRow({
    case_id: 'case_1',
    customer_name: '陈明',
    extra: {
      customer_identity: {
        wecom_remark: '办公室备注',
        wecom_nickname: '昵称',
      },
    },
  } as SavedCase);
  assert.equal(resolveFindabilityCustomerName(withRemark), '办公室备注');

  const withName = caseRow({
    case_id: 'case_2',
    customer_name: '陈明',
    extra: { customer_identity: { wecom_nickname: '昵称' } },
  } as SavedCase);
  assert.equal(resolveFindabilityCustomerName(withName), '陈明');

  const withNick = caseRow({
    case_id: 'case_3',
    customer_name: 'QA Customer',
    extra: { customer_identity: { wecom_nickname: '小明爸' } },
  } as SavedCase);
  assert.equal(resolveFindabilityCustomerName(withNick), '小明爸');
});

test('list action prefers broker_next_action_label', () => {
  const c = caseRow({
    case_id: 'case_act',
    workbench_list: {
      customer_current_action_label: '先不用操作',
      broker_next_action_label: '等待办公室审核',
    },
  });
  assert.equal(resolveCurrentActionLabel(c), '等待办公室审核');
});

test('broker-confirmed name wins and phone last four remains available', () => {
  const c = caseRow({
    case_id: 'case_abc',
    customer_name: '陈明',
    customer_phone: '6265552345',
  });
  assert.equal(resolveFindabilityCustomerName(c), '陈明');
});

test('qa_label resolves from known_facts', () => {
  const c = caseRow({
    case_id: 'case_abc',
    known_facts: { qa_label: 'Founder-iPhone' },
  });
  assert.equal(resolveQaLabel(c), 'Founder-iPhone');
});

test('search matches case_ref, qa_label, and phone digits', () => {
  const c = caseRow({
    case_id: 'case_92da6e0bcfce',
    case_ref: 'CLM-1031',
    customer_phone: '6265552345',
    known_facts: { qa_label: 'Founder-iPhone', own_vehicle_info: '2021 Toyota Camry' },
    workbench_list: {
      case_ref: 'CLM-1031',
      customer_display_name: '微信客户 · ab12',
      phone_last_four: '2345',
      vehicle_summary: '2021 Toyota Camry',
      qa_label: 'Founder-iPhone',
    },
  });
  assert.equal(matchesWorkbenchSearch(c, 'CLM-1031'), true);
  assert.equal(matchesWorkbenchSearch(c, 'founder-iphone'), true);
  assert.equal(matchesWorkbenchSearch(c, '2345'), true);
  assert.equal(matchesWorkbenchSearch(c, 'camry'), true);
  assert.equal(matchesWorkbenchSearch(c, '92da6e0b'), true);
  assert.equal(matchesWorkbenchSearch(c, 'nope'), false);
});

test('TEST filter hide/show/only', () => {
  const testCase = caseRow({ case_id: 'case_t', workbench_test: true });
  const realCase = caseRow({ case_id: 'case_r', workbench_test: false });
  assert.equal(resolveIsTestCase(testCase), true);
  assert.equal(matchesWorkbenchFilters(testCase, { status: 'all', testFilter: 'hide' }), false);
  assert.equal(matchesWorkbenchFilters(testCase, { status: 'all', testFilter: 'show' }), true);
  assert.equal(matchesWorkbenchFilters(realCase, { status: 'all', testFilter: 'only' }), false);
  assert.equal(matchesWorkbenchFilters(testCase, { status: 'all', testFilter: 'only' }), true);
});

test('hide TEST keeps Chen demo case visible', () => {
  const demoCase = caseRow({
    case_id: 'case_chen',
    workbench_test: true,
    demo_name: 'chen_known_customer_demo',
    known_facts: { qa_label: '演示·陈明' },
  });
  const noise = caseRow({ case_id: 'case_noise', workbench_test: true });
  assert.equal(isChenDemoCase(demoCase), true);
  assert.equal(matchesWorkbenchFilters(demoCase, { status: 'all', testFilter: 'hide' }), true);
  assert.equal(matchesWorkbenchFilters(noise, { status: 'all', testFilter: 'hide' }), false);
});

test('production default hides TEST; qa/local show', () => {
  assert.equal(defaultTestFilterForEnv('production'), 'hide');
  assert.equal(defaultTestFilterForEnv('qa'), 'show');
  assert.equal(defaultTestFilterForEnv('local'), 'show');
});

test('relative updated label', () => {
  const now = Date.parse('2026-07-23T12:00:00Z');
  assert.equal(formatRelativeUpdated('2026-07-23T11:59:30Z', now), '刚刚');
  assert.equal(formatRelativeUpdated('2026-07-23T11:50:00Z', now), '10分钟前');
});
