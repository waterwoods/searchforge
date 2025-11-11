// frontend/src/components/panels/QualityPanel.tsx
import { Card, Col, Empty, Progress, Row, Typography } from 'antd';
import { useAppStore } from '../../store/useAppStore';

const { Text } = Typography;

const getScoreStatus = (score: number): "success" | "exception" | "normal" => {
    if (score >= 0.9) return "success";
    if (score >= 0.8) return "normal";
    return "exception";
};

export const QualityPanel = () => {
    const { currentRagTriad } = useAppStore();

    if (!currentRagTriad) {
        return <Empty description="Run a query to see RAG quality scores" style={{ padding: '24px' }} />;
    }

    const formatPercent = (value?: number) => value ? Math.round(value * 100) : 0;

    return (
        <div style={{ padding: '16px' }}>
            <Card title="RAG Quality Triad (Mock Scores)">
                <Row gutter={[16, 24]}>
                    <Col span={24}>
                        <Text strong>Context Relevance:</Text>
                        <Progress
                            percent={formatPercent(currentRagTriad.context_relevance)}
                            status={getScoreStatus(currentRagTriad.context_relevance)}
                            format={(percent) => `${percent}%`}
                        />
                        <Text type="secondary" style={{ fontSize: '12px' }}>Is retrieved context relevant to the query?</Text>
                    </Col>
                    <Col span={24}>
                        <Text strong>Groundedness:</Text>
                        <Progress
                            percent={formatPercent(currentRagTriad.groundedness)}
                            status={getScoreStatus(currentRagTriad.groundedness)}
                            format={(percent) => `${percent}%`}
                        />
                        <Text type="secondary" style={{ fontSize: '12px' }}>Is the answer supported by the retrieved context?</Text>
                    </Col>
                    <Col span={24}>
                        <Text strong>Answer Relevance:</Text>
                        <Progress
                            percent={formatPercent(currentRagTriad.answer_relevance)}
                            status={getScoreStatus(currentRagTriad.answer_relevance)}
                            format={(percent) => `${percent}%`}
                        />
                        <Text type="secondary" style={{ fontSize: '12px' }}>Does the answer address the original query?</Text>
                    </Col>
                </Row>
            </Card>
        </div>
    );
};

