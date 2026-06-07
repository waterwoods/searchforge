/**
 * P16 Customer First — customer-facing status surface (Saved ≠ Submitted).
 */
import type { TriageResult } from '@/api/inboxTriage';
import { isFormalSubmissionToOfficeComplete } from '@/components/intake/AddCarRecordSummaryRail';
import { ADD_CAR_FIELD_LABELS } from '@/features/intake/constants';

export type CustomerSubmitState = 'saved' | 'submitted';

export type CustomerStatusLabel = 'saved_not_yet_submitted' | 'submitted_to_office';

export type CustomerContactState = 'waiting_for_customer' | 'office_reviewing' | 'broker_reviewing';

/** Single customer-visible business state (four states only). */
export type CustomerBusinessState =
    | 'awaiting_customer'
    | 'submitted_to_office'
    | 'office_processing'
    | 'closed';

/** English labels for status card Still Needed list (never count-only). */
const STATUS_SURFACE_FIELD_LABELS: Record<string, string> = {
    ...ADD_CAR_FIELD_LABELS,
    primary_driver: 'Driver License',
    delivery_date: 'Effective Date',
    make_model: 'Make & Model',
    driver_license: 'Driver License',
    effective_date: 'Effective Date',
};

export function customerStatusSurfaceFieldLabel(field: string): string {
    const key = field.trim();
    if (!key) return key;
    return STATUS_SURFACE_FIELD_LABELS[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function resolveCustomerSubmitState(
    triage: Pick<TriageResult, 'lifecycle_status' | 'formal_submitted_at'> | null | undefined,
): CustomerSubmitState {
    if (!triage) return 'saved';
    return isFormalSubmissionToOfficeComplete(triage as TriageResult) ? 'submitted' : 'saved';
}

export function resolveCustomerStatusLabel(
    summary: {
        submit_state?: string;
        is_formal_submitted?: boolean;
        status_label?: string;
    } | null | undefined,
): CustomerStatusLabel {
    if (summary?.status_label === 'submitted_to_office' || summary?.status_label === 'saved_not_yet_submitted') {
        return summary.status_label;
    }
    if (summary?.submit_state === 'submitted' || summary?.is_formal_submitted) {
        return 'submitted_to_office';
    }
    return 'saved_not_yet_submitted';
}

export function customerStatusLabelDisplay(label: CustomerStatusLabel): { en: string; zh: string } {
    if (label === 'submitted_to_office') {
        return { en: 'Submitted To Office', zh: '已提交办公室' };
    }
    return { en: 'Saved — Not Yet Submitted', zh: '已保存 · 尚未正式提交' };
}

export function resolveCustomerContactState(
    summary: {
        contact_state?: string;
        still_needed_fields?: string[];
        waiting_on?: string;
        submit_state?: string;
    } | null | undefined,
): CustomerContactState {
    const raw = summary?.contact_state?.trim();
    if (raw === 'waiting_for_customer' || raw === 'office_reviewing' || raw === 'broker_reviewing') {
        return raw;
    }
    const still = summary?.still_needed_fields?.filter(Boolean) ?? [];
    const waitingOn = (summary?.waiting_on ?? 'none').trim().toLowerCase();
    if (still.length > 0 || waitingOn === 'client') return 'waiting_for_customer';
    if (waitingOn === 'broker') return 'broker_reviewing';
    if (summary?.submit_state === 'submitted') return 'office_reviewing';
    return 'waiting_for_customer';
}

export function customerContactStateDisplay(state: CustomerContactState): { en: string; zh: string; hint?: string } {
    switch (state) {
        case 'office_reviewing':
            return {
                en: 'Office Reviewing',
                zh: '办公室审核中',
                hint: 'Your request has been received by the office.',
            };
        case 'broker_reviewing':
            return {
                en: 'Broker Reviewing',
                zh: '经纪人审核中',
                hint: 'Your broker usually responds within one business day.',
            };
        default:
            return {
                en: 'Waiting For Customer',
                zh: '等待您补充信息',
                hint: 'Please provide the missing information below.',
            };
    }
}

export function resolveCustomerBusinessState(
    summary: {
        business_state?: string;
        case_status?: string;
        status_label?: string;
        is_formal_submitted?: boolean;
        submit_state?: string;
        still_needed_fields?: string[];
        lifecycle_status?: string;
        waiting_on?: string;
    } | null | undefined,
): CustomerBusinessState {
    const raw = summary?.business_state?.trim();
    if (
        raw === 'awaiting_customer' ||
        raw === 'submitted_to_office' ||
        raw === 'office_processing' ||
        raw === 'closed'
    ) {
        return raw;
    }
    if (summary?.case_status?.trim().toLowerCase() === 'closed') {
        return 'closed';
    }
    const still = summary?.still_needed_fields?.filter(Boolean) ?? [];
    const formal =
        summary?.is_formal_submitted ||
        summary?.submit_state === 'submitted' ||
        summary?.status_label === 'submitted_to_office';
    if (still.length > 0 || !formal) {
        return 'awaiting_customer';
    }
    const lifecycle = (summary?.lifecycle_status ?? '').trim();
    const waitingOn = (summary?.waiting_on ?? 'none').trim().toLowerCase();
    if (lifecycle === 'office_followup') return 'office_processing';
    if (waitingOn === 'broker' || waitingOn === 'carrier' || waitingOn === 'underwriting') {
        return 'office_processing';
    }
    return 'submitted_to_office';
}

export function resolveCustomerBusinessStateFromTriage(
    triage: Pick<
        TriageResult,
        'still_needed_fields' | 'lifecycle_status' | 'formal_submitted_at' | 'waiting_on' | 'case_status'
    > | null | undefined,
): CustomerBusinessState {
    if (!triage) return 'awaiting_customer';
    if ((triage.case_status ?? '').trim().toLowerCase() === 'closed') {
        return 'closed';
    }
    if (!isFormalSubmissionToOfficeComplete(triage)) {
        return 'awaiting_customer';
    }
    return resolveCustomerBusinessState({
        is_formal_submitted: true,
        submit_state: 'submitted',
        status_label: 'submitted_to_office',
        still_needed_fields: triage.still_needed_fields,
        lifecycle_status: triage.lifecycle_status,
        waiting_on: triage.waiting_on,
    });
}

export function customerBusinessStateDisplay(state: CustomerBusinessState): {
    en: string;
    zh: string;
    hint?: string;
    tagColor: string;
} {
    switch (state) {
        case 'submitted_to_office':
            return {
                en: 'Submitted To Office',
                zh: '已提交办公室',
                hint: 'Your request has been received. The office will begin processing shortly.',
                tagColor: 'blue',
            };
        case 'office_processing':
            return {
                en: 'Office Processing',
                zh: '办公室处理中',
                hint: 'The office is working on your request. You do not need to resubmit the same information.',
                tagColor: 'processing',
            };
        case 'closed':
            return {
                en: 'Closed',
                zh: '已关闭',
                hint: 'This request has been closed. Contact your broker if you need to reopen.',
                tagColor: 'default',
            };
        default:
            return {
                en: 'Awaiting Your Information',
                zh: '等客户补资料',
                hint: 'Please provide the missing information below.',
                tagColor: 'gold',
            };
    }
}

export function customerSubmitStateLabel(state: CustomerSubmitState): { en: string; zh: string } {
    if (state === 'submitted') {
        return { en: 'Submitted To Office', zh: '已提交办公室' };
    }
    return { en: 'Saved — Not Yet Submitted', zh: '已保存 · 尚未正式提交' };
}

export const CUSTOMER_PHONE_STORAGE_KEY = 'unified_intake_customer_phone';
export const CUSTOMER_NAME_STORAGE_KEY = 'unified_intake_customer_name';

export function loadStoredCustomerPhone(): string {
    try {
        return localStorage.getItem(CUSTOMER_PHONE_STORAGE_KEY) ?? '';
    } catch {
        return '';
    }
}

export function saveStoredCustomerPhone(phone: string): void {
    try {
        localStorage.setItem(CUSTOMER_PHONE_STORAGE_KEY, phone.trim());
    } catch {
        /* ignore */
    }
}

export function loadStoredCustomerName(): string {
    try {
        return localStorage.getItem(CUSTOMER_NAME_STORAGE_KEY) ?? '';
    } catch {
        return '';
    }
}

export function saveStoredCustomerName(name: string): void {
    try {
        const v = name.trim();
        if (v) {
            localStorage.setItem(CUSTOMER_NAME_STORAGE_KEY, v);
        } else {
            localStorage.removeItem(CUSTOMER_NAME_STORAGE_KEY);
        }
    } catch {
        /* ignore */
    }
}

export function normalizePhoneInput(raw: string): string {
    const digits = raw.replace(/\D/g, '');
    if (digits.length === 11 && digits.startsWith('1')) {
        return digits.slice(1);
    }
    return digits;
}

export function isValidCustomerPhoneInput(raw: string): boolean {
    return normalizePhoneInput(raw).length === 10;
}

export function formatPhoneDisplay(raw: string): string {
    const d = normalizePhoneInput(raw);
    if (d.length !== 10) return raw.trim();
    return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
}
