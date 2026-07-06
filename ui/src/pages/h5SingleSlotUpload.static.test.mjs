/**
 * P19D-4B — H5 Add Vehicle photo flow static contract checks (no jsdom).
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
assert.match(src, /照片已收到/, 'flow success copy required');
assert.match(src, /此照片上传流程已完成/, 'completed flow clarity required');
assert.match(src, /重新加车/, 'restart hint required');
assert.match(src, /返回微信/, 'return to WeChat button required');
assert.match(src, /确认消息/, 'confirmation message expectation required');
assert.match(src, /已提交/, 'fallback reply hint required');
assert.match(src, /提车日期/, 'delivery date text field hint required');
assert.match(src, /停放 ZIP/, 'ZIP text field hint required');
assert.match(src, /联系电话/, 'phone text field hint required');
assert.match(src, /跳过此步骤/, 'optional insurance skip button required');
assert.match(src, /第 \$\{current\} 步 \/ 共 \$\{total\} 步/, 'flow step progress required');
assert.match(src, /上传未成功/, 'upload failure alert required');
assert.doesNotMatch(src, /multiple=\{true\}/, 'no multi-image UI');
assert.doesNotMatch(src, /已识别|OCR 已完成|加车已完成/, 'no OCR/completion claims');

console.log('h5SingleSlotUpload.static.test: PASS');
