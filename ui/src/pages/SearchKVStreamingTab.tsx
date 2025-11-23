// frontend/src/pages/SearchKVStreamingTab.tsx
//
// KV & Streaming Experiment Tab
//
// This tab compares four engine modes (baseline / kv_only / stream_only / kv_and_stream) on the same question.
// It runs multiple iterations per mode and displays aggregated metrics in a comparison table and chart.
//
import { useState } from 'react';
import {
    Row,
    Col,
    Card,
    Form,
    Input,
    InputNumber,
    Button,
    Typography,
    Space,
    Table,
    Tag,
    message,
    Skeleton,
    Select,
    Divider,
} from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KvExperimentRunRequest, KvExperimentRunResponse, KvExperimentModeResult } from '../types/api.types';

const { TextArea } = Input;
const { Text, Paragraph, Title } = Typography;

// Airbnb filter constants (matching SearchPlayground)
const AIRBNB_NEIGHBOURHOODS = [
    'Hollywood',
    'Venice',
    'Downtown',
    'West Los Angeles',
    'Santa Monica',
    'Long Beach',
];

const AIRBNB_ROOM_TYPES = [
    'Entire home/apt',
    'Private room',
    'Shared room',
];

// Default question
const DEFAULT_QUESTION = 'Find a 2 bedroom place in West LA under $200 per night';

export const SearchKVStreamingTab = () => {
    const [form] = Form.useForm();
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<KvExperimentRunResponse | null>(null);

    // Handle form submission
    const handleRunExperiment = async (values: any) => {
        setIsLoading(true);
        setResult(null);

        try {
            // Build request payload
            const request: KvExperimentRunRequest = {
                question: values.question || DEFAULT_QUESTION,
                collection: values.collection || 'airbnb_la_demo',
                profile_name: values.profile_name || 'airbnb_la_location_first',
                runs_per_mode: values.runs_per_mode || 5,
                filters: {
                    ...(values.price_max !== undefined && values.price_max !== null
                        ? { price_max: values.price_max }
                        : {}),
                    ...(values.min_bedrooms !== undefined && values.min_bedrooms !== null
                        ? { min_bedrooms: values.min_bedrooms }
                        : {}),
                    ...(values.neighbourhood ? { neighbourhood: values.neighbourhood } : {}),
                    ...(values.room_type ? { room_type: values.room_type } : {}),
                },
            };

            // Remove empty filters object if no filters are set
            if (Object.keys(request.filters || {}).length === 0) {
                delete request.filters;
            }

            const response = await fetch('/api/kv-experiment/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data: KvExperimentRunResponse = await response.json();

            if (!data.ok) {
                throw new Error(data.error || 'Experiment failed');
            }

            // Validate that all 4 modes are present
            if (!data.modes || !data.modes.baseline || !data.modes.kv_only ||
                !data.modes.stream_only || !data.modes.kv_and_stream) {
                throw new Error('Experiment completed but some modes are missing from results');
            }

            setResult(data);
        } catch (err: any) {
            console.error('KV experiment failed:', err);
            message.error(`Experiment failed: ${err.message || 'Unknown error'}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Generate takeaway summary
    const generateTakeaway = (): string => {
        if (!result || !result.modes) {
            return '';
        }

        const { baseline, kv_only, stream_only, kv_and_stream } = result.modes;

        // Guard against missing mode data
        if (!baseline || !kv_only || !stream_only || !kv_and_stream) {
            return 'Some mode data is missing. Please run the experiment again.';
        }

        // Calculate improvements
        const kvImprovement = baseline.p50_ms > 0
            ? ((baseline.p50_ms - kv_only.p50_ms) / baseline.p50_ms) * 100
            : 0;

        const streamImprovement = baseline.p50_ms > 0
            ? ((baseline.p50_ms - stream_only.p50_ms) / baseline.p50_ms) * 100
            : 0;

        const kvAndStreamImprovement = baseline.p50_ms > 0
            ? ((baseline.p50_ms - kv_and_stream.p50_ms) / baseline.p50_ms) * 100
            : 0;

        // Find mode with highest token usage
        const tokenUsages = [
            { mode: 'baseline', tokens: baseline.avg_total_tokens },
            { mode: 'kv_only', tokens: kv_only.avg_total_tokens },
            { mode: 'stream_only', tokens: stream_only.avg_total_tokens },
            { mode: 'kv_and_stream', tokens: kv_and_stream.avg_total_tokens },
        ];
        const highestTokenMode = tokenUsages.reduce((max, curr) =>
            curr.tokens > max.tokens ? curr : max
        );

        const takeaways: string[] = [];

        if (kvImprovement > 5) {
            takeaways.push(
                `kv_only reduced p50 latency by ~${Math.round(kvImprovement)}% vs baseline`
            );
        } else if (kvImprovement < -5) {
            takeaways.push(
                `kv_only increased p50 latency by ~${Math.round(Math.abs(kvImprovement))}% vs baseline`
            );
        }

        if (streamImprovement > 5) {
            takeaways.push(
                `stream_only reduced p50 latency by ~${Math.round(streamImprovement)}% vs baseline`
            );
        }

        if (kvAndStreamImprovement > 5) {
            takeaways.push(
                `kv_and_stream reduced p50 latency by ~${Math.round(kvAndStreamImprovement)}% vs baseline`
            );
        }

        if (highestTokenMode.tokens > 0) {
            takeaways.push(
                `${highestTokenMode.mode} had the highest token usage (${Math.round(highestTokenMode.tokens)} tokens avg)`
            );
        }

        if (kv_only.kv_hit_rate > 0.5) {
            takeaways.push(
                `KV cache hit rate was ${(kv_only.kv_hit_rate * 100).toFixed(0)}% for kv_only mode`
            );
        }

        if (takeaways.length === 0) {
            return 'All modes performed similarly in this run.';
        }

        return `In this run, ${takeaways.join(', ')}.`;
    };

    // Prepare table data
    const tableData = result
        ? [
            {
                key: 'baseline',
                mode: 'baseline',
                ...result.modes.baseline,
            },
            {
                key: 'kv_only',
                mode: 'kv_only',
                ...result.modes.kv_only,
            },
            {
                key: 'stream_only',
                mode: 'stream_only',
                ...result.modes.stream_only,
            },
            {
                key: 'kv_and_stream',
                mode: 'kv_and_stream',
                ...result.modes.kv_and_stream,
            },
        ]
        : [];

    // Prepare chart data
    const chartData = result
        ? [
            {
                mode: 'baseline',
                p50_ms: result.modes.baseline.p50_ms,
            },
            {
                mode: 'kv_only',
                p50_ms: result.modes.kv_only.p50_ms,
            },
            {
                mode: 'stream_only',
                p50_ms: result.modes.stream_only.p50_ms,
            },
            {
                mode: 'kv_and_stream',
                p50_ms: result.modes.kv_and_stream.p50_ms,
            },
        ]
        : [];

    // Table columns
    const columns = [
        {
            title: 'Mode',
            dataIndex: 'mode',
            key: 'mode',
            render: (text: string) => <Text strong>{text}</Text>,
        },
        {
            title: 'P50 (ms)',
            dataIndex: 'p50_ms',
            key: 'p50_ms',
            render: (value: number) => value.toFixed(1),
        },
        {
            title: 'P95 (ms)',
            dataIndex: 'p95_ms',
            key: 'p95_ms',
            render: (value: number) => value.toFixed(1),
        },
        {
            title: 'P50 First Token (ms)',
            dataIndex: 'p50_first_token_ms',
            key: 'p50_first_token_ms',
            render: (value: number) => value.toFixed(1),
        },
        {
            title: 'Avg Tokens',
            dataIndex: 'avg_total_tokens',
            key: 'avg_total_tokens',
            render: (value: number) => Math.round(value),
        },
        {
            title: 'KV Hit Rate',
            dataIndex: 'kv_hit_rate',
            key: 'kv_hit_rate',
            render: (value: number) => `${(value * 100).toFixed(1)}%`,
        },
        {
            title: 'Stream Enabled',
            dataIndex: 'stream_enabled',
            key: 'stream_enabled',
            render: (value: boolean) => (
                <Tag color={value ? 'green' : 'default'}>{value ? 'Yes' : 'No'}</Tag>
            ),
        },
        {
            title: 'KV Enabled',
            dataIndex: 'kv_enabled',
            key: 'kv_enabled',
            render: (value: boolean) => (
                <Tag color={value ? 'blue' : 'default'}>{value ? 'Yes' : 'No'}</Tag>
            ),
        },
    ];

    return (
        <Row gutter={16}>
            {/* Left Column: Config Form */}
            <Col span={8}>
                <Card title="Experiment Configuration" bordered={false}>
                    <Form
                        form={form}
                        layout="vertical"
                        initialValues={{
                            question: DEFAULT_QUESTION,
                            collection: 'airbnb_la_demo',
                            profile_name: 'airbnb_la_location_first',
                            runs_per_mode: 5,
                        }}
                        onFinish={handleRunExperiment}
                    >
                        <Form.Item
                            label="Question"
                            name="question"
                            rules={[{ required: true, message: 'Please enter a question' }]}
                        >
                            <TextArea rows={4} placeholder="Enter your question..." />
                        </Form.Item>

                        <Form.Item label="Runs per Mode" name="runs_per_mode">
                            <InputNumber min={1} max={10} style={{ width: '100%' }} />
                        </Form.Item>

                        <Divider orientation="left" style={{ marginTop: '16px', marginBottom: '16px' }}>
                            Optional Filters
                        </Divider>

                        <Form.Item label="Max Price ($/night)" name="price_max">
                            <InputNumber
                                min={0}
                                max={10000}
                                step={10}
                                style={{ width: '100%' }}
                                addonBefore="$"
                                placeholder="e.g., 200"
                            />
                        </Form.Item>

                        <Form.Item label="Min Bedrooms" name="min_bedrooms">
                            <InputNumber
                                min={0}
                                max={10}
                                style={{ width: '100%' }}
                                placeholder="e.g., 2"
                            />
                        </Form.Item>

                        <Form.Item label="Neighbourhood" name="neighbourhood">
                            <Select
                                placeholder="Select neighbourhood"
                                allowClear
                                style={{ width: '100%' }}
                            >
                                {AIRBNB_NEIGHBOURHOODS.map((n) => (
                                    <Select.Option key={n} value={n}>
                                        {n}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item label="Room Type" name="room_type">
                            <Select
                                placeholder="Select room type"
                                allowClear
                                style={{ width: '100%' }}
                            >
                                {AIRBNB_ROOM_TYPES.map((rt) => (
                                    <Select.Option key={rt} value={rt}>
                                        {rt}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>

                        <Form.Item>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={isLoading}
                                block
                                size="large"
                            >
                                Run KV Experiment
                            </Button>
                        </Form.Item>
                    </Form>
                </Card>
            </Col>

            {/* Right Column: Results */}
            <Col span={16}>
                {isLoading ? (
                    <Card bordered={false}>
                        <Skeleton active paragraph={{ rows: 8 }} />
                    </Card>
                ) : result ? (
                    <>
                        {/* Comparison Table */}
                        <Card title="Mode Comparison" bordered={false} style={{ marginBottom: '16px' }}>
                            {tableData.length > 0 ? (
                                <Table
                                    dataSource={tableData}
                                    columns={columns}
                                    pagination={false}
                                    size="small"
                                />
                            ) : (
                                <Text type="secondary">No data available</Text>
                            )}
                        </Card>

                        {/* Chart */}
                        <Card title="P50 Latency Comparison" bordered={false} style={{ marginBottom: '16px' }}>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="mode" />
                                        <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="p50_ms" fill="#1890ff" name="P50 Latency (ms)" />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <Text type="secondary">No chart data available</Text>
                            )}
                        </Card>

                        {/* Takeaway Summary */}
                        <Card title="Takeaway Summary" bordered={false}>
                            <Paragraph style={{ fontSize: '16px', lineHeight: '1.8' }}>
                                {generateTakeaway() || 'Run an experiment to see insights.'}
                            </Paragraph>
                        </Card>
                    </>
                ) : (
                    <Card bordered={false}>
                        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                            <Text type="secondary">
                                Configure and run an experiment to see results.
                            </Text>
                        </div>
                    </Card>
                )}
            </Col>
        </Row>
    );
};
