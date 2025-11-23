// frontend/src/types/api.types.ts

export interface Source {
    doc_id: string;
    title: string;
    text?: string;  // ✅ Added text field for document content
    url: string;
    score: number;
    // Airbnb 扩展字段（可选）
    price?: number;
    bedrooms?: number;
    neighbourhood?: string;
    room_type?: string;
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
        use_hybrid?: boolean;
        rrf_k?: number | null;
    };
    sources: Source[];
    metrics: {
        qps?: number;
        p95_ms?: number;
        recall_at_10?: number;
        total?: number;
        fusion?: any;
        rerank?: any;
        fusion_overlap?: number;
        rrf_candidates?: number;
        rerank_triggered?: boolean;
        rerank_timeout?: boolean;
        llm_enabled?: boolean;
        kv_enabled?: boolean;
        kv_hit?: boolean;
        llm_usage?: {
            prompt_tokens?: number;
            completion_tokens?: number;
            total_tokens?: number;
            cost_usd_est?: number | null;
            model?: string;
            use_kv_cache?: boolean;
        };
    };
    reranker_triggered: boolean;
    ts: string;
}

export interface ApiMetricsResponse {
    ok: boolean;
    p95_ms: number;
    recall_pct: number;
    qps: number;
    err_pct: number;
}

export interface RagTriadScores {
    context_relevance: number;
    groundedness: number;
    answer_relevance: number;
}

export interface AutoTunerStatus {
    status: 'idle' | 'running' | 'completed' | 'error';
    job_id?: string;
    progress?: number;
    current_params?: Record<string, any>;
}

export interface AutoTunerRecommendation {
    params: Record<string, any>;
    estimated_impact: {
        delta_p95_ms?: number;
        delta_recall_pct?: number;
    };
    reason: string;
    timestamp: string;
}

export interface ApiAutoTunerRecommendationsResponse {
    recommendations: AutoTunerRecommendation[];
}

export interface ApiRetrieverSimulationResponse {
    ok: boolean;
    results: RetrieverResultItem[];
}

export interface RetrieverResultItem {
    doc_id: string;
    title: string;
    score: number;
    rank: number;
}

export interface ApiRankerSimulationResponse {
    ok: boolean;
    results: RetrieverResultItem[];
}

export interface ApiIndexExplorerResponse {
    ok: boolean;
    points: ApiIndexPoint[];
}

export interface ApiIndexPoint {
    id: string;
    payload?: QdrantPointPayload;
}

export interface QdrantPointPayload {
    title?: string;
    text?: string;
    url?: string;
    [key: string]: any;
}

export interface AgentCodeFile {
    file_path: string;
    content: string;
    neighbors: AgentCodeNeighbor[];
}

export interface AgentCodeNeighbor {
    file_path: string;
    relationship: string;
}

export interface ApiAgentCodeResponse {
    ok: boolean;
    files: AgentCodeFile[];
    summary: string;
}

export interface ApiAgentResponse {
    files: AgentCodeFile[];
    summary: string;
}

export interface ApiAgentTuneResponse {
    ok: boolean;
    message: string;
}

export interface ApiQueryRequest {
    question: string;
    top_k?: number;
    rerank?: boolean;
    collection?: string;
    generate_answer?: boolean;
    stream?: boolean;
    use_kv_cache?: boolean;
    session_id?: string;
    profile_name?: string;          // ✅ Search profile name (e.g., 'airbnb_la_location_first')
    price_max?: number | null;      // ✅ Airbnb: Maximum price filter
    min_bedrooms?: number | null;   // ✅ Airbnb: Minimum bedrooms filter
    neighbourhood?: string | null;  // ✅ Airbnb: Neighbourhood filter
    room_type?: string | null;      // ✅ Airbnb: Room type filter
}

// ========================================
// KV Experiment API Types
// ========================================

export interface KvExperimentModeResult {
    num_runs: number;
    p50_ms: number;
    p95_ms: number;
    p50_first_token_ms: number;
    p95_first_token_ms: number;
    avg_total_tokens: number;
    avg_cost_usd: number;
    stream_enabled: boolean;
    kv_enabled: boolean;
    kv_hit_rate: number;
    stream_error_rate: number;
}

export interface KvExperimentRunRequest {
    question: string;
    collection?: string;
    profile_name?: string;
    runs_per_mode?: number;
    filters?: {
        price_max?: number;
        min_bedrooms?: number;
        neighbourhood?: string;
        room_type?: string;
    };
}

export interface KvExperimentRunResponse {
    ok: boolean;
    question: string;
    collection: string;
    profile_name?: string | null;
    modes: {
        baseline: KvExperimentModeResult;
        kv_only: KvExperimentModeResult;
        stream_only: KvExperimentModeResult;
        kv_and_stream: KvExperimentModeResult;
    };
    raw_samples?: any[];
    error?: string | null;
}

// ========================================
// Mortgage Agent API Types
// ========================================

export interface MortgagePlan {
    plan_id: string;
    name: string;
    monthly_payment: number;
    interest_rate: number;
    loan_amount: number;
    term_years: number;
    dti_ratio?: number | null;
    risk_level: 'low' | 'medium' | 'high';
    pros: string[];
    cons: string[];
    property_id?: string | null;
}

export interface MortgageAgentRequest {
    user_message: string;
    profile?: string;
    inputs?: {
        income?: number;
        debts?: number;
        purchase_price?: number;
        down_payment_pct?: number;
        state?: string;
    };
    property_id?: string | null;
}

export interface MaxAffordabilitySummary {
    max_monthly_payment: number;
    max_loan_amount: number;
    max_home_price: number;
    assumed_interest_rate: number;
    target_dti: number;
}

export interface AgentStep {
    step_id: string;
    step_name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    timestamp: string;
    duration_ms?: number | null;
    inputs?: Record<string, any> | null;
    outputs?: Record<string, any> | null;
    error?: string | null;
}

export interface CaseState {
    case_id: string;
    timestamp: string;
    inputs: Record<string, any>;
    plans: MortgagePlan[];
    max_affordability?: MaxAffordabilitySummary | null;
    risk_summary: Record<string, any>;
}

export interface MortgageAgentResponse {
    ok: boolean;
    agent_version: string;
    disclaimer: string;
    input_summary: string;
    plans: MortgagePlan[];
    followups: string[];
    max_affordability?: MaxAffordabilitySummary | null;
    error?: string | null;
    hard_warning?: string | null;
    llm_explanation?: string | null;
    llm_usage?: {
        prompt_tokens?: number;
        completion_tokens?: number;
        total_tokens?: number;
        cost_usd_est?: number | null;
        model?: string;
    } | null;
    lo_summary?: string | null;
    case_state?: CaseState | null;
    agent_steps?: AgentStep[] | null;
}

export interface MortgageProperty {
    id: string;
    name: string;
    city: string;
    state: string;
    purchase_price: number;
    property_tax_rate_pct: number;
    hoa_monthly: number;
    note?: string | null;
}

// ========================================
// Property Comparison Types
// ========================================
// [CHANGE] Added types for A/B property comparison feature
// These types match the backend schemas in services/fiqa_api/mortgage/schemas.py

export interface MortgagePropertySummary {
    property_id: string;
    display_name: string;
    city?: string | null;
    state?: string | null;
    listing_price: number;
}

export interface PropertyStressMetrics {
    monthly_payment: number;
    dti_ratio: number;
    risk_level: 'low' | 'medium' | 'high';
    within_affordability: boolean;
    dti_excess_pct?: number | null;
}

export interface PropertyComparisonEntry {
    property: MortgagePropertySummary;
    metrics: PropertyStressMetrics;
}

export interface MortgageCompareRequest {
    income: number;
    monthly_debts: number;
    down_payment_pct: number;
    state?: string | null;
    property_ids: string[];
}

export interface MortgageCompareResponse {
    ok: boolean;
    borrower_profile_summary: string;
    target_dti: number;
    max_affordability?: MaxAffordabilitySummary | null;
    properties: PropertyComparisonEntry[];
    best_property_id?: string | null;
    error?: string | null;
}

// ========================================
// Stress Check Types
// ========================================

export type StressBand = 'loose' | 'ok' | 'tight' | 'high_risk';

export interface ApprovalScore {
    /** Approval likelihood score from 0-100, where higher values indicate better approval chances */
    score: number;
    bucket: 'likely' | 'borderline' | 'unlikely';
    reasons?: string[] | null;
}

export interface SuggestedScenario {
    id: string;
    title: string;
    description?: string | null;
    scenario_key: 'income_minus_10' | 'price_minus_50k';
    reason?: string | null;
}

export interface StressCheckRequest {
    monthly_income: number;
    other_debts_monthly: number;
    list_price: number;
    down_payment_pct?: number | null;
    zip_code?: string | null;
    state?: string | null;
    hoa_monthly?: number | null;
    tax_rate_est?: number | null;
    insurance_ratio_est?: number | null;
    risk_preference?: 'conservative' | 'neutral' | 'aggressive' | null;
    profile_id?: string | null;
}

export interface WalletSnapshot {
    monthly_income: number;
    annual_income: number;
    other_debts_monthly: number;
    safe_payment_band: {
        min_safe: number;
        max_safe: number;
    };
    risk_preference: string;
}

export interface HomeSnapshot {
    list_price: number;
    down_payment_pct: number;
    loan_amount: number;
    zip_code?: string | null;
    state?: string | null;
    hoa_monthly: number;
    tax_rate_est: number;
    insurance_ratio_est: number;
}

export interface RiskAssessment {
    risk_flags: string[];
    hard_block: boolean;
    soft_warning: boolean;
}

export interface StressCheckResponse {
    total_monthly_payment: number;
    principal_interest_payment: number;
    estimated_tax_ins_hoa: number;
    dti_ratio: number;
    stress_band: StressBand;
    hard_warning?: string | null;
    wallet_snapshot: WalletSnapshot;
    home_snapshot: HomeSnapshot;
    case_state?: CaseState | null;
    agent_steps?: AgentStep[] | null;
    llm_explanation?: string | null;
    assumed_interest_rate_pct?: number | null;
    assumed_tax_rate_pct?: number | null;
    assumed_insurance_ratio_pct?: number | null;
    local_cost_factors_source?: string | null;
    recommended_scenarios?: SuggestedScenario[] | null;
    approval_score?: ApprovalScore | null;
    risk_assessment?: RiskAssessment | null;
}

// ========================================
// Single Home Agent Types
// ========================================
// NOTE: These types match the backend schemas in services/fiqa_api/mortgage/schemas.py
// SingleHomeAgentResponse fields:
//   - borrower_narrative: Optional[str] - Short, friendly explanation for the borrower
//   - recommended_actions: Optional[List[str]] - 1-3 bullet-style next steps
//   - stress_result.llm_explanation: Optional[str] - Raw LLM explanation (fallback if narrative/actions missing)

export interface SingleHomeAgentRequest {
    stress_request: StressCheckRequest;
    user_message?: string | null;
}

export interface MortgageProgramPreview {
    program_id: string;
    name: string;
    state?: string | null;
    max_dti?: number | null; // 0-1
    summary?: string | null;
    tags?: string[] | null;
}

export interface SingleHomeAgentResponse {
    stress_result: StressCheckResponse;
    borrower_narrative?: string | null;
    recommended_actions?: string[] | null;
    llm_usage?: {
        prompt_tokens?: number;
        completion_tokens?: number;
        total_tokens?: number;
        cost_usd_est?: number | null;
        model?: string;
    } | null;
    safety_upgrade?: SafetyUpgradeResult | null;
    mortgage_programs_preview?: MortgageProgramPreview[] | null;
    risk_assessment?: RiskAssessment | null;
    strategy_lab?: StrategyLabResult | null;
}

// ========================================
// Safer Homes Types
// ========================================

export interface LocalListingSummary {
    listing_id: string;
    title: string;
    city: string;
    state: string;
    zip_code: string;
    list_price: number;
    hoa_monthly?: number | null;
    beds?: number | null;
    baths?: number | null;
    sqft?: number | null;
}

export interface SaferHomeCandidate {
    listing: LocalListingSummary;
    stress_band: StressBand;
    dti_ratio?: number | null;
    total_monthly_payment?: number | null;
    comment?: string | null;
}

export interface SaferHomesResult {
    baseline_band?: StressBand | null;
    baseline_dti_ratio?: number | null;
    zip_code?: string | null;
    candidates: SaferHomeCandidate[];
}

// ========================================
// Safety Upgrade Types
// ========================================

export interface SafetyUpgradeSuggestion {
    reason: string;
    title: string;
    details: string;
    delta_dti?: number | null;
    target_price?: number | null;
    notes?: string[] | null;
}

export interface SafetyUpgradeResult {
    baseline_band?: StressBand | null;
    baseline_dti?: number | null;
    baseline_total_payment?: number | null;
    baseline_zip_code?: string | null;
    baseline_state?: string | null;
    baseline_is_tight_or_worse: boolean;
    safer_homes?: SaferHomesResult | null;
    primary_suggestion?: SafetyUpgradeSuggestion | null;
    alternative_suggestions?: SafetyUpgradeSuggestion[];
    mortgage_programs_checked?: boolean | null;
    mortgage_programs_hit_count?: number | null;
}

// ========================================
// Strategy Lab Types
// ========================================

export interface StrategyScenario {
    id: string;
    title: string;
    description?: string | null;
    price_delta_abs?: number | null;
    price_delta_pct?: number | null;
    down_payment_pct?: number | null;
    risk_preference?: 'conservative' | 'neutral' | 'aggressive' | null;
    note_tags?: string[] | null;
    stress_band?: StressBand | null;
    dti_ratio?: number | null;
    total_payment?: number | null;
    approval_score?: ApprovalScore | null;
    risk_assessment?: RiskAssessment | null;
}

export interface StrategyLabResult {
    baseline_stress_band?: StressBand | null;
    baseline_dti?: number | null;
    baseline_total_payment?: number | null;
    baseline_approval_score?: ApprovalScore | null;
    baseline_risk_assessment?: RiskAssessment | null;
    scenarios?: StrategyScenario[] | null;
}

