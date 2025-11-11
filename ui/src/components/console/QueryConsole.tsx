// frontend/src/components/console/QueryConsole.tsx
import { useState } from 'react';
import { Card, Input, List, Spin, Typography } from 'antd';
import { useAppStore } from '../../store/useAppStore';
import { ApiQueryResponse, Source } from '../../types/api.types';

const { Title, Text, Link } = Typography;

export const QueryConsole = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<ApiQueryResponse | null>(null);
    const { setCurrentTraceId, topK, rerank, setCurrentMetrics } = useAppStore();

    const handleSearch = (query: string) => {
        if (!query) return;

        setIsLoading(true); // Start loading immediately
        setResult(null);
        setCurrentTraceId(null);
        // Don't reset metrics here, let the response update them

        const isAfterQuery = rerank === true && topK <= 8; // Condition for "After" state
        const requestBody = JSON.stringify({
            question: query,
            top_k: topK,
            rerank: rerank,
        });

        const fetchQuery = () => {
            fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: requestBody,
            })
                .then((res) => res.json())
                .then((data: ApiQueryResponse) => {
                    setResult(data);
                    setCurrentTraceId(data.trace_id);

                    // Update global KPIs based on response
                    if (data.trace_id === 'tr_after_fast') {
                        setCurrentMetrics({
                            ok: true,
                            p95_ms: data.latency_ms,
                            recall_pct: 95.0, // Hardcoded "After" recall
                            qps: 3.2, err_pct: 0.0,
                        });
                    } else {
                        setCurrentMetrics({
                            ok: true,
                            p95_ms: data.latency_ms,
                            recall_pct: 82.0, // Hardcoded "Before" recall
                            qps: 3.2, err_pct: 0.0,
                        });
                    }
                })
                .catch((err) => console.error('Query failed:', err))
                .finally(() => setIsLoading(false)); // Stop loading only after fetch finishes
        };

        if (isAfterQuery) {
            // Add the 1.5 second "dramatic delay"
            setTimeout(fetchQuery, 1500);
        } else {
            // "Before" query runs instantly
            fetchQuery();
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <Input.Search
                placeholder="Explain investment returns in simple terms"
                enterButton="Ask"
                size="large"
                onSearch={handleSearch}
                loading={isLoading}
            />

            <Spin spinning={isLoading}>
                {result && (
                    <Card title={<Title level={4}>Answer</Title>}>
                        <Text>{result.answer}</Text>
                        <Title level={5} style={{ marginTop: '20px' }}>Sources</Title>
                        <List
                            dataSource={result.sources}
                            renderItem={(item: Source) => (
                                <List.Item>
                                    <Link href={item.url} target="_blank">
                                        {item.title} (Score: {item.score.toFixed(2)})
                                    </Link>
                                </List.Item>
                            )}
                        />
                    </Card>
                )}
            </Spin>
        </div>
    );
};

