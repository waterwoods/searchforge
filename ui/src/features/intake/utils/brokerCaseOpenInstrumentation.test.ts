/**
 * Broker-open instrumentation contract — unit tests (node).
 * Run: npx tsx ui/src/features/intake/utils/brokerCaseOpenInstrumentation.test.ts
 */
import assert from 'node:assert/strict';
import {
  BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE,
  planBrokerCaseOpenInstrumentation,
} from './brokerCaseOpenInstrumentation.ts';

const claim = planBrokerCaseOpenInstrumentation({ service_lane: 'claim' });
assert.equal(claim.fetchesFormalCaseDetail, true);
assert.equal(claim.instrumentationSurface, BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE);
assert.match(claim.notes, /broker_first_opened/);

const addCar = planBrokerCaseOpenInstrumentation({ service_lane: 'add_car' });
assert.equal(addCar.fetchesFormalCaseDetail, true);

const wecom = planBrokerCaseOpenInstrumentation({ service_lane: 'wecom_media_intake' });
assert.equal(wecom.fetchesFormalCaseDetail, false);

const missing = planBrokerCaseOpenInstrumentation(null);
assert.equal(missing.fetchesFormalCaseDetail, true);

console.log('brokerCaseOpenInstrumentation.test: PASS');
