import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Tabs,
    Button,
    Steps,
    Alert,
    Input,
    Descriptions,
    Card,
    List,
    Image,
    message,
    Spin,
    Row,
    Col,
    Statistic,
    Space,
    Typography,
    Badge,
    Tag,
    Switch,
} from 'antd';
import {
    RobotOutlined,
    CheckCircleOutlined,
    SyncOutlined,
    CloseCircleOutlined,
    FileTextOutlined,
    PictureOutlined,
    GithubOutlined,
    BarChartOutlined,
    DollarOutlined,
    ThunderboltOutlined,
    CheckCircleFilled,
    CloseCircleFilled,
} from '@ant-design/icons';
import StewardChat from '../../components/chat/StewardChat';
import { startPolling, rewritePollPath, normalizeStatus, TERMINAL_STATES } from '../../api/polling';

const { Title } = Typography;

// ----------------------------------------------------
// API Path Definition (follows /api convention)
// ----------------------------------------------------
const resolveOrchestrateBase = () => {
    const raw = import.meta.env.VITE_ORCH_BASE || '/orchestrate';
    if (/^https?:\/\//.test(raw)) {
        return raw.replace(/\/$/, '');
    }
    const normalized = raw.startsWith('/') ? raw : `/${raw}`;
    return normalized.replace(/\/$/, '');
};

const API_BASE = resolveOrchestrateBase();
const withApiBase = (path = '') => {
    if (!path) return API_BASE;
    return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
};

// ---- begin: run helpers ----
const ALLOW_KEYS = new Set([
    'preset', 'dataset', 'sample_size', 'top_k', 'rrf_k',
    'rerank', 'detail', 'commit'
]);

const toPlainValue = (v) => {
    // handle AntD select labelInValue or objects with { value }
    if (v && typeof v === 'object') {
        if ('value' in v) return v.value;
        // arrays -> plain arrays
        if (Array.isArray(v)) return v.map(toPlainValue);
        // plain object -> keep only primitives
        return Object.fromEntries(Object.entries(v)
            .filter(([_, val]) => val !== undefined && typeof val !== 'function'));
    }
    if (typeof v === 'function') return undefined;
    return v;
};

const buildRunPayload = (preset, overrides) => {
    const merged = { preset, ...(overrides || {}) };
    const cleaned = Object.fromEntries(
        Object.entries(merged)
            .filter(([k, v]) => ALLOW_KEYS.has(k) && v !== undefined && v !== null)
            .map(([k, v]) => [k, toPlainValue(v)])
    );
    // enforce commit=true unless caller sets explicitly
    if (!('commit' in cleaned)) cleaned.commit = true;
    return cleaned;
};

const extractReadableError = async (response) => {
    let msg = `HTTP ${response.status}`;
    try {
        const txt = await response.text();
        try {
            const j = JSON.parse(txt);
            msg = (j?.detail ?? j?.error ?? j?.message ?? txt) || msg;
        } catch {
            msg = txt || msg;
        }
    } catch { }
    return String(msg);
};
// ---- end: run helpers ----

// ----------------------------------------------------
// Mock API Calls (for frontend standalone development)
// ----------------------------------------------------
const mockApi = {
    run: async () => {
        await new Promise((res) => setTimeout(res, 500));
        return { run_id: `run_MOCK_${Date.now()}` };
    },
    status: async (run_id) => {
        await new Promise((res) => setTimeout(res, 2000));
        const stages = ['SMOKE', 'GRID', 'AB', 'SELECT', 'PUBLISH', 'COMPLETED', 'HEALTH_FAIL', 'RUNNER_TIMEOUT'];
        const randomStatus = stages[Math.floor(Math.random() * stages.length)];
        return { stage: randomStatus };
    },
    report: async (run_id) => {
        await new Promise((res) => setTimeout(res, 1000));
        return {
            run_id: run_id,
            sla_metrics: {
                p95_latency: '180.5ms',
                recall: '0.985',
                cost: '$0.0024',
            },
            artifacts: {
                winners_md: '/api/mock/path/to/winners.md', // Path should also be API path
                pareto_png: 'https://gw.alipayobjects.com/zos/antfincdn/RPoZHMSuAQ/chart-1.png', // Placeholder image
                ab_diff_png: 'https://gw.alipayobjects.com/zos/antfincdn/k%24sL1%24FdI/chart-2.png', // Placeholder image
                failTopN_csv: '/api/mock/path/to/failTopN.csv',
            },
        };
    },
    abort: async (run_id) => {
        await new Promise((res) => setTimeout(res, 500));
        return { status: 'aborted' };
    }
};
// ----------------------------------------------------

// Stage definitions
const STAGES = ['SMOKE', 'GRID', 'AB', 'SELECT', 'PUBLISH'];
const STAGE_MAP = STAGES.reduce((acc, stage, index) => {
    acc[stage] = index;
    return acc;
}, {});
const SUCCESS_STATES = new Set(['SUCCEEDED', 'COMPLETED', 'DONE']);
const FAILURE_STATES = new Set(['FAILED', 'ERROR', 'CANCELLED', 'CANCELED', 'ABORTED', 'TIMEOUT']);

const StewardDashboard = () => {
    const [runId, setRunId] = useState(null);
    const [runPollUrl, setRunPollUrl] = useState(null);
    const [lastJobMeta, setLastJobMeta] = useState(null);
    const DEBUG_ON = (typeof window !== 'undefined') && window.localStorage?.getItem('DEBUG_STEWARD') === '1';
    const [currentStage, setCurrentStage] = useState(0);
    const [runStatus, setRunStatus] = useState(null);
    const [errorInfo, setErrorInfo] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [reportLoading, setReportLoading] = useState(false);
    const [reflections, setReflections] = useState([]);
    const [detailLevel, setDetailLevel] = useState('lite');

    const chatStopRef = useRef(null);
    const latestRunIdRef = useRef(null);
    const pollCtlRef = useRef(null);
    const pollTimeoutRef = useRef(null);

    const registerChatStop = useCallback((stopper) => {
        chatStopRef.current = typeof stopper === 'function' ? stopper : null;
    }, []);

    const stopAllPolling = useCallback(() => {
        if (pollCtlRef.current) {
            try {
                pollCtlRef.current.stop?.();
            } catch {
                // noop
            }
            pollCtlRef.current = null;
        }
        if (pollTimeoutRef.current) {
            clearTimeout(pollTimeoutRef.current);
            pollTimeoutRef.current = null;
        }
        if (chatStopRef.current) {
            chatStopRef.current();
        }
    }, []);

    // Cleanup polling
    useEffect(() => {
        return () => {
            stopAllPolling();
        };
    }, [stopAllPolling]);

    // 3. Handle report fetching
    const handleFetchReport = async (id) => {
        if (!id) return;
        setReportLoading(true);
        message.loading({ content: `Fetching report (ID: ${id})...`, key: 'report' });
        try {
            // Switch to real API
            // const data = await fetch(withApiBase(`/report?run_id=${id}`)).then(res => res.json());
            const data = await mockApi.report(id);

            setReportData(data);
            message.success({ content: 'Report loaded successfully!', key: 'report' });
        } catch (e) {
            const msg = e?.message || (typeof e === 'string' ? e : 'Request failed');
            message.error({ content: msg });
        } finally {
            setReportLoading(false);
        }
    };

    const applySnapshot = useCallback((snapshot) => {
        if (!snapshot || typeof snapshot !== 'object') {
            return;
        }

        const stage = snapshot.stage;
        if (stage) {
            const stageIndex = STAGE_MAP[stage];
            if (stageIndex !== undefined) {
                setCurrentStage(stageIndex);
            }
        }

        const reflectionList = Array.isArray(snapshot.reflections) ? snapshot.reflections : null;
        if (reflectionList) {
            setReflections(reflectionList);
        }
    }, []);

    const applyPayloadSnapshot = useCallback(
        (payload) => {
            if (!payload || typeof payload !== 'object') return;
            const snapshot = payload?.job ?? payload;
            applySnapshot(snapshot);
        },
        [applySnapshot]
    );

    const handleTerminalStatus = useCallback(
        (state, payload) => {
            const snapshot = payload && typeof payload === 'object' ? payload?.job ?? payload : null;
            if (snapshot) {
                applySnapshot(snapshot);
            }

            const normalized = payload && typeof payload === 'object' ? normalizeStatus(payload) : { state };
            setLastJobMeta((prev) => {
                if (!prev || prev.id !== latestRunIdRef.current) return prev;
                const targetPoll = prev.backendPoll || prev.pollUrl || (runId ? `/orchestrate/status/${runId}` : '');
                return {
                    ...prev,
                    status: normalized.state || state,
                    finishedAt: normalized.finishedAt ?? new Date().toISOString(),
                    orchestratePath: rewritePollPath(targetPoll, detailLevel),
                    detail: detailLevel,
                };
            });

            if (SUCCESS_STATES.has(state)) {
                setCurrentStage(STAGES.length);
                setErrorInfo(null);
                message.success('Pipeline run successful!');
                if (latestRunIdRef.current) {
                    handleFetchReport(latestRunIdRef.current);
                }
                return;
            }

            if (TERMINAL_STATES.has(state)) {
                const reason =
                    snapshot?.reason ||
                    snapshot?.detail ||
                    snapshot?.message ||
                    (payload && typeof payload === 'object' ? payload?.error : null) ||
                    `Pipeline run ended with status ${state}`;
                setErrorInfo(reason);
                message.error(reason);
                return;
            }

            // non-terminal fallthrough (should not happen)
            setErrorInfo(`Unexpected polling completion state: ${state || 'UNKNOWN'}`);
        },
        [applySnapshot, detailLevel, handleFetchReport, runId]
    );

    const startStatusPolling = useCallback(
        (id, pollUrl, detail = 'lite') => {
            if (pollCtlRef.current) {
                try {
                    pollCtlRef.current.stop?.();
                } catch {
                    // noop
                }
                pollCtlRef.current = null;
            }

            if (!id && !pollUrl) return;

            if (pollTimeoutRef.current) {
                clearTimeout(pollTimeoutRef.current);
                pollTimeoutRef.current = null;
            }

            pollTimeoutRef.current = setTimeout(() => {
                if (pollCtlRef.current) {
                    try {
                        pollCtlRef.current.stop?.();
                    } catch {
                        // noop
                    }
                    pollCtlRef.current = null;
                }
                setIsLoading(false);
                setRunStatus('TIMEOUT');
                setErrorInfo('Polling timed out after 20 minutes');
                setLastJobMeta((prev) => {
                    if (!prev || prev.id !== latestRunIdRef.current) return prev;
                    return {
                        ...prev,
                        status: 'TIMEOUT',
                        finishedAt: new Date().toISOString(),
                    };
                });
                message.error('Polling timed out after 20 minutes');
            }, 20 * 60 * 1000);

            const resolved = pollUrl || `/orchestrate/status/${id}`;
            latestRunIdRef.current = id;
            pollCtlRef.current = startPolling({
                pollPath: resolved,
                intervalMs: 5000,
                detail,
                onUpdate: ({ state, payload }) => {
                    if (state) {
                        setRunStatus(state);
                        if (!TERMINAL_STATES.has(state)) {
                            setErrorInfo(null);
                        }
                    }
                    applyPayloadSnapshot(payload);
                },
                onDone: (state, payload) => {
                    if (pollTimeoutRef.current) {
                        clearTimeout(pollTimeoutRef.current);
                        pollTimeoutRef.current = null;
                    }
                    pollCtlRef.current = null;

                    const normalizedState =
                        payload && typeof payload === 'object' ? normalizeStatus(payload).state : state;
                    const finalState = normalizedState || state || 'UNKNOWN';
                    setRunStatus(finalState);
                    setIsLoading(false);

                    if (TERMINAL_STATES.has(finalState) || FAILURE_STATES.has(finalState) || SUCCESS_STATES.has(finalState)) {
                        handleTerminalStatus(finalState, payload);
                        return;
                    }

                    // fallback: treat as error
                    handleTerminalStatus('ERROR', payload);
                },
            });
        },
        [applyPayloadSnapshot, handleTerminalStatus]
    );

    // 1. Start run
    const handleRun = async (preset = 'smoke', overrides = {}) => {
        if (isLoading) return;
        stopAllPolling();
        setIsLoading(true);
        setErrorInfo(null);
        setReportData(null);
        setRunPollUrl(null);
        try {
            const payload = buildRunPayload(preset, overrides);
            message.loading({ content: 'Starting pipeline…', key: 'run' });
            const response = await fetch(withApiBase('/run?commit=true'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const errMsg = await extractReadableError(response);
                const friendlyMsg =
                    response.status === 404
                        ? `后端服务未运行或路径不存在 (${errMsg})。请检查后端服务是否在 localhost:8000 运行。`
                        : errMsg;
                message.error({ content: friendlyMsg, key: 'run', duration: 5 });
                setErrorInfo(friendlyMsg);
                setIsLoading(false);
                setRunStatus('ERROR');
                return;
            }
            const data = await response.json();
            const id = data?.job_id ?? data?.jobId ?? data?.run_id ?? null;
            const pollUrl = typeof data?.poll === 'string' ? data.poll : '';

            if (!id) {
                const msg = 'Missing job_id from backend response';
                setErrorInfo(msg);
                message.error({ content: msg });
                setIsLoading(false);
                setRunStatus('ERROR');
                return;
            }

            const fallbackPoll = `/orchestrate/status/${id}`;
            const resolvedPoll = pollUrl || fallbackPoll;
            const orchestratePath = rewritePollPath(resolvedPoll, detailLevel);

            setRunId(id);
            setRunPollUrl(pollUrl || null);
            const startedAt = new Date().toISOString();
            const meta = {
                id,
                backendPoll: pollUrl || null,
                pollUrl: resolvedPoll,
                orchestratePath,
                startedAt,
                status: 'RUNNING',
                detail: detailLevel,
            };
            setLastJobMeta(meta);
            console.table([meta]);
            message.success({ content: `Run started • job_id=${id}`, key: 'run', duration: 2 });
            try {
                document.title = `Steward · ${id.slice(0, 8)}…`;
            } catch {
                /* noop */
            }

            setRunStatus('RUNNING');
            setCurrentStage(0);
            setReflections([]);
            startStatusPolling(id, pollUrl, detailLevel);
        } catch (e) {
            const msg = e?.message || 'Request failed';
            const friendlyMsg =
                msg.includes('Failed to fetch') || msg.includes('NetworkError')
                    ? '无法连接到后端服务。请检查后端服务是否在 localhost:8000 运行。'
                    : msg;
            message.error({ content: friendlyMsg, key: 'run', duration: 5 });
            setErrorInfo(friendlyMsg);
            setRunStatus('ERROR');
            setIsLoading(false);
        }
    };

    // 4. Retry/Abort
    const handleRetry = () => {
        handleRun('smoke'); // Retry is just rerunning
    };

    const handleAbort = async () => {
        if (!runId) return;
        stopAllPolling();
        // Switch to real API
        // await fetch(withApiBase(`/abort?run_id=${runId}`), { method: 'POST' });
        await mockApi.abort(runId);
        setRunStatus('ABORTED');
        setIsLoading(false);
        setErrorInfo('Run aborted');
        setRunPollUrl(null);
        setLastJobMeta((prev) => {
            if (!prev || prev.id !== runId) return prev;
            return {
                ...prev,
                status: 'ABORTED',
                finishedAt: new Date().toISOString(),
            };
        });
        latestRunIdRef.current = null;
        message.warning('Run aborted');
    };

    // Render report (shared component)
    const renderReport = (data) => {
        if (!data) return null;
        return (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Card title={`Report Details (Run ID: ${data.run_id})`}>
                    <Descriptions bordered>
                        <Descriptions.Item label="P95 Latency" span={1}>
                            <Statistic value={data.sla_metrics.p95_latency} />
                        </Descriptions.Item>
                        <Descriptions.Item label="Recall" span={1}>
                            <Statistic value={data.sla_metrics.recall} />
                        </Descriptions.Item>
                        <Descriptions.Item label="Estimated Cost" span={1}>
                            <Statistic value={data.sla_metrics.cost} />
                        </Descriptions.Item>
                    </Descriptions>
                </Card>

                <Row gutter={16}>
                    <Col xs={24} md={12}>
                        <Card title={<><PictureOutlined /> Pareto Frontier</>}>
                            <Image width="100%" src={data.artifacts.pareto_png} />
                        </Card>
                    </Col>
                    <Col xs={24} md={12}>
                        <Card title={<><BarChartOutlined /> A/B Comparison</>}>
                            <Image width="100%" src={data.artifacts.ab_diff_png} />
                        </Card>
                    </Col>
                </Row>

                <Card title="Artifacts Download">
                    <List
                        dataSource={[
                            { name: 'winners.md', link: data.artifacts.winners_md, icon: <GithubOutlined /> },
                            { name: 'failTopN.csv', link: data.artifacts.failTopN_csv, icon: <FileTextOutlined /> },
                        ]}
                        renderItem={(item) => (
                            <List.Item>
                                <List.Item.Meta
                                    avatar={item.icon}
                                    title={<a href={item.link} target="_blank" rel="noopener noreferrer">{item.name}</a>}
                                />
                            </List.Item>
                        )}
                    />
                </Card>
            </Space>
        );
    };

    // Tab 1: Start new task
    const renderRunPipelineTab = () => {
        const failure = runStatus ? FAILURE_STATES.has(runStatus) : false;
        const success = runStatus ? SUCCESS_STATES.has(runStatus) : false;
        const stepsStatus = failure ? 'error' : success ? 'finish' : 'process';

        const fallbackPollPath = runId ? `/orchestrate/status/${runId}` : '';
        const debugPollPath = runId
            ? rewritePollPath(runPollUrl || fallbackPollPath, detailLevel)
            : lastJobMeta?.orchestratePath || '';

        return (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Button
                    type="primary"
                    size="large"
                    icon={<RobotOutlined />}
                    onClick={() => handleRun('smoke')}
                    loading={isLoading}
                    disabled={isLoading}
                >
                    {isLoading ? 'Pipeline running…' : 'Start New Evaluation'}
                </Button>

                {runId && (
                    <>
                        <Card title="Real-time Monitoring">
                            <Steps
                                current={currentStage}
                                status={stepsStatus}
                            >
                                {STAGES.map((stage) => (
                                    <Steps.Step key={stage} title={stage} />
                                ))}
                            </Steps>

                            {failure && (
                                <Alert
                                    message="Run Failed"
                                    description={errorInfo || 'Unknown error'}
                                    type="error"
                                    showIcon
                                    action={
                                        <Space>
                                            <Button onClick={() => handleRetry()} size="small" type="primary">
                                                Retry
                                            </Button>
                                            <Button onClick={() => handleAbort()} size="small" danger>
                                                Abort
                                            </Button>
                                        </Space>
                                    }
                                    style={{ marginTop: 24 }}
                                />
                            )}

                            {success && (
                                <Alert
                                    message="Pipeline run successful"
                                    type="success"
                                    showIcon
                                    style={{ marginTop: 24 }}
                                />
                            )}
                        </Card>

                        {/* Reflection Cards */}
                        {reflections.length > 0 && (
                            <Card
                                title={
                                    <Space>
                                        <span>Reflections</span>
                                        <Switch
                                            checkedChildren="Full"
                                            unCheckedChildren="Lite"
                                            checked={detailLevel === 'full'}
                                            onChange={(checked) => {
                                                const nextDetail = checked ? 'full' : 'lite';
                                                setDetailLevel(nextDetail);
                                                // Re-poll with new detail level
                                                if (runId && runStatus && !TERMINAL_STATES.has(runStatus)) {
                                                    startStatusPolling(runId, runPollUrl, nextDetail);
                                                }
                                                setLastJobMeta((prev) => {
                                                    if (!prev) return prev;
                                                    const targetPoll = runPollUrl || prev.pollUrl || (runId ? `/orchestrate/status/${runId}` : '');
                                                    return {
                                                        ...prev,
                                                        orchestratePath: rewritePollPath(targetPoll, nextDetail),
                                                        detail: nextDetail,
                                                    };
                                                });
                                            }}
                                        />
                                    </Space>
                                }
                                style={{ marginTop: 16 }}
                            >
                                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                    {reflections.map((reflection, idx) => (
                                        <Card
                                            key={idx}
                                            title={`Reflection · ${reflection.stage}`}
                                            size="small"
                                            extra={
                                                reflection.blocked && (
                                                    <Tag color="orange">LLM cost cap reached · fallback to rules</Tag>
                                                )
                                            }
                                        >
                                            {reflection.blocked && (
                                                <Alert
                                                    message="LLM cost cap reached · fallback to rules"
                                                    type="warning"
                                                    showIcon
                                                    style={{ marginBottom: 16 }}
                                                />
                                            )}
                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                {/* Four Badges */}
                                                <Space wrap>
                                                    <Badge
                                                        count={reflection.cost_usd?.toFixed(4) || '0.0000'}
                                                        showZero
                                                        style={{ backgroundColor: '#52c41a' }}
                                                    >
                                                        <Tag icon={<DollarOutlined />} color="green">
                                                            Cost
                                                        </Tag>
                                                    </Badge>
                                                    <Badge
                                                        count={reflection.tokens || 0}
                                                        showZero
                                                        style={{ backgroundColor: '#1890ff' }}
                                                    >
                                                        <Tag icon={<ThunderboltOutlined />} color="blue">
                                                            Tokens
                                                        </Tag>
                                                    </Badge>
                                                    <Tag
                                                        icon={reflection.cache_hit ? <CheckCircleFilled /> : <CloseCircleFilled />}
                                                        color={reflection.cache_hit ? 'green' : 'default'}
                                                    >
                                                        {reflection.cache_hit ? 'HIT' : 'MISS'}
                                                    </Tag>
                                                    <Tag color={reflection.blocked ? 'orange' : 'green'}>
                                                        {reflection.blocked ? 'BLOCKED' : 'OK'}
                                                    </Tag>
                                                </Space>

                                                {/* Rationale Summary */}
                                                {reflection.rationale_md && (
                                                    <div style={{
                                                        padding: '12px',
                                                        background: '#f5f5f5',
                                                        borderRadius: '4px',
                                                        maxHeight: '200px',
                                                        overflow: 'auto'
                                                    }}>
                                                        <Typography.Text>
                                                            {reflection.rationale_md}
                                                        </Typography.Text>
                                                    </div>
                                                )}

                                                {/* Next Actions */}
                                                {reflection.next_actions && reflection.next_actions.length > 0 && (
                                                    <Space wrap>
                                                        {reflection.next_actions.map((action, actIdx) => (
                                                            <Button
                                                                key={actIdx}
                                                                type="primary"
                                                                onClick={() => {
                                                                    // Extract preset from action id (e.g., "proceed_to_grid" -> "grid")
                                                                    const preset = action.id.replace('proceed_to_', '');
                                                                    handleRun(preset, {});
                                                                }}
                                                            >
                                                                {action.label} {action.eta_min ? `(${action.eta_min}min)` : ''}
                                                            </Button>
                                                        ))}
                                                    </Space>
                                                )}

                                                {(!reflection.next_actions || reflection.next_actions.length === 0) && (
                                                    <Typography.Text type="secondary">
                                                        (no reflection / rule-engine)
                                                    </Typography.Text>
                                                )}
                                            </Space>
                                        </Card>
                                    ))}
                                </Space>
                            </Card>
                        )}
                    </>
                )}

                {/* Report automatically displayed below after task completion */}
                {success && renderReport(reportData)}

                {DEBUG_ON && lastJobMeta && (
                    <div style={{
                        marginTop: 12,
                        padding: 10,
                        border: '1px dashed #555',
                        borderRadius: 8,
                        display: 'flex',
                        gap: 12,
                        alignItems: 'center',
                        flexWrap: 'wrap',
                    }}>
                        <span style={{ opacity: 0.8 }}>Debug:</span>
                        <span>job_id: <code>{lastJobMeta.id}</code></span>
                        <button
                            type="button"
                            onClick={() => lastJobMeta.id && navigator.clipboard?.writeText(lastJobMeta.id)}
                        >
                            Copy ID
                        </button>
                        {debugPollPath && (
                            <>
                                <span>
                                    poll:{' '}
                                    <code>{debugPollPath}</code>
                                </span>
                                <button
                                    type="button"
                                    onClick={() => navigator.clipboard?.writeText(debugPollPath)}
                                >
                                    Copy poll
                                </button>
                                <button
                                    type="button"
                                    onClick={() => window.open(debugPollPath, '_blank')}
                                >
                                    Open status
                                </button>
                            </>
                        )}
                        <button
                            type="button"
                            onClick={() => console.table([lastJobMeta])}
                        >
                            Log
                        </button>
                    </div>
                )}
            </Space>
        );
    };

    // Tab 2: View reports
    const renderViewReportTab = () => (
        <Spin spinning={reportLoading}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Input.Search
                    placeholder="Paste Run ID (e.g., run_MOCK_12345)"
                    enterButton="Fetch Report"
                    size="large"
                    onSearch={(value) => handleFetchReport(value)}
                    loading={reportLoading}
                />
                {reportData && renderReport(reportData)}
            </Space>
        </Spin>
    );

    return (
        <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
            <Card>
                <Title level={2}>Lab Steward</Title>
                <Typography.Text type="secondary">Automated RAG Evaluation Pipeline</Typography.Text>
            </Card>
            <Card style={{ marginTop: 16 }}>
                <Tabs
                    defaultActiveKey="1"
                    onChange={() => {
                        // Reset report when switching tabs
                        setReportData(null);
                    }}
                    items={[
                        {
                            label: 'Start New Task',
                            key: '1',
                            children: renderRunPipelineTab(),
                        },
                        {
                            label: 'View Historical Reports',
                            key: '2',
                            children: renderViewReportTab(),
                        },
                        {
                            label: 'Chat',
                            key: '3',
                            children: (
                                <StewardChat
                                    onBeforeStart={stopAllPolling}
                                    onRegisterStop={registerChatStop}
                                    onStop={() => registerChatStop(null)}
                                />
                            ),
                        },
                    ]}
                />
            </Card>
        </div>
    );
};

export default StewardDashboard;

