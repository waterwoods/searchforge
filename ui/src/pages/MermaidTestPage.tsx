import React from 'react';
import { Card, Typography } from 'antd';
import MermaidTest from '../components/MermaidTest';

const { Title } = Typography;

const MermaidTestPage: React.FC = () => {
    return (
        <div style={{ padding: '24px' }}>
            <Title level={2}>Mermaid.js 环境验证</Title>
            <Card>
                <MermaidTest />
            </Card>
        </div>
    );
};

export default MermaidTestPage;
