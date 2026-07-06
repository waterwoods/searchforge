/**
 * P19D-2 — H5 page static contract checks (no jsdom).
 * Run: node ui/src/pages/h5SingleSlotUpload.static.test.mjs
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const dir = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(dir, 'H5SingleSlotUploadPage.tsx'), 'utf8');

assert.match(src, /multiple=\{false\}/, 'file input must disallow multi-select');
assert.match(src, /capture="environment"/, 'file input should encourage camera');
assert.match(src, /确认提交/, 'preview confirm submit button required');
assert.match(src, /重新选择/, 'reselect button required');
assert.match(src, /VIN 照片已收到/, 'success copy required');
assert.match(src, /无法打开任务/, 'expired/error state required');
assert.match(src, /第 \{task\.step_current\} 步/, 'step progress required');
assert.doesNotMatch(src, /multiple=\{true\}/, 'no multi-image UI');
assert.doesNotMatch(src, /已识别|OCR 已完成|加车已完成/, 'no OCR/completion claims');

console.log('h5SingleSlotUpload.static.test: PASS');
