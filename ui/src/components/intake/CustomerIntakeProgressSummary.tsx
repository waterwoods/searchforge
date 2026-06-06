/**
 * Customer-facing intake progress — percentage + collected/missing checklist.
 * Uses triage.collected_fields / still_needed_fields only (no backend changes).
 */
import { Space, Typography } from 'antd';
import type { TriageResult } from '../../api/inboxTriage';
import {
    computeIntakeProgressPercent,
    uniqueCustomerProgressLabels,
} from './customerPortalPresentation';

const { Text } = Typography;

type Props = {
    triage: TriageResult;
};

function ChecklistBlock({
    heading,
    items,
    symbol,
    color,
}: {
    heading: string;
    items: string[];
    symbol: string;
    color: string;
}) {
    if (items.length === 0) return null;
    return (
        <div>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                {heading}
            </Text>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
                {items.map((label) => (
                    <Text key={label} style={{ fontSize: 14, color, display: 'block', lineHeight: 1.5 }}>
                        {symbol} {label}
                    </Text>
                ))}
            </Space>
        </div>
    );
}

export function CustomerIntakeProgressSummary({ triage }: Props) {
    const collected = triage.collected_fields?.filter(Boolean) ?? [];
    const stillNeeded = triage.still_needed_fields?.filter(Boolean) ?? [];
    const percent = computeIntakeProgressPercent(collected, stillNeeded);
    const collectedLabels = uniqueCustomerProgressLabels(collected);
    const missingLabels = uniqueCustomerProgressLabels(stillNeeded);

    if (collectedLabels.length === 0 && missingLabels.length === 0) return null;

    return (
        <div
            style={{
                padding: '12px 14px',
                background: '#fff',
                borderRadius: 8,
                border: '1px solid #f0f0f0',
            }}
        >
            <Text strong style={{ fontSize: 15, display: 'block', marginBottom: 10, color: '#262626' }}>
                进度 {percent}%
            </Text>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <ChecklistBlock heading="已收集：" items={collectedLabels} symbol="✓" color="#389e0d" />
                <ChecklistBlock heading="还缺：" items={missingLabels} symbol="○" color="#8c8c8c" />
            </Space>
        </div>
    );
}
