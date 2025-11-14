// frontend/src/App.tsx
import { ConfigProvider, theme, App as AntdApp } from 'antd';
import { AppLayout } from './components/layout/AppLayout';
import { Routes, Route } from 'react-router-dom';
import { ShowtimePage } from './pages/ShowtimePage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { AgentStudioPage } from './pages/AgentStudioPage';
import { RetrieverLabPage } from './pages/RetrieverLabPage';
import { RankerLabPage } from './pages/RankerLabPage';
import { IndexExplorerPage } from './pages/IndexExplorerPage';
import { SLATunerLabPage } from './pages/SLATunerLabPage';
import CodeLookupPage from './pages/CodeLookupPage';
import MermaidTestPage from './pages/MermaidTestPage';
import EdgesJsonTestPage from './pages/EdgesJsonTestPage';
import FlowGraphTestPage from './pages/FlowGraphTestPage';
import FlowGraphTestScenarios from './pages/FlowGraphTestScenarios';
import SimpleMermaidPage from './pages/SimpleMermaidPage';
import FlowGraphSelfTestPage from './pages/FlowGraphSelfTestPage';
import GraphViewerPage from './pages/GraphViewerPage';
import CodeMapPage from './pages/CodeMapPage';
import { RagLabRunPage } from './pages/RagLabRunPage';
import { RagLabHistoryPage } from './pages/RagLabHistoryPage';
import { RagLabDetailPage } from './pages/RagLabDetailPage';
import StewardDashboard from './pages/StewardDashboard';
import { MetricsHub } from './pages/lab/MetricsHub';

function App() {
    return (
        <ConfigProvider
            theme={{
                algorithm: theme.darkAlgorithm,
            }}
        >
            <AntdApp>
                <Routes>
                    {/* All pages use the same AppLayout */}
                    <Route path="/" element={<AppLayout />}>
                        {/* Default page is Showtime */}
                        <Route index element={<ShowtimePage />} />

                        {/* --- Workbench Routes --- */}
                        {/* The base /workbench route still shows the Leaderboard */}
                        <Route path="workbench" element={<WorkbenchPage />} />

                        {/* Add the new sub-pages */}
                        <Route path="workbench/agent-studio" element={<AgentStudioPage />} />
                        <Route path="workbench/retriever-lab" element={<RetrieverLabPage />} />
                        <Route path="workbench/ranker-lab" element={<RankerLabPage />} />
                        <Route path="workbench/index-explorer" element={<IndexExplorerPage />} />
                        <Route path="workbench/sla-tuner-lab" element={<SLATunerLabPage />} />

                        {/* Code Lookup Agent Route */}
                        <Route path="workbench/code-lookup-agent" element={<CodeLookupPage />} />

                        {/* Mermaid Test Route */}
                        <Route path="mermaid-test" element={<MermaidTestPage />} />

                        {/* Edges JSON Test Route */}
                        <Route path="edges-test" element={<EdgesJsonTestPage />} />

                        {/* FlowGraph Test Route */}
                        <Route path="flowgraph-test" element={<FlowGraphTestPage />} />

                        {/* FlowGraph Test Scenarios Route */}
                        <Route path="flowgraph-scenarios" element={<FlowGraphTestScenarios />} />

                        {/* Simple Mermaid Test Route */}
                        <Route path="simple-mermaid" element={<SimpleMermaidPage />} />

                        {/* FlowGraph Self-Test Route */}
                        <Route path="fg-selftest" element={<FlowGraphSelfTestPage />} />

                        {/* Graph Viewer Route */}
                        <Route path="graph-viewer" element={<GraphViewerPage />} />

                        {/* Code Map Route */}
                        <Route path="codemap" element={<CodeMapPage />} />

                        {/* RAG Lab Routes - V8 Three-Route Architecture */}
                        <Route path="rag-lab/run" element={<RagLabRunPage />} />
                        <Route path="rag-lab/history" element={<RagLabHistoryPage />} />
                        <Route path="rag-lab/history/:jobId" element={<RagLabDetailPage />} />
                        <Route path="rag-lab/steward" element={<StewardDashboard />} />
                        <Route path="rag-lab" element={<RagLabRunPage />} />

                        {/* Metrics Hub Route */}
                        <Route path="lab/metrics" element={<MetricsHub />} />
                    </Route>
                </Routes>
            </AntdApp>
        </ConfigProvider>
    );
}

export default App;
