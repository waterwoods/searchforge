// frontend/src/components/layout/AppLayout.tsx
import React from 'react';
import { Layout, Space, theme, Typography } from 'antd';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { KpiBar } from '../kpi/KpiBar';
import { RightPanelTabs } from '../panels/RightPanelTabs'; // This is for Showtime
import { WorkbenchPanel } from '../panels/WorkbenchPanel'; // <-- This is for Workbench
import { AppSider } from './AppSider';
import { ReleaseIdentityBar } from './ReleaseIdentityBar';
import { LabDevBanner } from './LabDevBanner';
import { useClientConfig } from '../../context/ClientConfigContext';
import { isUnifiedIntakeProductOnlyUi } from '../../config/productSurface';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

const UNIFIED_INTAKE_PATH = '/workbench/unified-intake';

export const AppLayout: React.FC = () => {
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    const location = useLocation();
    const isUnifiedIntake = location.pathname === UNIFIED_INTAKE_PATH;
    const { uiCopy } = useClientConfig();
    const productOnlyUi = isUnifiedIntakeProductOnlyUi();
    const appTitle = uiCopy.app_title ?? '金盾·陈魁团队 · 客户统一受理';

    // --- CONTEXT-AWARE LOGIC ---
    let rightPanelContent;
    if (location.pathname === '/workbench/code-lookup-agent' || location.pathname === '/workbench/single-home-stress' || location.pathname === '/jobhunter' || location.pathname === '/workbench/jobhunter' || location.pathname === '/vitals' || isUnifiedIntake) {
        rightPanelContent = null;
    } else if (location.pathname === '/workbench') {
        rightPanelContent = <WorkbenchPanel />;
    } else {
        rightPanelContent = <RightPanelTabs />;
    }
    // --- END ---

    return (
        <Layout style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'white', flexShrink: 0, paddingLeft: 24, paddingRight: 24, gap: 16 }}>
                <div style={{ flex: '1 1 0', minWidth: 0, maxWidth: 'calc(100% - 260px)', overflow: 'hidden' }}>
                    {isUnifiedIntake ? (
                        <Space size={16}>
                            <Text style={{ color: 'rgba(255,255,255,0.95)', fontSize: 16, fontWeight: 600 }}>
                                {appTitle}
                            </Text>
                            {!productOnlyUi && (
                            <Link to="/workbench" style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12 }}>
                                返回工作台
                            </Link>
                            )}
                        </Space>
                    ) : (
                        <KpiBar />
                    )}
                </div>
                {!isUnifiedIntake && <ReleaseIdentityBar />}
            </Header>
            <Layout style={{ flex: 1, overflow: 'hidden' }}>
                {!isUnifiedIntake && (
                    <Sider width={200} style={{ overflow: 'auto' }}>
                        <AppSider />
                    </Sider>
                )}
                <Layout style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <LabDevBanner pathname={location.pathname} />
                    <Content
                        style={{
                            flex: 1,
                            padding: 0,
                            margin: 0,
                            background: colorBgContainer,
                            borderRadius: borderRadiusLG,
                            overflow: 'auto',
                            display: 'flex',
                            flexDirection: 'column'
                        }}
                    >
                        <Outlet />
                    </Content>
                </Layout>
                {rightPanelContent !== null && (
                    <Sider width={300} style={{ overflow: 'auto' }}>
                        {rightPanelContent}
                    </Sider>
                )}
            </Layout>
        </Layout>
    );
};
