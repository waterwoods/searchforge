import { Space, Tag, Typography } from 'antd';
import type { UiCopy } from '@/api/clientConfig';
import type { TriageResult } from '@/api/inboxTriage';
import { addCarNextOwnerLine } from '@/components/intake/AddCarRecordSummaryRail';
import { CASE_STATUS_OPTIONS } from '@/features/intake/constants';
import {
    addCarQueueStatusPhase,
    buildOfficeWorkbenchGlance,
    formatPortalLocalDateTime,
    getCaseStatusColor,
    getFollowUpDueTag,
    getOfficeLifecycleTag,
    getPreviewText,
    getUrgencyColor,
    hasSavedFollowUpTarget,
    humanizeCaseStatus,
    humanizeUrgencyLabel,
    humanizeWaitingOn,
    normalizeFollowUpText,
    triageResultLooksLikeAddCar,
} from '@/features/intake/utils';

const { Text } = Typography;

export function UrgencyTag({ urgency }: { urgency: string }) {
    return <Tag color={getUrgencyColor(urgency)}>{humanizeUrgencyLabel(urgency)}</Tag>;
}

export function CaseStatusTag({ status }: { status?: string }) {
    const opt = CASE_STATUS_OPTIONS.find((o) => o.value === status);
    return <Tag color={getCaseStatusColor(status)}>{opt?.label ?? humanizeCaseStatus(status)}</Tag>;
}

/** Office workbench detail: submission/received + bounded timestamps + process owner (parity with customer closure model). */
export function OfficeWorkbenchAddCarSubmissionSnapshot({ triage, uiCopy }: { triage: TriageResult; uiCopy: UiCopy }) {
    if (!triageResultLooksLikeAddCar(triage)) return null;
    const u = uiCopy;
    const formal = addCarQueueStatusPhase(triage) === 'submitted';
    const lt = getOfficeLifecycleTag(triage.lifecycle_status);
    const created = formatPortalLocalDateTime(triage.created_at);
    const updated = formatPortalLocalDateTime(triage.updated_at);
    const title = u.office_workbench_submission_snapshot_title ?? '报送与送达';
    const qFormal = u.office_workbench_formal_to_office_question ?? '正式送达办公室';
    const yes = u.office_workbench_formal_to_office_yes ?? '是';
    const no = u.office_workbench_formal_to_office_no ?? '否';
    const stateLabel = u.office_workbench_current_handoff_state_label ?? '当前接手状态';
    const createdLabel = u.office_workbench_record_created_label ?? '记录创建';
    const updatedLabel = u.office_workbench_record_updated_label ?? '最近更新';
    const formalSubmittedLabel = u.office_workbench_formal_submitted_at_label ?? '正式送达办公室（首次）';
    const lastActivityLabel = u.office_workbench_last_activity_label ?? '最近活动（系统更新时间）';
    const processLabel = u.office_workbench_process_owner_label ?? '流程主要负责方';
    const proxyNote =
        u.office_workbench_submitted_proxy_note ??
        '时间说明：「正式送达」为首次进入办公室队列的时间（正式提交）；「最近活动」含后续追加、备注等写入。均为服务端 UTC 时间戳的本地显示。';
    const ls = (triage.lifecycle_status ?? '').trim();
    const formalAt = formatPortalLocalDateTime(triage.formal_submitted_at ?? triage.created_at);
    const timeLine = (() => {
        if (formal) {
            const parts: string[] = [];
            if (formalAt) parts.push(`${formalSubmittedLabel}：${formalAt}`);
            if (updated && (!formalAt || updated !== formalAt)) {
                parts.push(`${lastActivityLabel}：${updated}`);
            }
            if (parts.length) return parts.join(' · ');
            if (created) return `${createdLabel}：${created}`;
            return null;
        }
        if (created && updated && updated !== created) {
            return `${createdLabel}：${created} · ${updatedLabel}：${updated}`;
        }
        if (created) return `${createdLabel}：${created}`;
        if (updated) return `${updatedLabel}：${updated}`;
        return null;
    })();

    return (
        <div
            style={{
                marginBottom: 12,
                padding: 12,
                borderRadius: 8,
                border: '1px solid #e8e8e8',
                borderLeft: '4px solid #1677ff',
                background: '#fafcff',
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
                {title}
            </Text>
            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
                    <Text style={{ fontSize: 13 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>{qFormal}：</Text>
                        <Tag color={formal ? 'success' : 'warning'} style={{ marginInlineStart: 6 }}>
                            {formal ? yes : no}
                        </Tag>
                        {lt ? (
                            <Text type="secondary" style={{ fontSize: 12, marginInlineStart: 8 }}>
                                {stateLabel}：{lt.label}
                            </Text>
                        ) : null}
                    </Text>
                </div>
                {ls === 'handoff_pending' && (
                    <Text style={{ fontSize: 12, color: '#ad6800', lineHeight: 1.55 }}>
                        {u.office_workbench_handoff_pending_office_note}
                    </Text>
                )}
                {ls === 'collecting' && (
                    <Text style={{ fontSize: 12, color: '#0958d9', lineHeight: 1.55 }}>
                        {u.office_workbench_collecting_office_note}
                    </Text>
                )}
                {!formal && !ls && (triage.case_id ?? '').toString().trim() && (
                    <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55 }}>
                        {u.office_workbench_intake_phase_office_note}
                    </Text>
                )}
                {timeLine ? (
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                        {timeLine}
                    </Text>
                ) : null}
                {proxyNote ? (
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', lineHeight: 1.5 }}>
                        {proxyNote}
                    </Text>
                ) : null}
                <Text style={{ fontSize: 12, lineHeight: 1.55 }}>
                    <Text type="secondary">{processLabel}：</Text>
                    {addCarNextOwnerLine(triage)}
                </Text>
            </Space>
        </div>
    );
}

export function OfficeWorkbenchOneGlanceSummary({
    triage,
    inputFallback,
    uiCopy,
}: {
    triage: TriageResult;
    inputFallback: string;
    uiCopy: UiCopy;
}) {
    const g = buildOfficeWorkbenchGlance(triage, inputFallback);
    const addCar = triageResultLooksLikeAddCar(triage);
    const formal = addCar && addCarQueueStatusPhase(triage) === 'submitted';
    const u = uiCopy;
    const qFormal = u.office_workbench_formal_to_office_question ?? '正式送达办公室';
    const yes = u.office_workbench_formal_to_office_yes ?? '是';
    const no = u.office_workbench_formal_to_office_no ?? '否';
    const stateLabel = u.office_workbench_current_handoff_state_label ?? '当前接手状态';
    const lt = addCar ? getOfficeLifecycleTag(triage.lifecycle_status) : null;

    return (
        <div
            style={{
                marginBottom: 4,
                padding: 14,
                borderRadius: 8,
                border: '1px solid #d6e4ff',
                borderLeft: '4px solid #2f54eb',
                background: 'linear-gradient(180deg, #f0f5ff 0%, #ffffff 100%)',
            }}
        >
            <Text strong style={{ fontSize: 13, color: '#1d39c4', display: 'block', marginBottom: 4 }}>
                整理结果（办公室一眼）· 三步扫读
            </Text>
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 12, lineHeight: 1.45 }}>
                系统已把客户原文整理为可接手结论；需要核对原文时在下方「完整对话」展开。
            </Text>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                {g.missingLine ? (
                    <div
                        style={{
                            padding: '10px 12px',
                            borderRadius: 8,
                            background: '#fff7e6',
                            border: '1px solid #ffd591',
                            borderLeft: '4px solid #fa8c16',
                        }}
                    >
                        <Text strong style={{ fontSize: 12, color: '#ad4e00', display: 'block', marginBottom: 4 }}>
                            还缺什么（首要）
                        </Text>
                        <Text style={{ fontSize: 14, color: '#434343', lineHeight: 1.55, display: 'block' }}>{g.missingLine}</Text>
                    </div>
                ) : null}
                <div>
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ① 案子（谁 · 办什么）
                    </Text>
                    <Text style={{ fontSize: 13, color: '#262626', display: 'block', lineHeight: 1.55 }}>{g.contactLine}</Text>
                    <Text style={{ fontSize: 13, color: '#262626', display: 'block', lineHeight: 1.55 }}>{g.matterLine}</Text>
                    {g.vehicleLine ? (
                        <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55 }}>{g.vehicleLine}</Text>
                    ) : null}
                </div>

                <div
                    style={{
                        padding: 10,
                        borderRadius: 8,
                        background: 'rgba(0, 0, 0, 0.02)',
                        border: '1px solid #f0f0f0',
                    }}
                >
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ② 状态与缺口（信任）
                    </Text>
                    <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55 }}>{g.stageLine}</Text>
                    {addCar ? (
                        <div
                            style={{
                                marginTop: 8,
                                display: 'flex',
                                flexWrap: 'wrap',
                                alignItems: 'center',
                                gap: 8,
                            }}
                        >
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {qFormal}：
                            </Text>
                            <Tag color={formal ? 'success' : 'warning'}>{formal ? yes : no}</Tag>
                            {lt ? (
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    {stateLabel}：{lt.label}
                                </Text>
                            ) : null}
                        </div>
                    ) : null}
                    {g.quotePrepLine ? (
                        <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55, marginTop: 8 }}>
                            {g.quotePrepLine}
                        </Text>
                    ) : null}
                    {!g.missingLine ? (
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                            结构化缺项：当前未标「还缺」（仍以办公室核实为准）
                        </Text>
                    ) : (
                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 8 }}>
                            字段级明细可在下方「结构化字段」展开核对。
                        </Text>
                    )}
                </div>

                <div style={{ paddingTop: 4, borderTop: '1px solid #e6ebf5' }}>
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ③ 行动与对外
                    </Text>
                    {g.latestCustomerLine ? (
                        <Text
                            type="secondary"
                            style={{ fontSize: 11, display: 'block', lineHeight: 1.45, marginBottom: 8 }}
                        >
                            {g.latestCustomerLine}
                        </Text>
                    ) : null}
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                        主行动（办公室）
                    </Text>
                    <Text strong style={{ fontSize: 15, color: '#10239e', lineHeight: 1.5, display: 'block' }}>
                        {g.nextStep}
                    </Text>
                    {(() => {
                        const hasFu = hasSavedFollowUpTarget(triage);
                        const due = getFollowUpDueTag(triage.next_contact_by);
                        const wo = triage.waiting_on ?? 'none';
                        const ncb = normalizeFollowUpText(triage.next_contact_by);
                        if (!hasFu) return null;
                        return (
                            <div
                                style={{
                                    marginTop: 10,
                                    padding: '8px 10px',
                                    borderRadius: 6,
                                    background:
                                        due?.kind === 'overdue'
                                            ? 'rgba(255, 77, 79, 0.06)'
                                            : due?.kind === 'due_today'
                                              ? 'rgba(250, 140, 22, 0.08)'
                                              : 'rgba(24, 144, 255, 0.06)',
                                    border: '1px solid #f0f0f0',
                                }}
                            >
                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                    跟进计划（与主行动对齐）
                                </Text>
                                <Space wrap size={[4, 4]}>
                                    {due ? <Tag color={due.color}>{due.label}</Tag> : null}
                                    {wo !== 'none' ? (
                                        <Tag color="purple">在等：{humanizeWaitingOn(wo)}</Tag>
                                    ) : null}
                                    {ncb ? (
                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                            下次跟进：{ncb}
                                        </Text>
                                    ) : null}
                                </Space>
                            </div>
                        );
                    })()}
                    {(() => {
                        const d = (triage.client_reply_draft ?? '').trim();
                        if (!d) return null;
                        return (
                            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 10, lineHeight: 1.5 }}>
                                客户草稿预览：{getPreviewText(d, 96)}
                            </Text>
                        );
                    })()}
                </div>
            </Space>
        </div>
    );
}
