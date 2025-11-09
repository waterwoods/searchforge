// frontend/src/pages/RankerLabPage.tsx
import { useState, useEffect } from 'react';
import { Row, Col, Input, Card, List, Spin, Typography, Divider } from 'antd';
import { ApiRankerSimulationResponse, RetrieverResultItem } from '../types/api.types'; // Import RetrieverResultItem

const { Title, Text } = Typography;

export const RankerLabPage = () => {
    const [query, setQuery] = useState('example query needing reranking');
    const [results, setResults] = useState<ApiRankerSimulationResponse[]>([]);
    const [loading, setLoading] = useState(false);

    // Function to fetch simulation data for both models
    const fetchSimulations = async () => {
        setLoading(true);
        setResults([]); // Clear previous results
        try {
            // In a real app, send the query too
            const res = await fetch(`/api/labs/ranker/simulate?query=${encodeURIComponent(query)}`);
            const data: ApiRankerSimulationResponse[] = await res.json();
            if (Array.isArray(data) && data.length === 2) {
                setResults(data);
            } else {
                console.error("Unexpected response structure from ranker simulate API");
                setResults([]); // Clear results on error
            }
        } catch (error) {
            console.error(`Failed to fetch ranker simulations:`, error);
            setResults([]); // Clear results on error
        } finally {
            setLoading(false);
        }
    };

    // Fetch initial data on mount
    useEffect(() => {
        fetchSimulations();
    }, []);

    const renderResultList = (result: ApiRankerSimulationResponse) => {
        return (
            <>
                <Text strong>NDCG@10: {result.metrics.ndcg_at_10.toFixed(2)} | Latency: {result.metrics.latency_ms.toFixed(1)} ms</Text>
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
            <Title level={2}>Ranker Lab</Title>
            <Input.Search
                placeholder="Enter query to compare rankers..."
                defaultValue={query}
                onSearch={(q) => {
                    setQuery(q);
                    fetchSimulations(); // Re-fetch on new query
                }}
                style={{ marginBottom: '20px' }}
                enterButton="Compare Rankers"
                loading={loading}
            />

            <Spin spinning={loading}>
                <Row gutter={16}>
                    {results.length === 2 ? (
                        results.map((result, index) => (
                            <Col span={12} key={index}>
                                <Card title={`Model: ${result.model_name}`}>
                                    {renderResultList(result)}
                                </Card>
                            </Col>
                        ))
                    ) : (
                        !loading && <Text type="secondary" style={{ paddingLeft: '8px' }}>Failed to load simulation data. Check console.</Text>
                    )}
                </Row>
            </Spin>
        </div>
    );
};
