/**
 * RAG Lab History Page - V8
 * Job history list page
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
    Tooltip,
} from 'antd';
import {
    HistoryOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    EyeOutlined,
    ReloadOutlined,
} from '@ant-design/icons';
import { useRagLabStore } from '../store/ragLabStore';
import type { JobMeta } from '../api/experiment';

const { Title, Text, Paragraph } = Typography;

export const RagLabHistoryPage = () => {
    const navigate = useNavigate();
    const { history, loadHistory } = useRagLabStore();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [latestObs, setLatestObs] = useState<{ obs_url: string; trace_id: string } | null>(null);

    const fetchLatestObs = async () => {
        try {
            const response = await fetch('/obs/url');
            if (response.status === 204) {
                setLatestObs(null);
                return;
            }
            if (!response.ok) {
                setLatestObs(null);
                return;
            }
            const payload = await response.json();
            if (payload?.obs_url && payload?.trace_id) {
                setLatestObs({
                    obs_url: payload.obs_url as string,
                    trace_id: payload.trace_id as string,
                });
            } else {
                setLatestObs(null);
            }
        } catch {
            setLatestObs(null);
        }
    };

    const fetchJobs = async () => {
        setLoading(true);
        setError(null);
        try {
            // Load history with limit 100 to ensure we see all jobs including RUNNING/QUEUED
            await loadHistory();
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Failed to fetch jobs');
        } finally {
            await fetchLatestObs();
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, []);

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

    return (
        <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
            <Title level={2} style={{ marginBottom: '8px' }}>
                <HistoryOutlined /> RAG Lab - Job History
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                View and analyze all completed and running experiment jobs
            </Paragraph>

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

            <Card
                bordered={false}
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={fetchJobs}
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
                    <Empty description="No jobs found" />
                ) : (
                    <List
                        dataSource={history}
                        renderItem={(job: JobMeta) => {
                            const openUrl = latestObs?.obs_url ?? '';
                            const tooltipTitle = openUrl ? 'Open in Langfuse' : 'No recent trace';
                            const openLangfuse = () => {
                                if (openUrl) {
                                    window.open(openUrl, '_blank', 'noopener');
                                }
                            };
                            const obsButton = (
                                <Tooltip key="obs" title={tooltipTitle}>
                                    <span>
                                        <Button type="link" disabled={!openUrl} onClick={openLangfuse}>
                                            Open in Langfuse
                                        </Button>
                                    </span>
                                </Tooltip>
                            );
                            const obsInline = (
                                <Tooltip title={tooltipTitle}>
                                    <span>
                                        <Button
                                            type="link"
                                            disabled={!openUrl}
                                            onClick={openLangfuse}
                                            style={{ padding: 0, height: 'auto' }}
                                        >
                                            Open in Langfuse
                                        </Button>
                                    </span>
                                </Tooltip>
                            );
                            return (
                                <List.Item
                                    actions={[
                                        <Button
                                            key="view"
                                            type="link"
                                            icon={<EyeOutlined />}
                                            onClick={() => navigate(`/rag-lab/history/${job.job_id}`)}
                                        >
                                            View Details
                                        </Button>,
                                        obsButton,
                                    ]}
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
                                                {/* Show refresh indicator for RUNNING/QUEUED jobs */}
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
                                                {job.params && Object.keys(job.params).length > 0 && (
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            Params: {JSON.stringify(job.params)}
                                                        </Text>
                                                    </div>
                                                )}
                                                <div>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        Observability:{' '}
                                                        {obsInline}
                                                    </Text>
                                                </div>
                                            </Space>
                                        }
                                    />
                                </List.Item>
                            );
                        }}
                    />
                )}
            </Card>
        </div>
    );
};
