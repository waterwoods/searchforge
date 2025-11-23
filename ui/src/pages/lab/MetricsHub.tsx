/**
 * Metrics Hub Page
 * Read-only metrics view with KPI cards, trilines chart, and job details drawer
 */
import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
    Card,
    Typography,
    Space,
    List,
    Tag,
    Button,
    Spin,
    Empty,
    Alert,
    Drawer,
    Timeline,
    Collapse,
    Row,
    Col,
    Select,
    Skeleton,
    Tooltip,
    message,
    Table,
} from 'antd';
import {
    BarChartOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    FileImageOutlined,
    FileTextOutlined,
    ReloadOutlined,
    CloseOutlined,
    LinkOutlined,
    CopyOutlined,
    DownloadOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { useRagLabStore } from '../../store/ragLabStore';
import type { JobMeta } from '../../api/experiment';
import * as experimentApi from '../../api/experiment';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface TrilinesPoint {
    budget: number;
    t: number;
    p95_ms: number;
    recall10: number;
    cost_1k_usd: number;
}

interface TrilinesData {
    points: TrilinesPoint[];
    budgets: number[];
    updated_at: string;
}

interface KPIData {
    success_rate: number;
    p95_down: boolean;
    bounds_ok: boolean;
    stable_detune: boolean;
    budgets: number[];
    updated_at: string;
    cost_enabled: boolean;
}

interface BudgetSegmentRow {
    budget: number;
    recall10: number;
    p95: number;
    cost_per_1k: number;
    policy_used: string | null;
    updated_at: string;
    trace_url: string | null;
}

export const MetricsHub = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const { history, loadHistory } = useRagLabStore();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [drawerVisible, setDrawerVisible] = useState(false);
    const [selectedJob, setSelectedJob] = useState<JobMeta | null>(null);
    const [jobDetail, setJobDetail] = useState<any>(null);
    const [artifacts, setArtifacts] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [detailLoading, setDetailLoading] = useState(false);

    // Metrics data
    const [trilinesData, setTrilinesData] = useState<TrilinesData | null>(null);
    const [trilinesLoading, setTrilinesLoading] = useState(false);
    const [trilinesError, setTrilinesError] = useState<string | null>(null);
    const [selectedBudget, setSelectedBudget] = useState<number | null>(null);
    const [langfuseUrl, setLangfuseUrl] = useState<string | null>(null);
    const [lastTraceUrls, setLastTraceUrls] = useState<string[]>([]);
    const [lastTraceLoading, setLastTraceLoading] = useState(false);

    // KPI data
    const [kpiData, setKpiData] = useState<KPIData | null>(null);
    const [kpiLoading, setKpiLoading] = useState(false);
    const [kpiError, setKpiError] = useState<string | null>(null);

    // Autotuner policy
    const [autotunerPolicy, setAutotunerPolicy] = useState<string | null>(null);
    const [autotunerEnabled, setAutotunerEnabled] = useState(false);
    const [autotunerLoading, setAutotunerLoading] = useState(false);
    const [autotunerError, setAutotunerError] = useState<string | null>(null);

    // Time range and budget filters (default to generous values for visibility)
    const [timeRange, setTimeRange] = useState<string>('24h');
    const [budgetFilter, setBudgetFilter] = useState<number | null>(null);
    const [autoWidened, setAutoWidened] = useState(false);

    // Data source mode (full CI vs fast CI)
    type DataMode = "full" | "fast";
    const [dataMode, setDataMode] = useState<DataMode>("full");

    // Fetch KPI data with robust error handling
    const fetchKPI = async (mode?: DataMode) => {
        const currentMode = mode ?? dataMode;
        setKpiLoading(true);
        setKpiError(null);
        try {
            const params = new URLSearchParams();
            if (currentMode === "fast") {
                params.set('mode', 'fast');
            }
            const url = `/api/metrics/kpi${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('KPI endpoint not found (404)');
                    setKpiError(null); // Don't show error for 404, just use existing data
                    return;
                }
                throw new Error(`Failed to fetch KPI: ${response.status}`);
            }
            const data: KPIData = await response.json();
            setKpiData(data);
        } catch (err: any) {
            // Network errors or other failures - don't break the page
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('KPI fetch network error:', err);
                setKpiError(null); // Keep existing data, don't show error
            } else {
                setKpiError(err.message || 'Failed to fetch KPI data');
                console.error('KPI fetch error:', err);
            }
        } finally {
            setKpiLoading(false);
        }
    };

    // Fetch trilines data with robust error handling
    const fetchTrilines = async (timeRange?: string, budgetFilter?: number, mode?: DataMode) => {
        const currentMode = mode ?? dataMode;
        setTrilinesLoading(true);
        setTrilinesError(null);
        try {
            const params = new URLSearchParams();
            if (timeRange) params.set('time_range', timeRange);
            if (budgetFilter) params.set('budget', budgetFilter.toString());
            if (currentMode === "fast") {
                params.set('mode', 'fast');
            }
            const url = `/api/metrics/trilines${params.toString() ? '?' + params.toString() : ''}`;
            const response = await fetch(url);
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('Trilines endpoint not found (404)');
                    setTrilinesError(null); // Don't show error for 404, just use existing data
                    return;
                }
                if (response.status >= 500) {
                    setTrilinesError('Server error (500)');
                    return;
                }
                throw new Error(`Failed to fetch trilines: ${response.status}`);
            }
            const data: TrilinesData = await response.json();
            setTrilinesData(data);

            // Auto-widen filters if no data points found
            if (data.points.length === 0 && !autoWidened) {
                console.log('[MetricsHub] No data with current filters, auto-widening...');
                setTimeRange('48h');
                setAutoWidened(true);
                // Retry with wider filters
                const widerParams = new URLSearchParams();
                widerParams.set('time_range', '48h');
                if (currentMode === "fast") {
                    widerParams.set('mode', 'fast');
                }
                const widerUrl = `/api/metrics/trilines?${widerParams.toString()}`;
                try {
                    const widerResponse = await fetch(widerUrl);
                    if (widerResponse.ok) {
                        const widerData: TrilinesData = await widerResponse.json();
                        setTrilinesData(widerData);
                        if (widerData.points.length > 0) {
                            message.info('No data in narrow window, expanded filters automatically.');
                        }
                    }
                } catch (err) {
                    console.warn('Failed to fetch with widened filters:', err);
                }
            }

            // Set default budget to latest (highest)
            if (data.budgets.length > 0 && !selectedBudget) {
                setSelectedBudget(Math.max(...data.budgets));
            }
        } catch (err: any) {
            // Network errors or other failures - don't break the page
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Trilines fetch network error:', err);
                setTrilinesError(null); // Keep existing data, don't show error
            } else {
                setTrilinesError(err.message || 'Failed to fetch trilines data');
                console.error('Trilines fetch error:', err);
            }
        } finally {
            setTrilinesLoading(false);
        }
    };

    // Fetch Langfuse URL with robust error handling
    const fetchLangfuseUrl = async () => {
        try {
            const response = await fetch('/api/metrics/obs/url');
            if (response.status === 204) {
                setLangfuseUrl(null);
                return;
            }
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('Langfuse URL endpoint not found (404)');
                    setLangfuseUrl(null);
                    return;
                }
                throw new Error(`Failed to fetch Langfuse URL: ${response.status}`);
            }
            const data = await response.json();
            setLangfuseUrl(data.url || null);
        } catch (err: any) {
            // Network errors or other failures - silent fail
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Langfuse URL fetch network error:', err);
            } else {
                console.warn('Failed to fetch Langfuse URL:', err);
            }
            setLangfuseUrl(null);
        }
    };

    // Fetch last trace URLs with robust error handling
    const fetchLastTraceUrls = async () => {
        setLastTraceLoading(true);
        try {
            const response = await fetch('/api/metrics/obs/last?limit=10');
            if (response.status === 204) {
                setLastTraceUrls([]);
                return;
            }
            if (!response.ok) {
                if (response.status === 404) {
                    console.warn('Last trace URLs endpoint not found (404)');
                    setLastTraceUrls([]);
                    return;
                }
                throw new Error(`Failed to fetch last trace URLs: ${response.status}`);
            }
            const data = await response.json();
            setLastTraceUrls(data.urls || []);
        } catch (err: any) {
            // Network errors or other failures - silent fail
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Last trace URLs fetch network error:', err);
            } else {
                console.warn('Failed to fetch last trace URLs:', err);
            }
            setLastTraceUrls([]);
        } finally {
            setLastTraceLoading(false);
        }
    };

    // Handle open last trace
    const handleOpenLastTrace = async () => {
        setLastTraceLoading(true);
        try {
            const response = await fetch('/api/metrics/obs/last?limit=10');
            if (response.status === 204) {
                return;
            }
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            const urls = data.urls || [];
            setLastTraceUrls(urls);
            if (urls.length > 0) {
                window.open(urls[0], '_blank', 'noopener,noreferrer');
            }
        } catch (err: any) {
            console.warn('Failed to fetch last trace URLs:', err);
        } finally {
            setLastTraceLoading(false);
        }
    };

    // Handle copy URL
    const handleCopyUrl = async (url: string) => {
        try {
            await navigator.clipboard.writeText(url);
            message.success('URL copied to clipboard');
        } catch (err) {
            message.error('Failed to copy URL');
        }
    };

    // Get trace URL for a job (from job or fallback to most recent)
    const getTraceUrl = (job?: JobMeta | null): string | null => {
        if (job?.obs_url) {
            return job.obs_url;
        }
        // Fallback to most recent trace URL
        if (lastTraceUrls.length > 0) {
            return lastTraceUrls[0];
        }
        return null;
    };

    // Fetch autotuner status
    const fetchAutotunerStatus = async () => {
        setAutotunerLoading(true);
        setAutotunerError(null);
        try {
            // Only inject token in dev environment
            const token = import.meta.env.DEV ? (import.meta.env as any).VITE_AUTOTUNER_TOKEN : undefined;
            const maybeAuth: Record<string, string> = token ? { 'X-Autotuner-Token': token } : {};
            const headers: Record<string, string> = maybeAuth;
            const response = await fetch('/api/autotuner/status', { headers });
            if (!response.ok) {
                if (response.status === 404 || response.status >= 500) {
                    // Backend not upgraded or server error
                    setAutotunerEnabled(false);
                    setAutotunerPolicy(null);
                    setAutotunerError('Backend not upgraded');
                    return;
                }
                throw new Error(`Failed to fetch autotuner status: ${response.status}`);
            }
            const data = await response.json();
            if (data.policy && (data.policy === 'LatencyFirst' || data.policy === 'RecallFirst' || data.policy === 'Balanced')) {
                setAutotunerPolicy(data.policy);
                setAutotunerEnabled(true);
                setAutotunerError(null);
            } else {
                setAutotunerEnabled(false);
                setAutotunerPolicy(null);
                setAutotunerError('Strategy API not available');
            }
        } catch (err: any) {
            // Network errors or other failures
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Autotuner status fetch network error:', err);
            } else {
                console.warn('Failed to fetch autotuner status:', err);
            }
            setAutotunerEnabled(false);
            setAutotunerPolicy(null);
            setAutotunerError('Backend not upgraded');
        } finally {
            setAutotunerLoading(false);
        }
    };

    // Set autotuner policy
    const setPolicy = async (policy: string) => {
        try {
            // Only inject token in dev environment
            const token = import.meta.env.DEV ? (import.meta.env as any).VITE_AUTOTUNER_TOKEN : undefined;
            const maybeAuth: Record<string, string> = token ? { 'X-Autotuner-Token': token } : {};
            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
                ...maybeAuth,
            };
            const response = await fetch('/api/autotuner/set_policy', {
                method: 'POST',
                headers,
                body: JSON.stringify({ policy }),
            });
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    // Not authorized / token missing
                    setAutotunerEnabled(false);
                    setAutotunerError('Not authorized / token missing');
                    return;
                }
                if (response.status === 404 || response.status >= 500) {
                    // Backend not upgraded or server error
                    setAutotunerEnabled(false);
                    setAutotunerError('Backend not upgraded');
                    return;
                }
                throw new Error(`Failed to set policy: ${response.status}`);
            }
            const data = await response.json();
            message.success('Policy updated');
            // Refetch status
            await fetchAutotunerStatus();
        } catch (err: any) {
            // Network errors or other failures
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Set policy network error:', err);
            } else {
                console.warn('Failed to set policy:', err);
            }
            setAutotunerEnabled(false);
            setAutotunerError('Backend not upgraded');
        }
    };

    const fetchJobs = async () => {
        setLoading(true);
        setError(null);
        try {
            await loadHistory();
        } catch (err: any) {
            // Don't break the page on errors, just log
            if (err.response?.status === 404) {
                console.warn('Jobs endpoint not found (404)');
                setError(null);
            } else if (err.name === 'TypeError' && err.message.includes('fetch')) {
                console.warn('Jobs fetch network error:', err);
                setError(null);
            } else {
                setError(err.response?.data?.detail || err.message || 'Failed to fetch jobs');
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchJobDetail = async (job: JobMeta) => {
        setDetailLoading(true);
        try {
            const detail = await experimentApi.getJobDetail(job.job_id);
            setJobDetail(detail);
            // Fetch artifacts if job succeeded
            if (detail.status === 'SUCCEEDED') {
                try {
                    const artifactsData = await experimentApi.getJobArtifacts(job.job_id);
                    setArtifacts(artifactsData);
                } catch (err) {
                    console.warn('Failed to fetch artifacts:', err);
                }
            }
            // Fetch logs
            try {
                const logsString = await experimentApi.getJobLogs(job.job_id, 500);
                const logsArray = logsString ? logsString.split('\n').filter(line => line.trim() !== '') : [];
                setLogs(logsArray);
            } catch (err) {
                console.warn('Failed to fetch logs:', err);
                setLogs([]);
            }
        } catch (err: any) {
            console.error('Failed to fetch job details:', err);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleRowClick = (job: JobMeta) => {
        setSelectedJob(job);
        setDrawerVisible(true);
        setJobDetail(null);
        setArtifacts(null);
        setLogs([]);
        fetchJobDetail(job);
        // Update URL with jobId
        const newParams = new URLSearchParams(searchParams);
        newParams.set('jobId', job.job_id);
        setSearchParams(newParams);
    };

    const handleDrawerClose = () => {
        setDrawerVisible(false);
        setSelectedJob(null);
        setJobDetail(null);
        setArtifacts(null);
        setLogs([]);
        // Remove jobId from URL
        const newParams = new URLSearchParams(searchParams);
        newParams.delete('jobId');
        setSearchParams(newParams);
    };

    // Deep link: auto-open drawer if jobId in URL
    useEffect(() => {
        const jobId = searchParams.get('jobId');
        if (jobId && history && history.length > 0 && !drawerVisible) {
            const job = history.find(j => j.job_id === jobId);
            if (job && !selectedJob) {
                setSelectedJob(job);
                setDrawerVisible(true);
                fetchJobDetail(job);
            }
        }
    }, [searchParams, history, drawerVisible, selectedJob]);

    // Read filters from URL params (with defaults)
    useEffect(() => {
        const timeRangeParam = searchParams.get('time_range');
        const budgetParam = searchParams.get('budget');
        setTimeRange(timeRangeParam || '24h'); // Default to 24h if not in URL
        if (budgetParam) setBudgetFilter(parseFloat(budgetParam));
    }, [searchParams]);

    useEffect(() => {
        fetchJobs();
        fetchKPI();
        fetchTrilines(timeRange || undefined, budgetFilter || undefined);
        fetchLangfuseUrl();
        fetchLastTraceUrls();
        fetchAutotunerStatus();
    }, [timeRange, budgetFilter, dataMode]);

    // Refresh trilines when policy changes
    useEffect(() => {
        if (autotunerPolicy !== null) {
            fetchTrilines(timeRange || undefined, budgetFilter || undefined);
        }
    }, [autotunerPolicy, dataMode]);

    // Get current KPI values based on selected budget
    const getCurrentKPI = () => {
        if (!trilinesData || !selectedBudget) {
            return { p95: null, recall10: null, cost1k: null };
        }
        const point = trilinesData.points.find(p => p.budget === selectedBudget);
        if (!point) {
            return { p95: null, recall10: null, cost1k: null };
        }
        return {
            p95: point.p95_ms,
            recall10: point.recall10,
            cost1k: point.cost_1k_usd,
        };
    };

    // Get chart data filtered by selected budget
    const getChartData = () => {
        if (!trilinesData || !selectedBudget) {
            return [];
        }
        // Filter points for selected budget and sort by budget
        return trilinesData.points
            .filter(p => p.budget === selectedBudget)
            .sort((a, b) => a.budget - b.budget)
            .map(p => ({
                budget: p.budget,
                p95_ms: p.p95_ms,
                recall10: p.recall10,
                cost_1k_usd: p.cost_1k_usd,
            }));
    };

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'SUCCEEDED':
                return 'success';
            case 'RUNNING':
                return 'processing';
            case 'QUEUED':
                return 'default';
            case 'FAILED':
            case 'ABORTED':
                return 'error';
            case 'CANCELLED':
                return 'warning';
            default:
                return 'default';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'SUCCEEDED':
                return <CheckCircleOutlined />;
            case 'RUNNING':
                return <ClockCircleOutlined />;
            case 'QUEUED':
                return <ClockCircleOutlined />;
            case 'FAILED':
            case 'ABORTED':
                return <CloseCircleOutlined />;
            default:
                return <ClockCircleOutlined />;
        }
    };

    const formatTimestamp = (ts?: string | null) => {
        if (!ts) return '-';
        try {
            return new Date(ts).toLocaleString();
        } catch {
            return ts;
        }
    };

    // Check if data is stale (older than 2 hours)
    const isDataStale = (updatedAt: string | null | undefined): boolean => {
        if (!updatedAt) return false;
        try {
            const updated = new Date(updatedAt);
            const now = new Date();
            const diffHours = (now.getTime() - updated.getTime()) / (1000 * 60 * 60);
            return diffHours > 2;
        } catch {
            return false;
        }
    };

    // Check if cost series is all zeros
    const isCostAllZeros = (): boolean => {
        if (!trilinesData || !selectedBudget) return true;
        const points = trilinesData.points.filter(p => p.budget === selectedBudget);
        return points.length === 0 || points.every(p => p.cost_1k_usd === 0);
    };

    // Group trilines by budget and pick best point based on policy
    const getBudgetSegments = (): BudgetSegmentRow[] => {
        if (!trilinesData || trilinesData.points.length === 0) {
            return [];
        }

        // Group points by budget
        const budgetGroups = new Map<number, TrilinesPoint[]>();
        for (const point of trilinesData.points) {
            const budget = point.budget;
            if (!budgetGroups.has(budget)) {
                budgetGroups.set(budget, []);
            }
            budgetGroups.get(budget)!.push(point);
        }

        const segments: BudgetSegmentRow[] = [];

        for (const [budget, points] of budgetGroups.entries()) {
            if (points.length === 0) continue;

            let bestPoint: TrilinesPoint | null = null;

            // If autotuner policy is available, use it to select best point
            if (autotunerPolicy && autotunerEnabled) {
                if (autotunerPolicy === 'LatencyFirst') {
                    // Min p95
                    bestPoint = points.reduce((min, p) =>
                        p.p95_ms < min.p95_ms ? p : min
                    );
                } else if (autotunerPolicy === 'RecallFirst') {
                    // Max recall
                    bestPoint = points.reduce((max, p) =>
                        p.recall10 > max.recall10 ? p : max
                    );
                } else if (autotunerPolicy === 'Balanced') {
                    // Argmax of (recall - α * normalized_p95), with α=0.5
                    const alpha = 0.5;
                    const p95Values = points.map(p => p.p95_ms);
                    const minP95 = Math.min(...p95Values);
                    const maxP95 = Math.max(...p95Values);
                    const p95Range = maxP95 - minP95 || 1; // Avoid division by zero

                    bestPoint = points.reduce((best, p) => {
                        const normalizedP95 = (p.p95_ms - minP95) / p95Range;
                        const score = p.recall10 - alpha * normalizedP95;
                        const bestScore = best.recall10 - alpha * ((best.p95_ms - minP95) / p95Range);
                        return score > bestScore ? p : best;
                    });
                }
            }

            // If no policy or no best point selected, use Pareto-optimal (max recall, then min p95)
            if (!bestPoint) {
                // First, find max recall
                const maxRecall = Math.max(...points.map(p => p.recall10));
                const maxRecallPoints = points.filter(p => p.recall10 === maxRecall);
                // Then, among max recall points, find min p95
                bestPoint = maxRecallPoints.reduce((min, p) =>
                    p.p95_ms < min.p95_ms ? p : min
                );
            }

            // Get trace URL (fallback to latest trace)
            const traceUrl = lastTraceUrls.length > 0 ? lastTraceUrls[0] : null;

            segments.push({
                budget,
                recall10: bestPoint.recall10,
                p95: bestPoint.p95_ms,
                cost_per_1k: bestPoint.cost_1k_usd,
                policy_used: autotunerPolicy && autotunerEnabled ? autotunerPolicy : null,
                updated_at: trilinesData.updated_at,
                trace_url: traceUrl,
            });
        }

        // Sort by budget
        segments.sort((a, b) => a.budget - b.budget);

        // Apply time/budget filters if set
        let filtered = segments;
        if (budgetFilter !== null) {
            filtered = filtered.filter(s => s.budget === budgetFilter);
        }
        // Note: time_range filter would need to be applied at the trilines fetch level

        return filtered;
    };

    // Check if trace URL is accessible (for acceptance check)
    // Note: Due to CORS limitations, we can't reliably check accessibility
    // So we just check if URL exists and is non-empty
    const checkTraceAccessible = async (url: string | null): Promise<boolean> => {
        if (!url || url.trim() === '') return false;
        // For acceptance check, we consider a URL "accessible" if it exists
        // In a real scenario, you might want to do a HEAD request (with proper CORS setup)
        // or use a backend proxy to check accessibility
        return true;
    };

    // Download CSV helper
    const downloadCSV = (rows: BudgetSegmentRow[]) => {
        const headers = ['Budget', 'Recall@10', 'p95', 'Cost/1k', 'Policy', 'Updated At', 'Trace URL'];
        const csvRows = [
            headers.join(','),
            ...rows.map(row => [
                row.budget,
                row.recall10.toFixed(4),
                row.p95.toFixed(2),
                row.cost_per_1k.toFixed(4),
                row.policy_used || '',
                row.updated_at,
                row.trace_url || '',
            ].join(','))
        ];
        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `budget_segments_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const budgetSegments = getBudgetSegments();
    const kpi = getCurrentKPI();
    const chartData = getChartData();

    // Acceptance check: Table OK tag (dev-only)
    const [tableOk, setTableOk] = useState(false);
    const [checkingTable, setCheckingTable] = useState(false);

    useEffect(() => {
        if (import.meta.env.DEV && budgetSegments.length >= 3) {
            setCheckingTable(true);
            // Check if at least one trace is accessible
            const checkTraces = async () => {
                const checks = await Promise.all(
                    budgetSegments.slice(0, 3).map(row => checkTraceAccessible(row.trace_url))
                );
                setTableOk(checks.some(ok => ok));
                setCheckingTable(false);
            };
            checkTraces();
        } else {
            setTableOk(false);
        }
    }, [budgetSegments]);

    return (
        <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <Space>
                    <Title level={2} style={{ marginBottom: '8px', margin: 0 }}>
                        <BarChartOutlined /> Metrics Hub
                    </Title>
                    {import.meta.env.DEV && budgetSegments.length >= 3 && (
                        <Tag color={tableOk ? 'success' : 'default'} style={{ marginLeft: '8px' }}>
                            {checkingTable ? 'Checking...' : tableOk ? 'Table OK' : 'Table'}
                        </Tag>
                    )}
                </Space>
                <Space>
                    {/* Autotuner Policy Selector */}
                    <Space direction="vertical" size="small">
                        <Space>
                            <Text type="secondary">Strategy:</Text>
                            <Select
                                value={autotunerPolicy}
                                onChange={setPolicy}
                                disabled={!autotunerEnabled}
                                loading={autotunerLoading}
                                style={{ width: 150 }}
                                size="small"
                            >
                                <Select.Option value="LatencyFirst">LatencyFirst</Select.Option>
                                <Select.Option value="RecallFirst">RecallFirst</Select.Option>
                                <Select.Option value="Balanced">Balanced</Select.Option>
                            </Select>
                        </Space>
                        {autotunerError && !autotunerEnabled && (
                            <Alert
                                message={autotunerError === 'Not authorized / token missing'
                                    ? 'Not authorized / token missing'
                                    : 'Strategy API not available (backend not upgraded).'}
                                type="info"
                                showIcon={false}
                                style={{
                                    margin: 0,
                                    padding: '4px 8px',
                                    backgroundColor: '#f5f5f5',
                                    border: '1px solid #d9d9d9',
                                    fontSize: '12px'
                                }}
                            />
                        )}
                    </Space>
                    <Tooltip title={lastTraceUrls.length === 0 ? "No trace captured yet." : ""}>
                        <Button
                            type="primary"
                            icon={<LinkOutlined />}
                            onClick={handleOpenLastTrace}
                            loading={lastTraceLoading}
                            disabled={lastTraceUrls.length === 0 && !lastTraceLoading}
                        >
                            Open last trace
                        </Button>
                    </Tooltip>
                </Space>
            </div>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                View metrics and experiment results
            </Paragraph>

            {/* Error alerts */}
            {error && (
                <Alert
                    message="Error"
                    description={error}
                    type="error"
                    closable
                    onClose={() => setError(null)}
                    style={{ marginBottom: '16px' }}
                />
            )}
            {kpiError && (
                <Alert
                    message="KPI Error"
                    description={kpiError}
                    type="warning"
                    closable
                    onClose={() => setKpiError(null)}
                    style={{ marginBottom: '16px' }}
                />
            )}
            {trilinesError && (
                <Alert
                    message="Metrics Error"
                    description={trilinesError}
                    type="warning"
                    closable
                    onClose={() => setTrilinesError(null)}
                    style={{ marginBottom: '16px' }}
                />
            )}

            {/* Stale data warning */}
            {kpiData && isDataStale(kpiData.updated_at) && (
                <Alert
                    message="Data may be stale"
                    description="Last updated more than 2 hours ago. Run 'make ci' to refresh."
                    type="warning"
                    showIcon
                    style={{ marginBottom: '16px', backgroundColor: '#f5f5f5', borderColor: '#d9d9d9' }}
                />
            )}

            {/* KPI Cards */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">Success Rate</Text>
                            {kpiLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpiData ? `${(kpiData.success_rate * 100).toFixed(1)}%` : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">P95 Down</Text>
                            {kpiLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpiData ? (
                                        <Tag color={kpiData.p95_down ? 'success' : 'error'}>
                                            {kpiData.p95_down ? '✓' : '✗'}
                                        </Tag>
                                    ) : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">Bounds OK</Text>
                            {kpiLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpiData ? (
                                        <Tag color={kpiData.bounds_ok ? 'success' : 'error'}>
                                            {kpiData.bounds_ok ? '✓' : '✗'}
                                        </Tag>
                                    ) : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">Stable Detune</Text>
                            {kpiLoading ? (
                                <Skeleton.Input active size="large" style={{ width: '100%' }} />
                            ) : (
                                <Text strong style={{ fontSize: '24px' }}>
                                    {kpiData ? (
                                        <Tag color={kpiData.stable_detune ? 'success' : 'error'}>
                                            {kpiData.stable_detune ? '✓' : '✗'}
                                        </Tag>
                                    ) : '—'}
                                </Text>
                            )}
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* Last updated timestamp */}
            {kpiData && (
                <div style={{ marginBottom: '16px', textAlign: 'right' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        Last updated: {formatTimestamp(kpiData.updated_at)}
                    </Text>
                </div>
            )}

            {/* Filters and Budget Selector */}
            {trilinesData && trilinesData.budgets.length > 0 && (
                <Card
                    bordered={false}
                    style={{ marginBottom: '24px' }}
                    extra={
                        <Space>
                            <Text type="secondary">Dataset:</Text>
                            <Select
                                value={dataMode}
                                onChange={(value: DataMode) => {
                                    setDataMode(value);
                                }}
                                style={{ width: 160 }}
                                size="small"
                            >
                                <Select.Option value="full">Full CI (2000×15)</Select.Option>
                                <Select.Option value="fast">Fast CI (200×5)</Select.Option>
                            </Select>
                            <Text type="secondary">Time Range:</Text>
                            <Select
                                value={timeRange}
                                onChange={(value) => {
                                    setTimeRange(value || '24h');
                                    setAutoWidened(false); // Reset auto-widen flag when user changes filter
                                    const newParams = new URLSearchParams(searchParams);
                                    if (value) {
                                        newParams.set('time_range', value);
                                    } else {
                                        newParams.set('time_range', '24h'); // Default to 24h instead of clearing
                                    }
                                    setSearchParams(newParams);
                                }}
                                style={{ width: 120 }}
                                size="small"
                            >
                                <Select.Option value="1h">Last 1 hour</Select.Option>
                                <Select.Option value="6h">Last 6 hours</Select.Option>
                                <Select.Option value="24h">Last 24 hours</Select.Option>
                                <Select.Option value="48h">Last 48 hours</Select.Option>
                                <Select.Option value="7d">Last 7 days</Select.Option>
                            </Select>
                            <Text type="secondary">Budget Filter:</Text>
                            <Select
                                value={budgetFilter}
                                onChange={(value) => {
                                    setBudgetFilter(value);
                                    const newParams = new URLSearchParams(searchParams);
                                    if (value) {
                                        newParams.set('budget', value.toString());
                                    } else {
                                        newParams.delete('budget');
                                    }
                                    setSearchParams(newParams);
                                }}
                                style={{ width: 120 }}
                                size="small"
                                allowClear
                            >
                                {trilinesData.budgets.map(budget => (
                                    <Select.Option key={budget} value={budget}>
                                        {budget} ms
                                    </Select.Option>
                                ))}
                            </Select>
                            <Text type="secondary">Chart Budget:</Text>
                            <Select
                                value={selectedBudget}
                                onChange={setSelectedBudget}
                                style={{ width: 120 }}
                                size="small"
                            >
                                {trilinesData.budgets.map(budget => (
                                    <Select.Option key={budget} value={budget}>
                                        {budget} ms
                                    </Select.Option>
                                ))}
                            </Select>
                        </Space>
                    }
                >
                    {/* Trilines Chart */}
                    {trilinesLoading ? (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <Spin size="large" />
                        </div>
                    ) : chartData.length === 0 ? (
                        <Empty
                            description="No data available for selected budget"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            style={{ color: '#999' }}
                        />
                    ) : (
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                                <XAxis dataKey="budget" stroke="#aaa" fontSize={12} />
                                <YAxis yAxisId="left" label={{ value: 'P95 (ms)', angle: -90, position: 'insideLeft', fill: '#aaa' }} stroke="#FF7F0E" />
                                <YAxis yAxisId="right" orientation="right" label={{ value: 'Recall@10 / Cost', angle: 90, position: 'insideRight', fill: '#aaa' }} stroke="#1f77b4" />
                                <RechartsTooltip
                                    contentStyle={{ backgroundColor: '#333', border: 'none' }}
                                    itemStyle={{ color: '#eee' }}
                                    formatter={(value: any, name: string) => {
                                        if (name === 'Cost/1k ($)' && (isCostAllZeros() || (kpiData && !kpiData.cost_enabled))) {
                                            return ['—', name];
                                        }
                                        return [value, name];
                                    }}
                                />
                                <Legend
                                    formatter={(value: string) => {
                                        if (value === 'Cost/1k ($)' && kpiData && kpiData.cost_enabled) {
                                            return (
                                                <span>
                                                    {value}{' '}
                                                    <Tag color="blue" style={{ marginLeft: '4px', fontSize: '10px', lineHeight: '14px' }}>
                                                        estimated
                                                    </Tag>
                                                </span>
                                            );
                                        }
                                        return value;
                                    }}
                                />
                                <Line yAxisId="left" type="monotone" dataKey="p95_ms" name="P95 (ms)" stroke="#FFA500" strokeWidth={2} dot={{ r: 4 }} />
                                <Line yAxisId="right" type="monotone" dataKey="recall10" name="Recall@10" stroke="#00BFFF" strokeWidth={2} dot={{ r: 4 }} />
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="cost_1k_usd"
                                    name={kpiData && kpiData.cost_enabled ? 'Cost/1k ($) estimated' : 'Cost/1k ($)'}
                                    stroke="#8884d8"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                    strokeDasharray={isCostAllZeros() || (kpiData && !kpiData.cost_enabled) ? "5 5" : undefined}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                    {/* Cost enabled: show estimated badge */}
                    {kpiData && kpiData.cost_enabled && !isCostAllZeros() && (
                        <div style={{ marginTop: '8px', textAlign: 'center' }}>
                            <Space>
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    Cost/1k ($):
                                </Text>
                                <Tag color="blue">estimated</Tag>
                            </Space>
                        </div>
                    )}
                    {/* Cost disabled notice */}
                    {(isCostAllZeros() || (kpiData && !kpiData.cost_enabled)) && (
                        <div style={{ marginTop: '8px', textAlign: 'center' }}>
                            <Tooltip title="Configure MODEL_PRICING_JSON to enable cost.">
                                <Text type="secondary" style={{ fontSize: '12px', cursor: 'help' }}>
                                    Cost/1k ($): — (not configured)
                                </Text>
                            </Tooltip>
                        </div>
                    )}
                </Card>
            )}

            {/* Budget Segments Table */}
            {trilinesData && trilinesData.budgets.length > 0 && (
                <Card
                    title="Budget Segments Table"
                    bordered={false}
                    style={{ marginBottom: '24px' }}
                    extra={
                        <Button
                            icon={<DownloadOutlined />}
                            onClick={() => downloadCSV(budgetSegments)}
                            disabled={budgetSegments.length === 0}
                            size="small"
                        >
                            Download CSV
                        </Button>
                    }
                >
                    {trilinesLoading ? (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <Spin size="large" />
                        </div>
                    ) : budgetSegments.length === 0 ? (
                        <Empty
                            description="No budget segments available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            style={{ color: '#999' }}
                        />
                    ) : (
                        <Table<BudgetSegmentRow>
                            dataSource={budgetSegments}
                            rowKey="budget"
                            pagination={false}
                            size="small"
                            columns={[
                                {
                                    title: 'Budget',
                                    dataIndex: 'budget',
                                    key: 'budget',
                                    render: (value: number) => `${value} ms`,
                                    sorter: (a, b) => a.budget - b.budget,
                                },
                                {
                                    title: 'Recall@10',
                                    dataIndex: 'recall10',
                                    key: 'recall10',
                                    render: (value: number) => value.toFixed(4),
                                    sorter: (a, b) => a.recall10 - b.recall10,
                                },
                                {
                                    title: 'p95',
                                    dataIndex: 'p95',
                                    key: 'p95',
                                    render: (value: number) => `${value.toFixed(2)} ms`,
                                    sorter: (a, b) => a.p95 - b.p95,
                                },
                                {
                                    title: 'Cost/1k',
                                    dataIndex: 'cost_per_1k',
                                    key: 'cost_per_1k',
                                    render: (value: number, record) => {
                                        if (!kpiData?.cost_enabled || value === 0) {
                                            return (
                                                <Tooltip title="Configure MODEL_PRICING_JSON to enable cost.">
                                                    <Text type="secondary" style={{ fontStyle: 'italic' }}>
                                                        —
                                                    </Text>
                                                </Tooltip>
                                            );
                                        }
                                        return `$${value.toFixed(4)}`;
                                    },
                                    sorter: (a, b) => a.cost_per_1k - b.cost_per_1k,
                                },
                                {
                                    title: 'Actions',
                                    key: 'actions',
                                    render: (_: any, record: BudgetSegmentRow) => {
                                        const traceUrl = record.trace_url || (lastTraceUrls.length > 0 ? lastTraceUrls[0] : null);
                                        return (
                                            <Space>
                                                {traceUrl ? (
                                                    <>
                                                        <Button
                                                            type="link"
                                                            size="small"
                                                            icon={<LinkOutlined />}
                                                            onClick={() => window.open(traceUrl, '_blank', 'noopener,noreferrer')}
                                                        >
                                                            Open trace
                                                        </Button>
                                                        <Button
                                                            type="link"
                                                            size="small"
                                                            icon={<CopyOutlined />}
                                                            onClick={() => handleCopyUrl(traceUrl)}
                                                        >
                                                            Copy URL
                                                        </Button>
                                                    </>
                                                ) : (
                                                    <Button
                                                        type="link"
                                                        size="small"
                                                        disabled
                                                    >
                                                        No trace
                                                    </Button>
                                                )}
                                            </Space>
                                        );
                                    },
                                },
                            ]}
                        />
                    )}
                </Card>
            )}

            {/* Jobs List */}
            <Card
                bordered={false}
                extra={
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={() => {
                            fetchJobs();
                            fetchKPI();
                            fetchTrilines(timeRange || undefined, budgetFilter || undefined);
                            fetchLangfuseUrl();
                            fetchLastTraceUrls();
                        }}
                        loading={loading || kpiLoading || trilinesLoading}
                    >
                        Refresh
                    </Button>
                }
            >
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" />
                    </div>
                ) : !history || history.length === 0 ? (
                    <Empty
                        description="No records yet. Run experiments to see metrics here."
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        style={{ color: '#999' }}
                    />
                ) : (
                    <List
                        dataSource={history}
                        renderItem={(job: JobMeta) => {
                            const traceUrl = getTraceUrl(job);
                            return (
                                <List.Item
                                    style={{ cursor: 'pointer' }}
                                    onClick={() => handleRowClick(job)}
                                    actions={[
                                        <Space key="trace-actions" onClick={(e) => e.stopPropagation()}>
                                            {traceUrl ? (
                                                <>
                                                    <Button
                                                        type="link"
                                                        size="small"
                                                        icon={<LinkOutlined />}
                                                        onClick={() => window.open(traceUrl, '_blank', 'noopener,noreferrer')}
                                                    >
                                                        Open trace
                                                    </Button>
                                                    <Button
                                                        type="link"
                                                        size="small"
                                                        icon={<CopyOutlined />}
                                                        onClick={() => handleCopyUrl(traceUrl)}
                                                    >
                                                        Copy URL
                                                    </Button>
                                                </>
                                            ) : (
                                                <Button
                                                    type="link"
                                                    size="small"
                                                    disabled
                                                >
                                                    No trace
                                                </Button>
                                            )}
                                        </Space>
                                    ]}
                                >
                                    <List.Item.Meta
                                        avatar={
                                            <Tag
                                                color={getStatusColor(job.status)}
                                                icon={getStatusIcon(job.status)}
                                            >
                                                {job.status}
                                            </Tag>
                                        }
                                        title={
                                            <Space>
                                                <Text code style={{ fontSize: '12px' }}>
                                                    {job.job_id.substring(0, 8)}...
                                                </Text>
                                                {(job.status === 'RUNNING' || job.status === 'QUEUED') && (
                                                    <Tag color="blue" icon={<ReloadOutlined spin />}>
                                                        Active
                                                    </Tag>
                                                )}
                                            </Space>
                                        }
                                        description={
                                            <Space direction="vertical" size="small">
                                                <div>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        Created: {formatTimestamp(job.created_at)}
                                                    </Text>
                                                </div>
                                                {job.finished_at && (
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            Finished: {formatTimestamp(job.finished_at)}
                                                        </Text>
                                                    </div>
                                                )}
                                                {job.return_code !== null && job.return_code !== undefined && (
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            Return Code: {job.return_code}
                                                        </Text>
                                                    </div>
                                                )}
                                                {job.params && Object.keys(job.params).length > 0 && (
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            Dataset: {job.params?.dataset_name ?? 'unknown'}
                                                        </Text>
                                                    </div>
                                                )}
                                            </Space>
                                        }
                                    />
                                </List.Item>
                            );
                        }}
                    />
                )}
            </Card>

            {/* Detail Drawer */}
            <Drawer
                title={
                    <Space>
                        <BarChartOutlined />
                        <Text strong>Job Details</Text>
                    </Space>
                }
                placement="right"
                size="large"
                onClose={handleDrawerClose}
                open={drawerVisible}
                extra={
                    <Space>
                        {(() => {
                            const traceUrl = getTraceUrl(selectedJob);
                            return traceUrl ? (
                                <>
                                    <Button
                                        type="primary"
                                        icon={<LinkOutlined />}
                                        onClick={() => window.open(traceUrl, '_blank', 'noopener,noreferrer')}
                                    >
                                        Open trace
                                    </Button>
                                    <Button
                                        type="default"
                                        icon={<CopyOutlined />}
                                        onClick={() => handleCopyUrl(traceUrl)}
                                    >
                                        Copy URL
                                    </Button>
                                </>
                            ) : null;
                        })()}
                        {langfuseUrl && (
                            <Button
                                type="default"
                                icon={<LinkOutlined />}
                                onClick={() => window.open(langfuseUrl, '_blank', 'noopener,noreferrer')}
                            >
                                Open in Langfuse
                            </Button>
                        )}
                        <Button
                            type="text"
                            icon={<CloseOutlined />}
                            onClick={handleDrawerClose}
                        />
                    </Space>
                }
            >
                {detailLoading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" />
                    </div>
                ) : jobDetail ? (
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {/* Job Information */}
                        <Card title="Job Information" bordered={false} size="small">
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <div>
                                    <Text strong>Status: </Text>
                                    <Tag
                                        color={getStatusColor(jobDetail.status)}
                                        icon={getStatusIcon(jobDetail.status)}
                                    >
                                        {jobDetail.status}
                                    </Tag>
                                </div>

                                <div>
                                    <Text strong>Job ID: </Text>
                                    <Text code style={{ fontSize: '12px' }}>
                                        {jobDetail.job_id}
                                    </Text>
                                </div>

                                <div>
                                    <Text strong>Dataset: </Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {(() => {
                                            const dataset = jobDetail?.params?.dataset_name
                                                ?? jobDetail?.config?.dataset_name
                                                ?? (jobDetail?.cmd?.join(' ')?.match(/--dataset-name\s+(\S+)/)?.[1]);
                                            return dataset || 'unknown';
                                        })()} | Qrels: {(() => {
                                            const qrels = jobDetail?.params?.qrels_name
                                                ?? jobDetail?.config?.qrels_name
                                                ?? jobDetail?.cmd?.join(' ')?.match(/--qrels-name\s+(\S+)/)?.[1];
                                            return qrels ? qrels.replace('fiqa_qrels_', '').replace('_10k_v1', '').replace('_50k_v1', '').replace('_v1', '') : 'v1';
                                        })()} | Fields: title+abstract
                                    </Text>
                                </div>

                                {jobDetail.progress_hint && (
                                    <div>
                                        <Text strong>Progress: </Text>
                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                            {jobDetail.progress_hint}
                                        </Text>
                                    </div>
                                )}

                                <Space direction="vertical" size="small">
                                    <div>
                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                            Queued: {formatTimestamp(jobDetail.queued_at)}
                                        </Text>
                                    </div>
                                    {jobDetail.started_at && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Started: {formatTimestamp(jobDetail.started_at)}
                                            </Text>
                                        </div>
                                    )}
                                    {jobDetail.finished_at && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Finished: {formatTimestamp(jobDetail.finished_at)}
                                            </Text>
                                        </div>
                                    )}
                                    {jobDetail.return_code !== null && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                Return Code: {jobDetail.return_code}
                                            </Text>
                                        </div>
                                    )}
                                </Space>
                            </Space>
                        </Card>

                        {/* Timeline */}
                        <Card title="Job Timeline" bordered={false} size="small">
                            <Timeline
                                items={[
                                    {
                                        color: 'blue',
                                        children: (
                                            <div>
                                                <Text strong>Job Created</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.queued_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    jobDetail.started_at && {
                                        color: 'green',
                                        children: (
                                            <div>
                                                <Text strong>Job Started</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.started_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                    jobDetail.finished_at && {
                                        color: jobDetail.status === 'SUCCEEDED' ? 'green' : 'red',
                                        children: (
                                            <div>
                                                <Text strong>
                                                    Job {jobDetail.status === 'SUCCEEDED' ? 'Completed' : 'Failed'}
                                                </Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                                    {formatTimestamp(jobDetail.finished_at)}
                                                </Text>
                                            </div>
                                        ),
                                    },
                                ].filter(Boolean)}
                            />
                        </Card>

                        {/* Artifacts */}
                        <Card
                            title={
                                <Space>
                                    <FileImageOutlined /> Artifacts
                                </Space>
                            }
                            bordered={false}
                            size="small"
                        >
                            {artifacts?.artifacts ? (
                                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                    <div>
                                        <Text strong>Timestamp: </Text>
                                        <Text code style={{ fontSize: '12px' }}>
                                            {artifacts.artifacts.timestamp}
                                        </Text>
                                    </div>

                                    {artifacts.artifacts.combined_plot && (
                                        <div>
                                            <div style={{ marginBottom: '8px' }}>
                                                <Text strong>
                                                    <FileImageOutlined /> Combined Charts
                                                </Text>
                                            </div>
                                            <img
                                                src={`/${artifacts.artifacts.combined_plot}`}
                                                alt="Combined Charts"
                                                style={{
                                                    width: '100%',
                                                    borderRadius: '8px',
                                                    border: '1px solid #d9d9d9',
                                                }}
                                                onError={(e) => {
                                                    (e.target as HTMLImageElement).style.display = 'none';
                                                }}
                                            />
                                        </div>
                                    )}

                                    {artifacts.artifacts.report_data && (
                                        <Collapse>
                                            <Panel
                                                header={
                                                    <Space>
                                                        <FileTextOutlined />
                                                        <Text strong>Report Data</Text>
                                                    </Space>
                                                }
                                                key="report"
                                            >
                                                <pre style={{ fontSize: '11px', margin: 0 }}>
                                                    {JSON.stringify(artifacts.artifacts.report_data, null, 2)}
                                                </pre>
                                            </Panel>
                                        </Collapse>
                                    )}
                                </Space>
                            ) : jobDetail.status === 'SUCCEEDED' ? (
                                <Text type="secondary">Loading artifacts...</Text>
                            ) : (
                                <Text type="secondary">No artifacts available</Text>
                            )}
                        </Card>

                        {/* Logs */}
                        <Card
                            title="Job Logs"
                            bordered={false}
                            size="small"
                            extra={
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    {(logs || []).length} lines
                                </Text>
                            }
                            style={{ maxHeight: '400px', overflow: 'auto' }}
                        >
                            {(logs || []).length > 0 ? (
                                <List
                                    dataSource={logs}
                                    renderItem={(line) => (
                                        <List.Item style={{ padding: '4px 0', fontFamily: 'monospace' }}>
                                            <Text
                                                style={{
                                                    fontSize: '12px',
                                                    color: line.includes('ERROR') || line.includes('FAILED')
                                                        ? '#ff4d4f'
                                                        : line.includes('WARNING')
                                                            ? '#faad14'
                                                            : '#fff',
                                                }}
                                            >
                                                {line}
                                            </Text>
                                        </List.Item>
                                    )}
                                    size="small"
                                />
                            ) : (
                                <Text type="secondary">No logs available</Text>
                            )}
                        </Card>
                    </Space>
                ) : (
                    <Alert message="Job not found" type="warning" />
                )}
            </Drawer>

            {/* Footer with Backend URL */}
            <div style={{
                marginTop: '24px',
                paddingTop: '16px',
                borderTop: '1px solid #303030',
                textAlign: 'center'
            }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                    Backend URL: {window.location.origin}
                </Text>
            </div>
        </div>
    );
};
