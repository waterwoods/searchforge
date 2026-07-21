/**
 * P36 T5 — Vercel / Founder Console API base URL routing guards.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/api/cloudBackendUrls.test.ts
 */
import assert from 'node:assert/strict';
import {
  CLOUD_QA_API_BASE_URL,
  PRODUCTION_API_BASE_URL,
  assertVercelApiBaseUrl,
  normalizeApiBaseUrl,
} from './cloudBackendUrls.ts';

assert.equal(CLOUD_QA_API_BASE_URL, 'https://fiqa-api-qa-g7zatxrycq-uw.a.run.app');
assert.equal(PRODUCTION_API_BASE_URL, 'https://fiqa-api-g7zatxrycq-uw.a.run.app');
assert.notEqual(CLOUD_QA_API_BASE_URL, PRODUCTION_API_BASE_URL);

// Preview → Cloud QA
{
  const r = assertVercelApiBaseUrl({
    vercel: true,
    mode: 'production',
    vercelEnv: 'preview',
    rawBaseUrl: CLOUD_QA_API_BASE_URL,
  });
  assert.equal(r.ok, true);
  if (r.ok) assert.equal(r.url, CLOUD_QA_API_BASE_URL);
}

// Preview missing URL fails visibly (no Production fallback)
{
  const r = assertVercelApiBaseUrl({
    vercel: true,
    mode: 'production',
    vercelEnv: 'preview',
    rawBaseUrl: '',
  });
  assert.equal(r.ok, false);
  if (!r.ok) {
    assert.match(r.error, /required for Vercel Preview/i);
    assert.match(r.error, /fiqa-api-qa/);
  }
}

// Preview must not use Production
{
  const r = assertVercelApiBaseUrl({
    vercel: true,
    mode: 'production',
    vercelEnv: 'preview',
    rawBaseUrl: PRODUCTION_API_BASE_URL,
  });
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.error, /must not use Production/i);
}

// Production stays on Production URL
{
  const r = assertVercelApiBaseUrl({
    vercel: true,
    mode: 'production',
    vercelEnv: 'production',
    rawBaseUrl: PRODUCTION_API_BASE_URL,
  });
  assert.equal(r.ok, true);
}

// Production must not use Cloud QA
{
  const r = assertVercelApiBaseUrl({
    vercel: true,
    mode: 'production',
    vercelEnv: 'production',
    rawBaseUrl: CLOUD_QA_API_BASE_URL,
  });
  assert.equal(r.ok, false);
  if (!r.ok) assert.match(r.error, /must not use Cloud QA/i);
}

// Trailing slash normalized in success path
assert.equal(
  normalizeApiBaseUrl(`${CLOUD_QA_API_BASE_URL}/`),
  CLOUD_QA_API_BASE_URL,
);

console.log('cloudBackendUrls.test.ts: PASS');
