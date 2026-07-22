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

test('document-intake exposes short Case ID column and full detail copy', () => {
  const page = readFileSync(
    join(here, '../../../pages/DocumentIntakeInboxPage.tsx'),
    'utf8',
  );
  assert.match(page, /title:\s*'Case ID'/);
  assert.match(page, /shortCaseId/);
  assert.match(page, /CaseIdMeta/);
  assert.match(page, /mode:\s*'row'\s*\|\s*'detail'/);
  assert.match(page, /mode="detail"/);
  assert.match(page, /Copy Case ID|Case ID copied|Copy \$\{full\}|aria-label=\{`Copy Case ID/);
  assert.match(page, /copyToClipboard\(full\)/);
  // Must not expose resume tokens / person_link in the Case ID UI helper.
  assert.doesNotMatch(page, /resume_token|person_link_key|mp_prototype_resume/);
});
