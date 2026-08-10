/**
 * P1 UX polish — ClaimCaseBriefPanel scan contract (source inspection).
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/ClaimCaseBriefPanel.scanOrder.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, 'ClaimCaseBriefPanel.tsx'), 'utf8');

assert.match(src, /title="案件摘要"/);
assert.match(src, /案件摘要暂未生成/);
assert.doesNotMatch(src, /理赔结论/);

const nextIdx = src.indexOf('data-testid="claim-brief-next-action"');
const layersIdx = src.indexOf('data-testid="accident-story-assistant-layers"');
const factsMarker = src.indexOf('已收 {photoCount} 张');
const ackIdx = src.indexOf('data-testid="supplement-review-ack-banner"');
const acceptIdx = src.indexOf('data-testid="office-materials-accept-banner"');

assert.ok(nextIdx > 0, 'expected claim-brief-next-action marker');
assert.ok(layersIdx > 0, 'expected accident-story-assistant-layers');
assert.ok(factsMarker > 0, 'expected facts grid photo line');

// Banners stay above or adjacent to next action; next action before AI layers + facts.
assert.ok(ackIdx > 0 && ackIdx < nextIdx, 'supplement ack banner before 下一步');
assert.ok(acceptIdx > 0 && acceptIdx < nextIdx, 'office accept banner before 下一步');
assert.ok(nextIdx < layersIdx, '下一步 must appear before AI layers');
assert.ok(nextIdx < factsMarker, '下一步 must appear before fact grid');

// Layers / provenance still present.
assert.match(src, /客户原始描述/);
assert.match(src, /AI整理草稿/);
assert.match(src, /客户已确认事实/);

console.log('ClaimCaseBriefPanel.scanOrder.test.ts: PASS');
