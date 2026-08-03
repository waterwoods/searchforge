/**
 * T3 / QA Fast Lane V1 — 陈总演示工具 (QA-only Demo Invite launcher).
 *
 * Primary action: 「一键准备演示」— Fresh → office reset → issue → validate.
 * Not a customer-management feature. Hidden in Production.
 * Does not invent WeChat-native QR (T4).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { API_BASE_URL } from '@/api/config';
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
    runP35FreshForDemo,
    validateDemoInvite,
    type DemoInviteEntryPayload,
    type DemoInviteIssued,
    type DemoInviteScenario,
} from '@/api/demoInvite';
import { isChenDemoInviteUiEnabled } from '@/config/productSurface';
import {
    DOCUMENT_INTAKE_PATH,
    isCloudQaWorkbenchClient,
    workbenchApiProfileLabel,
} from '@/config/workbenchEnv';
import {
    formatExpiryCountdown,
    prepareChenDemo,
    type PrepareDemoVerdict,
} from '@/features/intake/utils/prepareChenDemo';
import { copyToClipboard } from '@/utils/demoCopy';

const { Text, Paragraph } = Typography;

type InviteUiStatus = 'none' | 'active' | 'revoked' | 'expired' | 'error';

function resolveHttpDetail(err: unknown): string {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    return mapDemoInviteError(detail || (err as Error)?.message);
}

export type ChenDemoInvitePanelProps = {
    /** Fired after a demo invite is generated — Workbench may hide unrelated TEST noise. */
    onInviteGenerated?: () => void;
};

export function ChenDemoInvitePanel({ onInviteGenerated }: ChenDemoInvitePanelProps = {}) {
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
    const [collapsed, setCollapsed] = useState(false);
    const [prepareVerdict, setPrepareVerdict] = useState<PrepareDemoVerdict | null>(null);
    const [nowSec, setNowSec] = useState(() => Math.floor(Date.now() / 1000));
    const [frontendHost, setFrontendHost] = useState('');
    const [workbenchUrl, setWorkbenchUrl] = useState('');
    /** Sync lock — React state alone cannot stop double-clicks before re-render. */
    const prepareInFlightRef = useRef(false);

    const activeCase = founderStatus?.active_case;
    const hasActiveCase = Boolean(activeCase?.has_active_case && activeCase?.case_id);
    const selectedSession = String(
        founderStatus?.selected_identity?.session_id || resetSessionId || '',
    ).trim();
    const apiProfile = workbenchApiProfileLabel(API_BASE_URL);
    const isCloudQa = isCloudQaWorkbenchClient(API_BASE_URL);
    const lockAfterPass =
        prepareVerdict === 'PASS' && inviteStatus === 'active' && Boolean(issued);

    useEffect(() => {
        if (typeof window === 'undefined') return;
        setFrontendHost(window.location.host);
        setWorkbenchUrl(`${window.location.origin}${DOCUMENT_INTAKE_PATH}`);
    }, []);

    useEffect(() => {
        if (!issued?.expires_at || inviteStatus !== 'active') return;
        const id = window.setInterval(() => {
            setNowSec(Math.floor(Date.now() / 1000));
        }, 1000);
        return () => window.clearInterval(id);
    }, [issued?.expires_at, inviteStatus]);

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

    const clearLocalInviteState = () => {
        setIssued(null);
        setEntry(null);
        setInviteStatus('none');
        setPrepareVerdict(null);
    };

    const onPrepareDemo = async () => {
        if (prepareInFlightRef.current || busy || lockAfterPass) return;
        prepareInFlightRef.current = true;
        setBusy(true);
        setError(null);
        // Remove previous invite/path before a new run.
        clearLocalInviteState();
        try {
            const res = await prepareChenDemo(
                {
                    apiBaseUrl: API_BASE_URL,
                    sessionId: selectedSession || resetSessionId,
                    scenarioId,
                    officeId: CHEN_DEMO_OFFICE_ID,
                    busy: false,
                },
                {
                    runFresh: (session_id) => runP35FreshForDemo(session_id),
                    resetOffice: (office_id) => resetDemoInviteOffice(office_id),
                    resetOverlay: (session_id) => resetDemoInviteOverlay(session_id),
                    issueInvite: (body) => issueDemoInvite(body),
                    validateInvite: (body) => validateDemoInvite(body),
                },
            );
            setPrepareVerdict(res.verdict);
            if (res.issued) {
                setIssued(res.issued);
                setEntry(res.entry || buildDemoInviteEntryPayload(res.issued));
                setInviteStatus(res.verdict === 'PASS' ? 'active' : 'error');
            }
            if (res.verdict === 'PASS' && res.issued) {
                setCollapsed(true);
                onInviteGenerated?.();
                message.success('一键准备演示 PASS — 请复制编译路径到手机');
            } else {
                setError(res.error || '准备失败');
                message.error(res.error || '准备失败');
            }
            await refreshFounderHint();
        } catch (e) {
            setPrepareVerdict('FAIL');
            setError(resolveHttpDetail(e));
            setInviteStatus('error');
        } finally {
            prepareInFlightRef.current = false;
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
            setPrepareVerdict(null);
            const check = await validateDemoInvite({
                token: issued.token,
                office_id: CHEN_DEMO_OFFICE_ID,
            });
            if (check.status === 'revoked' || !check.ok) {
                setInviteStatus('revoked');
            }
            message.success('邀请已撤销 — 可再次一键准备');
        } catch (e) {
            setError(resolveHttpDetail(e));
        } finally {
            setBusy(false);
        }
    };

    const runReset = async () => {
        if (lockAfterPass) return;
        setBusy(true);
        setError(null);
        try {
            const office = await resetDemoInviteOffice(CHEN_DEMO_OFFICE_ID);
            let overlayNote = '';
            if (selectedSession) {
                const ov = await resetDemoInviteOverlay(selectedSession);
                overlayNote = ov.cleared ? '；会话 overlay 已清除' : '；会话无 overlay';
            }
            clearLocalInviteState();
            message.success(
                `办公室演示邀请已重置（撤销 ${office.invites_revoked ?? 0}）${overlayNote}`,
            );
            if (hasActiveCase) {
                message.warning(
                    'Active Case 仍在。请使用「一键准备演示」执行 P35 Fresh，或到 Engineering QA Console 清除绑定。',
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
        if (lockAfterPass) {
            message.warning('有效邀请展示中 — 邀请创建后请勿重置。请先撤销邀请。');
            return;
        }
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
                            description={`案件 ${activeCase?.case_id} 仍保持权威。重置 overlay 不会静默替换该案件；换场景前请用「一键准备演示」。`}
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

    const canCollapse = Boolean(issued) && prepareVerdict === 'PASS';
    const showBody = !collapsed || !canCollapse;
    const countdown =
        issued?.expires_at && inviteStatus === 'active'
            ? formatExpiryCountdown(issued.expires_at, nowSec)
            : null;

    return (
        <Card
            size="small"
            title={
                <Space wrap size={6}>
                    <span>陈总演示工具</span>
                    <Tag color="blue" style={{ marginInlineEnd: 0, fontSize: 11 }}>
                        QA
                    </Tag>
                    <Tag
                        style={{
                            marginInlineEnd: 0,
                            fontSize: 11,
                            color: '#8c8c8c',
                            borderColor: '#d9d9d9',
                        }}
                    >
                        演示数据
                    </Tag>
                    {prepareVerdict === 'PASS' ? (
                        <Tag color="success" style={{ marginInlineEnd: 0 }}>
                            PASS
                        </Tag>
                    ) : null}
                    {prepareVerdict === 'FAIL' ? (
                        <Tag color="error" style={{ marginInlineEnd: 0 }}>
                            FAIL
                        </Tag>
                    ) : null}
                    {issued && inviteStatus === 'active' ? (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            已就绪 ·{' '}
                            {CHEN_DEMO_SCENARIO_UI[issued.scenario_id]?.customer ||
                                issued.customer_display_name}
                        </Text>
                    ) : null}
                </Space>
            }
            extra={
                canCollapse ? (
                    <Button type="link" size="small" onClick={() => setCollapsed((v) => !v)}>
                        {collapsed ? '展开' : '收起'}
                    </Button>
                ) : null
            }
            style={{
                marginBottom: 16,
                borderStyle: 'dashed',
                borderColor: '#d9d9d9',
                background: '#fafafa',
            }}
        >
            {!showBody ? (
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        演示入口已就绪（PASS）。收起以免干扰 Workbench；需要时可展开复制路径。
                    </Text>
                    {entry ? (
                        <Space wrap>
                            <Text code style={{ fontSize: 12, wordBreak: 'break-all' }}>
                                {entry.launch_path_with_query}
                            </Text>
                            <Button
                                size="small"
                                type="primary"
                                onClick={async () => {
                                    const ok = await copyToClipboard(entry.launch_path_with_query);
                                    message.success(ok ? '已复制编译路径' : '复制失败');
                                }}
                            >
                                复制编译路径
                            </Button>
                        </Space>
                    ) : null}
                </Space>
            ) : null}
            {showBody ? (
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                        一键准备：验证 Cloud QA → P35 Fresh → 办公室重置 → 签发并校验邀请。真实微信身份不变；仅临时
                        mock 客户展示。
                    </Paragraph>

                    <Space wrap size={8}>
                        <Tag color={isCloudQa ? 'blue' : 'error'}>
                            {isCloudQa ? 'QA' : '非 QA'}
                        </Tag>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            前端：{frontendHost || '—'}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            API：{apiProfile}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }} copyable={!!API_BASE_URL}>
                            {API_BASE_URL || '(relative / local)'}
                        </Text>
                    </Space>

                    <Text type="secondary" style={{ fontSize: 12 }}>
                        Workbench：{workbenchUrl || DOCUMENT_INTAKE_PATH}
                    </Text>

                    {!isCloudQa ? (
                        <Alert
                            type="error"
                            showIcon
                            message="当前前端未连接到 fiqa-api-qa"
                            description="一键准备演示已硬阻断。请打开 Cloud QA Preview（勿用 Production）。"
                        />
                    ) : null}

                    {hasActiveCase ? (
                        <Alert
                            type="warning"
                            showIcon
                            message="当前身份已有 Active Case"
                            description={`案件 ${activeCase?.case_id} 保持权威。「一键准备演示」会先执行 P35 Fresh 再签发新邀请。`}
                        />
                    ) : null}

                    {error ? (
                        <Alert
                            type="error"
                            showIcon
                            closable
                            message={error}
                            onClose={() => setError(null)}
                        />
                    ) : null}

                    <div>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>
                            选择演示客户（persona）
                        </Text>
                        <Radio.Group
                            value={scenarioId}
                            onChange={(e) => setScenarioId(e.target.value)}
                            disabled={lockAfterPass || busy}
                            style={{ width: '100%' }}
                        >
                            <Space direction="vertical">
                                {scenarioOptions.map((id) => {
                                    const meta = CHEN_DEMO_SCENARIO_UI[id];
                                    const row = catalog.find((c) => c.scenario_id === id);
                                    return (
                                        <Radio key={id} value={id}>
                                            {meta?.title || row?.label || id}
                                            <Tag
                                                style={{
                                                    marginLeft: 8,
                                                    fontSize: 11,
                                                    color: '#8c8c8c',
                                                    borderColor: '#d9d9d9',
                                                }}
                                            >
                                                演示
                                            </Tag>
                                        </Radio>
                                    );
                                })}
                            </Space>
                        </Radio.Group>
                    </div>

                    <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            已批准 QA session_id（精确 wx_*，来自 QA Console 或手机）
                        </Text>
                        <Input
                            size="small"
                            placeholder="wx_… session_id"
                            value={resetSessionId}
                            disabled={lockAfterPass || busy}
                            onChange={(e) => setResetSessionId(e.target.value)}
                            style={{ marginTop: 4, maxWidth: 480 }}
                        />
                    </div>

                    <Space wrap>
                        <Button
                            type="primary"
                            loading={busy}
                            disabled={lockAfterPass || !isCloudQa}
                            onClick={() => void onPrepareDemo()}
                        >
                            一键准备演示
                        </Button>
                        <Button
                            danger
                            disabled={!issued || inviteStatus === 'revoked' || busy}
                            onClick={() => void onRevoke()}
                        >
                            撤销邀请
                        </Button>
                        <Button disabled={busy || lockAfterPass} onClick={onResetClick}>
                            重置演示
                        </Button>
                    </Space>

                    {lockAfterPass ? (
                        <Alert
                            type="warning"
                            showIcon
                            message="邀请创建后请勿重置"
                            description="有效邀请展示中：重置 / 重新准备已禁用。若需新一轮，请先「撤销邀请」。"
                        />
                    ) : null}

                    <Alert
                        type="info"
                        showIcon
                        message="删除旧的 DevTools 编译模式"
                        description="手机编译前请删除旧的 dit= 编译条件，只保留本次复制的一条路径，避免兑换到已撤销 token。"
                    />

                    <Text type="secondary" style={{ fontSize: 12 }}>
                        办公室范围：{CHEN_DEMO_OFFICE_ID}
                        {uiMeta ? ` · persona：${uiMeta.customer} / ${uiMeta.vehicle}` : ''}
                    </Text>

                    {prepareVerdict ? (
                        <Alert
                            type={prepareVerdict === 'PASS' ? 'success' : 'error'}
                            showIcon
                            message={`准备结果：${prepareVerdict}`}
                            description={
                                prepareVerdict === 'PASS'
                                    ? 'status=active · scenario 匹配 · use_count=0 · 未过期'
                                    : error || '校验未通过 — 不会显示为可用入口'
                            }
                        />
                    ) : null}

                    {issued ? (
                        <Card size="small" type="inner" title="当前邀请">
                            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                <Space wrap>
                                    <Tag color={statusColor}>
                                        {inviteStatus === 'active'
                                            ? '有效 / active'
                                            : inviteStatus === 'revoked'
                                              ? '已撤销'
                                              : inviteStatus === 'expired'
                                                ? '已过期'
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
                                    {prepareVerdict ? (
                                        <Tag color={prepareVerdict === 'PASS' ? 'success' : 'error'}>
                                            {prepareVerdict}
                                        </Tag>
                                    ) : null}
                                </Space>
                                <Text type="secondary">
                                    过期：{formatDemoInviteExpiry(issued.expires_at)}
                                    {countdown ? ` · 倒计时 ${countdown}` : ''}
                                </Text>
                                <Text type="secondary" copyable={false}>
                                    Token（掩码）：{maskDemoInviteToken(issued.token)}
                                </Text>
                                {entry && prepareVerdict === 'PASS' ? (
                                    <>
                                        <Text strong style={{ fontSize: 12 }}>
                                            唯一编译路径
                                        </Text>
                                        <Text code style={{ fontSize: 12, wordBreak: 'break-all' }}>
                                            {entry.launch_path_with_query}
                                        </Text>
                                        <Button
                                            size="small"
                                            type="primary"
                                            onClick={async () => {
                                                const ok = await copyToClipboard(
                                                    entry.launch_path_with_query,
                                                );
                                                message.success(ok ? '已复制编译路径' : '复制失败');
                                            }}
                                        >
                                            复制编译路径
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
                                {entry && prepareVerdict === 'FAIL' ? (
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        校验未 PASS — 不展示可用编译路径。
                                    </Text>
                                ) : null}
                            </Space>
                        </Card>
                    ) : null}
                </Space>
            ) : null}
        </Card>
    );
}
