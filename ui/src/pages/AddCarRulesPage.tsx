/**
 * Add-Car Quote Rules Center — Minimal business rules editor
 *
 * Lets Chen Kui and assistants view, edit, and preview Add-Car Quote flow rules
 * without touching code. Business-friendly labels only.
 */
import { useEffect, useState } from 'react';
import {
    Alert,
    Badge,
    Button,
    Card,
    Col,
    Input,
    Row,
    Space,
    Spin,
    Tooltip,
    Typography,
    message,
} from 'antd';
import { EditOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import {
    getAddCarRules,
    previewAddCarRules,
    publishAddCarRules,
    type AddCarRules,
    type AddCarRulesOverride,
    type TriageResult,
} from '../api/inboxTriage';

const { TextArea } = Input;
const { Title, Text } = Typography;

const PREVIEW_EXAMPLES: Array<{
    label: string;
    text: string;
    turns?: Array<{ role: 'customer' | 'system'; text: string }>;
}> = [
    { label: '我想加一台X5', text: '我想加一台X5' },
    {
        label: '多轮：2024 90210',
        text: '2024 90210',
        turns: [
            { role: 'customer' as const, text: '我想加一台X5' },
            { role: 'system' as const, text: '先把年份和地址邮编发我，我就能帮你算报价。' },
        ],
    },
    { label: '2024 宝马X5', text: '2024 宝马X5' },
    { label: '90210', text: '90210' },
];

export default function AddCarRulesPage() {
    const [rules, setRules] = useState<AddCarRules | null>(null);
    const [draft, setDraft] = useState<AddCarRulesOverride | null>(null);
    const [loading, setLoading] = useState(true);
    const [previewText, setPreviewText] = useState('我想加一台X5');
    const [previewTurns, setPreviewTurns] = useState<Array<{ role: 'customer' | 'system'; text: string }> | undefined>();
    const [previewResult, setPreviewResult] = useState<TriageResult | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [publishLoading, setPublishLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadRules = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getAddCarRules();
            setRules(data);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Failed to load rules');
            message.error('加载规则失败');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRules();
    }, []);

    const runPreview = async () => {
        setPreviewResult(null);
        if (!previewText.trim()) {
            message.warning('请输入预览内容');
            return;
        }
        setPreviewLoading(true);
        try {
            const result = await previewAddCarRules(
                previewText.trim(),
                previewTurns,
                draft && (draft.ask_vehicle || draft.ask_zip || draft.ask_delivery_driver) ? draft : undefined,
            );
            setPreviewResult(result);
        } catch (e: unknown) {
            message.error('预览失败');
            setPreviewResult(null);
        } finally {
            setPreviewLoading(false);
        }
    };

    const updateDraft = (key: keyof AddCarRulesOverride, lang: 'zh' | 'en', value: string) => {
        setDraft((prev) => {
            const next = prev ? { ...prev } : {};
            const entry = next[key] || { zh: '', en: '' };
            next[key] = { ...entry, [lang]: value };
            return next;
        });
    };

    const getDisplayValue = (key: keyof AddCarRules, lang: 'zh' | 'en'): string => {
        const d = draft?.[key as keyof AddCarRulesOverride];
        if (d?.[lang]) return d[lang];
        return rules?.[key]?.[lang] ?? '';
    };

    const handlePublish = async () => {
        if (!rules) return;
        const toPublish = {
            ask_vehicle: {
                zh: getDisplayValue('ask_vehicle', 'zh') || rules.ask_vehicle.zh,
                en: getDisplayValue('ask_vehicle', 'en') || rules.ask_vehicle.en,
            },
            ask_zip: {
                zh: getDisplayValue('ask_zip', 'zh') || rules.ask_zip.zh,
                en: getDisplayValue('ask_zip', 'en') || rules.ask_zip.en,
            },
            ask_delivery_driver: {
                zh: getDisplayValue('ask_delivery_driver', 'zh') || rules.ask_delivery_driver.zh,
                en: getDisplayValue('ask_delivery_driver', 'en') || rules.ask_delivery_driver.en,
            },
        };
        setPublishLoading(true);
        try {
            await publishAddCarRules(toPublish);
            message.success('规则已发布');
            setDraft(null);
            await loadRules();
        } catch (e: unknown) {
            message.error(e instanceof Error ? e.message : '发布失败');
        } finally {
            setPublishLoading(false);
        }
    };

    const handleRestore = async () => {
        setDraft(null);
        await loadRules();
        message.info('已恢复为已发布版本');
    };

    if (loading) {
        return (
            <div style={{ padding: 24, textAlign: 'center' }}>
                <Spin size="large" />
            </div>
        );
    }

    if (error || !rules) {
        return (
            <div style={{ padding: 24 }}>
                <Alert
                    type="error"
                    message={error || '规则加载失败'}
                    action={
                        <Button onClick={loadRules} icon={<ReloadOutlined />}>
                            重试
                        </Button>
                    }
                />
            </div>
        );
    }

    const publishable = rules.publishable === true;

    return (
        <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
            <Space align="center" wrap style={{ marginBottom: 8 }}>
                <Title level={3} style={{ margin: 0 }}>加车报价流程规则</Title>
                {!publishable && (
                    <Badge status="warning" text="预览模式" />
                )}
            </Space>
            <Text type="secondary" style={{ display: 'block' }}>
                可编辑加车报价流程中的回复文案，预览效果后再发布。当前仅支持下一步提示语的编辑。
            </Text>

            <Row gutter={24} style={{ marginTop: 24 }}>
                {/* Current rules / Editable */}
                <Col xs={24} lg={12}>
                    <Card
                        title={
                            <Space>
                                <EditOutlined />
                                可编辑规则
                            </Space>
                        }
                        size="small"
                    >
                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                            <div>
                                <Text strong>缺年份车型时问什么（中文）</Text>
                                <Input
                                    value={getDisplayValue('ask_vehicle', 'zh')}
                                    onChange={(e) => updateDraft('ask_vehicle', 'zh', e.target.value)}
                                    placeholder="先把年份和车型发我，我就能帮你算。"
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                            <div>
                                <Text strong>缺年份车型时问什么（英文）</Text>
                                <Input
                                    value={getDisplayValue('ask_vehicle', 'en')}
                                    onChange={(e) => updateDraft('ask_vehicle', 'en', e.target.value)}
                                    placeholder="Send me the year and make/model first..."
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                            <div>
                                <Text strong>缺邮编时问什么（中文）</Text>
                                <Input
                                    value={getDisplayValue('ask_zip', 'zh')}
                                    onChange={(e) => updateDraft('ask_zip', 'zh', e.target.value)}
                                    placeholder="先把地址邮编发我，我就能帮你算。"
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                            <div>
                                <Text strong>缺邮编时问什么（英文）</Text>
                                <Input
                                    value={getDisplayValue('ask_zip', 'en')}
                                    onChange={(e) => updateDraft('ask_zip', 'en', e.target.value)}
                                    placeholder="Send me the zip or address first..."
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                            <div>
                                <Text strong>缺提车/驾驶人时问什么（中文）</Text>
                                <Input
                                    value={getDisplayValue('ask_delivery_driver', 'zh')}
                                    onChange={(e) => updateDraft('ask_delivery_driver', 'zh', e.target.value)}
                                    placeholder="提车日期和主要驾驶人发我一下，我好安排报价。"
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                            <div>
                                <Text strong>缺提车/驾驶人时问什么（英文）</Text>
                                <Input
                                    value={getDisplayValue('ask_delivery_driver', 'en')}
                                    onChange={(e) => updateDraft('ask_delivery_driver', 'en', e.target.value)}
                                    placeholder="Send me the delivery date and main driver..."
                                    style={{ marginTop: 4 }}
                                />
                            </div>
                        </Space>
                    </Card>

                    <Space style={{ marginTop: 16 }}>
                        {publishable ? (
                            <Button type="primary" onClick={handlePublish} loading={publishLoading}>
                                发布
                            </Button>
                        ) : (
                            <Tooltip title="此环境为预览模式，无法保存到配置。如需正式发布，请在本地环境操作。">
                                <span>
                                    <Button type="primary" disabled>
                                        发布（不可用）
                                    </Button>
                                </span>
                            </Tooltip>
                        )}
                        <Button onClick={handleRestore} icon={<ReloadOutlined />}>
                            恢复已发布版本
                        </Button>
                    </Space>

                    <Card title="当前流程（只读）" size="small" style={{ marginTop: 16 }}>
                        <Text type="secondary">
                            收集顺序：年份车型 → 邮编 → 提车日期/驾驶人 → 转办公室
                        </Text>
                        <br />
                        <Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
                            转办公室条件：有车 + 邮编 +（提车或驾驶人）
                        </Text>
                    </Card>
                </Col>

                {/* Preview */}
                <Col xs={24} lg={12}>
                    <Card
                        title={
                            <Space>
                                <EyeOutlined />
                                流程预览
                            </Space>
                        }
                        size="small"
                    >
                        <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                            输入客户消息，查看系统会如何回复（使用当前编辑的规则）
                        </Text>
                        <TextArea
                            value={previewText}
                            onChange={(e) => setPreviewText(e.target.value)}
                            placeholder="例如：我想加一台X5"
                            rows={2}
                            style={{ marginBottom: 8 }}
                        />
                        <Space wrap style={{ marginBottom: 12 }}>
                            {PREVIEW_EXAMPLES.map((ex) => (
                                <Button
                                    key={ex.label}
                                    size="small"
                                    onClick={() => {
                                        setPreviewText(ex.text);
                                        setPreviewTurns(ex.turns);
                                    }}
                                >
                                    {ex.label}
                                </Button>
                            ))}
                        </Space>
                        <Button type="primary" onClick={runPreview} loading={previewLoading}>
                            预览
                        </Button>

                        {previewResult && (
                            <Card
                                size="small"
                                title="预览结果"
                                style={{ marginTop: 16 }}
                                styles={{ body: { background: '#1a1a1a', borderRadius: 4 } }}
                            >
                                <Text strong>系统回复：</Text>
                                <div
                                    style={{
                                        marginTop: 8,
                                        padding: 12,
                                        background: '#0d0d0d',
                                        borderRadius: 4,
                                        whiteSpace: 'pre-wrap',
                                    }}
                                >
                                    {previewResult.client_reply_draft || '（无）'}
                                </div>
                                {previewResult.collected_fields && previewResult.collected_fields.length > 0 && (
                                    <div style={{ marginTop: 12 }}>
                                        <Text strong>已收集：</Text>{' '}
                                        {previewResult.collected_fields.join(', ')}
                                    </div>
                                )}
                                {previewResult.still_needed_fields &&
                                    previewResult.still_needed_fields.length > 0 && (
                                        <div style={{ marginTop: 4 }}>
                                            <Text strong>还需：</Text>{' '}
                                            {previewResult.still_needed_fields.join(', ')}
                                        </div>
                                    )}
                                {previewResult.handoff_ready && (
                                    <div style={{ marginTop: 8 }}>
                                        <Text type="success">✓ 可转办公室</Text>
                                    </div>
                                )}
                            </Card>
                        )}
                    </Card>

                    {publishable ? (
                        <Alert
                            type="info"
                            message="草稿与发布"
                            description="编辑后点击「预览」查看效果。确认无误后点击「发布」保存到配置。发布后，Unified Intake 将使用新规则。"
                            style={{ marginTop: 16 }}
                            showIcon
                        />
                    ) : (
                        <Alert
                            type="warning"
                            message="预览模式"
                            description="此环境为预览模式。可编辑和预览，但无法在此保存到配置。如需正式发布，请在本地环境操作。"
                            style={{ marginTop: 16 }}
                            showIcon
                        />
                    )}
                </Col>
            </Row>
        </div>
    );
}
