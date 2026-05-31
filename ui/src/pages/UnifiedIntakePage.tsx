/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — customer-facing intake
 * Tab B: My requests — user-facing case list + progress (persisted cases)
 * Tab C: Broker Workbench — office tool for triage, case sheet, follow-up, and drafts
 * Tab D: Scenario replay (simulation)
 *
 * Default tab: broker workbench in product_only trial; customer entry in dev/full UI.
 */
import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Space, Tabs, Tag, Typography } from 'antd';
import {
    CustomerServiceOutlined,
    InboxOutlined,
    PlayCircleOutlined,
    UnorderedListOutlined,
} from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import { ScenarioReplayTab } from '../components/simulation/ScenarioReplayTab';
import { useClientConfig } from '../context/ClientConfigContext';
import { CustomerEntryTab } from '@/features/intake/components/CustomerEntryTab';
import { BrokerWorkbenchTab } from '@/features/intake/components/BrokerWorkbenchTab';
import { MyRequestsTab } from '@/features/intake/components/MyRequestsTab';
import { isUnifiedIntakeProductOnlyUi } from '../config/productSurface';

const { Text } = Typography;

/** Shared chrome width for unified intake (light island inside dark app shell). */
const UNIFIED_INTAKE_SHELL_MAX = 1280;

const VALID_TABS = new Set(['customer', 'my_requests', 'broker', 'simulation']);

function resolveInitialTab(productOnlyUi: boolean, tabParam: string | null): string {
    if (tabParam && VALID_TABS.has(tabParam)) {
        if (tabParam === 'simulation' && productOnlyUi) {
            return 'broker';
        }
        if (tabParam === 'my_requests' && productOnlyUi) {
            return 'broker';
        }
        return tabParam;
    }
    return productOnlyUi ? 'broker' : 'customer';
}

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

/** Trial/product_only intro: cancellation-first wedge per Constitution V1. */
const TRIAL_PILOT_INTRO = {
    value:
        '试用重点：紧急客户消息整理——取消/付款风险、缺材料跟进、加车报价均可粘贴原文。系统整理服务记录、下一步与可编辑草稿；您确认后再发给客户。',
    trust: '不自动对外发送；由办公室确认后再联系客户。',
    does: '粘贴微信/通知原文 → 整理 urgency、下一步、草稿；演示队列可快速体验取消风险案例',
    doesNot: '不自动同步微信；不替代承保系统；不是完整 CRM',
    demoPath: '建议路径：本页粘贴客户消息，或点「加载演示队列」查看取消风险案例。',
};

export default function UnifiedIntakePage() {
    const { uiCopy, clientId } = useClientConfig();
    const [searchParams] = useSearchParams();
    const productOnlyUi = isUnifiedIntakeProductOnlyUi();
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

    const tabFromUrl = searchParams.get('tab');
    const [activeTab, setActiveTab] = useState<string>(() => resolveInitialTab(productOnlyUi, tabFromUrl));
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [pilotIntroCollapsed, setPilotIntroCollapsed] = useState(productOnlyUi);
    const [headerAvatarBroken, setHeaderAvatarBroken] = useState(false);
    const showSimulationTab = !productOnlyUi;
    const showMyRequestsTab = !productOnlyUi;
    const pilotIntro = productOnlyUi ? TRIAL_PILOT_INTRO : PILOT_INTRO;

    useEffect(() => {
        const next = resolveInitialTab(productOnlyUi, searchParams.get('tab'));
        setActiveTab((current) => (current === next ? current : next));
    }, [productOnlyUi, searchParams]);

    useEffect(() => {
        if (!showSimulationTab && activeTab === 'simulation') {
            setActiveTab('broker');
        }
        if (!showMyRequestsTab && activeTab === 'my_requests') {
            setActiveTab('broker');
        }
    }, [showSimulationTab, showMyRequestsTab, activeTab]);

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

    const tabItems = useMemo(() => {
        const items = [
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
                        onOpenScenarioSimulation={
                            showSimulationTab ? () => setActiveTab('simulation') : undefined
                        }
                        onOpenMyRequests={() => setActiveTab('my_requests')}
                    />
                ),
            },
            ...(showMyRequestsTab
                ? [
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
                              <MyRequestsTab onContinueInCustomerPortal={() => setActiveTab('customer')} />
                          ),
                      },
                  ]
                : []),
            {
                key: 'broker',
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
            ...(showSimulationTab
                ? [
                      {
                          key: 'simulation',
                          label: (
                              <span>
                                  <PlayCircleOutlined /> {portalTabSimulation}
                                  <Text
                                      type="secondary"
                                      style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}
                                  >
                                      — {portalTabSimulationSuffix}
                                  </Text>
                              </span>
                          ),
                          children: <ScenarioReplayTab />,
                      },
                  ]
                : []),
        ];
        return items;
    }, [
        clientId,
        brokerInitialCaseId,
        officeWorkbench,
        portalTabCustomer,
        portalTabCustomerSuffix,
        portalTabMyRequests,
        portalTabMyRequestsSuffix,
        portalTabOfficeSuffix,
        portalTabSimulation,
        portalTabSimulationSuffix,
        showMyRequestsTab,
        showSimulationTab,
    ]);

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
                        <Text strong>{pilotIntro.value}</Text>
                        <Space wrap size={[4, 4]}>
                            <Tag color="green">{pilotIntro.trust}</Tag>
                            <Tag color="blue">做：{pilotIntro.does}</Tag>
                            <Tag color="default">不做：{pilotIntro.doesNot}</Tag>
                        </Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            {pilotIntro.demoPath}
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
                items={tabItems}
            />
            </div>
        </div>
    );
}
