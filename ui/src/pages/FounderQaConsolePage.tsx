/**
 * P35.2 — Founder QA Console (internal testing surface).
 * Not customer-facing. Never stores support API keys.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Alert,
    Button,
    Card,
    Collapse,
    Input,
    Modal,
    Space,
    Typography,
    message,
    Spin,
    Tag,
} from 'antd';
import { Link } from 'react-router-dom';
import {
    brokerCaseOpenPath,
    forgetFounderQaIdentity,
    getFounderQaStatus,
    listFounderQaAudit,
    mapFounderQaError,
    runFounderQaPreset,
    selectFounderQaIdentity,
    type FounderQaAuditEvent,
    type FounderQaConsoleStatus,
    type FounderQaPresetResult,
} from '@/api/founderQaConsole';
import { isQaToolsEnabled } from '@/config/productSurface';

const { Title, Text, Paragraph } = Typography;

type PresetKey = 'fresh' | 'active' | 'request-more';

const PRESETS: Record<
    PresetKey,
    {
        title: string;
        description: string;
        expected: string[];
        button: string;
        confirm: string;
        primary?: boolean;
    }
> = {
    fresh: {
        title: 'Fresh Customer',
        description: 'Reset this exact QA identity to a clean first-use state.',
        expected: ['no active case', 'no resume token', 'Service Home shows 我要报案'],
        button: '切换为新客户',
        confirm: 'FRESH',
        primary: true,
    },
    active: {
        title: 'Active Claim',
        description: 'Create or restore one deterministic active QA claim.',
        expected: ['exactly one active claim', 'stable resume token', 'Service Home shows 继续处理当前报案'],
        button: '生成进行中案件',
        confirm: 'ACTIVE',
    },
    'request-more': {
        title: 'Request More — VIN',
        description: 'Create a deterministic claim with one Broker request for VIN.',
        expected: ['active claim exists', 'VIN request is open', 'Continue routes to missing-item workflow'],
        button: '生成 VIN 补件场景',
        confirm: 'REQUEST_MORE',
    },
};

function yesNo(v: boolean | undefined | null): string {
    if (v === true) return 'Yes';
    if (v === false) return 'No';
    return '—';
}

function envBanner(status: FounderQaConsoleStatus | null): {
    type: 'success' | 'warning' | 'error' | 'info';
    title: string;
    detail: string;
} {
    const env = (status?.environment || 'unknown').toLowerCase();
    const enabled = Boolean(status?.enabled);
    const prod = Boolean(status?.production_like);
    if (prod && !enabled) {
        return {
            type: 'error',
            title: '生产环境 · QA Reset 已强制禁用',
            detail: '此控制台不会执行任何重置。后端安全边界保持生效。',
        };
    }
    if (!enabled) {
        return {
            type: 'warning',
            title: `${env === 'qa' ? 'QA环境' : env} · Founder QA 未启用`,
            detail: '请设置 ENABLE_P35_MP_QA_HARNESS=1 与 UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1。',
        };
    }
    if (env === 'qa' || (!prod && enabled)) {
        return {
            type: 'success',
            title: `${env === 'qa' ? 'QA环境' : env} · Founder QA 已启用`,
            detail: status?.authorized === false ? '当前内部授权未通过。' : '可对已选精确身份执行预设。',
        };
    }
    return {
        type: 'warning',
        title: `${env} · Founder QA 已启用（生产态门控）`,
        detail: '生产态仍要求服务端 Support Key 已配置；浏览器不会收到该密钥。',
    };
}

export default function FounderQaConsolePage() {
    const toolsEnabled = isQaToolsEnabled();
    const [status, setStatus] = useState<FounderQaConsoleStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastResult, setLastResult] = useState<FounderQaPresetResult | null>(null);
    const [audit, setAudit] = useState<FounderQaAuditEvent[]>([]);
    const [auditError, setAuditError] = useState<string | null>(null);
    const [showMpHelp, setShowMpHelp] = useState(false);
    const [identityOpen, setIdentityOpen] = useState(false);
    const [identityDraft, setIdentityDraft] = useState('');
    const [identityLabel, setIdentityLabel] = useState('');
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [pendingPreset, setPendingPreset] = useState<PresetKey | null>(null);
    const [confirmPhrase, setConfirmPhrase] = useState('');
    const [copied, setCopied] = useState<string | null>(null);

    const banner = useMemo(() => envBanner(status), [status]);
    const hasIdentity = Boolean(status?.selected_identity?.session_id);
    const mutationsOk = Boolean(status?.mutations_allowed) && !running && hasIdentity;

    const refreshStatus = useCallback(async () => {
        try {
            const s = await getFounderQaStatus();
            setStatus(s);
            setError(null);
            return s;
        } catch (e) {
            const msg = (e as Error)?.message || mapFounderQaError('status_unavailable');
            setError(msg);
            // Do not clear selected identity on refresh failure.
            return null;
        }
    }, []);

    const refreshAudit = useCallback(async () => {
        try {
            const events = await listFounderQaAudit(15);
            setAudit(events);
            setAuditError(null);
        } catch (e) {
            setAuditError((e as Error)?.message || 'audit_unavailable');
        }
    }, []);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            await refreshStatus();
            if (!cancelled) setLoading(false);
        })();
        return () => {
            cancelled = true;
        };
    }, [refreshStatus]);

    const copyText = async (label: string, value: string | null | undefined) => {
        const v = (value || '').trim();
        if (!v) {
            message.warning(`无可复制的 ${label}`);
            return;
        }
        try {
            await navigator.clipboard.writeText(v);
            setCopied(label);
            message.success(`已复制 ${label}`);
            setTimeout(() => setCopied(null), 1500);
        } catch {
            message.error('复制失败');
        }
    };

    const onSelectIdentity = async () => {
        setRunning(true);
        try {
            const res = await selectFounderQaIdentity({
                session_id: identityDraft.trim(),
                label: identityLabel.trim() || undefined,
            });
            setStatus(res.status);
            setIdentityOpen(false);
            setIdentityDraft('');
            message.success('已选择 QA 身份');
        } catch (e) {
            message.error((e as Error)?.message || '选择失败');
        } finally {
            setRunning(false);
        }
    };

    const onForgetIdentity = async () => {
        setRunning(true);
        try {
            const res = await forgetFounderQaIdentity();
            setStatus(res.status);
            setLastResult(null);
            message.success('已清除所选身份');
        } catch (e) {
            message.error((e as Error)?.message || '清除失败');
        } finally {
            setRunning(false);
        }
    };

    const openConfirm = (preset: PresetKey) => {
        setPendingPreset(preset);
        setConfirmPhrase('');
        setConfirmOpen(true);
    };

    const executePreset = async () => {
        if (!pendingPreset || running) return;
        const meta = PRESETS[pendingPreset];
        if (confirmPhrase.trim() !== meta.confirm) {
            message.error(`请输入确认短语 ${meta.confirm}`);
            return;
        }
        setRunning(true);
        setError(null);
        try {
            const res = await runFounderQaPreset(pendingPreset, { confirm: confirmPhrase.trim() });
            setLastResult(res);
            if (res.status) setStatus(res.status);
            else await refreshStatus();
            setConfirmOpen(false);
            if (res.ok) {
                message.success(`${meta.title} 已应用`);
            } else {
                message.warning('操作未完全成功 — 请查看结果');
            }
            void refreshAudit();
        } catch (e) {
            const msg = (e as Error)?.message || 'preset_failed';
            setError(msg);
            message.error(msg);
            // Partial failure: refresh status without claiming success.
            await refreshStatus();
            void refreshAudit();
        } finally {
            setRunning(false);
        }
    };

    if (!toolsEnabled) {
        return (
            <div style={{ maxWidth: 880, margin: '24px auto', padding: 16 }}>
                <Alert
                    type="error"
                    showIcon
                    message="Founder QA Console 未对当前构建开放"
                    description="仅内部 QA 构建可见（Vite DEV 或 VITE_ENABLE_QA_TOOLS=1）。"
                />
            </div>
        );
    }

    const identity = status?.selected_identity;
    const active = status?.active_case;
    const caseId = active?.case_id || identity?.active_case_id || null;

    return (
        <div style={{ maxWidth: 960, margin: '0 auto', padding: '20px 16px 48px' }}>
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <div>
                    <Title level={3} style={{ marginBottom: 4 }}>
                        Founder QA Console
                    </Title>
                    <Text type="secondary">内部测试台 · 选择场景并验证 · 不改动客户产品导航</Text>
                </div>

                {/* SECTION 1 — Environment safety */}
                <Alert
                    type={banner.type}
                    showIcon
                    message={banner.title}
                    description={
                        <Space direction="vertical" size={2}>
                            <Text>
                                授权：{status?.authorized === false ? '未通过' : '已通过（Intake 边界）'}
                                {' · '}
                                内部用户：{status?.actor || 'founder'}
                                {' · '}
                                Support Key：
                                {status?.support_key_configured ? '服务端已配置（不下发）' : '未配置'}
                            </Text>
                            <Text type="secondary">{banner.detail}</Text>
                        </Space>
                    }
                />

                {error ? <Alert type="error" showIcon closable message={error} onClose={() => setError(null)} /> : null}

                {loading ? (
                    <div style={{ textAlign: 'center', padding: 48 }}>
                        <Spin />
                    </div>
                ) : (
                    <>
                        {/* SECTION 2 — QA Identity */}
                        <Card
                            size="small"
                            title="QA Identity"
                            extra={
                                <Space>
                                    <Button size="small" onClick={() => void refreshStatus()} disabled={running}>
                                        Refresh Status
                                    </Button>
                                    <Button
                                        size="small"
                                        type="primary"
                                        onClick={() => {
                                            setIdentityDraft(identity?.session_id || '');
                                            setIdentityLabel(identity?.label || '');
                                            setIdentityOpen(true);
                                        }}
                                        disabled={running}
                                    >
                                        {hasIdentity ? 'Change Identity' : 'Select QA Identity'}
                                    </Button>
                                </Space>
                            }
                        >
                            {hasIdentity && identity ? (
                                <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                    <Text>
                                        标签：<Text strong>{identity.label || '（未命名）'}</Text>
                                    </Text>
                                    <Text>
                                        Session：<Text code>{identity.identity_masked}</Text>{' '}
                                        <Button
                                            type="link"
                                            size="small"
                                            onClick={() => void copyText('Session ID', identity.session_id)}
                                        >
                                            {copied === 'Session ID' ? '已复制' : 'Copy exact ID'}
                                        </Button>
                                    </Text>
                                    <Text>
                                        Person link：<Text code>{identity.person_link_key_masked}</Text>
                                    </Text>
                                    <Text>
                                        Active case：<Text code>{identity.active_case_id || '—'}</Text>
                                    </Text>
                                    <Text type="secondary">
                                        已选时间：{identity.selected_at || identity.last_seen || '—'}
                                    </Text>
                                    <Button size="small" danger onClick={() => void onForgetIdentity()} disabled={running}>
                                        Forget Selected Identity
                                    </Button>
                                </Space>
                            ) : (
                                <Alert
                                    type="info"
                                    showIcon
                                    message="尚未选择 QA 身份"
                                    description="从微信开发者工具控制台复制：wx.getStorageSync('mp_customer_session_id')，粘贴一次即可保存到服务端偏好。"
                                />
                            )}
                        </Card>

                        {/* SECTION 3 — Current QA State */}
                        <Card
                            size="small"
                            title="Current QA State"
                            extra={
                                <Button size="small" onClick={() => void refreshStatus()} disabled={running}>
                                    Refresh
                                </Button>
                            }
                        >
                            {status?.inspect_error ? (
                                <Alert type="warning" showIcon message={`状态读取：${status.inspect_error}`} />
                            ) : null}
                            <div
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                                    gap: 10,
                                    marginTop: 8,
                                }}
                            >
                                <Metric label="Active claim" value={yesNo(active?.has_active_case)} />
                                <Metric label="Case ID" value={caseId || '—'} mono />
                                <Metric label="Claim status" value={active?.claim_status || '—'} />
                                <Metric label="Next action" value={active?.next_action || active?.current_task || '—'} />
                                <Metric
                                    label="Open request-more"
                                    value={
                                        status?.open_request_more
                                            ? `${status.open_request_more.item_type || '?'} (${status.open_request_more.status || 'open'})`
                                            : '—'
                                    }
                                />
                                <Metric label="Resume bound" value={yesNo(status?.resume_binding?.bound)} />
                                <Metric label="QA fixture" value={active?.qa_fixture_demo_name || '—'} />
                                <Metric
                                    label="Last preset"
                                    value={active?.last_preset_applied || status?.latest_qa_preset || '—'}
                                />
                                <Metric label="Last reset" value={active?.last_reset_time || '—'} />
                            </div>
                        </Card>

                        {/* SECTION 4 — Preset cards */}
                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                                gap: 12,
                            }}
                        >
                            {(Object.keys(PRESETS) as PresetKey[]).map((key) => {
                                const p = PRESETS[key];
                                return (
                                    <Card key={key} size="small" title={p.title}>
                                        <Paragraph type="secondary" style={{ minHeight: 44, marginBottom: 8 }}>
                                            {p.description}
                                        </Paragraph>
                                        <ul style={{ paddingLeft: 18, margin: '0 0 12px', color: '#595959' }}>
                                            {p.expected.map((line) => (
                                                <li key={line}>{line}</li>
                                            ))}
                                        </ul>
                                        <Button
                                            type={p.primary ? 'primary' : 'default'}
                                            block
                                            disabled={!mutationsOk || !status?.enabled}
                                            loading={running && pendingPreset === key}
                                            onClick={() => openConfirm(key)}
                                        >
                                            {p.button}
                                        </Button>
                                    </Card>
                                );
                            })}
                        </div>

                        {/* SECTION 5 — Result / quick actions / audit */}
                        <Card size="small" title="Result & Quick Actions">
                            {lastResult ? (
                                <Alert
                                    style={{ marginBottom: 12 }}
                                    type={lastResult.ok ? 'success' : 'error'}
                                    showIcon
                                    message={lastResult.ok ? '操作成功' : '操作失败 / 部分失败'}
                                    description={
                                        <Space direction="vertical" size={2}>
                                            <Text>Preset：{String(lastResult.preset || '—')}</Text>
                                            <Text>
                                                Identity：
                                                {String(
                                                    (lastResult.result as { identity_masked?: string })?.identity_masked ||
                                                        identity?.identity_masked ||
                                                        '—',
                                                )}
                                            </Text>
                                            <Text>
                                                Case ID：
                                                {String((lastResult.result as { case_id?: string })?.case_id || caseId || '—')}
                                            </Text>
                                            <Text>
                                                Resume：
                                                {String(
                                                    (lastResult.result as { resume_token_masked?: string })
                                                        ?.resume_token_masked ||
                                                        (status?.resume_binding?.bound ? 'bound' : 'cleared'),
                                                )}
                                            </Text>
                                            {(lastResult.result as { requested_item_type?: string })?.requested_item_type ? (
                                                <Text>
                                                    Request-more：
                                                    {String(
                                                        (lastResult.result as { requested_item_type?: string })
                                                            .requested_item_type,
                                                    )}
                                                </Text>
                                            ) : null}
                                            <Text type="secondary">
                                                Audit：
                                                {String(
                                                    ((lastResult.result as { audit?: { at?: string } })?.audit?.at) ||
                                                        status?.latest_qa_audit_event?.at ||
                                                        '—',
                                                )}
                                            </Text>
                                        </Space>
                                    }
                                />
                            ) : (
                                <Text type="secondary">执行预设后将显示结果。</Text>
                            )}

                            <Space wrap style={{ marginTop: 12 }}>
                                <Button onClick={() => void refreshStatus()} disabled={running}>
                                    Refresh State
                                </Button>
                                <Button onClick={() => void copyText('Case ID', caseId)} disabled={!caseId}>
                                    Copy Case ID
                                </Button>
                                <Button
                                    onClick={() => void copyText('Session ID', identity?.session_id)}
                                    disabled={!identity?.session_id}
                                >
                                    Copy Session ID
                                </Button>
                                {caseId ? (
                                    <Link to={brokerCaseOpenPath(caseId)}>
                                        <Button type="default">Open Broker Case</Button>
                                    </Link>
                                ) : null}
                                <Button onClick={() => setShowMpHelp(true)}>Show Mini Program test instructions</Button>
                                <Button
                                    onClick={() => {
                                        void refreshAudit();
                                        message.info('已刷新审计列表');
                                    }}
                                >
                                    View Recent QA Audit Events
                                </Button>
                            </Space>

                            {auditError ? (
                                <Alert
                                    style={{ marginTop: 12 }}
                                    type="warning"
                                    showIcon
                                    message="审计列表暂不可用（不影响重置）"
                                    description={auditError}
                                />
                            ) : null}
                            {audit.length > 0 ? (
                                <div style={{ marginTop: 12 }}>
                                    {audit.slice(0, 8).map((ev, idx) => (
                                        <div
                                            key={`${ev.at || idx}-${ev.preset}-${idx}`}
                                            style={{
                                                display: 'flex',
                                                gap: 8,
                                                flexWrap: 'wrap',
                                                padding: '6px 0',
                                                borderTop: '1px solid #f0f0f0',
                                                fontSize: 13,
                                            }}
                                        >
                                            <Tag color={ev.ok ? 'green' : 'red'}>{ev.ok ? 'ok' : 'fail'}</Tag>
                                            <Text code>{ev.preset}</Text>
                                            <Text type="secondary">{ev.identity_masked}</Text>
                                            <Text type="secondary">{ev.case_id}</Text>
                                            <Text type="secondary">{ev.at}</Text>
                                            {ev.error ? <Text type="danger">{String(ev.error)}</Text> : null}
                                        </div>
                                    ))}
                                </div>
                            ) : null}
                        </Card>

                        <Collapse
                            items={[
                                {
                                    key: 'diag',
                                    label: 'Diagnostic (raw, collapsible)',
                                    children: (
                                        <pre style={{ margin: 0, fontSize: 11, whiteSpace: 'pre-wrap' }}>
                                            {JSON.stringify(status, null, 2)}
                                        </pre>
                                    ),
                                },
                            ]}
                        />
                    </>
                )}
            </Space>

            <Modal
                title="Select QA Identity"
                open={identityOpen}
                onCancel={() => setIdentityOpen(false)}
                onOk={() => void onSelectIdentity()}
                okText="Save Identity"
                confirmLoading={running}
                destroyOnClose
            >
                <Space direction="vertical" style={{ width: '100%' }} size={10}>
                    <Alert
                        type="info"
                        showIcon
                        message="精确匹配 only"
                        description="粘贴完整 wx_* session ID。禁止通配符与模糊搜索。偏好保存在服务端（当前内部用户 + 环境）。"
                    />
                    <div>
                        <Text type="secondary">Session ID</Text>
                        <Input
                            value={identityDraft}
                            onChange={(e) => setIdentityDraft(e.target.value)}
                            placeholder="wx_…"
                            autoFocus
                        />
                    </div>
                    <div>
                        <Text type="secondary">Friendly label（可选）</Text>
                        <Input
                            value={identityLabel}
                            onChange={(e) => setIdentityLabel(e.target.value)}
                            placeholder="Founder DevTools"
                            maxLength={64}
                        />
                    </div>
                </Space>
            </Modal>

            <Modal
                title={pendingPreset ? `确认：${PRESETS[pendingPreset].title}` : '确认'}
                open={confirmOpen}
                onCancel={() => {
                    if (!running) setConfirmOpen(false);
                }}
                onOk={() => void executePreset()}
                okText="确认执行"
                confirmLoading={running}
                okButtonProps={{
                    disabled: !pendingPreset || confirmPhrase.trim() !== (pendingPreset ? PRESETS[pendingPreset].confirm : ''),
                }}
                destroyOnClose
            >
                {pendingPreset ? (
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                        {status?.production_like ? (
                            <Alert type="error" showIcon message="生产态警告：请确认你真的要在当前环境执行 QA Reset。" />
                        ) : null}
                        <Text>
                            环境：<Text strong>{status?.environment}</Text>
                        </Text>
                        <Text>
                            身份：<Text code>{identity?.identity_masked || '—'}</Text>
                        </Text>
                        <Text>操作：{PRESETS[pendingPreset].title}</Text>
                        <Text type="secondary">仅影响该精确身份下的 QA harness 记录（p35_mp_qa / binding）。</Text>
                        <ul style={{ paddingLeft: 18, margin: 0 }}>
                            {PRESETS[pendingPreset].expected.map((line) => (
                                <li key={line}>{line}</li>
                            ))}
                        </ul>
                        <div>
                            <Text type="secondary">输入确认短语：{PRESETS[pendingPreset].confirm}</Text>
                            <Input
                                value={confirmPhrase}
                                onChange={(e) => setConfirmPhrase(e.target.value)}
                                placeholder={PRESETS[pendingPreset].confirm}
                                autoFocus
                                onPressEnter={() => void executePreset()}
                            />
                        </div>
                    </Space>
                ) : null}
            </Modal>

            <Modal
                title="Mini Program 测试步骤"
                open={showMpHelp}
                onCancel={() => setShowMpHelp(false)}
                footer={[
                    <Button key="close" type="primary" onClick={() => setShowMpHelp(false)}>
                        关闭
                    </Button>,
                ]}
            >
                <ol style={{ paddingLeft: 18, margin: 0, lineHeight: 1.7 }}>
                    <li>关闭或重新编译启动微信小程序（清缓存更稳妥）</li>
                    <li>打开 Service Home</li>
                    <li>确认首页状态与所选预设一致（空态 / 继续处理 / VIN 补件）</li>
                    <li>按场景继续操作；Broker 侧用 Open Broker Case 核对 One Truth</li>
                </ol>
                <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
                    平台无法安全生成通用小程序 deep link 时，请用上述手动步骤验证。
                </Paragraph>
            </Modal>
        </div>
    );
}

function Metric({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
    return (
        <div
            style={{
                background: '#fafafa',
                border: '1px solid #f0f0f0',
                borderRadius: 8,
                padding: '8px 10px',
            }}
        >
            <div style={{ fontSize: 12, color: '#8c8c8c' }}>{label}</div>
            <div style={{ fontSize: 14, fontFamily: mono ? 'ui-monospace, SFMono-Regular, Menlo, monospace' : undefined }}>
                {value}
            </div>
        </div>
    );
}
