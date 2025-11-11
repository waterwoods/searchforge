// frontend/src/components/panels/RightPanelTabs.tsx
import { Tabs } from 'antd';
import { ExplainPanel } from './ExplainPanel';
import { ImprovePanel } from './ImprovePanel';
import { QualityPanel } from './QualityPanel';
import { ThunderboltOutlined, SlidersOutlined, CheckCircleOutlined } from '@ant-design/icons';

export const RightPanelTabs = () => {
    const items = [
        {
            label: 'Explain',
            key: '1',
            icon: <ThunderboltOutlined />,
            children: <ExplainPanel />,
        },
        {
            label: 'Improve',
            key: '2',
            icon: <SlidersOutlined />,
            children: <ImprovePanel />,
        },
        {
            label: 'Quality',
            key: '3',
            icon: <CheckCircleOutlined />,
            children: <QualityPanel />,
        },
    ];

    return <Tabs defaultActiveKey="1" items={items} style={{ padding: '0 16px' }} />;
};






