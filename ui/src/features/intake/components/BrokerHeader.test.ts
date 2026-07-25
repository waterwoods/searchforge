/**
 * P3-C Slice 1 — BrokerHeader field resolution (reuse findability projection).
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/BrokerHeader.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { SavedCase } from '@/api/inboxTriage';
import { resolveBrokerHeaderFields } from './BrokerHeader.tsx';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'BrokerHeader.tsx'), 'utf8');

assert.match(src, /broker-header/);
assert.match(src, /resolveFindabilityCustomerName/);
assert.match(src, /resolveVehicleContext/);
assert.match(src, /resolveCurrentActionLabel/);
assert.match(src, /data-testid="broker-header"/);

function caseRow(partial: Partial<SavedCase> & { workbench_list?: Record<string, unknown> }): SavedCase {
  return {
    case_id: 'case_p3c_header',
    ...partial,
  } as SavedCase;
}

test('prefers workbench_list projection for all three fields', () => {
  const fields = resolveBrokerHeaderFields(
    caseRow({
      customer_name: 'Fallback Name',
      primary_vehicle_summary: 'Fallback Vehicle',
      workbench_list: {
        customer_display_name: 'Andy Li',
        vehicle_summary: '2021 Toyota Camry',
        broker_next_action_label: '等待客户补充资料',
      },
    }),
  );
  assert.equal(fields.customerDisplayName, 'Andy Li');
  assert.equal(fields.vehicleSummary, '2021 Toyota Camry');
  assert.equal(fields.currentNextAction, '等待客户补充资料');
});

test('vehicle missing shows em dash', () => {
  const fields = resolveBrokerHeaderFields(
    caseRow({
      workbench_list: {
        customer_display_name: '陈明',
        vehicle_summary: '',
        broker_next_action_label: '等待审核',
      },
    }),
  );
  assert.equal(fields.vehicleSummary, '—');
  assert.equal(fields.customerDisplayName, '陈明');
  assert.equal(fields.currentNextAction, '等待审核');
});

test('customer name falls back to existing server projection path', () => {
  const fields = resolveBrokerHeaderFields(
    caseRow({
      customer_name: '陈明',
      workbench_list: {
        vehicle_summary: '2021 Toyota Camry',
        broker_next_action_label: '打开核对',
      },
    }),
  );
  assert.equal(fields.customerDisplayName, '陈明');
  assert.equal(fields.vehicleSummary, '2021 Toyota Camry');
});

console.log('BrokerHeader.test.ts: PASS');

function test(name: string, fn: () => void): void {
  fn();
  console.log(`  ✓ ${name}`);
}
