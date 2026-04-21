/**
 * Simulation / demo: surfaces backend progression signals (case_usable, action_ready, milestones, field strategy).
 * Defensive against older or partial API payloads.
 */
import { Space, Tag, Typography } from 'antd';
import type { TriageResult } from '../../api/inboxTriage';
import { railFieldLabel } from '../intake/addCarRecordRailLabels';

const { Text } = Typography;

export function milestoneLabelZh(milestone: string | undefined): string {
    const map: Record<string, string> = {
        collecting: '收集中',
        near_usable: '接近可用',
        usable: '案例可用',
        action_ready: '可推进',
    };
    if (!milestone) return '未知';
    return map[milestone] ?? milestone;
}

/** Structured keys from case_draft.known_fields (post-merge / OCR-aware view). */
export function extractedFieldKeysFromTriage(triage: TriageResult | undefined): string[] {
    const k = triage?.case_draft?.known_fields;
    if (!k || typeof k !== 'object') return [];
    return Object.keys(k).filter(Boolean).sort();
}

function formatFieldList(ids: string[] | undefined, max: number): string {
    const arr = (ids ?? []).filter(Boolean);
    if (arr.length === 0) return '';
    const labels = arr.slice(0, max).map(railFieldLabel);
    return labels.join('、') + (arr.length > max ? '…' : '');
}

/** One-line human read for demo/debug (Chinese). */
export function buildCaseProgressionExplanation(triage: TriageResult | undefined): string {
    if (!triage) return '尚未开始；无 triage 结果。';
    const uf = triage.still_needed_user_flow?.filter(Boolean) ?? [];
    const def = triage.deferred_to_broker_fields?.filter(Boolean) ?? [];
    const col = triage.collected_fields?.filter(Boolean) ?? [];

    if (triage.action_ready === true) {
        return '信息已足够，系统判定可推进（action_ready）。';
    }
    if (uf.length > 0) {
        const need = formatFieldList(uf, 6);
        const got = formatFieldList(col, 5);
        const prefix = got ? `${got} 已获取，仍缺 ${need}` : `仍缺用户侧：${need}`;
        return def.length > 0 ? `${prefix}；部分信息可由办公室补全` : prefix;
    }
    if (triage.case_usable === true) {
        return def.length > 0
            ? '案例已达可用结构；部分信息 deferred 给办公室'
            : '案例已达可用结构；用户路径无强制缺项';
    }
    if (def.length > 0 && col.length > 0) {
        const d = formatFieldList(def, 4);
        return `已收集 ${formatFieldList(col, 6)}；${d || '部分要点'}可由办公室补全`;
    }
    if (col.length > 0) {
        return `已收集 ${formatFieldList(col, 8)}；继续对话或材料以推进里程碑。`;
    }
    return '系统仍在收集要点；请看下方结构化字段与里程碑。';
}

function triBoolZh(v: boolean | undefined): { text: string; ok: boolean | null } {
    if (v === true) return { text: '是', ok: true };
    if (v === false) return { text: '否', ok: false };
    return { text: '未知', ok: null };
}

type StripProps = { triage: TriageResult; compact?: boolean };

export function CaseProgressionStatusStrip({ triage, compact }: StripProps) {
    const fs = compact ? 11 : 12;
    const cu = triBoolZh(triage.case_usable);
    const ar = triBoolZh(triage.action_ready);
    return (
        <div>
            <Text type="secondary" style={{ fontSize: fs, display: 'block', marginBottom: 6, fontWeight: 600 }}>
                进度里程碑
            </Text>
            <Space wrap size={[4, 4]}>
                <Tag color="blue">{milestoneLabelZh(triage.intake_flow_milestone)}</Tag>
                <Tag color={cu.ok === true ? 'green' : cu.ok === false ? 'default' : 'orange'}>
                    case_usable {cu.text}
                </Tag>
                <Tag color={ar.ok === true ? 'green' : ar.ok === false ? 'default' : 'orange'}>
                    action_ready {ar.text}
                </Tag>
            </Space>
        </div>
    );
}

function fieldTagRow(title: string, emoji: string, keys: string[], emptyNote: string) {
    return (
        <div>
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                {emoji} {title}
            </Text>
            {keys.length > 0 ? (
                <Space size={4} wrap>
                    {keys.map((k) => (
                        <Tag key={k} color="default" style={{ margin: 0 }}>
                            {railFieldLabel(k)}
                        </Tag>
                    ))}
                </Space>
            ) : (
                <Text type="secondary" style={{ fontSize: 12 }}>
                    {emptyNote}
                </Text>
            )}
        </div>
    );
}

export function CaseProgressionFieldPanel({ triage }: StripProps) {
    const collected = triage.collected_fields?.filter(Boolean) ?? [];
    const userFlow = triage.still_needed_user_flow?.filter(Boolean) ?? [];
    const broker = triage.deferred_to_broker_fields?.filter(Boolean) ?? [];
    return (
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
            {fieldTagRow('已收集（collected_fields）', '✅', collected, '—')}
            {fieldTagRow('仍缺用户路径（still_needed_user_flow）', '❗', userFlow, '—')}
            {fieldTagRow('办公室补全（deferred_to_broker_fields）', '🧠', broker, '—')}
        </Space>
    );
}

export function CaseProgressionExplanationLine({ triage }: { triage: TriageResult }) {
    return (
        <div
            style={{
                padding: '8px 10px',
                background: '#fafafa',
                borderRadius: 6,
                border: '1px solid #f0f0f0',
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                系统理解（一句话）
            </Text>
            <Text style={{ fontSize: 13, color: '#262626', lineHeight: 1.55 }}>
                {buildCaseProgressionExplanation(triage)}
            </Text>
        </div>
    );
}

export function CaseProgressionVisibilityBlock({ triage, compact = true }: StripProps) {
    return (
        <Space direction="vertical" size={10} style={{ width: '100%' }}>
            <CaseProgressionStatusStrip triage={triage} compact={compact} />
            <CaseProgressionFieldPanel triage={triage} compact={compact} />
            <CaseProgressionExplanationLine triage={triage} />
        </Space>
    );
}

export type ReplayStepIntelProps = {
    triage: TriageResult;
    /** Prior customer line for this triage step, if any */
    userInput?: string;
};

/** Inner content for replay accordion: mirrors main visibility at a single step. */
export function ReplayStepIntelPanel({ triage, userInput }: ReplayStepIntelProps) {
    const extracted = extractedFieldKeysFromTriage(triage);
    const collected = triage.collected_fields?.filter(Boolean) ?? [];
    const userFlow = triage.still_needed_user_flow?.filter(Boolean) ?? [];
    const broker = triage.deferred_to_broker_fields?.filter(Boolean) ?? [];
    return (
        <Space direction="vertical" size={8} style={{ width: '100%' }}>
            {userInput ? (
                <div>
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                        用户输入
                    </Text>
                    <Text style={{ fontSize: 12, lineHeight: 1.55, whiteSpace: 'pre-wrap', color: '#262626' }}>
                        {(userInput || '').trim() || '—'}
                    </Text>
                </div>
            ) : null}
            <div>
                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                    提取 / 已知（case_draft.known_fields）
                </Text>
                {extracted.length > 0 ? (
                    <Space size={4} wrap>
                        {extracted.map((k) => (
                            <Tag key={k} color="processing" style={{ margin: 0 }}>
                                {railFieldLabel(k)}
                            </Tag>
                        ))}
                    </Space>
                ) : (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        —
                    </Text>
                )}
            </div>
            <CaseProgressionStatusStrip triage={triage} compact />
            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                {fieldTagRow('本步后 · collected_fields', '✅', collected, '—')}
                {fieldTagRow('本步后 · still_needed_user_flow', '❗', userFlow, '—')}
                {fieldTagRow('本步后 · deferred_to_broker_fields', '🧠', broker, '—')}
            </Space>
            <CaseProgressionExplanationLine triage={triage} />
        </Space>
    );
}
