/**
 * T3 — 陈总演示工具 (QA-only Demo Invite launcher).
 *
 * Not a customer-management feature. Hidden in Production.
 * Issues T2 Demo Invites; does not invent WeChat-native QR (T4).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Alert,
    Button,
    Card,
    Input,
    Modal,
    Radio,
    Space,
    Tag,
    Typography,
    message,
} from 'antd';
import { getFounderQaStatus, type FounderQaConsoleStatus } from '@/api/founderQaConsole';
import {
    CHEN_DEMO_OFFICE_ID,
    CHEN_DEMO_SCENARIO_UI,
    buildDemoInviteEntryPayload,
    formatDemoInviteExpiry,
    issueDemoInvite,
    listDemoInviteCatalog,
    mapDemoInviteError,
    maskDemoInviteToken,
    resetDemoInviteOffice,
    resetDemoInviteOverlay,
    revokeDemoInvite,
    validateDemoInvite,
    type DemoInviteEntryPayload,
    type DemoInviteIssued,
    type DemoInviteScenario,
} from '@/api/demoInvite';
import { isChenDemoInviteUiEnabled } from '@/config/productSurface';
import { copyToClipboard } from '@/utils/demoCopy';

const { Text, Paragraph } = Typography;

type InviteUiStatus = 'none' | 'active' | 'revoked' | 'expired' | 'error';

function resolveHttpDetail(err: unknown): string {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    return mapDemoInviteError(detail || (err as Error)?.message);
}

export function ChenDemoInvitePanel() {
    const featureOn = isChenDemoInviteUiEnabled();
    const [authorized, setAuthorized] = useState<boolean | null>(null);
    const [catalog, setCatalog] = useState<DemoInviteScenario[]>([]);
    const [scenarioId, setScenarioId] = useState<string>('chen_camry');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [issued, setIssued] = useState<DemoInviteIssued | null>(null);
    const [inviteStatus, setInviteStatus] = useState<InviteUiStatus>('none');
    const [entry, setEntry] = useState<DemoInviteEntryPayload | null>(null);
    const [founderStatus, setFounderStatus] = useState<FounderQaConsoleStatus | null>(null);
    const [resetSessionId, setResetSessionId] = useState('');

    const activeCase = founderStatus?.active_case;
    const hasActiveCase = Boolean(activeCase?.has_active_case && activeCase?.case_id);
    const selectedSession = String(
        founderStatus?.selected_identity?.session_id || resetSessionId || '',
    ).trim();

    const loadCatalog = useCallback(async () => {
        if (!featureOn) {
            setAuthorized(false);
            return;
        }
        try {
            const rows = await listDemoInviteCatalog();
            setCatalog(rows);
            setAuthorized(true);
            setError(null);
            if (rows.length && !rows.some((r) => r.scenario_id === scenarioId)) {
                setScenarioId(rows[0].scenario_id);
            }
        } catch (e) {
            setAuthorized(false);
            setCatalog([]);
            setError(resolveHttpDetail(e));
        }
    }, [featureOn, scenarioId]);

    const refreshFounderHint = useCallback(async () => {
        try {
            const s = await getFounderQaStatus();
            setFounderStatus(s);
            const sid = String(s.selected_identity?.session_id || '').trim();
            if (sid) setResetSessionId(sid);
        } catch {
            setFounderStatus(null);
        }
    }, []);

    useEffect(() => {
        if (!featureOn) return;
        void loadCatalog();
        void refreshFounderHint();
    }, [featureOn, loadCatalog, refreshFounderHint]);

    const scenarioOptions = useMemo(() => {
        const ids = catalog.map((c) => c.scenario_id);
        const ordered = ['chen_camry', 'li_multi', 'wang_stale'].filter((id) => ids.includes(id));
        const rest = ids.filter((id) => !ordered.includes(id));
        return [...ordered, ...rest];
    }, [catalog]);

    if (!featureOn) return null;
    if (authorized === false) {
        return (
            <Card
                size="small"
                title="陈总演示工具"
                style={{
                    marginBottom: 16,
                    borderStyle: 'dashed',
                    borderColor: '#d9d9d9',
                    background: '#fafafa',
                }}
            >
                <Alert
                    type="warning"
                    showIcon
                    message="演示工具不可用"
                    description={
                        error ||
                        '需要 QA 演示开关与 Support 授权。Production 不会显示此面板。'
                    }
                />
            </Card>
        );
    }
    if (authorized !== true) return null;

    const onGenerate = async () => {
        if (busy) return;
        if (hasActiveCase && issued && issued.scenario_id !== scenarioId) {
            Modal.confirm({
                title: '已有进行中案件 — 不能静默换场景',
                content:
                    '当前选中身份仍有 Active Case。现有案件保持权威，换场景不会改写案件身份。请先点「重置演示」并确认，再生成新入口。',
                okText: '知道了',
                cancelButtonProps: { style: { display: 'none' } },
            });
            return;
        }
        setBusy(true);
        setError(null);
        try {
            const next = await issueDemoInvite({
                office_id: CHEN_DEMO_OFFICE_ID,
                scenario_id: scenarioId,
            });
            setIssued(next);
            setInviteStatus('active');
            setEntry(buildDemoInviteEntryPayload(next));
            message.success('演示入口已生成');
        } catch (e) {
            setError(resolveHttpDetail(e));
            setInviteStatus('error');
        } finally {
            setBusy(false);
        }
    };

    const onRevoke = async () => {
        if (!issued || busy) return;
        setBusy(true);
        setError(null);
        try {
            const res = await revokeDemoInvite({
                invite_id: issued.invite_id,
                token: issued.token,
            });
            if (!res.ok) {
                setError(mapDemoInviteError(res.error_code));
                return;
            }
            setInviteStatus('revoked');
            const check = await validateDemoInvite({
                token: issued.token,
                office_id: CHEN_DEMO_OFFICE_ID,
            });
            if (check.status === 'revoked' || !check.ok) {
                setInviteStatus('revoked');
            }
            message.success('邀请已撤销，无法再兑换');
        } catch (e) {
            setError(resolveHttpDetail(e));
        } finally {
            setBusy(false);
        }
    };

    const runReset = async () => {
        setBusy(true);
        setError(null);
        try {
            const office = await resetDemoInviteOffice(CHEN_DEMO_OFFICE_ID);
            let overlayNote = '';
            if (selectedSession) {
                const ov = await resetDemoInviteOverlay(selectedSession);
                overlayNote = ov.cleared ? '；会话 overlay 已清除' : '；会话无 overlay';
            }
            setIssued(null);
            setEntry(null);
            setInviteStatus('none');
            message.success(
                `办公室演示邀请已重置（撤销 ${office.invites_revoked ?? 0}）${overlayNote}`,
            );
            if (hasActiveCase) {
                message.warning(
                    'Active Case 仍在。请到 Engineering QA Console 执行 Fresh / 清除绑定后再开新演示。',
                    6,
                );
            }
            await refreshFounderHint();
        } catch (e) {
            setError(resolveHttpDetail(e));
        } finally {
            setBusy(false);
        }
    };

    const onResetClick = () => {
        Modal.confirm({
            title: '确认重置演示？',
            content: (
                <Space direction="vertical" size={8}>
                    <Text>
                        将撤销本办公室（{CHEN_DEMO_OFFICE_ID}）全部演示邀请，并清除所选会话的
                        overlay。不会改写真实 wx 身份。
                    </Text>
                    {hasActiveCase ? (
                        <Alert
                            type="warning"
                            showIcon
                            message="检测到 Active Case"
                            description={`案件 ${activeCase?.case_id} 仍保持权威。重置 overlay 不会静默替换该案件；换场景前还需在 QA Console 清除 Active Case。`}
                        />
                    ) : null}
                </Space>
            ),
            okText: '确认重置',
            okButtonProps: { danger: true },
            cancelText: '取消',
            onOk: () => runReset(),
        });
    };

    const uiMeta = CHEN_DEMO_SCENARIO_UI[scenarioId];
    const statusColor =
        inviteStatus === 'active'
            ? 'success'
            : inviteStatus === 'revoked'
              ? 'default'
              : inviteStatus === 'expired'
                ? 'warning'
                : 'processing';

    return (
        <Card
            size="small"
            title={
                <Space wrap>
                    <span>陈总演示工具</span>
                    <Tag color="orange">演示数据</Tag>
                    <Tag>QA only</Tag>
                </Space>
            }
            style={{
                marginBottom: 16,
                borderStyle: 'dashed',
                borderColor: '#fa8c16',
                background: '#fffbe6',
            }}
        >
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                    生成受控演示入口。真实微信身份不变；仅临时 mock 客户展示。非客户管理系统。
                </Paragraph>

                {hasActiveCase ? (
                    <Alert
                        type="warning"
                        showIcon
                        message="当前身份已有 Active Case"
                        description={`案件 ${activeCase?.case_id} 保持权威。不可静默换场景或重贴标签。换演示前请先「重置演示」并在 QA Console 清除 Active Case。`}
                    />
                ) : null}

                {error ? (
                    <Alert type="error" showIcon closable message={error} onClose={() => setError(null)} />
                ) : null}

                <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                        选择演示客户
                    </Text>
                    <Radio.Group
                        value={scenarioId}
                        onChange={(e) => setScenarioId(e.target.value)}
                        style={{ width: '100%' }}
                    >
                        <Space direction="vertical">
                            {scenarioOptions.map((id) => {
                                const meta = CHEN_DEMO_SCENARIO_UI[id];
                                const row = catalog.find((c) => c.scenario_id === id);
                                return (
                                    <Radio key={id} value={id}>
                                        {meta?.title || row?.label || id}
                                        <Tag style={{ marginLeft: 8 }} color="orange">
                                            演示数据
                                        </Tag>
                                    </Radio>
                                );
                            })}
                        </Space>
                    </Radio.Group>
                </div>

                <Space wrap>
                    <Button type="primary" loading={busy} onClick={() => void onGenerate()}>
                        生成演示入口
                    </Button>
                    <Button
                        danger
                        disabled={!issued || inviteStatus === 'revoked' || busy}
                        onClick={() => void onRevoke()}
                    >
                        撤销邀请
                    </Button>
                    <Button disabled={busy} onClick={onResetClick}>
                        重置演示
                    </Button>
                </Space>

                <Text type="secondary" style={{ fontSize: 12 }}>
                    办公室范围：{CHEN_DEMO_OFFICE_ID}
                    {uiMeta ? ` · ${uiMeta.customer} / ${uiMeta.vehicle}` : ''}
                </Text>

                {issued ? (
                    <Card size="small" type="inner" title="当前邀请">
                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                            <Space wrap>
                                <Tag color={statusColor}>
                                    {inviteStatus === 'active'
                                        ? 'active'
                                        : inviteStatus === 'revoked'
                                          ? 'revoked'
                                          : inviteStatus}
                                </Tag>
                                <Text>
                                    {CHEN_DEMO_SCENARIO_UI[issued.scenario_id]?.customer ||
                                        issued.customer_display_name}
                                </Text>
                                <Text type="secondary">
                                    {CHEN_DEMO_SCENARIO_UI[issued.scenario_id]?.vehicle ||
                                        issued.vehicle_summary}
                                </Text>
                            </Space>
                            <Text type="secondary">
                                过期：{formatDemoInviteExpiry(issued.expires_at)}
                            </Text>
                            <Text type="secondary" copyable={false}>
                                Token（掩码）：{maskDemoInviteToken(issued.token)}
                            </Text>
                            {entry ? (
                                <>
                                    <Text code style={{ fontSize: 12, wordBreak: 'break-all' }}>
                                        {entry.launch_path_with_query}
                                    </Text>
                                    <Button
                                        size="small"
                                        type="default"
                                        onClick={async () => {
                                            const ok = await copyToClipboard(
                                                entry.launch_path_with_query,
                                            );
                                            message.success(ok ? '已复制入口路径' : '复制失败');
                                        }}
                                    >
                                        复制入口路径
                                    </Button>
                                    <Alert
                                        type="info"
                                        showIcon
                                        message="暂不提供可扫微信码"
                                        description={
                                            <>
                                                <div>{entry.qr_blocker}</div>
                                                <div style={{ marginTop: 6 }}>{entry.t4_required}</div>
                                            </>
                                        }
                                    />
                                </>
                            ) : null}
                        </Space>
                    </Card>
                ) : null}

                <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        重置用 session（可选，来自 QA Console 选中身份）
                    </Text>
                    <Input
                        size="small"
                        placeholder="wx_… session_id"
                        value={resetSessionId}
                        onChange={(e) => setResetSessionId(e.target.value)}
                        style={{ marginTop: 4, maxWidth: 420 }}
                    />
                </div>
            </Space>
        </Card>
    );
}
