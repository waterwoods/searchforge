/**
 * P19H-3a claim workbench display helpers — unit tests (node).
 * Run: npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts
 */
import assert from 'node:assert/strict';
import type { SavedCase } from '@/api/inboxTriage';
import {
  buildClaimListSummary,
  claimDisplayStatus,
  claimLaneLabel,
  isClaimGuidedCase,
  isClaimGuidedLane,
  resolveClaimSummary,
} from './claimWorkbenchDisplay.ts';

const claimCase = {
  service_lane: 'claim',
  display_status: 'Claim Step 1 complete · Accident basics received',
  claim_summary: {
    accident_datetime: '今天上午10点',
    accident_location: 'Irvine Blvd 和 Culver 附近',
    accident_description: '对方变道刮到我左前门',
  },
} as SavedCase;

assert.equal(isClaimGuidedLane('claim'), true);
assert.equal(isClaimGuidedLane('claim_lite'), false);
assert.equal(isClaimGuidedLane('add_car'), false);
assert.equal(isClaimGuidedCase(claimCase), true);
assert.equal(claimLaneLabel(), 'Claim');

const summary = resolveClaimSummary(claimCase);
assert.equal(summary.accident_datetime, '今天上午10点');
assert.equal(summary.accident_location, 'Irvine Blvd 和 Culver 附近');
assert.equal(summary.accident_description, '对方变道刮到我左前门');

assert.equal(
  buildClaimListSummary(claimCase),
  '今天上午10点 · Irvine Blvd 和 Culver 附近 · 对方变道刮到我左前门',
);
assert.equal(
  claimDisplayStatus(claimCase),
  'Claim Step 1 complete · Accident basics received',
);
assert.ok(!claimDisplayStatus(claimCase).toLowerCase().includes('claim filed'));

const addCar = { service_lane: 'add_car', primary_vehicle_summary: '2024 Tesla Model 3' } as SavedCase;
assert.equal(isClaimGuidedCase(addCar), false);

console.log('claimWorkbenchDisplay.test: PASS');
