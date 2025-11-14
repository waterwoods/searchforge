/**
 * RAG Lab Detail Page - V8
 * Job detail and analysis page
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Typography,
    Space,
    Tag,
    Button,
    Spin,
    Alert,
    Row,
    Col,
    Timeline,
    List,
    Collapse,
    Tooltip,
} from 'antd';
import {
    TrophyOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    FileImageOutlined,
    FileTextOutlined,
    ReloadOutlined,
    ArrowLeftOutlined,
} from '@ant-design/icons';
import * as experimentApi from '../api/experiment';

const { Title, Text } = Typography;
const { Panel } = Collapse;

const fallbackObsUrl = (traceId?: string) => {
    const host = import.meta.env.VITE_LANGFUSE_HOST?.replace(/\/+$/, '') ?? '';
    const proj = import.meta.env.VITE_LANGFUSE_PROJECT_ID ?? '';
    if (!host || !proj || !traceId) {
        return '';
    }
    const q = encodeURIComponent(traceId);
    return `${host}/project/${proj}/traces?query=${q}`;
};

export const RagLabDetailPage = () => {
    const { jobId } = useParams<{ jobId: string }>();
    const navigate = useNavigate();
    const [jobDetail, setJobDetail] = useState<any>(null);
    const [artifacts, setArtifacts] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchJobDetail = async () => {
        if (!jobId) return;
        setLoading(true);
        setError(null);
        try {
            const detail = await experimentApi.getJobDetail(jobId);
            setJobDetail(detail);
            // Fetch artifacts if job succeeded
            if (detail.status === 'SUCCEEDED') {
                try {
                    const artifactsData = await experimentApi.getJobArtifacts(jobId);
                    setArtifacts(artifactsData);
                } catch (err) {
                    console.warn('Failed to fetch artifacts:', err);
                }
            }
            // Fetch logs
            try {
                const logsString = await experimentApi.getJobLogs(jobId, 500);
                // Convert string to array, handling empty string
                const logsArray = logsString ? logsString.split('\n').filter(line => line.trim() !== '') : [];
                setLogs(logsArray);
            } catch (err) {
                console.warn('Failed to fetch logs:', err);
                setLogs([]); // Ensure logs is always an array even on error
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to fetch job details');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobDetail();
    }, [jobId]);

    const getStatusColor = (status?: string): string => {
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

    const getStatusIcon = (status?: string) => {
        switch (status) {
            case 'SUCCEEDED':
                return <CheckCircleOutlined />;
            case 'RUNNING':
                return <ClockCircleOutlined />;
            case 'FAILED':
            case 'ABORTED':
                return <CloseCircleOutlined />;
            default:
                return <ClockCircleOutlined />;
        }
    };

    const formatTimestamp = (ts?: string) => {
        if (!ts) return '-';
        try {
            return new Date(ts).toLocaleString();
        } catch {
            return ts;
        }
    };

    return (
        <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
            <Space style={{ marginBottom: '24px' }}>
                <Button
                    icon={<ArrowLeftOutlined />}
                    onClick={() => navigate('/rag-lab/history')}
                >
                    Back to History
                </Button>
                <Button
                    icon={<ReloadOutlined />}
                    onClick={fetchJobDetail}
                    loading={loading}
                >
                    Refresh
                </Button>
            </Space>

            <Title level={2} style={{ marginBottom: '8px' }}>
                <TrophyOutlined /> Job Details
            </Title>

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

            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                </div>
            ) : jobDetail ? (
                <Row gutter={16}>
                    {/* Left Column */}
                    <Col span={8}>
                        {/* Job Info */}
                        <Card title="Job Information" bordered={false} style={{ marginBottom: '16px' }}>
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
                                    <Text strong>Observability: </Text>
                                    {(() => {
                                        const fallbackUrl = jobDetail?.trace_id ? fallbackObsUrl(jobDetail.trace_id) : '';
                                        const openObsUrl = jobDetail?.obs_url || fallbackUrl;
                                        const tooltipTitle = openObsUrl ? 'Open in Langfuse' : 'trace pending';
                                        const handleOpen = () => {
                                            if (openObsUrl) {
                                                window.open(openObsUrl, '_blank', 'noopener');
                                            }
                                        };
                                        return (
                                            <Tooltip title={tooltipTitle}>
                                                <span>
                                                    <Button
                                                        type="link"
                                                        disabled={!openObsUrl}
                                                        onClick={handleOpen}
                                                        style={{ padding: 0, height: 'auto' }}
                                                    >
                                                        Open in Langfuse
                                                    </Button>
                                                </span>
                                            </Tooltip>
                                        );
                                    })()}
                                </div>

                                {/* Dataset Badge */}
                                <div>
                                    <Text strong>Dataset: </Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {(() => {
                                            // Try multiple sources: params > config > cmd parsing
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
                        <Card title="Job Timeline" bordered={false}>
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
                    </Col>

                    {/* Right Column */}
                    <Col span={16}>
                        {/* Artifacts */}
                        <Card
                            title={
                                <Space>
                                    <TrophyOutlined /> Artifacts
                                </Space>
                            }
                            bordered={false}
                            style={{ marginBottom: '16px' }}
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
                            extra={
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {(logs || []).length} lines
                                </Text>
                            }
                            style={{ maxHeight: '600px', overflow: 'auto' }}
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
                    </Col>
                </Row>
            ) : (
                <Alert message="Job not found" type="warning" />
            )}
        </div>
    );
};
