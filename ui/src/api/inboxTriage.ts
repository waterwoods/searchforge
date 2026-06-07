/**
 * Unified Intake MVP — Inbox Triage API
 *
 * POST /api/inbox/triage
 * Accepts pasted message text, returns structured triage output.
 */
import request from './request';

export interface CaseNote {
    note_id: string;
    body: string;
    created_at: string;
}

export interface CaseActivityItem {
    activity_id: string;
    activity_type: string;
    message: string;
    created_at: string;
}

export interface ConversationTurn {
    role: 'customer' | 'system';
    text: string;
}

export interface TriageResult {
    issue_category: string;
    urgency: 'low' | 'medium' | 'high' | 'critical';
    manual_followup_needed: boolean;
    broker_next_step: string;
    client_prep: string;
    client_reply_draft: string;
    case_id?: string;
    case_status?: CaseStatus;
    created_at?: string;
    updated_at?: string;
    /** First office-visible persist (formal submit); stable across follow-up appends */
    formal_submitted_at?: string;
    source_text?: string;
    waiting_on?: WaitingOn;
    next_contact_by?: string;
    case_notes?: CaseNote[];
    case_activity?: CaseActivityItem[];
    case_persisted?: boolean;
    handoff_ready?: boolean;
    conversation_summary?: string;
    /** Mixed-intent: customer also asked about this (e.g. "Also asked: garaging/dec page meaning") */
    secondary_issue_note?: string;
    /** Append flow: same thread vs new-issue boundary hint (rule-based) */
    case_boundary?: 'new_issue' | 'borderline' | 'same_case';
    /** Append enforcement: backend blocked mutating old case due to clear new issue */
    append_blocked_new_issue?: boolean;
    /** Append enforcement action for boundary result */
    case_boundary_action?: 'append_allowed' | 'requires_confirmation' | 'requires_new_case';
    /** Append enforcement: old case mutation should stay false when blocked */
    old_case_mutated?: boolean;
    /** Optional operator-friendly boundary reason */
    boundary_reason?: string;
    follow_up_type?: string;
    collection_stage?: 'collecting' | 'enough_for_handoff';
    /** Add-car / new quote: structured fields already collected (year, make_model, zip, delivery_date, primary_driver, vin) */
    collected_fields?: string[];
    /** V5: structural broker-usable case (tier-1 + completeness policy); optional on older backends */
    case_usable?: boolean;
    /** V2.6: min-core bar met — safe to auto-progress toward quote */
    action_ready?: boolean;
    /** collecting | near_usable | usable | action_ready — intake progression milestone */
    intake_flow_milestone?: 'collecting' | 'near_usable' | 'usable' | 'action_ready';
    /** User-chat path: fields still needed from the customer before structural usability */
    still_needed_user_flow?: string[];
    /** Deferred to office/broker; should not block user chat path */
    deferred_to_broker_fields?: string[];
    /** Add-car / new quote: fields still needed before quote */
    still_needed_fields?: string[];
    /** Add-car only: quote_ready | almost_ready | need_more — for broker visibility (ADD_CAR_REAL_INTAKE_LITE) */
    quote_ready_status?: 'quote_ready' | 'almost_ready' | 'need_more';
    /** True when server replaced client_reply_draft with quote-ready conversion copy (additive). */
    conversion_layer_active?: boolean;
    /** Whether broker should explicitly confirm high‑risk fields before acting */
    human_confirmation_required?: boolean;
    /** Which structured fields are driving the confirmation recommendation */
    human_confirmation_fields?: string[];
    /** Phase 2: session/conversation ID when no case persisted */
    conversation_id?: string;
    /** Phase 2: what to ask next when handoff_ready=false */
    next_best_question?: string;
    /** Phase 2: collecting | handoff_pending | handed_off | office_followup */
    lifecycle_status?: 'collecting' | 'handoff_pending' | 'handed_off' | 'office_followup';
    /** Derived primary UX axis (additive); prefer over lifecycle_status for user-facing progress. */
    case_lifecycle?: 'collecting' | 'almost_ready' | 'ready_for_handoff' | 'submitted';
    /** Add-car: when a post-submit correction invalidates stale persisted slot ids (merge policy) */
    add_car_merge?: {
        correction_turn: boolean;
        invalidated_slots?: string[];
    };
    /** Add-Car: resolved current-turn intent (API may omit or null on non–Add-Car paths) */
    add_car_turn_intent?: {
        intent_family?: string;
        handoff_base_key?: string | null;
        truth_notes?: string[];
        phrase_storage_key?: string | null;
    } | null;
    /** Message-level history: role, text, sequence — for Recent customer messages */
    case_messages?: Array<{ role: string; text: string; sequence?: number; created_at?: string }>;
    /** Signal for UI: suggest persist when handoff_ready and meaningful */
    case_creation_suggested?: boolean;
    /** Speed routing: "fast" | "llm" | "rule" — for debugging */
    triage_path?: string;
    /**
     * Post-triage assist layer payload (additive). Never required for core UI.
     * See `triageResultContract.ts` for CORE vs OPTIONAL classification.
     */
    assist?: Record<string, unknown> | null;
    /** When TRIAGE_RETURN_PERF_METRICS is enabled on the server */
    route_perf?: Record<string, number> | null;
    /** Latency / metrics snapshot from triage turn (shape varies by backend version) */
    triage_turn_metrics?: Record<string, unknown> | null;
    /** Greenfield triage vs append-follow-up; disambiguates handoff_ready (Add-Car pilot contract). */
    triage_mode?: 'greenfield' | 'append';
    /** Stage-1 service lane when set (e.g. add_car) */
    service_lane?: string;
    /** Explicit lightweight service type */
    service_type?: string;
    /** Add-Car vehicle identity key (nullable) */
    vehicle_key?: string | null;
    /** True when customer text suggests more than one vehicle; vehicle_key stays primary/first only */
    additional_vehicle_mentioned?: boolean | null;
    /** Human-readable primary vehicle line aligned with vehicle_key (nullable) */
    primary_vehicle_summary?: string | null;
    /** When multi-vehicle: lightweight hint (e.g. 2); not a fleet counter */
    additional_vehicle_count_hint?: number | null;
    /** Rerouting: when soft_route conflicted with text intent */
    reroute_occurred?: boolean;
    reroute_message?: string;
    previous_soft_route?: string;
    new_intent?: string;
    /** A | B | C — questioning / confirmation style (server; optional) */
    intake_evolution_variant?: 'A' | 'B' | 'C';
    /** V6 auto-input variant (client-pack ui_copy or V6_AUTO_INPUT_VARIANT) */
    v6_auto_input_variant?: 'A' | 'B' | 'C';
    /** V4 zero-question path (B/C): server sets when case_draft uses V4 bundle */
    zero_question_intake?: boolean;
    /** Modeled / heuristic inference risk for broker review (0–1) */
    v4_error_risk_score?: number;
    /** Auto case draft: known / missing / confidence (add-car + generic) */
    case_draft?: {
        lane?: string;
        intent?: string;
        known_fields?: Record<string, { confidence?: number; source?: string }>;
        inferred_fields?: Record<string, { hint?: string; confidence?: number; needs_confirmation?: boolean }>;
        missing_fields?: string[];
        confidence_map?: Record<string, number>;
        needs_confirmation?: string[];
        quote_ready_status?: string;
        completion_message?: string;
        completion_fraction?: number | null;
        /** V6: single-block confirmation preview + OCR highlights (optional) */
        v6_confirmation?: {
            headline?: string;
            lines?: string[];
            ocr_highlight_field_keys?: string[];
            single_confirmation_step?: boolean;
        };
        v6_error_tolerance?: {
            low_confidence_field_keys?: string[];
            submission_blocked?: boolean;
            policy_note?: string;
        };
        merged_text_for_v6?: string;
    };
    /** Stage-1 optional light identity (nullable; not auth) */
    identity_binding_state?: 'unbound' | 'prompted' | 'deferred' | 'linked' | null;
    person_link_key?: string | null;
    person_link_source?: 'wechat' | 'phone' | 'email' | null;
    person_link_confidence?: number | null;
}

export type CaseStatus = 'new' | 'reviewing' | 'waiting_client' | 'done';
export type WaitingOn = 'none' | 'client' | 'broker' | 'carrier' | 'underwriting';

/** ADD_CAR_ATTACHMENT_READY_LITE: attachment metadata on case */
export interface CaseAttachment {
    attachment_id: string;
    filename: string;
    type: 'registration' | 'vin_photo' | 'dec_page' | 'screenshot';
    size_bytes: number;
    created_at: string;
}

/** Office workbench enrichment (GET /api/inbox/cases); optional on older payloads */
export type WorkbenchLaneKind = 'explicit' | 'legacy' | 'other';
export type PgMirrorState = 'unknown' | 'mirrored' | 'pg_missing' | 'mismatch';

export interface SavedCase extends TriageResult {
    case_id: string;
    case_status: CaseStatus;
    created_at: string;
    updated_at: string;
    source_text: string;
    /** ADD_CAR_ATTACHMENT_READY_LITE: uploaded materials */
    case_attachments?: CaseAttachment[];
    /** Optional: session_id that created this case (Minimal Production Backbone traceability) */
    origin_session_id?: string;
    /** Optional: client_id for append/reopen lifecycle (Client Identity Persistence) */
    client_id?: string;
    /** ADD_CAR_IDENTITY_CONTACT_LITE: lightweight customer contact */
    customer_name?: string;
    customer_phone?: string;
    customer_email?: string;
    /** Workbench: operator-marked test data */
    workbench_test?: boolean;
    /** Workbench: soft-archive (hidden in default “正式” views) */
    workbench_archived?: boolean;
    /** explicit add_car lane vs heuristic legacy vs other */
    workbench_lane_kind?: WorkbenchLaneKind;
    /** Postgres mirror glance when DB configured */
    pg_mirror_state?: PgMirrorState;
}

/** Soft-route intent from quick-start button (add_car, remove_car, claim_intake, cancellation_warning, missing_document, talk_to_agent) */
export type SoftRouteIntent =
    | 'add_car'
    | 'remove_car'
    | 'claim_intake'
    | 'cancellation_warning'
    | 'missing_document'
    | 'talk_to_agent';

/** Optional Stage-1 identity payload (formal submit; client-pack gated in UI) */
export type IdentityBindingState = 'unbound' | 'prompted' | 'deferred' | 'linked';

export interface LightIdentityPayload {
    identity_binding_state?: IdentityBindingState;
    person_link_key?: string | null;
    person_link_source?: 'wechat' | 'phone' | 'email' | null;
    person_link_confidence?: number | null;
}

const SESSION_ID_KEY = 'unified_intake_session_id';

/** Get existing session_id without creating (for restore check) */
export function getSessionId(): string | null {
    try {
        const sid = localStorage.getItem(SESSION_ID_KEY);
        return sid && sid.length >= 10 ? sid : null;
    } catch {
        return null;
    }
}

/** Get or create session_id for in-progress Customer Entry continuity (Phase 2) */
export function getOrCreateSessionId(): string {
    try {
        let sid = localStorage.getItem(SESSION_ID_KEY);
        if (!sid || sid.length < 10) {
            sid = crypto.randomUUID?.() ?? `sess_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
            localStorage.setItem(SESSION_ID_KEY, sid);
        }
        return sid;
    } catch {
        return '';
    }
}

/** Clear session_id when starting new conversation */
export function clearSessionId(): void {
    try {
        localStorage.removeItem(SESSION_ID_KEY);
    } catch {
        /* ignore */
    }
}

/** Role C simulation: next customer line from bounded LLM (backend). */
export interface SimulationRoleCCustomerResponse {
    customer_message: string;
    llm_used: boolean;
    model: string | null;
    turn_index: number;
    max_turns: number;
}

export async function fetchSimulationRoleCCustomer(params: {
    persona_id: string;
    optional_note?: string;
    difficulty: string;
    max_turns: number;
    conversation_turns: ConversationTurn[];
    client_id?: string | null;
}): Promise<SimulationRoleCCustomerResponse> {
    const payload: Record<string, unknown> = {
        persona_id: params.persona_id,
        optional_note: (params.optional_note ?? '').trim(),
        difficulty: params.difficulty,
        max_turns: params.max_turns,
        conversation_turns: params.conversation_turns,
    };
    if (params.client_id?.trim()) {
        payload.client_id = params.client_id.trim();
    }
    const response = await request.post<SimulationRoleCCustomerResponse>(
        '/api/inbox/simulation-role-c-customer',
        payload,
    );
    return response.data;
}

/** Optional inline image: server runs OCR and merges into v6_ocr_signals (text may be empty). */
export interface InlineImagePayload {
    base64: string;
    contentType?: string;
}

export async function triageMessage(
    text: string,
    persistCase = false,
    conversationTurns?: ConversationTurn[],
    softRoute?: SoftRouteIntent,
    sessionId?: string | null,
    clientId?: string | null,
    /** Add-Car: true when customer (or broker direct paste) is performing formal office submit. */
    formalSubmit = false,
    /** When customer continues the same persisted record, enables post-submit reply routing. */
    caseId?: string | null,
    /** Optional Stage-1 identity fields (only sent when UI enables; typically with formal formalSubmit). */
    identity?: LightIdentityPayload | null,
    /** When set, backend OCRs image and merges with case; `text` can be empty. */
    inlineImage?: InlineImagePayload | null,
): Promise<TriageResult> {
    const payload: {
        text: string;
        persist_case: boolean;
        formal_submit?: boolean;
        conversation_turns?: ConversationTurn[];
        soft_route?: string;
        session_id?: string;
        client_id?: string;
        case_id?: string;
        identity_binding_state?: string;
        person_link_key?: string | null;
        person_link_source?: string;
        person_link_confidence?: number;
        inline_image_base64?: string;
        inline_image_content_type?: string;
    } = {
        text: text.trim(),
        persist_case: persistCase,
    };
    if (formalSubmit) {
        payload.formal_submit = true;
    }
    const cid = (caseId ?? '').trim();
    if (cid) {
        payload.case_id = cid;
    }
    if (conversationTurns && conversationTurns.length > 0) {
        payload.conversation_turns = conversationTurns;
    }
    if (softRoute) {
        payload.soft_route = softRoute;
    }
    const sid = sessionId ?? getOrCreateSessionId();
    if (sid) {
        payload.session_id = sid;
    }
    if (clientId && clientId.trim()) {
        payload.client_id = clientId.trim();
    }
    if (identity && typeof identity === 'object') {
        const ib = identity.identity_binding_state;
        if (ib && ['unbound', 'prompted', 'deferred', 'linked'].includes(ib)) {
            payload.identity_binding_state = ib;
        }
        if (identity.person_link_key !== undefined && identity.person_link_key !== null) {
            payload.person_link_key = identity.person_link_key;
        }
        if (identity.person_link_source !== undefined && identity.person_link_source !== null) {
            payload.person_link_source = identity.person_link_source;
        }
        if (
            identity.person_link_confidence !== undefined &&
            identity.person_link_confidence !== null &&
            !Number.isNaN(identity.person_link_confidence)
        ) {
            payload.person_link_confidence = identity.person_link_confidence;
        }
    }
    if (inlineImage?.base64?.trim()) {
        payload.inline_image_base64 = inlineImage.base64.trim();
        if (inlineImage.contentType?.trim()) {
            payload.inline_image_content_type = inlineImage.contentType.trim();
        }
    }
    // Server may include route_perf when TRIAGE_RETURN_PERF_METRICS=1 (staging / profiling).
    const response = await request.post<TriageResult>('/api/inbox/triage', payload);
    return response.data;
}

/** GET /api/inbox/cases — paginated recent persisted cases */
export interface ListRecentCasesResponse {
    cases: SavedCase[];
    total_count: number;
    limit: number;
    offset: number;
    has_more: boolean;
}

/** GET /api/inbox/cases/{case_id} — full persisted case (use after opening from queue). */
export async function getSavedCase(caseId: string): Promise<SavedCase> {
    const response = await request.get<SavedCase>(`/api/inbox/cases/${encodeURIComponent(caseId)}`);
    return response.data;
}

export async function listRecentCasesPage(params: {
    limit?: number;
    offset?: number;
}): Promise<ListRecentCasesResponse> {
    const limit = params.limit ?? 50;
    const offset = params.offset ?? 0;
    const response = await request.get<ListRecentCasesResponse>('/api/inbox/cases', {
        params: { limit, offset },
    });
    return {
        cases: response.data.cases ?? [],
        total_count: response.data.total_count ?? 0,
        limit: response.data.limit ?? limit,
        offset: response.data.offset ?? offset,
        has_more: Boolean(response.data.has_more),
    };
}

/** Backward-compatible: first page only */
export async function listRecentCases(limit = 8): Promise<SavedCase[]> {
    const r = await listRecentCasesPage({ limit, offset: 0 });
    return r.cases;
}

/** P16 Customer First — active add-car case summary from phone lookup */
export interface CustomerActiveCaseSummary {
    case_id: string;
    vehicle_display: string;
    missing_fields: string[];
    missing_fields_display?: string[];
    is_formal_submitted: boolean;
    submit_state: 'submitted' | 'not_yet';
    /** Customer-facing submit dimension */
    status_label?: 'saved_not_yet_submitted' | 'submitted_to_office';
    /** Customer-visible contact state derived from waiting_on + still_needed */
    contact_state?: 'waiting_for_customer' | 'office_reviewing' | 'broker_reviewing';
    /** Single customer-visible business state (four states only) */
    business_state?: 'awaiting_customer' | 'submitted_to_office' | 'office_processing' | 'closed';
    waiting_on?: string;
    primary_vehicle_summary?: string | null;
    still_needed_fields?: string[];
    lifecycle_status?: string;
    formal_submitted_at?: string;
    customer_name?: string;
    updated_at?: string;
}

export interface CustomerActiveCaseLookupResponse {
    has_active_case: boolean;
    phone_normalized: string;
    active_case: CustomerActiveCaseSummary | null;
}

export async function lookupActiveCaseByPhone(
    phone: string,
    clientId?: string | null,
): Promise<CustomerActiveCaseLookupResponse> {
    const response = await request.get<CustomerActiveCaseLookupResponse>('/api/inbox/customer/active-case', {
        params: {
            phone: phone.trim(),
            ...(clientId?.trim() ? { client_id: clientId.trim() } : {}),
        },
    });
    return response.data;
}

export async function startCustomerAddCarDraft(params: {
    phone: string;
    customerName?: string;
    clientId?: string | null;
    sessionId?: string | null;
}): Promise<{ ok: boolean; case_id: string; case: CustomerActiveCaseSummary }> {
    const response = await request.post<{ ok: boolean; case_id: string; case: CustomerActiveCaseSummary }>(
        '/api/inbox/customer/start-add-car',
        {
            phone: params.phone.trim(),
            customer_name: params.customerName?.trim() || undefined,
            client_id: params.clientId?.trim() || undefined,
            session_id: params.sessionId?.trim() || undefined,
        },
    );
    return response.data;
}

/** DELETE — only allowed when case is marked workbench_test (server-enforced). */
export async function deleteTestCase(caseId: string): Promise<void> {
    await request.delete(`/api/inbox/cases/${encodeURIComponent(caseId)}`);
}

/** Mark test / archive flags on a case (JSON-first; soft-hide only). */
export async function patchCaseWorkbench(
    caseId: string,
    updates: { is_test?: boolean; archived?: boolean },
): Promise<SavedCase> {
    const response = await request.patch<SavedCase>(`/api/inbox/cases/${caseId}/workbench`, updates);
    return response.data;
}

export async function updateSavedCaseStatus(caseId: string, status: CaseStatus): Promise<SavedCase> {
    const response = await request.patch<SavedCase>(`/api/inbox/cases/${caseId}/status`, {
        status,
    });
    return response.data;
}

export async function addSavedCaseNote(caseId: string, note: string): Promise<SavedCase> {
    const response = await request.post<SavedCase>(`/api/inbox/cases/${caseId}/notes`, {
        note: note.trim(),
    });
    return response.data;
}

export async function updateSavedCaseFollowUp(
    caseId: string,
    waitingOn: WaitingOn,
    nextContactBy: string,
): Promise<SavedCase> {
    const response = await request.patch<SavedCase>(`/api/inbox/cases/${caseId}/follow-up`, {
        waiting_on: waitingOn,
        next_contact_by: nextContactBy.trim(),
    });
    return response.data;
}

/** Upload attachment to a case (ADD_CAR_ATTACHMENT_READY_LITE) */
export async function uploadCaseAttachment(caseId: string, file: File): Promise<SavedCase> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await request.post<SavedCase>(`/api/inbox/cases/${caseId}/attachments`, formData);
    return response.data;
}

/** Get attachment download URL (relative to API base) */
export function getAttachmentDownloadUrl(caseId: string, attachmentId: string): string {
    return `/api/inbox/cases/${caseId}/attachments/${attachmentId}`;
}

/** Update customer contact fields on a saved case (ADD_CAR_IDENTITY_CONTACT_LITE) */
export async function updateSavedCaseCustomer(
    caseId: string,
    updates: { customer_name?: string; customer_phone?: string; customer_email?: string },
): Promise<SavedCase> {
    const response = await request.patch<SavedCase>(`/api/inbox/cases/${caseId}/customer`, updates);
    return response.data;
}

/** Paste a new customer follow-up message into an existing case. Re-triages in context and updates case fields. */
export async function appendFollowUpMessage(
    caseId: string,
    newMessage: string,
    clientId?: string | null,
): Promise<SavedCase> {
    const payload: { new_message: string; client_id?: string } = {
        new_message: newMessage.trim(),
    };
    if (clientId && clientId.trim()) {
        payload.client_id = clientId.trim();
    }
    const response = await request.post<SavedCase>(`/api/inbox/cases/${caseId}/append-message`, payload);
    return response.data;
}

/** In-progress session restore: get turns + workflow_state by session_id for refresh recovery. */
export interface InProgressSession {
    turns: Array<{ role: 'customer' | 'system'; text: string; triageResult?: TriageResult }>;
    workflow_state: Partial<
        Pick<
            TriageResult,
            | 'handoff_ready'
            | 'lifecycle_status'
            | 'case_lifecycle'
            | 'collection_stage'
            | 'collected_fields'
            | 'still_needed_fields'
            | 'next_best_question'
        >
    >;
    updated_at?: string;
    /** Pending optional WeChat binding before formal submit (session JSON truth). */
    light_identity_binding?: LightIdentityPayload | null;
}

export async function getInProgressSession(sessionId: string): Promise<InProgressSession | null> {
    try {
        const response = await request.get<InProgressSession>(`/api/inbox/session/${sessionId}`);
        return response.data;
    } catch {
        return null;
    }
}

/** Optional WeChat binding (live client-pack): OAuth start or dev simulate. */
export async function fetchWeChatBindingStart(
    sessionId: string,
    clientId: string,
): Promise<{ authorize_url: string | null; state: string | null; dev_simulate: boolean }> {
    const response = await request.get<{
        authorize_url: string | null;
        state: string | null;
        dev_simulate: boolean;
    }>('/api/inbox/wechat/binding/start', {
        params: { session_id: sessionId, client_id: clientId },
    });
    return response.data;
}

export async function postWeChatBindingSimulateComplete(
    sessionId: string,
    clientId: string,
): Promise<{ ok: boolean }> {
    const response = await request.post<{ ok: boolean }>('/api/inbox/wechat/binding/simulate-complete', null, {
        params: { session_id: sessionId, client_id: clientId },
    });
    return response.data;
}

/** Add-Car Quote rules (Rules Center) */
export interface AddCarRules {
    ask_vehicle: { zh: string; en: string };
    ask_zip: { zh: string; en: string };
    ask_delivery_driver: { zh: string; en: string };
    first_reply: { zh: string; en: string };
    handoff: { zh: string; en: string };
    /** When false, backend config is read-only (e.g. Cloud Run); publish disabled. */
    publishable?: boolean;
}

export interface AddCarRulesOverride {
    ask_vehicle?: { zh?: string; en?: string };
    ask_zip?: { zh?: string; en?: string };
    ask_delivery_driver?: { zh?: string; en?: string };
}

export async function getAddCarRules(): Promise<AddCarRules> {
    const response = await request.get<AddCarRules>('/api/inbox/add-car-rules');
    return response.data;
}

export async function previewAddCarRules(
    text: string,
    conversationTurns?: Array<{ role: 'customer' | 'system'; text: string }>,
    rulesOverride?: AddCarRulesOverride,
): Promise<TriageResult> {
    const payload: {
        text: string;
        conversation_turns?: ConversationTurn[];
        rules_override?: AddCarRulesOverride;
    } = { text: text.trim() };
    if (conversationTurns && conversationTurns.length > 0) {
        payload.conversation_turns = conversationTurns;
    }
    if (rulesOverride && (rulesOverride.ask_vehicle || rulesOverride.ask_zip || rulesOverride.ask_delivery_driver)) {
        payload.rules_override = rulesOverride;
    }
    const response = await request.post<TriageResult>('/api/inbox/add-car-rules/preview', payload);
    return response.data;
}

export async function publishAddCarRules(rules: {
    ask_vehicle: { zh: string; en: string };
    ask_zip: { zh: string; en: string };
    ask_delivery_driver: { zh: string; en: string };
}): Promise<{ ok: boolean; message: string }> {
    const response = await request.put<{ ok: boolean; message: string }>('/api/inbox/add-car-rules', rules);
    return response.data;
}

/** Scenario Logic Center — aggregated scenario inventory for founder/broker review */
export interface ScenarioLogicItem {
    id: string;
    name: string;
    group: string;
    business_goal: string;
    common_phrasing: string[];
    main_route: string;
    ask_next: string;
    handoff_timing: string;
    broker_next_step: string;
    config_layer: string;
    config_sources: string[];
    maturity: 'strong' | 'medium' | 'weak';
    trial_order: number | null;
    sim_ids: string[];
    fix_status: 'fix_now' | 'fix_next' | 'defer' | null;
}

export interface ScenarioLogicCenter {
    version: string;
    description?: string;
    updated?: string;
    summary: {
        total_scenarios: number;
        strong: number;
        medium: number;
        weak: number;
        trial_recommended?: string[];
    };
    groups?: Record<string, { label: string; description: string }>;
    scenarios: ScenarioLogicItem[];
}

export async function getScenarioLogicCenter(): Promise<ScenarioLogicCenter> {
    const response = await request.get<ScenarioLogicCenter>('/api/inbox/scenario-logic-center');
    return response.data;
}
