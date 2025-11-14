/**
 * Metrics Hub Page
 * Read-only metrics view with KPI cards, trilines chart, and job details drawer
 */
import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Typography,
    Space,
    List,
    Tag,
    Button,
    Spin,
    Empty,
    Alert,
    Drawer,
    Timeline,
    Collapse,
    Row,
    Col,
    Select,
    Skeleton,
} from 'antd';
import {
    BarChartOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    FileImageOutlined,
    FileTextOutlined,
    ReloadOutlined,
    CloseOutlined,
    LinkOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useRagLabStore } from '../../store/ragLabStore';
import type { JobMeta } from '../../api/experiment';
import * as experimentApi from '../../api/experiment';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface TrilinesPoint {
    budget: number;
    t: number;
    p95_ms: number;
    recall10: number;
    cost_1k_usd: number;
}

interface TrilinesData {
    points: TrilinesPoint[];
    budgets: number[];
    updated_at: string;
}

export const MetricsHub = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const { history, loadHistory } = useRagLabStore();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [selectedJob, setSelectedJob] = useState<JobMeta | null>(null);
    const [jobDetail, setJobDetail] = useState<any>(null);
    const [artifacts, setArtifacts] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [detailLoading, setDetailLoading] = useState(false);

    // Metrics data
    const [trilinesData, setTrilinesData] = useState<TrilinesData | null>(null);
    const [trilinesLoading, setTrilinesLoading] = useState(false);
    const [trilinesError, setTrilinesError] = useState<string | null>(null);
    const [selectedBudget, setSelectedBudget] = useState<number | null>(null);
    const [langfuseUrl, setLangfuseUrl] = useState<string | null>(null);

    // Fetch trilines data
    const fetchTrilines = async () => {
        setTrilinesLoading(true);
        setTrilinesError(null);
        try {
            const response = await fetch('/api/metrics/trilines');
            if (!response.ok) {
                throw new Error(`Failed to fetch trilines: ${response.status}`);
            }
            const data: TrilinesData = await response.json();
            setTrilinesData(data);
            // Set default budget to latest (highest)
            if (data.budgets.length > 0 && !selectedBudget) {
                setSelectedBudget(Math.max(...data.budgets));
            }
        } catch (err: any) {
            setTrilinesError(err.message || 'Failed to fetch trilines data');
            console.error('Trilines fetch error:', err);
        } finally {
            setTrilinesLoading(false);
        }
    };

    // Fetch Langfuse URL
    const fetchLangfuseUrl = async () => {
        try {
            const response = await fetch('/api/metrics/obs/url');
            if (response.status === 204) {
                setLangfuseUrl(null);
                return;
            }
            if (!response.ok) {
                throw new Error(`Failed to fetch Langfuse URL: ${response.status}`);
            }
            const data = await response.json();
            setLangfuseUrl(data.url || null);
        } catch (err: any) {
            console.warn('Failed to fetch Langfuse URL:', err);
            setLangfuseUrl(null);
        }
    };

    const fetchJobs = async () => {
        setLoading(true);
        setError(null);
        try {
            await loadHistory();
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to fetch jobs');
        } finally {
            setLoading(false);
        }
    };

    const fetchJobDetail = async (job: JobMeta) => {
        setDetailLoading(true);
        try {
            const detail = await experimentApi.getJobDetail(job.job_id);
            setJobDetail(detail);
            // Fetch artifacts if job succeeded
            if (detail.status === 'SUCCEEDED') {
                try {
                    const artifactsData = await experimentApi.getJobArtifacts(job.job_id);
                    setArtifacts(artifactsData);
                } catch (err) {
                    console.warn('Failed to fetch artifacts:', err);
                }
            }
            // Fetch logs
            try {
                const logsString = await experimentApi.getJobLogs(job.job_id, 500);
                const logsArray = logsString ? logsString.split('\n').filter(line => line.trim() !== '') : [];
                setLogs(logsArray);
            } catch (err) {
                console.warn('Failed to fetch logs:', err);
                setLogs([]);
            }
        } catch (err: any) {
            console.error('Failed to fetch job details:', err);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleRowClick = (job: JobMeta) => {
        setSelectedJob(job);
        setDrawerVisible(true);
        setJobDetail(null);
        setArtifacts(null);
        setLogs([]);
        fetchJobDetail(job);
        // Update URL with jobId
        const newParams = new URLSearchParams(searchParams);
        newParams.set('jobId', job.job_id);
        setSearchParams(newParams);
    };

    const handleDrawerClose = () => {
        setDrawerVisible(false);
        setSelectedJob(null);
        setJobDetail(null);
        setArtifacts(null);
        setLogs([]);
        // Remove jobId from URL
        const newParams = new URLSearchParams(searchParams);
        newParams.delete('jobId');
        setSearchParams(newParams);
    };

    // Deep link: auto-open drawer if jobId in URL
    useEffect(() => {
        const jobId = searchParams.get('jobId');
        if (jobId && history && history.length > 0 && !drawerVisible) {
            const job = history.find(j => j.job_id === jobId);
            if (job && !selectedJob) {
                setSelectedJob(job);
                setDrawerVisible(true);
                fetchJobDetail(job);
            }
        }
    }, [searchParams, history, drawerVisible, selectedJob]);

    useEffect(() => {
        fetchJobs();
        fetchTrilines();
        fetchLangfuseUrl();
    }, []);

    // Get current KPI values based on selected budget
    const getCurrentKPI = () => {
        if (!trilinesData || !selectedBudget) {
            return { p95: null, recall10: null, cost1k: null };
        }
        const point = trilinesData.points.find(p => p.budget === selectedBudget);
        if (!point) {
            return { p95: null, recall10: null, cost1k: null };
        }
        return {
            p95: point.p95_ms,
            recall10: point.recall10,
            cost1k: point.cost_1k_usd,
        };
    };

    // Get chart data filtered by selected budget
    const getChartData = () => {
        if (!trilinesData || !selectedBudget) {
            return [];
        }
        // Filter points for selected budget and sort by budget
        return trilinesData.points
            .filter(p => p.budget === selectedBudget)
            .sort((a, b) => a.budget - b.budget)
            .map(p => ({
                budget: p.budget,
                p95_ms: p.p95_ms,
                recall10: p.recall10,
                cost_1k_usd: p.cost_1k_usd,
            }));
    };

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'SUCCEEDED':
                return 'success';
            case 'RUNNING':
                return 'processing';
            case 'QUEUED':
                return 'default';
            case 'FAILED':
            case 'ABORTED':
                return 'error';
            case 'CANCELLED':
                return 'warning';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'SUCCEEDED':
                return <CheckCircleOutlined />;
            case 'RUNNING':
                return <ClockCircleOutlined />;
            case 'QUEUED':
                return <ClockCircleOutlined />;
            case 'FAILED':
            case 'ABORTED':
                return <CloseCircleOutlined />;
            default:
                return <ClockCircleOutlined />;
        }
    };

    const formatTimestamp = (ts?: string | null) => {
        if (!ts) return '-';
        try {
            return new Date(ts).toLocaleString();
        } catch {
            return ts;
        }
    };

    const kpi = getCurrentKPI();
    const chartData = getChartData();

    return (
        <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
            <Title level={2} style={{ marginBottom: '8px' }}>
                <BarChartOutlined /> Metrics Hub
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                View metrics and experiment results
            </Paragraph>

            {/* Error alerts */}
            {error && (
                <Alert
                    message="Error"
                    description={error}
                    type="error"
                    closable
                    onClose={() => setError(null)}
                    style={{ marginBottom: '16px' }}
                />
            )}
            {trilinesError && (
                <Alert
                    message="Metrics Error"
                    description={trilinesError}
                    type="warning"
                    closable
                    onClose={() => setTrilinesError(null)}
                    style={{ marginBottom: '16px' }}
                />
            )}

            {/* KPI Cards */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
                <Col xs={24} sm={8}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">P95 Latency</Text>
                            {trilinesLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpi.p95 !== null ? `${kpi.p95.toFixed(2)} ms` : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">Recall@10</Text>
                            {trilinesLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpi.recall10 !== null ? `${(kpi.recall10 * 100).toFixed(1)}%` : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">Cost/1k Queries</Text>
                            {trilinesLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpi.cost1k !== null ? `$${kpi.cost1k.toFixed(2)}` : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* Budget Selector */}
            {trilinesData && trilinesData.budgets.length > 0 && (
                <Card
                    bordered={false}
                    style={{ marginBottom: '24px' }}
                    extra={
                        <Space>
                            <Text type="secondary">Budget:</Text>
                            <Select
                                value={selectedBudget}
                                onChange={setSelectedBudget}
                                style={{ width: 120 }}
                                size="small"
                            >
                                {trilinesData.budgets.map(budget => (
                                    <Select.Option key={budget} value={budget}>
                                        {budget} ms
                                    </Select.Option>
                                ))}
                            </Select>
                        </Space>
                    }
                >
                    {/* Trilines Chart */}
                    {trilinesLoading ? (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <Spin size="large" />
                        </div>
                    ) : chartData.length === 0 ? (
                        <Empty description="No data available for selected budget" />
                    ) : (
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                                <XAxis dataKey="budget" stroke="#aaa" fontSize={12} />
                                <YAxis yAxisId="left" label={{ value: 'P95 (ms)', angle: -90, position: 'insideLeft', fill: '#aaa' }} stroke="#FF7F0E" />
                                <YAxis yAxisId="right" orientation="right" label={{ value: 'Recall@10 / Cost', angle: 90, position: 'insideRight', fill: '#aaa' }} stroke="#1f77b4" />
                                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none' }} itemStyle={{ color: '#eee' }} />
                                <Legend />
                                <Line yAxisId="left" type="monotone" dataKey="p95_ms" name="P95 (ms)" stroke="#FFA500" strokeWidth={2} dot={{ r: 4 }} />
                                <Line yAxisId="right" type="monotone" dataKey="recall10" name="Recall@10" stroke="#00BFFF" strokeWidth={2} dot={{ r: 4 }} />
                                <Line yAxisId="right" type="monotone" dataKey="cost_1k_usd" name="Cost/1k ($)" stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </Card>
            )}

            {/* Jobs List */}
            <Card
                bordered={false}
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={() => {
                            fetchJobs();
                            fetchTrilines();
                            fetchLangfuseUrl();
                        }}
                        loading={loading}
                    >
                        Refresh
                    </Button>
                }
            >
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" />
                    </div>
                ) : !history || history.length === 0 ? (
                    <Empty description="No records yet. Run experiments to see metrics here." />
                ) : (
                    <List
                        dataSource={history}
                        renderItem={(job: JobMeta) => (
                            <List.Item
                                style={{ cursor: 'pointer' }}
                                onClick={() => handleRowClick(job)}
                            >
                                <List.Item.Meta
                                    avatar={
                                        <Tag
                                            color={getStatusColor(job.status)}
                                            icon={getStatusIcon(job.status)}
                                        >
                                            {job.status}
                                        </Tag>
                                    }
                                    title={
                                        <Space>
                                            <Text code style={{ fontSize: '12px' }}>
                                                {job.job_id.substring(0, 8)}...
                                            </Text>
                                            {(job.status === 'RUNNING' || job.status === 'QUEUED') && (
                                                <Tag color="blue" icon={<ReloadOutlined spin />}>
                                                    Active
                                                </Tag>
                                            )}
                                        </Space>
                                    }
                                    description={
                                        <Space direction="vertical" size="small">
                                            <div>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    Created: {formatTimestamp(job.created_at)}
                                                </Text>
                                            </div>
                                            {job.finished_at && (
                                                <div>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        Finished: {formatTimestamp(job.finished_at)}
                                                    </Text>
                                                </div>
                                            )}
                                            {job.return_code !== null && job.return_code !== undefined && (
                                                <div>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        Return Code: {job.return_code}
                                                    </Text>
                                                </div>
                                            )}
                                            {job.params && Object.keys(job.params).length > 0 && (
                                                <div>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        Dataset: {job.params?.dataset_name ?? 'unknown'}
                                                    </Text>
                                                </div>
                                            )}
                                        </Space>
                                    }
                                />
                            </List.Item>
                        )}
                    />
                )}
            </Card>

            {/* Detail Drawer */}
            <Drawer
                title={
                    <Space>
                        <BarChartOutlined />
                        <Text strong>Job Details</Text>
                    </Space>
                }
                placement="right"
                size="large"
                onClose={handleDrawerClose}
                open={drawerVisible}
                extra={
                    <Space>
                        {langfuseUrl && (
                            <Button
                                type="primary"
                                icon={<LinkOutlined />}
                                onClick={() => window.open(langfuseUrl, '_blank')}
                            >
                                Open in Langfuse
                            </Button>
                        )}
                        <Button
                            type="text"
                            icon={<CloseOutlined />}
                            onClick={handleDrawerClose}
                        />
                    </Space>
                }
            >
                {detailLoading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" />
                    </div>
                ) : jobDetail ? (
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {/* Job Information */}
                        <Card title="Job Information" bordered={false} size="small">
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <div>
                                    <Text strong>Status: </Text>
                                    <Tag
                                        color={getStatusColor(jobDetail.status)}
                                        icon={getStatusIcon(jobDetail.status)}
                                    >
                                        {jobDetail.status}
                                    </Tag>
                                </div>

                                <div>
                                    <Text strong>Job ID: </Text>
                                    <Text code style={{ fontSize: '12px' }}>
                                        {jobDetail.job_id}
                                    </Text>
                                </div>

                                <div>
                                    <Text strong>Dataset: </Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {(() => {
                                            const dataset = jobDetail?.params?.dataset_name
                                                ?? jobDetail?.config?.dataset_name
                                                ?? (jobDetail?.cmd?.join(' ')?.match(/--dataset-name\s+(\S+)/)?.[1]);
                                            return dataset || 'unknown';
                                        })()} | Qrels: {(() => {
                                            const qrels = jobDetail?.params?.qrels_name
                                                ?? jobDetail?.config?.qrels_name
                                                ?? jobDetail?.cmd?.join(' ')?.match(/--qrels-name\s+(\S+)/)?.[1];
                                            return qrels ? qrels.replace('fiqa_qrels_', '').replace('_10k_v1', '').replace('_50k_v1', '').replace('_v1', '') : 'v1';
                                        })()} | Fields: title+abstract
                                    </Text>
                                </div>

                                {jobDetail.progress_hint && (
                                    <div>
                                        <Text strong>Progress: </Text>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            {jobDetail.progress_hint}
                                        </Text>
                                    </div>
                                )}

                                <Space direction="vertical" size="small">
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Queued: {formatTimestamp(jobDetail.queued_at)}
                                        </Text>
                                    </div>
                                    {jobDetail.started_at && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Started: {formatTimestamp(jobDetail.started_at)}
                                            </Text>
                                        </div>
                                    )}
                                    {jobDetail.finished_at && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Finished: {formatTimestamp(jobDetail.finished_at)}
                                            </Text>
                                        </div>
                                    )}
                                    {jobDetail.return_code !== null && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Return Code: {jobDetail.return_code}
                                            </Text>
                                        </div>
                                    )}
                                </Space>
                            </Space>
                        </Card>

                        {/* Timeline */}
                        <Card title="Job Timeline" bordered={false} size="small">
                            <Timeline
                                items={[
                                    {
                                        color: 'blue',
                                        children: (
                                            <div>
                                                <Text strong>Job Created</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.queued_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    jobDetail.started_at && {
                                        color: 'green',
                                        children: (
                                            <div>
                                                <Text strong>Job Started</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.started_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    jobDetail.finished_at && {
                                        color: jobDetail.status === 'SUCCEEDED' ? 'green' : 'red',
                                        children: (
                                            <div>
                                                <Text strong>
                                                    Job {jobDetail.status === 'SUCCEEDED' ? 'Completed' : 'Failed'}
                                                </Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.finished_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                ].filter(Boolean)}
                            />
                        </Card>

                        {/* Artifacts */}
                        <Card
                            title={
                                <Space>
                                    <FileImageOutlined /> Artifacts
                                </Space>
                            }
                            bordered={false}
                            size="small"
                        >
                            {artifacts?.artifacts ? (
                                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                    <div>
                                        <Text strong>Timestamp: </Text>
                                        <Text code style={{ fontSize: '12px' }}>
                                            {artifacts.artifacts.timestamp}
                                        </Text>
                                    </div>

                                    {artifacts.artifacts.combined_plot && (
                                        <div>
                                            <div style={{ marginBottom: '8px' }}>
                                                <Text strong>
                                                    <FileImageOutlined /> Combined Charts
                                                </Text>
                                            </div>
                                            <img
                                                src={`/${artifacts.artifacts.combined_plot}`}
                                                alt="Combined Charts"
                                                style={{
                                                    width: '100%',
                                                    borderRadius: '8px',
                                                    border: '1px solid #d9d9d9',
                                                }}
                                                onError={(e) => {
                                                    (e.target as HTMLImageElement).style.display = 'none';
                                                }}
                                            />
                                        </div>
                                    )}

                                    {artifacts.artifacts.report_data && (
                                        <Collapse>
                                            <Panel
                                                header={
                                                    <Space>
                                                        <FileTextOutlined />
                                                        <Text strong>Report Data</Text>
                                                    </Space>
                                                }
                                                key="report"
                                            >
                                                <pre style={{ fontSize: '11px', margin: 0 }}>
                                                    {JSON.stringify(artifacts.artifacts.report_data, null, 2)}
                                                </pre>
                                            </Panel>
                                        </Collapse>
                                    )}
                                </Space>
                            ) : jobDetail.status === 'SUCCEEDED' ? (
                                <Text type="secondary">Loading artifacts...</Text>
                            ) : (
                                <Text type="secondary">No artifacts available</Text>
                            )}
                        </Card>

                        {/* Logs */}
                        <Card
                            title="Job Logs"
                            bordered={false}
                            size="small"
                            extra={
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {(logs || []).length} lines
                                </Text>
                            }
                            style={{ maxHeight: '400px', overflow: 'auto' }}
                        >
                            {(logs || []).length > 0 ? (
                                <List
                                    dataSource={logs}
                                    renderItem={(line) => (
                                        <List.Item style={{ padding: '4px 0', fontFamily: 'monospace' }}>
                                            <Text
                                                style={{
                                                    fontSize: '12px',
                                                    color: line.includes('ERROR') || line.includes('FAILED')
                                                        ? '#ff4d4f'
                                                        : line.includes('WARNING')
                                                            ? '#faad14'
                                                            : '#fff',
                                                }}
                                            >
                                                {line}
                                            </Text>
                                        </List.Item>
                                    )}
                                    size="small"
                                />
                            ) : (
                                <Text type="secondary">No logs available</Text>
                            )}
                        </Card>
                    </Space>
                ) : (
                    <Alert message="Job not found" type="warning" />
                )}
            </Drawer>
        </div>
    );
};
