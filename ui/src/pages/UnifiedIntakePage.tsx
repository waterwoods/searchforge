/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — customer-facing intake
 * Tab B: My requests — user-facing case list + progress (persisted cases)
 * Tab C: Broker Workbench — office tool for triage, case sheet, follow-up, and drafts
 * Tab D: Scenario replay (simulation)
 *
 * Customer Entry is the default visible tab.
 */
import { useEffect, useState } from 'react';
import { Alert, Button, Space, Tabs, Tag, Typography } from 'antd';
import {
    CustomerServiceOutlined,
    InboxOutlined,
    PlayCircleOutlined,
    UnorderedListOutlined,
} from '@ant-design/icons';
import { ScenarioReplayTab } from '../components/simulation/ScenarioReplayTab';
import { UserCaseListProgressPanel } from '../components/intake/UserCaseListProgressPanel';
import { useClientConfig } from '../context/ClientConfigContext';
import { CustomerEntryTab } from '@/features/intake/components/CustomerEntryTab';
import { BrokerWorkbenchTab } from '@/features/intake/components/BrokerWorkbenchTab';

const { Text } = Typography;

/** Shared chrome width for unified intake (light island inside dark app shell). */
const UNIFIED_INTAKE_SHELL_MAX = 1280;

// =============================================================================
// MAIN PAGE
// =============================================================================

/** Pilot-ready intro: Add-Car-first scope, trust boundary. Collapsible after first read. */
const PILOT_INTRO = {
    value:
        'Add-Car-first 试点：加车报价报送是当前最成熟的主路径——客户报送后系统整理要点、缺口与业务记录，办公室核对后再出价与对外联系。账单、理赔、保单变更等也可报送，但整理深度因场景而异；不以「全能助手」为承诺。',
    trust: '不自动对外发送；由办公室确认后再联系客户。',
    does: '加车：分步收集、进度提示、交办公室、同记录追加；其他意图：基础整理与草稿（成熟度因场景而异）',
    doesNot: '不直连邮箱/微信；不替代承保系统；不是完整 CRM',
    demoPath:
        '演示建议：客户报送 → 点「办理加车报价」或填写「加车报价 · 结构化报送」→ 办公室工作台查看同一服务记录。',
};

export default function UnifiedIntakePage() {
    const { uiCopy, clientId } = useClientConfig();
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const portalBrandTagline = uiCopy.portal_brand_tagline ?? '车险报送入口 · 加车报价为当前旗舰流程';
    const portalTabCustomer = uiCopy.portal_tab_customer_label ?? '客户报送';
    const portalTabCustomerSuffix = uiCopy.portal_tab_customer_suffix ?? '报送入口（加车优先）';
    const portalTabOfficeSuffix = uiCopy.portal_tab_office_suffix ?? '加车旗舰路径 · 与客户报送同一服务记录';
    const portalTabSimulation = uiCopy.portal_tab_simulation_label ?? '场景仿真';
    const portalTabSimulationSuffix = uiCopy.portal_tab_simulation_suffix ?? '加车脚本回放 · 状态同步';
    const portalTabMyRequests = uiCopy.portal_tab_my_requests_label ?? '我的办理';
    const portalTabMyRequestsSuffix =
        uiCopy.portal_tab_my_requests_suffix ?? '进行中的请求与待补充项';

    const [activeTab, setActiveTab] = useState<string>('customer');
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [pilotIntroCollapsed, setPilotIntroCollapsed] = useState(false);
    const [headerAvatarBroken, setHeaderAvatarBroken] = useState(false);

    const portalHeroTitle = uiCopy.portal_hero_title ?? '加车报价 · 客户统一报送';
    const officeWorkbenchDocumentTitle = uiCopy.office_workbench_document_title ?? '加车报价试点 · 办公室工作台';
    const simulationTabTitle =
        (uiCopy.portal_tab_simulation_label ?? '场景仿真') + ' · ' + (uiCopy.portal_brand_tagline ?? '车险报送入口');
    const myRequestsDocumentTitle =
        (uiCopy.portal_tab_my_requests_label ?? '我的办理') + ' · ' + (uiCopy.portal_brand_tagline ?? '车险报送入口');

    useEffect(() => {
        if (activeTab === 'customer') {
            document.title = portalHeroTitle;
        } else if (activeTab === 'my_requests') {
            document.title = myRequestsDocumentTitle;
        } else if (activeTab === 'broker') {
            document.title = officeWorkbenchDocumentTitle;
        } else {
            document.title = simulationTabTitle;
        }
    }, [activeTab, portalHeroTitle, myRequestsDocumentTitle, officeWorkbenchDocumentTitle, simulationTabTitle]);

    const handleSwitchToBroker = (caseId?: string) => {
        setBrokerInitialCaseId(caseId);
        setActiveTab('broker');
    };

    return (
        <div
            style={{
                minHeight: '100%',
                background: '#e8eaed',
                borderLeft: '1px solid #dfe3e8',
                borderRight: '1px solid #dfe3e8',
            }}
        >
            <div
                style={{
                    maxWidth: UNIFIED_INTAKE_SHELL_MAX,
                    margin: '0 auto',
                    padding: '10px 18px 28px',
                }}
            >
            <div
                style={{
                    background: '#fff',
                    borderRadius: 10,
                    border: '1px solid #e8e8e8',
                    padding: '14px 18px 16px',
                    marginBottom: 12,
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div
                        style={{
                            width: 44,
                            height: 44,
                            borderRadius: '50%',
                            overflow: 'hidden',
                            border: '1px solid #d9d9d9',
                            background: '#f5f5f5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}
                    >
                        {!headerAvatarBroken ? (
                            <img
                                src="/chen-kui-avatar.jpg"
                                alt="陈魁团队头像"
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={() => setHeaderAvatarBroken(true)}
                            />
                        ) : (
                            <Text style={{ color: '#8c8c8c', fontSize: 14, fontWeight: 600 }}>陈魁</Text>
                        )}
                    </div>
                    <div style={{ minWidth: 0 }}>
                        <Text style={{ display: 'block', color: '#1f1f1f', fontSize: 18, lineHeight: 1.35, fontWeight: 600 }}>
                            金盾保险 · 陈魁团队
                        </Text>
                        <Text style={{ display: 'block', color: '#595959', fontSize: 14, lineHeight: 1.5, marginTop: 2 }}>
                            {portalBrandTagline}
                        </Text>
                    </div>
                </div>
            </div>
            <Alert
                type="info"
                showIcon
                closable
                onClose={() => setPilotIntroCollapsed(true)}
                style={{
                    marginBottom: 12,
                    display: pilotIntroCollapsed ? 'none' : 'block',
                }}
                message={
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text strong>{PILOT_INTRO.value}</Text>
                        <Space wrap size={[4, 4]}>
                            <Tag color="green">{PILOT_INTRO.trust}</Tag>
                            <Tag color="blue">做：{PILOT_INTRO.does}</Tag>
                            <Tag color="default">不做：{PILOT_INTRO.doesNot}</Tag>
                        </Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            {PILOT_INTRO.demoPath}
                        </Text>
                    </Space>
                }
            />
            {pilotIntroCollapsed && (
                <div style={{ marginBottom: 6, textAlign: 'right' }}>
                    <Button type="link" size="small" onClick={() => setPilotIntroCollapsed(false)} style={{ padding: 0, fontSize: 12 }}>
                        显示产品说明
                    </Button>
                </div>
            )}
            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                size="large"
                tabBarStyle={{
                    marginBottom: 12,
                    paddingLeft: 0,
                    borderBottom: '1px solid #e8e8e8',
                }}
                items={[
                    {
                        key: 'customer',
                        label: (
                            <span>
                                <CustomerServiceOutlined /> {portalTabCustomer}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabCustomerSuffix}
                                </Text>
                            </span>
                        ),
                        children: (
                            <CustomerEntryTab
                                onSwitchToBroker={handleSwitchToBroker}
                                onOpenScenarioSimulation={() => setActiveTab('simulation')}
                                onOpenMyRequests={() => setActiveTab('my_requests')}
                            />
                        ),
                    },
                    {
                        key: 'my_requests',
                        forceRender: true,
                        label: (
                            <span>
                                <UnorderedListOutlined /> {portalTabMyRequests}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabMyRequestsSuffix}
                                </Text>
                            </span>
                        ),
                        children: (
                            <UserCaseListProgressPanel onContinueInCustomerPortal={() => setActiveTab('customer')} />
                        ),
                    },
                    {
                        key: 'broker',
                        /** Prefetch queue on page load: inactive tab bodies start unmounted (rc-tabs + rc-motion); without this, GET /api/inbox/cases only runs after first opening Office tab, and summary tiles briefly show 0. */
                        forceRender: true,
                        label: (
                            <span>
                                <InboxOutlined /> {officeWorkbench}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabOfficeSuffix}
                                </Text>
                            </span>
                        ),
                        children: <BrokerWorkbenchTab initialCaseId={brokerInitialCaseId} clientId={clientId} />,
                    },
                    {
                        key: 'simulation',
                        label: (
                            <span>
                                <PlayCircleOutlined /> {portalTabSimulation}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabSimulationSuffix}
                                </Text>
                            </span>
                        ),
                        children: <ScenarioReplayTab />,
                    },
                ]}
            />
            </div>
        </div>
    );
}
