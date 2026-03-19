/**
 * Scenario Logic Center — Founder/broker review page
 *
 * Shows what scenarios exist, how they work, what is strong/weak.
 * Read-only; no rules editing. Clearer, not heavier.
 */
import { useEffect, useState } from 'react';
import {
    Alert,
    Card,
    Collapse,
    Descriptions,
    Space,
    Spin,
    Tag,
    Typography,
} from 'antd';
import {
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    InfoCircleOutlined,
    UnorderedListOutlined,
} from '@ant-design/icons';
import { getScenarioLogicCenter, type ScenarioLogicCenter, type ScenarioLogicItem } from '../api/inboxTriage';

const { Title, Text } = Typography;

function MaturityBadge({ maturity }: { maturity: string }) {
    if (maturity === 'strong') {
        return (
            <Tag color="success" icon={<CheckCircleOutlined />}>
                Strong
            </Tag>
        );
    }
    if (maturity === 'medium') {
        return (
            <Tag color="processing" icon={<InfoCircleOutlined />}>
                Medium
            </Tag>
        );
    }
    return (
        <Tag color="default" icon={<ExclamationCircleOutlined />}>
            Weak
        </Tag>
    );
}

function FixStatusBadge({ fixStatus }: { fixStatus: string | null }) {
    if (!fixStatus) return null;
    if (fixStatus === 'fix_now') {
        return <Tag color="error">Fix now</Tag>;
    }
    if (fixStatus === 'fix_next') {
        return <Tag color="warning">Fix next</Tag>;
    }
    if (fixStatus === 'defer') {
        return <Tag color="default">Defer</Tag>;
    }
    return null;
}

function ScenarioCard({ scenario, groupLabel }: { scenario: ScenarioLogicItem; groupLabel: string }) {
    return (
        <Card
            size="small"
            title={
                <Space wrap>
                    <span>{scenario.name}</span>
                    <MaturityBadge maturity={scenario.maturity} />
                    <FixStatusBadge fixStatus={scenario.fix_status} />
                    {scenario.trial_order != null && (
                        <Tag color="blue">Trial #{scenario.trial_order}</Tag>
                    )}
                    <Tag>{scenario.config_layer}</Tag>
                </Space>
            }
            extra={groupLabel}
            style={{ marginBottom: 12 }}
        >
            <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                {scenario.business_goal}
            </Text>
            <Collapse
                size="small"
                items={[
                    {
                        key: '1',
                        label: 'How recognized · Ask next · Handoff · Broker step',
                        children: (
                            <Descriptions size="small" column={1} bordered>
                                <Descriptions.Item label="Route">{scenario.main_route}</Descriptions.Item>
                                <Descriptions.Item label="Ask next">{scenario.ask_next}</Descriptions.Item>
                                <Descriptions.Item label="Handoff when">{scenario.handoff_timing}</Descriptions.Item>
                                <Descriptions.Item label="Broker next step">
                                    <Text strong>{scenario.broker_next_step}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Config sources">
                                    {(scenario.config_sources ?? []).join(', ')}
                                </Descriptions.Item>
                                {(scenario.common_phrasing ?? []).length > 0 && (
                                    <Descriptions.Item label="Example phrasing">
                                        {(scenario.common_phrasing ?? []).slice(0, 5).join(' · ')}
                                    </Descriptions.Item>
                                )}
                            </Descriptions>
                        ),
                    },
                ]}
            />
        </Card>
    );
}

export default function ScenarioLogicCenterPage() {
    const [data, setData] = useState<ScenarioLogicCenter | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setError(null);
        getScenarioLogicCenter()
            .then(setData)
            .catch((e: unknown) => {
                const msg =
                    (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                    (e instanceof Error ? e.message : String(e)) ||
                    'Failed to load Scenario Logic Center';
                setError(msg);
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Spin size="large" />
            </div>
        );
    }

    if (error || !data) {
        return (
            <div style={{ padding: 24 }}>
                <Alert
                    type="error"
                    message={error || 'Failed to load Scenario Logic Center'}
                    description="Ensure backend is running on port 8001 and configs/scenario_logic_center.json exists."
                />
            </div>
        );
    }

    const summary = data.summary || { total_scenarios: 0, strong: 0, medium: 0, weak: 0 };
    const groups = data.groups || {};
    const scenarios = data.scenarios || [];

    // Group scenarios
    const byGroup: Record<string, ScenarioLogicItem[]> = {};
    for (const s of scenarios) {
        const g = s.group || 'other';
        if (!byGroup[g]) byGroup[g] = [];
        byGroup[g].push(s);
    }

    const groupOrder = ['standard_package', 'extended', 'fallback'];
    const orderedGroups = groupOrder.filter((g) => byGroup[g]?.length);

    return (
        <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <div>
                    <Title level={3} style={{ margin: 0 }}>
                        <UnorderedListOutlined /> Scenario Logic Center
                    </Title>
                    <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                        Chen Kui Unified Intake — what scenarios exist, how they work, what is strong/weak
                    </Text>
                </div>

                <Card size="small">
                    <Space wrap>
                        <Text strong>Scenarios: {summary.total_scenarios}</Text>
                        <Tag color="success">Strong: {summary.strong}</Tag>
                        <Tag color="processing">Medium: {summary.medium}</Tag>
                        <Tag color="default">Weak: {summary.weak}</Tag>
                        {summary.trial_recommended && summary.trial_recommended.length > 0 && (
                            <Text type="secondary">Trial: {summary.trial_recommended.join(', ')}</Text>
                        )}
                    </Space>
                </Card>

                {orderedGroups.map((groupKey) => {
                    const items = byGroup[groupKey] || [];
                    const groupMeta = groups[groupKey];
                    const label = groupMeta?.label || groupKey;
                    const desc = groupMeta?.description;
                    return (
                        <div key={groupKey}>
                            <Title level={5} style={{ marginBottom: 8 }}>
                                {label}
                            </Title>
                            {desc && (
                                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                                    {desc}
                                </Text>
                            )}
                            {items.map((s) => (
                                <ScenarioCard key={s.id} scenario={s} groupLabel={label} />
                            ))}
                        </div>
                    );
                })}

                <Alert
                    type="info"
                    message="Config layers"
                    description={
                        <span>
                            <strong>industry</strong> = configs/industries/insurance/ (markers, reply_templates, category_templates).{' '}
                            <strong>client</strong> = configs/clients/chen_kui/ (handoff_phrases, reply_overrides).{' '}
                            New client = new folder + handoff_phrases.
                        </span>
                    }
                    showIcon
                    icon={<InfoCircleOutlined />}
                />

                <Alert
                    type="info"
                    message="Doc index"
                    description={
                        <span>
                            Full specs: <code>docs/scenario_logic_center/INDEX.md</code> — Blueprint, Inventory,
                            Visibility, Health, Founder Inspection Notes.
                        </span>
                    }
                    showIcon
                    icon={<InfoCircleOutlined />}
                />
            </Space>
        </div>
    );
}
