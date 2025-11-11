// frontend/src/pages/IndexExplorerPage.tsx
import { useState, useEffect } from 'react';
import { Table, Spin, Typography, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ApiIndexExplorerResponse, ApiIndexPoint, QdrantPointPayload } from '../types/api.types';

const { Title, Text } = Typography;

// Define table columns
const columns: ColumnsType<ApiIndexPoint> = [
    {
        title: 'Point ID',
        dataIndex: 'id',
        key: 'id',
        ellipsis: true, // Truncate long IDs
        render: (id) => <Tooltip title={id}><Text copyable>{id.substring(0, 8)}...</Text></Tooltip>
    },
    {
        title: 'Source',
        dataIndex: 'payload',
        key: 'source',
        render: (payload: QdrantPointPayload) => (
            <div>
                <Tag color={payload.kind === 'function' ? 'geekblue' : payload.kind === 'class' ? 'volcano' : 'blue'}>
                    {payload.kind || 'chunk'}
                </Tag>
                <Text code style={{ marginLeft: '5px' }}>
                    {payload.name ? `${payload.file_path}::${payload.name}` : payload.file_path}
                </Text>
            </div>
        ),
    },
    {
        title: 'Chunk Index',
        dataIndex: ['payload', 'chunk_index'],
        key: 'chunk_index',
        width: 120,
    },
    {
        title: 'Edges',
        dataIndex: ['payload', 'edges_json'],
        key: 'edges',
        width: 80,
        render: (edgesJson: string | undefined) => {
            if (!edgesJson) {
                return <Text type="secondary">-</Text>;
            }
            try {
                const edges = JSON.parse(edgesJson);
                if (Array.isArray(edges)) {
                    return <Tag color="purple">{edges.length}</Tag>; // Show count
                }
            } catch (e) {
                return <Tag color="error">!</Tag>; // Indicate parse error
            }
            return <Text type="secondary">?</Text>; // Fallback
        },
    },
    {
        title: 'Text Snippet (Preview)',
        dataIndex: ['payload', 'text'],
        key: 'text',
        ellipsis: true, // Show only first line essentially
        render: (text) => <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{text}</pre>
    },
];

export const IndexExplorerPage = () => {
    const [points, setPoints] = useState<ApiIndexPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [totalPoints, setTotalPoints] = useState(0);

    // Function to fetch index data
    const fetchIndexData = async () => {
        setLoading(true);
        try {
            // In a real app, add pagination params
            const res = await fetch(`/api/index/browse`);
            const data: ApiIndexExplorerResponse = await res.json();
            if (data.ok) {
                setPoints(data.points);
                setTotalPoints(data.total); // In mock, this is just 3
            } else {
                console.error("Failed to fetch index data");
                setPoints([]); // Clear points on error
                setTotalPoints(0);
            }
        } catch (error) {
            console.error(`Failed to fetch index data:`, error);
            setPoints([]); // Clear points on error
            setTotalPoints(0);
        } finally {
            setLoading(false);
        }
    };

    // Fetch initial data on mount
    useEffect(() => {
        fetchIndexData();
    }, []);

    return (
        <div>
            <Title level={2}>Index Explorer</Title>
            <Text type="secondary">Browsing collection: searchforge_codebase (showing first {points.length} of {totalPoints} mock points)</Text>
            <Table
                columns={columns}
                dataSource={points}
                loading={loading}
                rowKey="id"
                style={{ marginTop: '20px' }}
            // Add pagination controls later if needed
            />
        </div>
    );
};
