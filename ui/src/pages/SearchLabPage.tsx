// frontend/src/pages/SearchLabPage.tsx
import { Card, Tabs, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { SearchPlayground } from '../components/search/SearchPlayground';
import { SearchKVStreamingTab } from './SearchKVStreamingTab';
import { useAppStore } from '../store/useAppStore';

const { Title, Paragraph } = Typography;

export const SearchLabPage = () => {
    const { currentMetrics } = useAppStore();

    return (
        <div style={{ padding: '24px' }}>
            <Title level={2} style={{ marginBottom: '24px' }}>
                <SearchOutlined /> Search Lab
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                Interactive playground and performance lab for the unified search API.
            </Paragraph>

            <Card bordered={false}>
                <Tabs
                    defaultActiveKey="playground"
                    items={[
                        {
                            key: 'playground',
                            label: 'Playground',
                            children: (
                                <SearchPlayground metrics={currentMetrics} />
                            ),
                        },
                        {
                            key: 'kv-streaming',
                            label: 'KV & Streaming Experiment',
                            children: <SearchKVStreamingTab />,
                        },
                    ]}
                />
            </Card>
        </div>
    );
};

