/**
 * Broker-open instrumentation contract — unit tests (node).
 * Run: npx tsx ui/src/features/intake/utils/brokerCaseOpenInstrumentation.test.ts
 */
import assert from 'node:assert/strict';
import {
  BROKER_FIRST_OPEN_ACTIVITY_PATH,
  BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE,
  notifyBrokerCaseDetailRendered,
  planBrokerCaseOpenInstrumentation,
} from './brokerCaseOpenInstrumentation.ts';

async function main(): Promise<void> {
  const claim = planBrokerCaseOpenInstrumentation({ service_lane: 'claim' });
  assert.equal(claim.fetchesFormalCaseDetail, true);
  assert.equal(claim.postsBrokerFirstOpenedActivity, true);
  assert.equal(claim.instrumentationSurface, BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE);
  assert.match(claim.notes, /POST activity\/broker-first-opened/);
  assert.match(claim.notes, /Generic GET never stamps/);
  assert.match(BROKER_FIRST_OPEN_ACTIVITY_PATH, /activity\/broker-first-opened/);

  const wecom = planBrokerCaseOpenInstrumentation({ service_lane: 'wecom_media_intake' });
  assert.equal(wecom.fetchesFormalCaseDetail, false);
  assert.equal(wecom.postsBrokerFirstOpenedActivity, false);

  let called = 0;
  await notifyBrokerCaseDetailRendered('case_abc', async () => {
    called += 1;
  });
  assert.equal(called, 1);

  await notifyBrokerCaseDetailRendered('', async () => {
    called += 1;
  });
  assert.equal(called, 1);

  await notifyBrokerCaseDetailRendered('case_abc', async () => {
    throw new Error('network');
  });
  assert.equal(called, 1);

  console.log('brokerCaseOpenInstrumentation.test: PASS');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
