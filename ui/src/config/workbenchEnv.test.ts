/**
 * Workbench env SSOT — Founder QA document-intake alignment.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/config/workbenchEnv.test.ts
 */
import assert from 'node:assert/strict';
import {
  CLOUD_QA_API_BASE_URL,
  PRODUCTION_API_BASE_URL,
} from '../api/cloudBackendUrls.ts';
import {
  DOCUMENT_INTAKE_PATH,
  WORKBENCH_PRODUCTION_DOCUMENT_INTAKE_URL,
  WORKBENCH_QA_DOCUMENT_INTAKE_URL,
  WORKBENCH_QA_HOST,
  isCloudQaWorkbenchClient,
  resolveWorkbenchClientEnv,
  workbenchApiProfileLabel,
} from './workbenchEnv.ts';

assert.equal(DOCUMENT_INTAKE_PATH, '/workbench/document-intake');
assert.equal(
  WORKBENCH_QA_DOCUMENT_INTAKE_URL,
  `${WORKBENCH_QA_HOST}/workbench/document-intake`,
);
assert.match(WORKBENCH_QA_DOCUMENT_INTAKE_URL, /document-intake/);
assert.equal(WORKBENCH_QA_DOCUMENT_INTAKE_URL.includes('unified-intake'), false);
assert.equal(WORKBENCH_QA_DOCUMENT_INTAKE_URL.includes('smoky-beta'), false);
assert.match(WORKBENCH_PRODUCTION_DOCUMENT_INTAKE_URL, /ui-smoky-beta/);
assert.match(WORKBENCH_PRODUCTION_DOCUMENT_INTAKE_URL, /document-intake/);

assert.equal(resolveWorkbenchClientEnv(CLOUD_QA_API_BASE_URL), 'qa');
assert.equal(resolveWorkbenchClientEnv(PRODUCTION_API_BASE_URL), 'production');
assert.equal(resolveWorkbenchClientEnv(''), 'local');
assert.equal(isCloudQaWorkbenchClient(CLOUD_QA_API_BASE_URL), true);
assert.equal(isCloudQaWorkbenchClient(PRODUCTION_API_BASE_URL), false);
assert.equal(workbenchApiProfileLabel(CLOUD_QA_API_BASE_URL), 'fiqa-api-qa');
assert.equal(workbenchApiProfileLabel(PRODUCTION_API_BASE_URL), 'fiqa-api');

console.log('workbenchEnv.test.ts: PASS');
