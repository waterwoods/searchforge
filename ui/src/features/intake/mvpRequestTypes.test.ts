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
assert.equal(isMvpSendableItemType('free_text'), false);
assert.equal(isMvpSendableItemType('policy_or_insurance_card'), false);

assert.match(
  formatUnsupportedSendItems(['Vehicle year / make / model']),
  /Vehicle year \/ make \/ model/,
);

assert.match(
  brokerSendBlockedMessage('unsupported_draft_item_type_for_send', ['Policy / insurance card']),
  /Policy \/ insurance card/,
);

console.log('mvpRequestTypes.test: PASS');
