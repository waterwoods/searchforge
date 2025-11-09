// frontend/src/types/api.types.ts
export interface ApiMetricsResponse {
    ok: boolean;
    p95_ms: number;
    recall_pct: number;
    qps: number;
    err_pct: number;
    [key: string]: any; // Allow other properties
}

export interface Source {
    doc_id: string;
    title: string;
    url: string;
    score: number;
}

export interface ApiQueryResponse {
    ok: boolean;
    trace_id: string;
    question: string;
    answer: string;
    latency_ms: number;
    route: string;
    params: {
        top_k: number;
        rerank: boolean;
    };
    sources: Source[];
    ts: string;
}

export interface ApiTraceStage {
    stage_name: string;
    start_ms: number;
    duration_ms: number;
    meta?: {
        top_k?: number;
        index?: string;
        prompt_tokens?: number;
        model?: string;
    };
}

export interface ApiTraceResponse {
    ok: boolean;
    trace_id: string;
    total_ms: number;
    stages: ApiTraceStage[];
    ts: string;
}

export interface ExperimentParams {
    top_k: number;
    rerank: boolean;
    ranker: string | null;
    chunk: string;
}

export interface ApiExperimentItem {
    exp_id: string;
    created_at: string;
    engine: string;
    params: ExperimentParams;
    p95_ms: number;
    qps: number;
    err_pct: number;
    recall_k: number;
    verdict: 'PASS' | 'EDGE' | 'FAIL';
}

export interface ApiLeaderboardResponse {
    items: ApiExperimentItem[];
    total: number;
}

// --- For Code Lookup ---
export interface AgentCodeNeighbor {
    path: string;
    snippet: string;
    relation: string; // e.g., 'called_by', 'calls', 'imports', 'calls_this_function'
    name: string; // Function/Class name
    start_line: number;
    end_line: number;
}

export interface AgentCodeFile {
    path: string;
    language: string;
    start_line: number;
    end_line: number;
    snippet: string;
    why_relevant: string;
    neighbors?: AgentCodeNeighbor[]; // One-hop neighbor information
}

export interface ApiAgentCodeResponse {
    agent: string;
    intent: 'code_lookup';
    query: string;
    summary_md: string;
    files: AgentCodeFile[];
}

// --- For AI Tuning ---
export interface ApiAgentTuneResponse {
    agent: string;
    intent: 'optimize_latency';
    message_md: string;
    params_patch: {
        top_k: number;
        rerank: boolean;
        ranker: string;
        rerank_top_n: number;
    };
    apply_hint: string;
}

// A union type for our handler
export type ApiAgentResponse = ApiAgentCodeResponse | ApiAgentTuneResponse;

export interface RagTriadScores {
    context_relevance: number;
    groundedness: number;
    answer_relevance: number;
}

export interface ApiTriadSample {
    trace_id: string;
    question: string;
    answer_snippet: string;
    evidence_snippet: string;
    scores: RagTriadScores;
    labels: string[];
}

export interface ApiRagTriadResponse {
    exp_id: string;
    summary: RagTriadScores;
    samples: ApiTriadSample[];
}

// --- For Retriever Lab ---
export interface RetrieverResultItem {
    doc_id: string;
    score: number;
    text_snippet: string;
}

export interface ApiRetrieverSimulationResponse {
    ok: boolean;
    params: { ef?: number; nprobe?: number;[key: string]: any }; // Example params
    results: RetrieverResultItem[];
    metrics: {
        p95_ms: number;
        recall_at_10: number;
    };
}

// --- For Ranker Lab ---
export interface ApiRankerSimulationResponse {
    ok: boolean;
    model_name: string; // e.g., "cross-encoder/ms-marco-MiniLM-L-6-v2" or "LLM Ranker (GPT-3.5)"
    results: RetrieverResultItem[]; // Reusing the same structure
    metrics: {
        ndcg_at_10: number; // Example quality metric
        latency_ms: number; // How long ranking took
    };
}

// --- For Index Explorer ---
export interface QdrantPointPayload {
    text: string;
    file_path: string;
    chunk_index: number;
    kind?: string;       // Optional: 'function', 'class', 'file', etc.
    name?: string | null; // Optional: function/class name
    start_line?: number | null; // Optional: start line in source
    end_line?: number | null;   // Optional: end line in source
    edges_json?: string; // Optional: JSON string of code relationships
    // Add other potential metadata fields if known
}

export interface ApiIndexPoint {
    id: string; // Qdrant point ID (UUID or int)
    payload: QdrantPointPayload;
    // We might not need the vector itself for display
}

export interface ApiIndexExplorerResponse {
    ok: boolean;
    points: ApiIndexPoint[];
    total: number;
    next_page_offset?: string | number; // For pagination
}

// --- For SLA Tuner Lab ---
export interface AutoTunerStatus {
    ok: boolean;
    job_id: string;
    status: 'idle' | 'running' | 'completed' | 'error';
    current_params: Record<string, any>; // e.g., { top_k: 10, rerank: true }
    progress?: number; // 0-100
    last_update: string;
}

export interface AutoTunerRecommendation {
    params: Record<string, any>;
    estimated_impact: {
        delta_p95_ms?: number;
        delta_recall_pct?: number;
        [key: string]: number | undefined;
    };
    reason: string;
    timestamp: string;
}

export interface ApiAutoTunerRecommendationsResponse {
    ok: boolean;
    job_id: string;
    recommendations: AutoTunerRecommendation[];
}

