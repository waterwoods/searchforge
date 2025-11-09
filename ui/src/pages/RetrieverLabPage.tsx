// frontend/src/pages/RetrieverLabPage.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Input, Slider, Card, List, Spin, Typography, Divider, Form } from 'antd'; // Ensure Form is imported
import { ApiRetrieverSimulationResponse, RetrieverResultItem } from '../types/api.types'; // Import RetrieverResultItem

const { Title, Text } = Typography;

export const RetrieverLabPage = () => {
    const [query, setQuery] = useState('example query');
    const [efValue, setEfValue] = useState(50); // Start with 'Before' state
    const [beforeResult, setBeforeResult] = useState<ApiRetrieverSimulationResponse | null>(null);
    const [afterResult, setAfterResult] = useState<ApiRetrieverSimulationResponse | null>(null);
    const [loading, setLoading] = useState(false);

    // Function to fetch simulation data
    const fetchSimulation = async (ef: number) => {
        setLoading(true);
        try {
            // In a real app, send the query too
            const res = await fetch(`/api/labs/retriever/simulate?ef=${ef}`);
            const data: ApiRetrieverSimulationResponse = await res.json();
            if (ef === 50) setBeforeResult(data);
            if (ef === 200) setAfterResult(data);
        } catch (error) {
            console.error(`Failed to fetch simulation for ef=${ef}:`, error);
            // Set state to null or handle error display
            if (ef === 50) setBeforeResult(null);
            if (ef === 200) setAfterResult(null);
        } finally {
            setLoading(false);
        }
    };

    // Fetch initial 'Before' data on mount
    useEffect(() => {
        fetchSimulation(50);
        setAfterResult(null); // Ensure 'After' is clear initially
    }, []);

    // Handle slider change - triggers fetching 'After' data
    const handleSliderChange = (value: number) => {
        setEfValue(value);
        // Simulate fetching 'After' only when slider moves towards it
        if (value > 100) {
            fetchSimulation(200);
        } else {
            setAfterResult(null); // Clear 'After' if slider moves back
        }
    };

    const renderResultList = (result: ApiRetrieverSimulationResponse | null) => {
        if (!result) return <Text type="secondary">Run simulation...</Text>;
        return (
            <>
                <Text strong>P95: {result.metrics.p95_ms.toFixed(1)} ms | Recall@10: {(result.metrics.recall_at_10 * 100).toFixed(1)}%</Text>
                <Divider />
                <List
                    dataSource={result.results}
                    renderItem={(item: RetrieverResultItem) => ( // Explicit type
                        <List.Item>
                            <List.Item.Meta
                                title={`Doc: ${item.doc_id} (Score: ${item.score.toFixed(2)})`}
                                description={item.text_snippet}
                            />
                        </List.Item>
                    )}
                    size="small"
                />
            </>
        );
    };


    return (
        <div>
            <Title level={2}>Retriever Lab</Title>
            <Input.Search
                placeholder="Enter query to simulate retriever..."
                defaultValue={query}
                onSearch={(q) => {
                    setQuery(q);
                    // Re-fetch both on new query for simplicity in demo
                    fetchSimulation(50);
                    if (efValue > 100) fetchSimulation(200); else setAfterResult(null);
                }}
                style={{ marginBottom: '20px' }}
                enterButton="Simulate"
            />

            <Card title="Retriever Parameters (Simulated)" style={{ marginBottom: '20px' }}>
                <Form layout="vertical"> {/* Wrap Slider in Form for layout consistency */}
                    <Form.Item label={`HNSW ef Parameter: ${efValue}`}>
                        <Slider
                            min={50}
                            max={200}
                            step={50}
                            value={efValue}
                            onChange={handleSliderChange}
                            marks={{ 50: '50 (Baseline)', 200: '200 (Optimized)' }}
                        />
                    </Form.Item>
                </Form>
            </Card>

            <Spin spinning={loading}>
                <Row gutter={16}>
                    {/* Before Column */}
                    <Col span={12}>
                        <Card title="Baseline Results (ef=50)">
                            {renderResultList(beforeResult)}
                        </Card>
                    </Col>

                    {/* After Column */}
                    <Col span={12}>
                        <Card title={`Simulated Results (ef=${efValue})`}>
                            {renderResultList(afterResult)}
                        </Card>
                    </Col>
                </Row>
            </Spin>
        </div>
    );
};
