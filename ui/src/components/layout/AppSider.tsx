// frontend/src/components/layout/AppSider.tsx
import {
    RocketOutlined,
    ExperimentOutlined,
    RobotOutlined,
    SearchOutlined,
    OrderedListOutlined,
    DatabaseOutlined,
    ThunderboltOutlined,
    NodeIndexOutlined,
    ToolOutlined,
    BarChartOutlined
} from '@ant-design/icons';
import { Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';

const menuItems = [
    {
        key: '/',
        icon: <RocketOutlined />,
        label: <Link to="/">Showtime</Link>,
    },
    {
        key: '/workbench',
        icon: <ExperimentOutlined />,
        label: <Link to="/workbench">Experiment Lab</Link>,
    },
    {
        key: '/codemap',
        icon: <NodeIndexOutlined />,
        label: <Link to="/codemap">Code Map</Link>,
    },
    {
        key: '/rag-lab-sub',
        icon: <ToolOutlined />,
        label: 'RAG Lab',
        children: [
            {
                key: '/rag-lab/run',
                icon: <ExperimentOutlined />,
                label: <Link to="/rag-lab/run">Run Experiment</Link>,
            },
            {
                key: '/rag-lab/history',
                icon: <SearchOutlined />,
                label: <Link to="/rag-lab/history">Job History</Link>,
            },
            {
                key: '/lab/metrics',
                icon: <BarChartOutlined />,
                label: <Link to="/lab/metrics">Metrics Hub (beta)</Link>,
            },
            {
                key: '/rag-lab/steward',
                icon: <RobotOutlined />,
                label: <Link to="/rag-lab/steward">Lab Steward</Link>,
            },
        ],
    },
    {
        key: '/workbench-sub',
        icon: <RobotOutlined />,
        label: 'AI Workbench',
        children: [
            {
                key: '/workbench/agent-studio',
                icon: <RobotOutlined />,
                label: <Link to="/workbench/agent-studio">Agent Studio</Link>,
            },
            {
                key: '/workbench/code-lookup-agent',
                icon: <NodeIndexOutlined />,
                label: <Link to="/workbench/code-lookup-agent">Code Intelligence Lab</Link>,
            },
            {
                key: '/workbench/retriever-lab',
                icon: <SearchOutlined />,
                label: <Link to="/workbench/retriever-lab">Retriever Lab</Link>,
            },
            {
                key: '/workbench/ranker-lab',
                icon: <OrderedListOutlined />,
                label: <Link to="/workbench/ranker-lab">Ranker Lab</Link>,
            },
            {
                key: '/workbench/index-explorer',
                icon: <DatabaseOutlined />,
                label: <Link to="/workbench/index-explorer">Index Explorer</Link>,
            },
            {
                key: '/workbench/sla-tuner-lab',
                icon: <ThunderboltOutlined />,
                label: <Link to="/workbench/sla-tuner-lab">SLA Tuner Lab</Link>,
            },
        ],
    },
];

export const AppSider = () => {
    const location = useLocation();
    const [selectedKeys, setSelectedKeys] = useState([location.pathname]);

    useEffect(() => {
        setSelectedKeys([location.pathname]);
    }, [location.pathname]);

    return (
        <Menu
            mode="inline"
            selectedKeys={selectedKeys}
            defaultOpenKeys={['/workbench-sub', '/rag-lab-sub']}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
        />
    );
};

