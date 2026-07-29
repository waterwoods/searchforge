/**
 * Chen Demo Invite panel — static contract tests (T3).
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/api/demoInvite.entryPayload.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  DEMO_INVITE_QR_BLOCKER,
  DEMO_INVITE_T4_REQUIRED,
  buildDemoInviteEntryPayload,
  maskDemoInviteToken,
  type DemoInviteIssued,
} from './demoInvite';

const here = dirname(fileURLToPath(import.meta.url));

const sample: DemoInviteIssued = {
  invite_id: 'dinv_abc123',
  token: 'di_abcdefghijklmnopqrstuvwxyz0123456789',
  office_id: 'chen_kui',
  scenario_id: 'chen_camry',
  mock_scenario: 'S3',
  demo_name: 'chen_known_customer_demo',
  is_demo: true,
  created_at: 1_700_000_000,
  expires_at: 1_700_014_400,
  customer_display_name: '陈明',
  vehicle_summary: '2020 Toyota Camry',
};

const entry = buildDemoInviteEntryPayload(sample);
assert.equal(entry.kind, 'chen_demo_invite');
assert.equal(entry.mini_program_path, 'pages/start-claim/start-claim');
assert.equal(entry.qr_supported, false);
assert.match(entry.launch_path_with_query, /^pages\/start-claim\/start-claim\?dit=/);
assert.ok(!entry.launch_path_with_query.includes('openid'));
assert.ok(!entry.launch_path_with_query.includes('陈明'));
assert.ok(entry.qr_blocker.includes('wxacode') || entry.qr_blocker === DEMO_INVITE_QR_BLOCKER);
assert.ok(entry.t4_required.includes('redeem') || entry.t4_required === DEMO_INVITE_T4_REQUIRED);
assert.match(maskDemoInviteToken(sample.token), /^di_/);
assert.ok(maskDemoInviteToken(sample.token).includes('…'));
assert.ok(!maskDemoInviteToken(sample.token).includes(sample.token));

const panel = readFileSync(
  join(here, '../features/intake/components/ChenDemoInvitePanel.tsx'),
  'utf8',
);
assert.match(panel, /陈总演示工具/);
assert.match(panel, /演示数据/);
assert.match(panel, /生成演示入口/);
assert.match(panel, /重置演示/);
assert.match(panel, /Active Case/);
assert.match(panel, /isChenDemoInviteUiEnabled/);
assert.doesNotMatch(panel, /QRCode/);
assert.doesNotMatch(panel, /openid/i);

const page = readFileSync(join(here, '../pages/DocumentIntakeInboxPage.tsx'), 'utf8');
assert.match(page, /ChenDemoInvitePanel/);

const surface = readFileSync(join(here, '../config/productSurface.ts'), 'utf8');
assert.match(surface, /isChenDemoInviteUiEnabled/);
assert.match(surface, /VITE_DISABLE_CHEN_DEMO_INVITE/);

console.log('demoInvite.entryPayload.test.ts: PASS');
