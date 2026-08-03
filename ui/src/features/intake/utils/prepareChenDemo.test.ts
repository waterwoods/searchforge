/**
 * QA Fast Lane V1 — Prepare Demo orchestration contracts.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/utils/prepareChenDemo.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import {
  CLOUD_QA_API_BASE_URL,
  PRODUCTION_API_BASE_URL,
} from '@/api/cloudBackendUrls';
import type { DemoInviteIssued, DemoInviteValidateResult } from '@/api/demoInvite';
import {
  assertPrepareDemoCloudQa,
  evaluateInvitePreparePass,
  prepareChenDemo,
  type PrepareDemoDeps,
} from './prepareChenDemo.ts';

const here = dirname(fileURLToPath(import.meta.url));
const SESSION = 'wx_08af8e4deadbeef01';

function issued(partial: Partial<DemoInviteIssued> = {}): DemoInviteIssued {
  return {
    invite_id: 'dinv_test1',
    token: 'di_abcdefghijklmnopqrstuvwxyz0123456789',
    office_id: 'chen_kui',
    scenario_id: 'chen_camry',
    mock_scenario: 'S3',
    demo_name: 'chen_known_customer_demo',
    is_demo: true,
    created_at: 1_700_000_000,
    expires_at: 1_700_014_400,
    use_count: 0,
    customer_display_name: '陈明',
    vehicle_summary: '2020 Toyota Camry',
    ...partial,
  };
}

function activeValidation(
  scenarioId = 'chen_camry',
  useCount = 0,
  expiresAt = 1_700_014_400,
): DemoInviteValidateResult {
  return {
    ok: true,
    status: 'active',
    invite: {
      invite_id: 'dinv_test1',
      office_id: 'chen_kui',
      scenario_id: scenarioId,
      expires_at: expiresAt,
      revoked: false,
      use_count: useCount,
    },
  };
}

function makeDeps(order: string[], overrides: Partial<PrepareDemoDeps> = {}): PrepareDemoDeps {
  return {
    runFresh: async () => {
      order.push('fresh');
      return { ok: true };
    },
    resetOffice: async () => {
      order.push('reset');
    },
    resetOverlay: async () => {
      order.push('overlay');
    },
    issueInvite: async () => {
      order.push('issue');
      return issued();
    },
    validateInvite: async () => {
      order.push('validate');
      return activeValidation();
    },
    nowSec: () => 1_700_000_100,
    ...overrides,
  };
}

test('correct reset → issue → validate order (Fresh before office reset before issue)', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'PASS');
  assert.deepEqual(order, ['fresh', 'reset', 'overlay', 'issue', 'validate']);
  assert.deepEqual(res.steps, [
    'gate_api',
    'require_session',
    'clear_previous',
    'p35_fresh',
    'office_reset',
    'issue',
    'validate',
    'done',
  ]);
  assert.equal(res.lockResetAndReprepare, true);
  assert.ok(res.entry?.launch_path_with_query.includes('dit='));
});

test('invite never issued before Fresh completes', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order, {
      runFresh: async () => {
        order.push('fresh');
        throw new Error('fresh_boom');
      },
    }),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.equal(res.error, 'fresh_boom');
  assert.ok(!order.includes('issue'));
  assert.ok(!order.includes('validate'));
  assert.ok(!order.includes('reset'));
});

test('reset disabled after a valid invite (lock flag)', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'PASS');
  assert.equal(res.lockResetAndReprepare, true);
});

test('Production API hard-blocked', async () => {
  assert.ok(assertPrepareDemoCloudQa(PRODUCTION_API_BASE_URL));
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: PRODUCTION_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.match(String(res.error), /Production|硬阻断/);
  assert.deepEqual(order, []);
});

test('unknown / non-QA API hard-blocked', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: 'https://evil.example.com',
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.deepEqual(order, []);
});

test('failed validation never displays PASS', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order, {
      validateInvite: async () => ({
        ok: false,
        status: 'revoked',
        invite: {
          invite_id: 'dinv_test1',
          office_id: 'chen_kui',
          scenario_id: 'chen_camry',
          expires_at: 1_700_014_400,
          revoked: true,
          use_count: 0,
        },
      }),
    }),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.equal(res.lockResetAndReprepare, false);
  assert.match(String(res.error), /invite_validation_failed/);
  assert.equal(
    evaluateInvitePreparePass({
      issued: issued(),
      validation: { ok: false, status: 'expired' },
      expectedScenarioId: 'chen_camry',
      nowSec: 1_700_000_100,
    }).pass,
    false,
  );
});

test('previous invite/path removed when preparing a new run (clear_previous step)', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.ok(res.steps.includes('clear_previous'));
  assert.ok(res.steps.indexOf('clear_previous') < res.steps.indexOf('p35_fresh'));
  assert.ok(res.steps.indexOf('clear_previous') < res.steps.indexOf('issue'));
});

test('duplicate button clicks do not create competing active runs', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: SESSION,
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
      busy: true,
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.equal(res.error, 'prepare_already_running');
  assert.deepEqual(order, []);
});

test('missing session refuses before Fresh / issue', async () => {
  const order: string[] = [];
  const res = await prepareChenDemo(
    {
      apiBaseUrl: CLOUD_QA_API_BASE_URL,
      sessionId: '',
      scenarioId: 'chen_camry',
      officeId: 'chen_kui',
    },
    makeDeps(order),
  );
  assert.equal(res.verdict, 'FAIL');
  assert.match(String(res.error), /session_id/);
  assert.deepEqual(order, []);
});

test('panel exposes one-click Prepare Demo surface', () => {
  const panel = readFileSync(join(here, '../components/ChenDemoInvitePanel.tsx'), 'utf8');
  assert.match(panel, /一键准备演示/);
  assert.match(panel, /prepareChenDemo/);
  assert.match(panel, /删除旧的 DevTools 编译模式|旧的.*编译模式/);
  assert.match(panel, /不要在邀请创建后重置|邀请创建后请勿重置/);
  assert.doesNotMatch(panel, /QRCode/);
  assert.match(panel, /runP35FreshForDemo|runFresh/);
});

console.log('prepareChenDemo.test.ts: PASS');
