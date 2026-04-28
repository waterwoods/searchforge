import { Tag, Typography } from 'antd';
import type { TriageResult } from '../../../api/inboxTriage';
import { buildAddCarStatusStripChips, buildGenericIntakeStatusChips } from '../utils/intakePure';

const { Text } = Typography;

export function AddCarCaseStatusStrip({
    triage,
    phase,
    caption,
}: {
    triage: TriageResult | null | undefined;
    phase: 'intake' | 'submitted';
    caption?: string;
}) {
    const chips = buildAddCarStatusStripChips(triage, phase);
    const bg = phase === 'submitted' ? '#f6ffed' : '#f0f5ff';
    const borderColor = phase === 'submitted' ? '#b7eb8f' : '#adc6ff';
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                alignItems: 'center',
                padding: '10px 12px',
                background: bg,
                borderRadius: 8,
                border: `1px solid ${borderColor}`,
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 12, fontWeight: 700, letterSpacing: 0.2 }}>
                {caption ?? '当前状态'}
            </Text>
            {chips.map((c, i) => (
                <Tag key={`${c.label}-${i}`} color={c.color} style={{ margin: 0, fontSize: 12 }}>
                    {c.label}
                </Tag>
            ))}
        </div>
    );
}

export function GenericIntakeStatusStrip({
    triage,
    caption,
}: {
    triage: TriageResult | null | undefined;
    caption?: string;
}) {
    if (!triage) return null;
    const chips = buildGenericIntakeStatusChips(triage);
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                alignItems: 'center',
                padding: '10px 12px',
                background: '#fafafa',
                borderRadius: 8,
                border: '1px solid #d9d9d9',
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
                {caption ?? '当前状态'}
            </Text>
            {chips.map((c, i) => (
                <Tag key={`${c.label}-${i}`} color={c.color} style={{ margin: 0, fontSize: 12 }}>
                    {c.label}
                </Tag>
            ))}
        </div>
    );
}

/** Amazon-style: one clear transaction path (3 beats). */
export function IntakeFlowStepTrack({
    flowStep,
    trackLabel,
    step1,
    step2,
    step3,
}: {
    flowStep: 1 | 2 | 3;
    trackLabel: string;
    step1: string;
    step2: string;
    step3: string;
}) {
    const steps: Array<{ n: 1 | 2 | 3; label: string }> = [
        { n: 1, label: step1 },
        { n: 2, label: step2 },
        { n: 3, label: step3 },
    ];
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 8,
                padding: '10px 12px',
                background: '#fcfcfc',
                borderRadius: 8,
                border: '1px solid #f0f0f0',
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
                {trackLabel}
            </Text>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
                {steps.map((s, idx) => {
                    const active = flowStep === s.n;
                    const done = flowStep > s.n;
                    return (
                        <span key={s.n} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                            {idx > 0 ? (
                                <Text type="secondary" style={{ fontSize: 12, userSelect: 'none' }}>
                                    →
                                </Text>
                            ) : null}
                            <Tag
                                color={done ? 'success' : active ? 'processing' : 'default'}
                                style={{ margin: 0, fontSize: 12, fontWeight: active ? 600 : 400 }}
                            >
                                {s.n}. {s.label}
                            </Tag>
                        </span>
                    );
                })}
            </div>
        </div>
    );
}
