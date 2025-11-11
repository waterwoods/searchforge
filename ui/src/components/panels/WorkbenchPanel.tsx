// frontend/src/components/panels/WorkbenchPanel.tsx
import { useEffect, useState } from 'react';
import { Card, Empty, Spin, Statistic, Row, Col, Table, Tag } from 'antd';
import { useAppStore } from '../../store/useAppStore';
import { ApiRagTriadResponse, ApiTriadSample } from '../../types/api.types';
import type { ColumnsType } from 'antd/es/table';

const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'green';
    if (score >= 0.8) return 'gold';
    return 'red';
};

const sampleColumns: ColumnsType<ApiTriadSample> = [
    { title: 'Question', dataIndex: 'question', key: 'question' },
    {
        title: 'Grounded',
        dataIndex: 'scores',
        key: 'grounded',
        render: (scores) => (
            <Tag color={getScoreColor(scores.groundedness)}>
                {scores.groundedness.toFixed(2)}
            </Tag>
        )
    },
    {
        title: 'Ctx. Rel.',
        dataIndex: 'scores',
        key: 'context',
        render: (scores) => (
            <Tag color={getScoreColor(scores.context_relevance)}>
                {scores.context_relevance.toFixed(2)}
            </Tag>
        )
    },
];

export const WorkbenchPanel = () => {
    const { currentExperimentId } = useAppStore();
    const [data, setData] = useState<ApiRagTriadResponse | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!currentExperimentId) {
            setData(null);
            return;
        }

        setLoading(true);
        fetch(`/api/experiments/${currentExperimentId}/rag-triad`)
            .then((res) => res.json())
            .then((json: ApiRagTriadResponse) => setData(json))
            .catch(console.error)
            .finally(() => setLoading(false));

    }, [currentExperimentId]);

    if (loading) {
        return <Spin style={{ padding: '24px' }} />;
    }

    if (!data) {
        return <Empty description="Select an experiment to see details" style={{ padding: '24px' }} />;
    }

    return (
        <div style={{ padding: '16px' }}>
            <Card title={`RAG Triad: ${data.exp_id}`}>
                <Row gutter={16}>
                    <Col span={8}>
                        <Statistic title="Context Relevance" value={data.summary.context_relevance * 100} suffix="%" valueStyle={{ color: getScoreColor(data.summary.context_relevance) }} />
                    </Col>
                    <Col span={8}>
                        <Statistic title="Groundedness" value={data.summary.groundedness * 100} suffix="%" valueStyle={{ color: getScoreColor(data.summary.groundedness) }} />
                    </Col>
                    <Col span={8}>
                        <Statistic title="Answer Relevance" value={data.summary.answer_relevance * 100} suffix="%" valueStyle={{ color: getScoreColor(data.summary.answer_relevance) }} />
                    </Col>
                </Row>
            </Card>
            <Table
                title={() => 'Bad Samples'}
                columns={sampleColumns}
                dataSource={data.samples}
                rowKey="trace_id"
                size="small"
                style={{ marginTop: '20px' }}
            />
        </div>
    );
};

