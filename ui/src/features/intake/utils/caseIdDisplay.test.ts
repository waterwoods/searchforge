/**
 * Founder QA Case ID visibility helpers + document-intake wiring smoke.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

import { fullCaseId, shortCaseId } from './caseIdDisplay.ts';

const here = dirname(fileURLToPath(import.meta.url));

test('shortCaseId strips case_ prefix and truncates to 8 chars', () => {
  assert.equal(shortCaseId('case_92da6e0bcfce'), '92da6e0b');
  assert.equal(shortCaseId('case_abcdef12zzzz'), 'abcdef12');
  assert.equal(shortCaseId('short'), 'short');
  assert.equal(shortCaseId(''), '');
  assert.equal(shortCaseId(null), '');
});

test('fullCaseId returns exact trimmed id', () => {
  assert.equal(fullCaseId('  case_92da6e0bcfce  '), 'case_92da6e0bcfce');
  assert.equal(fullCaseId(undefined), '');
});

test('document-intake freeze: list has no identifiers; detail keeps internal Case ID copy', () => {
  const page = readFileSync(
    join(here, '../../../pages/DocumentIntakeInboxPage.tsx'),
    'utf8',
  );
  assert.match(page, /InternalCaseIdMeta/);
  assert.match(page, /title:\s*'客户'/);
  assert.match(page, /title:\s*'车辆'/);
  assert.match(page, /title:\s*'下一步'/);
  assert.match(page, /title:\s*'更新'/);
  assert.match(page, /title:\s*'打开'/);
  assert.match(page, /内部 Case ID/);
  assert.match(page, /Copy Case ID|已复制内部 Case ID|aria-label=\{`Copy Case ID/);
  assert.match(page, /copyToClipboard\(full\)/);
  // Frozen: no Case Number / Case ID / Lane columns on the main list.
  assert.doesNotMatch(page, /title:\s*'案件'/);
  assert.doesNotMatch(page, /title:\s*'Case ID'/);
  assert.doesNotMatch(page, /title:\s*'Lane'/);
  assert.doesNotMatch(page, /mode:\s*'row'/);
  assert.doesNotMatch(page, /案件编号/);
  assert.doesNotMatch(page, /CLM-####/);
  // Must not expose resume tokens / person_link in the Case ID UI helper.
  assert.doesNotMatch(page, /resume_token|person_link_key|mp_prototype_resume/);
});
