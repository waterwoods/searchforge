/**
 * RAG Lab Run Page - V8
 * Main UI for running RAG experiment jobs
 */
import { useEffect, useState } from 'react';
import {
    Card,
    Button,
    Typography,
    Space,
    Select,
    Input,
    InputNumber,
    Tag,
    Progress,
    Timeline,
    Alert,
    Spin,
    Divider,
    List,
    Row,
    Col,
    Checkbox,
    Form,
    Switch,
} from 'antd';
import {
    PlayCircleOutlined,
    StopOutlined,
    ExperimentOutlined,
    ReloadOutlined,
    ClearOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
} from '@ant-design/icons';
import { useRagLabStore } from '../store/ragLabStore';
import type { ExperimentConfig, VersionedPreset } from '../api/experiment';
import { DiffPanel } from '../components/DiffPanel';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export const RagLabRunPage = () => {
    const {
        currentJobId,
        currentJobStatus,
        currentJobLogs,
        queueStatus,
        presets,
        versionedPresets,
        presetsVersion,
        loading,
        error,
        isPolling,
        runExperiment,
        startExperiment,
        cancelCurrentJob,
        refreshJobStatus,
        fetchJobLogs,
        fetchQueueStatus,
        fetchPresets,
        fetchVersionedPresets,
        startPolling,
        stopPolling,
        clearError,
        reset,
        runOverrides,
        setRunOverrides,
        phase,
        jobId,
        logs,
        abortController,
    } = useRagLabStore();

    // Local UI state
    const [autoRefresh, setAutoRefresh] = useState(true);

    // V10/V11 state
    const [selectedPreset, setSelectedPreset] = useState<VersionedPreset | null>(null);
    const [customConfig, setCustomConfig] = useState<ExperimentConfig>({
        dataset_name: 'fiqa_10k_v1',
        qrels_name: 'fiqa_qrels_10k_v1',
        qdrant_collection: 'fiqa_10k_v1',
        top_k: 40,
        repeats: 1,
        warmup: 5,
        concurrency: 16,
        sample: 200,
        fast_mode: false,  // Default to false
        groups: [
            {
                name: 'Baseline',
                use_hybrid: false,
                rerank: false,
                description: 'Pure vector search baseline'
            }
        ]
    });

    // Cleanup on unmount: abort polling
    useEffect(() => {
        return () => {
            if (abortController) {
                abortController.abort();
            }
            stopPolling();
        };
    }, [abortController, stopPolling]);

    // Fetch versioned presets and queue status on mount
    useEffect(() => {
        fetchVersionedPresets();
        fetchQueueStatus();
        const intervalId = setInterval(() => {
            if (!currentJobId && autoRefresh) {
                fetchQueueStatus();
            }
        }, 10000);
        return () => clearInterval(intervalId);
    }, [currentJobId, autoRefresh, fetchVersionedPresets, fetchQueueStatus]);

    // Helper function for safe array access
    const asArray = <T,>(v: unknown): T[] => Array.isArray(v) ? v as T[] : [];

    // Get current config for badge display (must be defined before handleStart)
    const currentConfig = selectedPreset ? selectedPreset.config : customConfig;

    // Handle start experiment (V9/V10/V11 compatible)
    const handleStart = async () => {
        // Ensure sample/repeats have default values and are properly typed
        const sample = Number(runOverrides?.sample ?? 200);
        const repeats = Number(runOverrides?.repeats ?? 1);
        const fast_mode = runOverrides?.fast_mode ?? false;

        // Extract dataset_name and qrels_name from preset or custom config
        // Ensure we always have values (even if from default customConfig)
        const dataset_name = currentConfig?.dataset_name || customConfig.dataset_name;
        const qrels_name = currentConfig?.qrels_name || customConfig.qrels_name;

        console.info("[HANDLE_START] currentConfig:", {
            dataset_name: currentConfig?.dataset_name,
            qrels_name: currentConfig?.qrels_name,
            preset: selectedPreset?.name,
        });

        // Use new startExperiment action with polling
        await startExperiment({
            sample,
            repeats,
            fast_mode,
            config_file: null, // Can add config_file support later if needed
            dataset_name,
            qrels_name,
        });
    };

    // Handle cancel
    const handleCancel = async () => {
        await cancelCurrentJob();
    };

    // Handle manual refresh
    const handleRefresh = async () => {
        if (currentJobId) {
            await refreshJobStatus();
            await fetchJobLogs();
        }
        await fetchQueueStatus();
    };

    // Get status color based on phase or status
    const getStatusColor = (status?: string, currentPhase?: string): string => {
        const statusToCheck = currentPhase || status;
        switch (statusToCheck) {
            case 'SUCCEEDED':
            case 'succeeded':
                return 'success';
            case 'RUNNING':
            case 'running':
                return 'processing';
            case 'QUEUED':
            case 'queued':
            case 'submitting':
                return 'default';
            case 'FAILED':
            case 'failed':
            case 'ABORTED':
                return 'error';
            case 'CANCELLED':
                return 'warning';
            default:
                return 'default';
        }
    };

    // Get status icon
    const getStatusIcon = (status?: string, currentPhase?: string) => {
        const statusToCheck = currentPhase || status;
        switch (statusToCheck) {
            case 'SUCCEEDED':
            case 'succeeded':
                return <CheckCircleOutlined />;
            case 'RUNNING':
            case 'running':
            case 'queued':
            case 'submitting':
                return <ClockCircleOutlined />;
            case 'FAILED':
            case 'failed':
            case 'ABORTED':
                return <CloseCircleOutlined />;
            default:
                return <ClockCircleOutlined />;
        }
    };

    // Format timestamp
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
            <Title level={2} style={{ marginBottom: '8px' }}>
                <ExperimentOutlined /> RAG Lab - Run Experiment
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                Configure and run RAG experiment jobs
            </Paragraph>

            {/* Error Alert */}
            {error && (
                <Alert
                    message="Error"
                    description={typeof error === 'string' ? error : String(error)}
                    type="error"
                    closable
                    onClose={clearError}
                    style={{ marginBottom: '16px' }}
                />
            )}

            {/* V11 Diff Panel */}
            <div style={{ marginBottom: '24px' }}>
                <DiffPanel />
            </div>

            <Row gutter={16}>
                {/* Left Column: Controls & Status */}
                <Col span={8}>
                    {/* Experiment Configuration */}
                    <Card
                        title="Experiment Configuration"
                        bordered={false}
                        style={{ marginBottom: '16px' }}
                    >
                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                            {/* Data Source Badge */}
                            {currentConfig && (
                                <div style={{ marginBottom: '12px', padding: '8px', background: '#1f1f1f', borderRadius: '4px' }}>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        Dataset: <Text code>{currentConfig.dataset_name || 'N/A'}</Text>
                                        {' · '}
                                        Qrels: <Text code>{currentConfig.qrels_name || 'N/A'}</Text>
                                        {' · '}
                                        Collection: <Text code>{currentConfig.qdrant_collection || 'N/A'}</Text>
                                        {' · '}
                                        Rerank: <Text code>{(selectedPreset?.config?.groups?.[0]?.rerank ?? customConfig.groups?.[0]?.rerank) ? 'ON' : 'OFF'}</Text>
                                        {(selectedPreset?.config?.groups?.[0]?.rerank ?? customConfig.groups?.[0]?.rerank) && (
                                            <>
                                                {' · '}RerankTopK: <Text code>{selectedPreset?.config?.groups?.[0]?.rerank_top_k ?? customConfig.groups?.[0]?.rerank_top_k ?? 10}</Text>
                                            </>
                                        )}
                                    </Text>
                                </div>
                            )}

                            <div>
                                <Text strong>Use Preset:</Text>
                                <Select
                                    value={selectedPreset?.name || undefined}
                                    onChange={(val) => {
                                        if (val) {
                                            const preset = versionedPresets.find(p => p.name === val);
                                            setSelectedPreset(preset || null);
                                        } else {
                                            setSelectedPreset(null);
                                        }
                                    }}
                                    style={{ width: '100%', marginTop: '8px' }}
                                    disabled={!!currentJobId}
                                    placeholder="Or use custom config"
                                    allowClear
                                >
                                    {versionedPresets.map((preset) => (
                                        <Option key={preset.name} value={preset.name}>
                                            {preset.label}
                                        </Option>
                                    ))}
                                </Select>
                            </div>

                            {/* Tunable Params Form */}
                            <div style={{ marginTop: '16px' }}>
                                <Text strong>Tunable Params:</Text>
                                <Space direction="vertical" style={{ width: '100%', marginTop: '8px' }} size="small">
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>top_k:</Text>
                                        <InputNumber
                                            value={runOverrides?.top_k ?? 40}
                                            onChange={(val) => setRunOverrides({ ...runOverrides, top_k: val ?? undefined })}
                                            min={10}
                                            max={200}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            disabled={!!currentJobId}
                                        />
                                    </div>
                                    {selectedPreset?.config?.groups?.[0]?.use_hybrid && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '12px' }}>bm25_k:</Text>
                                            <InputNumber
                                                value={runOverrides?.bm25_k ?? 60}
                                                onChange={(val) => setRunOverrides({ ...runOverrides, bm25_k: val ?? undefined })}
                                                min={20}
                                                max={200}
                                                style={{ width: '100%', marginTop: '4px' }}
                                                disabled={!!currentJobId}
                                            />
                                        </div>
                                    )}
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px', marginRight: '8px' }}>Rerank:</Text>
                                        <Switch
                                            checked={runOverrides?.rerank ?? (selectedPreset?.config?.groups?.[0]?.rerank ?? customConfig.groups?.[0]?.rerank ?? false)}
                                            onChange={(checked) => setRunOverrides({ ...runOverrides, rerank: checked })}
                                            disabled={!!currentJobId}
                                        />
                                    </div>
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>Rerank Top-K:</Text>
                                        <InputNumber
                                            value={runOverrides?.rerank_top_k ?? runOverrides?.rerank_topk ?? 10}
                                            onChange={(val) => setRunOverrides({ ...runOverrides, rerank_top_k: val ?? undefined })}
                                            min={5}
                                            max={100}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            disabled={!!currentJobId || !(runOverrides?.rerank ?? (selectedPreset?.config?.groups?.[0]?.rerank ?? customConfig.groups?.[0]?.rerank ?? false))}
                                        />
                                    </div>
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>sample:</Text>
                                        <InputNumber
                                            value={runOverrides?.sample ?? 200}
                                            onChange={(val) => setRunOverrides({ ...runOverrides, sample: val ?? undefined })}
                                            min={50}
                                            max={2000}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            disabled={!!currentJobId}
                                        />
                                    </div>
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>repeats:</Text>
                                        <InputNumber
                                            value={runOverrides?.repeats ?? 1}
                                            onChange={(val) => setRunOverrides({ ...runOverrides, repeats: val ?? undefined })}
                                            min={1}
                                            max={5}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            disabled={!!currentJobId}
                                        />
                                    </div>
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px', marginRight: '8px' }}>fast_mode:</Text>
                                        <Switch
                                            checked={runOverrides?.fast_mode ?? false}
                                            onChange={(checked) => setRunOverrides({ ...runOverrides, fast_mode: checked })}
                                            disabled={!!currentJobId}
                                        />
                                    </div>
                                </Space>
                            </div>

                            {!selectedPreset && (
                                /* Custom Config Form */
                                <>
                                    <Text strong>Custom Config:</Text>
                                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '12px' }}>Top K:</Text>
                                            <InputNumber
                                                value={customConfig.top_k}
                                                onChange={(val) => setCustomConfig({ ...customConfig, top_k: val || 40 })}
                                                min={1}
                                                max={1000}
                                                style={{ width: '100%', marginTop: '4px' }}
                                                disabled={!!currentJobId}
                                            />
                                        </div>
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '12px' }}>Repeats:</Text>
                                            <InputNumber
                                                value={customConfig.repeats}
                                                onChange={(val) => setCustomConfig({ ...customConfig, repeats: val || 1 })}
                                                min={1}
                                                max={10}
                                                style={{ width: '100%', marginTop: '4px' }}
                                                disabled={!!currentJobId}
                                            />
                                        </div>
                                        {/* Removed duplicate Fast Mode checkbox - use the top switch instead */}
                                    </Space>
                                </>
                            )}

                            <Space style={{ width: '100%' }}>
                                <Button
                                    type="primary"
                                    icon={<PlayCircleOutlined />}
                                    onClick={handleStart}
                                    loading={loading || phase === 'submitting' || phase === 'queued' || phase === 'running'}
                                    disabled={!!currentJobId || loading || phase === 'submitting' || phase === 'queued' || phase === 'running'}
                                    block
                                >
                                    Start Experiment
                                </Button>
                                <Button
                                    danger
                                    icon={<StopOutlined />}
                                    onClick={handleCancel}
                                    loading={loading}
                                    disabled={!currentJobId || (phase !== 'running' && currentJobStatus?.state !== 'RUNNING')}
                                >
                                    Cancel
                                </Button>
                            </Space>

                            <Button
                                icon={<ReloadOutlined />}
                                onClick={handleRefresh}
                                loading={loading}
                                block
                            >
                                Refresh
                            </Button>
                        </Space>
                    </Card>

                    {/* Job Status */}
                    <Card title="Job Status" bordered={false} style={{ marginBottom: '16px' }}>
                        {(currentJobStatus || phase !== 'idle') ? (
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <div>
                                    <Text strong>Status: </Text>
                                    <Tag
                                        color={getStatusColor(currentJobStatus?.state, phase)}
                                        icon={getStatusIcon(currentJobStatus?.state, phase)}
                                    >
                                        {phase === 'submitting' ? 'SUBMITTING' :
                                            phase === 'queued' ? 'QUEUED' :
                                                phase === 'running' ? 'RUNNING' :
                                                    phase === 'succeeded' ? 'SUCCEEDED' :
                                                        phase === 'failed' ? 'FAILED' :
                                                            currentJobStatus?.state || 'UNKNOWN'}
                                    </Tag>
                                </div>

                                {(jobId || currentJobId) && (
                                    <div>
                                        <Text strong>Job ID: </Text>
                                        <Text code style={{ fontSize: '12px' }}>
                                            {jobId || currentJobId}
                                        </Text>
                                    </div>
                                )}

                                {(phase === 'submitting' || phase === 'queued' || phase === 'running') && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            {phase === 'submitting' && 'Submitting experiment...'}
                                            {phase === 'queued' && 'Waiting in queue...'}
                                            {phase === 'running' && 'Experiment running...'}
                                        </Text>
                                    </div>
                                )}

                                {phase === 'succeeded' && (
                                    <Alert
                                        message="Experiment Completed Successfully"
                                        type="success"
                                        showIcon
                                        style={{ marginTop: '8px' }}
                                    />
                                )}

                                {phase === 'failed' && error && (
                                    <Alert
                                        message="Experiment Failed"
                                        description={error}
                                        type="error"
                                        showIcon
                                        style={{ marginTop: '8px' }}
                                    />
                                )}

                                {(phase === 'running' || currentJobStatus?.state === 'RUNNING') && (
                                    <Progress
                                        percent={100}
                                        status="active"
                                        strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                                    />
                                )}

                                {currentJobStatus?.progress_hint && (
                                    <div>
                                        <Text strong>Progress: </Text>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            {currentJobStatus.progress_hint}
                                        </Text>
                                    </div>
                                )}

                                <Divider style={{ margin: '12px 0' }} />

                                {currentJobStatus?.queued_at && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Queued: {formatTimestamp(currentJobStatus.queued_at)}
                                        </Text>
                                    </div>
                                )}
                                {currentJobStatus?.started_at && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Started: {formatTimestamp(currentJobStatus.started_at)}
                                        </Text>
                                    </div>
                                )}
                                {currentJobStatus?.finished_at && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Finished: {formatTimestamp(currentJobStatus.finished_at)}
                                        </Text>
                                    </div>
                                )}

                                {currentJobStatus?.return_code !== null && currentJobStatus?.return_code !== undefined && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Return Code: {currentJobStatus.return_code}
                                        </Text>
                                    </div>
                                )}

                                {phase === 'failed' && logs && (
                                    <div>
                                        <Text strong>Logs:</Text>
                                        <pre style={{
                                            fontSize: '11px',
                                            background: '#1a1a1a',
                                            padding: '8px',
                                            borderRadius: '4px',
                                            maxHeight: '200px',
                                            overflow: 'auto'
                                        }}>
                                            {logs}
                                        </pre>
                                    </div>
                                )}

                                <Button
                                    size="small"
                                    icon={<ClearOutlined />}
                                    onClick={reset}
                                    disabled={phase === 'running' || currentJobStatus?.state === 'RUNNING'}
                                    block
                                >
                                    Clear Job
                                </Button>
                            </Space>
                        ) : (
                            <Text type="secondary">No active job</Text>
                        )}
                    </Card>

                    {/* Queue Status */}
                    <Card title="Queue Status" bordered={false}>
                        {queueStatus ? (
                            <Space direction="vertical" style={{ width: '100%' }} size="small">
                                <div>
                                    <Text strong>Queued: </Text>
                                    <Text>{Array.isArray(queueStatus?.queued) ? queueStatus.queued.length : 0}</Text>
                                </div>
                                <div>
                                    <Text strong>Running: </Text>
                                    <Text>{Array.isArray(queueStatus?.running) ? queueStatus.running.length : 0}</Text>
                                </div>
                            </Space>
                        ) : (
                            <Spin size="small" />
                        )}
                    </Card>
                </Col>

                {/* Right Column: Logs & Timeline */}
                <Col span={16}>
                    {/* Job Timeline */}
                    <Card
                        title="Job Timeline"
                        bordered={false}
                        style={{ marginBottom: '16px' }}
                        extra={
                            <Space>
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {Array.isArray(currentJobLogs) ? currentJobLogs.length : 0} lines
                                </Text>
                                <Button
                                    size="small"
                                    icon={<ReloadOutlined />}
                                    onClick={() => fetchJobLogs(500)}
                                    disabled={!currentJobId}
                                >
                                    Load More
                                </Button>
                            </Space>
                        }
                    >
                        {currentJobId ? (
                            <Timeline
                                items={[
                                    {
                                        color: 'blue',
                                        children: (
                                            <div>
                                                <Text strong>Job Created</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(currentJobStatus?.queued_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    currentJobStatus?.started_at && {
                                        color: 'green',
                                        children: (
                                            <div>
                                                <Text strong>Job Started</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(currentJobStatus.started_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    currentJobStatus?.finished_at && {
                                        color:
                                            currentJobStatus.status === 'SUCCEEDED' ? 'green' : 'red',
                                        children: (
                                            <div>
                                                <Text strong>
                                                    Job {currentJobStatus.status === 'SUCCEEDED' ? 'Completed' : 'Failed'}
                                                </Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(currentJobStatus.finished_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                ].filter(Boolean)}
                            />
                        ) : (
                            <Text type="secondary">No job timeline available</Text>
                        )}
                    </Card>

                    {/* Job Logs */}
                    <Card
                        title="Job Logs"
                        bordered={false}
                        style={{ maxHeight: '600px', overflow: 'auto' }}
                    >
                        {currentJobId ? (
                            (Array.isArray(currentJobLogs) && currentJobLogs.length > 0) ? (
                                <List
                                    dataSource={currentJobLogs}
                                    renderItem={(line, index) => (
                                        <List.Item style={{ padding: '4px 0', fontFamily: 'monospace' }}>
                                            <Text
                                                style={{
                                                    fontSize: '12px',
                                                    color: (typeof line === 'string' && (line.includes('ERROR') || line.includes('FAILED')))
                                                        ? '#ff4d4f'
                                                        : (typeof line === 'string' && line.includes('WARNING'))
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
                                <Spin tip="Loading logs..." />
                            )
                        ) : (
                            <Text type="secondary">No logs available. Start an experiment to see logs.</Text>
                        )}
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
