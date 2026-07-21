/**
 * P35.2 — Founder QA Console client helpers.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/api/founderQaConsole.test.ts
 */
import assert from 'node:assert/strict';
import { brokerCaseOpenPath, mapFounderQaError } from './founderQaConsole.ts';

assert.equal(
  brokerCaseOpenPath('case_abc'),
  '/workbench/unified-intake?tab=broker&caseId=case_abc',
);

assert.match(mapFounderQaError('selected_identity_required'), /选择/);
assert.match(mapFounderQaError('confirm_fresh_required'), /FRESH/);
assert.match(mapFounderQaError('p35_mp_qa_harness_disabled'), /未启用/);
assert.match(mapFounderQaError('founder_qa_rate_limited'), /频繁/);
assert.match(mapFounderQaError('intake_api_unauthorized'), /未授权/);
assert.match(mapFounderQaError('support_key_not_accepted_on_console'), /Support Key/);
assert.match(mapFounderQaError('seed_claim_failed:x'), /部分失败/);
assert.match(mapFounderQaError('request_more_failed:slice1_not_enabled'), /P20_SLICE1_REQUEST_MORE/);

// Ensure client module source does not embed support-key usage for this console.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'founderQaConsole.ts'), 'utf8');
assert.equal(src.includes('VITE_UNIFIED_INTAKE_SUPPORT_API_KEY'), false);
assert.equal(src.includes('X-Unified-Intake-Support-Key'), false);

console.log('founderQaConsole.test.ts: PASS');
