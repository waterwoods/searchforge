import React from 'react';
import { Card, Typography } from 'antd';
import EdgesJsonTest from '../components/EdgesJsonTest';

const { Title } = Typography;

const EdgesJsonTestPage: React.FC = () => {
    return (
        <div style={{ padding: '24px' }}>
            <Title level={2}>Edges JSON API 测试</Title>
            <Card>
                <EdgesJsonTest />
            </Card>
        </div>
    );
};

export default EdgesJsonTestPage;
