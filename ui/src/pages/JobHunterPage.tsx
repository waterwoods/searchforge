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

import React, { useState, useEffect } from 'react';
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
} from 'antd';
import { SearchOutlined, MessageOutlined, FileTextOutlined, HistoryOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { API_BASE_URL } from '../api/config';
import { fetchJobhunterCache, fetchCachedJDDetail, type CachedJDDetail } from '../api/jobhunter';
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

    // Cached batch analysis list (from backend SQLite/Qdrant cache via /api/jobhunter/cache)
    const [cachedJobs, setCachedJobs] = useState<CachedJobAnalysis[]>([]);
    const [cacheLoading, setCacheLoading] = useState(false);
    const [cacheError, setCacheError] = useState<string | null>(null);

    // Cached detail loading state
    const [selectedCacheId, setSelectedCacheId] = useState<number | null>(null);
    const [cachedDetailLoading, setCachedDetailLoading] = useState(false);
    const [cachedDetailError, setCachedDetailError] = useState<string | null>(null);

    const getProfileIdForMode = (mode: "agent" | "data_eng"): string => {
        // Map UI profile mode to backend profile_id used for caching
        if (mode === "data_eng") {
            return "data_engineer_gcp";
        }
        return "llm_agent";
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

    // ========================================
    // Flow 1: JD 解读 + 适配度分析
    // ========================================
    const handleAnalyzeJD = async () => {
        try {
            const values = await form.validateFields(['jd_description']);
            setLoading(true);
            setAnalysisResult(null);
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

            // 添加到历史记录
            // 优先使用后端返回的 jd_summary 中的信息，因为后端可能会从 JD 文本中提取标题
            const newRecord: AnalyzedJDRecord = {
                id: `jd_${Date.now()}`,
                job_id: data.jd_summary?.job_id || jdInput.job_id,
                title: data.jd_summary?.title || jdInput.title || 'Untitled Job',
                company: data.jd_summary?.company || jdInput.company || 'Unknown Company',
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

            // Clear chat history when loading cached detail
            setChatHistory([]);

            // Fetch detailed analysis from cache
            const detail: CachedJDDetail = await fetchCachedJDDetail(item.cache_id);

            // Convert cached detail to JDAnalysisResponse format
            // The backend returns analysis as a dict with jd_summary, fit_summary, constraints, graph_steps, etc.
            const analysisData: JDAnalysisResponse = {
                ok: true,
                jd_summary: detail.analysis.jd_summary,
                fit_summary: detail.analysis.fit_summary,
                constraints: detail.analysis.constraints,
                graph_steps: detail.analysis.graph_steps,
            };

            // Set analysis result (same format as single JD analysis)
            setAnalysisResult(analysisData);

            // Log debug info about core_signals
            if (analysisData.jd_summary?.core_signals) {
                console.log(`[JobHunter] Loaded cached core_signals:`, analysisData.jd_summary.core_signals.length);
            }
            if (analysisData.jd_summary?.core_narrative) {
                console.log(`[JobHunter] Loaded cached core_narrative:`, analysisData.jd_summary.core_narrative.substring(0, 100));
            }

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

                                    {/* Batch results backed by backend SQLite cache via /api/jobhunter/cache (no live LLM calls) */}
                                    {(cacheLoading || cachedDetailLoading) && (
                                        <div style={{ textAlign: 'center', padding: '12px 0' }}>
                                            <Spin size="small" />
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
                                    {!cacheLoading && !cacheError && cachedJobs.length > 0 && (
                                        <List
                                            size="small"
                                            dataSource={cachedJobs}
                                            renderItem={(item) => {
                                                const score = item.match_score ?? 0;
                                                const scorePct = Math.max(
                                                    0,
                                                    Math.min(100, Math.round(score * 10))
                                                );
                                                const isSelected = selectedCacheId === item.cache_id;
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
                                                                        {item.company} · {item.title}
                                                                    </span>
                                                                    <Tag
                                                                        color={getCategoryColor(
                                                                            item.category as any
                                                                        )}
                                                                    >
                                                                        {item.category || '-'} · {scorePct}%
                                                                    </Tag>
                                                                </div>
                                                            }
                                                            description={
                                                                <div
                                                                    style={{
                                                                        display: 'flex',
                                                                        justifyContent: 'space-between',
                                                                        alignItems: 'center',
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
                    ======================================== */}
                <Col xs={24} lg={10}>
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
                        <Form
                            form={form}
                            layout="vertical"
                            initialValues={{
                                jd_description: '',
                                jd_title: '',
                                jd_company: '',
                                jd_location: '',
                            }}
                            style={{ flex: 'none', marginBottom: '16px' }}
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

                        <Divider style={{ margin: '16px 0' }}>Career Coach Chat</Divider>

                        {/* 聊天区域 */}
                        <div
                            style={{
                                flex: 1,
                                border: '1px solid #434343',
                                borderRadius: '4px',
                                padding: '12px',
                                marginBottom: '12px',
                                overflow: 'auto',
                                backgroundColor: '#1a1a1a',
                                minHeight: '200px',
                            }}
                        >
                            {chatHistory.length === 0 ? (
                                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                    <MessageOutlined style={{ fontSize: '32px', marginBottom: '12px' }} />
                                    <Paragraph type="secondary">
                                        After analyzing a JD, you can chat with the AI career coach here
                                    </Paragraph>
                                </div>
                            ) : (
                                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                    {chatHistory.map((msg, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                textAlign: msg.role === 'user' ? 'right' : 'left',
                                                marginBottom: '8px',
                                            }}
                                        >
                                            <div
                                                style={{
                                                    display: 'inline-block',
                                                    maxWidth: '80%',
                                                    padding: '8px 12px',
                                                    borderRadius: '8px',
                                                    backgroundColor: msg.role === 'user' ? '#1890ff' : '#434343',
                                                    color: '#fff',
                                                }}
                                            >
                                                <Tag
                                                    color={msg.role === 'user' ? 'blue' : 'default'}
                                                    style={{ marginBottom: '4px', marginRight: '4px' }}
                                                >
                                                    {msg.role === 'user' ? 'You' : 'Coach'}
                                                </Tag>
                                                <div style={{ marginTop: '4px' }}>
                                                    {msg.role === 'assistant' ? (
                                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                    ) : (
                                                        <Text style={{ color: '#fff' }}>{msg.content}</Text>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {chatLoading && (
                                        <div style={{ textAlign: 'left' }}>
                                            <Spin size="small" /> <Text type="secondary">AI is thinking...</Text>
                                        </div>
                                    )}
                                </Space>
                            )}
                        </div>

                        {/* 聊天输入框 */}
                        <Space.Compact style={{ width: '100%' }}>
                            <Input
                                value={currentChatInput}
                                onChange={(e) => setCurrentChatInput(e.target.value)}
                                placeholder="Enter your question..."
                                onPressEnter={handleSendChatMessage}
                                disabled={!analysisResult?.jd_summary || chatLoading}
                            />
                            <Button
                                type="primary"
                                icon={<MessageOutlined />}
                                onClick={handleSendChatMessage}
                                loading={chatLoading}
                                disabled={!analysisResult?.jd_summary || !currentChatInput.trim()}
                            >
                                Send
                            </Button>
                        </Space.Compact>
                    </Card>
                </Col>

                {/* ========================================
                    右侧栏：JD 分析结果详情
                    （金银铜要点、适配度、优势/缺口等）
                    ======================================== */}
                <Col xs={24} lg={isHistoryCollapsed ? 12 : 8}>
                    <Card
                        title={
                            <Space>
                                <FileTextOutlined />
                                <span>Analysis Results</span>
                                <Tag color={profileMode === "agent" ? "blue" : "green"}>
                                    {profileMode === "agent" ? "Profile: LLM / Agent" : "Profile: Data Engineer (GCP)"}
                                </Tag>
                            </Space>
                        }
                        bordered={false}
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, overflow: 'auto', padding: '16px' }}
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
                            <Tabs
                                defaultActiveKey={analysisResult.fit_summary ? "fit" : "summary"}
                                size="small"
                            >
                                {/* JD Interpretation Tab */}
                                <Tabs.TabPane tab="JD Summary" key="summary">
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
                                                        title={<span style={{ color: '#fff' }}>🔥 Core Signals</span>}
                                                        size="small"
                                                        style={{ backgroundColor: '#2a1a1a', borderColor: '#ff4d4f', marginBottom: '12px' }}
                                                        headStyle={{ backgroundColor: '#2a1a1a', borderColor: '#ff4d4f' }}
                                                    >
                                                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                            {summary?.core_narrative && (
                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
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
                                                                                    <Text strong style={{ color: '#fff', fontSize: '14px' }}>
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
                                                                                    <Paragraph style={{ color: '#d9d9d9', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
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
                                                    title={<span style={{ color: '#fff' }}>🥇 Core Requirements (Must Have)</span>}
                                                    size="small"
                                                    style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                >
                                                    <List
                                                        size="small"
                                                        dataSource={analysisResult.jd_summary.gold_points}
                                                        renderItem={(item) => (
                                                            <List.Item style={{ padding: '4px 0' }}>
                                                                <Text style={{ color: '#fff' }}>{item}</Text>
                                                            </List.Item>
                                                        )}
                                                    />
                                                </Card>
                                            )}

                                            {/* 重要要求（银） */}
                                            {analysisResult.jd_summary.silver_points && analysisResult.jd_summary.silver_points.length > 0 && (
                                                <Card
                                                    title={<span style={{ color: '#fff' }}>🥈 Important Requirements (Should Have)</span>}
                                                    size="small"
                                                    style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                >
                                                    <List
                                                        size="small"
                                                        dataSource={analysisResult.jd_summary.silver_points}
                                                        renderItem={(item) => (
                                                            <List.Item style={{ padding: '4px 0' }}>
                                                                <Text style={{ color: '#fff' }}>{item}</Text>
                                                            </List.Item>
                                                        )}
                                                    />
                                                </Card>
                                            )}

                                            {/* 加分项（铜） */}
                                            {analysisResult.jd_summary.bronze_points && analysisResult.jd_summary.bronze_points.length > 0 && (
                                                <Card
                                                    title={<span style={{ color: '#fff' }}>🥉 Nice to Have</span>}
                                                    size="small"
                                                    style={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                    headStyle={{ backgroundColor: '#2a2a2a', borderColor: '#434343' }}
                                                >
                                                    <List
                                                        size="small"
                                                        dataSource={analysisResult.jd_summary.bronze_points}
                                                        renderItem={(item) => (
                                                            <List.Item style={{ padding: '4px 0' }}>
                                                                <Text style={{ color: '#fff' }}>{item}</Text>
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
                                                        title={<span style={{ color: '#fff' }}>💭 Reflection</span>}
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
                                                                    <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
                                                                        {analysisResult.jd_summary.reflection_problem_summary}
                                                                    </Paragraph>
                                                                </div>
                                                            )}

                                                            {analysisResult.jd_summary.reflection_day_in_life && (
                                                                <div>
                                                                    <Text strong style={{ color: '#1890ff', display: 'block', marginBottom: '8px' }}>
                                                                        Ideal day-in-the-life:
                                                                    </Text>
                                                                    <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
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
                                                                    <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
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
                                                                    <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
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
                                                    title={<span style={{ color: '#fff' }}>🔄 Lifecycle & Spotlight Stories</span>}
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
                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', whiteSpace: 'pre-wrap' }}>
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
                                                                        <List.Item style={{ padding: '4px 0' }}>
                                                                            <Text style={{ color: '#fff' }}>
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
                                                                        <Text strong style={{ color: '#ff4d4f', display: 'block', marginBottom: '8px', fontSize: '14px' }}>
                                                                            Story {idx + 1}: {story.focus_area}
                                                                        </Text>
                                                                        <Space direction="vertical" style={{ width: '100%' }} size="small">
                                                                            <div>
                                                                                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>Why Important:</Text>
                                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                                                                                    {story.why_important}
                                                                                </Paragraph>
                                                                            </div>
                                                                            <div>
                                                                                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>Upstream & Downstream:</Text>
                                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                                                                                    {story.upstream_downstream}
                                                                                </Paragraph>
                                                                            </div>
                                                                            <div>
                                                                                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>Tools & Systems:</Text>
                                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                                                                                    {story.tools_and_systems}
                                                                                </Paragraph>
                                                                            </div>
                                                                            <div>
                                                                                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>Constraints & Risks:</Text>
                                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                                                                                    {story.constraints_and_risks}
                                                                                </Paragraph>
                                                                            </div>
                                                                            <div>
                                                                                <Text strong style={{ color: '#1890ff', fontSize: '12px' }}>Success Metrics:</Text>
                                                                                <Paragraph style={{ color: '#fff', marginBottom: '0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
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
                                        </Space>
                                    )}
                                </Tabs.TabPane>

                                {/* Fit Analysis Tab */}
                                <Tabs.TabPane tab="Fit Analysis" key="fit">
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
                        )}
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
