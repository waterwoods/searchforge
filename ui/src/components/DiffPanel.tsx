/**
 * DiffPanel - V11 Job Comparison Panel
 * Minimal diff panel for comparing two SUCCEEDED jobs
 */
import { useState, useEffect } from 'react';
import {
    Card,
    Button,
    Select,
    Table,
    Tag,
    Space,
    Typography,
    Alert,
    Spin,
    Descriptions,
    Modal,
    App,
} from 'antd';
import {
    SwapOutlined,
    ArrowUpOutlined,
    ArrowDownOutlined,
} from '@ant-design/icons';
import { useRagLabStore } from '../store/ragLabStore';
import * as experimentApi from '../api/experiment';

const { Title, Text } = Typography;
const { Option } = Select;

export const DiffPanel = () => {
    const { message } = App.useApp();
    const {
        diffLoading,
        diffResult,
        diffError,
        runDiff,
        clearDiff,
    } = useRagLabStore();

    // Local state
    const [jobIdA, setJobIdA] = useState<string>('');
    const [jobIdB, setJobIdB] = useState<string>('');
    const [jobsList, setJobsList] = useState<any[]>([]);
    const [loadingJobs, setLoadingJobs] = useState(false);
    const [incompatibleModalVisible, setIncompatibleModalVisible] = useState(false);

    // Fetch jobs list (only SUCCEEDED)
    useEffect(() => {
        const fetchJobs = async () => {
            setLoadingJobs(true);
            try {
                const response = await experimentApi.listJobs(500);
                // Filter only SUCCEEDED jobs
                const succeeded = response.jobs.filter((job: any) => job.status === 'SUCCEEDED');
                setJobsList(succeeded);
            } catch (err) {
                console.error('Failed to fetch jobs:', err);
            } finally {
                setLoadingJobs(false);
            }
        };
        fetchJobs();
    }, []);

    // Handle compare button
    const handleCompare = () => {
        if (!jobIdA || !jobIdB || jobIdA === jobIdB) {
            message.warning('Please select two different SUCCEEDED jobs');
            return;
        }
        runDiff(jobIdA, jobIdB);
    };

    // Handle error display
    useEffect(() => {
        if (diffError) {
            if (diffError.error === 'job_not_found') {
                message.error(`Job not found: ${diffError.job_id}`);
            } else if (diffError.error === 'job_in_progress') {
                message.warning(`Job ${diffError.job_id} is still in progress`);
            } else if (diffError.error === 'job_failed') {
                message.error(`Job ${diffError.job_id} failed and cannot be compared`);
            } else if (diffError.error === 'metrics_missing') {
                message.error(`Metrics missing for job ${diffError.job_id}`);
            } else if (diffError.error === 'incompatible_context') {
                setIncompatibleModalVisible(true);
            }
        }
    }, [diffError, message]);


    // Metrics table data
    const metricsData = diffResult
        ? [
            {
                key: 'recall_at_10',
                metric: 'Recall@10',
                A: diffResult.metrics.A.recall_at_10,
                B: diffResult.metrics.B.recall_at_10,
                delta: diffResult.metrics.B.recall_at_10 - diffResult.metrics.A.recall_at_10,
                deltaPct:
                    diffResult.metrics.A.recall_at_10 !== 0
                        ? ((diffResult.metrics.B.recall_at_10 - diffResult.metrics.A.recall_at_10) /
                            diffResult.metrics.A.recall_at_10) *
                        100
                        : 0,
                isBetter: diffResult.metrics.B.recall_at_10 > diffResult.metrics.A.recall_at_10, // Higher is better
            },
            {
                key: 'p95_ms',
                metric: 'P95 (ms)',
                A: diffResult.metrics.A.p95_ms,
                B: diffResult.metrics.B.p95_ms,
                delta: diffResult.metrics.B.p95_ms - diffResult.metrics.A.p95_ms,
                deltaPct:
                    diffResult.metrics.A.p95_ms !== 0
                        ? ((diffResult.metrics.B.p95_ms - diffResult.metrics.A.p95_ms) / diffResult.metrics.A.p95_ms) * 100
                        : 0,
                isBetter: diffResult.metrics.B.p95_ms < diffResult.metrics.A.p95_ms, // Lower is better
            },
            {
                key: 'cost_per_query',
                metric: 'Cost/Query',
                A: diffResult.metrics.A.cost_per_query,
                B: diffResult.metrics.B.cost_per_query,
                delta: diffResult.metrics.B.cost_per_query - diffResult.metrics.A.cost_per_query,
                deltaPct:
                    diffResult.metrics.A.cost_per_query !== 0
                        ? ((diffResult.metrics.B.cost_per_query - diffResult.metrics.A.cost_per_query) /
                            diffResult.metrics.A.cost_per_query) *
                        100
                        : 0,
                isBetter: diffResult.metrics.B.cost_per_query < diffResult.metrics.A.cost_per_query, // Lower is better
            },
        ]
        : [];

    const metricsColumns = [
        {
            title: 'Metric',
            dataIndex: 'metric',
            key: 'metric',
        },
        {
            title: 'A',
            dataIndex: 'A',
            key: 'A',
            render: (val: number) => val.toFixed(4),
        },
        {
            title: 'B',
            dataIndex: 'B',
            key: 'B',
            render: (val: number) => val.toFixed(4),
        },
        {
            title: 'Delta',
            key: 'delta',
            render: (_: any, record: any) => {
                const { delta, deltaPct, isBetter } = record;
                const icon = isBetter ? <ArrowUpOutlined /> : <ArrowDownOutlined />;
                const color = isBetter ? 'green' : 'red';
                return (
                    <Space>
                        <Tag color={color} icon={icon}>
                            {delta > 0 ? '+' : ''}
                            {delta.toFixed(4)}
                        </Tag>
                        <Text type="secondary">({deltaPct > 0 ? '+' : ''}{deltaPct.toFixed(2)}%)</Text>
                    </Space>
                );
            },
        },
    ];

    const canCompare = jobIdA && jobIdB && jobIdA !== jobIdB;

    return (
        <Card
            title={
                <Space>
                    <SwapOutlined />
                    <span>Job Comparison (V11)</span>
                </Space>
            }
            bordered={false}
            extra={
                <Button size="small" onClick={clearDiff}>
                    Clear
                </Button>
            }
        >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {/* Job Selection */}
                <Space style={{ width: '100%' }} size="middle">
                    <div style={{ flex: 1 }}>
                        <Text strong>Job A:</Text>
                        <Select
                            value={jobIdA || undefined}
                            onChange={setJobIdA}
                            placeholder="Select Job A"
                            style={{ width: '100%', marginTop: '8px' }}
                            loading={loadingJobs}
                            showSearch
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {jobsList.map((job) => (
                                <Option key={job.job_id} value={job.job_id}>
                                    {job.job_id} {job.queued_at ? `(${new Date(job.queued_at).toLocaleString()})` : ''}
                                </Option>
                            ))}
                        </Select>
                    </div>
                    <div style={{ flex: 1 }}>
                        <Text strong>Job B:</Text>
                        <Select
                            value={jobIdB || undefined}
                            onChange={setJobIdB}
                            placeholder="Select Job B"
                            style={{ width: '100%', marginTop: '8px' }}
                            loading={loadingJobs}
                            showSearch
                            filterOption={(input, option) =>
                                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                            }
                        >
                            {jobsList.map((job) => (
                                <Option key={job.job_id} value={job.job_id}>
                                    {job.job_id} {job.queued_at ? `(${new Date(job.queued_at).toLocaleString()})` : ''}
                                </Option>
                            ))}
                        </Select>
                    </div>
                    <Button
                        type="primary"
                        icon={<SwapOutlined />}
                        onClick={handleCompare}
                        loading={diffLoading}
                        disabled={!canCompare || diffLoading}
                    >
                        Compare
                    </Button>
                </Space>

                {/* Error Display */}
                {diffError && diffError.error !== 'incompatible_context' && (
                    <Alert
                        message="Comparison Error"
                        description={
                            diffError.error === 'job_not_found'
                                ? `Job not found: ${diffError.job_id}`
                                : diffError.error === 'job_in_progress'
                                    ? `Job ${diffError.job_id} is still in progress`
                                    : diffError.error === 'job_failed'
                                        ? `Job ${diffError.job_id} failed and cannot be compared`
                                        : `Metrics missing for job ${diffError.job_id}`
                        }
                        type="error"
                        closable
                        onClose={clearDiff}
                    />
                )}

                {/* Loading State */}
                {diffLoading && (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" tip="Comparing jobs..." />
                    </div>
                )}

                {/* Results */}
                {diffResult && !diffLoading && (
                    <>
                        {/* Metrics Table */}
                        <div>
                            <Title level={5}>Metrics Comparison</Title>
                            <Table
                                dataSource={metricsData}
                                columns={metricsColumns}
                                pagination={false}
                                size="small"
                            />
                        </div>

                        {/* Params Diff */}
                        {Object.keys(diffResult.params_diff).length > 0 && (
                            <div>
                                <Title level={5}>Parameters Changed</Title>
                                <Space wrap>
                                    {Object.entries(diffResult.params_diff).map(([key, [valA, valB]]) => (
                                        <Tag key={key} color="orange">
                                            {key}: {JSON.stringify(valA)} → {JSON.stringify(valB)}
                                        </Tag>
                                    ))}
                                </Space>
                            </div>
                        )}

                        {/* Meta */}
                        <div>
                            <Title level={5}>Metadata</Title>
                            <Descriptions size="small" column={2}>
                                <Descriptions.Item label="Dataset">{diffResult.meta.dataset_name}</Descriptions.Item>
                                <Descriptions.Item label="Schema Version">{diffResult.meta.schema_version}</Descriptions.Item>
                                <Descriptions.Item label="Git SHA">
                                    {diffResult.meta.git_sha ? diffResult.meta.git_sha : '(unknown)'}
                                </Descriptions.Item>
                                <Descriptions.Item label="Created At">
                                    {typeof diffResult.meta.created_at === 'object' && 'A' in diffResult.meta.created_at && 'B' in diffResult.meta.created_at
                                        ? `A: ${new Date(diffResult.meta.created_at.A).toLocaleString()} | B: ${new Date(diffResult.meta.created_at.B).toLocaleString()}`
                                        : typeof diffResult.meta.created_at === 'string'
                                            ? new Date(diffResult.meta.created_at).toLocaleString()
                                            : '-'}
                                </Descriptions.Item>
                            </Descriptions>
                        </div>
                    </>
                )}
            </Space>

            {/* Incompatible Context Modal */}
            <Modal
                title="Incompatible Context"
                open={incompatibleModalVisible}
                onOk={() => setIncompatibleModalVisible(false)}
                onCancel={() => setIncompatibleModalVisible(false)}
                footer={<Button onClick={() => setIncompatibleModalVisible(false)}>Close</Button>}
            >
                <Alert
                    message="Jobs have incompatible context"
                    description="The following fields do not match:"
                    type="warning"
                    style={{ marginBottom: '16px' }}
                />
                {diffError?.mismatch && (
                    <Space direction="vertical" style={{ width: '100%' }}>
                        {Object.entries(diffError.mismatch).map(([key, [valA, valB]]) => (
                            <div key={key}>
                                <Text strong>{key}:</Text> {JSON.stringify(valA)} vs {JSON.stringify(valB)}
                            </div>
                        ))}
                    </Space>
                )}
            </Modal>
        </Card>
    );
};

