/**
 * P20 MVP request gating helpers.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/mvpRequestTypes.test.ts
 */
import assert from 'node:assert/strict';
import {
  brokerSendBlockedMessage,
  formatUnsupportedSendItems,
  isMvpSendableItemType,
} from './mvpRequestTypes';

assert.equal(isMvpSendableItemType('vin'), true);
assert.equal(isMvpSendableItemType('vehicle_information'), true);
assert.equal(isMvpSendableItemType('policy_or_insurance_card'), true);
assert.equal(isMvpSendableItemType('free_text'), false);
assert.equal(isMvpSendableItemType('photo_evidence'), false);

assert.match(
  formatUnsupportedSendItems(['Vehicle year / make / model']),
  /Vehicle year \/ make \/ model/,
);

assert.match(
  brokerSendBlockedMessage('unsupported_draft_item_type_for_send', ['Policy / insurance card']),
  /Policy \/ insurance card/,
);

assert.match(brokerSendBlockedMessage('illegal_state'), /不能发出补充请求/);

console.log('mvpRequestTypes.test: PASS');
