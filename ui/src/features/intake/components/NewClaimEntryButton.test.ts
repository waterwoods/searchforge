/**
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/NewClaimEntryButton.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'NewClaimEntryButton.tsx'), 'utf8');

assert.match(src, /Create Test Case/);
assert.match(src, /isQaToolsEnabled/);
assert.doesNotMatch(src, />\s*New Claim\s*</);
assert.match(src, /create-test-case-button/);

console.log('NewClaimEntryButton.test.ts: PASS');
