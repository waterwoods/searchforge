/**
 * Customer portal presentation helpers — copy and layout only; no triage or persistence logic.
 */
import type { TriageResult } from '../../api/inboxTriage';
import { humanizeStructuredFieldForCustomer } from '../../features/intake/utils';
import { isFormalSubmissionToOfficeComplete } from './AddCarRecordSummaryRail';

/** Short labels for progress checklist (customer scan, not broker rail). */
const PROGRESS_FIELD_LABELS: Record<string, string> = {
    year: '车辆',
    make_model: '车辆',
    model: '车辆',
    vin: 'VIN',
    zip: '邮编',
    primary_driver: '主驾',
    name: '姓名',
    phone: '电话',
};

export function customerProgressFieldLabel(field: string): string {
    return PROGRESS_FIELD_LABELS[field] ?? humanizeStructuredFieldForCustomer(field);
}

/** Dedupe display labels (e.g. year + make_model → one「车辆」). */
export function uniqueCustomerProgressLabels(fieldIds: string[]): string[] {
    const seen = new Set<string>();
    const out: string[] = [];
    for (const f of fieldIds.filter(Boolean)) {
        const label = customerProgressFieldLabel(f);
        if (!seen.has(label)) {
            seen.add(label);
            out.push(label);
        }
    }
    return out;
}

export function computeIntakeProgressPercent(collected: string[], stillNeeded: string[]): number {
    const c = collected.filter(Boolean).length;
    const s = stillNeeded.filter(Boolean).length;
    const total = c + s;
    if (total === 0) return 0;
    return Math.round((c / total) * 100);
}

function joinChineseList(labels: string[]): string {
    if (labels.length === 0) return '';
    if (labels.length === 1) return labels[0]!;
    if (labels.length === 2) return `${labels[0]}和${labels[1]}`;
    return `${labels.slice(0, -1).join('、')}和${labels[labels.length - 1]}`;
}

/** Customer-facing next-step body from existing triage fields (decision logic unchanged). */
export function buildCustomerNextStepPresentation(triage: TriageResult): {
    primary: string;
    secondary?: string;
} {
    const still = triage.still_needed_fields?.filter(Boolean) ?? [];
    const nbq = (triage.next_best_question ?? '').trim();

    let primary: string;
    if (still.length > 0) {
        const labels = uniqueCustomerProgressLabels(still);
        primary = `请补充${joinChineseList(labels)}。`;
    } else if (nbq) {
        primary = nbq.endsWith('。') || nbq.endsWith('？') ? nbq : `${nbq}。`;
    } else {
        return { primary: '' };
    }

    const secondary =
        !isFormalSubmissionToOfficeComplete(triage) && !triage.handoff_ready
            ? '办公室收到后即可开始报价。'
            : undefined;

    return { primary, secondary };
}
