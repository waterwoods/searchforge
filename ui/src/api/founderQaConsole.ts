/**
 * P35.2 — Founder QA Console API client.
 * Uses intake API key via shared request interceptor.
 * Never sends or stores UNIFIED_INTAKE_SUPPORT_API_KEY.
 */
import request from './request';

export type FounderQaOpenRequestMore = {
    request_item_id?: string | null;
    item_type?: string | null;
    label?: string | null;
    status?: string | null;
};

export type FounderQaSelectedIdentity = {
    label?: string | null;
    identity_masked?: string;
    session_id?: string;
    person_link_key_masked?: string;
    active_case_id?: string | null;
    bound_case_id?: string | null;
    selected_at?: string | null;
    last_seen?: string | null;
    environment?: string | null;
};

export type FounderQaActiveCase = {
    has_active_case?: boolean;
    case_id?: string | null;
    claim_status?: string | null;
    current_task?: string | null;
    next_action?: string | null;
    qa_fixture_demo_name?: string | null;
    last_preset_applied?: string | null;
    last_reset_time?: string | null;
    bound_case_is_harness?: boolean;
};

export type FounderQaConsoleStatus = {
    ok?: boolean;
    environment?: string;
    enabled?: boolean;
    authorized?: boolean;
    production_like?: boolean;
    production_safety?: string;
    support_key_configured?: boolean;
    require_support_key?: boolean;
    intake_api_configured?: boolean;
    actor?: string;
    selected_identity?: FounderQaSelectedIdentity | null;
    active_case?: FounderQaActiveCase | null;
    resume_binding?: { bound?: boolean; resume_token_masked?: string | null } | null;
    open_request_more?: FounderQaOpenRequestMore | null;
    latest_qa_preset?: string | null;
    latest_qa_audit_event?: Record<string, unknown> | null;
    inspect_error?: string | null;
    mutations_allowed?: boolean;
    notes?: string | null;
};

export type FounderQaPresetResult = {
    ok?: boolean;
    preset?: string;
    result?: Record<string, unknown>;
    status?: FounderQaConsoleStatus;
};

export type FounderQaAuditEvent = {
    at?: string;
    preset?: string;
    ok?: boolean;
    actor?: string;
    identity_masked?: string;
    case_id?: string;
    error?: string;
    partial?: boolean;
    source?: string;
    [key: string]: unknown;
};

function detailFromError(e: unknown): string {
    const ax = e as { response?: { status?: number; data?: { detail?: string } }; message?: string };
    const detail = ax?.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail.trim();
    if (ax?.response?.status === 429) return 'founder_qa_rate_limited';
    if (ax?.response?.status === 401) return 'intake_api_unauthorized';
    if (ax?.response?.status === 403) return String(detail || 'forbidden');
    return String(ax?.message || 'request_failed');
}

export function mapFounderQaError(code: string): string {
    switch (code) {
        case 'p35_mp_qa_harness_disabled':
        case 'founder_qa_harness_disabled':
            return 'Founder QA 未启用。请确认 ENABLE_P35_MP_QA_HARNESS=1 与 UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1。';
        case 'p35_mp_qa_surface_disabled':
            return 'QA Fixture Surface 未启用。';
        case 'p35_mp_qa_support_key_required':
            return '生产态要求服务端已配置 Support Key（不会下发到浏览器）。';
        case 'founder_qa_production_requires_intake_key':
            return '生产环境必须配置 Intake API Key 才能打开控制台。';
        case 'selected_identity_required':
            return '请先选择精确的 wx_* QA 身份。';
        case 'exact_wx_session_id_required':
        case 'wildcard_identity_forbidden':
            return '仅接受精确的 wx_* session ID（禁止通配符）。';
        case 'confirm_fresh_required':
            return '请输入确认短语 FRESH。';
        case 'confirm_active_required':
            return '请输入确认短语 ACTIVE。';
        case 'confirm_request_more_required':
            return '请输入确认短语 REQUEST_MORE。';
        case 'founder_qa_rate_limited':
        case 'p35_mp_qa_rate_limited':
            return '操作过于频繁，请稍后再试。';
        case 'intake_api_unauthorized':
            return '未授权：缺少或错误的 Intake API Key。';
        case 'support_key_not_accepted_on_console':
            return '控制台不接受 Support Key（请勿从浏览器传递）。';
        case 'status_unavailable':
            return '状态刷新失败，已保留当前已选身份。';
        case 'request_more_failed:slice1_not_enabled':
        case 'slice1_not_enabled':
            return '部分失败：案件可能已创建，但 Request More 未启用（需要 P20_SLICE1_REQUEST_MORE=1）。请勿当作成功；启用后重试或改用 CLI。';
        default:
            if (code.startsWith('seed_claim_failed') || code.startsWith('request_more_failed')) {
                return `部分失败：${code}。请查看结果详情后手动重试（可能已创建案件）。`;
            }
            return code || '操作失败';
    }
}

export async function getFounderQaStatus(): Promise<FounderQaConsoleStatus> {
    try {
        const response = await request.get<FounderQaConsoleStatus>('/api/internal/founder-qa/status');
        return response.data;
    } catch (e) {
        throw new Error(mapFounderQaError(detailFromError(e)));
    }
}

export async function selectFounderQaIdentity(body: {
    session_id: string;
    label?: string;
}): Promise<{ ok: boolean; selected_identity: FounderQaSelectedIdentity; status: FounderQaConsoleStatus }> {
    try {
        const response = await request.post('/api/internal/founder-qa/identity', body);
        return response.data;
    } catch (e) {
        throw new Error(mapFounderQaError(detailFromError(e)));
    }
}

export async function forgetFounderQaIdentity(): Promise<{
    ok: boolean;
    forgotten: boolean;
    status: FounderQaConsoleStatus;
}> {
    try {
        const response = await request.delete('/api/internal/founder-qa/identity');
        return response.data;
    } catch (e) {
        throw new Error(mapFounderQaError(detailFromError(e)));
    }
}

export async function runFounderQaPreset(
    preset: 'fresh' | 'active' | 'request-more',
    body: { confirm: string; session_id?: string },
): Promise<FounderQaPresetResult> {
    try {
        const response = await request.post<FounderQaPresetResult>(
            `/api/internal/founder-qa/presets/${preset}`,
            body,
            { timeout: 60000 },
        );
        return response.data;
    } catch (e) {
        throw new Error(mapFounderQaError(detailFromError(e)));
    }
}

export async function listFounderQaAudit(limit = 20): Promise<FounderQaAuditEvent[]> {
    try {
        const response = await request.get<{ ok: boolean; events: FounderQaAuditEvent[] }>(
            '/api/internal/founder-qa/audit',
            { params: { limit } },
        );
        return response.data.events || [];
    } catch (e) {
        throw new Error(mapFounderQaError(detailFromError(e)));
    }
}

export function brokerCaseOpenPath(caseId: string): string {
    const id = (caseId || '').trim();
    return `/workbench/unified-intake?tab=broker&caseId=${encodeURIComponent(id)}`;
}
