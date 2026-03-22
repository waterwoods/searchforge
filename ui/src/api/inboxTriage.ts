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
    follow_up_type?: string;
    collection_stage?: 'collecting' | 'enough_for_handoff';
    /** Add-car / new quote: structured fields already collected (year, make_model, zip, delivery_date, primary_driver, vin) */
    collected_fields?: string[];
    /** Add-car / new quote: fields still needed before quote */
    still_needed_fields?: string[];
    /** Add-car only: quote_ready | almost_ready | need_more — for broker visibility (ADD_CAR_REAL_INTAKE_LITE) */
    quote_ready_status?: 'quote_ready' | 'almost_ready' | 'need_more';
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
    /** correction, already_sent, etc. — for handoff context badge */
    follow_up_type?: string;
    /** Message-level history: role, text, sequence — for Recent customer messages */
    case_messages?: Array<{ role: string; text: string; sequence?: number; created_at?: string }>;
    /** Signal for UI: suggest persist when handoff_ready and meaningful */
    case_creation_suggested?: boolean;
    /** Speed routing: "fast" | "llm" | "rule" — for debugging */
    triage_path?: string;
    /** Rerouting: when soft_route conflicted with text intent */
    reroute_occurred?: boolean;
    reroute_message?: string;
    previous_soft_route?: string;
    new_intent?: string;
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
}

/** Soft-route intent from quick-start button (add_car, remove_car, claim_intake, cancellation_warning, missing_document, talk_to_agent) */
export type SoftRouteIntent =
    | 'add_car'
    | 'remove_car'
    | 'claim_intake'
    | 'cancellation_warning'
    | 'missing_document'
    | 'talk_to_agent';

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

export async function triageMessage(
    text: string,
    persistCase = false,
    conversationTurns?: ConversationTurn[],
    softRoute?: SoftRouteIntent,
    sessionId?: string | null,
    clientId?: string | null,
): Promise<TriageResult> {
    const payload: {
        text: string;
        persist_case: boolean;
        conversation_turns?: ConversationTurn[];
        soft_route?: string;
        session_id?: string;
        client_id?: string;
    } = {
        text: text.trim(),
        persist_case: persistCase,
    };
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
    const response = await request.post<TriageResult>('/api/inbox/triage', payload);
    return response.data;
}

export async function listRecentCases(limit = 8): Promise<SavedCase[]> {
    const response = await request.get<{ cases: SavedCase[] }>('/api/inbox/cases', {
        params: { limit },
    });
    return response.data.cases ?? [];
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
    workflow_state: Partial<Pick<TriageResult, 'handoff_ready' | 'lifecycle_status' | 'collection_stage' | 'collected_fields' | 'still_needed_fields' | 'next_best_question'>>;
    updated_at?: string;
}

export async function getInProgressSession(sessionId: string): Promise<InProgressSession | null> {
    try {
        const response = await request.get<InProgressSession>(`/api/inbox/session/${sessionId}`);
        return response.data;
    } catch {
        return null;
    }
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
