/**
 * User-facing case list + progress panel (Unified Intake — Add-Car pilot).
 * Uses persisted case payloads from GET /api/inbox/cases (SavedCase / CASE_CONTRACT_V1 fields).
 */
import { useCallback, useEffect, useMemo, useState, type CSSProperties } from 'react';
import { Button, Card, Col, Collapse, Empty, Row, Space, Spin, Tag, Typography } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import { listRecentCasesPage, type SavedCase } from '../../api/inboxTriage';
import { useClientConfig } from '../../context/ClientConfigContext';
import { groupAddCarRailFields, railFieldLabel } from './addCarRecordRailLabels';
import { caseLifecycleUserLabel, resolveCaseLifecycle } from './caseLifecycleDisplay';

const { Text, Title, Paragraph } = Typography;

const LIST_PAGE_SIZE = 30;

export function userFacingCaseTitle(c: SavedCase): string {
    const v = (c.primary_vehicle_summary || '').trim();
    if (v) {
        if (/加车|报价|车辆/i.test(v)) return v;
        return `加车 · ${v}`;
    }
    if (c.service_lane === 'add_car' || (c.service_type || '').toLowerCase().includes('add')) {
        return '加车申请';
    }
    return '服务申请';
}

function shortStatusHint(c: SavedCase): string {
    const n = c.still_needed_fields?.filter(Boolean).length ?? 0;
    if (n > 0) return `还差 ${n} 项`;
    return caseLifecycleUserLabel(resolveCaseLifecycle(c));
}

function formatLocalTime(iso: string | undefined): string {
    if (!iso) return '—';
    try {
        return new Date(iso).toLocaleString();
    } catch {
        return iso;
    }
}

function nextStepHint(c: SavedCase): string {
    const q = (c.next_best_question || '').trim();
    if (q) return q;
    const needed = c.still_needed_fields?.filter(Boolean) ?? [];
    const cl = resolveCaseLifecycle(c);
    if (needed.length > 0) {
        const labels = needed.slice(0, 4).map((id) => railFieldLabel(id));
        const more = needed.length > 4 ? ` 等共 ${needed.length} 项` : '';
        return `请先补充：${labels.join('、')}${more}。在「客户报送」输入即可写入同一条记录。`;
    }
    if (cl === 'ready_for_handoff') {
        return '要点已齐：请在「客户报送」点击「正式提交办公室」，将本条记录送达办公室。';
    }
    if (cl === 'submitted') {
        return '本条已送达办公室。若需补充同一车辆信息，请在「客户报送」追加到本条记录。';
    }
    return '可在「客户报送」继续本条办理。';
}

function filterUserVisibleCases(cases: SavedCase[], clientId: string): SavedCase[] {
    return cases.filter((c) => {
        if (c.workbench_test) return false;
        if (c.workbench_archived) return false;
        const cid = (c.client_id || '').trim();
        if (cid && clientId && cid !== clientId) return false;
        return true;
    });
}

export type UserCaseListProgressPanelProps = {
    onContinueInCustomerPortal?: (caseId: string) => void;
};

export function UserCaseListProgressPanel({ onContinueInCustomerPortal }: UserCaseListProgressPanelProps) {
    const { uiCopy, clientId } = useClientConfig();
    const heroTitle = uiCopy.portal_my_requests_hero_title ?? '我的办理进度';
    const heroSubtitle =
        uiCopy.portal_my_requests_hero_subtitle ??
        '查看已送达办公室的请求与待补充项。与客户报送使用同一条服务记录。';
    const listTitle = uiCopy.portal_my_requests_list_title ?? '进行中的请求';
    const emptyHint =
        uiCopy.portal_my_requests_empty_hint ??
        '还没有可在本页展示的记录。请先在「客户报送」完成办理并正式提交办公室。';
    const panelTitle = uiCopy.portal_my_requests_detail_title ?? '选中请求的进度';
    const collectedHeading = uiCopy.portal_my_requests_collected_heading ?? '已记录的信息';
    const missingHeading = uiCopy.portal_my_requests_missing_heading ?? '仍需要的信息';
    const nextHeading = uiCopy.portal_my_requests_next_heading ?? '建议下一步';
    const formalLabel = uiCopy.portal_formal_submitted_at_label ?? '正式送达办公室（首次）';
    const updatedLabel = uiCopy.portal_last_activity_at_label ?? '最近更新';
    const goChatCta = uiCopy.portal_my_requests_go_customer_cta ?? '去客户报送继续';

    const [loading, setLoading] = useState(true);
    const [cases, setCases] = useState<SavedCase[]>([]);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const visible = useMemo(() => filterUserVisibleCases(cases, clientId), [cases, clientId]);

    const load = useCallback(async () => {
        setLoading(true);
        setLoadError(null);
        try {
            const { cases: page } = await listRecentCasesPage({ limit: LIST_PAGE_SIZE, offset: 0 });
            setCases(page);
        } catch (e: unknown) {
            const msg =
                (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? '加载失败';
            setLoadError(typeof msg === 'string' ? msg : '加载失败');
            setCases([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        const onFocus = () => void load();
        window.addEventListener('focus', onFocus);
        return () => window.removeEventListener('focus', onFocus);
    }, [load]);

    useEffect(() => {
        if (!visible.length) {
            setSelectedId(null);
            return;
        }
        if (!selectedId || !visible.some((c) => c.case_id === selectedId)) {
            setSelectedId(visible[0].case_id);
        }
    }, [visible, selectedId]);

    const selected = useMemo(
        () => visible.find((c) => c.case_id === selectedId) ?? null,
        [visible, selectedId],
    );

    const cardShell: CSSProperties = {
        background: '#fff',
        border: '1px solid #e8e8e8',
        borderRadius: 10,
        boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
    };

    const renderFieldChips = (ids: string[]) => {
        const groups = groupAddCarRailFields(ids);
        if (!groups.length) return <Text type="secondary">—</Text>;
        return (
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
                {groups.map((g) => (
                    <div key={g.title}>
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                            {g.title}
                        </Text>
                        <Space size={[4, 4]} wrap>
                            {g.keys.map((k) => (
                                <Tag key={k} style={{ margin: 0 }}>
                                    {railFieldLabel(k)}
                                </Tag>
                            ))}
                        </Space>
                    </div>
                ))}
            </Space>
        );
    };

    return (
        <div style={{ width: '100%', padding: '0 0 28px', boxSizing: 'border-box' }}>
            <div
                style={{
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: 12,
                    boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
                    padding: '26px 18px 30px',
                }}
            >
                <Space direction="vertical" size={20} style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
                        <Space align="start" size={10}>
                            <FileTextOutlined style={{ fontSize: 22, color: '#1677ff', marginTop: 2 }} />
                            <div style={{ minWidth: 0 }}>
                                <Title level={2} style={{ margin: 0, fontWeight: 600, color: '#262626', fontSize: 22 }}>
                                    {heroTitle}
                                </Title>
                            </div>
                        </Space>
                    </div>

                    <Row gutter={[16, 16]}>
                        <Col xs={24} lg={9}>
                            <Card size="small" style={cardShell} title={<Text strong>{listTitle}</Text>}>
                                {loadError ? (
                                    <Text type="danger">{loadError}</Text>
                                ) : loading && !cases.length ? (
                                    <div style={{ textAlign: 'center', padding: 24 }}>
                                        <Spin />
                                    </div>
                                ) : !visible.length ? (
                                    <Empty description={emptyHint} image={Empty.PRESENTED_IMAGE_SIMPLE} />
                                ) : (
                                    <Space direction="vertical" size={10} style={{ width: '100%' }}>
                                        {visible.map((c) => {
                                            const active = c.case_id === selectedId;
                                            return (
                                                <button
                                                    key={c.case_id}
                                                    type="button"
                                                    onClick={() => setSelectedId(c.case_id)}
                                                    style={{
                                                        width: '100%',
                                                        textAlign: 'left',
                                                        padding: '12px 14px',
                                                        borderRadius: 8,
                                                        border: active ? '1px solid #1677ff' : '1px solid #f0f0f0',
                                                        background: active ? '#e6f4ff' : '#fafafa',
                                                        cursor: 'pointer',
                                                        boxSizing: 'border-box',
                                                    }}
                                                >
                                                    <Text strong style={{ display: 'block', fontSize: 14, color: '#262626' }}>
                                                        {userFacingCaseTitle(c)}
                                                    </Text>
                                                    <Space size={6} wrap style={{ marginTop: 6 }}>
                                                        <Tag color="blue" style={{ margin: 0 }}>
                                                            {caseLifecycleUserLabel(resolveCaseLifecycle(c))}
                                                        </Tag>
                                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                                            {shortStatusHint(c)}
                                                        </Text>
                                                    </Space>
                                                </button>
                                            );
                                        })}
                                    </Space>
                                )}
                            </Card>
                        </Col>
                        <Col xs={24} lg={15}>
                            <Card size="small" style={cardShell} title={<Text strong>{panelTitle}</Text>}>
                                {!selected ? (
                                    <Empty description="请从左侧选择一条记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                                ) : (
                                    <Space direction="vertical" size={16} style={{ width: '100%' }}>
                                        <div>
                                            <Title level={4} style={{ margin: '0 0 8px', fontSize: 17 }}>
                                                {userFacingCaseTitle(selected)}
                                            </Title>
                                            <Space size={8} wrap align="center">
                                                <Tag color="processing">
                                                    {caseLifecycleUserLabel(resolveCaseLifecycle(selected))}
                                                </Tag>
                                            </Space>
                                        </div>

                                        <div
                                            style={{
                                                padding: '12px 14px',
                                                background: '#fafafa',
                                                borderRadius: 8,
                                                border: '1px solid #f0f0f0',
                                            }}
                                        >
                                            <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                                                {updatedLabel}
                                            </Text>
                                            <Text style={{ fontSize: 13 }}>{formatLocalTime(selected.updated_at)}</Text>
                                        </div>

                                        {(selected.collected_fields?.filter(Boolean).length ?? 0) > 0 && (
                                            <Collapse
                                                bordered={false}
                                                style={{ background: 'transparent' }}
                                                defaultActiveKey={[]}
                                                items={[
                                                    {
                                                        key: 'collected',
                                                        label: (
                                                            <Text style={{ fontSize: 13 }}>
                                                                {collectedHeading}（{selected.collected_fields!.filter(Boolean).length} 项）
                                                            </Text>
                                                        ),
                                                        children: renderFieldChips(selected.collected_fields?.filter(Boolean) ?? []),
                                                    },
                                                ]}
                                            />
                                        )}
                                        {(selected.still_needed_fields?.filter(Boolean).length ?? 0) > 0 && (
                                            <div>
                                                <Text strong style={{ display: 'block', marginBottom: 8 }}>
                                                    {missingHeading}
                                                </Text>
                                                <Space size={[4, 4]} wrap>
                                                    {selected.still_needed_fields!.filter(Boolean).slice(0, 4).map((id) => (
                                                        <Tag key={id} color="orange" style={{ margin: 0 }}>
                                                            {railFieldLabel(id)}
                                                        </Tag>
                                                    ))}
                                                </Space>
                                            </div>
                                        )}
                                        <div
                                            style={{
                                                padding: '12px 14px',
                                                background: 'linear-gradient(90deg, #e6f4ff 0%, #f0f7ff 100%)',
                                                borderRadius: 8,
                                                border: '1px solid #91caff',
                                            }}
                                        >
                                            <Text strong style={{ display: 'block', marginBottom: 6, color: '#0958d9' }}>
                                                {nextHeading}
                                            </Text>
                                            <Paragraph style={{ margin: 0, fontSize: 14, color: '#262626', lineHeight: 1.6 }}>
                                                {nextStepHint(selected)}
                                            </Paragraph>
                                        </div>

                                        {onContinueInCustomerPortal && selected ? (
                                            <Button
                                                type="primary"
                                                onClick={() => onContinueInCustomerPortal(selected.case_id)}
                                            >
                                                {goChatCta}
                                            </Button>
                                        ) : null}
                                    </Space>
                                )}
                            </Card>
                        </Col>
                    </Row>
                </Space>
            </div>
        </div>
    );
}
