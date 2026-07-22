/**
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/utils/caseLifecycle.test.ts
 */
import assert from 'node:assert/strict';
import { isCaseClosedHistory } from './caseLifecycle.ts';

assert.equal(isCaseClosedHistory(null), false);
assert.equal(isCaseClosedHistory({ case_status: 'reviewing' }), false);
assert.equal(isCaseClosedHistory({ workbench_archived: true, case_status: 'reviewing' }), false);
assert.equal(isCaseClosedHistory({ case_status: 'closed' }), true);
assert.equal(isCaseClosedHistory({ case_history_state: 'history' }), true);
assert.equal(isCaseClosedHistory({ closed_at: '2026-07-22T00:00:00Z' }), true);
assert.equal(isCaseClosedHistory({ admin_lifecycle: 'closed' }), true);

console.log('caseLifecycle.test.ts: PASS');
