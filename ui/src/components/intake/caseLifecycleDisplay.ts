/**
 * Primary user-facing progress axis: API `case_lifecycle` (see `services/fiqa_api/inbox_triage/case_lifecycle.py`
 * and `routes/inbox_triage._attach_case_lifecycle`, which may overlay `formal_submitted_at` from persisted case).
 * Falls back to client-side derivation when `case_lifecycle` is absent or non-canonical (older payloads).
 */
import type { TriageResultCore } from '../../api/triageResultContract';

export type CaseLifecycle = 'collecting' | 'almost_ready' | 'ready_for_handoff' | 'submitted';

const VALID = new Set<string>(['collecting', 'almost_ready', 'ready_for_handoff', 'submitted']);

function str(x: unknown): string {
    return (x ?? '').toString().trim();
}

/** Mirrors backend `_derive_case_lifecycle` for offline / legacy responses. */
export function resolveCaseLifecycle(
    t:
        | Pick<
              TriageResultCore,
              'case_lifecycle' | 'formal_submitted_at' | 'triage_mode' | 'handoff_ready' | 'quote_ready_status'
          >
        | null
        | undefined,
): CaseLifecycle {
    if (!t) return 'collecting';
    const direct = str(t.case_lifecycle);
    if (direct && VALID.has(direct)) return direct as CaseLifecycle;
    if (str(t.formal_submitted_at)) return 'submitted';
    if (str(t.triage_mode).toLowerCase() === 'greenfield' && t.handoff_ready === true) return 'ready_for_handoff';
    if (str(t.quote_ready_status).toLowerCase() === 'almost_ready') return 'almost_ready';
    return 'collecting';
}

/** Short label for tags / list rows (user-friendly, not CRM jargon). */
export function caseLifecycleUserLabel(cl: CaseLifecycle): string {
    switch (cl) {
        case 'collecting':
            return '补充资料中';
        case 'almost_ready':
            return '还差少量信息';
        case 'ready_for_handoff':
            return '可提交办公室';
        case 'submitted':
            return '已送达办公室';
        default:
            return '办理中';
    }
}

/** Ant Design Tag color token. */
export function caseLifecycleTagColor(cl: CaseLifecycle): string {
    switch (cl) {
        case 'collecting':
            return 'default';
        case 'almost_ready':
            return 'gold';
        case 'ready_for_handoff':
            return 'green';
        case 'submitted':
            return 'blue';
        default:
            return 'default';
    }
}

/** Formal submit CTA: derived axis + legacy `lifecycle_status` for older servers. */
export function isAddCarReadyForFormalSubmit(t: TriageResultCore | undefined | null): boolean {
    if (!t) return false;
    if (resolveCaseLifecycle(t) === 'ready_for_handoff') return true;
    return t.lifecycle_status === 'handoff_pending';
}
