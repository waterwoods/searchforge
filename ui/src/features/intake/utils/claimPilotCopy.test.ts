/**
 * P27-B2 — frozen claim pilot vocabulary.
 * Run: npx tsx ui/src/features/intake/utils/claimPilotCopy.test.ts
 */
import assert from 'node:assert/strict';
import {
  CLAIM_PILOT_STATUS,
  CLAIM_REQUEST_MORE_COPY,
  claimRequestMoreBlockedMessage,
  normalizeClaimPilotStatus,
} from './claimPilotCopy.ts';

assert.equal(CLAIM_PILOT_STATUS.waitingCustomer, '等待客户');
assert.equal(CLAIM_PILOT_STATUS.waitingBroker, '等待经纪人');
assert.equal(CLAIM_PILOT_STATUS.officeProcessing, '办公室处理中');
assert.equal(CLAIM_PILOT_STATUS.completed, '已完成');
assert.equal(CLAIM_PILOT_STATUS.needMaterials, '需补充材料');

assert.equal(normalizeClaimPilotStatus('Waiting for customer'), CLAIM_PILOT_STATUS.waitingCustomer);
assert.equal(normalizeClaimPilotStatus('Customer is working'), CLAIM_PILOT_STATUS.waitingCustomer);
assert.equal(normalizeClaimPilotStatus('办公室处理中'), CLAIM_PILOT_STATUS.officeProcessing);
assert.equal(normalizeClaimPilotStatus('Ready for Review'), CLAIM_PILOT_STATUS.waitingBroker);
assert.equal(normalizeClaimPilotStatus('等待审核'), CLAIM_PILOT_STATUS.waitingBroker);
assert.equal(normalizeClaimPilotStatus('已完成'), CLAIM_PILOT_STATUS.completed);
assert.equal(normalizeClaimPilotStatus('需补充'), CLAIM_PILOT_STATUS.needMaterials);
assert.equal(normalizeClaimPilotStatus('Claim · Request More'), CLAIM_PILOT_STATUS.waitingCustomer);
assert.equal(normalizeClaimPilotStatus('Claim · Broker Review'), CLAIM_PILOT_STATUS.waitingBroker);
assert.equal(normalizeClaimPilotStatus(''), null);
assert.equal(normalizeClaimPilotStatus('random status'), null);

assert.match(claimRequestMoreBlockedMessage('illegal_state'), /不能发出补充请求/);
assert.match(claimRequestMoreBlockedMessage('open_request_exists'), /进行中的补充请求/);
assert.equal(CLAIM_REQUEST_MORE_COPY.sendButton, '发出补充请求');
assert.equal(CLAIM_REQUEST_MORE_COPY.waitingCustomerTitle, '等待客户');
assert.equal(CLAIM_REQUEST_MORE_COPY.waitingBrokerTitle, '等待经纪人');

console.log('claimPilotCopy.test: PASS');
