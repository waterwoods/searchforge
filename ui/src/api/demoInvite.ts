/**
 * Chen Demo Invite — QA Broker API client (T3).
 * Uses support-key auth. Never logs raw OpenID. Token returned once from issue.
 */
import request from './request';

function supportAuthHeaders(): Record<string, string> {
    const key = String(import.meta.env.VITE_UNIFIED_INTAKE_SUPPORT_API_KEY || '').trim();
    if (!key) return {};
    return { 'X-Unified-Intake-Support-Key': key };
}

/** Default office scope for Chen known-customer demo (explicit, not Production). */
export const CHEN_DEMO_OFFICE_ID = 'chen_kui';

export const CHEN_DEMO_SCENARIO_UI: Record<
    string,
    { title: string; customer: string; vehicle: string }
> = {
    chen_camry: {
        title: '陈明 · Toyota Camry',
        customer: '陈明',
        vehicle: 'Toyota Camry',
    },
    li_multi: {
        title: '李娜 · 多辆车',
        customer: '李娜',
        vehicle: '多辆车',
    },
    wang_stale: {
        title: '王先生 · 保单资料较旧',
        customer: '王先生',
        vehicle: '保单资料较旧',
    },
};

export type DemoInviteScenario = {
    scenario_id: string;
    label: string;
    customer_display_name: string;
    vehicle_summary: string;
    demo_name: string;
    is_demo: boolean;
    mock_scenario: string;
};

export type DemoInviteIssued = {
    ok?: boolean;
    invite_id: string;
    token: string;
    office_id: string;
    scenario_id: string;
    mock_scenario: string;
    demo_name: string;
    is_demo: boolean;
    created_at: number;
    expires_at: number;
    revoked?: boolean;
    use_count?: number;
    max_uses?: number | null;
    customer_display_name?: string;
    vehicle_summary?: string;
    label?: string;
};

export type DemoInviteValidateResult = {
    ok: boolean;
    status: string;
    error_code?: string | null;
    is_demo?: boolean;
    demo_name?: string;
    invite?: {
        invite_id: string;
        office_id: string;
        scenario_id: string;
        expires_at: number;
        revoked: boolean;
        use_count: number;
    };
};

/** Mini Program path + query T4 will redeem. Not a WeChat URL Link / wxacode. */
export type DemoInviteEntryPayload = {
    kind: 'chen_demo_invite';
    mini_program_path: string;
    query: string;
    /** Copy into WeChat DevTools compile mode / T4 wiring */
    launch_path_with_query: string;
    office_id: string;
    scenario_id: string;
    invite_id: string;
    expires_at_iso: string;
    qr_supported: false;
    qr_blocker: string;
    t4_required: string;
};

export const DEMO_INVITE_QR_BLOCKER =
    'Native WeChat Mini Program QR (wxacode.getUnlimited) is not wired. ' +
    'HTTPS URL Link / claim-task deep-link redeem for dit= is T4 work. ' +
    'Do not invent a camera QR that WeChat cannot open.';

export const DEMO_INVITE_T4_REQUIRED =
    'T4 must: (1) read launch query dit= on Mini Program start, ' +
    '(2) POST /api/h5/demo-invite/redeem with session_id + token, ' +
    '(3) then run existing Smart Claim Start. Optional later: HTTPS bridge or wxacode.';

export function buildDemoInviteEntryPayload(issued: DemoInviteIssued): DemoInviteEntryPayload {
    const token = String(issued.token || '').trim();
    const query = `dit=${encodeURIComponent(token)}`;
    const path = 'pages/start-claim/start-claim';
    const expiresAt = Number(issued.expires_at || 0);
    return {
        kind: 'chen_demo_invite',
        mini_program_path: path,
        query,
        launch_path_with_query: `${path}?${query}`,
        office_id: String(issued.office_id || ''),
        scenario_id: String(issued.scenario_id || ''),
        invite_id: String(issued.invite_id || ''),
        expires_at_iso: expiresAt > 0 ? new Date(expiresAt * 1000).toISOString() : '',
        qr_supported: false,
        qr_blocker: DEMO_INVITE_QR_BLOCKER,
        t4_required: DEMO_INVITE_T4_REQUIRED,
    };
}

export function maskDemoInviteToken(token: string): string {
    const raw = String(token || '').trim();
    if (raw.length < 12) return 'di_…';
    return `${raw.slice(0, 6)}…${raw.slice(-4)}`;
}

export function formatDemoInviteExpiry(expiresAtSec: number): string {
    if (!expiresAtSec) return '—';
    try {
        return new Date(expiresAtSec * 1000).toLocaleString();
    } catch {
        return String(expiresAtSec);
    }
}

export async function listDemoInviteCatalog(): Promise<DemoInviteScenario[]> {
    const response = await request.get<{
        ok?: boolean;
        scenarios?: DemoInviteScenario[];
    }>('/api/inbox/support/demo-invite/catalog', { headers: supportAuthHeaders() });
    return Array.isArray(response.data?.scenarios) ? response.data.scenarios : [];
}

export async function issueDemoInvite(body: {
    office_id: string;
    scenario_id: string;
    ttl_seconds?: number;
    max_uses?: number;
}): Promise<DemoInviteIssued> {
    const response = await request.post<DemoInviteIssued>(
        '/api/inbox/support/demo-invite/issue',
        body,
        { headers: supportAuthHeaders() },
    );
    return response.data;
}

export async function validateDemoInvite(body: {
    token: string;
    office_id?: string;
}): Promise<DemoInviteValidateResult> {
    const response = await request.post<DemoInviteValidateResult>(
        '/api/inbox/support/demo-invite/validate',
        body,
        { headers: supportAuthHeaders() },
    );
    return response.data;
}

export async function revokeDemoInvite(body: {
    token?: string;
    invite_id?: string;
}): Promise<{ ok: boolean; revoked?: boolean; error_code?: string }> {
    const response = await request.post<{ ok: boolean; revoked?: boolean; error_code?: string }>(
        '/api/inbox/support/demo-invite/revoke',
        body,
        { headers: supportAuthHeaders() },
    );
    return response.data;
}

export async function resetDemoInviteOverlay(session_id: string): Promise<{
    ok: boolean;
    cleared?: boolean;
}> {
    const response = await request.post<{ ok: boolean; cleared?: boolean }>(
        '/api/inbox/support/demo-invite/reset-overlay',
        { session_id },
        { headers: supportAuthHeaders() },
    );
    return response.data;
}

export async function resetDemoInviteOffice(office_id: string): Promise<{
    ok: boolean;
    invites_revoked?: number;
    overlays_cleared?: number;
}> {
    const response = await request.post<{
        ok: boolean;
        invites_revoked?: number;
        overlays_cleared?: number;
    }>('/api/inbox/support/demo-invite/reset-office', { office_id }, { headers: supportAuthHeaders() });
    return response.data;
}

export function mapDemoInviteError(detail: unknown): string {
    const code = String(detail || '').trim();
    const map: Record<string, string> = {
        demo_invite_disabled: '演示入口未启用（CHEN_DEMO_INVITE_ENABLED）',
        demo_invite_disabled_production: 'Production 已硬关闭演示入口',
        support_export_unauthorized: '缺少 Support Key，无法使用演示工具',
        scenario_not_allowlisted: '场景不在允许列表',
        office_id_required: '需要 office_id',
        active_case_blocks_scenario_switch: '已有进行中案件，需先显式重置后再换场景',
    };
    return map[code] || code || '演示工具请求失败';
}
