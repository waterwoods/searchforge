/**
 * Lazy-loaded lab / platform pages — not shipped in product-only UI builds.
 * Keeps SearchForge R&D surfaces out of the paid-pilot bundle when tree-shaken.
 */
import { lazy } from 'react';

export const ShowtimePage = lazy(() =>
    import('../pages/ShowtimePage').then((m) => ({ default: m.ShowtimePage })),
);
export const WorkbenchPage = lazy(() =>
    import('../pages/WorkbenchPage').then((m) => ({ default: m.WorkbenchPage })),
);
export const AgentStudioPage = lazy(() =>
    import('../pages/AgentStudioPage').then((m) => ({ default: m.AgentStudioPage })),
);
export const RetrieverLabPage = lazy(() =>
    import('../pages/RetrieverLabPage').then((m) => ({ default: m.RetrieverLabPage })),
);
export const RankerLabPage = lazy(() =>
    import('../pages/RankerLabPage').then((m) => ({ default: m.RankerLabPage })),
);
export const IndexExplorerPage = lazy(() =>
    import('../pages/IndexExplorerPage').then((m) => ({ default: m.IndexExplorerPage })),
);
export const SLATunerLabPage = lazy(() =>
    import('../pages/SLATunerLabPage').then((m) => ({ default: m.SLATunerLabPage })),
);
export const SearchLabPage = lazy(() =>
    import('../pages/SearchLabPage').then((m) => ({ default: m.SearchLabPage })),
);
export const MortgageAssistantPage = lazy(() =>
    import('../pages/MortgageAssistantPage').then((m) => ({ default: m.MortgageAssistantPage })),
);
export const SingleHomeStressPage = lazy(() =>
    import('../pages/SingleHomeStressPage').then((m) => ({ default: m.SingleHomeStressPage })),
);
export const JobHunterPage = lazy(() => import('../pages/JobHunterPage'));
export const CodeLookupPage = lazy(() => import('../pages/CodeLookupPage'));
export const MermaidTestPage = lazy(() => import('../pages/MermaidTestPage'));
export const EdgesJsonTestPage = lazy(() => import('../pages/EdgesJsonTestPage'));
export const FlowGraphTestPage = lazy(() => import('../pages/FlowGraphTestPage'));
export const FlowGraphTestScenarios = lazy(() => import('../pages/FlowGraphTestScenarios'));
export const SimpleMermaidPage = lazy(() => import('../pages/SimpleMermaidPage'));
export const FlowGraphSelfTestPage = lazy(() => import('../pages/FlowGraphSelfTestPage'));
export const GraphViewerPage = lazy(() => import('../pages/GraphViewerPage'));
export const CodeMapPage = lazy(() => import('../pages/CodeMapPage'));
export const RagLabRunPage = lazy(() =>
    import('../pages/RagLabRunPage').then((m) => ({ default: m.RagLabRunPage })),
);
export const RagLabHistoryPage = lazy(() =>
    import('../pages/RagLabHistoryPage').then((m) => ({ default: m.RagLabHistoryPage })),
);
export const RagLabDetailPage = lazy(() =>
    import('../pages/RagLabDetailPage').then((m) => ({ default: m.RagLabDetailPage })),
);
export const StewardDashboard = lazy(() => import('../pages/StewardDashboard'));
export const MetricsHub = lazy(() =>
    import('../pages/lab/MetricsHub').then((m) => ({ default: m.MetricsHub })),
);
export const VitalsDashboardPage = lazy(() => import('../pages/VitalsDashboardPage'));
export const ScenarioLogicCenterPage = lazy(() => import('../pages/ScenarioLogicCenterPage'));
export const AddCarRulesPage = lazy(() => import('../pages/AddCarRulesPage'));

/** Path prefixes that are internal/lab-only (founder dev). */
export const LAB_PATH_PREFIXES = [
    '/workbench/agent-studio',
    '/workbench/code-lookup-agent',
    '/workbench/retriever-lab',
    '/workbench/ranker-lab',
    '/workbench/index-explorer',
    '/workbench/sla-tuner-lab',
    '/workbench/search-lab',
    '/workbench/mortgage-assistant',
    '/workbench/single-home-stress',
    '/workbench/jobhunter',
    '/workbench/scenario-logic-center',
    '/workbench/add-car-rules',
    '/jobhunter',
    '/rag-lab',
    '/lab/',
    '/vitals',
    '/codemap',
    '/mermaid-test',
    '/edges-test',
    '/flowgraph-test',
    '/flowgraph-scenarios',
    '/simple-mermaid',
    '/fg-selftest',
    '/graph-viewer',
];

export function isLabPath(pathname: string): boolean {
    if (pathname === '/' || pathname === '/workbench') return true;
    return LAB_PATH_PREFIXES.some(
        (p) => pathname === p || pathname.startsWith(`${p}/`) || pathname.startsWith(p),
    );
}
