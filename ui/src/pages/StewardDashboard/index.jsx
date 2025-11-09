import React, { useState, useEffect, useRef } from 'react';
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

const StewardDashboard = () => {
    const [runId, setRunId] = useState(null);
    const [currentStage, setCurrentStage] = useState(0);
    const [runStatus, setRunStatus] = useState('idle'); // idle, running, success, failed
    const [errorInfo, setErrorInfo] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [reportLoading, setReportLoading] = useState(false);
    const [reflections, setReflections] = useState([]);
    const [detailLevel, setDetailLevel] = useState('lite');

    const pollIntervalRef = useRef(null);

    // Cleanup polling
    useEffect(() => {
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, []);

    const stopPolling = () => {
        if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
        }
    };

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
            message.error({ content: 'Failed to fetch report', key: 'report' });
        } finally {
            setReportLoading(false);
        }
    };

    // 2. Poll status
    const handlePollStatus = (id) => {
        stopPolling();
        pollIntervalRef.current = setInterval(async () => {
            try {
                // Use real API with detail=lite
                const data = await fetch(withApiBase(`/status?run_id=${id}&detail=${detailLevel}`)).then(res => res.json());
                // Fallback to mock if API fails
                // const data = await mockApi.status(id);

                const stageIndex = STAGE_MAP[data.stage];

                if (stageIndex !== undefined) {
                    setCurrentStage(stageIndex);
                }

                // Update reflections
                if (data.reflections && Array.isArray(data.reflections)) {
                    setReflections(data.reflections);
                }

                // Check failure status
                if (data.stage === 'HEALTH_FAIL' || data.stage === 'RUNNER_TIMEOUT' || data.status === 'failed') {
                    stopPolling();
                    setRunStatus('failed');
                    setErrorInfo(
                        data.stage === 'HEALTH_FAIL' ? 'Health check failed (HEALTH_FAIL)' :
                            data.stage === 'RUNNER_TIMEOUT' ? 'Runner timeout (RUNNER_TIMEOUT)' :
                                'Pipeline run failed',
                    );
                    message.error('Pipeline run failed');
                }

                // Check success status (assuming PUBLISH is the final step)
                if (data.stage === 'PUBLISH' || data.status === 'completed') {
                    setCurrentStage(STAGES.length); // Mark all completed
                    setRunStatus('success');
                    stopPolling();
                    message.success('Pipeline run successful!');
                    handleFetchReport(id); // Automatically fetch report
                }
            } catch (e) {
                console.error('Poll status error:', e);
                // Don't fail on network errors, just log
            }
        }, 5000); // Poll every 5 seconds
    };

    // 1. Start run
    const handleRun = async (preset = 'smoke', overrides = {}) => {
        stopPolling();
        setIsLoading(true);
        setRunStatus('running');
        setRunId(null);
        setReportData(null);
        setErrorInfo(null);
        setCurrentStage(0);
        setReflections([]);
        message.loading({ content: 'Starting pipeline...', key: 'run' });

        try {
            // Use real API
            const payload = { preset, overrides };
            const response = await fetch(withApiBase('/run?commit=true'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to start pipeline');
            }

            setRunId(data.run_id);
            message.success({ content: `Started successfully! Run ID: ${data.run_id}`, key: 'run' });
            handlePollStatus(data.run_id); // Start polling
        } catch (e) {
            setRunStatus('failed');
            setErrorInfo(e.message || 'Failed to start pipeline');
            message.error({ content: e.message || 'Failed to start pipeline', key: 'run' });
        } finally {
            setIsLoading(false);
        }
    };

    // 4. Retry/Abort
    const handleRetry = () => {
        handleRun(); // Retry is just rerunning
    };

    const handleAbort = async () => {
        if (!runId) return;
        stopPolling();
        // Switch to real API
        // await fetch(withApiBase(`/abort?run_id=${runId}`), { method: 'POST' });
        await mockApi.abort(runId);
        setRunStatus('idle');
        setErrorInfo('Run aborted');
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
    const renderRunPipelineTab = () => (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Button
                type="primary"
                size="large"
                icon={<RobotOutlined />}
                onClick={handleRun}
                loading={isLoading || (runStatus === 'running' && !errorInfo)}
            >
                {runStatus === 'running' ? 'Pipeline running...' : 'Start New Evaluation'}
            </Button>

            {runId && (
                <>
                    <Card title="Real-time Monitoring">
                        <Steps
                            current={currentStage}
                            status={runStatus === 'failed' ? 'error' : 'process'}
                        >
                            {STAGES.map((stage) => (
                                <Steps.Step key={stage} title={stage} />
                            ))}
                        </Steps>

                        {runStatus === 'failed' && (
                            <Alert
                                message="Run Failed"
                                description={errorInfo || 'Unknown error'}
                                type="error"
                                showIcon
                                action={
                                    <Space>
                                        <Button onClick={handleRetry} size="small" type="primary">
                                            Retry
                                        </Button>
                                        <Button onClick={handleAbort} size="small" danger>
                                            Abort
                                        </Button>
                                    </Space>
                                }
                                style={{ marginTop: 24 }}
                            />
                        )}

                        {runStatus === 'success' && (
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
                                            setDetailLevel(checked ? 'full' : 'lite');
                                            // Re-poll with new detail level
                                            if (runId) {
                                                handlePollStatus(runId);
                                            }
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
            {runStatus === 'success' && renderReport(reportData)}
        </Space>
    );

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
                    ]}
                />
            </Card>
        </div>
    );
};

export default StewardDashboard;

