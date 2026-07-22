/**
 * P0 Founder QA UX — Phase 1 Founder surface view model.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/founderGoldenQaViewModel.test.ts
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
    assertNoFounderEngineeringLeak,
    founderVisibleText,
    FOUNDER_GOLDEN_QA_SUBTITLE,
    FOUNDER_GOLDEN_QA_TASK,
    FOUNDER_GOLDEN_QA_TITLE,
    primaryCtaCount,
    resolveFounderGoldenQaView,
    type FounderGoldenQaState,
} from './founderGoldenQaViewModel.ts';

function viewFor(state: FounderGoldenQaState) {
    switch (state) {
        case 'idle':
            return resolveFounderGoldenQaView({
                api: { status: 'idle', enabled: true },
                busy: false,
                sessionProgress: null,
                hasError: false,
            });
        case 'preparing':
            return resolveFounderGoldenQaView({
                api: { status: 'running_reset', enabled: true },
                busy: true,
                sessionProgress: null,
                hasError: false,
            });
        case 'ready':
            return resolveFounderGoldenQaView({
                api: {
                    ok: true,
                    status: 'ready_to_scan',
                    preview_prepared: true,
                    enabled: true,
                    case_id: 'case_should_not_leak',
                    expires_at: '2099-01-01T00:00:00Z',
                    token_masked: 'abcd…wxyz',
                    devtools_hint: 'DevTools → compile mode',
                },
                busy: false,
                sessionProgress: null,
                hasError: false,
            });
        case 'testing':
            return resolveFounderGoldenQaView({
                api: { ok: true, status: 'ready_to_scan', preview_prepared: true, enabled: true },
                busy: false,
                sessionProgress: 'testing',
                hasError: false,
            });
        case 'verified':
            return resolveFounderGoldenQaView({
                api: { ok: true, status: 'ready_to_scan', preview_prepared: true, enabled: true },
                busy: false,
                sessionProgress: 'verified',
                hasError: false,
            });
        case 'blocked':
            return resolveFounderGoldenQaView({
                api: {
                    ok: true,
                    status: 'ready_to_scan',
                    preview_prepared: false,
                    enabled: true,
                    failure_reason: 'preview_not_prepared',
                    case_id: 'case_blocked',
                    devtools_hint: 'Run bash scripts/launch_golden_qa.sh',
                },
                busy: false,
                sessionProgress: null,
                hasError: false,
            });
        default: {
            const _exhaustive: never = state;
            throw new Error(String(_exhaustive));
        }
    }
}

const STATES: FounderGoldenQaState[] = [
    'idle',
    'preparing',
    'ready',
    'testing',
    'verified',
    'blocked',
];

// 1) Founder view contains no hidden engineering concepts (including when API carries them).
for (const state of STATES) {
    const view = viewFor(state);
    const text = founderVisibleText(view);
    const leaks = assertNoFounderEngineeringLeak(text);
    assert.deepEqual(leaks, [], `state=${state} leaked: ${leaks.join(', ')}`);
    assert.match(text, new RegExp(FOUNDER_GOLDEN_QA_TITLE));
    assert.match(text, new RegExp(FOUNDER_GOLDEN_QA_SUBTITLE));
    assert.match(text, new RegExp(FOUNDER_GOLDEN_QA_TASK));
}

// 2) Correct plain-language state is rendered.
assert.equal(viewFor('preparing').statusLabel, 'Preparing');
assert.match(viewFor('preparing').statusDetail, /Preparing your test/);
assert.equal(viewFor('ready').statusLabel, 'Ready');
assert.match(viewFor('ready').statusDetail, /Scan the QR code/);
assert.equal(viewFor('testing').statusLabel, 'Testing');
assert.match(viewFor('testing').statusDetail, /上传保险卡/);
assert.equal(viewFor('verified').statusLabel, 'Verified');
assert.match(viewFor('verified').statusDetail, /Broker workbench/);
assert.equal(viewFor('blocked').statusLabel, 'Blocked');
assert.match(viewFor('blocked').statusDetail, /could not be prepared/);

// Ready never accepts stale / unprepared Preview.
assert.equal(viewFor('blocked').state, 'blocked');
assert.equal(viewFor('blocked').showQrPlaceholder, false);
assert.equal(viewFor('ready').showQrPlaceholder, true);
assert.equal(
    resolveFounderGoldenQaView({
        api: { ok: true, status: 'ready_to_scan', preview_prepared: false, enabled: true },
        busy: false,
        sessionProgress: null,
        hasError: false,
    }).state,
    'blocked',
);

// 3) Only one primary CTA (or none while Preparing).
assert.equal(primaryCtaCount(viewFor('preparing')), 0);
assert.equal(primaryCtaCount(viewFor('idle')), 1);
assert.equal(primaryCtaCount(viewFor('ready')), 1);
assert.equal(primaryCtaCount(viewFor('testing')), 1);
assert.equal(primaryCtaCount(viewFor('verified')), 1);
assert.equal(primaryCtaCount(viewFor('blocked')), 1);

// 4) Blocked state provides a safe retry (reuses launch; no secret exposure).
const blocked = viewFor('blocked');
assert.equal(blocked.primaryCta, 'Try again');
assert.equal(blocked.primaryAction, 'launch');
assert.equal(assertNoFounderEngineeringLeak(founderVisibleText(blocked)).length, 0);

// Failed launch also blocks with retry.
const failed = resolveFounderGoldenQaView({
    api: { ok: false, status: 'failed', failure_reason: 'golden_reset_failed_closed', enabled: true },
    busy: false,
    sessionProgress: null,
    hasError: true,
});
assert.equal(failed.state, 'blocked');
assert.equal(failed.primaryCta, 'Try again');
assert.equal(failed.primaryAction, 'launch');

// 5) Existing Engineering QA Console remains usable (source still exposes harness controls).
const here = dirname(fileURLToPath(import.meta.url));
const engineeringPage = readFileSync(join(here, '../../../pages/FounderQaConsolePage.tsx'), 'utf8');
assert.match(engineeringPage, /Engineering QA Console/);
assert.match(engineeringPage, /QA Identity/);
assert.match(engineeringPage, /Select QA Identity/);
assert.match(engineeringPage, /View Recent QA Audit Events/);
assert.match(engineeringPage, /runFounderQaPreset/);
assert.match(engineeringPage, /FRESH|ACTIVE|REQUEST_MORE/);

const founderPanel = readFileSync(join(here, 'LaunchGoldenQaPanel.tsx'), 'utf8');
assert.match(founderPanel, /FOUNDER_GOLDEN_QA_TITLE|Camry Golden QA/);
assert.match(founderPanel, /Engineering QA Console/);
assert.match(founderPanel, /launchGoldenQa/);
// Founder panel must not render engineering copy targets / identity UX.
assert.equal(founderPanel.includes('QA Identity'), false);
assert.equal(founderPanel.includes('Copy Case ID'), false);
assert.equal(founderPanel.includes('Copy Session'), false);
assert.equal(founderPanel.includes('Token expiration'), false);
assert.equal(founderPanel.includes('Latest Case ID'), false);
assert.equal(founderPanel.includes('devtools_hint'), false);
assert.equal(founderPanel.includes('Open Founder QA Console'), false);

console.log('founderGoldenQaViewModel.test.ts: PASS');
