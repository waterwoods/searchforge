/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — customer-facing intake (default in dev / supervised demo)
 * Tab B: My requests — secondary in supervised demo; top-level tab in full dev only
 * Tab C: Broker Workbench — office tool for triage, case sheet, follow-up, and drafts
 * Tab D: Scenario replay (simulation)
 *
 * Default tab: broker in product_only trial; customer in dev / supervised demo preview.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { Drawer, Tabs, Typography } from 'antd';
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
import { isUnifiedIntakeProductOnlyUi, isUnifiedIntakeSupervisedDemoUi } from '../config/productSurface';

const { Text } = Typography;

/** Shared chrome width for unified intake (light island inside dark app shell). */
const UNIFIED_INTAKE_SHELL_MAX = 1280;

const VALID_TABS = new Set(['customer', 'my_requests', 'broker', 'simulation']);

function resolveInitialTab(productOnlyUi: boolean, supervisedDemoUi: boolean, tabParam: string | null): string {
    const hideCustomerTabs = productOnlyUi && !supervisedDemoUi;
    if (tabParam && VALID_TABS.has(tabParam)) {
        if (hideCustomerTabs && (tabParam === 'simulation' || tabParam === 'my_requests' || tabParam === 'customer')) {
            return 'broker';
        }
        // Supervised demo: my_requests is a secondary action inside 客户报送, not a primary tab.
        if (supervisedDemoUi && tabParam === 'my_requests') {
            return 'customer';
        }
        return tabParam;
    }
    return productOnlyUi && !supervisedDemoUi ? 'broker' : 'customer';
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
    const supervisedDemoUi = isUnifiedIntakeSupervisedDemoUi();
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const portalBrandTagline = supervisedDemoUi
        ? (uiCopy.portal_brand_tagline ?? '车险报送入口 · 加车报价为当前旗舰流程')
        : productOnlyUi
          ? (uiCopy.portal_brand_tagline_trial ?? '粘贴客户消息 · 整理草稿 · 您确认后发送')
          : (uiCopy.portal_brand_tagline ?? '车险报送入口 · 加车报价为当前旗舰流程');
    const portalTrustLineFallback = uiCopy.portal_trust_line ?? '我们不会自动回复；办公室确认后再联系您';
    const portalTabCustomer = uiCopy.portal_tab_customer_label ?? '客户报送';
    const portalTabCustomerSuffix = uiCopy.portal_tab_customer_suffix ?? '报送入口（加车优先）';
    const portalTabOfficeSuffix = uiCopy.portal_tab_office_suffix ?? '加车旗舰路径 · 与客户报送同一服务记录';
    const portalTabSimulation = uiCopy.portal_tab_simulation_label ?? '场景仿真';
    const portalTabSimulationSuffix = uiCopy.portal_tab_simulation_suffix ?? '加车脚本回放 · 状态同步';
    const portalTabMyRequests = uiCopy.portal_tab_my_requests_label ?? '我的办理';
    const portalTabMyRequestsSuffix =
        uiCopy.portal_tab_my_requests_suffix ?? '进行中的请求与待补充项';

    const tabFromUrl = searchParams.get('tab');
    const [activeTab, setActiveTab] = useState<string>(() => resolveInitialTab(productOnlyUi, supervisedDemoUi, tabFromUrl));
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [customerContinueCaseId, setCustomerContinueCaseId] = useState<string | null>(null);
    const [headerAvatarBroken, setHeaderAvatarBroken] = useState(false);
    const [myRequestsDrawerOpen, setMyRequestsDrawerOpen] = useState(false);
    const showCustomerTab = !productOnlyUi || supervisedDemoUi;
    const showSimulationTab = !productOnlyUi || supervisedDemoUi;
    const showMyRequestsTab = !productOnlyUi && !supervisedDemoUi;
    const pilotIntro = supervisedDemoUi ? PILOT_INTRO : productOnlyUi ? TRIAL_PILOT_INTRO : PILOT_INTRO;
    const singleTabMode = productOnlyUi && !showCustomerTab && !showMyRequestsTab && !showSimulationTab;

    useEffect(() => {
        const tabParam = searchParams.get('tab');
        const next = resolveInitialTab(productOnlyUi, supervisedDemoUi, tabParam);
        setActiveTab((current) => (current === next ? current : next));
        if (supervisedDemoUi && tabParam === 'my_requests') {
            setMyRequestsDrawerOpen(true);
        }
    }, [productOnlyUi, supervisedDemoUi, searchParams]);

    useEffect(() => {
        if (!showCustomerTab && activeTab === 'customer') {
            setActiveTab('broker');
        }
        if (!showSimulationTab && activeTab === 'simulation') {
            setActiveTab('broker');
        }
        if (!showMyRequestsTab && activeTab === 'my_requests') {
            setActiveTab('broker');
        }
    }, [showCustomerTab, showSimulationTab, showMyRequestsTab, activeTab]);

    const portalHeroTitle = uiCopy.portal_hero_title ?? '加车报价 · 客户统一报送';
    const officeWorkbenchDocumentTitle = productOnlyUi
        ? (uiCopy.office_workbench_document_title_trial ?? '办公室工作台 · 客户消息整理')
        : (uiCopy.office_workbench_document_title ?? '加车报价试点 · 办公室工作台');
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

    const handleOpenMyRequests = () => {
        if (supervisedDemoUi) {
            setMyRequestsDrawerOpen(true);
            return;
        }
        setActiveTab('my_requests');
    };

    const handleContinueInCustomerPortal = (caseId: string) => {
        setCustomerContinueCaseId(caseId);
        setMyRequestsDrawerOpen(false);
        setActiveTab('customer');
    };

    const renderTabLabel = (icon: ReactNode, primary: string, suffix?: string, showSuffix = false) => (
        <span>
            {icon} {primary}
            {showSuffix && suffix ? (
                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                    — {suffix}
                </Text>
            ) : null}
        </span>
    );

    const tabItems = useMemo(() => {
        const items = [
            ...(showCustomerTab
                ? [
                      {
                          key: 'customer',
                          label: renderTabLabel(
                              <CustomerServiceOutlined />,
                              portalTabCustomer,
                              portalTabCustomerSuffix,
                              false,
                          ),
                          children: (
                              <CustomerEntryTab
                                  onSwitchToBroker={handleSwitchToBroker}
                                  onOpenScenarioSimulation={
                                      showSimulationTab ? () => setActiveTab('simulation') : undefined
                                  }
                                  onOpenMyRequests={showCustomerTab ? handleOpenMyRequests : undefined}
                                  continueCaseId={customerContinueCaseId}
                                  onContinueCaseHandled={() => setCustomerContinueCaseId(null)}
                              />
                          ),
                      },
                  ]
                : []),
            ...(showMyRequestsTab
                ? [
                      {
                          key: 'my_requests',
                          forceRender: true,
                          label: renderTabLabel(
                              <UnorderedListOutlined />,
                              portalTabMyRequests,
                              portalTabMyRequestsSuffix,
                              false,
                          ),
                          children: (
                              <MyRequestsTab onContinueInCustomerPortal={handleContinueInCustomerPortal} />
                          ),
                      },
                  ]
                : []),
            {
                key: 'broker',
                forceRender: true,
                label: renderTabLabel(<InboxOutlined />, officeWorkbench, portalTabOfficeSuffix, !productOnlyUi),
                children: <BrokerWorkbenchTab initialCaseId={brokerInitialCaseId} clientId={clientId} />,
            },
            ...(showSimulationTab
                ? [
                      {
                          key: 'simulation',
                          label: renderTabLabel(
                              <PlayCircleOutlined />,
                              portalTabSimulation,
                              portalTabSimulationSuffix,
                              false,
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
        customerContinueCaseId,
        officeWorkbench,
        portalTabCustomer,
        portalTabCustomerSuffix,
        portalTabMyRequests,
        portalTabMyRequestsSuffix,
        portalTabOfficeSuffix,
        portalTabSimulation,
        portalTabSimulationSuffix,
        showCustomerTab,
        showMyRequestsTab,
        showSimulationTab,
        productOnlyUi,
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
                            {activeTab === 'customer' || activeTab === 'my_requests'
                                ? portalTrustLineFallback
                                : portalBrandTagline}
                        </Text>
                    </div>
                </div>
            </div>
            {(productOnlyUi || supervisedDemoUi) && (
                <Text type="secondary" style={{ display: 'block', marginBottom: 12, fontSize: 13 }}>
                    {pilotIntro.trust}
                </Text>
            )}
            {singleTabMode ? (
                <BrokerWorkbenchTab initialCaseId={brokerInitialCaseId} clientId={clientId} />
            ) : (
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
            )}
            {supervisedDemoUi ? (
                <Drawer
                    title={portalTabMyRequests}
                    placement="right"
                    width={Math.min(520, typeof window !== 'undefined' ? window.innerWidth - 24 : 520)}
                    open={myRequestsDrawerOpen}
                    onClose={() => setMyRequestsDrawerOpen(false)}
                    destroyOnClose={false}
                >
                    <MyRequestsTab onContinueInCustomerPortal={handleContinueInCustomerPortal} />
                </Drawer>
            ) : null}
            </div>
        </div>
    );
}
