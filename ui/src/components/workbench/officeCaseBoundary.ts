import type { TriageResult } from '../../api/inboxTriage';

/** Office workbench: append / matter-boundary states from triage (aligned with backend contract). */
export type OfficeCaseBoundaryPresentation = {
    badgeColor: string;
    badgeLabel: string;
    /** One line: what happened / what it means */
    summaryLine: string;
    /** One line: recommended broker action */
    actionLine: string;
};

/**
 * Returns presentation when `case_boundary` is set on the service record (post-append triage).
 * Omit when absent — initial-only cases may not have run append boundary classification.
 */
export function getOfficeCaseBoundaryPresentation(
    c: Pick<TriageResult, 'case_boundary' | 'case_boundary_action' | 'boundary_reason'>,
): OfficeCaseBoundaryPresentation | null {
    const cb = (c.case_boundary ?? '').trim();
    if (cb === 'same_case') {
        return {
            badgeColor: 'cyan',
            badgeLabel: '同案追加',
            summaryLine: '本条与当前服务记录一致，可按同一条继续整理与跟进。',
            actionLine: '推荐：正常跟进与回复；若实际是分项事项再单独开案。',
        };
    }
    if (cb === 'borderline') {
        return {
            badgeColor: 'gold',
            badgeLabel: '边界待确认（已落库）',
            summaryLine:
                '客户消息已写入本条记录（可追溯）；主题是否仍属同一事项不够明确——并非拦截，而是提醒复核。',
            actionLine: '推荐：办公室确认范围或向客户确认是否分项处理。',
        };
    }
    if (cb === 'new_issue') {
        return {
            badgeColor: 'volcano',
            badgeLabel: '疑似新事项',
            summaryLine: '系统判断不宜把本条当作普通追加合并进当前案（与「同案继续」不同）。',
            actionLine: '推荐：新开服务记录或先与客户确认分项，再分别跟进。',
        };
    }
    return null;
}

/** Compact tag for queue cards — same semantics as detail strip */
export function getOfficeCaseBoundaryListTag(
    c: Pick<TriageResult, 'case_boundary'>,
): { color: string; label: string } | null {
    const cb = (c.case_boundary ?? '').trim();
    if (cb === 'same_case') return { color: 'cyan', label: '追加 · 同案继续' };
    if (cb === 'borderline') return { color: 'gold', label: '追加 · 边界待确认（已落库）' };
    if (cb === 'new_issue') return { color: 'volcano', label: '追加 · 疑似新事项' };
    return null;
}

/** Short fragment for queue preview line (Chinese) */
export function getOfficeCaseBoundaryPreviewSuffix(caseBoundary?: string): string | null {
    const cb = (caseBoundary ?? '').trim();
    if (cb === 'same_case') return '边界：同案继续';
    if (cb === 'borderline') return '边界：待确认（已落库）';
    if (cb === 'new_issue') return '边界：疑似新事项';
    return null;
}
