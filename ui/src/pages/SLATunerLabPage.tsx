// frontend/src/pages/SLATunerLabPage.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Statistic, Progress, Timeline, Typography, Spin, Tag, Space, Select, InputNumber } from 'antd';
import { PlayCircleOutlined, StopOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { AutoTunerStatus, AutoTunerRecommendation, ApiAutoTunerRecommendationsResponse } from '../types/api.types';
import { RealTimePerfChart } from '../components/charts/RealTimePerfChart';

const { Title, Text, Paragraph } = Typography;

export const SLATunerLabPage = () => {
    const [status, setStatus] = useState<AutoTunerStatus | null>(null);
    const [recommendations, setRecommendations] = useState<AutoTunerRecommendation[]>([]);
    const [loadingStatus, setLoadingStatus] = useState(false);
    const [loadingRecs, setLoadingRecs] = useState(false);

    // 流量生成配置
    const [qpsMode, setQpsMode] = useState<'standard' | 'high'>('standard');
    const [duration, setDuration] = useState(60);
    const [isGenerating, setIsGenerating] = useState(false);

    // Fetch status periodically
    useEffect(() => {
        const fetchStatus = () => {
            setLoadingStatus(true);
            fetch('/api/autotuner/status')
                .then(res => res.json())
                .then((data: AutoTunerStatus) => setStatus(data))
                .catch(console.error)
                .finally(() => setLoadingStatus(false));
        };
        fetchStatus(); // Initial fetch
        const intervalId = setInterval(fetchStatus, 5000); // Poll every 5 seconds
        return () => clearInterval(intervalId); // Cleanup interval on unmount
    }, []);

    // Fetch recommendations once
    useEffect(() => {
        setLoadingRecs(true);
        fetch('/api/autotuner/recommendations')
            .then(res => res.json())
            .then((data: ApiAutoTunerRecommendationsResponse) => {
                // Ensure we always set an array, even if the response is malformed
                setRecommendations(data?.recommendations || []);
            })
            .catch(err => {
                console.error('Failed to fetch recommendations:', err);
                setRecommendations([]); // Set empty array on error
            })
            .finally(() => setLoadingRecs(false));
    }, []);

    const handleStart = () => {
        fetch('/api/autotuner/start', { method: 'POST' });
        // Optimistic update
        setStatus(prev => prev ? { ...prev, status: 'running', progress: 0 } : null);
    };

    const handleStop = () => {
        fetch('/api/autotuner/stop', { method: 'POST' });
        setStatus(prev => prev ? { ...prev, status: 'idle', progress: undefined } : null);
    };

    const handleGenerateTraffic = async () => {
        if (isGenerating) return;

        setIsGenerating(true);
        try {
            console.log(`🚀 启动流量生成: ${qpsMode}模式, ${duration}秒`);

            const response = await fetch(`/api/demo/generate-traffic?high_qps=${qpsMode === 'high'}&duration=${duration}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ 流量生成启动:', data);

            // 显示成功消息
            alert(`✅ ${data.mode} 启动成功!\n持续时间: ${duration}秒\n进程ID: ${data.pid}`);

        } catch (err: any) {
            console.error('❌ 流量生成失败:', err);
            alert(`❌ 启动失败: ${err.message || err}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const getStatusColor = (s: string) => {
        switch (s) {
            case 'running': return 'processing';
            case 'completed': return 'success';
            case 'error': return 'error';
            default: return 'default';
        }
    };

    return (
        <div style={{ padding: '24px' }}>
            <Title level={2} style={{ marginBottom: '24px' }}>
                <ThunderboltOutlined /> SLA Tuner Lab
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                Automated performance tuning for your RAG pipeline. Start a tuning job to optimize top_k, rerank, and other parameters based on real-time metrics.
            </Paragraph>

            <Row gutter={16}>
                {/* Left Column: Controls */}
                <Col span={6}>
                    <Card title="Experiment Controls" bordered={false}>
                        <Paragraph style={{ color: '#999' }}>
                            Select RAG config, set SLA targets, and run Auto-Tuner.
                        </Paragraph>

                        {/* Status Display */}
                        <div style={{ marginBottom: '20px', padding: '16px', background: '#1a1a1a', borderRadius: '8px' }}>
                            <Space direction="vertical" style={{ width: '100%' }}>
                                <div>
                                    <Text strong>Status: </Text>
                                    <Tag color={getStatusColor(status?.status || 'idle')}>
                                        {status?.status?.toUpperCase() || 'LOADING...'}
                                    </Tag>
                                </div>
                                {status?.job_id && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            Job ID: {status.job_id}
                                        </Text>
                                    </div>
                                )}
                                {status?.status === 'running' && status.progress !== undefined && (
                                    <Progress
                                        percent={status.progress}
                                        size="small"
                                        status="active"
                                        strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                                    />
                                )}
                                {status?.current_params && (
                                    <div>
                                        <Text strong style={{ fontSize: '12px' }}>Current Params:</Text>
                                        <pre style={{
                                            fontSize: '11px',
                                            color: '#bbb',
                                            marginTop: '8px',
                                            background: '#0d0d0d',
                                            padding: '8px',
                                            borderRadius: '4px',
                                            overflow: 'auto'
                                        }}>
                                            {JSON.stringify(status.current_params, null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </Space>
                        </div>

                        {/* Control Buttons */}
                        <Space>
                            <Button
                                type="primary"
                                icon={<PlayCircleOutlined />}
                                onClick={handleStart}
                                disabled={status?.status === 'running'}
                                loading={loadingStatus && status?.status !== 'running'}
                            >
                                Start Job
                            </Button>
                            <Button
                                icon={<StopOutlined />}
                                onClick={handleStop}
                                disabled={status?.status !== 'running'}
                            >
                                Stop
                            </Button>
                        </Space>

                        {/* Demo Traffic Generator */}
                        <div style={{ marginTop: '16px', padding: '12px', background: '#1a1a1a', borderRadius: '8px' }}>
                            <Text strong style={{ fontSize: '12px', color: '#fff' }}>Demo Traffic Generator</Text>

                            {/* 配置选项 */}
                            <div style={{ marginTop: '12px' }}>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    {/* QPS模式选择 */}
                                    <div>
                                        <Text style={{ fontSize: '11px', color: '#ccc' }}>QPS模式:</Text>
                                        <Select
                                            size="small"
                                            value={qpsMode}
                                            onChange={setQpsMode}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            options={[
                                                { value: 'standard', label: '标准模式 (10 QPS)' },
                                                { value: 'high', label: '高QPS模式 (20 QPS)' }
                                            ]}
                                        />
                                    </div>

                                    {/* 时间设置 */}
                                    <div>
                                        <Text style={{ fontSize: '11px', color: '#ccc' }}>持续时间:</Text>
                                        <InputNumber
                                            size="small"
                                            value={duration}
                                            onChange={(value) => setDuration(value || 60)}
                                            min={10}
                                            max={300}
                                            step={10}
                                            style={{ width: '100%', marginTop: '4px' }}
                                            addonAfter="秒"
                                        />
                                    </div>

                                    {/* 启动按钮 */}
                                    <Button
                                        type="primary"
                                        size="small"
                                        onClick={handleGenerateTraffic}
                                        loading={isGenerating}
                                        disabled={isGenerating}
                                        style={{ width: '100%' }}
                                    >
                                        {isGenerating ? '生成中...' : `启动测试 (${qpsMode === 'high' ? '20' : '10'} QPS, ${duration}秒)`}
                                    </Button>

                                    {/* 说明文字 */}
                                    <Text type="secondary" style={{ fontSize: '10px' }}>
                                        预计生成 {qpsMode === 'high' ? duration * 20 : duration * 10} 个请求
                                    </Text>
                                </Space>
                            </div>
                        </div>

                        {/* Placeholder for config selection */}
                        <div style={{ marginTop: '24px', padding: '12px', background: '#1a1a1a', borderRadius: '8px', border: '1px dashed #444' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                📝 Config selection UI (coming soon)
                            </Text>
                        </div>
                    </Card>
                </Col>

                {/* Middle Column: Real-time Monitor */}
                <Col span={10}>
                    <Card title="Real-time Performance" bordered={false}>
                        <RealTimePerfChart expId="monitor_demo" windowSec={300} refreshIntervalMs={2000} />
                        <div style={{ marginTop: '16px', textAlign: 'center' }}>
                            <Text type="secondary" style={{ fontSize: '13px' }}>
                                Live P95 Latency & QPS (Data from /api/metrics/mini)
                            </Text>
                        </div>

                        {/* Mock Statistics */}
                        <Row gutter={16} style={{ marginTop: '24px' }}>
                            <Col span={8}>
                                <Statistic
                                    title="P95 Latency"
                                    value={120.4}
                                    suffix="ms"
                                    valueStyle={{ color: '#cf1322' }}
                                />
                            </Col>
                            <Col span={8}>
                                <Statistic
                                    title="QPS"
                                    value={3.2}
                                    valueStyle={{ color: '#3f8600' }}
                                />
                            </Col>
                            <Col span={8}>
                                <Statistic
                                    title="Recall"
                                    value={82.0}
                                    suffix="%"
                                    valueStyle={{ color: '#1890ff' }}
                                />
                            </Col>
                        </Row>
                    </Card>
                </Col>

                {/* Right Column: Results & Suggestions */}
                <Col span={8}>
                    <Spin spinning={loadingRecs}>
                        <Card title="Auto-Tuner Recommendations" bordered={false}>
                            <Timeline style={{ marginTop: '10px' }}>
                                {!loadingRecs && recommendations && Array.isArray(recommendations) && recommendations.length > 0 ? (
                                    recommendations.map((rec, index) => (
                                        <Timeline.Item
                                            key={index}
                                            color={index === 0 ? 'green' : 'blue'}
                                        >
                                            <div style={{ marginBottom: '12px' }}>
                                                <div style={{ marginBottom: '8px' }}>
                                                    <Text strong>Params: </Text>
                                                    <Text code style={{ fontSize: '11px' }}>
                                                        {JSON.stringify(rec.params)}
                                                    </Text>
                                                </div>

                                                <div style={{ marginBottom: '8px' }}>
                                                    <Text strong>Impact:</Text>
                                                    <div style={{ marginLeft: '8px', marginTop: '4px' }}>
                                                        {rec.estimated_impact.delta_p95_ms !== undefined && (
                                                            <div>
                                                                <Text style={{ color: rec.estimated_impact.delta_p95_ms < 0 ? '#52c41a' : '#ff4d4f' }}>
                                                                    P95: {rec.estimated_impact.delta_p95_ms > 0 ? '+' : ''}{rec.estimated_impact.delta_p95_ms.toFixed(1)}ms
                                                                </Text>
                                                            </div>
                                                        )}
                                                        {rec.estimated_impact.delta_recall_pct !== undefined && (
                                                            <div>
                                                                <Text style={{ color: rec.estimated_impact.delta_recall_pct < 0 ? '#ff4d4f' : '#52c41a' }}>
                                                                    Recall: {rec.estimated_impact.delta_recall_pct > 0 ? '+' : ''}{rec.estimated_impact.delta_recall_pct.toFixed(1)}%
                                                                </Text>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <div style={{ marginBottom: '8px' }}>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        {rec.reason}
                                                    </Text>
                                                </div>

                                                <div style={{ marginBottom: '8px' }}>
                                                    <Text style={{ fontSize: '11px', color: '#666' }}>
                                                        {new Date(rec.timestamp).toLocaleString()}
                                                    </Text>
                                                </div>

                                                <Button type="link" size="small" style={{ paddingLeft: 0 }}>
                                                    Apply Configuration →
                                                </Button>
                                            </div>
                                        </Timeline.Item>
                                    ))
                                ) : !loadingRecs ? (
                                    // Show "No recommendations" only if not loading and array is empty/null
                                    <Timeline.Item>
                                        <div style={{ textAlign: 'center', padding: '20px 0' }}>
                                            <Text type="secondary">No recommendations available yet. Start a tuning job to see suggestions.</Text>
                                        </div>
                                    </Timeline.Item>
                                ) : null /* Do not render anything while loading */}
                            </Timeline>
                        </Card>
                    </Spin>
                </Col>
            </Row>
        </div>
    );
};

