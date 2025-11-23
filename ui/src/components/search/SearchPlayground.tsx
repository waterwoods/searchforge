// frontend/src/components/search/SearchPlayground.tsx
//
// This page is designed as an interview-friendly search console: sample queries, raw JSON,
// and basic metrics for /api/query. It showcases the API contract clearly and is easy to demo
// and debug.
//
import { useState } from 'react';
import { Card, Input, List, Spin, Typography, InputNumber, Switch, Space, Button, Row, Col, Statistic, Select, Collapse, message, Drawer, Divider, Tag } from 'antd';
import { ApiQueryResponse, Source, ApiQueryRequest } from '../../types/api.types';

const { Title, Text, Link, Paragraph } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;

// Airbnb filter constants
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

interface SearchPlaygroundProps {
    metrics?: any;
}

const SAMPLE_QUERIES = [
    "Explain the architecture of SearchForge.",
    "How does the KV-cache and streaming experiment work?",
    "What is the AutoTuner responsible for?",
    "What are the main components of the search pipeline?",
    "How does reranking improve search results?",
    // Airbnb LA queries
    "Find a 2-bedroom entire home in Hollywood under $250 per night.",
    "Quiet studio in Downtown LA with good availability.",
    "Family-friendly Airbnb near Santa Monica with at least 2 bedrooms.",
];

export const SearchPlayground = ({ metrics }: SearchPlaygroundProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<ApiQueryResponse | null>(null);
    const [query, setQuery] = useState<string>('');
    const [topK, setTopK] = useState<number>(20);
    const [rerank, setRerank] = useState<boolean>(false);
    const [generateAnswer, setGenerateAnswer] = useState<boolean>(true);
    const [stream, setStream] = useState<boolean>(false);
    const [useKvCache, setUseKvCache] = useState<boolean>(false);
    const [collection, setCollection] = useState<string>(''); // 空字符串表示使用默认 collection
    const [selectedSource, setSelectedSource] = useState<Source | null>(null);
    const [drawerVisible, setDrawerVisible] = useState<boolean>(false);
    // Airbnb filter state
    const [priceMax, setPriceMax] = useState<number | undefined>(undefined);
    const [minBedrooms, setMinBedrooms] = useState<number | undefined>(undefined);
    const [neighbourhood, setNeighbourhood] = useState<string | undefined>(undefined);
    const [roomType, setRoomType] = useState<string | undefined>(undefined);

    const handleSearch = () => {
        if (!query.trim()) return;

        // Note: Streaming is not supported in this component. Use the KV & Streaming tab for streaming queries.
        if (stream) {
            message.warning('Streaming is not supported in this view. Use the "KV & Streaming" tab for streaming queries.');
            return;
        }

        setIsLoading(true);
        setResult(null);

        // Construct payload with Airbnb filters when using airbnb_la_demo collection
        const payload: ApiQueryRequest = {
            question: query,
            top_k: topK,
            rerank: rerank,
            generate_answer: generateAnswer,
            stream: stream,
            use_kv_cache: useKvCache,
            ...(collection ? { collection: collection } : {}),
            // ✅ When using Airbnb demo, add profile & filters
            ...(collection === 'airbnb_la_demo'
                ? {
                    profile_name: 'airbnb_la_location_first', // Match backend profile name
                    price_max: priceMax ?? null,
                    min_bedrooms: minBedrooms ?? null,
                    neighbourhood: neighbourhood ?? null,
                    room_type: roomType ?? null,
                }
                : {}),
        };

        // Remove undefined values to avoid sending them (backend will use null/None instead)
        const cleanedPayload = Object.fromEntries(
            Object.entries(payload).filter(([_, v]) => v !== undefined)
        ) as ApiQueryRequest;

        const requestBody = JSON.stringify(cleanedPayload);

        fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: requestBody,
        })
            .then((res) => res.json())
            .then((data: ApiQueryResponse) => {
                setResult(data);
            })
            .catch((err) => {
                console.error('Query failed:', err);
                message.error(`Query failed: ${err.message || 'Unknown error'}`);
            })
            .finally(() => setIsLoading(false));
    };

    const handleSampleQuerySelect = (value: string) => {
        setQuery(value);
    };

    const isLLMDisabled = !generateAnswer || (result?.metrics?.llm_enabled === false);

    return (
        <div style={{ padding: '24px', minHeight: '100%' }}>
            <Row gutter={16}>
                {/* Left Column: Query Form */}
                <Col span={6}>
                    <Card title={<span style={{ fontSize: '18px' }}>Query Form</span>} bordered={false}>
                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                            <div>
                                <Text strong style={{ fontSize: '16px' }}>Sample Queries</Text>
                                <Select
                                    placeholder="Select a sample query..."
                                    style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                    onChange={handleSampleQuerySelect}
                                    options={SAMPLE_QUERIES.map((q, idx) => ({
                                        label: q,
                                        value: q,
                                    }))}
                                />
                            </div>

                            <div>
                                <Text strong style={{ fontSize: '16px' }}>Question</Text>
                                <TextArea
                                    placeholder="Enter your question here..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    rows={4}
                                    style={{ marginTop: '8px', fontSize: '16px' }}
                                    onPressEnter={(e) => {
                                        if (e.shiftKey) return; // Allow new lines with Shift+Enter
                                        e.preventDefault();
                                        handleSearch();
                                    }}
                                />
                            </div>

                            <div>
                                <Text strong style={{ fontSize: '16px' }}>top_k</Text>
                                <InputNumber
                                    value={topK}
                                    onChange={(value) => setTopK(value || 20)}
                                    min={1}
                                    max={100}
                                    style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                />
                            </div>

                            <div>
                                <Space>
                                    <Switch
                                        checked={rerank}
                                        onChange={setRerank}
                                    />
                                    <Text style={{ fontSize: '16px' }}>Rerank</Text>
                                </Space>
                            </div>

                            <div>
                                <Space>
                                    <Switch
                                        checked={generateAnswer}
                                        onChange={setGenerateAnswer}
                                    />
                                    <Text style={{ fontSize: '16px' }}>Generate Answer</Text>
                                </Space>
                            </div>

                            <div>
                                <Space>
                                    <Switch
                                        checked={stream}
                                        onChange={setStream}
                                    />
                                    <Text style={{ fontSize: '16px' }}>Stream</Text>
                                </Space>
                            </div>

                            <div>
                                <Space>
                                    <Switch
                                        checked={useKvCache}
                                        onChange={setUseKvCache}
                                    />
                                    <Text style={{ fontSize: '16px' }}>Use KV Cache</Text>
                                </Space>
                            </div>

                            <div>
                                <Text strong style={{ fontSize: '16px' }}>Collection (optional)</Text>
                                <Select
                                    value={collection || undefined}
                                    onChange={(value) => {
                                        setCollection(value || '');
                                        // Reset Airbnb filters when switching away from airbnb_la_demo
                                        if (value !== 'airbnb_la_demo') {
                                            setPriceMax(undefined);
                                            setMinBedrooms(undefined);
                                            setNeighbourhood(undefined);
                                            setRoomType(undefined);
                                        }
                                    }}
                                    placeholder="Use default collection"
                                    allowClear
                                    style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                >
                                    <Select.Option value="fiqa">fiqa</Select.Option>
                                    <Select.Option value="airbnb_la_demo">airbnb_la_demo</Select.Option>
                                </Select>
                            </div>

                            {/* Airbnb Filters Card - Only show when airbnb_la_demo is selected */}
                            {collection === 'airbnb_la_demo' && (
                                <Card title={<span style={{ fontSize: '18px' }}>Airbnb Filters (LA)</span>} bordered={false} style={{ marginTop: '16px' }}>
                                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                        <div>
                                            <Text strong style={{ fontSize: '16px' }}>Max Price ($/night)</Text>
                                            <InputNumber
                                                value={priceMax}
                                                onChange={(value) => setPriceMax(value ?? undefined)}
                                                placeholder="e.g., 200"
                                                min={0}
                                                max={10000}
                                                step={10}
                                                style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                                addonBefore="$"
                                            />
                                        </div>

                                        <div>
                                            <Text strong style={{ fontSize: '16px' }}>Min Bedrooms</Text>
                                            <InputNumber
                                                value={minBedrooms}
                                                onChange={(value) => setMinBedrooms(value ?? undefined)}
                                                placeholder="e.g., 2"
                                                min={0}
                                                max={10}
                                                style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                            />
                                        </div>

                                        <div>
                                            <Text strong style={{ fontSize: '16px' }}>Neighbourhood</Text>
                                            <Select
                                                value={neighbourhood || undefined}
                                                onChange={(value) => setNeighbourhood(value || undefined)}
                                                placeholder="Select neighbourhood"
                                                allowClear
                                                style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                            >
                                                {AIRBNB_NEIGHBOURHOODS.map((n) => (
                                                    <Select.Option key={n} value={n}>
                                                        {n}
                                                    </Select.Option>
                                                ))}
                                            </Select>
                                        </div>

                                        <div>
                                            <Text strong style={{ fontSize: '16px' }}>Room Type</Text>
                                            <Select
                                                value={roomType || undefined}
                                                onChange={(value) => setRoomType(value || undefined)}
                                                placeholder="Select room type"
                                                allowClear
                                                style={{ width: '100%', marginTop: '8px', fontSize: '16px' }}
                                            >
                                                {AIRBNB_ROOM_TYPES.map((rt) => (
                                                    <Select.Option key={rt} value={rt}>
                                                        {rt}
                                                    </Select.Option>
                                                ))}
                                            </Select>
                                        </div>
                                    </Space>
                                </Card>
                            )}

                            {/* Active Filters Display (Optional) */}
                            {collection === 'airbnb_la_demo' && (priceMax !== undefined || minBedrooms !== undefined || neighbourhood || roomType) && (
                                <div style={{ marginTop: '16px' }}>
                                    <Text strong style={{ display: 'block', marginBottom: '8px', fontSize: '16px' }}>
                                        Active Filters:
                                    </Text>
                                    <Space wrap>
                                        {priceMax !== undefined && <Tag color="blue">Price ≤ ${priceMax}/night</Tag>}
                                        {minBedrooms !== undefined && <Tag color="green">Bedrooms ≥ {minBedrooms}</Tag>}
                                        {neighbourhood && <Tag color="orange">Neighbourhood: {neighbourhood}</Tag>}
                                        {roomType && <Tag color="purple">Room Type: {roomType}</Tag>}
                                    </Space>
                                </div>
                            )}

                            <Button
                                type="primary"
                                onClick={handleSearch}
                                loading={isLoading}
                                block
                                style={{ marginTop: '16px' }}
                            >
                                Search
                            </Button>
                        </Space>
                    </Card>
                </Col>

                {/* Middle Column: Answer + Sources */}
                <Col span={10}>
                    <Spin spinning={isLoading}>
                        {result ? (
                            <>
                                <Card title={<Title level={4}>Answer</Title>} bordered={false} style={{ marginBottom: '16px' }}>
                                    {isLLMDisabled ? (
                                        <Text type="secondary" style={{ fontStyle: 'italic', fontSize: '17px' }}>
                                            LLM answer disabled – only retrieval results are shown.
                                        </Text>
                                    ) : result.answer ? (
                                        <Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: '17px', lineHeight: '1.7' }}>{result.answer}</Paragraph>
                                    ) : (
                                        <Text type="secondary" style={{ fontSize: '17px' }}>No answer generated.</Text>
                                    )}
                                </Card>

                                <Card title={<Title level={4}>Sources</Title>} bordered={false} style={{ marginBottom: '16px' }}>
                                    {result.sources && result.sources.length > 0 ? (
                                        <List
                                            dataSource={result.sources}
                                            renderItem={(item: Source) => {
                                                // 检查是否是 Airbnb collection（通过检查是否有 Airbnb 特定字段）
                                                const isAirbnb = item.price !== undefined || item.neighbourhood !== undefined;
                                                return (
                                                    <List.Item>
                                                        <div style={{ width: '100%' }}>
                                                            <Text
                                                                style={{
                                                                    color: '#1890ff',
                                                                    cursor: 'pointer',
                                                                    textDecoration: 'underline',
                                                                    fontSize: '17px',
                                                                }}
                                                                onClick={() => {
                                                                    setSelectedSource(item);
                                                                    setDrawerVisible(true);
                                                                }}
                                                            >
                                                                {item.title || item.doc_id}
                                                            </Text>
                                                            {item.score !== undefined && (
                                                                <Text type="secondary" style={{ marginLeft: '8px', fontSize: '16px' }}>
                                                                    (Score: {item.score.toFixed(3)})
                                                                </Text>
                                                            )}
                                                            {/* Airbnb 字段展示 */}
                                                            {isAirbnb && (
                                                                <div style={{ marginTop: '4px' }}>
                                                                    <Text type="secondary" style={{ fontSize: '16px' }}>
                                                                        {item.neighbourhood && <span>{item.neighbourhood}</span>}
                                                                        {item.room_type && <span> • {item.room_type}</span>}
                                                                        {item.price !== undefined && item.price > 0 && (
                                                                            <span> • ${item.price.toFixed(0)}/night</span>
                                                                        )}
                                                                        {item.bedrooms !== undefined && item.bedrooms > 0 && (
                                                                            <span> • {item.bedrooms} bedroom{item.bedrooms > 1 ? 's' : ''}</span>
                                                                        )}
                                                                    </Text>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </List.Item>
                                                );
                                            }}
                                        />
                                    ) : (
                                        <Text type="secondary">No sources found.</Text>
                                    )}
                                </Card>

                                {/* Source Detail Drawer */}
                                <Drawer
                                    title={selectedSource?.title || selectedSource?.doc_id || 'Source Details'}
                                    placement="right"
                                    width={600}
                                    onClose={() => {
                                        setDrawerVisible(false);
                                        setSelectedSource(null);
                                    }}
                                    open={drawerVisible}
                                >
                                    {selectedSource && (
                                        <div>
                                            <div style={{ marginBottom: '16px' }}>
                                                <Text strong style={{ fontSize: '17px' }}>Document ID:</Text>
                                                <Paragraph copyable style={{ marginTop: '4px', fontSize: '16px' }}>
                                                    {selectedSource.doc_id}
                                                </Paragraph>
                                            </div>

                                            {selectedSource.score !== undefined && (
                                                <div style={{ marginBottom: '16px' }}>
                                                    <Text strong style={{ fontSize: '17px' }}>Relevance Score: </Text>
                                                    <Text style={{ fontSize: '16px' }}>{selectedSource.score.toFixed(4)}</Text>
                                                </div>
                                            )}

                                            {/* Airbnb specific fields */}
                                            {(selectedSource.price !== undefined ||
                                                selectedSource.bedrooms !== undefined ||
                                                selectedSource.neighbourhood ||
                                                selectedSource.room_type) && (
                                                    <>
                                                        <Divider orientation="left">Listing Details</Divider>
                                                        <Space direction="vertical" style={{ width: '100%' }} size="small">
                                                            {selectedSource.neighbourhood && (
                                                                <div>
                                                                    <Text strong style={{ fontSize: '17px' }}>Neighbourhood: </Text>
                                                                    <Text style={{ fontSize: '16px' }}>{selectedSource.neighbourhood}</Text>
                                                                </div>
                                                            )}
                                                            {selectedSource.room_type && (
                                                                <div>
                                                                    <Text strong style={{ fontSize: '17px' }}>Room Type: </Text>
                                                                    <Text style={{ fontSize: '16px' }}>{selectedSource.room_type}</Text>
                                                                </div>
                                                            )}
                                                            {selectedSource.price !== undefined && selectedSource.price > 0 && (
                                                                <div>
                                                                    <Text strong style={{ fontSize: '17px' }}>Price: </Text>
                                                                    <Text style={{ color: '#cf1322', fontSize: '18px' }}>
                                                                        ${selectedSource.price.toFixed(0)}/night
                                                                    </Text>
                                                                </div>
                                                            )}
                                                            {selectedSource.bedrooms !== undefined && selectedSource.bedrooms > 0 && (
                                                                <div>
                                                                    <Text strong style={{ fontSize: '17px' }}>Bedrooms: </Text>
                                                                    <Text style={{ fontSize: '16px' }}>{selectedSource.bedrooms} bedroom{selectedSource.bedrooms > 1 ? 's' : ''}</Text>
                                                                </div>
                                                            )}
                                                        </Space>
                                                    </>
                                                )}

                                            {/* Text content */}
                                            {selectedSource.text && (
                                                <>
                                                    <Divider orientation="left">Description</Divider>
                                                    <Paragraph style={{ whiteSpace: 'pre-wrap', maxHeight: '400px', overflow: 'auto', fontSize: '16px', lineHeight: '1.7' }}>
                                                        {selectedSource.text}
                                                    </Paragraph>
                                                </>
                                            )}

                                            {!selectedSource.text && (
                                                <Text type="secondary" style={{ fontStyle: 'italic', fontSize: '16px' }}>
                                                    No description available.
                                                </Text>
                                            )}
                                        </div>
                                    )}
                                </Drawer>

                                <Collapse style={{ marginTop: '16px' }}>
                                    <Panel header="Raw Response (Debug)" key="raw">
                                        <pre
                                            style={{
                                                background: '#1a1a1a',
                                                color: '#fff',
                                                padding: '16px',
                                                borderRadius: '8px',
                                                fontSize: '16px',
                                                overflow: 'auto',
                                                maxHeight: '400px',
                                                fontFamily: 'monospace',
                                            }}
                                        >
                                            {JSON.stringify(result, null, 2)}
                                        </pre>
                                    </Panel>
                                </Collapse>
                            </>
                        ) : (
                            <Card bordered={false}>
                                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                    <Text type="secondary">Enter a query and click Search to see results.</Text>
                                </div>
                            </Card>
                        )}
                    </Spin>
                </Col>

                {/* Right Column: Metrics */}
                <Col span={8}>
                    <Card title={<span style={{ fontSize: '18px' }}>Metrics</span>} bordered={false}>
                        {result ? (
                            <Row gutter={16}>
                                <Col span={24} style={{ marginBottom: '16px' }}>
                                    <Statistic
                                        title={<span style={{ fontSize: '16px' }}>Latency</span>}
                                        value={result.latency_ms}
                                        precision={1}
                                        suffix="ms"
                                        valueStyle={{ color: result.latency_ms > 100 ? '#cf1322' : '#3f8600', fontSize: '20px' }}
                                    />
                                </Col>
                                <Col span={24} style={{ marginBottom: '16px' }}>
                                    <Statistic
                                        title={<span style={{ fontSize: '16px' }}>LLM Enabled</span>}
                                        value={result.metrics?.llm_enabled ? 'Yes' : 'No'}
                                        valueStyle={{ color: result.metrics?.llm_enabled ? '#3f8600' : '#999', fontSize: '18px' }}
                                    />
                                </Col>
                                {result.metrics?.llm_usage?.total_tokens !== undefined && (
                                    <Col span={24} style={{ marginBottom: '16px' }}>
                                        <Statistic
                                            title={<span style={{ fontSize: '16px' }}>Total Tokens</span>}
                                            value={result.metrics.llm_usage.total_tokens}
                                            valueStyle={{ color: '#3f8600', fontSize: '18px' }}
                                        />
                                    </Col>
                                )}
                                {result.metrics?.llm_usage?.cost_usd_est !== undefined && result.metrics.llm_usage.cost_usd_est !== null && (
                                    <Col span={24} style={{ marginBottom: '16px' }}>
                                        <Statistic
                                            title={<span style={{ fontSize: '16px' }}>Cost (USD est.)</span>}
                                            value={result.metrics.llm_usage.cost_usd_est}
                                            precision={4}
                                            prefix="$"
                                            valueStyle={{ color: '#3f8600', fontSize: '18px' }}
                                        />
                                    </Col>
                                )}
                                {result.route && (
                                    <Col span={24} style={{ marginBottom: '16px' }}>
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '16px' }}>Route: </Text>
                                            <Text strong style={{ fontSize: '16px' }}>{result.route}</Text>
                                        </div>
                                    </Col>
                                )}
                            </Row>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                <Text type="secondary" style={{ fontSize: '16px' }}>Metrics will appear here after a query.</Text>
                            </div>
                        )}
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

