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

/** P19H-3c-3A — per-slot Claim evidence row for Workbench checklist */
export type ClaimEvidenceSlot = {
    slot_key: string;
    label: string;
    required_level: 'required' | 'soft_required' | 'optional' | string;
    status: 'missing' | 'received' | 'skipped' | 'needs_retake' | string;
    source_channel: string;
    attachment_count: number;
    latest_attachment: null | {
        attachment_id?: string;
        filename?: string;
        mime_type?: string;
        source?: string;
        received_at?: string;
        [key: string]: unknown;
    };
    skip_reason: string | null;
    needs_broker_review: boolean;
};

/** P19H-3d — unassigned WeCom photos pending broker slot classification */
export type ClaimUnassignedWecomPhoto = {
    attachment_id?: string | null;
    filename?: string | null;
    mime_type?: string | null;
    source?: string;
    received_at?: string | null;
    needs_broker_review?: boolean;
};

export type ClaimUnassignedWecomPhotos = {
    count: number;
    items: ClaimUnassignedWecomPhoto[];
    broker_next_action?: string;
};

/** P19H-3c-3A — Claim evidence checklist summary for Workbench drawer */
export type ClaimEvidenceSummary = {
    slots: ClaimEvidenceSlot[];
    missing_required_slots: string[];
    missing_soft_required_slots: string[];
    received_slots: string[];
    skipped_slots: string[];
    completion_level: 'empty' | 'partial' | 'required_complete' | 'review_ready' | 'complete' | string;
    broker_next_action: string;
    summary_text: string;
    unassigned_wecom_photos?: ClaimUnassignedWecomPhotos;
};

/** P19H-3e-1 — Claim story timeline event */
export type ClaimTimelineEvent = {
    event_id: string;
    event_type: string;
    source_channel?: string;
    created_at?: string;
    actor?: string;
    message_id?: string | null;
    attachment_id?: string | null;
    text?: string | null;
    metadata?: Record<string, unknown>;
};

export type ClaimMissingInfoItem = {
    key: string;
    label: string;
    severity: 'critical' | 'important' | 'optional' | string;
    reason: string;
};

export type ClaimBriefHighlight = {
    level: 'important' | 'missing' | 'received' | string;
    label: string;
    kind: 'injury' | 'missing_info' | 'evidence' | 'basics' | string;
};

/** P19H-3e-1 — Claim Case Brief for Workbench hero panel */
export type ClaimCaseBrief = {
    summary: string;
    customer?: {
        name?: string | null;
        phone?: string | null;
        wecom_external_userid?: string | null;
    };
    key_facts?: {
        accident_datetime?: string | null;
        accident_location?: string | null;
        accident_description?: string | null;
        injury_status?: 'yes' | 'no' | 'unknown' | string;
        police_involved?: 'yes' | 'no' | 'unknown' | string;
        other_party_info?: string | null;
        other_party_plate?: string | null;
        own_vehicle_info?: string | null;
    };
    evidence_received?: {
        photo_count?: number;
        photo_sources?: Record<string, number>;
        voice_count?: number;
        has_basics?: boolean;
        slots_received?: string[];
        slots_missing?: string[];
        unassigned_wecom_photos?: number;
    };
    missing_info?: ClaimMissingInfoItem[];
    highlights?: ClaimBriefHighlight[];
    next_best_question?: string;
    confidence?: 'low' | 'medium' | 'high' | string;
    source_event_ids?: string[];
    brief_updated_at?: string;
    brief_version?: number;
};

export type Slice1RequestItemType = 'vin' | 'policy_or_insurance_card' | 'free_text' | 'photo_evidence';

export type Slice1RequestItemStatus =
    | 'queued'
    | 'active'
    | 'in_progress'
    | 'satisfied'
    | 'withdrawn'
    | 'superseded'
    | string;

export type Slice1CustomerResponse = {
    kind: 'fact' | 'evidence' | 'missing' | string;
    field_id?: string | null;
    submitted_value?: string | null;
    canonical_value?: string | null;
    attachment_id?: string | null;
    evidence_ref?: string | null;
    submitted_at?: string | null;
    submitted_by_actor?: string | null;
    submitted_by?: string | null;
    receipt_event_id?: string | null;
    review_status?: string | null;
    applied_to_canonical_facts?: boolean;
    message?: string;
    value_redacted?: boolean;
};

export type Slice1RequestItem = {
    request_item_id: string;
    request_id?: string;
    item_type: Slice1RequestItemType | string;
    label: string;
    instructions: string;
    required: boolean;
    position: number;
    status: Slice1RequestItemStatus;
    actionable?: boolean;
    created_at?: string;
    satisfied_at?: string | null;
    satisfied_by_event_id?: string | null;
    customer_response?: Slice1CustomerResponse | null;
};

export type Slice1NextAction = {
    action_type: string;
    request_id?: string | null;
    request_item_id?: string | null;
    title?: string;
    instructions?: string;
    required_input?: string | null;
    status?: string;
    ordering?: { position?: number | null; total?: number | null };
    allowed_actions?: string[];
    version?: number;
    last_updated_at?: string;
};

export type Slice1RequestProgress = {
    satisfied: number;
    total: number;
    remaining: number;
};

export type Slice1RequestSummary = {
    request_id: string;
    status: 'open' | 'completed' | 'withdrawn' | 'superseded' | string;
    reason?: string;
    created_at?: string;
    updated_at?: string;
    completed_at?: string | null;
    active_item?: Slice1RequestItem | null;
    queued_items?: Slice1RequestItem[];
    items?: Slice1RequestItem[];
    progress?: Slice1RequestProgress;
};

export type Slice1Projection = {
    case_id: string;
    workflow_state: string;
    aggregate_version: number;
    customer_next_action?: Slice1NextAction;
    broker_next_action?: Slice1NextAction;
    open_request?: Slice1RequestSummary | null;
    queued_request_items?: Slice1RequestItem[];
    request_progress?: Slice1RequestProgress;
    latest_events?: Array<Record<string, unknown>>;
    server_timestamp?: string;
};

export type Slice1CommandOutcome = 'accepted' | 'replayed' | 'conflict' | 'rejected' | string;

export type Slice1CommandResult = {
    outcome: Slice1CommandOutcome;
    command_id: string;
    correlation_id?: string;
    idempotency_key: string;
    event_ids: string[];
    aggregate_version?: number;
    customer_projection?: Slice1Projection;
    broker_projection?: Slice1Projection;
    request_summary?: Slice1RequestSummary | null;
    server_timestamp?: string;
    error_code?: string;
    original_outcome?: string;
};

export type RequestMoreDraftItem = {
    item_type: Slice1RequestItemType;
    label: string;
    instructions: string;
    required: boolean;
    position: number;
    request_item_id?: string;
};

export type CreateRequestMoreCommand = {
    command_id: string;
    idempotency_key: string;
    expected_case_version: number;
    requested_items: RequestMoreDraftItem[];
    reason?: string;
    request_id?: string;
    correlation_id?: string;
};

export type MissingInfoFactStatus =
    | 'missing'
    | 'unknown'
    | 'supplied_unconfirmed'
    | 'confirmed'
    | 'needs_correction'
    | 'not_applicable'
    | string;

export type MissingInformationChecklistItem = {
    field_key: string;
    label: string;
    customer_label: string;
    item_type: string;
    business_class?: 'must_have' | 'nice_to_have' | 'request_more' | string;
    severity?: string;
    status: MissingInfoFactStatus;
    value?: string | null;
    previous_value?: string | null;
    reason?: string;
    suggested_for_request?: boolean;
    request_mode?: string;
    mvp_sendable?: boolean;
    is_authoritative_fact?: boolean;
};

export type CaseIntakeRequestDraftItem = {
    draft_item_id?: string;
    field_key?: string | null;
    item_type: string;
    label: string;
    instructions: string;
    required: boolean;
    position: number;
    request_mode?: string;
    selected?: boolean;
};

export type CaseIntakeRequestDraft = {
    draft_id: string;
    draft_version: number;
    status: string;
    items: CaseIntakeRequestDraftItem[];
    updated_at?: string;
    updated_by?: string;
    content_hash?: string;
};

export type CustomerAccessCard = {
    access_ready?: boolean;
    access_status?: string;
    status?: string;
    launch_url?: string | null;
    qr_payload?: string | null;
    copy_link?: string | null;
    mini_program_path?: string;
    expires_at?: string;
    channel?: string;
    instruction_zh?: string;
    simple_status?: string;
    request_sent?: boolean;
    qr_preparing?: boolean;
    message?: string;
    progress?: { satisfied_count?: number; total_count?: number } | null;
    production_qr_blocker?: string;
};

export type CaseIntakeProjection = {
    case_id: string;
    capability?: string;
    capability_version?: number;
    is_test?: boolean;
    admin_lifecycle?: string;
    workflow_state?: string | null;
    aggregate_version: number;
    office_id?: string | null;
    tenant_id?: string | null;
    known_facts?: Record<string, { status?: string; value?: unknown; previous_value?: unknown; reason?: string }>;
    missing_information_checklist?: MissingInformationChecklistItem[];
    request_draft?: CaseIntakeRequestDraft | null;
    open_request_more?: { request_id?: string; status?: string } | null;
    customer_access?: CustomerAccessCard | null;
    customer_next_action?: null;
    allowed_next_commands?: string[];
    simple_status?: string;
    server_timestamp?: string;
    auth_posture?: string;
};

export type SendRequestCommand = {
    command_id: string;
    idempotency_key: string;
    expected_case_version: number;
    request_draft_id: string;
    correlation_id?: string;
};

export type SendRequestCommandResult = CaseIntakeCommandResult & {
    customer_access?: CustomerAccessCard | null;
    slice1_projection?: Slice1Projection | null;
};

export type CaseIntakeCommandResult = {
    outcome: Slice1CommandOutcome;
    command_id: string;
    correlation_id?: string;
    idempotency_key: string;
    event_ids: string[];
    aggregate_version?: number;
    case_id?: string;
    broker_projection?: CaseIntakeProjection;
    customer_projection?: { customer_next_action?: null; message?: string };
    server_timestamp?: string;
    error_code?: string;
    original_outcome?: string;
};

export type CreateClaimCommand = {
    command_id: string;
    idempotency_key: string;
    correlation_id?: string;
    is_test?: boolean;
    customer_name?: string;
    customer_phone?: string;
    contact_note?: string;
    title?: string;
    vin?: string;
    accident_description?: string;
    known_facts?: Record<string, string>;
};

export type SaveRequestDraftCommand = {
    command_id: string;
    idempotency_key: string;
    expected_case_version: number;
    items: CaseIntakeRequestDraftItem[];
    draft_id?: string;
    correlation_id?: string;
};

export type UpdateFactStatusCommand = {
    command_id: string;
    idempotency_key: string;
    expected_case_version: number;
    field_key: string;
    status: MissingInfoFactStatus;
    reason?: string;
    correlation_id?: string;
};

export type Slice1RequestMoreErrorKind =
    | 'validation'
    | 'version_conflict'
    | 'feature_disabled'
    | 'authorization'
    | 'timeout'
    | 'server'
    | 'not_found'
    | 'unknown';

export class Slice1RequestMoreError extends Error {
    kind: Slice1RequestMoreErrorKind;
    status?: number;
    detail?: unknown;
    result?: Slice1CommandResult;

    constructor(message: string, kind: Slice1RequestMoreErrorKind, options: { status?: number; detail?: unknown; result?: Slice1CommandResult } = {}) {
        super(message);
        this.name = 'Slice1RequestMoreError';
        this.kind = kind;
        this.status = options.status;
        this.detail = options.detail;
        this.result = options.result;
    }
}

function isCommandResult(value: unknown): value is Slice1CommandResult {
    return Boolean(value && typeof value === 'object' && 'outcome' in value);
}

function normalizeSlice1RequestMoreError(error: unknown): Slice1RequestMoreError {
    const e = error as {
        code?: string;
        message?: string;
        response?: { status?: number; data?: { detail?: unknown } };
        request?: unknown;
    };
    const status = e.response?.status;
    const detail = e.response?.data?.detail;
    const result = isCommandResult(detail) ? detail : undefined;
    const errorCode = String(result?.error_code || (typeof detail === 'object' && detail ? (detail as { error?: unknown }).error : '') || '');

    if (status === 409 && result?.error_code === 'version_conflict') {
        return new Slice1RequestMoreError('The case changed while you were editing.', 'version_conflict', { status, detail, result });
    }
    if (status === 403) {
        return new Slice1RequestMoreError('You are not authorized to request more on this case.', 'authorization', { status, detail, result });
    }
    if (status === 404) {
        return new Slice1RequestMoreError('Case not found.', 'not_found', { status, detail, result });
    }
    if (status === 422) {
        const kind: Slice1RequestMoreErrorKind =
            result?.error_code === 'slice1_not_enabled' || errorCode === 'slice1_not_enabled'
                ? 'feature_disabled'
                : 'validation';
        return new Slice1RequestMoreError('Request More was rejected by validation.', kind, { status, detail, result });
    }
    if (status && status >= 500) {
        return new Slice1RequestMoreError('Request More failed on the server.', 'server', { status, detail, result });
    }
    if (e.code === 'ECONNABORTED' || (!e.response && e.request)) {
        return new Slice1RequestMoreError('Network outcome is uncertain.', 'timeout', { detail });
    }
    return new Slice1RequestMoreError(e.message || 'Request More failed.', 'unknown', { status, detail, result });
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
    /** P18 Loop 1 — workbench intelligence (structured_payload JSONB pass-through) */
    workbench_tags?: string[];
    risk_flags?: string[];
    conflict_flags?: string[];
    demo_summary?: string;
    known_facts?: Record<string, string>;
    /** P19H-3a — Claim guided lane workbench display (GET /api/inbox/cases enrichment) */
    workflow_id?: string;
    workflow_phase?: string;
    display_title?: string;
    display_status?: string;
    claim_summary?: {
        accident_datetime?: string | null;
        accident_location?: string | null;
        accident_description?: string | null;
    };
    /** P19H-3c-3A — Claim evidence checklist summary (GET /api/inbox/cases enrichment) */
    claim_evidence_summary?: ClaimEvidenceSummary;
    /** P19H-3e-1 — Claim story timeline + case brief */
    claim_timeline?: ClaimTimelineEvent[];
    claim_case_brief?: ClaimCaseBrief;
    slice1_capability_version?: number;
    p20_slice1_capability_version?: number;
    slice1_projection?: Slice1Projection;
    p20_slice1_projection?: Slice1Projection;
    slice1_request_summary?: Slice1RequestSummary;
    p20_slice1_request_summary?: Slice1RequestSummary;
    workbench_visible?: boolean;
    /** P18 Loop 1 — demo seed metadata (extra JSONB) */
    demo_name?: string;
    demo_flags?: Record<string, unknown>;
    wecom_external_userid?: string | null;
}

export type CaseStatus = 'new' | 'reviewing' | 'waiting_client' | 'done';
export type WaitingOn = 'none' | 'client' | 'broker' | 'carrier' | 'underwriting';

/** ADD_CAR_ATTACHMENT_READY_LITE + P19B WeCom attachment metadata */
export interface CaseAttachment {
    attachment_id: string;
    /** Web upload filename (legacy) */
    filename?: string;
    /** Legacy web upload type */
    type?: 'registration' | 'vin_photo' | 'dec_page' | 'screenshot';
    size_bytes?: number;
    created_at?: string;
    /** P19B WeCom / workbench fields */
    source?: string;
    msgtype?: string;
    document_type?: string;
    document_type_confidence?: string;
    mime_type?: string;
    received_at?: string;
    binding_confidence?: string;
    ocr_status?: string;
    broker_confirmed?: boolean;
    intake_status?: string;
    guardrail_status?: string;
    eligible_for_ocr?: boolean;
    requires_customer_confirm?: boolean;
    quarantine_reason?: string | null;
    slot_assignment?: string | null;
    bulk_sequence?: number;
    preview_available?: boolean;
    preview_url?: string;
    storage_status?: string;
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
    /** Capability 2: admin draft lifecycle (pre-task) */
    admin_lifecycle?: string;
    /** Capability 2: authoritative missing-information checklist */
    missing_information_checklist?: MissingInformationChecklistItem[];
    /** Capability 2: broker-selected request draft (not active Request More) */
    request_draft?: CaseIntakeRequestDraft | null;
    /** Capability 2 projection blob */
    p20_case_intake_projection?: CaseIntakeProjection;
    case_intake_projection?: CaseIntakeProjection;
    /** Capability 3A: customer QR/link access card after Send Request */
    customer_access?: CustomerAccessCard | null;
    /** Workbench: soft-archive (hidden in default “正式” views) */
    workbench_archived?: boolean;
    /** explicit add_car lane vs heuristic legacy vs other */
    workbench_lane_kind?: WorkbenchLaneKind;
    /** Postgres mirror glance when DB configured */
    pg_mirror_state?: PgMirrorState;
    /** P16 document-intake full packet blob for broker reopen */
    p16_broker_packet?: Record<string, unknown>;
    /**
     * Track B0.3 (Active Workspace): set once, by broker action only, via
     * PATCH /cases/{case_id}/confirm. Presence = Active Case; null = Draft
     * Case. Immutable once set (mirrors formal_submitted_at).
     */
    broker_confirmed_at?: string | null;
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

export async function createCaseRequestMore(
    caseId: string,
    command: CreateRequestMoreCommand,
): Promise<Slice1CommandResult> {
    try {
        const response = await request.post<Slice1CommandResult>(
            `/api/inbox/cases/${encodeURIComponent(caseId)}/request-more`,
            {
                command_id: command.command_id,
                idempotency_key: command.idempotency_key,
                expected_case_version: command.expected_case_version,
                requested_items: command.requested_items.map((item, index) => ({
                    item_type: item.item_type,
                    label: item.label.trim(),
                    instructions: item.instructions.trim(),
                    required: item.required,
                    position: item.position || index + 1,
                    request_item_id: item.request_item_id,
                })),
                reason: (command.reason ?? '').trim(),
                request_id: command.request_id,
                correlation_id: command.correlation_id,
            },
        );
        return response.data;
    } catch (error) {
        throw normalizeSlice1RequestMoreError(error);
    }
}

function newCommandIds(prefix: string): { command_id: string; idempotency_key: string } {
    const stamp = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    return {
        command_id: `${prefix}_${stamp}`,
        idempotency_key: `${prefix}_idem_${stamp}`,
    };
}

export async function createClaimCase(command: CreateClaimCommand): Promise<CaseIntakeCommandResult> {
    const ids = newCommandIds('create_claim');
    const response = await request.post<CaseIntakeCommandResult>('/api/inbox/claims', {
        command_id: command.command_id || ids.command_id,
        idempotency_key: command.idempotency_key || ids.idempotency_key,
        correlation_id: command.correlation_id,
        is_test: Boolean(command.is_test),
        customer_name: command.customer_name,
        customer_phone: command.customer_phone,
        contact_note: command.contact_note,
        title: command.title,
        vin: command.vin,
        accident_description: command.accident_description,
        known_facts: command.known_facts,
    });
    return response.data;
}

export async function saveCaseRequestDraft(
    caseId: string,
    command: SaveRequestDraftCommand,
): Promise<CaseIntakeCommandResult> {
    const response = await request.post<CaseIntakeCommandResult>(
        `/api/inbox/cases/${encodeURIComponent(caseId)}/request-draft`,
        {
            command_id: command.command_id,
            idempotency_key: command.idempotency_key,
            expected_case_version: command.expected_case_version,
            items: command.items.map((item, index) => ({
                draft_item_id: item.draft_item_id,
                field_key: item.field_key,
                item_type: item.item_type,
                label: item.label.trim(),
                instructions: (item.instructions || '').trim(),
                required: item.required !== false,
                position: item.position || index + 1,
                request_mode: item.request_mode || 'request_missing',
                selected: item.selected !== false,
            })),
            draft_id: command.draft_id,
            correlation_id: command.correlation_id,
        },
    );
    return response.data;
}

export async function sendCaseRequest(
    caseId: string,
    command: SendRequestCommand,
): Promise<SendRequestCommandResult> {
    try {
        const response = await request.post<SendRequestCommandResult>(
            `/api/inbox/cases/${encodeURIComponent(caseId)}/send-request`,
            {
                command_id: command.command_id,
                idempotency_key: command.idempotency_key,
                expected_case_version: command.expected_case_version,
                request_draft_id: command.request_draft_id,
                correlation_id: command.correlation_id,
            },
        );
        return response.data;
    } catch (error) {
        throw normalizeSlice1RequestMoreError(error);
    }
}

export async function updateCaseFactStatus(
    caseId: string,
    command: UpdateFactStatusCommand,
): Promise<CaseIntakeCommandResult> {
    const response = await request.post<CaseIntakeCommandResult>(
        `/api/inbox/cases/${encodeURIComponent(caseId)}/fact-status`,
        {
            command_id: command.command_id,
            idempotency_key: command.idempotency_key,
            expected_case_version: command.expected_case_version,
            field_key: command.field_key,
            status: command.status,
            reason: command.reason || '',
            correlation_id: command.correlation_id,
        },
    );
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

/**
 * Track B0.3 — Broker Confirm. Sets `broker_confirmed_at` and triggers exactly
 * ONE Done Card to the customer (server-side, idempotent). Safe to call twice.
 */
export async function confirmCaseByBroker(
    caseId: string,
): Promise<SavedCase & { done_card_sent?: boolean; already_confirmed?: boolean }> {
    const response = await request.patch<SavedCase & { done_card_sent?: boolean; already_confirmed?: boolean }>(
        `/api/inbox/cases/${caseId}/confirm`,
        {},
    );
    return response.data;
}

/**
 * P19H-3f-2 — Claim True End Card when broker marks record phase done.
 * Idempotent; second call does not resend End Card.
 */
export async function markClaimBrokerDone(
    caseId: string,
): Promise<
    SavedCase & {
        already_done?: boolean;
        end_card_sent?: boolean;
        end_card_preview?: string;
        end_card_send_skipped?: boolean;
        end_card_send_reason?: string;
    }
> {
    const response = await request.post<
        SavedCase & {
            already_done?: boolean;
            end_card_sent?: boolean;
            end_card_preview?: string;
            end_card_send_skipped?: boolean;
            end_card_send_reason?: string;
        }
    >(`/api/inbox/cases/${caseId}/broker-done`, {});
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

/** Get attachment download URL (relative to API base) — local filesystem uploads */
export function getAttachmentDownloadUrl(caseId: string, attachmentId: string): string {
    return `/api/inbox/cases/${caseId}/attachments/${attachmentId}`;
}

/** Auth-gated preview URL (P19B — WeCom GCS proxy or local file) */
export function getAttachmentPreviewUrl(caseId: string, attachmentId: string): string {
    return `/api/inbox/cases/${caseId}/attachments/${attachmentId}/preview`;
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
