/**
 * Add-Car right-rail / record summary: step, why-here, grouped received vs missing, correction signal, next owner.
 * Used by customer portal progress card and simulation state column (§4.6 / §4.7 alignment).
 */
import { Divider, Space, Tag, Typography } from 'antd';
import type { UiCopy } from '../../api/clientConfig';
import type { TriageResult } from '../../api/inboxTriage';
import { AddCarFlowExplanation } from './AddCarFlowExplanation';
import {
    clearedStillNeededSincePrior,
    groupAddCarRailFields,
    newCollectedSincePrior,
    newStillNeededSincePrior,
    railFieldLabel,
} from './addCarRecordRailLabels';

const { Text } = Typography;

function formatHandoffRailDateTime(iso?: string): string | null {
    const s = (iso ?? '').trim();
    if (!s) return null;
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return d.toLocaleString('zh-CN', { hour12: false });
}

/**
 * True when office-visible formal submit truth exists (immutable first queue write or explicit post-handoff lifecycle).
 * Not `handoff_ready` / not `case_id` alone — a draft record may exist before the customer formally submits.
 */
export function isFormalSubmissionToOfficeComplete(triage: TriageResult | undefined): boolean {
    if (!triage) return false;
    const ls = (triage.lifecycle_status ?? '').trim();
    if (ls === 'handoff_pending' || ls === 'collecting') return false;
    if ((triage.formal_submitted_at ?? '').toString().trim()) return true;
    if (ls === 'handed_off' || ls === 'office_followup') return true;
    return false;
}

export function computeAddCarFlowStep(triage: TriageResult | undefined, hasConversationStarted: boolean): 1 | 2 | 3 {
    if (isFormalSubmissionToOfficeComplete(triage)) return 3;
    if (hasConversationStarted) return 2;
    return 1;
}

/** Process-oriented next-owner line (broker/founder scan). */
export function addCarNextOwnerLine(t: TriageResult | undefined): string {
    if (!t) return '—';
    if (isFormalSubmissionToOfficeComplete(t)) return '办公室 — 核对记录、出价准备与对外跟进';
    if (t.lifecycle_status === 'handoff_pending') return '客户 — 确认并提交，将本条记录正式送办公室';
    if ((t.still_needed_fields?.length ?? 0) > 0 || (t.next_best_question ?? '').trim()) {
        return '客户 — 按缺项与系统提示继续补充（写入同一条服务记录）';
    }
    return '系统 — 继续整理要点与下一步提示';
}

function stepTitle(flowStep: 1 | 2 | 3, ui: UiCopy): string {
    const s1 = ui.portal_flow_step_1 ?? '开始报送';
    const s2 = ui.portal_flow_step_2 ?? '补齐关键信息';
    const s3 = ui.portal_flow_step_3 ?? '办公室接手处理';
    if (flowStep === 1) return `第 1 步：${s1}`;
    if (flowStep === 2) return `第 2 步：${s2}`;
    return `第 3 步：${s3}`;
}

/** Step-2 only: what “done” means before office takeover (Amazon-style completion clarity). */
function completionConditionLines(triage: TriageResult, flowStep: 1 | 2 | 3, ui: UiCopy): string[] {
    if (flowStep !== 2) return [];
    if (isFormalSubmissionToOfficeComplete(triage)) return [];
    if (triage.lifecycle_status === 'handoff_pending') {
        return [
            ui.record_rail_completion_hint_handoff_pending ??
                '完成条件：系统已标「资料已齐」— 请在入口点击提交，将本条记录正式送办公室。',
        ];
    }
    const stillN = triage.still_needed_fields?.filter(Boolean).length ?? 0;
    if (stillN > 0 || (triage.next_best_question ?? '').trim()) {
        return [
            ui.record_rail_completion_hint_gaps ??
                '完成条件：按上方「仍缺项」与「您这边下一步」补全或说明，直至系统标为可交办公室。',
        ];
    }
    return [
        ui.record_rail_completion_hint_collecting ??
            '完成条件：系统仍在整理要点；若出现缺项或追问，请继续在同一记录内补充。',
    ];
}

function whyHereLines(triage: TriageResult, flowStep: 1 | 2 | 3, submitLabel: string): string[] {
    const lines: string[] = [];
    if (flowStep === 1) {
        lines.push('尚未开始对话报送；点选办理类型或输入内容后，系统会把本条请求锚定到服务记录。');
        return lines;
    }
    if (isFormalSubmissionToOfficeComplete(triage) || flowStep === 3) {
        lines.push('办公室已收到本条服务记录：可接手核对、出价准备与对外跟进。');
        return lines;
    }
    if (triage.lifecycle_status === 'handoff_pending') {
        lines.push('系统判断关键要点已齐：等待您在入口正式提交，将记录送办公室。');
        lines.push(`请在准备好后点「${submitLabel}」，将本条正式送办公室。`);
        return lines;
    }
    const still = triage.still_needed_fields?.filter(Boolean) ?? [];
    if (still.length > 0) {
        const labels = still.slice(0, 6).map(railFieldLabel).join('、');
        lines.push(`仍在补齐阶段：系统标记还缺 ${labels}${still.length > 6 ? '…' : ''}。`);
    } else if ((triage.next_best_question ?? '').trim()) {
        lines.push('仍有追问或说明待确认：请按「您这边下一步」或办公室回复继续补充。');
    } else {
        lines.push('仍在第二步：请通过下方输入继续说明，直至达到可提交办公室的条件。');
    }
    return lines;
}

export type AddCarRecordSummaryRailMode = 'portal_pre' | 'portal_post_compact' | 'simulation';

type Props = {
    triage: TriageResult;
    priorSystemTriage?: TriageResult | null;
    uiCopy: UiCopy;
    mode: AddCarRecordSummaryRailMode;
    flowStep: 1 | 2 | 3;
    /** Pre-handoff submit button label (handoff_pending CTA). */
    submitLabel?: string;
    stillNeededLabelsForExplain?: string[];
};

function GroupedFieldBlock({
    title,
    groups,
    color,
}: {
    title: string;
    groups: ReturnType<typeof groupAddCarRailFields>;
    color: string;
}) {
    if (groups.length === 0) return null;
    return (
        <div>
            <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 8 }}>
                {title}
            </Text>
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
                {groups.map((g) => (
                    <div key={g.title}>
                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                            {g.title}
                        </Text>
                        <Space size={4} wrap>
                            {g.keys.map((k) => (
                                <Tag key={k} color={color}>
                                    {railFieldLabel(k)}
                                </Tag>
                            ))}
                        </Space>
                    </div>
                ))}
            </Space>
        </div>
    );
}

/** Prior system triage vs current: new collected ids, still-needed deltas, correction flag, impact copy (bounded, no fake field diffs). */
export function buildAddCarRailTurnModel(triage: TriageResult, priorSystemTriage: TriageResult | null | undefined, ui: UiCopy) {
    const prior = priorSystemTriage ?? null;
    const collected = triage.collected_fields?.filter(Boolean) ?? [];
    const still = triage.still_needed_fields?.filter(Boolean) ?? [];
    const newKeys = prior ? newCollectedSincePrior(prior.collected_fields, triage.collected_fields) : [];
    const clearedStill = prior ? clearedStillNeededSincePrior(prior.still_needed_fields, triage.still_needed_fields) : [];
    const addedStill = prior ? newStillNeededSincePrior(prior.still_needed_fields, triage.still_needed_fields) : [];
    const showCorrectionBanner = triage.follow_up_type === 'correction';
    const showNewCollected = newKeys.length > 0;
    const showStillDelta = clearedStill.length > 0 || addedStill.length > 0;
    const showUpdateSection = showCorrectionBanner || showNewCollected || showStillDelta;

    const understoodLead =
        ui.record_rail_understood_version_lead ??
        '以下为本条服务记录截至本轮的系统理解版本；与上方步骤、缺项及下一步一致。';
    const showUnderstoodLead = collected.length > 0 || still.length > 0;

    const impactLines: string[] = [];
    if (prior) {
        if (!prior.handoff_ready && triage.handoff_ready) {
            impactLines.push(
                ui.record_rail_impact_handoff_became_ready ??
                    '本回合起记录已达到可交办公室条件；步骤与主要负责方随之上移（见上方「当前步骤」）。',
            );
        }
        if (clearedStill.length > 0) {
            impactLines.push(ui.record_rail_impact_still_reduced ?? '缺项减少，记录更接近可提交办公室状态。');
        }
        if (addedStill.length > 0) {
            impactLines.push(ui.record_rail_impact_still_increased ?? '缺项增加或调整，当前仍需按上方「仍缺项」补充。');
        }
        const handoffUnchanged = prior.handoff_ready === triage.handoff_ready;
        if (
            showCorrectionBanner &&
            clearedStill.length === 0 &&
            addedStill.length === 0 &&
            newKeys.length === 0 &&
            handoffUnchanged
        ) {
            impactLines.push(
                ui.record_rail_impact_correction_same_gaps ??
                    '步骤与缺项列表未变，但已记要点已按最新说法整理；请以绿色标签为准。',
            );
        }
        if (
            newKeys.length > 0 &&
            clearedStill.length === 0 &&
            addedStill.length === 0 &&
            !showCorrectionBanner &&
            handoffUnchanged
        ) {
            impactLines.push(
                ui.record_rail_impact_new_fields_only ?? '本回合新记入字段已并入上方「系统已收到的要点」。',
            );
        }
    }
    const showImpactSection = prior !== null && impactLines.length > 0;

    return {
        collected,
        still,
        newKeys,
        clearedStill,
        addedStill,
        showCorrectionBanner,
        showNewCollected,
        showUpdateSection,
        understoodLead,
        showUnderstoodLead,
        impactLines,
        showImpactSection,
    };
}

export function AddCarRecordSummaryRail({
    triage,
    priorSystemTriage,
    uiCopy,
    mode,
    flowStep,
    submitLabel = '提交补充',
    stillNeededLabelsForExplain,
}: Props) {
    const u = uiCopy;
    const stillLabelsForFlow =
        stillNeededLabelsForExplain ?? (triage.still_needed_fields?.filter(Boolean) ?? []).map(railFieldLabel);

    const sectionCurrent = u.record_rail_section_current_step ?? '当前步骤';
    const sectionWhy = u.record_rail_section_why_here ?? '为什么在这一步';
    const sectionCompletion = u.record_rail_section_completion ?? '完成条件（本步）';
    const sectionReceived = u.record_rail_section_received ?? '系统已收到的要点';
    const sectionMissing = u.record_rail_section_still_needed ?? '仍缺项（报价准备前）';
    const sectionUpdate = u.record_rail_section_latest_update ?? '本轮更新 / 更正';
    const sectionNext = u.record_rail_section_next_owner ?? '下一步谁负责 · 两条路径';

    const {
        collected,
        still,
        newKeys,
        clearedStill,
        addedStill,
        showCorrectionBanner,
        showNewCollected,
        showUpdateSection,
        understoodLead,
        showUnderstoodLead,
        impactLines,
        showImpactSection,
    } = buildAddCarRailTurnModel(triage, priorSystemTriage, u);

    const whyLines = whyHereLines(triage, flowStep, submitLabel);
    const completionLines = completionConditionLines(triage, flowStep, u);
    const ownerLine = addCarNextOwnerLine(triage);
    const appendCustomer = u.record_rail_if_continue_append_hint ?? '若继续补充，系统将写入同一条服务记录。';
    const appendOffice = u.record_rail_if_stop_office_hint ?? '若暂不补充，办公室将按当前记录继续核对与出价。';

    const compact = mode === 'simulation';
    const titleSize = compact ? 11 : 12;
    const bodySize = compact ? 12 : 13;

    const groupedCollected = groupAddCarRailFields(collected);
    const groupedStill = groupAddCarRailFields(still);

    return (
        <Space direction="vertical" size={compact ? 10 : 14} style={{ width: '100%' }}>
            {mode === 'portal_pre' && (
                <AddCarFlowExplanation
                    uiCopy={uiCopy}
                    variant="pre_handoff"
                    stillNeededLabels={stillLabelsForFlow}
                    handoffPending={triage.lifecycle_status === 'handoff_pending'}
                />
            )}

            <div
                style={{
                    padding: compact ? '8px 0 0' : '10px 12px',
                    background: compact ? undefined : '#fafafa',
                    border: compact ? undefined : '1px solid #f0f0f0',
                    borderRadius: 8,
                }}
            >
                {triage.human_confirmation_required && (
                    <Tag color="gold" style={{ marginBottom: 8, fontSize: compact ? 11 : 12 }}>
                        {u.record_rail_human_confirm_tag ?? '含需办公室核对要点（VIN/驾驶人/材料等）'}
                    </Tag>
                )}
                <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginBottom: 4 }}>
                    {sectionCurrent}
                </Text>
                <Tag color={flowStep === 3 ? 'success' : flowStep === 2 ? 'processing' : 'default'} style={{ fontSize: compact ? 12 : 13, marginBottom: 8 }}>
                    {stepTitle(flowStep, u)}
                </Tag>

                <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginBottom: 6 }}>
                    {sectionWhy}
                </Text>
                {whyLines.map((line, i) => (
                    <Text key={i} style={{ fontSize: bodySize, lineHeight: 1.6, display: 'block' }}>
                        {line}
                    </Text>
                ))}

                {completionLines.length > 0 && (
                    <>
                        <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginTop: 10, marginBottom: 6 }}>
                            {sectionCompletion}
                        </Text>
                        {completionLines.map((line, i) => (
                            <Text key={`c-${i}`} style={{ fontSize: bodySize, lineHeight: 1.6, display: 'block' }}>
                                {line}
                            </Text>
                        ))}
                    </>
                )}

                <Divider style={{ margin: compact ? '10px 0' : '14px 0' }} />

                {showUnderstoodLead && (
                    <Text type="secondary" style={{ fontSize: compact ? 11 : 12, lineHeight: 1.55, display: 'block', marginBottom: 10 }}>
                        {understoodLead}
                    </Text>
                )}
                <GroupedFieldBlock title={sectionReceived} groups={groupedCollected} color="green" />
                {groupedCollected.length > 0 && groupedStill.length > 0 ? <Divider style={{ margin: '10px 0' }} /> : null}
                <GroupedFieldBlock title={sectionMissing} groups={groupedStill} color="orange" />
                {groupedStill.length === 0 && collected.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: bodySize }}>
                        {u.record_rail_no_structured_yet ?? '暂无结构化字段；以对话与办公室整理为准。'}
                    </Text>
                ) : null}
                {groupedStill.length === 0 && collected.length > 0 ? (
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                        {u.simulation_no_missing ?? '系统未标额外缺项（办公室仍可能核对补问）。'}
                    </Text>
                ) : null}

                {showUpdateSection && (
                    <>
                        <Divider style={{ margin: '12px 0' }} />
                        <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginBottom: 6 }}>
                            {sectionUpdate}
                        </Text>
                        {showCorrectionBanner && (
                            <>
                                <Text style={{ fontSize: bodySize, lineHeight: 1.55, display: 'block', marginBottom: 4 }}>
                                    {u.record_rail_correction_detected_short ?? '本轮检测到客户更正或补充说明。'}
                                </Text>
                                <Text style={{ fontSize: bodySize, lineHeight: 1.55, display: 'block' }}>
                                    {u.record_rail_correction_absorbed_note ??
                                        '上文「系统已收到的要点」为最新整理结果，覆盖此前同字段理解（不展示逐字段旧值以免误导）。'}
                                </Text>
                            </>
                        )}
                        {showNewCollected && (
                            <Space size={4} wrap style={{ marginTop: showCorrectionBanner ? 8 : 0 }}>
                                <Text style={{ fontSize: bodySize }}>{u.record_rail_newly_recorded_prefix ?? '本回合新记入：'}</Text>
                                {newKeys.map((k) => (
                                    <Tag key={k} color="blue">
                                        {railFieldLabel(k)}
                                    </Tag>
                                ))}
                            </Space>
                        )}
                        {clearedStill.length > 0 && (
                            <div style={{ marginTop: showCorrectionBanner || showNewCollected ? 8 : 0 }}>
                                <Text style={{ fontSize: bodySize, display: 'block', marginBottom: 4 }}>
                                    {u.record_rail_still_cleared_subheading ?? '本轮起不再标缺：'}
                                </Text>
                                <Space size={4} wrap>
                                    {clearedStill.map((k) => (
                                        <Tag key={k} color="cyan">
                                            {railFieldLabel(k)}
                                        </Tag>
                                    ))}
                                </Space>
                            </div>
                        )}
                        {addedStill.length > 0 && (
                            <div style={{ marginTop: 8 }}>
                                <Text style={{ fontSize: bodySize, display: 'block', marginBottom: 4 }}>
                                    {u.record_rail_still_added_subheading ?? '本轮新增缺项标记：'}
                                </Text>
                                <Space size={4} wrap>
                                    {addedStill.map((k) => (
                                        <Tag key={k} color="orange">
                                            {railFieldLabel(k)}
                                        </Tag>
                                    ))}
                                </Space>
                            </div>
                        )}
                    </>
                )}

                {showImpactSection && (
                    <>
                        <Divider style={{ margin: '12px 0' }} />
                        <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginBottom: 6 }}>
                            {u.record_rail_impact_section_title ?? '对当前步骤与缺项的含义'}
                        </Text>
                        {impactLines.map((line, i) => (
                            <Text key={i} style={{ fontSize: bodySize, lineHeight: 1.55, display: 'block' }}>
                                {line}
                            </Text>
                        ))}
                    </>
                )}

                <Divider style={{ margin: '12px 0' }} />
                <Text type="secondary" style={{ fontSize: titleSize, display: 'block', marginBottom: 6 }}>
                    {sectionNext}
                </Text>
                <Text strong style={{ fontSize: bodySize, display: 'block', lineHeight: 1.55 }}>
                    {ownerLine}
                </Text>
                {mode !== 'simulation' && (
                    <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block', marginTop: 6 }}>
                        {appendCustomer} {appendOffice}
                    </Text>
                )}
            </div>
        </Space>
    );
}

/** Post-handoff: grouped snapshot only (inside green card); flow explainer stays outside. */
export function AddCarHandoffGroupedSnapshot({
    triage,
    priorSystemTriage,
    uiCopy,
}: {
    triage: TriageResult;
    priorSystemTriage?: TriageResult | null;
    uiCopy: UiCopy;
}) {
    const u = uiCopy;
    const {
        collected,
        still,
        newKeys,
        clearedStill,
        addedStill,
        showCorrectionBanner,
        showNewCollected,
        showUpdateSection,
        understoodLead,
        showUnderstoodLead,
        impactLines,
        showImpactSection,
    } = buildAddCarRailTurnModel(triage, priorSystemTriage, u);

    const sectionReceived = u.record_rail_section_received ?? '系统已收到的要点';
    const sectionMissing = u.record_rail_section_still_needed ?? '仍缺项（报价准备前）';
    const sectionUpdate = u.record_rail_section_latest_update ?? '本轮更新 / 更正';

    const gCol = groupAddCarRailFields(collected);
    const gStill = groupAddCarRailFields(still);

    return (
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
            {gCol.length === 0 && gStill.length === 0 ? (
                <Text type="secondary" style={{ fontSize: 12 }}>
                    {u.record_rail_no_structured_yet ?? '暂无结构化字段；以对话与办公室整理为准。'}
                </Text>
            ) : (
                <>
                    {showUnderstoodLead && (
                        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block' }}>
                            {understoodLead}
                        </Text>
                    )}
                    <GroupedFieldBlock title={sectionReceived} groups={gCol} color="green" />
                    <Divider style={{ margin: '4px 0' }} />
                    <GroupedFieldBlock title={sectionMissing} groups={gStill} color="orange" />
                </>
            )}
            {showUpdateSection && (
                <div>
                    <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                        {sectionUpdate}
                    </Text>
                    {showCorrectionBanner && (
                        <>
                            <Text style={{ fontSize: 13, lineHeight: 1.55, display: 'block', marginBottom: 4 }}>
                                {u.record_rail_correction_detected_short ?? '本轮检测到客户更正或补充说明。'}
                            </Text>
                            <Text style={{ fontSize: 13, lineHeight: 1.55, display: 'block' }}>
                                {u.record_rail_correction_absorbed_note ??
                                    '上文「系统已收到的要点」为最新整理结果，覆盖此前同字段理解（不展示逐字段旧值以免误导）。'}
                            </Text>
                        </>
                    )}
                    {showNewCollected && (
                        <Space size={4} wrap style={{ marginTop: showCorrectionBanner ? 8 : 0 }}>
                            <Text style={{ fontSize: 13 }}>{u.record_rail_newly_recorded_prefix ?? '本回合新记入：'}</Text>
                            {newKeys.map((k) => (
                                <Tag key={k} color="blue">
                                    {railFieldLabel(k)}
                                </Tag>
                            ))}
                        </Space>
                    )}
                    {clearedStill.length > 0 && (
                        <div style={{ marginTop: showCorrectionBanner || showNewCollected ? 8 : 0 }}>
                            <Text style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                                {u.record_rail_still_cleared_subheading ?? '本轮起不再标缺：'}
                            </Text>
                            <Space size={4} wrap>
                                {clearedStill.map((k) => (
                                    <Tag key={k} color="cyan">
                                        {railFieldLabel(k)}
                                    </Tag>
                                ))}
                            </Space>
                        </div>
                    )}
                    {addedStill.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                            <Text style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                                {u.record_rail_still_added_subheading ?? '本轮新增缺项标记：'}
                            </Text>
                            <Space size={4} wrap>
                                {addedStill.map((k) => (
                                    <Tag key={k} color="orange">
                                        {railFieldLabel(k)}
                                    </Tag>
                                ))}
                            </Space>
                        </div>
                    )}
                </div>
            )}
            {showImpactSection && (
                <div>
                    <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                        {u.record_rail_impact_section_title ?? '对当前步骤与缺项的含义'}
                    </Text>
                    {impactLines.map((line, i) => (
                        <Text key={i} style={{ fontSize: 13, lineHeight: 1.55, display: 'block' }}>
                            {line}
                        </Text>
                    ))}
                </div>
            )}
            {isFormalSubmissionToOfficeComplete(triage) &&
                (triage.formal_submitted_at || triage.created_at || triage.updated_at) && (
                    <>
                        <Divider style={{ margin: '8px 0' }} />
                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                            {u.record_rail_timing_section_title ?? '时间与活动'}
                        </Text>
                        {(() => {
                            const f = formatHandoffRailDateTime(
                                triage.formal_submitted_at ?? triage.created_at,
                            );
                            const a = formatHandoffRailDateTime(triage.updated_at);
                            const showBoth = Boolean(f && a && f !== a);
                            if (showBoth) {
                                return (
                                    <>
                                        <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.55, display: 'block' }}>
                                            {u.portal_formal_submitted_at_label ?? '正式送达办公室（首次进入办公室队列）'}：{f}
                                        </Text>
                                        <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.55, display: 'block' }}>
                                            {u.portal_last_activity_at_label ?? '最近活动（系统更新时间）'}：{a}
                                        </Text>
                                    </>
                                );
                            }
                            if (f) {
                                return (
                                    <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.55, display: 'block' }}>
                                        {u.portal_formal_submitted_at_label ?? '正式送达办公室（首次进入办公室队列）'}：{f}
                                    </Text>
                                );
                            }
                            return (
                                <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.55, display: 'block' }}>
                                    {u.portal_last_activity_at_label ?? '最近活动（系统更新时间）'}：{a}
                                </Text>
                            );
                        })()}
                    </>
                )}
        </Space>
    );
}
