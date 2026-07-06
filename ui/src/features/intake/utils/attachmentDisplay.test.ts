/**
 * P19B attachment display helpers — unit tests (node).
 * Run: node --experimental-strip-types ui/src/features/intake/utils/attachmentDisplay.test.mjs
 * Or: npx tsx ui/src/features/intake/utils/attachmentDisplay.test.ts
 */
import assert from 'node:assert/strict';
import {
  countCaseAttachments,
  guardrailStatusLabel,
  humanizeDocumentType,
  isImageAttachment,
  isQuarantinedAttachment,
  isWeComMediaIntakeLane,
  ocrStatusLabel,
  partitionAttachments,
} from './attachmentDisplay.ts';

assert.equal(humanizeDocumentType('unknown_document'), 'Unknown document');
assert.equal(humanizeDocumentType('vin_photo'), 'VIN photo');
assert.equal(ocrStatusLabel('not_started'), 'OCR: not started');
assert.equal(isWeComMediaIntakeLane('wecom_media_intake'), true);
assert.equal(isWeComMediaIntakeLane('add_car'), false);
assert.equal(countCaseAttachments([]), 0);
assert.equal(countCaseAttachments([{ attachment_id: 'a' }]), 1);
assert.equal(
  countCaseAttachments([
    { attachment_id: 'a', intake_status: 'promoted' },
    { attachment_id: 'b', intake_status: 'quarantined' },
  ]),
  1,
);
assert.equal(isQuarantinedAttachment({ intake_status: 'quarantined' }), true);
assert.equal(isQuarantinedAttachment({ intake_status: 'promoted' }), false);
assert.equal(guardrailStatusLabel('bulk_upload_paused'), 'Bulk upload paused');
assert.equal(guardrailStatusLabel('accepted'), null);
const parts = partitionAttachments([
  { attachment_id: 'p', intake_status: 'promoted' },
  { attachment_id: 'q', intake_status: 'quarantined' },
]);
assert.equal(parts.promoted.length, 1);
assert.equal(parts.quarantined.length, 1);
assert.equal(isImageAttachment({ mime_type: 'image/jpeg' }), true);
assert.equal(isImageAttachment({ mime_type: 'application/pdf' }), false);

console.log('attachmentDisplay.test: PASS');
