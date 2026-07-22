/**
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/CloseCaseButton.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { isCaseClosedHistory } from '../utils/caseLifecycle.ts';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'CloseCaseButton.tsx'), 'utf8');

assert.match(src, /Close Case/);
assert.match(src, /Modal\.confirm/);
assert.match(src, /read-only History/);
assert.match(src, /no longer edit or upload/);
assert.match(src, /closed-history-badge/);
assert.match(src, /close-case-button/);
assert.match(src, /isCaseClosedHistory/);
assert.equal(
  isCaseClosedHistory({ case_status: 'closed', case_history_state: 'history' }),
  true,
);
assert.equal(isCaseClosedHistory({ workbench_archived: true, case_status: 'reviewing' }), false);

console.log('CloseCaseButton.test.ts: PASS');
