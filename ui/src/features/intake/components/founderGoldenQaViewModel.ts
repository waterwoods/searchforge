/**
 * P0 Founder QA UX — Phase 1 view model.
 *
 * Founder tests the product. The system operates the QA infrastructure.
 * Never expose engineering concepts to the Founder.
 *
 * Reuses LaunchGoldenQaStatus; does not change the Golden QA pipeline.
 */

import type { LaunchGoldenQaStatus } from '@/api/inboxTriage';

/** Camry Golden QA current customer task (projection oracle). */
export const FOUNDER_GOLDEN_QA_TASK = '上传保险卡';

export const FOUNDER_GOLDEN_QA_TITLE = 'Camry Golden QA';
export const FOUNDER_GOLDEN_QA_SUBTITLE = 'Test Claim Vehicle';

/**
 * Founder-facing lifecycle states (Architecture Freeze).
 * `idle` is the pre-launch entry only; it is never shown as Ready.
 */
export type FounderGoldenQaState =
    | 'idle'
    | 'preparing'
    | 'ready'
    | 'testing'
    | 'verified'
    | 'blocked';

/** Client-only progress after a Ready handoff (no phone telemetry in Phase 1). */
export type FounderGoldenQaSessionProgress = 'testing' | 'verified' | null;

export type FounderPrimaryAction = 'launch' | 'acknowledge_testing' | 'acknowledge_verified' | null;

export type FounderGoldenQaView = {
    state: FounderGoldenQaState;
    statusLabel: string;
    statusDetail: string;
    currentTask: string;
    /** Exactly one primary CTA label, or null while waiting in Preparing. */
    primaryCta: string | null;
    primaryAction: FounderPrimaryAction;
    showQrPlaceholder: boolean;
};

/** Engineering terms that must never appear in the Founder surface render tree. */
export const FOUNDER_HIDDEN_ENGINEERING_TERMS = [
    'QA Identity',
    'session_id',
    'wx_',
    'token',
    'expires_at',
    'Token expiration',
    'case_id',
    'Case ID',
    'apiProfile',
    'DevTools',
    'compile mode',
    '清缓存',
    'audit',
    'Audit',
    'REQUEST_MORE',
    'confirm phrase',
    'Copy Session',
    'Copy Case',
    'paste',
    'devtools_hint',
    'token_masked',
    'handoff.json',
    'ENABLE_GOLDEN_QA',
    'preview_prepared',
    'running_reset',
    'preparing_preview',
] as const;

export function resolveFounderGoldenQaView(input: {
    api: LaunchGoldenQaStatus | null;
    busy: boolean;
    sessionProgress: FounderGoldenQaSessionProgress;
    hasError: boolean;
}): FounderGoldenQaView {
    const { api, busy, sessionProgress, hasError } = input;
    const status = String(api?.status || 'idle').toLowerCase();
    const previewPrepared = Boolean(api?.preview_prepared);
    const launchInFlight = Boolean(api?.launch_in_flight);
    const enabled = api?.enabled !== false;

    if (
        busy ||
        launchInFlight ||
        status === 'running_reset' ||
        status === 'preparing_preview'
    ) {
        return {
            state: 'preparing',
            statusLabel: 'Preparing',
            statusDetail: 'Preparing your test. Please wait…',
            currentTask: FOUNDER_GOLDEN_QA_TASK,
            primaryCta: null,
            primaryAction: null,
            showQrPlaceholder: false,
        };
    }

    if (sessionProgress === 'verified') {
        return {
            state: 'verified',
            statusLabel: 'Verified',
            statusDetail: 'Test complete. Broker workbench received the result.',
            currentTask: FOUNDER_GOLDEN_QA_TASK,
            primaryCta: 'Start a new test',
            primaryAction: 'launch',
            showQrPlaceholder: false,
        };
    }

    if (sessionProgress === 'testing') {
        return {
            state: 'testing',
            statusLabel: 'Testing',
            statusDetail: `Phone connected. Complete ${FOUNDER_GOLDEN_QA_TASK}.`,
            currentTask: FOUNDER_GOLDEN_QA_TASK,
            primaryCta: 'Mark test complete',
            primaryAction: 'acknowledge_verified',
            showQrPlaceholder: false,
        };
    }

    // Ready only when reset + Preview preparation both succeeded.
    // Never display a stale / unprepared Preview as Ready.
    if (api?.ok && status === 'ready_to_scan' && previewPrepared) {
        return {
            state: 'ready',
            statusLabel: 'Ready',
            statusDetail: 'Scan the QR code to test Claim Vehicle.',
            currentTask: FOUNDER_GOLDEN_QA_TASK,
            primaryCta: 'I scanned — continue',
            primaryAction: 'acknowledge_testing',
            showQrPlaceholder: true,
        };
    }

    const failedClosed =
        hasError ||
        !enabled ||
        status === 'failed' ||
        api?.ok === false ||
        (status === 'ready_to_scan' && !previewPrepared) ||
        Boolean(api?.failure_reason && status !== 'idle');

    if (failedClosed) {
        return {
            state: 'blocked',
            statusLabel: 'Blocked',
            statusDetail: 'Test could not be prepared.',
            currentTask: FOUNDER_GOLDEN_QA_TASK,
            primaryCta: 'Try again',
            primaryAction: 'launch',
            showQrPlaceholder: false,
        };
    }

    // Pre-launch entry — not Ready (no current QR).
    return {
        state: 'idle',
        statusLabel: 'Waiting',
        statusDetail: 'Launch when you are ready to test Claim Vehicle.',
        currentTask: FOUNDER_GOLDEN_QA_TASK,
        primaryCta: 'Launch on Phone',
        primaryAction: 'launch',
        showQrPlaceholder: false,
    };
}

/** Collect Founder-visible strings for regression scanning. */
export function founderVisibleText(view: FounderGoldenQaView): string {
    return [
        FOUNDER_GOLDEN_QA_TITLE,
        FOUNDER_GOLDEN_QA_SUBTITLE,
        view.statusLabel,
        view.statusDetail,
        `Current task: ${view.currentTask}`,
        view.primaryCta || '',
        view.showQrPlaceholder ? 'QR code' : '',
        view.showQrPlaceholder
            ? 'Scan with WeChat, then complete the task on your phone.'
            : '',
    ]
        .filter(Boolean)
        .join('\n');
}

export function assertNoFounderEngineeringLeak(text: string): string[] {
    const hits: string[] = [];
    for (const term of FOUNDER_HIDDEN_ENGINEERING_TERMS) {
        if (text.includes(term)) hits.push(term);
    }
    return hits;
}

/** Count primary CTAs implied by a view (0 or 1). */
export function primaryCtaCount(view: FounderGoldenQaView): number {
    return view.primaryCta ? 1 : 0;
}
