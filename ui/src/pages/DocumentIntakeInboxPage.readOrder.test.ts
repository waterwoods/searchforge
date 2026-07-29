/**
 * P3.7 — Claim detail read-order contract (source inspection).
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/pages/DocumentIntakeInboxPage.readOrder.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'DocumentIntakeInboxPage.tsx'), 'utf8');

/** Extract the !hasFullPacket claim detail return block (primary Mini Program claim path). */
const noPacketStart = src.indexOf('if (!hasFullPacket)');
assert.ok(noPacketStart > 0, 'expected !hasFullPacket branch');
const noPacketBlock = src.slice(noPacketStart, src.indexOf('const pkt = blob!', noPacketStart));

const markers = [
  'BrokerHeader',
  'ClaimCaseBriefPanel',
  'MissingInformationChecklistPanel',
  'ClaimAccidentBasicsCard',
  'ClaimEvidenceChecklist',
  'CaseAttachmentsPanel',
  'CloseCaseButton',
  '删除测试案件',
] as const;

let cursor = -1;
for (const marker of markers) {
  const idx = noPacketBlock.indexOf(marker);
  assert.ok(idx >= 0, `missing marker in !hasFullPacket branch: ${marker}`);
  assert.ok(
    idx > cursor,
    `read-order violation: ${marker} should appear after prior section (idx=${idx}, cursor=${cursor})`,
  );
  cursor = idx;
}

// Close Case must not appear before the claim brief in the no-packet path.
const closeIdx = noPacketBlock.indexOf('<CloseCaseButton');
const briefIdx = noPacketBlock.indexOf('<ClaimCaseBriefPanel');
const requestIdx = noPacketBlock.indexOf('<MissingInformationChecklistPanel');
assert.ok(briefIdx >= 0 && requestIdx >= 0 && closeIdx >= 0);
assert.ok(briefIdx < requestIdx, 'Claim brief must precede Request More');
assert.ok(requestIdx < closeIdx, 'Request More must precede Close Case');

console.log('DocumentIntakeInboxPage.readOrder.test.ts: PASS');
