import type { UiCopy } from '../../../api/clientConfig';
import type { SavedCase, SoftRouteIntent, TriageResult, WaitingOn } from '../../../api/inboxTriage';
import type { TriageResultCore } from '../../../api/triageResultContract';
import {
    caseLifecycleTagColor,
    caseLifecycleUserLabel,
    resolveCaseLifecycle,
} from '../../../components/intake/caseLifecycleDisplay';
import { getOfficeCaseBoundaryPreviewSuffix } from '../../../components/workbench/officeCaseBoundary';
import type { AttentionKind, FollowUpDueKind, OfficeGlanceLines, WorkbenchListFilter } from '../types';
import {
    ADD_CAR_FIELD_LABELS,
    ADD_CAR_TRIAGE_FIELD_IDS,
    CASE_FOCUS_DISPLAY_ZH,
    CASE_STATUS_OPTIONS,
    CATEGORY_DISPLAY_LABELS,
    CLAIM_FIELD_LABELS,
    CUSTOMER_FIELD_LABELS_ZH,
    DEFAULT_QUICK_START_BUTTONS,
    LIFECYCLE_STATUS_LABELS,
    MISSING_DOC_FIELD_LABELS,
    QUOTE_READY_STATUS_LABELS,
    RENEWAL_FIELD_LABELS,
    WAITING_ON_OPTIONS,
} from '../constants';

export function getQuickStartButtons(uiCopy: UiCopy): Array<{ id: SoftRouteIntent; label: string; shortLabel: string; starterMessage: string }> {
    const qsb = uiCopy.quick_start_buttons;
    const defaults = DEFAULT_QUICK_START_BUTTONS;
    return defaults.map((d) => {
        const b = qsb?.[d.id];
        return {
            id: d.id,
            label: b?.label?.trim() || d.label,
            shortLabel: b?.shortLabel?.trim() || b?.label?.trim() || d.shortLabel,
            starterMessage: b?.starterMessage?.trim() || d.starterMessage,
        };
    });
}
export function normalizeFollowUpText(value?: string): string {
    let text = (value ?? '').trim();
    const stripLegacyPrefix = (raw: string): string => {
        let next = raw;
        let lowered = next.toLowerCase();
        for (const marker of ['undefined', 'null']) {
            while (lowered.startsWith(marker)) {
                next = next.slice(marker.length).trim().replace(/^[-:;, ]+/, '');
                lowered = next.toLowerCase();
            }
        }
        return next;
    };
    text = stripLegacyPrefix(text);
    if (!text || text.toLowerCase() === 'undefined' || text.toLowerCase() === 'null') {
        return '';
    }
    return text;
}
/** When backend returns ISO timestamp on persisted case — customer closure observability. */
export function formatPortalLocalDateTime(iso: string | undefined): string | null {
    const s = (iso ?? '').trim();
    if (!s) return null;
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return d.toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' });
}

/** Workbench trust strip: API host only (no path), dev-safe label when using Vite proxy. */
export function formatWorkbenchApiEndpointLabel(baseUrl: string): string {
    const raw = (baseUrl ?? '').trim();
    if (!raw) {
        return 'dev · 本机代理';
    }
    try {
        const withProto = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
        return new URL(withProto).host;
    } catch {
        return raw.replace(/^https?:\/\//i, '').replace(/\/+$/, '').slice(0, 64) || '—';
    }
}

/** Aggregate PG mirror hints for the current queue page (trust; optional when backend omits). */
export function workbenchPgMirrorTrustLine(cases: SavedCase[]): string | null {
    const states = cases
        .map((c) => c.pg_mirror_state)
        .filter((s): s is NonNullable<SavedCase['pg_mirror_state']> => Boolean(s));
    if (states.length === 0) return null;
    const bad = states.filter((s) => s === 'mismatch' || s === 'pg_missing').length;
    if (bad > 0) {
        return `本页数据库镜像：${bad} 条需关注（已标注 ${states.length} 条）`;
    }
    if (states.every((s) => s === 'unknown')) {
        return `本页 ${states.length} 条：镜像状态未校验`;
    }
    return `本页数据库镜像：与服务器一致（${states.length} 条已标注）`;
}

/** Office queue + detail: same vocabulary as customer Add-Car status strip (STATE parity). */
export function getOfficeLifecycleTag(lifecycleStatus: string | undefined): { label: string; color: string } | null {
    const key = (lifecycleStatus ?? '').trim();
    if (!key) return null;
    const mapped = LIFECYCLE_STATUS_LABELS[key];
    if (mapped) return mapped;
    return { label: key, color: 'default' };
}

/** Ordered chips for Add-Car status strip — primary axis: `case_lifecycle` (not lifecycle_status / collection_stage). */
export function buildAddCarStatusStripChips(
    triage: TriageResultCore | null | undefined,
    phase: 'intake' | 'submitted',
): Array<{ label: string; color: string }> {
    const out: Array<{ label: string; color: string }> = [{ label: '加车报价', color: 'blue' }];
    if (!triage) return out;

    const cl = resolveCaseLifecycle(triage);
    if (phase === 'submitted' || cl === 'submitted') {
        out.push({
            label: caseLifecycleUserLabel('submitted'),
            color: caseLifecycleTagColor('submitted'),
        });
        return out;
    }

    out.push({
        label: caseLifecycleUserLabel(cl),
        color: caseLifecycleTagColor(cl),
    });
    return out;
}
export function buildGenericIntakeStatusChips(triage: TriageResultCore): Array<{ label: string; color: string }> {
    const out: Array<{ label: string; color: string }> = [{ label: '客户报送', color: 'blue' }];
    if (triage.issue_category) {
        out.push({ label: humanizeCategory(triage.issue_category, triage.source_text), color: 'cyan' });
    }
    if (triage.case_status) {
        const lab = CASE_STATUS_OPTIONS.find((o) => o.value === triage.case_status)?.label ?? triage.case_status;
        out.push({ label: `记录：${lab}`, color: 'geekblue' });
    }
    const cl = resolveCaseLifecycle(triage);
    out.push({
        label: caseLifecycleUserLabel(cl),
        color: caseLifecycleTagColor(cl),
    });
    return out;
}
/** Broker-facing structured field labels (office Chinese); prefer CUSTOMER_FIELD_LABELS_ZH when available */
export function humanizeStructuredField(field: string): string {
    return (
        CUSTOMER_FIELD_LABELS_ZH[field] ??
        ADD_CAR_FIELD_LABELS[field] ??
        RENEWAL_FIELD_LABELS[field] ??
        CLAIM_FIELD_LABELS[field] ??
        MISSING_DOC_FIELD_LABELS[field] ??
        field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    );
}

export function getCaseFocusDisplayLabel(focus: string | null): string | null {
    if (!focus) return null;
    return CASE_FOCUS_DISPLAY_ZH[focus] ?? focus;
}

export function inferCaseFocusFromText(text: string): string | null {
    const t = (text || '').toLowerCase();
    if (/\b(联系人工|联系陈奎|联系办公室|我要找人工|找经纪人|找人工|talk to agent)\b/.test(t)) {
        return '联系人工';
    }
    if (/\b(加|加一台|加一辆|新车|提车|报价|先出报价|买了|保费多少钱)\b/.test(t) && /\b(车|vin|tesla|toyota|honda|model|bmw|宝马|x5)\b/i.test(t)) {
        return 'Add car quote';
    }
    if (/\b(拿掉|删掉|去掉|卖掉|卖车|卖掉了)\b/.test(t) && /\b(车|honda|accord|vehicle)\b/i.test(t)) {
        return 'Remove car';
    }
    if (/\b(保费|太贵|太高|怎么降|降一点|续保)\b/.test(t)) {
        return 'Premium review';
    }
    if (/\b(事故|出险|理赔|撞车|撞了|accident|claim)\b/.test(t)) {
        return 'Claim intake';
    }
    if (/\b(dmv|sr-22|sr22|suspension|clearance|带什么)\b/i.test(t)) {
        return 'DMV / SR-22 help';
    }
    return null;
}

/** Extract last 2–3 customer messages for handoff visibility. Uses case_messages when available, else parses source_text. */
export function getRecentCustomerMessages(
    caseItem: Pick<TriageResult, 'case_messages' | 'source_text'>,
    maxCount = 3,
): string[] {
    const msgs = caseItem.case_messages;
    if (Array.isArray(msgs) && msgs.length > 0) {
        const customer = msgs
            .filter((m) => (m.role || '').toLowerCase() === 'customer')
            .sort((a, b) => (b.sequence ?? 0) - (a.sequence ?? 0));
        return customer.slice(0, maxCount).map((m) => (m.text || '').trim()).filter(Boolean);
    }
    const src = caseItem.source_text ?? '';
    if (!src) return [];
    const matches = src.matchAll(/\[客户\]\s*([^[]+)/g);
    const arr = [...matches].map((m) => m[1].trim()).filter(Boolean);
    return arr.slice(-maxCount);
}

/** One-line handoff summary for Case Report — "可交办公室: X — Y" or "信息收集中: X — Y" (office Chinese) */
export function getCaseReportOneLiner(
    caseItem: Pick<TriageResult, 'collection_stage' | 'broker_next_step' | 'collected_fields' | 'still_needed_fields' | 'issue_category' | 'source_text'>,
    inputFallback: string,
): string {
    const focus =
        inferCaseFocusFromStructuredFields(
            caseItem.collected_fields,
            caseItem.still_needed_fields,
            caseItem.issue_category,
        ) ?? inferCaseFocusFromText(caseItem.source_text ?? inputFallback);
    const stage = caseItem.collection_stage === 'enough_for_handoff' ? '可交办公室' : '信息收集中';
    const focusDisplay = getCaseFocusDisplayLabel(focus) ?? focus;
    const nextPreview = (caseItem.broker_next_step ?? '').slice(0, 60);
    const suffix = nextPreview ? ` — ${nextPreview}${nextPreview.length >= 60 ? '…' : ''}` : '';
    return focusDisplay ? `${stage}：${focusDisplay}${suffix}` : `${stage}${suffix}`.trim() || '';
}

/** Infer case focus from structured fields when present — more reliable than text regex */
export function inferCaseFocusFromStructuredFields(
    collected?: string[],
    stillNeeded?: string[],
    category?: string,
): string | null {
    if (category === 'customer_requested_human') return '联系人工';
    const fields = [...(collected ?? []), ...(stillNeeded ?? [])];
    if (fields.some((f) => ['year', 'make_model', 'model', 'zip', 'delivery_date', 'primary_driver', 'vin'].includes(f))) {
        return 'Add car quote';
    }
    if (fields.some((f) => /premium|renewal|remove_vehicle|coverage_adjust/.test(f))) {
        return 'Premium review';
    }
    if (fields.some((f) => /accident|photos|other_driver|hit_and_run|police_report/.test(f))) {
        return 'Claim intake';
    }
    if (category === 'missing_document' || category === 'underwriting_followup' || fields.some((f) => /declaration|garaging|driver_license|verify_carrier/.test(f))) {
        return 'Missing document';
    }
    if (category === 'cancellation_warning' || category === 'payment_lapse_expiration') {
        return 'Payment / cancellation risk';
    }
    return null;
}

/** Whether triage output indicates an Add-Car quote transaction (for customer UI framing). */
export function triageResultLooksLikeAddCar(triage: TriageResult | undefined): boolean {
    if (!triage) return false;
    if (triage.quote_ready_status) return true;
    const all = [...(triage.collected_fields ?? []), ...(triage.still_needed_fields ?? [])];
    if (all.some((f) => ADD_CAR_TRIAGE_FIELD_IDS.has(f))) return true;
    const focus =
        inferCaseFocusFromStructuredFields(
            triage.collected_fields,
            triage.still_needed_fields,
            triage.issue_category,
        ) ?? inferCaseFocusFromText(triage.source_text ?? '');
    return focus === 'Add car quote';
}

export function customerEntryIsAddCarActive(
    turns: Array<{ role: string; triageResult?: TriageResult }>,
    selectedIntent: SoftRouteIntent | null,
): boolean {
    if (selectedIntent === 'add_car') return true;
    const lastSystem = [...turns].reverse().find((t) => t.role === 'system');
    return triageResultLooksLikeAddCar(lastSystem?.triageResult);
}

export function humanizeCategory(cat: string, sourceText?: string): string {
    const category = (cat || '').trim();
    if (category === 'customer_requested_human') return '联系人工';
    if (category === 'customer_question' && sourceText) {
        const focus = inferCaseFocusFromText(sourceText);
        if (focus) return focus;
    }
    return CATEGORY_DISPLAY_LABELS[category] ?? category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function humanizeStructuredFieldForCustomer(field: string): string {
    return CUSTOMER_FIELD_LABELS_ZH[field] ?? humanizeStructuredField(field);
}

/** Workbench queue/detail: align strip phase with customer (one state world). */
export function addCarQueueStatusPhase(triage: Pick<TriageResult, 'lifecycle_status'> | null | undefined): 'intake' | 'submitted' {
    const ls = (triage?.lifecycle_status ?? '').trim();
    if (ls === 'handed_off' || ls === 'office_followup') return 'submitted';
    return 'intake';
}

export function humanizeCaseStatus(status?: string): string {
    return (status || 'new').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Office workbench: short Chinese label for waiting_on */
export function humanizeWaitingOn(waitingOn?: string): string {
    const w = (waitingOn || 'none') as WaitingOn;
    return WAITING_ON_OPTIONS.find((o) => o.value === w)?.label ?? '无阻塞';
}

export function getCaseStatusColor(status?: string): string {
    if (status === 'done') return 'green';
    if (status === 'waiting_client') return 'gold';
    if (status === 'reviewing') return 'blue';
    return 'default';
}

export function getUrgencyColor(urgency: string): string {
    if (urgency === 'critical') return 'red';
    if (urgency === 'high') return 'orange';
    if (urgency === 'medium') return 'gold';
    return 'green';
}

/** Office-facing urgency (Chinese); avoids raw EN tokens on broker surfaces */
export function humanizeUrgencyLabel(urgency: string): string {
    const u = (urgency || 'low').toLowerCase();
    if (u === 'critical') return '紧急';
    if (u === 'high') return '高';
    if (u === 'medium') return '中';
    return '低';
}

export function getResponseWindow(urgency: TriageResult['urgency']): string {
    if (urgency === 'critical' || urgency === 'high') return '建议当日处理';
    if (urgency === 'medium') return '1–3 工作日内处理';
    return '非紧急 / 常规跟进';
}

/** Whether this case has AI-collected info that broker should confirm before acting */
export function needsHumanConfirmation(caseItem: TriageResult): boolean {
    // Prefer explicit backend signal when available
    if (typeof caseItem.human_confirmation_required === 'boolean') {
        return caseItem.human_confirmation_required;
    }
    // Backwards‑compatible heuristic (pre‑state‑layer consolidation)
    const cat = (caseItem.issue_category ?? '').toLowerCase();
    const collected = caseItem.collected_fields ?? [];
    if (cat === 'cancellation_warning' || cat === 'payment_lapse_expiration') return true;
    if (collected.some((f) => f.includes('customer_says_sent') || f.includes('already_sent'))) return true;
    if (collected.some((f) => f === 'vin' || f === 'primary_driver')) return true;
    return false;
}

export function getDraftReadinessLabel(result: TriageResult): string {
    return result.manual_followup_needed ? '需您修改后再发' : '可审核草稿';
}

export function formatDateLabel(value?: string): string {
    if (!value) return '—';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString('zh-CN', { hour12: false });
}

export function getPreviewText(text: string, maxLength = 96): string {
    const clean = (text || '').replace(/\s+/g, ' ').trim();
    if (clean.length <= maxLength) return clean;
    return `${clean.slice(0, maxLength - 1)}...`;
}

export function normalizeCaseSourceText(text: string): string {
    return (text || '').replace(/\s+/g, ' ').trim().toLowerCase();
}

/** Most recent of (latest note, latest activity) by created_at — for daily-use "what changed" visibility */
export function getLatestUpdateForDisplay(
    caseItem: Pick<TriageResult, 'case_notes' | 'case_activity'>,
    maxLen = 88,
): string | null {
    const note = caseItem.case_notes?.[0];
    const activity = caseItem.case_activity?.[0];
    if (!note && !activity) return null;
    if (!note) return getPreviewText(activity!.message?.trim() ?? '', maxLen);
    if (!activity) return `最新备注：${getPreviewText(note.body?.trim() ?? '', maxLen - 14)}`;
    const noteTime = new Date(note.created_at ?? 0).getTime();
    const activityTime = new Date(activity.created_at ?? 0).getTime();
    if (activityTime >= noteTime) {
        return getPreviewText(activity.message?.trim() ?? '', maxLen);
    }
    return `最新备注：${getPreviewText(note.body?.trim() ?? '', maxLen - 14)}`;
}

export function hasSavedFollowUpTarget(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by'>): boolean {
    const waitingOn = caseItem.waiting_on ?? 'none';
    const nextContactBy = normalizeFollowUpText(caseItem.next_contact_by);
    return waitingOn !== 'none' || !!nextContactBy;
}

export function getLatestCaseContext(caseItem: Pick<TriageResult, 'case_notes' | 'case_activity'>): string {
    const latest = getLatestUpdateForDisplay(caseItem);
    return latest ?? '暂无备注或操作记录';
}

export function getFollowUpSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by'>): string {
    const waitingOn = caseItem.waiting_on ?? 'none';
    const nextContactBy = normalizeFollowUpText(caseItem.next_contact_by);
    if (waitingOn === 'none' && !nextContactBy) {
        return '尚未保存跟进计划';
    }
    const parts: string[] = [];
    if (waitingOn !== 'none') {
        parts.push(`在等：${humanizeWaitingOn(waitingOn)}`);
    }
    if (nextContactBy) {
        parts.push(`下次跟进：${nextContactBy}`);
    }
    return parts.join(' · ');
}

export function getCaseTrackingSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by' | 'case_notes' | 'case_activity'>): string {
    if (hasSavedFollowUpTarget(caseItem)) {
        return getFollowUpSummary(caseItem);
    }
    return getLatestCaseContext(caseItem);
}

export function getFollowUpDueTag(nextContactBy?: string): { color: string; label: string; kind: FollowUpDueKind } | null {
    const raw = (nextContactBy || '').trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;
    const dueDate = new Date(`${raw}T00:00:00`);
    if (Number.isNaN(dueDate.getTime())) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (dueDate.getTime() < today.getTime()) {
        return { color: 'red', label: '已逾期', kind: 'overdue' };
    }
    if (dueDate.getTime() === today.getTime()) {
        return { color: 'orange', label: '今日到期', kind: 'due_today' };
    }
    if (dueDate.getTime() === tomorrow.getTime()) {
        return { color: 'gold', label: '明日到期', kind: 'due_tomorrow' };
    }
    return null;
}

/** Due-state label for "Where this case stands" — overdue / due today / due tomorrow / no due date */
export function getDueStateLabel(nextContactBy?: string): string {
    const tag = getFollowUpDueTag(nextContactBy);
    if (tag) return tag.label;
    const raw = normalizeFollowUpText(nextContactBy);
    if (raw) return `跟进：${raw}`;
    return '未设日期';
}

export function getCaseAttentionState(
    caseItem: Pick<TriageResult, 'urgency' | 'manual_followup_needed' | 'waiting_on' | 'next_contact_by' | 'case_status'>,
): { label: string; color: string; reason: string; section: 'action' | 'tracking'; kind: AttentionKind } {
    const dueTag = getFollowUpDueTag(caseItem.next_contact_by);
    if (caseItem.case_status === 'done') {
        return {
            label: '已结案',
            color: 'green',
            reason: '已标记完成，保留便于快速查阅。',
            section: 'tracking',
            kind: 'done',
        };
    }
    if (dueTag?.kind === 'overdue') {
        return {
            label: '立即处理',
            color: 'red',
            reason: '跟进日期已过，需尽快复核。',
            section: 'action',
            kind: 'overdue',
        };
    }
    if (dueTag?.kind === 'due_today') {
        return {
            label: '今日到期',
            color: 'orange',
            reason: '计划今日跟进。',
            section: 'action',
            kind: 'due_today',
        };
    }
    if (caseItem.waiting_on === 'broker') {
        return {
            label: '待您处理',
            color: 'volcano',
            reason: '当前阻塞在经纪人行动。',
            section: 'action',
            kind: 'wait_broker',
        };
    }
    if (caseItem.manual_followup_needed && (caseItem.urgency === 'critical' || caseItem.urgency === 'high')) {
        return {
            label: '紧急跟进',
            color: 'red',
            reason: '高风险 case 仍需经纪人跟进。',
            section: 'action',
            kind: 'urgent_manual',
        };
    }
    if (caseItem.manual_followup_needed) {
        return {
            label: '尽快跟进',
            color: 'gold',
            reason: '暂存前需经纪人跟进。',
            section: 'action',
            kind: 'manual_followup',
        };
    }
    if (caseItem.waiting_on && caseItem.waiting_on !== 'none') {
        return {
            label: `在等：${humanizeWaitingOn(caseItem.waiting_on)}`,
            color: 'purple',
            reason: '跟进计划说明当前由谁推进下一步。',
            section: 'tracking',
            kind: 'wait_external',
        };
    }
    if (caseItem.case_status === 'reviewing') {
        return {
            label: '处理中',
            color: 'blue',
            reason: '此 case 已在处理流程中。',
            section: 'tracking',
            kind: 'reviewing',
        };
    }
    return {
        label: '暂存',
        color: 'default',
        reason: '已保存便于快速查阅，暂无待办。',
        section: 'tracking',
        kind: 'parked',
    };
}

/** Queue-level: "可行动" vs "需更多信息" — helps broker scan without opening (office Chinese) */
export function getQueueReadinessLabel(caseItem: SavedCase): { label: string; color: string } {
    const collected = caseItem.collected_fields ?? [];
    const stillNeeded = caseItem.still_needed_fields ?? [];
    const cat = (caseItem.issue_category ?? '').toLowerCase();
    const src = (caseItem.source_text ?? '').toLowerCase();

    if (cat === 'cancellation_warning' || cat === 'payment_lapse_expiration') {
        return { label: '当日处理', color: 'red' };
    }
    if (cat === 'missing_document' || cat === 'underwriting_followup') {
        const hasSent = collected.some((f) => f.includes('customer_says_sent') || f.includes('already_sent'));
        if (hasSent || /发过|already sent|sent it|上周发|又发/i.test(src)) {
            return { label: '需核实收到', color: 'orange' };
        }
        if (stillNeeded.some((f) => f.includes('verify_carrier'))) {
            return { label: '需核实收到', color: 'orange' };
        }
        return stillNeeded.length > 0 ? { label: '需更多信息', color: 'gold' } : { label: '可行动', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Add car quote' || /add.?car|加车|加一台|新车|报价/i.test(src)) {
        if (caseItem.lifecycle_status === 'handed_off' || caseItem.lifecycle_status === 'office_followup') {
            if ((caseItem.still_needed_fields?.filter(Boolean).length ?? 0) > 0) {
                return { label: '已送达·待补缺口', color: 'orange' };
            }
            return { label: '已报送办公室', color: 'green' };
        }
        if (caseItem.lifecycle_status === 'handoff_pending') {
            return { label: '待客户提交', color: 'gold' };
        }
        const qrs = (caseItem as { quote_ready_status?: string }).quote_ready_status;
        if (qrs === 'quote_ready') return { label: '可报价', color: 'green' };
        if (qrs === 'almost_ready') return { label: '差一点', color: 'gold' };
        if (qrs === 'need_more') return { label: '信息不足', color: 'orange' };
        const hasCore = collected.some((f) => ['year', 'make_model', 'zip', 'delivery_date'].includes(f));
        const needsDriver = stillNeeded.some((f) => f.includes('driver'));
        if (hasCore && !needsDriver) return { label: '可行动', color: 'green' };
        if (stillNeeded.length > 0) return { label: '需更多信息', color: 'gold' };
        return { label: '可行动', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Claim intake' || /accident|事故|claim|撞/i.test(src)) {
        return stillNeeded.length > 0 ? { label: '需更多信息', color: 'gold' } : { label: '可行动', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Premium review' || /保费|续保|premium|renewal/i.test(src)) {
        return stillNeeded.some((f) => f.includes('renewal') || f.includes('bill')) ? { label: '需更多信息', color: 'gold' } : { label: '可行动', color: 'green' };
    }
    return { label: '可行动', color: 'green' };
}

/** Compact flow-specific preview for queue cards — not full case card (office Chinese) */
export function getCompactQueuePreview(caseItem: SavedCase): string {
    const collected = (caseItem.collected_fields ?? []).map(humanizeStructuredField);
    const stillNeeded = (caseItem.still_needed_fields ?? []).map(humanizeStructuredField);
    const focus = inferCaseFocusFromText(caseItem.source_text ?? '');
    const cat = caseItem.issue_category ?? '';

    if (focus === 'Add car quote' || /add.?car|加车|加一台|新车|报价/i.test((caseItem.source_text ?? '').toLowerCase())) {
        const formal = addCarQueueStatusPhase(caseItem) === 'submitted';
        const cl = resolveCaseLifecycle(caseItem);
        const phaseLead = formal
            ? '已正式送达 · '
            : cl === 'ready_for_handoff'
              ? '待客户正式提交 · '
              : `${caseLifecycleUserLabel(cl)} · `;
        const submittedAt = formatPortalLocalDateTime(
            caseItem.formal_submitted_at ?? caseItem.created_at,
        );
        const activity = formatPortalLocalDateTime(caseItem.updated_at);
        const activityBit =
            submittedAt && activity && submittedAt !== activity
                ? `送达 ${submittedAt} · 最近活动 ${activity}`
                : activity
                  ? `最近活动 ${activity}`
                  : submittedAt
                    ? `送达 ${submittedAt}`
                    : '';
        const qrs = (caseItem as { quote_ready_status?: string }).quote_ready_status;
        const statusLabel = qrs ? (QUOTE_READY_STATUS_LABELS[qrs]?.label ?? '') : '';
        if (collected.length > 0 || stillNeeded.length > 0 || statusLabel) {
            const parts: string[] = [];
            if (statusLabel) parts.push(statusLabel);
            if (collected.length > 0) parts.push(`已收集：${collected.slice(0, 4).join('、')}`);
            if (stillNeeded.length > 0) parts.push(`还缺：${stillNeeded.slice(0, 2).join('、')}`);
            const core = parts.join(' · ') || '加车报价';
            const boundaryBit = getOfficeCaseBoundaryPreviewSuffix(caseItem.case_boundary);
            const withBoundary = boundaryBit ? `${core} · ${boundaryBit}` : core;
            return activityBit ? `${phaseLead}${withBoundary} · ${activityBit}` : `${phaseLead}${withBoundary}`;
        }
        const boundaryBit = getOfficeCaseBoundaryPreviewSuffix(caseItem.case_boundary);
        const lead = boundaryBit ? `加车报价 · ${boundaryBit}` : '加车报价';
        return activityBit ? `${phaseLead}${lead} · ${activityBit}` : `${phaseLead}${lead}`;
    }
    if (focus === 'Premium review' || cat === 'renewal_reminder') {
        if (collected.length > 0 || stillNeeded.length > 0) {
            return `保费关注${collected.length > 0 ? ` · ${collected.slice(0, 2).join('、')}` : ''}${stillNeeded.some((s) => /renewal|bill/i.test(s)) ? ' · 还缺续保通知' : ''}`;
        }
        return '保费关注 · 待复核选项';
    }
    if (focus === 'Claim intake' || /accident|事故|claim/i.test((caseItem.source_text ?? '').toLowerCase())) {
        if (collected.length > 0 || stillNeeded.length > 0) {
            return `已报事故${collected.length > 0 ? ` · ${collected.slice(0, 2).join('、')}` : ''}${stillNeeded.length > 0 ? ` · 还缺：${stillNeeded.slice(0, 2).join('、')}` : ''}`;
        }
        return '已报事故 · 收集现场照片和对方信息';
    }
    if (cat === 'missing_document' || cat === 'underwriting_followup') {
        const hasSent = (caseItem.collected_fields ?? []).some((f) => f.includes('customer_says_sent') || f.includes('already_sent'));
        if (hasSent || /发过|already sent|sent it|上周发|又发/i.test(caseItem.source_text ?? '')) {
            return '客户称已发送 · 需核实收到';
        }
        if (stillNeeded.length > 0) {
            return `还缺：${stillNeeded.slice(0, 2).join('、')}`;
        }
        return '材料补交 · 需核实';
    }
    if (cat === 'cancellation_warning' || cat === 'payment_lapse_expiration') {
        return '当日处理 · 确认应付余额';
    }
    return getPreviewText(caseItem.broker_next_step ?? '', 72);
}

export function getCaseWorkbenchScore(
    caseItem: Pick<TriageResult, 'urgency' | 'manual_followup_needed' | 'waiting_on' | 'next_contact_by' | 'case_status'>,
): number {
    const attention = getCaseAttentionState(caseItem);
    let score = attention.section === 'action' ? 100 : 0;
    if (attention.kind === 'overdue') score += 70;
    else if (attention.kind === 'due_today') score += 60;
    else if (attention.kind === 'wait_broker') score += 50;
    else if (attention.kind === 'urgent_manual') score += 40;
    else if (attention.kind === 'manual_followup') score += 25;
    if (caseItem.urgency === 'critical') score += 20;
    else if (caseItem.urgency === 'high') score += 15;
    else if (caseItem.urgency === 'medium') score += 8;
    if (caseItem.case_status === 'done') score -= 100;
    return score;
}

export function orderCasesForWorkbench<T extends SavedCase>(cases: T[]): T[] {
    return [...cases].sort((a, b) => {
        const scoreDiff = getCaseWorkbenchScore(b) - getCaseWorkbenchScore(a);
        if (scoreDiff !== 0) return scoreDiff;
        return (b.updated_at || '').localeCompare(a.updated_at || '');
    });
}

/** Customer-facing urgency note */
export function getCustomerUrgencyNote(urgency: TriageResult['urgency']): string {
    if (urgency === 'critical') return 'This needs urgent attention.';
    if (urgency === 'high') return 'This needs attention soon.';
    if (urgency === 'medium') return 'We will review within 1–3 business days.';
    return 'No urgent action needed.';
}

/** Customer-facing follow-up note when broker will act */
export function getCustomerFollowUpNote(manualFollowupNeeded: boolean): string {
    if (manualFollowupNeeded) {
        return "Chen Kui's office will review this and follow up with you.";
    }
    return 'No further action needed from our office at this time.';
}

/** Hybrid add-car intake: compose one first message from short structured fields (ADD_CAR_HYBRID_INTAKE). */
export function composeAddCarStructuredIntakeMessage(fields: {
    year: string;
    makeModel: string;
    zip: string;
    delivery: string;
    driver: string;
}): string | null {
    const year = fields.year.trim();
    const makeModel = fields.makeModel.trim();
    const zip = fields.zip.trim();
    const delivery = fields.delivery.trim();
    const driver = fields.driver.trim();
    if (!year && !makeModel && !zip && !delivery && !driver) return null;
    const details: string[] = [];
    if (year) details.push(`年份：${year}`);
    if (makeModel) details.push(`车型：${makeModel}`);
    if (zip) details.push(`邮编：${zip}`);
    if (delivery) details.push(`提车/预计拿车：${delivery}`);
    if (driver) details.push(`主要驾驶人：${driver}`);
    return `我想给新车加保报价。${details.join('；')}。`;
}
export function isWithinLast24Hours(iso: string | undefined): boolean {
    if (!iso) return false;
    const t = Date.parse(iso);
    if (Number.isNaN(t)) return false;
    return Date.now() - t <= 24 * 60 * 60 * 1000;
}

export function passesWorkbenchListFilter(c: SavedCase, f: WorkbenchListFilter): boolean {
    const test = Boolean(c.workbench_test);
    const archived = Boolean(c.workbench_archived);
    const lane = c.workbench_lane_kind;
    const pg = c.pg_mirror_state;

    switch (f) {
        case 'all':
            return true;
        case 'formal':
            return !test && !archived;
        case 'test':
            return test;
        case 'legacy':
            return lane === 'legacy';
        case 'mirror_bad':
            return pg === 'pg_missing' || pg === 'mismatch';
        case 'recent24h':
            return isWithinLast24Hours(c.updated_at);
        default:
            return true;
    }
}

export function workbenchLaneLabel(lane: SavedCase['workbench_lane_kind']): string {
    switch (lane) {
        case 'explicit':
            return '标准加车识别';
        case 'legacy':
            return '历史识别·加车';
        case 'other':
            return '其他事项';
        default:
            return '—';
    }
}

/** Hide raw API tokens (e.g. add_car) from office UI */
export function humanizeServiceLaneOffice(sl?: string | null): string | null {
    const s = (sl || '').trim().toLowerCase();
    if (!s) return null;
    if (s === 'add_car' || s === 'add-car') return '加车报价';
    return s.replace(/_/g, ' ');
}

/** Add-Car: which vehicle-related slots are already captured (values live in thread; we only show field coverage) */
export function buildAddCarVehicleGlanceLine(caseItem: TriageResult): string | null {
    if (!triageResultLooksLikeAddCar(caseItem)) return null;
    const collected = new Set(caseItem.collected_fields ?? []);
    const keys = ['year', 'make_model', 'model', 'zip', 'delivery_date', 'primary_driver', 'vin'].filter((k) =>
        collected.has(k),
    );
    if (keys.length === 0) return null;
    const labels = keys.map((k) => humanizeStructuredField(k)).filter(Boolean);
    return `已录入要点：${labels.join('、')}`;
}

export function buildOfficeWorkbenchGlance(
    triage: TriageResult & { customer_name?: string | null; customer_phone?: string | null },
    inputFallback: string,
): OfficeGlanceLines {
    const focus =
        inferCaseFocusFromStructuredFields(
            triage.collected_fields,
            triage.still_needed_fields,
            triage.issue_category,
        ) ?? inferCaseFocusFromText(triage.source_text ?? inputFallback);
    const matter =
        (getCaseFocusDisplayLabel(focus) ?? focus)?.trim()
        || humanizeCategory(triage.issue_category, triage.source_text ?? inputFallback);
    const stRaw = (triage.service_type || '').trim();
    const stZh = humanizeServiceLaneOffice(stRaw) ?? stRaw;
    const matterExtra = stZh && !matter.includes(stZh) && stZh !== matter ? `（${stZh}）` : '';

    const name = triage.customer_name?.trim();
    const phone = triage.customer_phone?.trim();
    let contactLine = '';
    if (name || phone) {
        contactLine = [name ? `姓名：${name}` : null, phone ? `电话：${phone}` : null].filter(Boolean).join(' · ');
    } else {
        contactLine = '客户联系：尚未在记录中留名或电话（报价前建议补齐）';
    }

    const formalDelivered = triageResultLooksLikeAddCar(triage) && addCarQueueStatusPhase(triage) === 'submitted';
    const ls = triage.lifecycle_status;
    let stageLine = '';
    if (formalDelivered) {
        stageLine = '阶段：已正式送达办公室 · 可接手跟进';
    } else if (ls === 'handoff_pending') {
        stageLine = '阶段：资料已齐 · 待客户正式提交';
    } else if (ls === 'handed_off' || ls === 'office_followup') {
        stageLine = '阶段：办公室流程中';
    } else {
        stageLine = `阶段：${triage.collection_stage === 'enough_for_handoff' ? '可交办公室（客户侧）' : '信息收集中'}`;
    }

    const still = triage.still_needed_fields?.filter(Boolean) ?? [];
    const missingLine =
        still.length > 0
            ? formalDelivered
                ? `待补问（结构化）：${still
                      .slice(0, 6)
                      .map((f) => humanizeStructuredField(f))
                      .join('、')}${still.length > 6 ? '…' : ''} — 记录已送达办公室，建议先向客户补齐再深报价`
                : `还缺：${still.slice(0, 6).map((f) => humanizeStructuredField(f)).join('、')}${still.length > 6 ? '…' : ''}`
            : null;

    const qrs = triage.quote_ready_status;
    const quotePrepLine =
        triageResultLooksLikeAddCar(triage) && qrs && QUOTE_READY_STATUS_LABELS[qrs]
            ? `整理度（报价准备）：${QUOTE_READY_STATUS_LABELS[qrs].label}`
            : null;

    const recent = getRecentCustomerMessages(triage, 1);
    const latestCustomerLine = recent[0] ? `最近客户：${getPreviewText(recent[0], 120)}` : null;

    const vehicleLine = buildAddCarVehicleGlanceLine(triage);

    return {
        contactLine,
        matterLine: `事项：${matter}${matterExtra}`,
        stageLine,
        vehicleLine,
        quotePrepLine,
        missingLine,
        latestCustomerLine,
        nextStep: (triage.broker_next_step ?? '').trim() || '—（系统未生成下一步，请阅原文或备注）',
    };
}

export function workbenchPgMirrorLabel(pg: SavedCase['pg_mirror_state']): string {
    switch (pg) {
        case 'mirrored':
            return 'PG 已镜像';
        case 'pg_missing':
            return 'PG 缺失';
        case 'mismatch':
            return '镜像不一致';
        case 'unknown':
        default:
            return 'PG 未校验';
    }
}

export function workbenchPgMirrorTagColor(pg: SavedCase['pg_mirror_state']): string {
    switch (pg) {
        case 'mirrored':
            return 'cyan';
        case 'pg_missing':
        case 'mismatch':
            return 'volcano';
        default:
            return 'default';
    }
}

export function hasWorkbenchOpsTags(savedCase: SavedCase): boolean {
    return Boolean(
        savedCase.workbench_test
        || savedCase.workbench_archived
        || savedCase.workbench_lane_kind
        || savedCase.pg_mirror_state,
    );
}

/** Short id for queue anchor / scan — long UUIDs show prefix + ellipsis */
export function formatQueueCaseIdShort(caseId: string | undefined): string {
    const s = (caseId ?? '').trim();
    if (!s) return '—';
    if (s.length <= 12) return s;
    return `${s.slice(0, 8)}…`;
}
