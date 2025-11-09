// frontend/src/components/layout/AppLayout.tsx
import React from 'react';
import { Layout, theme } from 'antd';
import { Outlet, useLocation } from 'react-router-dom'; // <-- Add useLocation
import { KpiBar } from '../kpi/KpiBar';
import { RightPanelTabs } from '../panels/RightPanelTabs'; // This is for Showtime
import { WorkbenchPanel } from '../panels/WorkbenchPanel'; // <-- This is for Workbench
import { AppSider } from './AppSider';

const { Header, Content, Sider } = Layout;

export const AppLayout: React.FC = () => {
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    const location = useLocation();

    // --- NEW CONTEXT-AWARE LOGIC ---
    // Determine which panel to show in the right Sider
    let rightPanelContent;
    if (location.pathname === '/workbench/code-lookup-agent') {
        // Hide the generic right panel for the Code Lookup Agent page
        rightPanelContent = null;
    } else if (location.pathname === '/workbench') {
        // ONLY the Leaderboard page shows the Experiment (RAG Triad) panel
        rightPanelContent = <WorkbenchPanel />;
    } else {
        // Showtime (/) AND AgentStudio (/workbench/agent-studio)
        // both need the "Improve" controls (RightPanelTabs).
        rightPanelContent = <RightPanelTabs />;
    }
    // --- END NEW LOGIC ---

    return (
        <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Header style={{ display: 'flex', alignItems: 'center', color: 'white', flexShrink: 0 }}>
                <KpiBar />
            </Header>
            <Layout style={{ flex: 1, overflow: 'hidden' }}>
                <Sider width={200} style={{ overflow: 'auto' }}>
                    <AppSider />
                </Sider>
                <Layout style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <Content
                        style={{
                            flex: 1,
                            padding: 0,
                            margin: 0,
                            background: colorBgContainer,
                            borderRadius: borderRadiusLG,
                            overflow: 'hidden',
                            display: 'flex',
                            flexDirection: 'column'
                        }}
                    >
                        <Outlet />
                    </Content>
                </Layout>
                <Sider width={300} style={{ overflow: 'auto' }}>
                    {rightPanelContent} {/* <-- Render the correct panel */}
                </Sider>
            </Layout>
        </Layout>
    );
};
