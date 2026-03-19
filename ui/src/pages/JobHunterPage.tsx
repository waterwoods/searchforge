// frontend/src/pages/JobHunterPage.tsx
// JobHunter Agent - 三栏布局页面
// 
// 布局说明：
// - 左侧栏：已分析的 JD 历史记录列表
// - 中间栏：JD 输入框 + 聊天对话区域
// - 右侧栏：JD 分析结果详情（金银铜要点、适配度、优势/缺口等）
//
// 需要连接的三个后端 Flow：
// - Flow 1: JD 解读 + 适配度分析 (POST /api/jobhunter/analyze)
// - Flow 2: 多轮职业教练对话 (POST /api/jobhunter/chat)
// - Flow 3: 偏好/历史经验加权 (POST /api/jobhunter/preferences) - 可稍后接

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
    Card,
    Typography,
    Input,
    Button,
    Row,
    Col,
    Form,
    App,
    Spin,
    Tag,
    List,
    Divider,
    Alert,
    Space,
    Tabs,
    Empty,
    Radio,
    Collapse,
    Tooltip,
    Checkbox,
    Select,
} from 'antd';
import { SearchOutlined, MessageOutlined, FileTextOutlined, HistoryOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { API_BASE_URL } from '../api/config';
import {
    fetchJobhunterCache,
    fetchCachedJDDetail,
    type CachedJDDetail,
    getUserResume,
    saveUserResume,
    sendCareerChat,
    type CareerChatMessage,
    type CareerChatTopic,
    getQuickView,
    type QuickViewResponse,
    runFullAnalysisForCacheId,
} from '../api/jobhunter';
import {
    getJobApplications,
    upsertJobApplication,
    deleteJobApplication,
    type ApplicationStatus,
} from '../api/jobhunter_applications';
import type { CachedJobAnalysis } from '../types/api.types';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

// ========================================
// 类型定义（临时，后续需要从 api.types.ts 导入）
// ========================================
interface JobJDInput {
    job_id?: string;
    title?: string;
    company?: string;
    description: string;
    location?: string;
}

interface LifecycleSummary {
    summary?: string;
    stages?: string[];
}

interface SpotlightStory {
    focus_area: string;
    why_important: string;
    upstream_downstream: string;
    tools_and_systems: string;
    constraints_and_risks: string;
    success_metrics: string;
    evidence_snippets?: string[];  // [Step 2] 新增：从 JD 原文提取的证据片段
}

interface CoreSignal {
    theme: string;
    importance?: "HIGH" | "MEDIUM";
    rationale?: string;
    related_spotlights?: string[];
}

interface JobJDSummary {
    gold_points: string[];  // 核心要求（必须满足）
    silver_points: string[]; // 重要要求（最好有）
    bronze_points: string[]; // 加分项（有更好）
    reflection_problem_summary?: string;
    reflection_day_in_life?: string;
    reflection_pros_for_candidate?: string;
    reflection_risks_for_candidate?: string;
    lifecycle?: LifecycleSummary;
    spotlight_stories?: SpotlightStory[];
    core_signals?: CoreSignal[];  // [Core Signals] 新增：2-3 个核心主题
    core_narrative?: string;  // [Core Signals] 新增：总括叙事
}

interface JobFitSummary {
    match_score: number;  // 1-10
    category: 'A' | 'B' | 'C';  // A=强匹配, B=相关但不理想, C=不匹配
    strengths: string[];  // 优势
    gaps: string[];  // 缺口
    recommendation: 'APPLY' | 'MAYBE' | 'SKIP';
    reasoning_summary: string;
    next_actions?: string[];  // Next actions (optional, may be called action_items in backend)
    action_items?: string[];  // Action items (optional, backend field name)
}

interface ConstraintCheckResult {
    hard_block: boolean;
    hard_reasons?: string[];  // [Step 1] 新增：触发硬条件的具体原因
    soft_flags: string[];
    reasons: string[];
    tags: string[];
    profile_mismatch_score?: number;  // [Quick Filter] Profile/JD mismatch score (0-10)
    profile_mismatch_reasons?: string[];  // [Quick Filter] Reasons for profile mismatch
    skip_deep_analysis?: boolean;  // [Quick Filter] If true, deep analysis was skipped
}

// [Engineering View] Graph step model for debugging
interface GraphStep {
    name: string;  // Node name (e.g., "check_constraints", "interpret_jd")
    status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
    started_at?: string;  // ISO timestamp
    finished_at?: string;  // ISO timestamp
    duration_ms?: number;  // Duration in milliseconds
    extra_info?: Record<string, any>;  // Optional extra information
}

interface JDAnalysisResponse {
    ok: boolean;
    jd_summary?: JobJDSummary;
    fit_summary?: JobFitSummary;
    constraints?: ConstraintCheckResult;
    graph_steps?: GraphStep[];  // [Engineering View] Graph execution steps for debugging
    cn_fast_read?: string;  // [CN Summary] 新增：中文速读摘要
    error?: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
}

interface JDChatResponse {
    reply: string;
    messages: ChatMessage[];
}

interface AnalyzedJDRecord {
    id: string;
    job_id?: string;
    title: string;
    company: string;
    timestamp: string;
    match_score?: number;
    category?: 'A' | 'B' | 'C';
}

export const JobHunterPage = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [chatLoading, setChatLoading] = useState(false);

    // 分析结果状态
    const [analysisResult, setAnalysisResult] = useState<JDAnalysisResponse | null>(null);

    // 右侧当前 Job 标题栏状态
    const [currentJobTitle, setCurrentJobTitle] = useState<string | null>(null);
    const [currentJobCompany, setCurrentJobCompany] = useState<string | null>(null);
    const [currentJobUrl, setCurrentJobUrl] = useState<string | null>(null);

    // 聊天历史状态
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const [currentChatInput, setCurrentChatInput] = useState('');

    // 历史记录状态（左侧栏）
    const [analyzedJDList, setAnalyzedJDList] = useState<AnalyzedJDRecord[]>([]);
    const [selectedJDId, setSelectedJDId] = useState<string | null>(null);

    // 当前 JD 输入状态
    const [currentJDInput, setCurrentJDInput] = useState<JobJDInput | null>(null);

    // Profile mode state
    const [profileMode, setProfileMode] = useState<"agent" | "data_eng">("agent");

    // History sidebar collapse state (default: collapsed)
    const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(true);

    // 中间搜索表单折叠状态（默认展开）
    const [isSearchPanelCollapsed, setIsSearchPanelCollapsed] = useState(false);

    // Cached batch analysis list (from backend SQLite/Qdrant cache via /api/jobhunter/cache)
    const [cachedJobs, setCachedJobs] = useState<CachedJobAnalysis[]>([]);
    const [cacheLoading, setCacheLoading] = useState(false);
    const [cacheError, setCacheError] = useState<string | null>(null);

    // Cached detail loading state
    const [selectedCacheId, setSelectedCacheId] = useState<number | null>(null);
    const [cachedDetailLoading, setCachedDetailLoading] = useState(false);
    const [cachedDetailError, setCachedDetailError] = useState<string | null>(null);

    // Quick View state
    const [quickView, setQuickView] = useState<string | null>(null);  // Legacy: single string
    const [quickViewStructured, setQuickViewStructured] = useState<{ cn_overview: string; responsibilities: string[]; requirements: string[]; red_flags: string[] } | null>(null);  // New: structured
    const [quickViewLoading, setQuickViewLoading] = useState(false);
    const [quickViewError, setQuickViewError] = useState<string | null>(null);

    // Deep analysis state
    const [deepAnalysisLoading, setDeepAnalysisLoading] = useState(false);
    const [hasDeepAnalysis, setHasDeepAnalysis] = useState<boolean>(false);

    // Resume management state
    const [resumeText, setResumeText] = useState<string>('');
    const [resumeLoading, setResumeLoading] = useState(false);
    const [resumeSaving, setResumeSaving] = useState(false);
    const [resumeError, setResumeError] = useState<string | null>(null);

    // Career Coach chat state
    const [careerChatMessages, setCareerChatMessages] = useState<CareerChatMessage[]>([]);
    const [careerChatTopic, setCareerChatTopic] = useState<CareerChatTopic>('resume_opt');
    const [careerChatInput, setCareerChatInput] = useState('');
    const [careerChatLoading, setCareerChatLoading] = useState(false);
    const [careerChatError, setCareerChatError] = useState<string | null>(null);
    const chatEndRef = useRef<HTMLDivElement | null>(null);

    // Job application status state (map job_url -> application status)
    // CRITICAL: Use job_url as the primary key instead of cache_id to prevent
    // status loss when cache_id changes (e.g., after re-analysis or re-import)
    const [applicationStatusMap, setApplicationStatusMap] = useState<Map<string, ApplicationStatus>>(new Map());
    const [updatingApplicationId, setUpdatingApplicationId] = useState<number | null>(null);

    // Filter and sort state for cached jobs list
    const [onlyRecommended, setOnlyRecommended] = useState<boolean>(false);
    const [onlyNotApplied, setOnlyNotApplied] = useState<boolean>(false);
    const [sortMode, setSortMode] = useState<"default" | "fit_desc">("default");
    // View mode: 'all' shows all jobs, 'top' shows only high-fit jobs (category A, score >= 80)
    const [viewMode, setViewMode] = useState<'all' | 'top'>('all');

    const getProfileIdForMode = (mode: "agent" | "data_eng"): string => {
        // Map UI profile mode to backend profile_id used for caching
        if (mode === "data_eng") {
            return "data_engineer_gcp";
        }
        return "llm_agent";
    };

    /**
     * Generate a stable key for job application status lookup.
     * Priority: job_url > cache_id fallback
     * This ensures status persists even when cache_id changes (e.g., after re-analysis).
     */
    const getJobStatusKey = (job: CachedJobAnalysis): string => {
        // Priority 1: Use job_url as the primary stable identifier
        if (job.job_url && job.job_url.trim().length > 0) {
            return job.job_url.trim();
        }
        // Fallback: Use cache_id for legacy data without job_url
        // This prevents UI crashes for old records that might not have job_url
        return `cache_${job.cache_id}`;
    };

    // Load cached batch results whenever profile mode changes.
    // NOTE: This list is based on backend SQLite cache via /api/jobhunter/cache,
    // not on real-time LLM analysis.
    useEffect(() => {
        const loadCache = async () => {
            try {
                setCacheLoading(true);
                setCacheError(null);
                const profileId = getProfileIdForMode(profileMode);
                const items = await fetchJobhunterCache(profileId, 50);

                // Safety: sort by match_score descending (backend also orders by updated_at)
                const sorted = [...items].sort((a, b) => {
                    const aScore = a.match_score ?? 0;
                    const bScore = b.match_score ?? 0;
                    return bScore - aScore;
                });

                setCachedJobs(sorted);
            } catch (err) {
                const msg = err instanceof Error ? err.message : 'Failed to load cached jobs';
                console.error('[JobHunter] Failed to load cache:', err);
                setCacheError(msg);
            } finally {
                setCacheLoading(false);
            }
        };

        loadCache();
    }, [profileMode]);

    // Load job application statuses when profile mode changes
    // IMPORTANT: This state is independent of filters and should never be cleared
    // by filter logic. Only update when profileMode changes or when explicitly
    // marking/unmarking applications.
    useEffect(() => {
        const loadApplicationStatuses = async () => {
            try {
                const profileId = getProfileIdForMode(profileMode);
                const response = await getJobApplications({ profileId, limit: 500 });

                // Build map of job_url -> status (fallback to cache_id for legacy data)
                // CRITICAL: Use job_url as primary key to prevent status loss when cache_id changes
                const statusMap = new Map<string, ApplicationStatus>();
                response.items.forEach(item => {
                    // Priority: Use job_url if available, otherwise fallback to cache_id
                    const key = (item.job_url && item.job_url.trim().length > 0)
                        ? item.job_url.trim()
                        : item.cache_id ? `cache_${item.cache_id}` : null;
                    
                    if (key) {
                        statusMap.set(key, item.status);
                    } else {
                        console.warn(`[JobHunter] Skipping item without job_url or cache_id:`, item);
                    }
                });
                
                // Only update state if we successfully loaded data
                // This ensures we don't accidentally clear existing state on error
                setApplicationStatusMap(statusMap);
                
                // Debug: Log application statuses for troubleshooting
                const appliedCount = response.items.filter(item => item.status === 'applied').length;
                console.log(
                    `[JobHunter] Loaded application statuses:`,
                    Object.keys(statusMap).length,
                    "entries",
                    "keys sample:",
                    Array.from(statusMap.keys()).slice(0, 3)
                );
                console.log(`[JobHunter] Loaded ${response.items.length} application statuses (${appliedCount} applied) for profile=${profileId}`);
                if (response.items.length > 0) {
                    console.log('[JobHunter] Application status map:', Object.fromEntries(statusMap));
                    // Log each item's key and status for debugging
                    response.items.forEach(item => {
                        const key = (item.job_url && item.job_url.trim().length > 0)
                            ? item.job_url.trim()
                            : item.cache_id ? `cache_${item.cache_id}` : 'N/A';
                        console.log(`[JobHunter] Status item: key=${key}, cache_id=${item.cache_id}, status=${item.status}, job_url=${item.job_url?.substring(0, 50)}`);
                    });
                } else {
                    console.log(`[JobHunter] No application statuses found for profile=${profileId}`);
                }
            } catch (err) {
                console.error('[JobHunter] Failed to load application statuses:', err);
                // CRITICAL: Don't clear existing state on error - keep what we have
                // This prevents accidental data loss if API call fails
                // Don't show error to user, just log it
            }
        };

        loadApplicationStatuses();
    }, [profileMode]);

    // Load resume whenever profile mode changes
    useEffect(() => {
        const loadResume = async () => {
            try {
                setResumeLoading(true);
                setResumeError(null);
                const profileId = getProfileIdForMode(profileMode);
                const text = await getUserResume(profileId);
                setResumeText(text || '');
            } catch (err) {
                const msg = err instanceof Error ? err.message : 'Failed to load resume';
                console.error('[JobHunter] Failed to load resume', err);
                setResumeError(msg);
            } finally {
                setResumeLoading(false);
            }
        };

        loadResume();
    }, [profileMode]);

    // Auto-scroll chat to bottom when messages change
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [careerChatMessages, careerChatLoading]);

    /**
     * Get match priority for sorting (higher number = higher priority).
     * Priority order:
     * 1. Applied jobs (highest priority)
     * 2. Category A > B > C > other/null
     * 3. Within same category, higher match_score is better
     * 4. Missing category/score = lowest priority
     */
    const getMatchPriority = (job: CachedJobAnalysis, applicationStatusMap: Map<string, ApplicationStatus>): number => {
        const statusKey = getJobStatusKey(job);
        const status = applicationStatusMap.get(statusKey);
        const isApplied = status === 'applied';
        
        // Applied jobs get highest priority (10000+)
        if (isApplied) {
            return 10000 + (job.match_score ?? 0);
        }
        
        // Category priority: A=1000, B=100, C=10, other/null=0
        let categoryPriority = 0;
        if (job.category === 'A') {
            categoryPriority = 1000;
        } else if (job.category === 'B') {
            categoryPriority = 100;
        } else if (job.category === 'C') {
            categoryPriority = 10;
        }
        
        // Add match_score (0-10) to category priority
        const score = job.match_score ?? 0;
        
        return categoryPriority + score;
    };

    // Filter and sort cached jobs based on user preferences
    // IMPORTANT: This is a pure filtering/sorting function that does NOT modify
    // applicationStatusMap or any other state. It only affects what is displayed.
    const visibleJobs = useMemo(() => {
        if (!cachedJobs || cachedJobs.length === 0) return [];

        // Create a copy to avoid mutating the original array
        let jobs = [...cachedJobs];

        // 1) View mode filter: "Top recommended" shows only category A with score >= 8 (≥80%)
        // match_score is 0-10 range, and we treat >=8 (which displays as ≥80%) as high fit
        // This filter is applied BEFORE other filters to ensure consistent behavior
        if (viewMode === 'top') {
            jobs = jobs.filter(job => {
                const score = job.match_score ?? 0;
                return job.category === 'A' && score >= 8;
            });
        }

        // 2) Only recommended: filter out auto_skip === true jobs
        // This filter only affects display, not the underlying data
        if (onlyRecommended) {
            jobs = jobs.filter(job => !job.autoSkip);
        }

        // 3) Only not applied: filter out jobs with status === 'applied'
        // CRITICAL: This only filters the display list. It does NOT modify
        // applicationStatusMap or delete any application records.
        if (onlyNotApplied) {
            jobs = jobs.filter(job => {
                const statusKey = getJobStatusKey(job);
                const status = applicationStatusMap.get(statusKey);
                // Show job if it doesn't have 'applied' status
                // This includes jobs with no status (undefined) and other statuses
                return status !== 'applied';
            });
        }

        // 4) Unified sorting rule (always applied, regardless of sortMode):
        // Priority 1: Applied jobs first
        // Priority 2: Category A > B > C > other/null
        // Priority 3: Within same category, higher match_score first
        // Missing category/score = lowest priority
        jobs.sort((a, b) => {
            const priorityA = getMatchPriority(a, applicationStatusMap);
            const priorityB = getMatchPriority(b, applicationStatusMap);
            return priorityB - priorityA; // Higher priority first
        });

        return jobs;
    }, [cachedJobs, viewMode, onlyRecommended, onlyNotApplied, applicationStatusMap, getJobStatusKey]);

    // ========================================
    // Resume Management Functions
    // ========================================
    const handleSaveResume = async () => {
        try {
            setResumeSaving(true);
            setResumeError(null);
            const profileId = getProfileIdForMode(profileMode);
            await saveUserResume(profileId, resumeText);
            message.success('简历已保存');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to save resume';
            console.error('[JobHunter] Failed to save resume', err);
            setResumeError(msg);
            message.error('保存简历失败');
        } finally {
            setResumeSaving(false);
        }
    };

    // ========================================
    // Helper: derive human-friendly Job title/company for header
    // ========================================
    const deriveJobHeader = (
        data: JDAnalysisResponse | null,
        fallback?: { title?: string | null; company?: string | null }
    ): { title: string; company: string } => {
        const anyData = data as any;
        const summary: any = data?.jd_summary || {};

        const metaTitle: string | undefined =
            anyData?.metadata?.job_title ||
            anyData?.metadata?.title ||
            summary?.job_title ||
            summary?.title;
        const metaCompany: string | undefined =
            anyData?.metadata?.company ||
            summary?.company;

        const title =
            metaTitle ||
            fallback?.title ||
            'Untitled job';

        const company =
            metaCompany ||
            fallback?.company ||
            'Unknown company';

        return { title, company };
    };

    // ========================================
    // Flow 1: JD 解读 + 适配度分析
    // ========================================
    const handleAnalyzeJD = async () => {
        try {
            const values = await form.validateFields(['jd_description']);
            setLoading(true);
            setAnalysisResult(null);
            setCurrentJobTitle(null);
            setCurrentJobCompany(null);
            setCurrentJobUrl(null);
            setChatHistory([]);  // 清空聊天历史，开始新的分析
            setSelectedCacheId(null);  // 清除缓存选中状态，因为这是新的分析

            const jdInput: JobJDInput = {
                description: values.jd_description,
                title: values.jd_title || undefined,
                company: values.jd_company || undefined,
                location: values.jd_location || undefined,
            };

            setCurrentJDInput(jdInput);

            // 连接后端 Flow 1 API
            // POST /api/jobhunter/analyze
            const res = await fetch(`${API_BASE_URL}/api/jobhunter/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jd_input: jdInput,
                    use_default_profile: true,  // 使用默认 profile 以生成 fit_summary
                    profile_mode: profileMode,
                }),
            });

            if (!res.ok) {
                throw new Error(`API request failed with status ${res.status}`);
            }

            const data: JDAnalysisResponse = await res.json();

            if (!data.ok) {
                throw new Error(data.error || 'Unknown error occurred');
            }

            // [Debug] Log constraints data to console for debugging
            if (data.constraints) {
                console.log('[JobHunter] Constraints received:', {
                    hard_block: data.constraints.hard_block,
                    hard_reasons: data.constraints.hard_reasons,
                    soft_flags: data.constraints.soft_flags,
                    reasons: data.constraints.reasons,
                });
            } else {
                console.log('[JobHunter] No constraints data in response');
            }

            // [Debug] Log spotlight stories evidence
            if (data.jd_summary?.spotlight_stories) {
                data.jd_summary.spotlight_stories.forEach((story, idx) => {
                    console.log(`[JobHunter] Story ${idx + 1} evidence_snippets:`, story.evidence_snippets?.length || 0);
                });
            }

            // [Debug] Log core signals
            if (data.jd_summary?.core_signals) {
                console.log(`[JobHunter] Core signals received:`, data.jd_summary.core_signals.length, data.jd_summary.core_signals);
            }
            if (data.jd_summary?.core_narrative) {
                console.log(`[JobHunter] Core narrative received:`, data.jd_summary.core_narrative.substring(0, 100));
            }

            setAnalysisResult(data);

            // Clear chat history when starting a new analysis
            setChatHistory([]);

            // Derive header title/company for this analysis
            const headerInfo = deriveJobHeader(data, {
                title: jdInput.title,
                company: jdInput.company,
            });
            setCurrentJobTitle(headerInfo.title);
            setCurrentJobCompany(headerInfo.company);

            // 添加到历史记录
            // 优先使用后端返回的 jd_summary 中的信息，因为后端可能会从 JD 文本中提取标题
            const newRecord: AnalyzedJDRecord = {
                id: `jd_${Date.now()}`,
                job_id: (data.jd_summary as any)?.job_id || jdInput.job_id,
                title: (data.jd_summary as any)?.title || jdInput.title || 'Untitled Job',
                company: (data.jd_summary as any)?.company || jdInput.company || 'Unknown Company',
                timestamp: new Date().toISOString(),
                match_score: data.fit_summary?.match_score,
                category: data.fit_summary?.category,
            };
            setAnalyzedJDList(prev => [newRecord, ...prev]);
            setSelectedJDId(newRecord.id);

            message.success('JD analysis completed!');
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            message.error(`Analysis failed: ${errorMessage}`);
            console.error('JD analysis error:', err);
        } finally {
            setLoading(false);
        }
    };

    // ========================================
    // Handle selecting a cached job from batch list
    // ========================================
    const handleSelectCachedJob = async (item: CachedJobAnalysis) => {
        if (!item.cache_id) {
            message.error('Invalid cache ID');
            return;
        }

        try {
            setCachedDetailLoading(true);
            setCachedDetailError(null);
            setSelectedCacheId(item.cache_id);
            setCurrentJobTitle(null);
            setCurrentJobCompany(null);
            setCurrentJobUrl(null);

            // Clear chat history when loading cached detail
            setChatHistory([]);

            // Clear career chat history when switching JD
            setCareerChatMessages([]);
            setCareerChatError(null);

            // Fetch detailed analysis from cache
            const detail: CachedJDDetail = await fetchCachedJDDetail(item.cache_id);

            // Convert cached detail to JDAnalysisResponse format
            // The backend returns analysis as a dict with jd_summary, fit_summary, constraints, graph_steps, cn_fast_read, etc.
            const analysisData: JDAnalysisResponse = {
                ok: true,
                jd_summary: detail.analysis.jd_summary,
                fit_summary: detail.analysis.fit_summary,
                constraints: detail.analysis.constraints,
                graph_steps: detail.analysis.graph_steps,
                cn_fast_read: detail.analysis.cn_fast_read,
            };

            // Set analysis result (same format as single JD analysis)
            setAnalysisResult(analysisData);

            // Check if deep analysis exists (has jd_summary, fit_summary, or constraints)
            // Also check if analysis_json is non-empty (not just empty dict)
            const analysis = detail.analysis || {};
            const hasAnalysis = !!(
                (analysisData.jd_summary && Object.keys(analysisData.jd_summary).length > 0) || 
                (analysisData.fit_summary && Object.keys(analysisData.fit_summary).length > 0) || 
                (analysisData.constraints && Object.keys(analysisData.constraints).length > 0) ||
                (analysis.core_signals && analysis.core_signals.length > 0) ||
                (analysis.lifecycle && Object.keys(analysis.lifecycle).length > 0) ||
                (analysis.spotlight_stories && analysis.spotlight_stories.length > 0)
            );
            setHasDeepAnalysis(hasAnalysis);

            // Derive header title/company prioritizing detail, then cached list item
            const summary: any = analysisData.jd_summary || {};
            const headerFromDetail = deriveJobHeader(analysisData, {
                title: detail.job_title || summary?.title || item.title,
                company: summary?.company || item.company,
            });
            setCurrentJobTitle(headerFromDetail.title);
            setCurrentJobCompany(headerFromDetail.company);
            // Set job_url from detail or item (treat empty strings as null)
            const detailUrl = detail.job_url && detail.job_url.trim() ? detail.job_url : null;
            const itemUrl = item.job_url && item.job_url.trim() ? item.job_url : null;
            setCurrentJobUrl(detailUrl || itemUrl || null);

            // Log debug info about core_signals
            if (analysisData.jd_summary?.core_signals) {
                console.log(`[JobHunter] Loaded cached core_signals:`, analysisData.jd_summary.core_signals.length);
            }
            if (analysisData.jd_summary?.core_narrative) {
                console.log(`[JobHunter] Loaded cached core_narrative:`, analysisData.jd_summary.core_narrative.substring(0, 100));
            }

            // Load quick view
            setQuickView(null);
            setQuickViewStructured(null);
            setQuickViewError(null);
            setQuickViewLoading(true);
            getQuickView(item.cache_id)
                .then((res) => {
                    if (res.error) {
                        setQuickViewError(res.error);
                        setQuickView(null);
                        setQuickViewStructured(null);
                    } else if (res.quick_view) {
                        // New structured format
                        setQuickViewStructured(res.quick_view);
                        // Also set legacy string format for backward compatibility
                        setQuickView(res.quick_view.cn_overview || res.quick_view_cn || null);
                        setQuickViewError(null);
                    } else if (res.quick_view_cn) {
                        // Legacy string format
                        setQuickView(res.quick_view_cn);
                        setQuickViewStructured(null);
                        setQuickViewError(null);
                    } else {
                        setQuickViewError(res.error || "Quick view not available yet, please try again later.");
                        setQuickView(null);
                        setQuickViewStructured(null);
                    }
                })
                .catch((err) => {
                    console.error("failed to load quick view", err);
                    const errorMsg = err instanceof Error ? err.message : "Failed to load quick view.";
                    setQuickViewError(errorMsg);
                    setQuickView(null);
                    setQuickViewStructured(null);
                })
                .finally(() => {
                    setQuickViewLoading(false);
                });

            // Store raw_text for potential deep analysis trigger
            // Note: We'll need to get this from detail if available, or fetch it separately

        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load cached analysis detail';
            console.error('[JobHunter] Failed to load cached detail:', err);
            setCachedDetailError(msg);
            message.error(msg);
            setSelectedCacheId(null);
        } finally {
            setCachedDetailLoading(false);
        }
    };

    // ========================================
    // Job Application Functions
    // ========================================
    const handleMarkApplicationStatus = async (job: CachedJobAnalysis, status: ApplicationStatus, e?: React.MouseEvent) => {
        if (e) {
            e.stopPropagation(); // Prevent triggering List.Item onClick
        }

        try {
            setUpdatingApplicationId(job.cache_id);
            const profileId = getProfileIdForMode(profileMode);
            await upsertJobApplication({
                profileId,
                cacheId: job.cache_id,
                status,
            });

            // Update local status map using job_url-based key
            // CRITICAL: Use functional update to preserve all other entries
            // This ensures we don't accidentally lose other application statuses
            const statusKey = getJobStatusKey(job);
            setApplicationStatusMap(prev => {
                const newMap = new Map(prev);
                newMap.set(statusKey, status);
                console.log(`[JobHunter] Mark applied:`, statusKey, job.job_title, job.job_url);
                console.log(`[JobHunter] Updated application status: statusKey=${statusKey}, cache_id=${job.cache_id}, status=${status}, total entries=${newMap.size}`);
                return newMap;
            });

            const statusText = {
                'applied': 'Applied',
                'interviewing': 'Interviewing',
                'offer': 'Offer',
                'rejected': 'Rejected',
                'skipped': 'Skipped',
                'planned': 'Planned',
            }[status] || status;

            message.success(`Marked as: ${statusText}`);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to mark application';
            console.error('[JobHunter] Failed to mark application status:', err);
            message.error(msg);
        } finally {
            setUpdatingApplicationId(null);
        }
    };

    const handleRunDeepAnalysis = async () => {
        if (!selectedCacheId) {
            message.warning('Please select a job first');
            return;
        }

        try {
            setDeepAnalysisLoading(true);
            const profileId = getProfileIdForMode(profileMode);

            // Call new analyze_cached API endpoint
            await runFullAnalysisForCacheId(selectedCacheId, profileId);

            // Reload cached detail to get updated analysis
            const updatedDetail: CachedJDDetail = await fetchCachedJDDetail(selectedCacheId);
            const updatedAnalysisData: JDAnalysisResponse = {
                ok: true,
                jd_summary: updatedDetail.analysis.jd_summary,
                fit_summary: updatedDetail.analysis.fit_summary,
                constraints: updatedDetail.analysis.constraints,
                graph_steps: updatedDetail.analysis.graph_steps,
                cn_fast_read: updatedDetail.analysis.cn_fast_read,
            };
            setAnalysisResult(updatedAnalysisData);

            // Check if deep analysis exists (has jd_summary, fit_summary, or constraints)
            const hasAnalysis = !!(
                updatedAnalysisData.jd_summary || 
                updatedAnalysisData.fit_summary || 
                updatedAnalysisData.constraints
            );
            setHasDeepAnalysis(hasAnalysis);

            message.success('Deep analysis completed!');

        } catch (err) {
            console.error('Failed to run deep analysis:', err);
            const errorMsg = err instanceof Error ? err.message : 'Failed to run deep analysis';
            message.error(errorMsg);
        } finally {
            setDeepAnalysisLoading(false);
        }
    };

    const handleUnmarkApplicationStatus = async (job: CachedJobAnalysis, e?: React.MouseEvent) => {
        if (e) {
            e.stopPropagation(); // Prevent triggering List.Item onClick
        }

        // Show confirmation dialog for all unmark operations
        const confirmed = window.confirm(
            "Are you sure you want to clear the application status for this job?"
        );

        if (!confirmed) {
            return; // User cancelled, do nothing
        }

        try {
            setUpdatingApplicationId(job.cache_id);
            const profileId = getProfileIdForMode(profileMode);
            await deleteJobApplication({
                profileId,
                cacheId: job.cache_id,
            });

            // Remove from local status map using job_url-based key
            // CRITICAL: Use functional update to preserve all other entries
            // This ensures we don't accidentally lose other application statuses
            const statusKey = getJobStatusKey(job);
            setApplicationStatusMap(prev => {
                const newMap = new Map(prev);
                newMap.delete(statusKey);
                console.log(`[JobHunter] Unmark applied:`, statusKey, job.job_title, job.job_url);
                console.log(`[JobHunter] Removed application status: statusKey=${statusKey}, cache_id=${job.cache_id}, remaining entries=${newMap.size}`);
                return newMap;
            });

            message.success('Application status removed');
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to remove application status';
            console.error('[JobHunter] Failed to unmark application status:', err);
            message.error(msg);
        } finally {
            setUpdatingApplicationId(null);
        }
    };

    // ========================================
    // Career Coach Chat Functions
    // ========================================
    const handleSendCareerChat = async (forcedQuestion?: string, forcedTopic?: CareerChatTopic) => {
        console.log('[JobHunter] handleSendCareerChat called', { forcedQuestion, careerChatInput, selectedCacheId });

        // 1) 没选 JD：直接设置 careerChatError 并返回
        if (!selectedCacheId) {
            setCareerChatError('请先在左侧选择一条职位（JD）。');
            return;
        }

        // 2) 获取问题：优先使用 forcedQuestion，否则使用 careerChatInput
        const question = (forcedQuestion ?? careerChatInput).trim();
        if (!question) {
            console.warn('[JobHunter] handleSendCareerChat: question is empty', { forcedQuestion, careerChatInput });
            setCareerChatError('请输入问题内容');
            return;
        }

        console.log('[JobHunter] handleSendCareerChat: proceeding with question', { question, topic: forcedTopic ?? careerChatTopic });

        // 3) 获取 topic：优先使用 forcedTopic，否则使用当前的 careerChatTopic
        const topic = forcedTopic ?? careerChatTopic;

        const profileId = getProfileIdForMode(profileMode);
        const userMsg: CareerChatMessage = { role: 'user', content: question };

        // 4) 本地先把消息 push 到 careerChatMessages 里（乐观更新）
        const oldMessages = [...careerChatMessages];
        const nextMessages = [...careerChatMessages, userMsg];
        setCareerChatMessages(nextMessages);
        // 只有在使用 careerChatInput 时才清空输入框（如果是 forcedQuestion，不清空）
        if (!forcedQuestion) {
            setCareerChatInput('');
        }
        setCareerChatLoading(true);
        setCareerChatError(null);

        try {
            // 5) 调用 sendCareerChat
            const res = await sendCareerChat({
                profileId,
                cacheId: selectedCacheId,
                topic: topic,
                messages: nextMessages,
            });

            // 6) 根据返回处理
            if (!res.ok || !res.answer) {
                const errorMsg = res.error || 'Career chat failed';
                // 恢复到旧消息
                setCareerChatMessages(oldMessages);
                setCareerChatError(errorMsg);
                message.error('对话失败，请稍后重试');
                return;
            }

            // ok=true：用 response.messages 覆盖本地 careerChatMessages
            // 注意：后端返回的是 answer，我们需要手动构建完整的消息列表
            const assistantMsg: CareerChatMessage = { role: 'assistant', content: res.answer };
            setCareerChatMessages([...nextMessages, assistantMsg]);
        } catch (err) {
            // 出错/异常：恢复到旧消息，设置错误
            const msg = err instanceof Error ? err.message : '对话服务出错，请稍后再试。';
            console.error('[JobHunter] Career chat failed', err);
            setCareerChatMessages(oldMessages);
            setCareerChatError(msg);
            message.error('对话失败，请稍后重试');
        } finally {
            setCareerChatLoading(false);
        }
    };

    // ========================================
    // Flow 2: 多轮职业教练对话
    // ========================================
    const handleSendChatMessage = async () => {
        if (!currentChatInput.trim()) {
            return;
        }

        if (!analysisResult?.jd_summary) {
            message.warning('Please analyze a JD first before starting a conversation');
            return;
        }

        try {
            setChatLoading(true);

            const userMessage: ChatMessage = {
                role: 'user',
                content: currentChatInput.trim(),
                timestamp: new Date().toISOString(),
            };

            const updatedHistory = [...chatHistory, userMessage];
            setChatHistory(updatedHistory);
            setCurrentChatInput('');

            // Call backend Flow 2 API
            // POST /api/jobhunter/chat
            const res = await fetch(`${API_BASE_URL}/api/jobhunter/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jd_summary: analysisResult.jd_summary,
                    fit_summary: analysisResult.fit_summary || null,
                    messages: updatedHistory.map(m => ({ role: m.role, content: m.content })),
                    use_default_profile: true,
                    profile_mode: profileMode,
                }),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.detail || `API request failed with status ${res.status}`);
            }

            const data: JDChatResponse = await res.json();

            // Update chat history with the complete message list from backend
            const updatedMessages: ChatMessage[] = data.messages.map(msg => ({
                role: msg.role,
                content: msg.content,
                timestamp: new Date().toISOString(),
            }));

            setChatHistory(updatedMessages);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            message.error(`Failed to send message: ${errorMessage}`);
            console.error('Chat error:', err);

            // Add error message to chat
            const errorChatMessage: ChatMessage = {
                role: 'assistant',
                content: 'Sorry, something went wrong while answering this question.',
                timestamp: new Date().toISOString(),
            };
            setChatHistory([...chatHistory, errorChatMessage]);
        } finally {
            setChatLoading(false);
        }
    };

    // 获取分类标签颜色
    const getCategoryColor = (category?: 'A' | 'B' | 'C') => {
        switch (category) {
            case 'A':
                return 'success';
            case 'B':
                return 'warning';
            case 'C':
                return 'error';
            default:
                return 'default';
        }
    };

    // 获取推荐标签颜色
    const getRecommendationColor = (rec?: 'APPLY' | 'MAYBE' | 'SKIP') => {
        switch (rec) {
            case 'APPLY':
                return 'success';
            case 'MAYBE':
                return 'warning';
            case 'SKIP':
                return 'error';
            default:
                return 'default';
        }
    };

    return (
        <div style={{ padding: '24px', height: '100vh', overflow: 'auto' }}>
            <Title level={2} style={{ marginBottom: '8px' }}>
                <SearchOutlined /> JobHunter Agent
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                AI Career Coach: Interpret job descriptions, analyze fit, and provide career advice
            </Paragraph>

            <Row gutter={24} style={{ height: 'calc(100vh - 150px)' }}>
                {/* ========================================
                    左侧栏：已分析的 JD 历史记录列表（可折叠）
                    ======================================== */}
                <Col
                    xs={24}
                    lg={isHistoryCollapsed ? 2 : 6}
                    style={{
                        transition: 'all 0.2s ease-in-out',
                        width: isHistoryCollapsed ? '28px' : undefined,
                        flex: isHistoryCollapsed ? '0 0 28px' : undefined,
                        minWidth: isHistoryCollapsed ? '28px' : undefined,
                        maxWidth: isHistoryCollapsed ? '28px' : undefined,
                    }}
                >
                    <div
                        style={{
                            height: '100%',
                            borderRight: '1px solid #262626',
                            backgroundColor: 'rgba(10, 10, 10, 0.6)',
                            display: 'flex',
                            flexDirection: 'column',
                            transition: 'all 0.2s ease-in-out',
                            width: isHistoryCollapsed ? '28px' : '288px',
                            minWidth: isHistoryCollapsed ? '28px' : '260px',
                        }}
                    >
                        {isHistoryCollapsed ? (
                            // Collapsed: show vertical History bar
                            <button
                                type="button"
                                onClick={() => setIsHistoryCollapsed(false)}
                                style={{
                                    flex: 1,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '10px',
                                    letterSpacing: '0.05em',
                                    color: '#d4d4d4',
                                    backgroundColor: 'transparent',
                                    border: 'none',
                                    cursor: 'pointer',
                                    writingMode: 'vertical-rl',
                                    textOrientation: 'mixed',
                                    transform: 'rotate(180deg)',
                                    padding: '8px 4px',
                                    transition: 'all 0.2s ease-in-out',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.color = '#fff';
                                    e.currentTarget.style.backgroundColor = 'rgba(38, 38, 38, 0.8)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.color = '#d4d4d4';
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                            >
                                History ▸
                            </button>
                        ) : (
                            // Expanded: show header and list
                            <>
                                <div
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        gap: '8px',
                                        padding: '8px 12px',
                                        borderBottom: '1px solid #262626',
                                    }}
                                >
                                    <span
                                        style={{
                                            fontSize: '12px',
                                            fontWeight: 500,
                                            color: '#e5e5e5',
                                        }}
                                    >
                                        Analysis History
                                    </span>
                                    <button
                                        type="button"
                                        onClick={() => setIsHistoryCollapsed(true)}
                                        style={{
                                            fontSize: '11px',
                                            color: '#a3a3a3',
                                            backgroundColor: 'transparent',
                                            border: 'none',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '4px 8px',
                                            borderRadius: '4px',
                                            transition: 'all 0.2s ease-in-out',
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.color = '#fff';
                                            e.currentTarget.style.backgroundColor = 'rgba(38, 38, 38, 0.5)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.color = '#a3a3a3';
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }}
                                    >
                                        ◂ Hide
                                    </button>
                                </div>
                                <div
                                    style={{
                                        flex: 1,
                                        overflowY: 'auto',
                                        padding: '8px',
                                    }}
                                >
                                    {/* Session-only analysis history (in-memory for this tab) */}
                                    {analyzedJDList.length === 0 ? (
                                        <Empty
                                            description="No analysis records"
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            style={{ marginTop: '24px' }}
                                        />
                                    ) : (
                                        <List
                                            dataSource={analyzedJDList}
                                            renderItem={(item) => (
                                                <List.Item
                                                    style={{
                                                        cursor: 'pointer',
                                                        backgroundColor:
                                                            selectedJDId === item.id ? '#1890ff20' : 'transparent',
                                                        borderRadius: '4px',
                                                        padding: '12px',
                                                        marginBottom: '8px',
                                                    }}
                                                    onClick={() => setSelectedJDId(item.id)}
                                                >
                                                    <div style={{ width: '100%' }}>
                                                        <div style={{ marginBottom: '4px' }}>
                                                            <Text strong>{item.title}</Text>
                                                        </div>
                                                        <div style={{ marginBottom: '4px' }}>
                                                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                                                {item.company}
                                                            </Text>
                                                        </div>
                                                        <div>
                                                            {item.category && (
                                                                <Tag color={getCategoryColor(item.category)} size="small">
                                                                    {item.category}
                                                                </Tag>
                                                            )}
                                                            {item.match_score !== undefined && (
                                                                <Tag color="blue" size="small">
                                                                    Match: {item.match_score}/10
                                                                </Tag>
                                                            )}
                                                        </div>
                                                        <div style={{ marginTop: '4px' }}>
                                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                                {new Date(item.timestamp).toLocaleString()}
                                                            </Text>
                                                        </div>
                                                    </div>
                                                </List.Item>
                                            )}
                                        />
                                    )}

                                    <Divider style={{ margin: '12px 0', borderColor: '#262626' }}>
                                        <span style={{ fontSize: '11px', color: '#a3a3a3' }}>
                                            Batch Results (from cache)
                                        </span>
                                    </Divider>

                                    {/* Summary Statistics Bar */}
                                    {!cacheLoading && !cacheError && cachedJobs.length > 0 && (() => {
                                        // Calculate statistics from cachedJobs and applicationStatusMap
                                        // NOTE: This summary bar only displays existing cached data, no new API calls
                                        const totalJobs = cachedJobs.length;
                                        // match_score is 0-10 range, and we treat >=8 (which displays as ≥80%) as "High fit (A, ≥80)"
                                        const highFitJobs = cachedJobs.filter(job => {
                                            const score = job.match_score ?? 0;
                                            return job.category === 'A' && score >= 8;
                                        }).length;
                                        const appliedJobs = Array.from(applicationStatusMap.values()).filter(
                                            status => status === 'applied'
                                        ).length;
                                        const autoSkippedJobs = cachedJobs.filter(job => job.autoSkip === true).length;
                                        
                                        return (
                                            <div style={{ 
                                                marginBottom: '12px', 
                                                padding: '8px 12px', 
                                                backgroundColor: 'rgba(255, 255, 255, 0.03)',
                                                borderRadius: '4px',
                                                fontSize: '12px',
                                                color: '#bfbfbf'
                                            }}>
                                                <Text style={{ fontSize: '12px', color: '#bfbfbf' }}>
                                                    Total jobs: <strong style={{ color: '#fff' }}>{totalJobs}</strong>
                                                    {' · '}
                                                    High fit (A, ≥80): <strong style={{ color: '#52c41a' }}>{highFitJobs}</strong>
                                                    {' · '}
                                                    Applied: <strong style={{ color: '#1890ff' }}>{appliedJobs}</strong>
                                                    {' · '}
                                                    Auto-skipped: <strong style={{ color: '#ff4d4f' }}>{autoSkippedJobs}</strong>
                                                </Text>
                                            </div>
                                        );
                                    })()}

                                    {/* Filter and sort controls */}
                                    {!cacheLoading && !cacheError && cachedJobs.length > 0 && (
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                                            {/* View mode toggle: All jobs vs Top recommended */}
                                            <Select
                                                size="small"
                                                value={viewMode}
                                                style={{ width: 160, fontSize: '11px' }}
                                                onChange={value => setViewMode(value)}
                                                options={[
                                                    { label: 'View: All jobs', value: 'all' },
                                                    { label: 'View: Top recommended', value: 'top' },
                                                ]}
                                            />

                                            <Checkbox
                                                checked={onlyRecommended}
                                                onChange={e => setOnlyRecommended(e.target.checked)}
                                                style={{ fontSize: '11px', color: '#bfbfbf' }}
                                            >
                                                Only recommended
                                            </Checkbox>

                                            <Checkbox
                                                checked={onlyNotApplied}
                                                onChange={e => setOnlyNotApplied(e.target.checked)}
                                                style={{ fontSize: '11px', color: '#bfbfbf' }}
                                            >
                                                Only not applied
                                            </Checkbox>
                                        </div>
                                    )}

                                    {/* Batch results backed by backend SQLite cache via /api/jobhunter/cache (no live LLM calls) */}
                                    {(cacheLoading || cachedDetailLoading) && (
                                        <div style={{ textAlign: 'center', padding: '12px 0', color: '#bfbfbf', fontSize: '12px' }}>
                                            <Spin size="small" />
                                            <span style={{ marginLeft: 8 }}>
                                                {cachedDetailLoading ? 'Loading job details…' : 'Loading cached jobs…'}
                                            </span>
                                        </div>
                                    )}
                                    {cacheError && (
                                        <Alert
                                            type="error"
                                            showIcon
                                            message="Failed to load cached jobs"
                                            description={cacheError}
                                            style={{ marginBottom: '8px' }}
                                        />
                                    )}
                                    {cachedDetailError && (
                                        <Alert
                                            type="error"
                                            showIcon
                                            message="Failed to load cached detail"
                                            description={cachedDetailError}
                                            style={{ marginBottom: '8px' }}
                                        />
                                    )}
                                    {!cacheLoading && !cacheError && cachedJobs.length === 0 && (
                                        <Empty
                                            description="No cached batch results"
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            style={{ marginTop: '8px' }}
                                        />
                                    )}
                                    {!cacheLoading && !cacheError && cachedJobs.length > 0 && visibleJobs.length === 0 && (
                                        <Empty
                                            description="No jobs match the current filters"
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            style={{ marginTop: '8px' }}
                                        />
                                    )}
                                    {!cacheLoading && !cacheError && cachedJobs.length > 0 && visibleJobs.length > 0 && (
                                        <List
                                            size="small"
                                            dataSource={visibleJobs}
                                            renderItem={(item, index) => {
                                                const score = item.match_score ?? 0;
                                                const scorePct = Math.max(
                                                    0,
                                                    Math.min(100, Math.round(score * 10))
                                                );
                                                const isSelected = selectedCacheId === item.cache_id;
                                                const indexNumber = String(index + 1).padStart(2, '0');
                                                const isAutoSkipped = item.autoSkip === true;
                                                // Use job_url-based key for status lookup
                                                const statusKey = getJobStatusKey(item);
                                                const status = applicationStatusMap.get(statusKey);
                                                if (index < 5 || status) { // Log first 5 items or items with status
                                                    console.log(`[JobHunter] Row ${index}: statusKey=${statusKey}, cache_id=${item.cache_id}, status=${status}, job_title=${item.job_title?.substring(0, 50)}`);
                                                }
                                                return (
                                                    <List.Item
                                                        onClick={() => handleSelectCachedJob(item)}
                                                        style={{
                                                            padding: '8px 8px',
                                                            marginBottom: '4px',
                                                            borderRadius: '4px',
                                                            backgroundColor: isSelected ? 'rgba(24, 144, 255, 0.15)' : 'transparent',
                                                            border: isSelected ? '1px solid #1890ff' : '1px solid transparent',
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s',
                                                            opacity: isAutoSkipped ? 0.45 : 1,
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            if (!isSelected) {
                                                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                                                            }
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            if (!isSelected) {
                                                                e.currentTarget.style.backgroundColor = 'transparent';
                                                            }
                                                        }}
                                                    >
                                                        <List.Item.Meta
                                                            title={
                                                                <div
                                                                    style={{
                                                                        display: 'flex',
                                                                        justifyContent: 'space-between',
                                                                        alignItems: 'center',
                                                                    }}
                                                                >
                                                                    <span
                                                                        style={{
                                                                            color: '#e5e5e5',
                                                                            fontSize: '12px',
                                                                        }}
                                                                    >
                                                                        <span
                                                                            style={{
                                                                                color: '#8c8c8c',
                                                                                fontSize: '11px',
                                                                                marginRight: '6px',
                                                                                fontFamily: 'monospace',
                                                                            }}
                                                                        >
                                                                            {indexNumber}
                                                                        </span>
                                                                        {item.company} · {item.title}
                                                                    </span>
                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                                        {isAutoSkipped && (
                                                                            <Tooltip
                                                                                title={
                                                                                    item.autoSkipReasons && item.autoSkipReasons.length > 0
                                                                                        ? `Reasons: ${item.autoSkipReasons.join(', ')}`
                                                                                        : 'Low fit'
                                                                                }
                                                                            >
                                                                                <Tag 
                                                                                    color="orange" 
                                                                                    size="small" 
                                                                                    style={{ 
                                                                                        fontSize: '10px',
                                                                                        fontWeight: '500',
                                                                                        opacity: 0.9
                                                                                    }}
                                                                                >
                                                                                    Low fit
                                                                                </Tag>
                                                                            </Tooltip>
                                                                        )}
                                                                        <Tag
                                                                            color={getCategoryColor(
                                                                                item.category as any
                                                                            )}
                                                                        >
                                                                            {item.category || '-'} · {scorePct}%
                                                                        </Tag>
                                                                    </div>
                                                                </div>
                                                            }
                                                            description={
                                                                <div
                                                                    style={{
                                                                        display: 'flex',
                                                                        justifyContent: 'space-between',
                                                                        alignItems: 'center',
                                                                        gap: '8px',
                                                                    }}
                                                                >
                                                                    <span
                                                                        style={{
                                                                            color: '#737373',
                                                                            fontSize: '11px',
                                                                        }}
                                                                    >
                                                                        {item.recommendation || '—'}
                                                                    </span>
                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                                        {status && (
                                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                                                <Tag
                                                                                    color={
                                                                                        status === 'applied' ? 'green' :
                                                                                            status === 'interviewing' ? 'blue' :
                                                                                                status === 'offer' ? 'gold' :
                                                                                                    'default'
                                                                                    }
                                                                                    style={{ fontSize: '10px', margin: 0 }}
                                                                                >
                                                                                    {status === 'applied' ? 'Applied' :
                                                                                        status === 'interviewing' ? 'Interviewing' :
                                                                                            status === 'offer' ? 'Offer' :
                                                                                                status === 'rejected' ? 'Rejected' :
                                                                                                    status === 'skipped' ? 'Skipped' :
                                                                                                        status === 'planned' ? 'Planned' :
                                                                                                            status}
                                                                                </Tag>
                                                                                {status === 'applied' && (
                                                                                    <Button
                                                                                        type="link"
                                                                                        size="small"
                                                                                        loading={updatingApplicationId === item.cache_id}
                                                                                        onClick={(e) => handleUnmarkApplicationStatus(item, e)}
                                                                                        style={{
                                                                                            fontSize: '10px',
                                                                                            height: '18px',
                                                                                            padding: '0 4px',
                                                                                            color: '#8c8c8c',
                                                                                        }}
                                                                                    >
                                                                                        Unmark
                                                                                    </Button>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        {!status && (
                                                                            <Button
                                                                                type="link"
                                                                                size="small"
                                                                                loading={updatingApplicationId === item.cache_id}
                                                                                onClick={(e) => handleMarkApplicationStatus(item, 'applied', e)}
                                                                                style={{
                                                                                    fontSize: '11px',
                                                                                    height: '20px',
                                                                                    padding: '0 4px',
                                                                                    color: '#1890ff',
                                                                                }}
                                                                            >
                                                                                Mark as Applied
                                                                            </Button>
                                                                        )}
                                                                        <span
                                                                            style={{
                                                                                color: '#525252',
                                                                                fontSize: '11px',
                                                                            }}
                                                                        >
                                                                            {item.last_analyzed_at
                                                                                ? new Date(
                                                                                    item.last_analyzed_at
                                                                                ).toLocaleString()
                                                                                : ''}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            }
                                                        />
                                                    </List.Item>
                                                );
                                            }}
                                        />
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </Col>

                {/* ========================================
                    中间栏：JD 输入框 + 聊天对话区域
                    （在折叠时整体隐藏列，以让右侧占满空间）
                    ======================================== */}
                {!isSearchPanelCollapsed && (
                    <Col xs={24} lg={8}>
                        <Card
                            title={
                                <Space>
                                    <FileTextOutlined />
                                    <span>JD Input & Analysis</span>
                                </Space>
                            }
                            bordered={false}
                            style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}
                            bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '16px', overflow: 'auto' }}
                        >
                            <>
                                <Form
                                    form={form}
                                    layout="vertical"
                                    initialValues={{
                                        jd_description: '',
                                        jd_title: '',
                                        jd_company: '',
                                        jd_location: '',
                                    }}
                                    style={{
                                        flex: 'none',
                                        marginBottom: '16px',
                                    }}
                                >
                                    <Form.Item
                                        label="Profile"
                                    >
                                        <Radio.Group
                                            value={profileMode}
                                            onChange={(e) => setProfileMode(e.target.value)}
                                            optionType="button"
                                            buttonStyle="solid"
                                        >
                                            <Radio.Button value="agent">LLM / Agent Engineer</Radio.Button>
                                            <Radio.Button value="data_eng">Data Engineer (GCP)</Radio.Button>
                                        </Radio.Group>
                                    </Form.Item>

                                    <Form.Item
                                        name="jd_title"
                                        label="Job Title (Optional)"
                                    >
                                        <Input placeholder="e.g., Senior Software Engineer" />
                                    </Form.Item>

                                    <Form.Item
                                        name="jd_company"
                                        label="Company Name (Optional)"
                                    >
                                        <Input placeholder="e.g., Anthropic" />
                                    </Form.Item>

                                    <Form.Item
                                        name="jd_location"
                                        label="Location (Optional)"
                                    >
                                        <Input placeholder="e.g., San Francisco, CA or Remote" />
                                    </Form.Item>

                                    <Form.Item
                                        name="jd_description"
                                        label="Job Description (Required)"
                                        rules={[{ required: true, message: 'Please enter job description' }]}
                                    >
                                        <TextArea
                                            autoSize={{ minRows: 10, maxRows: 24 }}
                                            placeholder="Paste the complete job description (JD) content..."
                                            style={{ minHeight: '220px' }}
                                        />
                                    </Form.Item>

                                    <Form.Item style={{ marginTop: '16px', marginBottom: '0' }}>
                                        <Button
                                            type="primary"
                                            size="large"
                                            onClick={handleAnalyzeJD}
                                            loading={loading}
                                            block
                                            icon={<SearchOutlined />}
                                            style={{
                                                height: '48px',
                                                fontSize: '16px',
                                                fontWeight: 'bold'
                                            }}
                                        >
                                            🔍 Analyze JD
                                        </Button>
                                    </Form.Item>
                                </Form>

                                {/* Resume Management Card */}
                                <Card
                                    title="Your Resume / 我的简历（当前 profile）"
                                    size="small"
                                    style={{
                                        marginTop: 16,
                                        marginBottom: 16,
                                        backgroundColor: '#141414',
                                        borderColor: '#434343'
                                    }}
                                    headStyle={{
                                        backgroundColor: '#141414',
                                        borderColor: '#434343',
                                        color: '#e5e5e5'
                                    }}
                                >
                                    {resumeLoading ? (
                                        <div style={{ textAlign: 'center', padding: '20px' }}>
                                            <Spin />
                                        </div>
                                    ) : (
                                        <>
                                            {resumeError && (
                                                <Alert
                                                    type="error"
                                                    showIcon
                                                    message="加载简历失败"
                                                    description={resumeError}
                                                    style={{ marginBottom: 8 }}
                                                />
                                            )}
                                            <TextArea
                                                value={resumeText}
                                                onChange={(e) => setResumeText(e.target.value)}
                                                autoSize={{ minRows: 8, maxRows: 15 }}
                                                placeholder="在这里输入或编辑你的简历内容..."
                                                style={{
                                                    marginBottom: 8,
                                                    backgroundColor: '#1a1a1a',
                                                    borderColor: '#434343',
                                                    color: '#e5e5e5'
                                                }}
                                            />
                                            <Button
                                                type="primary"
                                                onClick={handleSaveResume}
                                                loading={resumeSaving}
                                                block
                                            >
                                                保存简历
                                            </Button>
                                        </>
                                    )}
                                </Card>
                            </>
                        </Card>
                    </Col>
                )}

                {/* ========================================
                    右侧栏：JD 分析结果详情
                    （金银铜要点、适配度、优势/缺口等）
                    ======================================== */}
                <Col
                    xs={24}
                    lg={
                        isSearchPanelCollapsed
                            ? (isHistoryCollapsed ? 22 : 16)
                            : (isHistoryCollapsed ? 14 : 10)
                    }
                >
                    <Card
                        title={
                            <Space style={{ width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Space>
                                    <FileTextOutlined />
                                    <span>Analysis Results</span>
                                    <Tag color={profileMode === "agent" ? "blue" : "green"}>
                                        {profileMode === "agent" ? "Profile: LLM / Agent" : "Profile: Data Engineer (GCP)"}
                                    </Tag>
                                </Space>
                                <Button
                                    size="small"
                                    type="default"
                                    onClick={() => setIsSearchPanelCollapsed(!isSearchPanelCollapsed)}
                                >
                                    {isSearchPanelCollapsed ? 'Show input panel' : 'Hide input panel'}
                                </Button>
                            </Space>
                        }
                        bordered={false}
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, overflow: 'auto', padding: '20px 20px 16px' }}
                    >
                        {loading && (
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                <Spin size="large" />
                                <div style={{ marginTop: '16px' }}>Analyzing JD...</div>
                            </div>
                        )}

                        {!loading && !analysisResult && (
                            <Empty
                                description="Please input and analyze a JD first"
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                                style={{ marginTop: '40px' }}
                            />
                        )}

                        {!loading && analysisResult && (
                            <div>
                                {(currentJobTitle || currentJobCompany) && (
                                    <div
                                        style={{
                                            marginBottom: 16,
                                            padding: '8px 12px',
                                            borderRadius: 6,
                                            backgroundColor: '#111111',
                                            border: '1px solid #262626',
                                        }}
                                    >
                                        {currentJobTitle && (
                                            <Title
                                                level={4}
                                                style={{
                                                    margin: 0,
                                                    color: '#ffffff',
                                                    fontSize: 18,
                                                    lineHeight: 1.4,
                                                }}
                                            >
                                                {currentJobTitle}
                                            </Title>
                                        )}
                                        {currentJobCompany && (
                                            <Text
                                                type="secondary"
                                                style={{
                                                    display: 'block',
                                                    marginTop: 4,
                                                    color: '#bfbfbf',
                                                    fontSize: 14,
                                                }}
                                            >
                                                {currentJobCompany}
                                            </Text>
                                        )}
                                        {currentJobUrl && currentJobUrl.trim() && (
                                            <a
                                                href={currentJobUrl}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                style={{
                                                    display: 'block',
                                                    marginTop: 8,
                                                    color: '#1890ff',
                                                    fontSize: 13,
                                                    textDecoration: 'none',
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.textDecoration = 'underline';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.textDecoration = 'none';
                                                }}
                                            >
                                                🔗 View Job Posting
                                            </a>
                                        )}
                                    </div>
                                )}

                                {/* Run Full Analysis Button */}
                                {selectedCacheId && (
                                    <div style={{ marginBottom: 12 }}>
                                        {!hasDeepAnalysis ? (
                                            <Button
                                                type="primary"
                                                size="large"
                                                loading={deepAnalysisLoading}
                                                onClick={handleRunDeepAnalysis}
                                                block
                                                style={{
                                                    height: 40,
                                                    fontSize: 15,
                                                    fontWeight: 500,
                                                }}
                                            >
                                                {deepAnalysisLoading ? 'Running full analysis...' : 'Run full analysis / 运行深度分析'}
                                            </Button>
                                        ) : (
                                            <Button
                                                disabled
                                                size="large"
                                                block
                                                style={{
                                                    height: 40,
                                                    fontSize: 15,
                                                    fontWeight: 500,
                                                }}
                                            >
                                                Full analysis ready / 已完成深度分析
                                            </Button>
                                        )}
                                    </div>
                                )}

                                {/* Quick View / 快速概览 Card */}
                                {selectedCacheId && (
                                    <div
                                        style={{
                                            marginBottom: 12,
                                            padding: 16,
                                            borderRadius: 6,
                                            backgroundColor: '#141414',
                                            border: '1px solid #434343',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                            <span style={{ fontSize: 15, fontWeight: 600, color: '#d9d9d9' }}>
                                                Quick View / 快速概览
                                            </span>
                                            {quickViewLoading && (
                                                <span style={{ fontSize: 10, color: '#8c8c8c' }}>Loading...</span>
                                            )}
                                        </div>
                                        {quickViewError && (
                                            <div style={{ fontSize: 12, color: '#ff4d4f' }}>
                                                {quickViewError}
                                            </div>
                                        )}
                                        {!quickViewError && !quickViewLoading && (quickViewStructured || quickView) && (
                                            <div style={{ fontSize: 15, color: '#d9d9d9', lineHeight: 1.7 }}>
                                                {quickViewStructured ? (
                                                    <div>
                                                        {/* Overview */}
                                                        {quickViewStructured.cn_overview && (
                                                            <div style={{ marginBottom: 14, fontSize: 15, lineHeight: 1.7 }}>
                                                                {quickViewStructured.cn_overview}
                                                            </div>
                                                        )}
                                                        {/* Responsibilities */}
                                                        {quickViewStructured.responsibilities && quickViewStructured.responsibilities.length > 0 && (
                                                            <div style={{ marginBottom: 14 }}>
                                                                <div style={{ fontWeight: 600, marginBottom: 6, color: '#bfbfbf', fontSize: 15 }}>主要职责：</div>
                                                                <ul style={{ margin: 0, paddingLeft: 22 }}>
                                                                    {quickViewStructured.responsibilities.map((item, idx) => (
                                                                        <li key={idx} style={{ marginBottom: 6, fontSize: 15, lineHeight: 1.7 }}>{item}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                        {/* Requirements */}
                                                        {quickViewStructured.requirements && quickViewStructured.requirements.length > 0 && (
                                                            <div style={{ marginBottom: 14 }}>
                                                                <div style={{ fontWeight: 600, marginBottom: 6, color: '#bfbfbf', fontSize: 15 }}>硬性要求：</div>
                                                                <ul style={{ margin: 0, paddingLeft: 22 }}>
                                                                    {quickViewStructured.requirements.map((item, idx) => (
                                                                        <li key={idx} style={{ marginBottom: 6, fontSize: 15, lineHeight: 1.7 }}>{item}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                        {/* Red Flags */}
                                                        {quickViewStructured.red_flags && quickViewStructured.red_flags.length > 0 && (
                                                            <div>
                                                                <div style={{ fontWeight: 600, marginBottom: 6, color: '#ff4d4f', fontSize: 15 }}>红旗：</div>
                                                                <div>
                                                                    {quickViewStructured.red_flags.map((flag, idx) => (
                                                                        <Tag key={idx} color="red" style={{ marginRight: 4, marginBottom: 4, fontSize: 13 }}>
                                                                            {flag}
                                                                        </Tag>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <div style={{ whiteSpace: 'pre-line', fontSize: 15, lineHeight: 1.7 }}>
                                                        {quickView}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        {!quickViewError && !quickViewLoading && !quickView && !quickViewStructured && (
                                            <div style={{ fontSize: 14, color: '#8c8c8c' }}>
                                                Quick view is not available for this job yet.
                                            </div>
                                        )}
                                    </div>
                                )}

                                <Tabs
                                    defaultActiveKey={analysisResult.cn_fast_read ? "cn_summary" : (analysisResult.fit_summary ? "fit" : "summary")}
                                    size="small"
                                >
                                    {/* JD Interpretation Tab */}
                                    <Tabs.TabPane tab="JD Summary" key="summary">
                                        {!hasDeepAnalysis && selectedCacheId && (
                                            <Alert
                                                type="info"
                                                message="Deep analysis has not been run for this job yet"
                                                description={
                                                    <div>
                                                        <p style={{ marginBottom: 12 }}>
                                                            This job only has a quick view. Run deep analysis to see detailed fit assessment, core signals, lifecycle analysis, and more.
                                                        </p>
                                                        <Button
                                                            type="primary"
                                                            loading={deepAnalysisLoading}
                                                            onClick={handleRunDeepAnalysis}
                                                        >
                                                            Run deep analysis now / 运行深度分析
                                                        </Button>
                                                    </div>
                                                }
                                                showIcon
                                                closable={false}
                                                style={{ marginBottom: 16 }}
                                            />
                                        )}
                                        {analysisResult.jd_summary && (
                                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                {/* [Quick Filter] Quick filter alert at top */}
                                                {analysisResult.constraints?.skip_deep_analysis && (
                                                    <Alert
                                                        type="warning"
                                                        message="Quick Filter: JD does not look like a Data Engineer / LLM Engineer role"
                                                        description={
                                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                                {analysisResult.constraints.profile_mismatch_reasons && analysisResult.constraints.profile_mismatch_reasons.length > 0 ? (
                                                                    <div>
                                                                        {analysisResult.constraints.profile_mismatch_reasons.map((reason, idx) => (
                                                                            <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0' }}>
                                                                                • {reason}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <div>Quick role filter detected this is a sales/financial advisor role, not a data engineering position, so deep analysis was skipped.</div>
                                                                )}
                                                            </Space>
                                                        }
                                                        showIcon
                                                        closable={false}
                                                        style={{ marginBottom: '16px' }}
                                                    />
                                                )}

                                                {/* [Step 1] Hard/Soft Constraints Alert */}
                                                {analysisResult.constraints && (
                                                    (analysisResult.constraints.hard_block ||
                                                        (analysisResult.constraints.soft_flags && analysisResult.constraints.soft_flags.length > 0)) && (
                                                        <Alert
                                                            type={analysisResult.constraints.hard_block ? "error" : "warning"}
                                                            message={
                                                                analysisResult.constraints.hard_block
                                                                    ? "Hard constraints: This role may not be worth deep pursuit"
                                                                    : "Soft concerns"
                                                            }
                                                            description={
                                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                                    {analysisResult.constraints.hard_block && analysisResult.constraints.hard_reasons && analysisResult.constraints.hard_reasons.length > 0 && (
                                                                        <div>
                                                                            {analysisResult.constraints.hard_reasons.map((reason, idx) => (
                                                                                <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0' }}>
                                                                                    • {reason}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                    {!analysisResult.constraints.hard_block && analysisResult.constraints.soft_flags && analysisResult.constraints.soft_flags.length > 0 && (
                                                                        <div>
                                                                            {analysisResult.constraints.soft_flags.map((flag, idx) => (
                                                                                <Tag key={idx} color="orange" style={{ marginBottom: '4px' }}>
                                                                                    {flag}
                                                                                </Tag>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                    {analysisResult.constraints.reasons && analysisResult.constraints.reasons.length > 0 && !analysisResult.constraints.hard_block && (
                                                                        <div style={{ marginTop: '8px' }}>
                                                                            {analysisResult.constraints.reasons.map((reason, idx) => (
                                                                                <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0', fontSize: '12px' }}>
                                                                                    • {reason}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                </Space>
                                                            }
                                                            showIcon
                                                            closable={false}
                                                            style={{ marginBottom: '16px' }}
                                                        />
                                                    )
                                                )}

                                                {/* [Core Signals] Core Signals 区块 */}
                                                {(() => {
                                                    const summary = analysisResult.jd_summary;
                                                    const hasCoreSignals = summary?.core_narrative || (summary?.core_signals && summary.core_signals.length > 0);
                                                    return hasCoreSignals ? (
                                                        <Card
                                                            title={
                                                                <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                    🔥 Core Signals
                                                                </span>
                                                            }
                                                            size="small"
                                                            style={{ backgroundColor: '#2a1a1a', borderColor: '#ff4d4f', marginBottom: '12px' }}
                                                            headStyle={{ backgroundColor: '#2a1a1a', borderColor: '#ff4d4f' }}
                                                        >
                                                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                                {summary?.core_narrative && (
                                                                    <Paragraph
                                                                        style={{
                                                                            color: '#e5e5e5',
                                                                            marginBottom: 0,
                                                                            whiteSpace: 'pre-wrap',
                                                                            fontSize: 14,
                                                                            lineHeight: 1.6,
                                                                        }}
                                                                    >
                                                                        {summary.core_narrative}
                                                                    </Paragraph>
                                                                )}
                                                                {summary?.core_signals && summary.core_signals.length > 0 && (
                                                                    <List
                                                                        size="small"
                                                                        dataSource={summary.core_signals}
                                                                        renderItem={(item) => (
                                                                            <List.Item style={{ padding: '8px 0', borderBottom: '1px solid #434343' }}>
                                                                                <div style={{ width: '100%' }}>
                                                                                    <div style={{ marginBottom: '4px' }}>
                                                                                        <Text strong style={{ color: '#fff', fontSize: 15 }}>
                                                                                            {item.theme}
                                                                                        </Text>
                                                                                        {item.importance && (
                                                                                            <Tag
                                                                                                color={item.importance === "HIGH" ? "red" : "blue"}
                                                                                                style={{ marginLeft: '8px' }}
                                                                                            >
                                                                                                {item.importance}
                                                                                            </Tag>
                                                                                        )}
                                                                                    </div>
                                                                                    {item.rationale && (
                                                                                        <Paragraph
                                                                                            style={{
                                                                                                color: '#d9d9d9',
                                                                                                marginBottom: 0,
                                                                                                fontSize: 14,
                                                                                                lineHeight: 1.6,
                                                                                                whiteSpace: 'pre-wrap',
                                                                                            }}
                                                                                        >
                                                                                            {item.rationale}
                                                                                        </Paragraph>
                                                                                    )}
                                                                                    {item.related_spotlights && item.related_spotlights.length > 0 && (
                                                                                        <div style={{ marginTop: '4px' }}>
                                                                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                                                                Related spotlight: {item.related_spotlights.join(", ")}
                                                                                            </Text>
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            </List.Item>
                                                                        )}
                                                                    />
                                                                )}
                                                            </Space>
                                                        </Card>
                                                    ) : null;
                                                })()}

                                                {/* 核心要求（金） */}
                                                {analysisResult.jd_summary.gold_points && analysisResult.jd_summary.gold_points.length > 0 && (
                                                    <Card
                                                        title={
                                                            <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                🥇 Core Requirements (Must Have)
                                                            </span>
                                                        }
                                                        size="small"
                                                        style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                        headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    >
                                                        <List
                                                            size="small"
                                                            dataSource={analysisResult.jd_summary.gold_points}
                                                            renderItem={(item) => (
                                                                <List.Item style={{ padding: '4px 0', marginBottom: 2 }}>
                                                                    <Text style={{ color: '#fff', fontSize: 14, lineHeight: 1.6 }}>{item}</Text>
                                                                </List.Item>
                                                            )}
                                                        />
                                                    </Card>
                                                )}

                                                {/* 重要要求（银） */}
                                                {analysisResult.jd_summary.silver_points && analysisResult.jd_summary.silver_points.length > 0 && (
                                                    <Card
                                                        title={
                                                            <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                🥈 Important Requirements (Should Have)
                                                            </span>
                                                        }
                                                        size="small"
                                                        style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                        headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    >
                                                        <List
                                                            size="small"
                                                            dataSource={analysisResult.jd_summary.silver_points}
                                                            renderItem={(item) => (
                                                                <List.Item style={{ padding: '4px 0', marginBottom: 2 }}>
                                                                    <Text style={{ color: '#fff', fontSize: 14, lineHeight: 1.6 }}>{item}</Text>
                                                                </List.Item>
                                                            )}
                                                        />
                                                    </Card>
                                                )}

                                                {/* 加分项（铜） */}
                                                {analysisResult.jd_summary.bronze_points && analysisResult.jd_summary.bronze_points.length > 0 && (
                                                    <Card
                                                        title={
                                                            <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                🥉 Nice to Have
                                                            </span>
                                                        }
                                                        size="small"
                                                        style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                        headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    >
                                                        <List
                                                            size="small"
                                                            dataSource={analysisResult.jd_summary.bronze_points}
                                                            renderItem={(item) => (
                                                                <List.Item style={{ padding: '4px 0', marginBottom: 2 }}>
                                                                    <Text style={{ color: '#fff', fontSize: 14, lineHeight: 1.6 }}>{item}</Text>
                                                                </List.Item>
                                                            )}
                                                        />
                                                    </Card>
                                                )}

                                                {/* Reflection Section */}
                                                {(analysisResult.jd_summary.reflection_problem_summary ||
                                                    analysisResult.jd_summary.reflection_day_in_life ||
                                                    analysisResult.jd_summary.reflection_pros_for_candidate ||
                                                    analysisResult.jd_summary.reflection_risks_for_candidate) && (
                                                        <Card
                                                            title={
                                                                <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                    💭 Reflection
                                                                </span>
                                                            }
                                                            size="small"
                                                            style={{ backgroundColor: '#2a2a2a', borderColor: '#1890ff', marginTop: '16px' }}
                                                            headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#1890ff' }}
                                                        >
                                                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                                {analysisResult.jd_summary.reflection_problem_summary && (
                                                                    <div>
                                                                        <Text strong style={{ color: '#1890ff', display: 'block', marginBottom: '8px' }}>
                                                                            Problem the team is trying to solve:
                                                                        </Text>
                                                                        <Paragraph
                                                                            style={{
                                                                                color: '#e5e5e5',
                                                                                marginBottom: 0,
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontSize: 14,
                                                                                lineHeight: 1.6,
                                                                            }}
                                                                        >
                                                                            {analysisResult.jd_summary.reflection_problem_summary}
                                                                        </Paragraph>
                                                                    </div>
                                                                )}

                                                                {analysisResult.jd_summary.reflection_day_in_life && (
                                                                    <div>
                                                                        <Text strong style={{ color: '#1890ff', display: 'block', marginBottom: '8px' }}>
                                                                            Ideal day-in-the-life:
                                                                        </Text>
                                                                        <Paragraph
                                                                            style={{
                                                                                color: '#e5e5e5',
                                                                                marginBottom: 0,
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontSize: 14,
                                                                                lineHeight: 1.6,
                                                                            }}
                                                                        >
                                                                            {analysisResult.jd_summary.reflection_day_in_life.split('\n').map((line, idx) => (
                                                                                <React.Fragment key={idx}>
                                                                                    {line.trim() && (line.trim().startsWith('-') || line.trim().startsWith('•')) ? (
                                                                                        <span>{line.trim()}</span>
                                                                                    ) : line.trim() ? (
                                                                                        <span>- {line.trim()}</span>
                                                                                    ) : null}
                                                                                    <br />
                                                                                </React.Fragment>
                                                                            ))}
                                                                        </Paragraph>
                                                                    </div>
                                                                )}

                                                                {analysisResult.jd_summary.reflection_pros_for_candidate && (
                                                                    <div>
                                                                        <Text strong style={{ color: '#52c41a', display: 'block', marginBottom: '8px' }}>
                                                                            Pros for Andy:
                                                                        </Text>
                                                                        <Paragraph
                                                                            style={{
                                                                                color: '#e5e5e5',
                                                                                marginBottom: 0,
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontSize: 14,
                                                                                lineHeight: 1.6,
                                                                            }}
                                                                        >
                                                                            {analysisResult.jd_summary.reflection_pros_for_candidate.split('\n').map((line, idx) => (
                                                                                <React.Fragment key={idx}>
                                                                                    {line.trim() && (line.trim().startsWith('-') || line.trim().startsWith('•')) ? (
                                                                                        <span>{line.trim()}</span>
                                                                                    ) : line.trim() ? (
                                                                                        <span>- {line.trim()}</span>
                                                                                    ) : null}
                                                                                    <br />
                                                                                </React.Fragment>
                                                                            ))}
                                                                        </Paragraph>
                                                                    </div>
                                                                )}

                                                                {analysisResult.jd_summary.reflection_risks_for_candidate && (
                                                                    <div>
                                                                        <Text strong style={{ color: '#faad14', display: 'block', marginBottom: '8px' }}>
                                                                            Risks / possible pitfalls:
                                                                        </Text>
                                                                        <Paragraph
                                                                            style={{
                                                                                color: '#e5e5e5',
                                                                                marginBottom: 0,
                                                                                whiteSpace: 'pre-wrap',
                                                                                fontSize: 14,
                                                                                lineHeight: 1.6,
                                                                            }}
                                                                        >
                                                                            {analysisResult.jd_summary.reflection_risks_for_candidate.split('\n').map((line, idx) => (
                                                                                <React.Fragment key={idx}>
                                                                                    {line.trim() && (line.trim().startsWith('-') || line.trim().startsWith('•')) ? (
                                                                                        <span>{line.trim()}</span>
                                                                                    ) : line.trim() ? (
                                                                                        <span>- {line.trim()}</span>
                                                                                    ) : null}
                                                                                    <br />
                                                                                </React.Fragment>
                                                                            ))}
                                                                        </Paragraph>
                                                                    </div>
                                                                )}
                                                            </Space>
                                                        </Card>
                                                    )}

                                                {/* Lifecycle & Spotlight Stories Section */}
                                                {(analysisResult.jd_summary.lifecycle || analysisResult.jd_summary.spotlight_stories) && (
                                                    <Card
                                                        title={
                                                            <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                🔄 Lifecycle & Spotlight Stories
                                                            </span>
                                                        }
                                                        size="small"
                                                        style={{ backgroundColor: '#2a2a2a', borderColor: '#722ed1', marginTop: '16px' }}
                                                        headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#722ed1' }}
                                                    >
                                                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                            {/* Lifecycle Summary */}
                                                            {analysisResult.jd_summary.lifecycle?.summary && (
                                                                <div>
                                                                    <Text strong style={{ color: '#722ed1', display: 'block', marginBottom: '8px' }}>
                                                                        Lifecycle Summary:
                                                                    </Text>
                                                                    <Paragraph
                                                                        style={{
                                                                            color: '#e5e5e5',
                                                                            marginBottom: 0,
                                                                            whiteSpace: 'pre-wrap',
                                                                            fontSize: 14,
                                                                            lineHeight: 1.6,
                                                                        }}
                                                                    >
                                                                        {analysisResult.jd_summary.lifecycle.summary}
                                                                    </Paragraph>
                                                                </div>
                                                            )}

                                                            {/* Lifecycle Stages */}
                                                            {analysisResult.jd_summary.lifecycle?.stages && analysisResult.jd_summary.lifecycle.stages.length > 0 && (
                                                                <div>
                                                                    <Text strong style={{ color: '#722ed1', display: 'block', marginBottom: '8px' }}>
                                                                        Lifecycle Stages:
                                                                    </Text>
                                                                    <List
                                                                        size="small"
                                                                        dataSource={analysisResult.jd_summary.lifecycle.stages}
                                                                        renderItem={(item, idx) => (
                                                                            <List.Item style={{ padding: '4px 0', marginBottom: 2 }}>
                                                                                <Text style={{ color: '#fff', fontSize: 14, lineHeight: 1.6 }}>
                                                                                    {idx + 1}. {item}
                                                                                </Text>
                                                                            </List.Item>
                                                                        )}
                                                                    />
                                                                </div>
                                                            )}

                                                            {/* Spotlight Stories */}
                                                            {analysisResult.jd_summary.spotlight_stories && analysisResult.jd_summary.spotlight_stories.length > 0 && (
                                                                <div>
                                                                    <Text strong style={{ color: '#722ed1', display: 'block', marginBottom: '12px' }}>
                                                                        Spotlight Deep-Dive Stories:
                                                                    </Text>
                                                                    {analysisResult.jd_summary.spotlight_stories.map((story, idx) => (
                                                                        <div key={idx} style={{ marginBottom: idx < analysisResult.jd_summary.spotlight_stories!.length - 1 ? '20px' : '0' }}>
                                                                            <Text strong style={{ color: '#ff4d4f', display: 'block', marginBottom: '8px', fontSize: 15 }}>
                                                                                Story {idx + 1}: {story.focus_area}
                                                                            </Text>
                                                                            <Space direction="vertical" style={{ width: '100%' }} size="small">
                                                                                <div>
                                                                                    <Text strong style={{ color: '#1890ff', fontSize: 13 }}>Why Important:</Text>
                                                                                    <Paragraph
                                                                                        style={{
                                                                                            color: '#e5e5e5',
                                                                                            marginBottom: 0,
                                                                                            fontSize: 14,
                                                                                            lineHeight: 1.6,
                                                                                            whiteSpace: 'pre-wrap',
                                                                                        }}
                                                                                    >
                                                                                        {story.why_important}
                                                                                    </Paragraph>
                                                                                </div>
                                                                                <div>
                                                                                    <Text strong style={{ color: '#1890ff', fontSize: 13 }}>Upstream & Downstream:</Text>
                                                                                    <Paragraph
                                                                                        style={{
                                                                                            color: '#e5e5e5',
                                                                                            marginBottom: 0,
                                                                                            fontSize: 14,
                                                                                            lineHeight: 1.6,
                                                                                            whiteSpace: 'pre-wrap',
                                                                                        }}
                                                                                    >
                                                                                        {story.upstream_downstream}
                                                                                    </Paragraph>
                                                                                </div>
                                                                                <div>
                                                                                    <Text strong style={{ color: '#1890ff', fontSize: 13 }}>Tools & Systems:</Text>
                                                                                    <Paragraph
                                                                                        style={{
                                                                                            color: '#e5e5e5',
                                                                                            marginBottom: 0,
                                                                                            fontSize: 14,
                                                                                            lineHeight: 1.6,
                                                                                            whiteSpace: 'pre-wrap',
                                                                                        }}
                                                                                    >
                                                                                        {story.tools_and_systems}
                                                                                    </Paragraph>
                                                                                </div>
                                                                                <div>
                                                                                    <Text strong style={{ color: '#1890ff', fontSize: 13 }}>Constraints & Risks:</Text>
                                                                                    <Paragraph
                                                                                        style={{
                                                                                            color: '#e5e5e5',
                                                                                            marginBottom: 0,
                                                                                            fontSize: 14,
                                                                                            lineHeight: 1.6,
                                                                                            whiteSpace: 'pre-wrap',
                                                                                        }}
                                                                                    >
                                                                                        {story.constraints_and_risks}
                                                                                    </Paragraph>
                                                                                </div>
                                                                                <div>
                                                                                    <Text strong style={{ color: '#1890ff', fontSize: 13 }}>Success Metrics:</Text>
                                                                                    <Paragraph
                                                                                        style={{
                                                                                            color: '#e5e5e5',
                                                                                            marginBottom: 0,
                                                                                            fontSize: 14,
                                                                                            lineHeight: 1.6,
                                                                                            whiteSpace: 'pre-wrap',
                                                                                        }}
                                                                                    >
                                                                                        {story.success_metrics}
                                                                                    </Paragraph>
                                                                                </div>
                                                                                {/* [Step 2] Evidence snippets from JD */}
                                                                                {story.evidence_snippets && story.evidence_snippets.length > 0 && (
                                                                                    <div style={{ marginTop: '8px' }}>
                                                                                        <Collapse
                                                                                            size="small"
                                                                                            items={[
                                                                                                {
                                                                                                    key: 'evidence',
                                                                                                    label: (
                                                                                                        <Text strong style={{ color: '#52c41a', fontSize: '12px' }}>
                                                                                                            📎 Show evidence from JD ({story.evidence_snippets.length} snippet{story.evidence_snippets.length > 1 ? 's' : ''})
                                                                                                        </Text>
                                                                                                    ),
                                                                                                    children: (
                                                                                                        <List
                                                                                                            size="small"
                                                                                                            dataSource={story.evidence_snippets}
                                                                                                            renderItem={(snippet, snippetIdx) => (
                                                                                                                <List.Item style={{ padding: '4px 0', borderBottom: 'none' }}>
                                                                                                                    <Text style={{ color: '#d9d9d9', fontSize: '11px', fontStyle: 'italic' }}>
                                                                                                                        • {snippet}
                                                                                                                    </Text>
                                                                                                                </List.Item>
                                                                                                            )}
                                                                                                        />
                                                                                                    ),
                                                                                                    style: { backgroundColor: '#1a1a1a', borderColor: '#434343' },
                                                                                                },
                                                                                            ]}
                                                                                            style={{ backgroundColor: '#1a1a1a' }}
                                                                                        />
                                                                                    </div>
                                                                                )}
                                                                            </Space>
                                                                            {idx < analysisResult.jd_summary.spotlight_stories!.length - 1 && (
                                                                                <Divider style={{ margin: '12px 0', borderColor: '#434343' }} />
                                                                            )}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </Space>
                                                    </Card>
                                                )}

                                                {/* CN Fast-read Summary Inline Preview (optional, main view in CN Summary tab) */}
                                                {analysisResult.cn_fast_read && (
                                                    <Card
                                                        title={
                                                            <span style={{ color: '#e5e5e5', fontSize: 16, fontWeight: 600 }}>
                                                                📘 CN Summary / 中文速读（简要预览）
                                                            </span>
                                                        }
                                                        size="small"
                                                        style={{ backgroundColor: '#1f1f1f', borderColor: '#434343', marginTop: '16px' }}
                                                        headStyle={{ backgroundColor: '#1f1f1f', borderColor: '#434343' }}
                                                    >
                                                        <Paragraph
                                                            style={{
                                                                color: '#e5e5e5',
                                                                marginBottom: 0,
                                                                whiteSpace: 'pre-wrap',
                                                                fontSize: 15,
                                                                lineHeight: 1.8,
                                                                maxHeight: 160,
                                                                overflow: 'hidden',
                                                                textOverflow: 'ellipsis',
                                                            }}
                                                        >
                                                            {analysisResult.cn_fast_read}
                                                        </Paragraph>
                                                    </Card>
                                                )}
                                            </Space>
                                        )}
                                    </Tabs.TabPane>

                                    {/* CN Summary / 中文速读 Tab */}
                                    <Tabs.TabPane tab="CN Summary / 中文速读" key="cn_summary">
                                        <Card
                                            size="small"
                                            style={{ backgroundColor: '#141414', borderColor: '#434343', minHeight: 200 }}
                                            headStyle={{ backgroundColor: '#141414', borderColor: '#434343' }}
                                        >
                                            {analysisResult.cn_fast_read ? (
                                                <Paragraph
                                                    style={{
                                                        color: '#e5e5e5',
                                                        marginBottom: 0,
                                                        whiteSpace: 'pre-wrap',
                                                        fontSize: 16,
                                                        lineHeight: 1.8,
                                                    }}
                                                >
                                                    {analysisResult.cn_fast_read}
                                                </Paragraph>
                                            ) : (
                                                <Text type="secondary" style={{ fontSize: 15 }}>
                                                    暂无中文速读内容，请先完成一次分析，或等待后端缓存生成该字段。
                                                </Text>
                                            )}
                                        </Card>
                                    </Tabs.TabPane>

                                    {/* Fit Analysis Tab */}
                                    <Tabs.TabPane tab="Fit Analysis" key="fit">
                                        {!hasDeepAnalysis && selectedCacheId && (
                                            <Alert
                                                type="info"
                                                message="Deep analysis has not been run for this job yet"
                                                description={
                                                    <div>
                                                        <p style={{ marginBottom: 12 }}>
                                                            Fit analysis requires deep analysis. Run deep analysis to see detailed fit assessment, strengths, gaps, and recommendations.
                                                        </p>
                                                        <Button
                                                            type="primary"
                                                            loading={deepAnalysisLoading}
                                                            onClick={handleRunDeepAnalysis}
                                                        >
                                                            Run deep analysis now / 运行深度分析
                                                        </Button>
                                                    </div>
                                                }
                                                showIcon
                                                closable={false}
                                                style={{ marginBottom: 16 }}
                                            />
                                        )}
                                        {analysisResult.fit_summary && (
                                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                {/* [Quick Filter] Quick filter alert at top of Fit Analysis */}
                                                {analysisResult.constraints?.skip_deep_analysis && (
                                                    <Alert
                                                        type="warning"
                                                        message="Quick Filter: JD does not look like a Data Engineer / LLM Engineer role"
                                                        description={
                                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                                {analysisResult.constraints.profile_mismatch_reasons && analysisResult.constraints.profile_mismatch_reasons.length > 0 ? (
                                                                    <div>
                                                                        {analysisResult.constraints.profile_mismatch_reasons.map((reason, idx) => (
                                                                            <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0' }}>
                                                                                • {reason}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ) : (
                                                                    <div>Quick role filter detected this is a sales/financial advisor role, not a data engineering position, so deep analysis was skipped.</div>
                                                                )}
                                                            </Space>
                                                        }
                                                        showIcon
                                                        closable={false}
                                                        style={{ marginBottom: '16px' }}
                                                    />
                                                )}

                                                {/* [Step 1] Hard/Soft Constraints Alert - Also show in Fit Analysis tab */}
                                                {analysisResult.constraints && (
                                                    (analysisResult.constraints.hard_block ||
                                                        (analysisResult.constraints.soft_flags && analysisResult.constraints.soft_flags.length > 0)) && (
                                                        <Alert
                                                            type={analysisResult.constraints.hard_block ? "error" : "warning"}
                                                            message={
                                                                analysisResult.constraints.hard_block
                                                                    ? "Hard constraints: This role may not be worth deep pursuit"
                                                                    : "Soft concerns"
                                                            }
                                                            description={
                                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                                    {analysisResult.constraints.hard_block && analysisResult.constraints.hard_reasons && analysisResult.constraints.hard_reasons.length > 0 && (
                                                                        <div>
                                                                            {analysisResult.constraints.hard_reasons.map((reason, idx) => (
                                                                                <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0' }}>
                                                                                    • {reason}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                    {!analysisResult.constraints.hard_block && analysisResult.constraints.soft_flags && analysisResult.constraints.soft_flags.length > 0 && (
                                                                        <div>
                                                                            {analysisResult.constraints.soft_flags.map((flag, idx) => (
                                                                                <Tag key={idx} color="orange" style={{ marginBottom: '4px' }}>
                                                                                    {flag}
                                                                                </Tag>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                    {analysisResult.constraints.reasons && analysisResult.constraints.reasons.length > 0 && !analysisResult.constraints.hard_block && (
                                                                        <div style={{ marginTop: '8px' }}>
                                                                            {analysisResult.constraints.reasons.map((reason, idx) => (
                                                                                <div key={idx} style={{ marginTop: idx > 0 ? '4px' : '0', fontSize: '12px' }}>
                                                                                    • {reason}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                </Space>
                                                            }
                                                            showIcon
                                                            closable={false}
                                                            style={{ marginBottom: '16px' }}
                                                        />
                                                    )
                                                )}

                                                {/* Match Score */}
                                                <Card
                                                    size="small"
                                                    style={{ backgroundColor: '#1f1f1f', borderColor: '#434343' }}
                                                    headStyle={{ backgroundColor: '#1f1f1f', borderColor: '#434343' }}
                                                >
                                                    <Space direction="vertical" style={{ width: '100%' }}>
                                                        <div>
                                                            <Text strong style={{ color: '#fff' }}>Match Score: </Text>
                                                            <Text style={{ fontSize: '20px', color: '#1890ff' }}>
                                                                {analysisResult.fit_summary.match_score != null ? analysisResult.fit_summary.match_score : '—'}/10
                                                            </Text>
                                                        </div>
                                                        <div>
                                                            <Text strong style={{ color: '#fff' }}>Category: </Text>
                                                            <Tag color={getCategoryColor(analysisResult.fit_summary.category)}>
                                                                {analysisResult.fit_summary.category === 'A' ? 'Strong Match' :
                                                                    analysisResult.fit_summary.category === 'B' ? 'Related but Not Ideal' :
                                                                        'Not a Good Fit'}
                                                            </Tag>
                                                        </div>
                                                        <div>
                                                            <Text strong style={{ color: '#fff' }}>Recommendation: </Text>
                                                            <Tag color={getRecommendationColor(analysisResult.fit_summary.recommendation)}>
                                                                {analysisResult.fit_summary.recommendation === 'APPLY' ? 'Apply' :
                                                                    analysisResult.fit_summary.recommendation === 'MAYBE' ? 'Maybe' :
                                                                        'Skip'}
                                                            </Tag>
                                                        </div>
                                                    </Space>
                                                </Card>

                                                {/* Strengths */}
                                                {analysisResult.fit_summary.strengths && analysisResult.fit_summary.strengths.length > 0 && (
                                                    <Card
                                                        title={<span style={{ color: '#fff' }}>✅ Strengths</span>}
                                                        size="small"
                                                        style={{ backgroundColor: '#1a3a1a', borderColor: '#52c41a' }}
                                                        headStyle={{ backgroundColor: '#1a3a1a', borderColor: '#52c41a' }}
                                                    >
                                                        <List
                                                            size="small"
                                                            dataSource={analysisResult.fit_summary.strengths}
                                                            renderItem={(item) => (
                                                                <List.Item style={{ padding: '4px 0' }}>
                                                                    <Text style={{ color: '#fff' }}>{item}</Text>
                                                                </List.Item>
                                                            )}
                                                        />
                                                    </Card>
                                                )}

                                                {/* Gaps */}
                                                {analysisResult.fit_summary.gaps && analysisResult.fit_summary.gaps.length > 0 && (
                                                    <Card
                                                        title={<span style={{ color: '#fff' }}>⚠️ Gaps</span>}
                                                        size="small"
                                                        style={{ backgroundColor: '#3a2a1a', borderColor: '#faad14' }}
                                                        headStyle={{ backgroundColor: '#3a2a1a', borderColor: '#faad14' }}
                                                    >
                                                        <List
                                                            size="small"
                                                            dataSource={analysisResult.fit_summary.gaps}
                                                            renderItem={(item) => (
                                                                <List.Item style={{ padding: '4px 0' }}>
                                                                    <Text style={{ color: '#fff' }}>{item}</Text>
                                                                </List.Item>
                                                            )}
                                                        />
                                                    </Card>
                                                )}

                                                {/* Reasoning */}
                                                {analysisResult.fit_summary.reasoning_summary && (
                                                    <Card
                                                        title={<span style={{ color: '#fff' }}>💡 Reasoning</span>}
                                                        size="small"
                                                        style={{ backgroundColor: '#1f1f1f', borderColor: '#434343' }}
                                                        headStyle={{ backgroundColor: '#1f1f1f', borderColor: '#434343' }}
                                                    >
                                                        <Paragraph style={{ color: '#fff' }}>
                                                            {analysisResult.fit_summary.reasoning_summary}
                                                        </Paragraph>
                                                    </Card>
                                                )}

                                                {/* Next Actions */}
                                                {(analysisResult.fit_summary.next_actions?.length > 0 ||
                                                    analysisResult.fit_summary.action_items?.length > 0) && (
                                                        <Card
                                                            title={<span style={{ color: '#fff' }}>📋 Next Actions</span>}
                                                            size="small"
                                                            style={{ backgroundColor: '#1f1f1f', borderColor: '#1890ff' }}
                                                            headStyle={{ backgroundColor: '#1f1f1f', borderColor: '#1890ff' }}
                                                        >
                                                            <List
                                                                size="small"
                                                                dataSource={analysisResult.fit_summary.next_actions || analysisResult.fit_summary.action_items || []}
                                                                renderItem={(item, idx) => (
                                                                    <List.Item style={{ padding: '4px 0' }}>
                                                                        <Text style={{ color: '#fff' }}>
                                                                            {idx + 1}. {item}
                                                                        </Text>
                                                                    </List.Item>
                                                                )}
                                                            />
                                                        </Card>
                                                    )}
                                            </Space>
                                        )}
                                        {!analysisResult.fit_summary && (
                                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                                <Text type="secondary">
                                                    {analysisResult.jd_summary
                                                        ? "Fit analysis is not available. Please ensure a candidate profile is configured."
                                                        : "Run 'Analyze JD' first to see your fit analysis."}
                                                </Text>
                                            </div>
                                        )}
                                    </Tabs.TabPane>

                                    {/* [Engineering View] Graph Trace Tab - For engineers only */}
                                    <Tabs.TabPane tab="Engineering" key="engineering">
                                        {analysisResult?.graph_steps && Array.isArray(analysisResult.graph_steps) && analysisResult.graph_steps.length > 0 ? (
                                            <Card
                                                title="Agent Graph / Execution Trace"
                                                size="small"
                                                style={{ backgroundColor: '#1a1a1a', borderColor: '#434343' }}
                                                headStyle={{ backgroundColor: '#1a1a1a', borderColor: '#434343' }}
                                            >
                                                <Paragraph type="secondary" style={{ fontSize: '12px', marginBottom: '16px' }}>
                                                    This view shows the LangGraph workflow steps executed during JD analysis.
                                                    For engineering/debugging purposes only.
                                                </Paragraph>
                                                <List
                                                    size="small"
                                                    dataSource={analysisResult.graph_steps}
                                                    renderItem={(step: GraphStep, idx: number) => {
                                                        const getStatusColor = (step: GraphStep): string => {
                                                            // If step is skipped (either status is 'skipped' or extra_info has skipped field), use gray
                                                            if (step.status === 'skipped' || step.extra_info?.skipped) {
                                                                return 'default';  // Gray for skipped
                                                            }
                                                            // Otherwise, use the status field
                                                            switch (step.status) {
                                                                case 'completed':
                                                                    return 'success';
                                                                case 'failed':
                                                                    return 'error';
                                                                case 'in_progress':
                                                                    return 'processing';
                                                                default:
                                                                    return 'default';
                                                            }
                                                        };

                                                        const getStatusLabel = (step: GraphStep): string => {
                                                            // If step is skipped (either status is 'skipped' or extra_info has skipped field)
                                                            if (step.status === 'skipped' || step.extra_info?.skipped) {
                                                                return 'SKIPPED';
                                                            }
                                                            // Otherwise, use the status field
                                                            switch (step.status) {
                                                                case 'failed':
                                                                    return 'FAILED';
                                                                case 'in_progress':
                                                                    return 'RUNNING';
                                                                case 'completed':
                                                                    return 'COMPLETED';
                                                                case 'pending':
                                                                    return 'PENDING';
                                                                default:
                                                                    return step.status.toUpperCase();
                                                            }
                                                        };

                                                        const formatDuration = (ms?: number) => {
                                                            if (!ms) return 'N/A';
                                                            if (ms < 1) return '< 1 ms';
                                                            if (ms < 1000) return `${ms.toFixed(1)} ms`;
                                                            return `${(ms / 1000).toFixed(2)} s`;
                                                        };

                                                        // Check if step is skipped (either status is 'skipped' or extra_info has skipped field)
                                                        const isSkipped = step.status === 'skipped' || step.extra_info?.skipped;

                                                        return (
                                                            <List.Item
                                                                style={{
                                                                    padding: '8px 0',
                                                                    borderBottom: '1px solid #434343',
                                                                }}
                                                            >
                                                                <Space direction="vertical" style={{ width: '100%' }} size="small">
                                                                    <Space>
                                                                        <Text strong style={{ color: '#fff', fontFamily: 'monospace' }}>
                                                                            {step.name}
                                                                        </Text>
                                                                        <Tag color={getStatusColor(step)}>
                                                                            {getStatusLabel(step)}
                                                                        </Tag>
                                                                        {!isSkipped && step.duration_ms !== undefined && (
                                                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                                                {formatDuration(step.duration_ms)}
                                                                            </Text>
                                                                        )}
                                                                        {isSkipped && (
                                                                            <Text type="secondary" style={{ fontSize: '11px', color: '#999' }}>
                                                                                —
                                                                            </Text>
                                                                        )}
                                                                    </Space>
                                                                    {step.started_at && (
                                                                        <Text type="secondary" style={{ fontSize: '11px' }}>
                                                                            Started: {new Date(step.started_at).toLocaleString()}
                                                                        </Text>
                                                                    )}
                                                                    {isSkipped && step.extra_info?.skipped && (
                                                                        <div style={{ marginTop: '4px' }}>
                                                                            <Text type="secondary" style={{ fontSize: '11px', color: '#999', fontStyle: 'italic' }}>
                                                                                {step.extra_info.skipped}
                                                                            </Text>
                                                                        </div>
                                                                    )}
                                                                    {!isSkipped && step.extra_info && Object.keys(step.extra_info).length > 0 && (
                                                                        <div style={{ marginTop: '4px' }}>
                                                                            <Text type="secondary" style={{ fontSize: '11px' }}>
                                                                                Extra: {JSON.stringify(step.extra_info, null, 2)}
                                                                            </Text>
                                                                        </div>
                                                                    )}
                                                                </Space>
                                                            </List.Item>
                                                        );
                                                    }}
                                                />
                                            </Card>
                                        ) : (
                                            <Card
                                                size="small"
                                                style={{ backgroundColor: '#1a1a1a', borderColor: '#434343' }}
                                            >
                                                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                                    <Paragraph type="secondary">
                                                        Graph trace not available for this run.
                                                    </Paragraph>
                                                </div>
                                            </Card>
                                        )}
                                    </Tabs.TabPane>
                                </Tabs>
                            </div>
                        )}

                        {/* Career Coach / 职业教练对话区 */}
                        <Card
                            title="Career Coach / 职业教练对话（Beta）"
                            size="small"
                            style={{
                                marginTop: 16,
                                backgroundColor: '#141414',
                                borderColor: '#434343'
                            }}
                            headStyle={{
                                backgroundColor: '#141414',
                                borderColor: '#434343',
                                color: '#e5e5e5'
                            }}
                        >
                            {/* 主题按钮 */}
                            <Space style={{ marginBottom: 8, flexWrap: 'wrap' }}>
                                <Button
                                    type={careerChatTopic === 'resume_opt' ? 'primary' : 'default'}
                                    size="small"
                                    onClick={() => {
                                        const newTopic: CareerChatTopic = 'resume_opt';
                                        const defaultQuestion = "帮我为这份工作提 3–5 条简历修改建议（英文 bullet），优先强调我已有的优势。";

                                        setCareerChatTopic(newTopic);
                                        setCareerChatError(null);
                                        setCareerChatInput(defaultQuestion);
                                    }}
                                >
                                    为这份工作优化简历
                                </Button>
                                <Button
                                    type={careerChatTopic === 'gap_analysis' ? 'primary' : 'default'}
                                    size="small"
                                    onClick={() => {
                                        const newTopic: CareerChatTopic = 'gap_analysis';
                                        const defaultQuestion = "请帮我用中英文简要分析一下：我和这份工作之间最主要的 3 个差距是什么？";

                                        setCareerChatTopic(newTopic);
                                        setCareerChatError(null);
                                        setCareerChatInput(defaultQuestion);
                                    }}
                                >
                                    我和这份工作的差距
                                </Button>
                                <Button
                                    type={careerChatTopic === 'tech_question' ? 'primary' : 'default'}
                                    size="small"
                                    onClick={() => {
                                        const newTopic: CareerChatTopic = 'tech_question';
                                        const defaultQuestion = "从这份 JD 看，这个岗位最关键的技术栈和系统设计能力有哪些？我应该重点准备哪些面试问题？";

                                        setCareerChatTopic(newTopic);
                                        setCareerChatError(null);
                                        setCareerChatInput(defaultQuestion);
                                    }}
                                >
                                    问技术问题
                                </Button>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                                提示：先在左侧选中一个职位，再选择上方主题，主题会帮你填入一个示例问题，你可以直接点击"发送"或先修改后再发送（支持中英文）。
                            </Text>

                            {careerChatError && (
                                <Alert
                                    type="error"
                                    showIcon
                                    message="对话出错"
                                    description={careerChatError}
                                    style={{ marginBottom: 8 }}
                                />
                            )}

                            {/* 消息列表 */}
                            <div
                                style={{
                                    maxHeight: 260,
                                    overflowY: 'auto',
                                    padding: '8px 8px',
                                    borderRadius: 4,
                                    border: '1px solid #303030',
                                    marginBottom: 8,
                                    backgroundColor: '#1a1a1a',
                                }}
                            >
                                {careerChatMessages.length === 0 ? (
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        还没有开始对话，先选择主题并输入你的第一个问题。
                                    </Text>
                                ) : (
                                    <>
                                        {careerChatMessages.map((msg, idx) => (
                                            <div
                                                key={idx}
                                                style={{
                                                    marginBottom: 6,
                                                    textAlign: msg.role === 'user' ? 'right' : 'left',
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        display: 'inline-block',
                                                        padding: '6px 10px',
                                                        borderRadius: 8,
                                                        backgroundColor: msg.role === 'user' ? '#177ddc' : '#262626',
                                                        color: '#f5f5f5',
                                                        maxWidth: '100%',
                                                        whiteSpace: 'pre-wrap',
                                                        fontSize: 13,
                                                        lineHeight: 1.5,
                                                    }}
                                                >
                                                    {msg.content}
                                                </div>
                                            </div>
                                        ))}
                                        {careerChatLoading && (
                                            <div style={{ textAlign: 'left', marginTop: 8 }}>
                                                <Spin size="small" /> <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>AI 正在思考...</Text>
                                            </div>
                                        )}
                                        <div ref={chatEndRef} />
                                    </>
                                )}
                            </div>

                            {/* 输入区 */}
                            <Space.Compact style={{ width: '100%' }}>
                                <Input.TextArea
                                    value={careerChatInput}
                                    onChange={(e) => setCareerChatInput(e.target.value)}
                                    autoSize={{ minRows: 1, maxRows: 3 }}
                                    placeholder={
                                        selectedCacheId
                                            ? '输入你想问的问题，例如：帮我为这份 Sony 数据工程师职位提 3 个简历修改建议'
                                            : '请先在左侧选择一个职位'
                                    }
                                    disabled={careerChatLoading || !selectedCacheId}
                                    style={{
                                        backgroundColor: '#1a1a1a',
                                        borderColor: '#434343',
                                        color: '#e5e5e5'
                                    }}
                                    onPressEnter={(e) => {
                                        if (e.shiftKey) {
                                            return; // Allow new line with Shift+Enter
                                        }
                                        e.preventDefault();
                                        handleSendCareerChat();
                                    }}
                                />
                                <Button
                                    type="primary"
                                    onClick={() => handleSendCareerChat()}
                                    loading={careerChatLoading}
                                    disabled={!selectedCacheId || !careerChatInput.trim() || careerChatLoading}
                                >
                                    发送
                                </Button>
                            </Space.Compact>
                        </Card>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
