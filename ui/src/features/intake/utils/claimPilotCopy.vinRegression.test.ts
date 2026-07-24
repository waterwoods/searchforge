/**
 * P3-B — VIN is optional for Request More send; copy must stay neutral.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import {
  CLAIM_REQUEST_MORE_COPY,
  claimRequestMoreBlockedMessage,
} from './claimPilotCopy.ts';

const here = dirname(fileURLToPath(import.meta.url));

test('select-before-send copy is neutral (not VIN-only)', () => {
  assert.equal(
    CLAIM_REQUEST_MORE_COPY.selectAtLeastOneBeforeSend,
    '请选择至少一项需要客户补充的资料。',
  );
  assert.equal(
    CLAIM_REQUEST_MORE_COPY.selectVinBeforeSend,
    '请选择至少一项需要客户补充的资料。',
  );
  assert.doesNotMatch(CLAIM_REQUEST_MORE_COPY.selectAtLeastOneBeforeSend, /VIN/);
  assert.doesNotMatch(CLAIM_REQUEST_MORE_COPY.waitingDraftSave, /勾选 VIN/);
});

test('empty draft error no longer requires VIN specifically', () => {
  const msg = claimRequestMoreBlockedMessage('request_draft_empty');
  assert.equal(msg, '请选择至少一项需要客户补充的资料。');
  assert.doesNotMatch(msg, /VIN/);
});

test('MissingInformationChecklistPanel uses selectAtLeastOneBeforeSend', () => {
  const panel = readFileSync(
    join(here, '../components/MissingInformationChecklistPanel.tsx'),
    'utf8',
  );
  assert.match(panel, /selectAtLeastOneBeforeSend/);
  assert.doesNotMatch(panel, /Please select VIN before sending/i);
});
