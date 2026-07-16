/**
 * P20 Capability 3A — H5 claim QR landing static contract checks (no jsdom).
 * Run: node ui/src/pages/h5ClaimIntakeLanding.static.test.mjs
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(dir, 'H5ClaimIntakePage.tsx'), 'utf8');
const landing = readFileSync(
  join(dir, '../features/claim-h5/h5ClaimLanding.ts'),
  'utf8',
);

assert.match(src, /resolveH5ClaimLanding/, 'page must use authoritative landing helper');
assert.match(src, /补充车辆 VIN|landing\.title/, 'VIN / request-item title path required');
assert.match(src, /查看全部资料/, 'secondary overview affordance required');
assert.match(src, /提交给陈总/, 'primary action affordance required');
assert.match(src, /customer_qa_marker|qaMarker|renderQaMarker/, 'QA marker path required');
assert.match(src, /slice1_projection_error|projection_error/, 'projection error retry path required');
assert.match(src, /invalid_or_expired_task_link/, 'expired token path required');
assert.match(src, /setShowOverview\(false\)/, 'refresh must re-land on task (not sticky overview)');
assert.doesNotMatch(
  src,
  /\{info\.case_id\}|\{info\?\.case_id\}/,
  'raw case_id must not be rendered in JSX',
);
assert.doesNotMatch(src, /case_d3187eb826f4/, 'QA case id must not be hardcoded in customer page');

assert.match(landing, /request_item/, 'landing helper must support request-item mode');
assert.match(landing, /projection_error/, 'landing helper must support projection error');
assert.match(landing, /provide_fact/, 'landing helper must key off actionable next action');
assert.match(landing, /TEST · Cap3A VIN QA/, 'QA marker copy required');

console.log('h5ClaimIntakeLanding.static.test: PASS');
