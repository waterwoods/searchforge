// frontend/src/App.tsx
import { ConfigProvider, theme, App as AntdApp, Spin } from 'antd';
import { Suspense } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { Routes, Route, Navigate } from 'react-router-dom';
import UnifiedIntakePage from './pages/UnifiedIntakePage';
import { DemoPage } from './pages/DemoPage';
import { ClientConfigProvider } from './context/ClientConfigContext';
import { isUnifiedIntakeProductOnlyUi } from './config/productSurface';
import * as Lab from './routes/labPages';

const routeFallback = (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin size="large" />
    </div>
);

function LabRoutes() {
    return (
        <>
            <Route index element={<Lab.ShowtimePage />} />
            <Route path="workbench" element={<Lab.WorkbenchPage />} />
            <Route path="workbench/agent-studio" element={<Lab.AgentStudioPage />} />
            <Route path="workbench/retriever-lab" element={<Lab.RetrieverLabPage />} />
            <Route path="workbench/ranker-lab" element={<Lab.RankerLabPage />} />
            <Route path="workbench/index-explorer" element={<Lab.IndexExplorerPage />} />
            <Route path="workbench/sla-tuner-lab" element={<Lab.SLATunerLabPage />} />
            <Route path="workbench/search-lab" element={<Lab.SearchLabPage />} />
            <Route path="workbench/mortgage-assistant" element={<Lab.MortgageAssistantPage />} />
            <Route path="workbench/single-home-stress" element={<Lab.SingleHomeStressPage />} />
            <Route path="workbench/jobhunter" element={<Lab.JobHunterPage />} />
            <Route path="jobhunter" element={<Lab.JobHunterPage />} />
            <Route path="workbench/code-lookup-agent" element={<Lab.CodeLookupPage />} />
            <Route path="mermaid-test" element={<Lab.MermaidTestPage />} />
            <Route path="edges-test" element={<Lab.EdgesJsonTestPage />} />
            <Route path="flowgraph-test" element={<Lab.FlowGraphTestPage />} />
            <Route path="flowgraph-scenarios" element={<Lab.FlowGraphTestScenarios />} />
            <Route path="simple-mermaid" element={<Lab.SimpleMermaidPage />} />
            <Route path="fg-selftest" element={<Lab.FlowGraphSelfTestPage />} />
            <Route path="graph-viewer" element={<Lab.GraphViewerPage />} />
            <Route path="codemap" element={<Lab.CodeMapPage />} />
            <Route path="rag-lab/run" element={<Lab.RagLabRunPage />} />
            <Route path="rag-lab/history" element={<Lab.RagLabHistoryPage />} />
            <Route path="rag-lab/history/:jobId" element={<Lab.RagLabDetailPage />} />
            <Route path="rag-lab/steward" element={<Lab.StewardDashboard />} />
            <Route path="rag-lab" element={<Lab.RagLabRunPage />} />
            <Route path="lab/metrics" element={<Lab.MetricsHub />} />
            <Route path="vitals" element={<Lab.VitalsDashboardPage />} />
            <Route path="workbench/scenario-logic-center" element={<Lab.ScenarioLogicCenterPage />} />
            <Route path="workbench/add-car-rules" element={<Lab.AddCarRulesPage />} />
        </>
    );
}

function App() {
    const productOnlyUi = isUnifiedIntakeProductOnlyUi();

    return (
        <ConfigProvider
            theme={{
                algorithm: theme.darkAlgorithm,
            }}
        >
            <AntdApp>
                <Suspense fallback={routeFallback}>
                    <Routes>
                        <Route path="/" element={<ClientConfigProvider><AppLayout /></ClientConfigProvider>}>
                            {productOnlyUi ? (
                                <>
                                    <Route index element={<Navigate to="/workbench/unified-intake" replace />} />
                                    <Route path="workbench" element={<Navigate to="/workbench/unified-intake" replace />} />
                                </>
                            ) : (
                                <LabRoutes />
                            )}
                            <Route path="workbench/unified-intake" element={
                                <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
                                    <div style={{ minHeight: '100%', background: '#e8eaed' }}>
                                        <UnifiedIntakePage />
                                    </div>
                                </ConfigProvider>
                            } />
                        </Route>

                        <Route path="/demo" element={
                            <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
                                <div style={{ minHeight: '100vh', background: '#fff', padding: '1rem' }}>
                                    <DemoPage />
                                </div>
                            </ConfigProvider>
                        } />
                    </Routes>
                </Suspense>
            </AntdApp>
        </ConfigProvider>
    );
}

export default App;
