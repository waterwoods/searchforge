// frontend/src/pages/WorkbenchPage.tsx
import { useEffect, useState } from 'react';
import { Table, Tag, Typography, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ApiExperimentItem, ApiLeaderboardResponse } from '../types/api.types';
import { useAppStore } from '../store/useAppStore';

const { Title } = Typography;

// Define the columns for our table as a function that uses the hook
const WorkbenchColumns = (): ColumnsType<ApiExperimentItem> => {
    const { setCurrentExperimentId } = useAppStore();

    return [
        {
            title: 'Experiment ID',
            dataIndex: 'exp_id',
            key: 'exp_id',
            render: (text, record) => (
                <Button
                    type="link"
                    style={{ padding: 0 }}
                    onClick={() => setCurrentExperimentId(record.exp_id)}
                >
                    {text}
                </Button>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (text) => new Date(text).toLocaleString(),
        },
        {
            title: 'Params',
            dataIndex: 'params',
            key: 'params',
            render: (params) => <pre style={{ margin: 0 }}>{JSON.stringify(params, null, 2)}</pre>,
        },
        {
            title: 'P95 (ms)',
            dataIndex: 'p95_ms',
            key: 'p95_ms',
            sorter: (a, b) => a.p95_ms - b.p95_ms,
        },
        {
            title: 'Recall@K',
            dataIndex: 'recall_k',
            key: 'recall_k',
            render: (val) => `${(val * 100).toFixed(1)}%`,
            sorter: (a, b) => a.recall_k - b.recall_k,
        },
        {
            title: 'Verdict',
            dataIndex: 'verdict',
            key: 'verdict',
            render: (verdict: string) => {
                let color = 'geekblue';
                if (verdict === 'PASS') color = 'green';
                if (verdict === 'FAIL') color = 'volcano';
                if (verdict === 'EDGE') color = 'gold';
                return <Tag color={color}>{verdict.toUpperCase()}</Tag>;
            },
            filters: [
                { text: 'PASS', value: 'PASS' },
                { text: 'EDGE', value: 'EDGE' },
                { text: 'FAIL', value: 'FAIL' },
            ],
            onFilter: (value, record) => record.verdict === value,
        },
    ];
};

export const WorkbenchPage = () => {
    const [data, setData] = useState<ApiExperimentItem[]>([]);
    const [loading, setLoading] = useState(true);
    const columns = WorkbenchColumns(); // Call the function to get columns

    useEffect(() => {
        setLoading(true);
        fetch('/api/experiments/leaderboard')
            .then((res) => res.json())
            .then((json: ApiLeaderboardResponse) => {
                setData(json.items);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return (
        <div>
            <Title level={2}>Workbench: Experiment Leaderboard</Title>
            <Table
                columns={columns}
                dataSource={data}
                loading={loading}
                rowKey="exp_id"
            />
        </div>
    );
};
