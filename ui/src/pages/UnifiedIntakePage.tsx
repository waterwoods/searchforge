/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — customer-facing intake
 * Tab B: Broker Workbench — office tool for triage, case sheet, follow-up, and drafts
 *
 * Customer Entry is the default visible tab.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
    Alert,
    Button,
    Card,
    Col,
    Collapse,
    Divider,
    Input,
    Radio,
    Row,
    Select,
    Space,
    Spin,
    Tabs,
    Tag,
    Typography,
    message,
} from 'antd';
import {
    ClockCircleOutlined,
    CopyOutlined,
    CustomerServiceOutlined,
    InboxOutlined,
    PaperClipOutlined,
    PlayCircleOutlined,
    SendOutlined,
    SwapOutlined,
    UploadOutlined,
} from '@ant-design/icons';
import { ScenarioReplayTab } from '../components/simulation/ScenarioReplayTab';
import { AddCarFlowExplanation } from '../components/intake/AddCarFlowExplanation';
import {
    AddCarHandoffGroupedSnapshot,
    AddCarRecordSummaryRail,
    addCarNextOwnerLine,
    computeAddCarFlowStep,
    isFormalSubmissionToOfficeComplete,
} from '../components/intake/AddCarRecordSummaryRail';
import {
    addSavedCaseNote,
    appendFollowUpMessage,
    clearSessionId,
    getInProgressSession,
    getSessionId,
    getAttachmentDownloadUrl,
    listRecentCases,
    triageMessage,
    updateSavedCaseFollowUp,
    updateSavedCaseStatus,
    uploadCaseAttachment,
    type CaseStatus,
    type SavedCase,
    type SoftRouteIntent,
    type TriageResult,
    type WaitingOn,
} from '../api/inboxTriage';
import { copyToClipboard } from '../utils/demoCopy';
import { useClientConfig } from '../context/ClientConfigContext';
import type { UiCopy } from '../api/clientConfig';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

/** Shared chrome width for unified intake (light island inside dark app shell). */
const UNIFIED_INTAKE_SHELL_MAX = 1280;

/** Derive quick-start buttons from ui_copy; fallback to defaults */
function getQuickStartButtons(uiCopy: UiCopy): Array<{ id: SoftRouteIntent; label: string; shortLabel: string; starterMessage: string }> {
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

type DemoExample = {
    label: string;
    purpose: string;
    text: string;
    urgency: TriageResult['urgency'];
};

type FounderDemoSeed = {
    label: string;
    purpose: string;
    text: string;
    status?: CaseStatus;
    waiting_on?: WaitingOn;
    next_contact_by?: string;
    note?: string;
    open_after_load?: boolean;
};

/** Default quick-start buttons when config missing */
const DEFAULT_QUICK_START_BUTTONS: Array<{ id: SoftRouteIntent; label: string; shortLabel: string; starterMessage: string }> = [
    { id: 'add_car', label: '办理加车报价', shortLabel: '加车', starterMessage: '我想加新车报价' },
    { id: 'remove_car', label: '保单变更', shortLabel: '变更', starterMessage: '我想从保单拿掉一辆车' },
    { id: 'claim_intake', label: '报事故', shortLabel: '事故', starterMessage: '刚出事故了' },
    { id: 'cancellation_warning', label: '付款 / 账单', shortLabel: '付款', starterMessage: '付款有问题' },
    { id: 'missing_document', label: '上传材料', shortLabel: '材料', starterMessage: '有材料要补' },
    { id: 'talk_to_agent', label: '联系人工', shortLabel: '联系人工', starterMessage: '我想联系陈奎办公室' },
];

const CUSTOMER_ENTRY_EXAMPLES: DemoExample[] = [
    {
        label: 'Payment failed',
        purpose: 'Cancellation risk',
        urgency: 'critical',
        text: '客户问：这个英文 notice 说 payment failed，我现在怎么办？',
    },
    {
        label: 'English notice confusion',
        purpose: 'What does this mean?',
        urgency: 'medium',
        text: '客户发来一张DMV的信，问「这是什么意思？我需要做什么？」',
    },
    {
        label: 'Missing document',
        purpose: 'Declaration page / DL',
        urgency: 'medium',
        text: '客户发来carrier email，说 declaration page missing，他问这个什么意思',
    },
    {
        label: 'Add car / premium',
        purpose: 'Quote or review',
        urgency: 'medium',
        text: '客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价',
    },
    {
        label: 'BMW X5 quote (Chinese)',
        purpose: 'New car premium quote',
        urgency: 'medium',
        text: '我刚刚买了2026年的宝马X5，我想问一下保费多少钱',
    },
];

const QUICK_FILL_EXAMPLES: DemoExample[] = [
    {
        label: 'Cancellation warning',
        purpose: 'Urgent broker action',
        urgency: 'critical',
        text: 'Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.',
    },
    {
        label: 'Missing document',
        purpose: 'Operational follow-up',
        urgency: 'medium',
        text: "Underwriting requested driver's license copy. Client says \"I already sent it last week.\"",
    },
    {
        label: 'Mixed shorthand chase',
        purpose: 'Messy real-world follow-up',
        urgency: 'medium',
        text: 'UW follow up - need dec page + garaging proof. 客户说上周发过了',
    },
    {
        label: 'Payment failed / lapse risk',
        purpose: 'Same-day payment fix',
        urgency: 'high',
        text: 'AutoPay failed again, please update card to avoid interruption in coverage',
    },
    {
        label: 'Renewal / premium too high',
        purpose: 'Structured renewal; remove-vehicle interest',
        urgency: 'medium',
        text: '续保保费太高了，其中一辆去掉会便宜吗',
    },
    {
        label: 'Claim intake / accident',
        purpose: 'Structured claim; first response',
        urgency: 'medium',
        text: '刚出事故了，要收集什么？',
    },
];

function getIsoDateOffset(daysFromToday: number): string {
    const value = new Date();
    value.setHours(0, 0, 0, 0);
    value.setDate(value.getDate() + daysFromToday);
    return value.toISOString().slice(0, 10);
}

const FOUNDER_DEMO_QUEUE: FounderDemoSeed[] = [
    {
        label: 'Cancellation risk',
        purpose: 'Same-day risk triage; broker-owned next move',
        text: 'Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client is worried coverage may stop today; call after confirming balance due.',
        open_after_load: true,
    },
    {
        label: 'Missing document follow-up',
        purpose: 'Reopen continuity; waiting-client state; saved note',
        text: 'UW follow up - need dec page + garaging proof. 客户说上周发过了',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(1),
        note: 'Client said they can resend declaration page and garaging proof tomorrow morning.',
    },
    {
        label: 'Add-car quote request',
        purpose: 'Practical quote intake; everyday broker work',
        text: '客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Same-day quote if VIN and driver details come back before end of day.',
    },
    {
        label: 'Premium review',
        purpose: 'Retention-style follow-up; repetitive office work',
        text: '客户说这个月保费太高了，能不能看看怎么降一点',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(2),
        note: 'Waiting on latest bill and declaration page before reviewing adjustment options.',
    },
    {
        label: 'DMV / SR-22 help',
        purpose: 'Broker-style guidance on confusing DMV wording',
        text: 'DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(1),
        note: 'Confirm whether DMV wants SR-22 filing proof before telling client what to bring.',
    },
    {
        label: 'Payment failed / lapse risk',
        purpose: 'AutoPay failure; same-day fix needed',
        text: 'AutoPay failed again, please update card to avoid interruption in coverage',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Same-day payment fix; client may not have seen carrier notice yet.',
    },
    {
        label: 'Remove car',
        purpose: 'Vehicle removal; policy update',
        text: '客户卖掉旧车了，想把2014 Honda Accord从保单拿掉',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Confirm sale date and remove vehicle; check if replacement car needs adding.',
    },
    {
        label: 'English notice + Chinese confusion',
        purpose: 'Chinese client confused by English carrier notice',
        text: '客户问：这个英文 notice 说 payment failed，我现在怎么办？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client confused by English carrier notice; draft reply in Chinese.',
    },
    {
        label: 'Declaration page missing',
        purpose: 'Carrier missing doc; client asks what it means',
        text: '客户发来carrier email，说 declaration page missing，他问这个什么意思',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(1),
        note: 'Explain declaration page = 保单首页; client will resend.',
    },
    {
        label: 'Chinese cancellation summary',
        purpose: 'Client pasted carrier summary in Chinese',
        text: '保险公司说我的保单7天后要cancel',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'Client pasted carrier summary; confirm exact deadline and balance due.',
    },
    {
        label: 'Claim intake / accident first response',
        purpose: 'Structured claim intake; broker sees collected/still-needed',
        text: '刚出事故了，要收集什么？',
        status: 'reviewing',
        waiting_on: 'broker',
        next_contact_by: getIsoDateOffset(0),
        note: 'First-response claim; guide client to collect photos and other driver info.',
    },
    {
        label: 'Renewal / remove one car to save',
        purpose: 'Structured renewal; remove-vehicle interest',
        text: '续保保费太高了，其中一辆去掉会便宜吗',
        status: 'waiting_client',
        waiting_on: 'client',
        next_contact_by: getIsoDateOffset(2),
        note: 'Waiting on latest bill and which vehicle to remove before quoting.',
    },
];

const CASE_STATUS_OPTIONS: Array<{ value: CaseStatus; label: string }> = [
    { value: 'new', label: '新建' },
    { value: 'reviewing', label: '处理中' },
    { value: 'waiting_client', label: '等客户' },
    { value: 'done', label: '已完成' },
];

const WAITING_ON_OPTIONS: Array<{ value: WaitingOn; label: string }> = [
    { value: 'none', label: '无阻塞' },
    { value: 'client', label: '客户' },
    { value: 'broker', label: '经纪人 / 办公室' },
    { value: 'carrier', label: '保险公司' },
    { value: 'underwriting', label: '核保' },
];

type FollowUpDraft = {
    waiting_on: WaitingOn;
    next_contact_by: string;
};

function normalizeFollowUpText(value?: string): string {
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

/** Quote-ready status labels (ADD_CAR_REAL_INTAKE_LITE) */
const QUOTE_READY_STATUS_LABELS: Record<string, { label: string; color: string }> = {
    quote_ready: { label: '可报价', color: 'green' },
    almost_ready: { label: '差一点', color: 'gold' },
    need_more: { label: '信息不足', color: 'orange' },
};

/** Lifecycle strip labels — maps existing API `lifecycle_status` only */
const LIFECYCLE_STATUS_LABELS: Record<string, { label: string; color: string }> = {
    collecting: { label: '信息收集中', color: 'default' },
    handoff_pending: { label: '资料已齐 · 可提交', color: 'gold' },
    handed_off: { label: '已交办公室', color: 'blue' },
    /** Canonical with customer closure / scorecard: office-owned processing */
    office_followup: { label: '办公室处理中', color: 'purple' },
};

/** When backend returns ISO timestamp on persisted case — customer closure observability. */
function formatPortalLocalDateTime(iso: string | undefined): string | null {
    const s = (iso ?? '').trim();
    if (!s) return null;
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return d.toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' });
}

/** Office queue + detail: same vocabulary as customer Add-Car status strip (STATE parity). */
function getOfficeLifecycleTag(lifecycleStatus: string | undefined): { label: string; color: string } | null {
    const key = (lifecycleStatus ?? '').trim();
    if (!key) return null;
    const mapped = LIFECYCLE_STATUS_LABELS[key];
    if (mapped) return mapped;
    return { label: key, color: 'default' };
}

/** Ordered chips for Add-Car status strip (ADD_CAR_RESULT_CARD_STATUS_FLOW_HARDENING_SPRINT) */
function buildAddCarStatusStripChips(
    triage: TriageResult | null | undefined,
    phase: 'intake' | 'submitted',
): Array<{ label: string; color: string }> {
    const out: Array<{ label: string; color: string }> = [{ label: '加车报价', color: 'blue' }];
    if (!triage) return out;

    if (phase === 'submitted') {
        out.push({ label: '已报送办公室', color: 'processing' });
        const qrs = triage.quote_ready_status;
        if (qrs && QUOTE_READY_STATUS_LABELS[qrs]) {
            const q = QUOTE_READY_STATUS_LABELS[qrs];
            out.push({ label: `整理度：${q.label}`, color: q.color });
        }
        const ls = triage.lifecycle_status;
        if (ls === 'office_followup' && LIFECYCLE_STATUS_LABELS.office_followup) {
            out.push({ ...LIFECYCLE_STATUS_LABELS.office_followup });
        } else if (ls === 'collecting' && LIFECYCLE_STATUS_LABELS.collecting) {
            out.push({ ...LIFECYCLE_STATUS_LABELS.collecting });
        } else if (ls === 'handed_off') {
            out.push({ label: '办公室处理中', color: 'cyan' });
        }
        return out;
    }

    const qrs = triage.quote_ready_status;
    if (qrs && QUOTE_READY_STATUS_LABELS[qrs]) {
        out.push({ ...QUOTE_READY_STATUS_LABELS[qrs] });
    }
    const ls = triage.lifecycle_status;
    if (ls && LIFECYCLE_STATUS_LABELS[ls]) {
        out.push({ ...LIFECYCLE_STATUS_LABELS[ls] });
    } else if (triage.collection_stage) {
        out.push(
            triage.collection_stage === 'enough_for_handoff'
                ? { label: '可交办公室', color: 'green' }
                : { label: '信息收集中', color: 'default' },
        );
    }
    return out;
}

function AddCarCaseStatusStrip({
    triage,
    phase,
    caption,
}: {
    triage: TriageResult | null | undefined;
    phase: 'intake' | 'submitted';
    caption?: string;
}) {
    const chips = buildAddCarStatusStripChips(triage, phase);
    const bg = phase === 'submitted' ? '#f6ffed' : '#f0f5ff';
    const borderColor = phase === 'submitted' ? '#b7eb8f' : '#adc6ff';
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                alignItems: 'center',
                padding: '10px 12px',
                background: bg,
                borderRadius: 8,
                border: `1px solid ${borderColor}`,
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 12, fontWeight: 700, letterSpacing: 0.2 }}>
                {caption ?? '当前状态'}
            </Text>
            {chips.map((c, i) => (
                <Tag key={`${c.label}-${i}`} color={c.color} style={{ margin: 0, fontSize: 12 }}>
                    {c.label}
                </Tag>
            ))}
        </div>
    );
}

/** Non–Add-Car: visible case-style status chips (Zendesk-like scanability). */
function buildGenericIntakeStatusChips(triage: TriageResult): Array<{ label: string; color: string }> {
    const out: Array<{ label: string; color: string }> = [{ label: '客户报送', color: 'blue' }];
    if (triage.issue_category) {
        out.push({ label: humanizeCategory(triage.issue_category, triage.source_text), color: 'cyan' });
    }
    if (triage.case_status) {
        const lab = CASE_STATUS_OPTIONS.find((o) => o.value === triage.case_status)?.label ?? triage.case_status;
        out.push({ label: `记录：${lab}`, color: 'geekblue' });
    }
    const ls = triage.lifecycle_status;
    if (ls && LIFECYCLE_STATUS_LABELS[ls]) {
        out.push({ ...LIFECYCLE_STATUS_LABELS[ls] });
    } else if (triage.collection_stage) {
        out.push(
            triage.collection_stage === 'enough_for_handoff'
                ? { label: '可交办公室', color: 'green' }
                : { label: '信息收集中', color: 'default' },
        );
    }
    const qrs = triage.quote_ready_status;
    if (qrs && QUOTE_READY_STATUS_LABELS[qrs]) {
        const q = QUOTE_READY_STATUS_LABELS[qrs];
        out.push({ label: `整理度：${q.label}`, color: q.color });
    }
    return out;
}

function GenericIntakeStatusStrip({
    triage,
    caption,
}: {
    triage: TriageResult | null | undefined;
    caption?: string;
}) {
    if (!triage) return null;
    const chips = buildGenericIntakeStatusChips(triage);
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                alignItems: 'center',
                padding: '10px 12px',
                background: '#fafafa',
                borderRadius: 8,
                border: '1px solid #d9d9d9',
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
                {caption ?? '当前状态'}
            </Text>
            {chips.map((c, i) => (
                <Tag key={`${c.label}-${i}`} color={c.color} style={{ margin: 0, fontSize: 12 }}>
                    {c.label}
                </Tag>
            ))}
        </div>
    );
}

/** Amazon-style: one clear transaction path (3 beats). */
function IntakeFlowStepTrack({
    flowStep,
    trackLabel,
    step1,
    step2,
    step3,
}: {
    flowStep: 1 | 2 | 3;
    trackLabel: string;
    step1: string;
    step2: string;
    step3: string;
}) {
    const steps: Array<{ n: 1 | 2 | 3; label: string }> = [
        { n: 1, label: step1 },
        { n: 2, label: step2 },
        { n: 3, label: step3 },
    ];
    return (
        <div
            style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 8,
                padding: '10px 12px',
                background: '#fcfcfc',
                borderRadius: 8,
                border: '1px solid #f0f0f0',
                marginBottom: 12,
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
                {trackLabel}
            </Text>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
                {steps.map((s, idx) => {
                    const active = flowStep === s.n;
                    const done = flowStep > s.n;
                    return (
                        <span key={s.n} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                            {idx > 0 ? (
                                <Text type="secondary" style={{ fontSize: 12, userSelect: 'none' }}>
                                    →
                                </Text>
                            ) : null}
                            <Tag
                                color={done ? 'success' : active ? 'processing' : 'default'}
                                style={{ margin: 0, fontSize: 12, fontWeight: active ? 600 : 400 }}
                            >
                                {s.n}. {s.label}
                            </Tag>
                        </span>
                    );
                })}
            </div>
        </div>
    );
}

/** Structured field labels for broker scan — add-car, renewal, claim */
const ADD_CAR_FIELD_LABELS: Record<string, string> = {
    year: 'Year',
    make_model: 'Make/Model',
    zip: 'ZIP',
    delivery_date: 'Delivery',
    primary_driver: 'Primary driver',
    vin: 'VIN',
    name: 'Name',
    phone: 'Phone',
};

const RENEWAL_FIELD_LABELS: Record<string, string> = {
    premium_concern: 'Premium too high',
    renewal_context: 'Renewal context',
    remove_vehicle_interest: 'Remove vehicle interest',
    coverage_adjust_interest: 'Coverage adjust interest',
    policy_bill_sent: 'Policy/bill sent',
    renewal_notice_or_bill: 'Renewal notice or bill',
    current_premium_details: 'Current premium details',
    which_vehicle_to_remove: 'Which vehicle to remove',
    target_coverage_preference: 'Target coverage preference',
};

const CLAIM_FIELD_LABELS: Record<string, string> = {
    accident_reported: 'Accident reported',
    hit_and_run: 'Hit-and-run',
    photos: 'Photos',
    other_driver_info: 'Other driver info',
    police_report: 'Police report',
    injuries: 'Injuries',
    other_driver_insurance_license: 'Other driver insurance/license',
    accident_time_location: 'Accident time/location',
    police_report_if_applicable: 'Police report (if applicable)',
};

/** Missing document / underwriting follow-up — selective structured intake */
const MISSING_DOC_FIELD_LABELS: Record<string, string> = {
    requested_declaration_page: 'Requested: Declaration page',
    requested_garaging_proof: 'Requested: Garaging proof',
    requested_driver_license: 'Requested: Driver license',
    requested_questionnaire: 'Requested: Questionnaire',
    customer_says_sent_declaration_page: 'Customer says sent: Declaration page',
    customer_says_sent_garaging_proof: 'Customer says sent: Garaging proof',
    customer_says_sent_driver_license: 'Customer says sent: Driver license',
    customer_says_sent_questionnaire: 'Customer says sent: Questionnaire',
    already_sent_claimed: 'Customer claims already sent',
    underwriting_followup: 'UW follow-up',
    declaration_page: 'Declaration page',
    garaging_proof: 'Garaging proof',
    driver_license: 'Driver license',
    questionnaire: 'Questionnaire',
    verify_carrier_received: 'Verify carrier received',
};

/** Broker-facing structured field labels (office Chinese); prefer CUSTOMER_FIELD_LABELS_ZH when available */
function humanizeStructuredField(field: string): string {
    return (
        CUSTOMER_FIELD_LABELS_ZH[field] ??
        ADD_CAR_FIELD_LABELS[field] ??
        RENEWAL_FIELD_LABELS[field] ??
        CLAIM_FIELD_LABELS[field] ??
        MISSING_DOC_FIELD_LABELS[field] ??
        field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    );
}

const CATEGORY_DISPLAY_LABELS: Record<string, string> = {
    cancellation_warning: '取消风险',
    payment_lapse_expiration: '付款/取消风险',
    missing_document: '材料补交',
    missing_signature: '缺签名',
    underwriting_followup: '核保跟进',
    renewal_reminder: '续保提醒',
    policy_delay_pending: '保单待出',
    informational: '信息类',
    unclear: '需澄清',
    customer_question: '客户咨询',
    customer_requested_human: '联系人工',
};

/** Case focus display labels (broker-facing Chinese) — maps internal focus keys to office Chinese */
const CASE_FOCUS_DISPLAY_ZH: Record<string, string> = {
    '联系人工': '联系人工',
    'Add car quote': '加车报价',
    'Remove car': '删车',
    'Premium review': '保费复查',
    'Claim intake': '事故报险',
    'DMV / SR-22 help': 'DMV / SR-22 协助',
    'Missing document': '材料补交',
    'Payment / cancellation risk': '付款/取消风险',
};

function getCaseFocusDisplayLabel(focus: string | null): string | null {
    if (!focus) return null;
    return CASE_FOCUS_DISPLAY_ZH[focus] ?? focus;
}

function inferCaseFocusFromText(text: string): string | null {
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
function getRecentCustomerMessages(
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
function getCaseReportOneLiner(
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
function inferCaseFocusFromStructuredFields(
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

const ADD_CAR_TRIAGE_FIELD_IDS = new Set([
    'year',
    'make_model',
    'model',
    'zip',
    'delivery_date',
    'primary_driver',
    'vin',
]);

/** Whether triage output indicates an Add-Car quote transaction (for customer UI framing). */
function triageResultLooksLikeAddCar(triage: TriageResult | undefined): boolean {
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

function customerEntryIsAddCarActive(
    turns: Array<{ role: string; triageResult?: TriageResult }>,
    selectedIntent: SoftRouteIntent | null,
): boolean {
    if (selectedIntent === 'add_car') return true;
    const lastSystem = [...turns].reverse().find((t) => t.role === 'system');
    return triageResultLooksLikeAddCar(lastSystem?.triageResult);
}

function humanizeCategory(cat: string, sourceText?: string): string {
    const category = (cat || '').trim();
    if (category === 'customer_requested_human') return '联系人工';
    if (category === 'customer_question' && sourceText) {
        const focus = inferCaseFocusFromText(sourceText);
        if (focus) return focus;
    }
    return CATEGORY_DISPLAY_LABELS[category] ?? category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Customer-facing (Chinese) field labels; also used for broker Workbench (office Chinese) */
const CUSTOMER_FIELD_LABELS_ZH: Record<string, string> = {
    year: '年份',
    make_model: '车型',
    zip: '邮编',
    delivery_date: '提车日期',
    primary_driver: '主驾信息',
    vin: '车架号',
    name: '姓名',
    phone: '电话',
    model: '车型',
    notice_present: '有通知',
    payment_proof_or_screenshot: '付款凭证/截图',
    verify_carrier_received: '需核实保险公司收到',
    requested_declaration_page: '需保单首页',
    requested_driver_license: '需驾照',
    requested_garaging_proof: '需停放证明',
    customer_says_sent_declaration_page: '客户说已发保单首页',
    customer_says_sent_driver_license: '客户说已发驾照',
    customer_says_sent_garaging_proof: '客户说已发停放证明',
    already_sent_claimed: '客户说已发过',
    underwriting_followup: '核保跟进',
    accident_reported: '已报事故',
    photos: '现场照片',
    other_driver_info: '对方信息',
    accident_time_location: '事故时间地点',
    premium_concern: '保费关注',
    renewal_context: '续保相关',
    remove_vehicle_interest: '考虑删车',
    policy_bill_sent: '已发保单/账单',
    renewal_notice_or_bill: '续保通知/账单',
    current_premium_details: '当前保费明细',
    which_vehicle_to_remove: '拟删车辆',
    target_coverage_preference: '目标保障偏好',
    coverage_adjust_interest: '保障调整意向',
    hit_and_run: '肇事逃逸',
    police_report: '报警记录',
    injuries: '受伤情况',
    other_driver_insurance_license: '对方保险/驾照',
    police_report_if_applicable: '报警记录（如适用）',
    requested_questionnaire: '需问卷',
    customer_says_sent_questionnaire: '客户说已发问卷',
    declaration_page: '保单首页',
    garaging_proof: '停放证明',
    driver_license: '驾照',
    questionnaire: '问卷',
};

function humanizeStructuredFieldForCustomer(field: string): string {
    return CUSTOMER_FIELD_LABELS_ZH[field] ?? humanizeStructuredField(field);
}

/** Workbench queue/detail: align strip phase with customer (one state world). */
function addCarQueueStatusPhase(triage: Pick<TriageResult, 'lifecycle_status'> | null | undefined): 'intake' | 'submitted' {
    const ls = (triage?.lifecycle_status ?? '').trim();
    if (ls === 'handed_off' || ls === 'office_followup') return 'submitted';
    return 'intake';
}

function humanizeCaseStatus(status?: string): string {
    return (status || 'new').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Office workbench: short Chinese label for waiting_on */
function humanizeWaitingOn(waitingOn?: string): string {
    const w = (waitingOn || 'none') as WaitingOn;
    return WAITING_ON_OPTIONS.find((o) => o.value === w)?.label ?? '无阻塞';
}

function getCaseStatusColor(status?: string): string {
    if (status === 'done') return 'green';
    if (status === 'waiting_client') return 'gold';
    if (status === 'reviewing') return 'blue';
    return 'default';
}

function getUrgencyColor(urgency: string): string {
    if (urgency === 'critical') return 'red';
    if (urgency === 'high') return 'orange';
    if (urgency === 'medium') return 'gold';
    return 'green';
}

function UrgencyTag({ urgency }: { urgency: string }) {
    return <Tag color={getUrgencyColor(urgency)}>{urgency.toUpperCase()}</Tag>;
}

function CaseStatusTag({ status }: { status?: string }) {
    const opt = CASE_STATUS_OPTIONS.find((o) => o.value === status);
    return <Tag color={getCaseStatusColor(status)}>{opt?.label ?? humanizeCaseStatus(status)}</Tag>;
}

function getResponseWindow(urgency: TriageResult['urgency']): string {
    if (urgency === 'critical' || urgency === 'high') return '建议当日处理';
    if (urgency === 'medium') return '1–3 工作日内处理';
    return '非紧急 / 常规跟进';
}

/** Whether this case has AI-collected info that broker should confirm before acting */
function needsHumanConfirmation(caseItem: TriageResult): boolean {
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

function getDraftReadinessLabel(result: TriageResult): string {
    return result.manual_followup_needed ? '需您修改后再发' : '可审核草稿';
}

function formatDateLabel(value?: string): string {
    if (!value) return '—';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString('zh-CN', { hour12: false });
}

function getPreviewText(text: string, maxLength = 96): string {
    const clean = (text || '').replace(/\s+/g, ' ').trim();
    if (clean.length <= maxLength) return clean;
    return `${clean.slice(0, maxLength - 1)}...`;
}

function normalizeCaseSourceText(text: string): string {
    return (text || '').replace(/\s+/g, ' ').trim().toLowerCase();
}

/** Most recent of (latest note, latest activity) by created_at — for daily-use "what changed" visibility */
function getLatestUpdateForDisplay(
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

function hasSavedFollowUpTarget(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by'>): boolean {
    const waitingOn = caseItem.waiting_on ?? 'none';
    const nextContactBy = normalizeFollowUpText(caseItem.next_contact_by);
    return waitingOn !== 'none' || !!nextContactBy;
}

function getLatestCaseContext(caseItem: Pick<TriageResult, 'case_notes' | 'case_activity'>): string {
    const latest = getLatestUpdateForDisplay(caseItem);
    return latest ?? '暂无备注或操作记录';
}

function getFollowUpSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by'>): string {
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

function getCaseTrackingSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by' | 'case_notes' | 'case_activity'>): string {
    if (hasSavedFollowUpTarget(caseItem)) {
        return getFollowUpSummary(caseItem);
    }
    return getLatestCaseContext(caseItem);
}

type FollowUpDueKind = 'overdue' | 'due_today' | 'due_tomorrow';

function getFollowUpDueTag(nextContactBy?: string): { color: string; label: string; kind: FollowUpDueKind } | null {
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
function getDueStateLabel(nextContactBy?: string): string {
    const tag = getFollowUpDueTag(nextContactBy);
    if (tag) return tag.label;
    const raw = normalizeFollowUpText(nextContactBy);
    if (raw) return `跟进：${raw}`;
    return '未设日期';
}

type AttentionKind =
    | 'done'
    | 'overdue'
    | 'due_today'
    | 'wait_broker'
    | 'urgent_manual'
    | 'manual_followup'
    | 'wait_external'
    | 'reviewing'
    | 'parked';

function getCaseAttentionState(
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
function getQueueReadinessLabel(caseItem: SavedCase): { label: string; color: string } {
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

/** Workbench Add-Car: mirror customer lifecycle so office sees the same “ready vs waiting” line. */
function getOfficeAddCarReadinessMirror(
    caseItem: TriageResult,
    ui: UiCopy,
): { headline: string; body: string; borderColor: string; background: string } | null {
    if (!triageResultLooksLikeAddCar(caseItem)) return null;
    const ls = caseItem.lifecycle_status;
    const still = caseItem.still_needed_fields?.filter(Boolean) ?? [];
    const missingShort = still
        .slice(0, 6)
        .map((f) => humanizeStructuredField(f))
        .join('、');
    const missingSuffix = still.length > 6 ? '…' : '';

    if (ls === 'handoff_pending') {
        return {
            headline: ui.office_readiness_handoff_pending_headline ?? '待客户正式提交',
            body: ui.office_readiness_handoff_pending_body ?? '',
            borderColor: '#faad14',
            background: 'rgba(250, 173, 20, 0.08)',
        };
    }
    if (ls === 'handed_off' || ls === 'office_followup') {
        const base = ui.office_readiness_submitted_body ?? '';
        const extra =
            still.length > 0
                ? ` 仍标缺项（报价前建议补齐）：${missingShort}${missingSuffix}`
                : '';
        return {
            headline: ui.office_readiness_submitted_headline ?? '已报送 · 可接手处理',
            body: `${base}${extra}`,
            borderColor: '#52c41a',
            background: '#f6ffed',
        };
    }
    const base = ui.office_readiness_collecting_body ?? '';
    const extra = still.length > 0 ? ` 当前还缺：${missingShort}${missingSuffix}` : ' 当前未标结构化缺项。';
    return {
        headline: ui.office_readiness_collecting_headline ?? '信息收集中',
        body: `${base}${extra}`,
        borderColor: '#1890ff',
        background: 'rgba(24, 144, 255, 0.06)',
    };
}

/** Office workbench detail: submission/received + bounded timestamps + process owner (parity with customer closure model). */
function OfficeWorkbenchAddCarSubmissionSnapshot({ triage, uiCopy }: { triage: TriageResult; uiCopy: UiCopy }) {
    if (!triageResultLooksLikeAddCar(triage)) return null;
    const u = uiCopy;
    const formal = addCarQueueStatusPhase(triage) === 'submitted';
    const lt = getOfficeLifecycleTag(triage.lifecycle_status);
    const created = formatPortalLocalDateTime(triage.created_at);
    const updated = formatPortalLocalDateTime(triage.updated_at);
    const title = u.office_workbench_submission_snapshot_title ?? '报送与送达';
    const qFormal = u.office_workbench_formal_to_office_question ?? '正式送达办公室';
    const yes = u.office_workbench_formal_to_office_yes ?? '是';
    const no = u.office_workbench_formal_to_office_no ?? '否';
    const stateLabel = u.office_workbench_current_handoff_state_label ?? '当前接手状态';
    const createdLabel = u.office_workbench_record_created_label ?? '记录创建';
    const updatedLabel = u.office_workbench_record_updated_label ?? '最近更新';
    const formalSubmittedLabel = u.office_workbench_formal_submitted_at_label ?? '正式送达办公室（首次）';
    const lastActivityLabel = u.office_workbench_last_activity_label ?? '最近活动（系统更新时间）';
    const processLabel = u.office_workbench_process_owner_label ?? '流程主要负责方';
    const proxyNote =
        u.office_workbench_submitted_proxy_note ??
        '时间说明：「正式送达」为首次进入办公室队列的时间（正式提交）；「最近活动」含后续追加、备注等写入。均为服务端 UTC 时间戳的本地显示。';
    const ls = (triage.lifecycle_status ?? '').trim();
    const formalAt = formatPortalLocalDateTime(triage.formal_submitted_at ?? triage.created_at);
    const timeLine = (() => {
        if (formal) {
            const parts: string[] = [];
            if (formalAt) parts.push(`${formalSubmittedLabel}：${formalAt}`);
            if (updated && (!formalAt || updated !== formalAt)) {
                parts.push(`${lastActivityLabel}：${updated}`);
            }
            if (parts.length) return parts.join(' · ');
            if (created) return `${createdLabel}：${created}`;
            return null;
        }
        if (created && updated && updated !== created) {
            return `${createdLabel}：${created} · ${updatedLabel}：${updated}`;
        }
        if (created) return `${createdLabel}：${created}`;
        if (updated) return `${updatedLabel}：${updated}`;
        return null;
    })();

    return (
        <div
            style={{
                marginBottom: 12,
                padding: 12,
                borderRadius: 8,
                border: '1px solid #e8e8e8',
                borderLeft: '4px solid #1677ff',
                background: '#fafcff',
            }}
        >
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
                {title}
            </Text>
            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
                    <Text style={{ fontSize: 13 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>{qFormal}：</Text>
                        <Tag color={formal ? 'success' : 'warning'} style={{ marginInlineStart: 6 }}>
                            {formal ? yes : no}
                        </Tag>
                        {lt ? (
                            <Text type="secondary" style={{ fontSize: 12, marginInlineStart: 8 }}>
                                {stateLabel}：{lt.label}
                            </Text>
                        ) : null}
                    </Text>
                </div>
                {ls === 'handoff_pending' && (
                    <Text style={{ fontSize: 12, color: '#ad6800', lineHeight: 1.55 }}>
                        {u.office_workbench_handoff_pending_office_note}
                    </Text>
                )}
                {ls === 'collecting' && (
                    <Text style={{ fontSize: 12, color: '#0958d9', lineHeight: 1.55 }}>
                        {u.office_workbench_collecting_office_note}
                    </Text>
                )}
                {!formal && !ls && (triage.case_id ?? '').toString().trim() && (
                    <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55 }}>
                        {u.office_workbench_intake_phase_office_note}
                    </Text>
                )}
                {timeLine ? (
                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                        {timeLine}
                    </Text>
                ) : null}
                {proxyNote ? (
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', lineHeight: 1.5 }}>
                        {proxyNote}
                    </Text>
                ) : null}
                <Text style={{ fontSize: 12, lineHeight: 1.55 }}>
                    <Text type="secondary">{processLabel}：</Text>
                    {addCarNextOwnerLine(triage)}
                </Text>
            </Space>
        </div>
    );
}

/** Compact flow-specific preview for queue cards — not full case card (office Chinese) */
function getCompactQueuePreview(caseItem: SavedCase): string {
    const collected = (caseItem.collected_fields ?? []).map(humanizeStructuredField);
    const stillNeeded = (caseItem.still_needed_fields ?? []).map(humanizeStructuredField);
    const focus = inferCaseFocusFromText(caseItem.source_text ?? '');
    const cat = caseItem.issue_category ?? '';

    if (focus === 'Add car quote' || /add.?car|加车|加一台|新车|报价/i.test((caseItem.source_text ?? '').toLowerCase())) {
        const formal = addCarQueueStatusPhase(caseItem) === 'submitted';
        const ls = caseItem.lifecycle_status;
        const phaseLead = formal
            ? '已正式送达 · '
            : ls === 'handoff_pending'
              ? '待客户正式提交 · '
              : '信息收集中 · ';
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
            return activityBit ? `${phaseLead}${core} · ${activityBit}` : `${phaseLead}${core}`;
        }
        return activityBit ? `${phaseLead}加车报价 · ${activityBit}` : `${phaseLead}加车报价`;
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

function getCaseWorkbenchScore(
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

function orderCasesForWorkbench<T extends SavedCase>(cases: T[]): T[] {
    return [...cases].sort((a, b) => {
        const scoreDiff = getCaseWorkbenchScore(b) - getCaseWorkbenchScore(a);
        if (scoreDiff !== 0) return scoreDiff;
        return (b.updated_at || '').localeCompare(a.updated_at || '');
    });
}

/** Customer-facing urgency note */
function getCustomerUrgencyNote(urgency: TriageResult['urgency']): string {
    if (urgency === 'critical') return 'This needs urgent attention.';
    if (urgency === 'high') return 'This needs attention soon.';
    if (urgency === 'medium') return 'We will review within 1–3 business days.';
    return 'No urgent action needed.';
}

/** Customer-facing follow-up note when broker will act */
function getCustomerFollowUpNote(manualFollowupNeeded: boolean): string {
    if (manualFollowupNeeded) {
        return "Chen Kui's office will review this and follow up with you.";
    }
    return 'No further action needed from our office at this time.';
}

/** Hybrid add-car intake: compose one first message from short structured fields (ADD_CAR_HYBRID_INTAKE). */
function composeAddCarStructuredIntakeMessage(fields: {
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

// =============================================================================
// CUSTOMER ENTRY TAB — Same-page conversational intake
// =============================================================================

type ConversationTurn = {
    role: 'customer' | 'system';
    content: string;
    triageResult?: TriageResult;
};

type CustomerEntryTabProps = {
    onSwitchToBroker: (caseId?: string) => void;
    onOpenScenarioSimulation?: () => void;
};

function CustomerEntryTab({ onSwitchToBroker, onOpenScenarioSimulation }: CustomerEntryTabProps) {
    const { uiCopy, clientId } = useClientConfig();
    const quickStartButtons = useMemo(
        () => (uiCopy.quick_start_buttons ? getQuickStartButtons(uiCopy) : DEFAULT_QUICK_START_BUTTONS),
        [uiCopy.quick_start_buttons],
    );
    const officeLabel = uiCopy.office_label ?? '办公室';
    const handoffDefault = uiCopy.handoff_default ?? '办公室会尽快处理，有结果会联系您。';
    const addCarHandoffToast = uiCopy.add_car_handoff_toast ?? handoffDefault;
    const welcomeHint = uiCopy.welcome_hint ?? '如需人工协助，点击「联系人工」即可，消息会直接转给办公室。';
    const portalHeroTitle = uiCopy.portal_hero_title ?? '加车报价 · 客户统一报送';
    const portalServiceTagline =
        uiCopy.portal_service_tagline ??
        '本入口以加车报价报送为主路径：系统按步骤整理要点并形成业务记录，由办公室核对与跟进；其他事项也可报送，完整度因场景而异。';
    const portalEmptyHeadline = uiCopy.portal_empty_headline ?? '建议从加车报价开始（当前试点最成熟路径）';
    const portalEmptySecondary = uiCopy.portal_empty_secondary ?? welcomeHint;
    const portalChoosePathLabel = uiCopy.portal_choose_path_label ?? '办理类型（点选后开始本条业务 · 加车为推荐主路径）';
    const portalThreadHeading = uiCopy.portal_thread_heading ?? '本条办理过程与办公室整理';
    const portalCustomerBubble = uiCopy.portal_customer_bubble_label ?? '您的报送';
    const portalOfficeBubble = uiCopy.portal_office_bubble_label ?? '办公室整理回复';
    const portalLoadingStatus = uiCopy.portal_loading_status ?? '办公室正在整理您的报送，请稍候…';
    const portalProgressNote = uiCopy.portal_progress_annotation ?? '状态随报送更新';
    const portalGenericProgressTitle = uiCopy.portal_generic_progress_title ?? '当前受理进度';
    const portalSubmitFollowup = uiCopy.portal_submit_followup ?? '提交补充';
    const portalFormalSubmittedAtLabel =
        uiCopy.portal_formal_submitted_at_label ?? '正式送达办公室（首次进入办公室队列）';
    const portalLastActivityAtLabel = uiCopy.portal_last_activity_at_label ?? '最近活动（系统更新时间）';
    const portalSubmittedAtPrimaryLabel = uiCopy.portal_submitted_at_primary_label ?? '办公室侧最近活动时间（系统更新时间）';
    const portalSubmittedAtCreatedPrefix = uiCopy.portal_submitted_at_created_prefix ?? '服务记录首次建立：';
    const portalSubmittedAtTimingTruthNote =
        uiCopy.portal_submitted_at_timing_truth_note ??
        '说明：「正式送达」时间为首次写入办公室可见服务记录的时刻；若您后续追加补充，只有「最近活动」时间会更新，正式送达时间不变。时间为 UTC 戳的本地显示。';
    const portalAddCarQuickTitle = uiCopy.portal_add_car_quick_title ?? '加车报价 · 结构化报送（可选）';
    const portalAddCarQuickHint =
        uiCopy.portal_add_car_quick_hint ??
        '填写几项可一次报送办公室，减少来回确认；也可只点上方办理类型，用一句话开始。';
    const portalAddCarQuickCta = uiCopy.portal_add_car_quick_cta ?? '用以上内容发起加车报送';
    const portalSessionRestored = uiCopy.portal_session_restored_toast ?? '已恢复未完成的报送';
    const portalClosureSummaryLabel = uiCopy.portal_closure_reply_summary_label ?? '办公室办理摘要';
    const portalPostHandoffThreadHeading =
        uiCopy.portal_post_handoff_thread_heading ?? '同条服务记录的报送留痕（备查）';
    const portalPostHandoffThreadHint =
        uiCopy.portal_post_handoff_thread_hint ??
        '主记录是下方受理结果卡与服务记录编号。报送气泡仅作过程备查，您无需把已提交内容再复述一遍。';
    const portalPostHandoffThreadCollapseLabel =
        uiCopy.portal_post_handoff_thread_collapse_label ?? '展开查看报送原文（可选）';
    const portalPostHandoffNextSectionLabel =
        uiCopy.portal_post_handoff_next_section_label ?? '下一步 · 办公室已接手本条记录';
    const portalPostHandoffClosureSectionLabel =
        uiCopy.portal_post_handoff_closure_section_label ?? '办公室对外说明（同条记录，非新聊天）';
    const portalInputEmpty =
        uiCopy.portal_input_placeholder_empty ??
        '非加车事项可在此说明或粘贴要点；办理加车更推荐点上方的「办理加车报价」或结构化字段。';
    const portalInputContinue =
        uiCopy.portal_input_placeholder_continue ?? '继续补充本条报送的要点，然后提交';
    const addCarStatusStripLabel = uiCopy.add_car_status_strip_label ?? '当前状态';
    const addCarResultEyebrow = uiCopy.add_car_result_card_eyebrow ?? '加车报价 · 受理结果卡';
    const addCarResultEyebrowHint =
        uiCopy.add_car_result_card_eyebrow_hint ?? '以下为业务工单式整理，非聊天流水。';
    const addCarCaseRecordLabel = uiCopy.add_car_case_record_id_label ?? '服务记录编号';
    const addCarBrokerNextHeading = uiCopy.add_car_broker_next_step_heading ?? '办公室侧下一步（接手本条记录）';
    const customerSubmitAddCarLabel = uiCopy.customer_entry_submit_add_car ?? '提交加车请求';
    const addCarBoundaryHint =
        uiCopy.add_car_boundary_hint ??
        '同一台车或同一条加车请求的补充、更正、补材料 → 用上方「追加到本条记录」。账单、理赔或与加车无关的新问题 → 点「提交新问题」另开一条，方便办公室分单处理。';
    const portalBrandTagline = uiCopy.portal_brand_tagline ?? '车险报送入口 · 加车报价为当前旗舰流程';
    const portalFlowTrackLabel = uiCopy.portal_flow_track_label ?? '办理进度';
    const portalAddCarFlowTrackLabel = uiCopy.portal_add_car_flow_track_label ?? portalFlowTrackLabel;
    const portalFlowStep1 = uiCopy.portal_flow_step_1 ?? '开始报送';
    const portalFlowStep2 = uiCopy.portal_flow_step_2 ?? '补齐关键信息';
    const portalFlowStep3 = uiCopy.portal_flow_step_3 ?? '办公室接手处理';
    const portalPreHandoffAddCarThreadCollapseLabel =
        uiCopy.portal_pre_handoff_add_car_thread_collapse_label ?? '展开查看报送对话（过程留痕，可选）';
    const officeGenericBrokerNextHeading =
        uiCopy.generic_broker_next_step_heading ?? '办公室侧下一步（系统整理）';
    const portalCustomerNextSuggestedHeading =
        uiCopy.portal_customer_next_suggested_heading ?? '您这边下一步（系统建议）';

    const [input, setInput] = useState('');
    const [turns, setTurns] = useState<ConversationTurn[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showExamples, setShowExamples] = useState(false);
    const [lastCaseId, setLastCaseId] = useState<string | undefined>();
    const [selectedButtonIntent, setSelectedButtonIntent] = useState<SoftRouteIntent | null>(null);
    /** Optional structured first turn for add-car (hybrid intake). */
    const [addCarQuickFields, setAddCarQuickFields] = useState({
        year: '',
        makeModel: '',
        zip: '',
        delivery: '',
        driver: '',
    });
    /** Post-handoff: optional append to same saved case (portal-style same-request lane). */
    const [postHandoffAppendKeys, setPostHandoffAppendKeys] = useState<string[]>([]);
    const [postHandoffAppendDraft, setPostHandoffAppendDraft] = useState('');
    const [postHandoffAppendSaving, setPostHandoffAppendSaving] = useState(false);
    const loadingPlaceholderRef = useRef<HTMLDivElement>(null);

    const lastSystemTurnForFlowStep = useMemo(
        () => [...turns].reverse().find((t) => t.role === 'system'),
        [turns],
    );
    const intakeFlowStep: 1 | 2 | 3 = useMemo(
        () => computeAddCarFlowStep(lastSystemTurnForFlowStep?.triageResult, turns.length > 0),
        [lastSystemTurnForFlowStep?.triageResult, turns.length],
    );
    /** Office has persisted service record — distinct from API `handoff_ready` (true while still `handoff_pending`). */
    const formalSubmissionComplete =
        turns.length > 0 &&
        turns[turns.length - 1]?.role === 'system' &&
        isFormalSubmissionToOfficeComplete(turns[turns.length - 1]?.triageResult);

    const primarySubmitLabel = useMemo(() => {
        const addCarLaneActive = customerEntryIsAddCarActive(turns, selectedButtonIntent);
        const lt = lastSystemTurnForFlowStep?.triageResult;
        if (turns.length === 0 && selectedButtonIntent === 'add_car') return customerSubmitAddCarLabel;
        if (addCarLaneActive && lt?.lifecycle_status === 'handoff_pending') {
            return uiCopy.portal_submit_handoff_pending ?? '正式提交办公室';
        }
        return portalSubmitFollowup;
    }, [turns, selectedButtonIntent, lastSystemTurnForFlowStep?.triageResult, customerSubmitAddCarLabel, uiCopy.portal_submit_handoff_pending, portalSubmitFollowup]);

    const inputPlaceholderResolved = useMemo(() => {
        if (turns.length === 0) return portalInputEmpty;
        const addCarLaneActive = customerEntryIsAddCarActive(turns, selectedButtonIntent);
        const lt = lastSystemTurnForFlowStep?.triageResult;
        if (addCarLaneActive && lt?.lifecycle_status === 'handoff_pending') {
            return (
                uiCopy.portal_input_placeholder_handoff_pending ??
                '可选：给办公室留一句备注（如提车日变更）；无需重复已整理要点。也可留空，直接点下方提交。'
            );
        }
        return portalInputContinue;
    }, [
        turns,
        selectedButtonIntent,
        lastSystemTurnForFlowStep?.triageResult,
        portalInputEmpty,
        portalInputContinue,
        uiCopy.portal_input_placeholder_handoff_pending,
    ]);

    const showHandoffPendingHint = useMemo(
        () =>
            customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
            lastSystemTurnForFlowStep?.triageResult?.lifecycle_status === 'handoff_pending',
        [turns, selectedButtonIntent, lastSystemTurnForFlowStep?.triageResult],
    );

    const portalHandoffPendingCtaHint =
        uiCopy.portal_handoff_pending_cta_hint ??
        '当前为「资料已齐 · 待正式提交」：下方按钮将把本条服务记录送达办公室，不是普通「继续补充」。若还要改要点，请先写在输入框再与提交一并送达。';

    /** In-progress persistence: restore conversation on mount when session_id exists */
    useEffect(() => {
        const sid = getSessionId();
        if (!sid) return;
        getInProgressSession(sid).then((data) => {
            if (!data?.turns?.length) return;
            const restored: ConversationTurn[] = data.turns.map((t) => ({
                role: t.role as 'customer' | 'system',
                content: t.text,
                triageResult: t.triageResult,
            }));
            setTurns(restored);
            message.success(portalSessionRestored, 2);
        });
    }, []);

    useEffect(() => {
        if (loading && loadingPlaceholderRef.current) {
            loadingPlaceholderRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }, [loading]);

    /** Submit with explicit message and optional soft route. Used for both manual submit and button-starter flow. */
    const submitMessage = async (messageText: string, softRoute?: SoftRouteIntent) => {
        const trimmed = messageText.trim();
        if (!trimmed) {
            setError('请输入您的问题。');
            return;
        }
        setError(null);
        setLoading(true);

        const customerTurn: ConversationTurn = { role: 'customer', content: trimmed };
        setTurns((prev) => [...prev, customerTurn]);
        setInput('');

        const conversationTurnsForApi = turns
            .filter((t) => t.role === 'customer' || t.role === 'system')
            .map((t) => ({
                role: t.role as 'customer' | 'system',
                text: t.content,
            }));

        try {
            const addCarLaneActive = customerEntryIsAddCarActive(turns, selectedButtonIntent);
            const ltFormal = lastSystemTurnForFlowStep?.triageResult;
            const formalSubmit =
                addCarLaneActive && ltFormal?.lifecycle_status === 'handoff_pending';
            const data = await triageMessage(
                trimmed,
                true,
                conversationTurnsForApi,
                softRoute ?? undefined,
                undefined,
                clientId,
                formalSubmit,
                lastCaseId,
            );
            // Rerouting: clear button selection when text overrode it; show acknowledgment
            if (data.reroute_occurred) {
                setSelectedButtonIntent(null);
            }
            const replyContent =
                data.reroute_occurred && data.reroute_message
                    ? `${data.reroute_message}\n\n${data.client_reply_draft}`
                    : data.client_reply_draft;
            const systemTurn: ConversationTurn = {
                role: 'system',
                content: replyContent,
                triageResult: data,
            };
            setTurns((prev) => [...prev, systemTurn]);
            const addCarFlow = triageResultLooksLikeAddCar(data);
            if (data.case_id) {
                setLastCaseId(data.case_id);
                clearSessionId(); // Phase 2: new session for next conversation
                message.success(addCarFlow ? addCarHandoffToast : `已整理成 case。${handoffDefault}`);
            } else if (data.handoff_ready) {
                const suppressReadyToast =
                    addCarFlow && data.lifecycle_status === 'handoff_pending';
                if (!suppressReadyToast) {
                    message.success(addCarFlow ? addCarHandoffToast : handoffDefault);
                }
            }
        } catch (e: unknown) {
            setTurns((prev) => prev.slice(0, -1));
            setInput(trimmed);
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? '出错了，请稍后再试。';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = () => {
        const addCarLaneActive = customerEntryIsAddCarActive(turns, selectedButtonIntent);
        const lt = lastSystemTurnForFlowStep?.triageResult;
        const handoffPendingHere =
            addCarLaneActive && lt?.lifecycle_status === 'handoff_pending';
        const trimmed = input.trim();
        const emptyFormalLine =
            uiCopy.portal_handoff_pending_empty_submit_line?.trim() ||
            '【正式提交办公室】请按系统已整理要点将本条加车记录交办公室处理；暂无额外备注。';
        const messageText = trimmed || (handoffPendingHere ? emptyFormalLine : '');
        if (!messageText.trim()) {
            setError('请输入您的问题。');
            return;
        }
        submitMessage(messageText, selectedButtonIntent ?? undefined);
    };

    /** Button-starter: when user clicks a quick-start button with empty input, begin the flow immediately. */
    const handleButtonStarter = (btn: (typeof quickStartButtons)[0]) => {
        if (input.trim()) {
            // User has typed; just set intent, they will click Submit
            setSelectedButtonIntent(prev => (prev === btn.id ? null : btn.id));
            return;
        }
        // Empty input: proactively begin the flow with starter message
        setSelectedButtonIntent(btn.id);
        submitMessage(btn.starterMessage, btn.id);
    };

    const handleExampleFill = (text: string) => {
        setInput(text);
        setError(null);
    };

    const handleNewConversation = () => {
        setTurns([]);
        setInput('');
        setLastCaseId(undefined);
        setError(null);
        setSelectedButtonIntent(null);
        setAddCarQuickFields({ year: '', makeModel: '', zip: '', delivery: '', driver: '' });
        setPostHandoffAppendKeys([]);
        setPostHandoffAppendDraft('');
        clearSessionId(); // Phase 2: fresh session for new conversation
    };

    const handlePostHandoffAppendSameCase = async () => {
        const tid = lastCaseId;
        const text = postHandoffAppendDraft.trim();
        if (!tid) {
            message.error('尚未生成服务记录，无法追加。');
            return;
        }
        if (!text) {
            message.warning('请输入要补充的内容');
            return;
        }
        setPostHandoffAppendSaving(true);
        setError(null);
        try {
            const updated = await appendFollowUpMessage(tid, text, clientId);
            const sysReply = (updated.client_reply_draft || '').trim() || handoffDefault;
            setTurns((prev) => [
                ...prev,
                { role: 'customer', content: text },
                { role: 'system', content: sysReply, triageResult: updated as TriageResult },
            ]);
            setPostHandoffAppendDraft('');
            if (updated.case_boundary === 'new_issue') {
                message.warning('已追加。系统判断这可能属于另一件事——以后请优先点击「提交新问题」单独发送。');
            } else if (updated.case_boundary === 'borderline') {
                message.info('已追加。办公室可能需要确认是否仍属同一条加车请求。');
            } else {
                message.success('已追加到您的服务记录');
            }
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? '追加失败，请稍后再试。';
            setError(msg);
            message.error(msg);
        } finally {
            setPostHandoffAppendSaving(false);
        }
    };

    const handleStartWithAddCarStructured = () => {
        const composed = composeAddCarStructuredIntakeMessage(addCarQuickFields);
        if (!composed) {
            setError('请至少填写一项加车信息（年份、车型、邮编、提车或驾驶人）。');
            return;
        }
        setError(null);
        setSelectedButtonIntent('add_car');
        submitMessage(composed, 'add_car');
    };

    const cardStyle: React.CSSProperties = {
        background: '#fff',
        border: '1px solid #e8e8e8',
        borderRadius: 10,
        boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
    };

    return (
        <div style={{ width: '100%', padding: '0 0 28px', boxSizing: 'border-box' }}>
            <div
                style={{
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: 12,
                    boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
                    /* Match top chrome strip horizontal rhythm (统一服务入口 card uses 18px). */
                    padding: '26px 18px 30px',
                }}
            >
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
                {/* Layer 1 — Trust / Hero: full when empty; compact when session active (fewer competing surfaces) */}
                {turns.length === 0 ? (
                    <Card size="small" style={{ ...cardStyle, background: '#fafafa', borderColor: '#f0f0f0' }}>
                        <Space direction="vertical" size={12} style={{ width: '100%' }}>
                            <Title level={2} style={{ margin: 0, fontWeight: 600, color: '#262626', fontSize: 24 }}>
                                <CustomerServiceOutlined style={{ marginRight: 8, color: '#1677ff' }} />
                                {portalHeroTitle}
                            </Title>
                            <Paragraph style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: '#595959' }}>
                                {portalServiceTagline}
                            </Paragraph>
                            {onOpenScenarioSimulation && (
                                <Button
                                    icon={<PlayCircleOutlined />}
                                    onClick={() => onOpenScenarioSimulation()}
                                    size="small"
                                    type="text"
                                    style={{ color: '#8c8c8c', fontSize: 12, padding: 0, height: 'auto' }}
                                >
                                    {uiCopy.portal_tab_simulation_label ?? '场景仿真'}
                                </Button>
                            )}
                        </Space>
                    </Card>
                ) : (
                    <Card size="small" style={{ ...cardStyle, background: '#fafafa', borderColor: '#f0f0f0' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                            <Space align="start" size={10}>
                                <CustomerServiceOutlined style={{ fontSize: 20, color: '#1677ff', marginTop: 2 }} />
                                <div style={{ minWidth: 0 }}>
                                    <Text strong style={{ fontSize: 16, color: '#262626', display: 'block' }}>
                                        {portalHeroTitle}
                                    </Text>
                                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4, lineHeight: 1.5 }}>
                                        {portalBrandTagline}
                                    </Text>
                                </div>
                            </Space>
                            {onOpenScenarioSimulation && (
                                <Button
                                    icon={<PlayCircleOutlined />}
                                    onClick={() => onOpenScenarioSimulation()}
                                    size="small"
                                    type="text"
                                    style={{ color: '#8c8c8c', fontSize: 12, padding: 0, height: 'auto', flexShrink: 0 }}
                                >
                                    {uiCopy.portal_tab_simulation_label ?? '场景仿真'}
                                </Button>
                            )}
                        </div>
                    </Card>
                )}

                <IntakeFlowStepTrack
                    flowStep={intakeFlowStep}
                    trackLabel={
                        selectedButtonIntent === 'add_car' ||
                        (turns.length > 0 && customerEntryIsAddCarActive(turns, selectedButtonIntent))
                            ? portalAddCarFlowTrackLabel
                            : portalFlowTrackLabel
                    }
                    step1={portalFlowStep1}
                    step2={portalFlowStep2}
                    step3={portalFlowStep3}
                />

                {turns.length > 0 &&
                    customerEntryIsAddCarActive(turns, selectedButtonIntent) && (
                        <Card
                            size="small"
                            style={{
                                ...cardStyle,
                                background: 'linear-gradient(90deg, #e6f4ff 0%, #f0f7ff 100%)',
                                borderColor: '#91caff',
                            }}
                        >
                            <Space direction="vertical" size={4} style={{ width: '100%' }}>
                                <Text strong style={{ fontSize: 15, color: '#0958d9' }}>
                                    {uiCopy.add_car_transaction_title ?? '当前办理：加车报价'}
                                </Text>
                                <Text type="secondary" style={{ fontSize: 13, lineHeight: 1.55 }}>
                                    {uiCopy.add_car_transaction_subtitle ??
                                        '这是正式的加车报价请求流程：我们会按业务步骤收齐资料，并提交办公室出价与跟进。'}
                                </Text>
                            </Space>
                        </Card>
                    )}

                {/* Layer 2 — Primary entry actions (when empty state) */}
                {turns.length === 0 && (
                    <Card size="small" style={cardStyle}>
                        <Space direction="vertical" size={20} style={{ width: '100%' }}>
                            <div>
                                <Text strong style={{ fontSize: 18, display: 'block', marginBottom: 8, color: '#262626' }}>
                                    {portalEmptyHeadline}
                                </Text>
                                <Text style={{ fontSize: 14, lineHeight: 1.6, color: '#8c8c8c' }}>
                                    {portalEmptySecondary}
                                </Text>
                            </div>
                            <div>
                                <Text style={{ fontSize: 13, display: 'block', marginBottom: 12, color: '#595959', fontWeight: 500 }}>
                                    {portalChoosePathLabel}
                                </Text>
                                <Row gutter={[12, 12]}>
                                    {quickStartButtons.map((btn) => {
                                        const primary =
                                            selectedButtonIntent === btn.id ||
                                            (selectedButtonIntent === null && btn.id === 'add_car');
                                        return (
                                        <Col xs={24} sm={12} md={8} key={btn.id}>
                                            <Button
                                                type={primary ? 'primary' : 'default'}
                                                onClick={() => handleButtonStarter(btn)}
                                                loading={loading}
                                                size="large"
                                                block
                                                style={
                                                    primary
                                                        ? { backgroundColor: '#1677ff', borderColor: '#1677ff' }
                                                        : { borderColor: '#d9d9d9', color: '#262626', background: '#fff' }
                                                }
                                            >
                                                <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
                                                    {btn.label}
                                                    {btn.id === 'add_car' && selectedButtonIntent === null ? (
                                                        <Tag color="processing" style={{ margin: 0, fontSize: 11 }}>
                                                            {uiCopy.portal_add_car_button_badge ?? '推荐主路径'}
                                                        </Tag>
                                                    ) : null}
                                                </span>
                                            </Button>
                                        </Col>
                                        );
                                    })}
                                </Row>
                            </div>
                            {/* Hybrid add-car: structured short card + same conversational pipeline (flagship hardening) */}
                            <div
                                style={{
                                    marginTop: 8,
                                    paddingTop: 16,
                                    borderTop: '1px solid #f0f0f0',
                                }}
                            >
                                <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 4, color: '#262626' }}>
                                    {portalAddCarQuickTitle}
                                </Text>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 12 }}>
                                    {portalAddCarQuickHint}
                                </Text>
                                <Row gutter={[10, 10]}>
                                    <Col xs={24} sm={12}>
                                        <Input
                                            placeholder="年份，如 2024"
                                            value={addCarQuickFields.year}
                                            onChange={(e) => setAddCarQuickFields((p) => ({ ...p, year: e.target.value }))}
                                            disabled={loading}
                                        />
                                    </Col>
                                    <Col xs={24} sm={12}>
                                        <Input
                                            placeholder="车型，如 Tesla Model Y"
                                            value={addCarQuickFields.makeModel}
                                            onChange={(e) => setAddCarQuickFields((p) => ({ ...p, makeModel: e.target.value }))}
                                            disabled={loading}
                                        />
                                    </Col>
                                    <Col xs={24} sm={12}>
                                        <Input
                                            placeholder="邮编 ZIP"
                                            value={addCarQuickFields.zip}
                                            onChange={(e) => setAddCarQuickFields((p) => ({ ...p, zip: e.target.value }))}
                                            disabled={loading}
                                        />
                                    </Col>
                                    <Col xs={24} sm={12}>
                                        <Input
                                            placeholder="提车 / 预计拿车"
                                            value={addCarQuickFields.delivery}
                                            onChange={(e) => setAddCarQuickFields((p) => ({ ...p, delivery: e.target.value }))}
                                            disabled={loading}
                                        />
                                    </Col>
                                    <Col xs={24}>
                                        <Input
                                            placeholder="主要驾驶人（姓名或关系，如：本人 / 配偶）"
                                            value={addCarQuickFields.driver}
                                            onChange={(e) => setAddCarQuickFields((p) => ({ ...p, driver: e.target.value }))}
                                            disabled={loading}
                                        />
                                    </Col>
                                </Row>
                                <Button
                                    type="primary"
                                    style={{ marginTop: 12 }}
                                    onClick={handleStartWithAddCarStructured}
                                    loading={loading}
                                    disabled={loading}
                                >
                                    {portalAddCarQuickCta}
                                </Button>
                            </div>
                        </Space>
                    </Card>
                )}

                {turns.length > 0 && (() => {
                    const lastSystemTurn = [...turns].reverse().find((t) => t.role === 'system');
                    const latestTriage = lastSystemTurn?.triageResult;
                    const addCarActiveHere = customerEntryIsAddCarActive(turns, selectedButtonIntent);
                    const submitLabelForNextLane =
                        turns.length === 0 && selectedButtonIntent === 'add_car'
                            ? customerSubmitAddCarLabel
                            : addCarActiveHere && latestTriage?.lifecycle_status === 'handoff_pending'
                              ? (uiCopy.portal_submit_handoff_pending ?? '正式提交办公室')
                              : portalSubmitFollowup;
                    const systemTurnsWithTriage = turns.filter((t) => t.role === 'system' && t.triageResult);
                    const priorSystemTriage =
                        systemTurnsWithTriage.length >= 2
                            ? systemTurnsWithTriage[systemTurnsWithTriage.length - 2].triageResult
                            : undefined;
                    const threadSpace = (
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            {turns.map((turn, idx) => (
                                <div
                                    key={idx}
                                    style={{
                                        display: 'flex',
                                        justifyContent: turn.role === 'customer' ? 'flex-end' : 'flex-start',
                                        width: '100%',
                                    }}
                                >
                                    <div
                                        style={{
                                            maxWidth: '85%',
                                            padding: 10,
                                            borderRadius: 6,
                                            background: turn.role === 'customer' ? 'rgba(24, 144, 255, 0.15)' : 'rgba(82, 196, 26, 0.12)',
                                            borderLeft: turn.role === 'system' ? '3px solid #52c41a' : undefined,
                                            borderRight: turn.role === 'customer' ? '3px solid #1890ff' : undefined,
                                            lineHeight: 1.45,
                                        }}
                                    >
                                        <Text strong style={{ fontSize: 11, color: '#8c8c8c', display: 'block', marginBottom: 2 }}>
                                            {turn.role === 'customer' ? portalCustomerBubble : portalOfficeBubble}
                                        </Text>
                                        <Text style={{ fontSize: 14, whiteSpace: 'pre-wrap', lineHeight: 1.45 }}>{turn.content}</Text>
                                        {turn.role === 'system' && turn.triageResult && (
                                            <Space size={4} wrap style={{ marginTop: 6 }}>
                                                {(turn.triageResult.urgency === 'critical' || turn.triageResult.urgency === 'high') && (
                                                    <Tag color="orange" icon={<ClockCircleOutlined />} style={{ fontSize: 11 }}>
                                                        {getCustomerUrgencyNote(turn.triageResult.urgency)}
                                                    </Tag>
                                                )}
                                                {turn.triageResult.collection_stage && (
                                                    <Tag
                                                        color={turn.triageResult.collection_stage === 'enough_for_handoff' ? 'green' : 'default'}
                                                        style={{ fontSize: 11 }}
                                                    >
                                                        {turn.triageResult.collection_stage === 'enough_for_handoff'
                                                            ? '可交办公室'
                                                            : '信息收集中'}
                                                    </Tag>
                                                )}
                                                {turn.triageResult.follow_up_type && turn.triageResult.follow_up_type !== 'new_info' && (
                                                    <Tag color="blue" style={{ fontSize: 11 }}>
                                                        跟进：{turn.triageResult.follow_up_type === 'correction' ? '客户更正' : turn.triageResult.follow_up_type === 'already_sent' ? '称已发送' : turn.triageResult.follow_up_type}
                                                    </Tag>
                                                )}
                                                {turn.triageResult.human_confirmation_required && (
                                                    <Tag color="gold" style={{ fontSize: 11 }}>
                                                        需办公室核对要点
                                                    </Tag>
                                                )}
                                            </Space>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div ref={loadingPlaceholderRef} style={{ display: 'flex', justifyContent: 'flex-start', width: '100%' }}>
                                    <div
                                        style={{
                                            maxWidth: '85%',
                                            padding: 10,
                                            borderRadius: 6,
                                            background: 'rgba(82, 196, 26, 0.12)',
                                            borderLeft: '3px solid #52c41a',
                                            lineHeight: 1.45,
                                        }}
                                    >
                                        <Text strong style={{ fontSize: 11, color: '#8c8c8c', display: 'block', marginBottom: 2 }}>
                                            {portalOfficeBubble}
                                        </Text>
                                        <Space size={8}>
                                            <Spin size="small" />
                                            <Text type="secondary" style={{ fontSize: 14 }}>{portalLoadingStatus}</Text>
                                        </Space>
                                    </div>
                                </div>
                            )}
                        </Space>
                    );
                    const threadCard = (
                        <Card size="small" style={{ ...cardStyle, maxHeight: 360, overflowY: 'auto' }}>
                            {threadSpace}
                        </Card>
                    );
                    /** Add-Car pre-handoff: progress/state above thread so the task record reads before chat bubbles (broker-first scan). */
                    const preHandoffProgressCard =
                        latestTriage && !formalSubmissionComplete ? (
                        <Card
                            size="small"
                            title={
                                <Space size={4}>
                                    <InboxOutlined />
                                    <span>
                                        {addCarActiveHere
                                            ? (uiCopy.add_car_progress_card_title ?? '加车报价 · 进度')
                                            : portalGenericProgressTitle}
                                    </span>
                                    <Text type="secondary" style={{ fontSize: 10, fontWeight: 400 }}>（{portalProgressNote}）</Text>
                                </Space>
                            }
                            style={{ ...cardStyle, background: '#fafafa', borderColor: '#f0f0f0' }}
                        >
                            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                {addCarActiveHere && latestTriage && (
                                    <AddCarCaseStatusStrip
                                        triage={latestTriage}
                                        phase="intake"
                                        caption={addCarStatusStripLabel}
                                    />
                                )}
                                {addCarActiveHere && lastCaseId && (
                                    <Text
                                        type="secondary"
                                        style={{ fontSize: 12, display: 'block', fontFamily: 'monospace' }}
                                        copyable={{ text: lastCaseId }}
                                    >
                                        {addCarCaseRecordLabel}：{lastCaseId}
                                    </Text>
                                )}
                                {addCarActiveHere && latestTriage && turns.some((t) => t.role === 'system') && (
                                    <AddCarRecordSummaryRail
                                        triage={latestTriage}
                                        priorSystemTriage={priorSystemTriage}
                                        uiCopy={uiCopy}
                                        mode="portal_pre"
                                        flowStep={intakeFlowStep}
                                        submitLabel={submitLabelForNextLane}
                                    />
                                )}
                                {!addCarActiveHere && latestTriage && (
                                    <GenericIntakeStatusStrip triage={latestTriage} caption={addCarStatusStripLabel} />
                                )}
                                <div>
                                    <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                                        当前请求与类型
                                    </Text>
                                    {latestTriage?.issue_category && (
                                        <div style={{ marginBottom: 6 }}>
                                            <Tag color="blue">{humanizeCategory(latestTriage.issue_category, latestTriage.source_text)}</Tag>
                                        </div>
                                    )}
                                    {latestTriage?.quote_ready_status && !addCarActiveHere && (
                                        <div>
                                            <Text type="secondary" style={{ fontSize: 11 }}>整理度 / 报价准备：</Text>{' '}
                                            <Tag color={QUOTE_READY_STATUS_LABELS[latestTriage.quote_ready_status]?.color ?? 'default'}>
                                                {QUOTE_READY_STATUS_LABELS[latestTriage.quote_ready_status]?.label ?? latestTriage.quote_ready_status}
                                            </Tag>
                                        </div>
                                    )}
                                </div>
                                <Divider style={{ margin: '4px 0' }} />
                                {!addCarActiveHere && (latestTriage?.collected_fields?.length ?? 0) > 0 && (
                                    <div>
                                        <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                                            已记录要点
                                        </Text>
                                        <Space size={4} wrap>
                                            {latestTriage!.collected_fields!.slice(0, 6).map((f) => (
                                                <Tag key={f} color="green">
                                                    {humanizeStructuredFieldForCustomer(f)}
                                                </Tag>
                                            ))}
                                        </Space>
                                    </div>
                                )}
                                {!addCarActiveHere && (latestTriage?.still_needed_fields?.length ?? 0) > 0 && (
                                    <div>
                                        <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                                            仍缺 / 待补充
                                        </Text>
                                        <Space size={4} wrap>
                                            {latestTriage!.still_needed_fields!.slice(0, 4).map((f) => (
                                                <Tag key={f} color="orange">
                                                    {humanizeStructuredFieldForCustomer(f)}
                                                </Tag>
                                            ))}
                                        </Space>
                                    </div>
                                )}
                                {latestTriage?.next_best_question && (
                                    <div>
                                        <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                                            {portalCustomerNextSuggestedHeading}
                                        </Text>
                                        <Text style={{ fontSize: 12, display: 'block', lineHeight: 1.55 }}>
                                            {latestTriage.next_best_question.slice(0, 120)}
                                            {(latestTriage.next_best_question?.length ?? 0) > 120 ? '…' : ''}
                                        </Text>
                                    </div>
                                )}
                                {latestTriage?.lifecycle_status && !addCarActiveHere && (() => {
                                    const lc = LIFECYCLE_STATUS_LABELS[latestTriage.lifecycle_status!];
                                    return (
                                        <Tag
                                            color={
                                                latestTriage.lifecycle_status === 'handoff_pending'
                                                    ? 'green'
                                                    : (lc?.color ?? 'default')
                                            }
                                            style={{ fontSize: 10 }}
                                        >
                                            {lc?.label ?? latestTriage.lifecycle_status}
                                        </Tag>
                                    );
                                })()}
                            </Space>
                        </Card>
                    ) : null;

                    const threadBlock = (
                        <>
                <div>
                    <Text strong style={{ fontSize: 14, color: '#262626', display: 'block', marginBottom: formalSubmissionComplete ? 4 : 8 }}>
                        {formalSubmissionComplete ? portalPostHandoffThreadHeading : portalThreadHeading}
                    </Text>
                    {formalSubmissionComplete && (
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8, lineHeight: 1.5 }}>
                            {portalPostHandoffThreadHint}
                        </Text>
                    )}
                </div>
                {formalSubmissionComplete ? (
                    <Collapse
                        bordered={false}
                        style={{ background: 'transparent' }}
                        defaultActiveKey={[]}
                        items={[
                            {
                                key: 'full_thread',
                                label: <Text style={{ fontSize: 13 }}>{portalPostHandoffThreadCollapseLabel}</Text>,
                                children: threadCard,
                            },
                        ]}
                    />
                ) : addCarActiveHere && turns.length > 0 ? (
                    <Collapse
                        bordered={false}
                        style={{ background: 'transparent' }}
                        defaultActiveKey={[]}
                        items={[
                            {
                                key: 'pre_handoff_add_car_thread',
                                label: <Text style={{ fontSize: 13 }}>{portalPreHandoffAddCarThreadCollapseLabel}</Text>,
                                children: threadCard,
                            },
                        ]}
                    />
                ) : (
                    threadCard
                )}
                        </>
                    );

                    return (
                        <>
                {addCarActiveHere && preHandoffProgressCard}
                {threadBlock}
                {!addCarActiveHere && preHandoffProgressCard}
                        </>
                    );
                })()}

                {!formalSubmissionComplete && (
                    <Card size="small" style={cardStyle}>
                        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                            {turns.length > 0 &&
                                customerEntryIsAddCarActive(turns, selectedButtonIntent) && (
                                <Space size={4} wrap>
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        当前办理：
                                    </Text>
                                    <Tag
                                        color="blue"
                                        closable={!!selectedButtonIntent}
                                        onClose={() => setSelectedButtonIntent(null)}
                                        style={{ fontSize: 12 }}
                                    >
                                        加车报价
                                    </Tag>
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                        （与本次加车无关的其他问题，完成后请用「提交新问题」）
                                    </Text>
                                </Space>
                            )}
                            {turns.length > 0 &&
                                !customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
                                selectedButtonIntent && (
                                <Space size={4}>
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        当前主题：
                                    </Text>
                                    <Tag
                                        color="blue"
                                        closable
                                        onClose={() => setSelectedButtonIntent(null)}
                                        style={{ fontSize: 12 }}
                                    >
                                        {quickStartButtons.find((b) => b.id === selectedButtonIntent)?.label ?? selectedButtonIntent}
                                    </Tag>
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                        （可点击 × 取消，直接输入会覆盖）
                                    </Text>
                                </Space>
                            )}
                            {turns.length === 0 && (
                                <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                                    可先点选办理类型，或直接在此完成报送；提交后办公室将按记录跟进。
                                </Text>
                            )}
                            {showHandoffPendingHint && (
                                <Alert
                                    type="warning"
                                    showIcon
                                    message={uiCopy.portal_handoff_pending_alert_title ?? '资料已齐 · 待正式送达办公室'}
                                    description={
                                        <Text style={{ fontSize: 13, lineHeight: 1.55, margin: 0 }}>
                                            {portalHandoffPendingCtaHint}
                                        </Text>
                                    }
                                />
                            )}
                            <TextArea
                                placeholder={inputPlaceholderResolved}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                rows={turns.length > 0 ? 3 : 4}
                                disabled={loading}
                                style={{ fontSize: 15 }}
                            />
                            <Button
                                type="primary"
                                size="large"
                                icon={<SendOutlined />}
                                onClick={handleSubmit}
                                loading={loading}
                                block
                            >
                                {turns.length === 0
                                    ? selectedButtonIntent === 'add_car'
                                        ? (uiCopy.customer_entry_submit_add_car ?? '提交加车请求')
                                        : '提交报送'
                                    : primarySubmitLabel}
                            </Button>
                            {showHandoffPendingHint && (
                                <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block' }}>
                                    {uiCopy.portal_handoff_pending_button_subline ??
                                        '点按后本条服务记录视为正式送达办公室排队处理；之后仍可在同一条记录下追加补充，不等于已报价或核保完成。'}
                                </Text>
                            )}
                            <Button type="text" size="small" onClick={() => setShowExamples((v) => !v)}>
                                {showExamples ? '收起示例' : '不确定如何描述？查看示例'}
                            </Button>
                            {showExamples && (
                                <Card size="small" style={{ ...cardStyle, background: '#fafafa', borderColor: '#f0f0f0' }}>
                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                        {CUSTOMER_ENTRY_EXAMPLES.map((ex) => (
                                            <Button
                                                key={ex.label}
                                                size="small"
                                                type="link"
                                                onClick={() => handleExampleFill(ex.text)}
                                            >
                                                {ex.label}
                                            </Button>
                                        ))}
                                    </Space>
                                </Card>
                            )}
                        </Space>
                    </Card>
                )}

                {formalSubmissionComplete && (() => {
                    const lastTurn = turns[turns.length - 1];
                    const triage = lastTurn?.role === 'system' ? lastTurn.triageResult : null;
                    const systemTurnsHandoff = turns.filter((t) => t.role === 'system' && t.triageResult);
                    const priorHandoffTriage =
                        systemTurnsHandoff.length >= 2
                            ? systemTurnsHandoff[systemTurnsHandoff.length - 2].triageResult
                            : undefined;
                    const caseFocus = triage
                        ? (inferCaseFocusFromStructuredFields(triage.collected_fields, triage.still_needed_fields, triage.issue_category)
                            ?? inferCaseFocusFromText(triage.source_text ?? ''))
                        : null;
                    const oneLiner = triage ? getCaseReportOneLiner(triage, turns.find((t) => t.role === 'customer')?.content ?? '') : '';
                    const addCarHandoff =
                        selectedButtonIntent === 'add_car' || triageResultLooksLikeAddCar(triage ?? undefined);
                    const closureHeadline = addCarHandoff
                        ? (uiCopy.handoff_closure_headline_add_car ?? '本加车报价请求已提交办公室处理')
                        : (uiCopy.handoff_closure_headline_generic ?? '本请求已整理并提交办公室');
                    const processingLine = addCarHandoff
                        ? (uiCopy.handoff_closure_processing_add_car ??
                            '办公室正在继续处理本次加车报价；您无需重复提交相同资料，有进展会联系您。')
                        : null;
                    const caseFollowLine = lastCaseId
                        ? (uiCopy.handoff_case_created_line ?? `已生成服务记录，${officeLabel}会按流程跟进本次请求。`)
                        : (uiCopy.handoff_case_pending_line ?? `如有需要，${officeLabel}会主动联系您。`);
                    const boundaryHint =
                        uiCopy.handoff_new_issue_hint ??
                        '若您还有其他与本次无关的问题，请点「提交新问题」开启新的请求，以免对话混在一起。';
                    const clientPrepTrimmed = (triage?.client_prep ?? '').trim();
                    const showAddCarStructuredPanel =
                        addCarHandoff &&
                        triage &&
                        ((triage.collected_fields?.length ?? 0) > 0 ||
                            (triage.still_needed_fields?.length ?? 0) > 0 ||
                            !!triage.quote_ready_status);
                    return (
                        <Card
                            size="small"
                            style={{
                                borderLeft: '4px solid #52c41a',
                                background: '#f6ffed',
                                border: '1px solid #b7eb8f',
                                borderRadius: 10,
                            }}
                        >
                            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                {addCarHandoff && triage && (
                                    <AddCarFlowExplanation
                                        uiCopy={uiCopy}
                                        variant="post_handoff"
                                        stillNeededLabels={(triage.still_needed_fields ?? []).map((f) =>
                                            humanizeStructuredFieldForCustomer(f),
                                        )}
                                    />
                                )}
                                <div>
                                    {addCarHandoff && triage && (
                                        <AddCarCaseStatusStrip
                                            triage={triage}
                                            phase="submitted"
                                            caption={addCarStatusStripLabel}
                                        />
                                    )}
                                    {!addCarHandoff && triage && (
                                        <GenericIntakeStatusStrip triage={triage} caption={addCarStatusStripLabel} />
                                    )}
                                    {lastCaseId && (
                                        <Text
                                            type="secondary"
                                            style={{ fontSize: 12, display: 'block', marginBottom: 10, fontFamily: 'monospace' }}
                                            copyable={{ text: lastCaseId }}
                                        >
                                            {addCarCaseRecordLabel}：{lastCaseId}
                                        </Text>
                                    )}
                                    {(() => {
                                        const formalTs = formatPortalLocalDateTime(
                                            triage?.formal_submitted_at ?? triage?.created_at,
                                        );
                                        const activityTs = formatPortalLocalDateTime(triage?.updated_at);
                                        const hasCase = Boolean((triage?.case_id ?? '').toString().trim());
                                        if (!formalTs && !activityTs) return null;
                                        const showActivityLine =
                                            hasCase &&
                                            Boolean(formalTs && activityTs && activityTs !== formalTs);
                                        const showFormalOnlyPersisted =
                                            hasCase && Boolean(formalTs) && !showActivityLine;
                                        return (
                                            <div style={{ marginBottom: 10 }}>
                                                {showActivityLine ? (
                                                    <>
                                                        <Text
                                                            type="secondary"
                                                            style={{ fontSize: 12, display: 'block', lineHeight: 1.5 }}
                                                        >
                                                            {portalFormalSubmittedAtLabel}：{formalTs}
                                                        </Text>
                                                        <Text
                                                            type="secondary"
                                                            style={{ fontSize: 12, display: 'block', lineHeight: 1.5, marginTop: 4 }}
                                                        >
                                                            {portalLastActivityAtLabel}：{activityTs}
                                                        </Text>
                                                    </>
                                                ) : showFormalOnlyPersisted ? (
                                                    <Text
                                                        type="secondary"
                                                        style={{ fontSize: 12, display: 'block', lineHeight: 1.5 }}
                                                    >
                                                        {portalFormalSubmittedAtLabel}：{formalTs}
                                                    </Text>
                                                ) : (
                                                    <>
                                                        <Text
                                                            type="secondary"
                                                            style={{ fontSize: 12, display: 'block', lineHeight: 1.5 }}
                                                        >
                                                            {portalSubmittedAtPrimaryLabel}：{activityTs ?? formalTs}
                                                        </Text>
                                                        {Boolean(
                                                            formalTs && activityTs && formalTs !== activityTs,
                                                        ) ? (
                                                            <Text
                                                                type="secondary"
                                                                style={{
                                                                    fontSize: 11,
                                                                    display: 'block',
                                                                    lineHeight: 1.5,
                                                                    marginTop: 4,
                                                                }}
                                                            >
                                                                {portalSubmittedAtCreatedPrefix}
                                                                {formalTs}
                                                            </Text>
                                                        ) : null}
                                                    </>
                                                )}
                                                <Text
                                                    type="secondary"
                                                    style={{ fontSize: 11, display: 'block', lineHeight: 1.5, marginTop: 6 }}
                                                >
                                                    {portalSubmittedAtTimingTruthNote}
                                                </Text>
                                            </div>
                                        );
                                    })()}
                                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                        {addCarHandoff ? addCarResultEyebrow : '受理结果 · 案件整理（非聊天正文）'}
                                    </Text>
                                    {addCarHandoff && (
                                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 10, lineHeight: 1.5 }}>
                                            {addCarResultEyebrowHint}
                                        </Text>
                                    )}
                                    <Text strong style={{ fontSize: 15, color: '#237804', display: 'block', marginBottom: 10 }}>
                                        {closureHeadline}
                                    </Text>
                                    {addCarHandoff && (triage?.broker_next_step ?? '').trim() && (
                                        <div
                                            style={{
                                                padding: '10px 12px',
                                                background: '#fff',
                                                border: '1px solid #d9d9d9',
                                                borderRadius: 8,
                                                marginBottom: 10,
                                            }}
                                        >
                                            <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                                                {addCarBrokerNextHeading}
                                            </Text>
                                            <Text style={{ fontSize: 13, lineHeight: 1.55 }}>{triage!.broker_next_step}</Text>
                                        </div>
                                    )}
                                    <Text strong style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 6 }}>
                                        当前请求与类型
                                    </Text>
                                    <Space wrap size={[6, 6]} style={{ marginBottom: oneLiner ? 6 : 0 }}>
                                        {triage?.issue_category && (
                                            <Tag color="blue">
                                                {humanizeCategory(triage.issue_category, triage.source_text)}
                                            </Tag>
                                        )}
                                        {caseFocus && (
                                            <Tag color="cyan">{getCaseFocusDisplayLabel(caseFocus) ?? caseFocus}</Tag>
                                        )}
                                    </Space>
                                    {oneLiner && (
                                        <Text type="secondary" style={{ fontSize: 12, display: 'block', lineHeight: 1.55 }}>
                                            {oneLiner}
                                        </Text>
                                    )}
                                </div>
                                {showAddCarStructuredPanel && triage && (
                                        <div
                                            style={{
                                                padding: '12px 14px',
                                                background: '#fff',
                                                borderRadius: 8,
                                                border: '1px solid #e6e6e6',
                                            }}
                                        >
                                            <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                                                {uiCopy.handoff_received_summary_title_add_car ??
                                                    '结构化记录（办公室核对用）'}
                                            </Text>
                                            <Text
                                                type="secondary"
                                                style={{ fontSize: 12, display: 'block', marginBottom: 8, lineHeight: 1.55 }}
                                            >
                                                {uiCopy.handoff_received_summary_intro_add_car ??
                                                    '请您快速核对下列整理结果。若有出入，请用下方「追加到本条记录」说明，无需重开对话。'}
                                            </Text>
                                            {triage.human_confirmation_required && (
                                                <Text
                                                    type="secondary"
                                                    style={{ fontSize: 12, display: 'block', marginBottom: 8, lineHeight: 1.55 }}
                                                >
                                                    {uiCopy.handoff_verify_with_office_note_add_car ??
                                                        '其中标出的项目（如 VIN、驾驶人、材料是否已到齐）办公室仍会最终核实；若您发现不对，也请一并更正。'}
                                                </Text>
                                            )}
                                            <Divider style={{ margin: '10px 0' }} />
                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                {triage.quote_ready_status && (
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: 11 }}>
                                                            整理度：
                                                        </Text>{' '}
                                                        <Tag
                                                            color={
                                                                QUOTE_READY_STATUS_LABELS[triage.quote_ready_status]?.color ??
                                                                'default'
                                                            }
                                                        >
                                                            {QUOTE_READY_STATUS_LABELS[triage.quote_ready_status]?.label ??
                                                                triage.quote_ready_status}
                                                        </Tag>
                                                    </div>
                                                )}
                                                <AddCarHandoffGroupedSnapshot
                                                    triage={triage}
                                                    priorSystemTriage={priorHandoffTriage}
                                                    uiCopy={uiCopy}
                                                />
                                            </Space>
                                        </div>
                                    )}
                                <Divider orientation="left" plain style={{ margin: '4px 0' }}>
                                    {portalPostHandoffNextSectionLabel}
                                </Divider>
                                {processingLine && (
                                    <Text style={{ fontSize: 13, lineHeight: 1.55, display: 'block' }}>
                                        {processingLine}
                                    </Text>
                                )}
                                {(triage?.broker_next_step ?? '').trim() && !addCarHandoff && (
                                    <div
                                        style={{
                                            padding: '10px 12px',
                                            background: '#fff',
                                            border: '1px solid #d9d9d9',
                                            borderRadius: 8,
                                        }}
                                    >
                                        <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
                                            {officeGenericBrokerNextHeading}
                                        </Text>
                                        <Text style={{ fontSize: 13, lineHeight: 1.55 }}>{triage.broker_next_step}</Text>
                                    </div>
                                )}
                                {clientPrepTrimmed && (
                                    <Alert
                                        type="info"
                                        showIcon
                                        message="您可准备"
                                        description={<Text style={{ fontSize: 13, lineHeight: 1.55 }}>{clientPrepTrimmed}</Text>}
                                        style={{ background: '#e6f7ff', border: '1px solid #91d5ff' }}
                                    />
                                )}
                                {addCarHandoff && uiCopy.handoff_office_followup_timing_add_car && (
                                    <Alert
                                        type="info"
                                        showIcon
                                        icon={<ClockCircleOutlined />}
                                        message={
                                            <Text style={{ fontSize: 13, lineHeight: 1.55 }}>
                                                {uiCopy.handoff_office_followup_timing_add_car}
                                            </Text>
                                        }
                                        style={{ background: '#e6f7ff', border: '1px solid #91d5ff' }}
                                    />
                                )}
                                <Divider orientation="left" plain style={{ margin: '4px 0' }}>
                                    {portalPostHandoffClosureSectionLabel}
                                </Divider>
                                <div
                                    style={{
                                        padding: '12px 14px',
                                        background: '#fff',
                                        borderRadius: 8,
                                        border: '1px solid #d9f7be',
                                        borderLeft: '4px solid #389e0d',
                                    }}
                                >
                                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>
                                        {portalClosureSummaryLabel}
                                    </Text>
                                    <Paragraph
                                        style={{
                                            fontSize: addCarHandoff ? 13 : 15,
                                            lineHeight: 1.55,
                                            whiteSpace: 'pre-wrap',
                                            marginBottom: 0,
                                        }}
                                    >
                                        {lastTurn?.content ?? handoffDefault}
                                    </Paragraph>
                                </div>
                                <Text type="secondary" style={{ fontSize: 13, lineHeight: 1.55 }}>
                                    {caseFollowLine}
                                </Text>
                                {lastCaseId && addCarHandoff && (
                                    <Collapse
                                        bordered={false}
                                        style={{ background: 'transparent' }}
                                        activeKey={postHandoffAppendKeys}
                                        onChange={(keys) =>
                                            setPostHandoffAppendKeys(Array.isArray(keys) ? keys : keys ? [keys] : [])
                                        }
                                        items={[
                                            {
                                                key: 'same_case_append',
                                                label: (
                                                    <Text style={{ fontSize: 13, fontWeight: 500 }}>
                                                        {uiCopy.handoff_same_request_panel_title ??
                                                            '还要继续补充本次加车？（同一服务记录）'}
                                                    </Text>
                                                ),
                                                children: (
                                                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55 }}>
                                                            {uiCopy.handoff_same_request_panel_intro ??
                                                                '仅用于更正/补材料等同一条加车请求。另一件事请用「提交新问题」。'}
                                                        </Text>
                                                        <TextArea
                                                            placeholder={
                                                                uiCopy.handoff_same_request_placeholder ??
                                                                '例如：VIN 更正为… / 行驶证截图已发微信…'
                                                            }
                                                            value={postHandoffAppendDraft}
                                                            onChange={(e) => setPostHandoffAppendDraft(e.target.value)}
                                                            rows={3}
                                                            disabled={postHandoffAppendSaving}
                                                            style={{ fontSize: 14 }}
                                                        />
                                                        <Button
                                                            type="default"
                                                            onClick={handlePostHandoffAppendSameCase}
                                                            loading={postHandoffAppendSaving}
                                                            disabled={!postHandoffAppendDraft.trim()}
                                                        >
                                                            {uiCopy.handoff_same_request_submit ?? '追加到本条记录'}
                                                        </Button>
                                                    </Space>
                                                ),
                                            },
                                        ]}
                                    />
                                )}
                                {addCarHandoff && (
                                    <>
                                        <Divider style={{ margin: '12px 0 8px' }} />
                                        <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 6, color: '#434343' }}>
                                            本条记录 vs 新事项
                                        </Text>
                                        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.55, display: 'block', marginBottom: 8 }}>
                                            {addCarBoundaryHint}
                                        </Text>
                                    </>
                                )}
                                <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.5, color: '#595959' }}>
                                    {boundaryHint}
                                </Text>
                                <Space size="middle" wrap>
                                    <Button
                                        type="primary"
                                        size="large"
                                        onClick={() => onSwitchToBroker(lastCaseId)}
                                        icon={<SwapOutlined />}
                                    >
                                        查看工作台
                                    </Button>
                                    <Button type="primary" ghost onClick={handleNewConversation}>
                                        提交新问题
                                    </Button>
                                </Space>
                            </Space>
                        </Card>
                    );
                })()}

                {error && (
                    <Alert type="error" message={error} showIcon closable onClose={() => setError(null)} />
                )}
            </Space>
            </div>
        </div>
    );
}

// =============================================================================
// BROKER WORKBENCH TAB
// =============================================================================

type BrokerWorkbenchTabProps = {
    initialCaseId?: string;
    clientId?: string;
};

function BrokerWorkbenchTab({ initialCaseId, clientId: clientIdProp }: BrokerWorkbenchTabProps) {
    const { uiCopy, clientId: contextClientId } = useClientConfig();
    const clientId = clientIdProp ?? contextClientId;
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const officeWorkbenchSubtitle =
        uiCopy.office_workbench_subtitle ??
        '与客户报送入口一致：此处处理的是同源「服务记录」——客户在微信/入口提交的内容与办公室粘贴整理进入同一队列。加车报价为当前试点最成熟路径；其它场景也会整理，但深度因案而异。';
    const officeWorkbenchDocumentTitle = uiCopy.office_workbench_document_title ?? '加车报价试点 · 办公室工作台';
    const officeRecentCardTitle = uiCopy.office_workbench_recent_card_title ?? '服务记录队列';
    const officeRecentCardExtra = uiCopy.office_workbench_recent_card_extra ?? '与客户报送同源';
    const officePasteCardTitle = uiCopy.office_workbench_paste_card_title ?? '从客户消息整理服务记录';
    const officeEmptyQueueHint =
        uiCopy.office_workbench_empty_queue_hint ??
        '暂无服务记录。请先在右侧粘贴客户消息开始整理；与客户入口提交的报送进入同一队列。演示时可选用「加载演示队列」。';
    const officeCaseRecordLabel = uiCopy.add_car_case_record_id_label ?? '服务记录编号';
    const officeCaseIdHint =
        uiCopy.office_workbench_case_id_hint ?? '与客户报送受理结果卡上的编号一致，便于办公室对单。';
    const officeOpenRecordCta = uiCopy.office_workbench_open_record_cta ?? '打开本条服务记录';
    const officeCaseStatusStripCaption = uiCopy.add_car_status_strip_label ?? '当前状态';
    const officeWorkbenchBrokerNextPreviewLabel =
        uiCopy.office_workbench_broker_next_preview_label ?? '办公室侧下一步：';
    const officeQueueScanSubmitted = uiCopy.office_queue_scan_submitted ?? '已正式送达办公室';
    const officeQueueScanHandoffPending = uiCopy.office_queue_scan_handoff_pending ?? '待客户正式提交';
    const officeQueueScanCollecting = uiCopy.office_queue_scan_collecting ?? '信息收集中';
    const officeQueueScanRecentActivity = uiCopy.office_queue_scan_recent_activity ?? '最近活动';

    const [input, setInput] = useState('');
    const [currentCase, setCurrentCase] = useState<TriageResult | null>(null);
    const [recentCases, setRecentCases] = useState<SavedCase[]>([]);
    const [caseView, setCaseView] = useState<'new' | 'reopened'>('new');
    const [showExamples, setShowExamples] = useState(false);
    const [noteDraft, setNoteDraft] = useState('');
    const [followUpDraft, setFollowUpDraft] = useState<FollowUpDraft>({ waiting_on: 'none', next_contact_by: '' });
    const [loading, setLoading] = useState(false);
    const [recentLoading, setRecentLoading] = useState(false);
    const [statusSaving, setStatusSaving] = useState(false);
    const [noteSaving, setNoteSaving] = useState(false);
    const [followUpSaving, setFollowUpSaving] = useState(false);
    const [appendMessageDraft, setAppendMessageDraft] = useState('');
    const [appendSaving, setAppendSaving] = useState(false);
    const [attachmentUploading, setAttachmentUploading] = useState(false);
    const [demoQueueLoading, setDemoQueueLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const recentCasesSectionRef = useRef<HTMLDivElement>(null);

    const activeExample = useMemo(
        () => QUICK_FILL_EXAMPLES.find((example) => example.text === input.trim()) ?? null,
        [input],
    );
    const actionNowCases = useMemo(
        () => recentCases.filter((savedCase) => getCaseAttentionState(savedCase).section === 'action'),
        [recentCases],
    );
    const trackingCases = useMemo(
        () => recentCases.filter((savedCase) => getCaseAttentionState(savedCase).section !== 'action'),
        [recentCases],
    );
    const currentAttention = currentCase ? getCaseAttentionState(currentCase) : null;
    const currentDueTag = currentCase ? getFollowUpDueTag(currentCase.next_contact_by) : null;
    const currentTrackingSummary = currentCase ? getCaseTrackingSummary(currentCase) : '';
    const currentFollowUpSummary = currentCase ? getFollowUpSummary(currentCase) : '';
    const currentLatestContext = currentCase ? getLatestCaseContext(currentCase) : '';
    const waitingOnClientCount = useMemo(
        () => recentCases.filter((savedCase) => savedCase.case_status !== 'done' && savedCase.waiting_on === 'client').length,
        [recentCases],
    );
    const highRiskCount = useMemo(
        () => recentCases.filter((savedCase) => savedCase.urgency === 'critical' || savedCase.urgency === 'high').length,
        [recentCases],
    );
    const founderQueueLoadedCount = useMemo(() => {
        const loaded = new Set(recentCases.map((savedCase) => normalizeCaseSourceText(savedCase.source_text)));
        return FOUNDER_DEMO_QUEUE.filter((seed) => loaded.has(normalizeCaseSourceText(seed.text))).length;
    }, [recentCases]);

    const loadRecent = async () => {
        setRecentLoading(true);
        try {
            const cases = await listRecentCases(12);
            setRecentCases(orderCasesForWorkbench(cases));
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Could not load recent cases.';
            setError((current) => current ?? msg);
        } finally {
            setRecentLoading(false);
        }
    };

    useEffect(() => {
        void loadRecent();
    }, []);

    useEffect(() => {
        const previousTitle = document.title;
        document.title = officeWorkbenchDocumentTitle;
        return () => {
            document.title = previousTitle;
        };
    }, [officeWorkbenchDocumentTitle]);

    useEffect(() => {
        setFollowUpDraft({
            waiting_on: (currentCase?.waiting_on ?? 'none') as WaitingOn,
            next_contact_by: normalizeFollowUpText(currentCase?.next_contact_by),
        });
    }, [currentCase?.case_id, currentCase?.waiting_on, currentCase?.next_contact_by]);

    useEffect(() => {
        if (!initialCaseId || recentCases.length === 0 || currentCase?.case_id === initialCaseId) return;
        const match = recentCases.find((c) => c.case_id === initialCaseId);
        if (match) {
            setInput(match.source_text);
            setCaseView('reopened');
            setCurrentCase(match);
            setNoteDraft('');
            setError(null);
        }
    }, [initialCaseId, recentCases, currentCase?.case_id]);

    const handleSubmit = async () => {
        const trimmed = input.trim();
        if (!trimmed) {
            setError('Please paste or type a message to triage.');
            return;
        }
        setError(null);
        setCurrentCase(null);
        setLoading(true);
        try {
            const data = await triageMessage(trimmed, true, undefined, undefined, undefined, clientId, true);
            setCaseView('new');
            setCurrentCase(data);
            setNoteDraft('');
            if (data.case_id) {
                message.success('case 已保存到最近列表');
                await loadRecent();
            } else {
                message.warning('case 已创建，但保存到最近列表未完成');
            }
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Triage request failed.';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickFill = (text: string) => {
        setInput(text);
        setCaseView('new');
        setCurrentCase(null);
        setNoteDraft('');
        setError(null);
    };

    const handleOpenRecent = (savedCase: SavedCase) => {
        setInput(savedCase.source_text);
        setCaseView('reopened');
        setCurrentCase(savedCase);
        setNoteDraft('');
        setAppendMessageDraft('');
        setError(null);
    };

    const handleCopyDraft = async () => {
        const draft = (currentCase?.client_reply_draft || '').trim();
        if (!draft) {
            message.warning('暂无草稿可复制');
            return;
        }
        const ok = await copyToClipboard(draft);
        if (ok) message.success('草稿已复制');
        else message.error('复制失败');
    };

    const handleCopyCaseSnapshot = async () => {
        if (!currentCase) return;
        const focus =
            inferCaseFocusFromStructuredFields(
                currentCase.collected_fields,
                currentCase.still_needed_fields,
                currentCase.issue_category,
            ) ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim());
        const lines: string[] = [];
        const focusDisplay = focus ? (getCaseFocusDisplayLabel(focus) ?? focus) : null;
        lines.push(`案件：${focusDisplay ?? '—'}`);
        if (triageResultLooksLikeAddCar(currentCase)) {
            const formal = addCarQueueStatusPhase(currentCase) === 'submitted';
            lines.push(`正式送达办公室：${formal ? '是' : '否'}`);
            const lt = getOfficeLifecycleTag(currentCase.lifecycle_status);
            if (lt) lines.push(`当前接手状态：${lt.label}`);
            const fAt = formatPortalLocalDateTime(
                currentCase.formal_submitted_at ?? currentCase.created_at,
            );
            const uAt = formatPortalLocalDateTime(currentCase.updated_at);
            if (fAt) lines.push(`正式送达办公室（首次）：${fAt}`);
            if (uAt && uAt !== fAt) lines.push(`最近活动（系统更新时间）：${uAt}`);
            lines.push(`流程主要负责方：${addCarNextOwnerLine(currentCase)}`);
        }
        lines.push(`下一步：${(currentCase.broker_next_step ?? '').trim() || '—'}`);
        if ((currentCase.collected_fields?.length ?? 0) > 0) {
            lines.push(
                `已收集：${currentCase.collected_fields!.map(humanizeStructuredField).join('、')}`,
            );
        }
        if ((currentCase.still_needed_fields?.length ?? 0) > 0) {
            lines.push(
                `还缺：${currentCase.still_needed_fields!.map(humanizeStructuredField).join('、')}`,
            );
        }
        const draftPreview = (currentCase.client_reply_draft ?? '').trim().slice(0, 120);
        if (draftPreview) {
            lines.push(`草稿：${draftPreview}${draftPreview.length >= 120 ? '…' : ''}`);
        }
        const snapshot = lines.join('\n');
        const ok = await copyToClipboard(snapshot);
        if (ok) message.success('case 摘要已复制');
        else message.error('复制失败');
    };

    const handleLoadFounderQueue = async () => {
        setDemoQueueLoading(true);
        setError(null);
        try {
            const existingSourceTexts = new Set(recentCases.map((savedCase) => normalizeCaseSourceText(savedCase.source_text)));
            const strongestExistingCase = recentCases.find((savedCase) =>
                normalizeCaseSourceText(savedCase.source_text) === normalizeCaseSourceText(FOUNDER_DEMO_QUEUE[0].text),
            );
            let openedCase: SavedCase | TriageResult | null = null;
            let createdCount = 0;

            for (const seed of FOUNDER_DEMO_QUEUE) {
                if (existingSourceTexts.has(normalizeCaseSourceText(seed.text))) {
                    continue;
                }

                const created = await triageMessage(seed.text, true, undefined, undefined, undefined, clientId, true);
                createdCount += 1;
                existingSourceTexts.add(normalizeCaseSourceText(seed.text));
                let updatedCase: SavedCase | TriageResult = created;

                if (created.case_id && seed.status && seed.status !== created.case_status) {
                    updatedCase = await updateSavedCaseStatus(created.case_id, seed.status);
                }
                if (created.case_id && (seed.waiting_on || seed.next_contact_by)) {
                    updatedCase = await updateSavedCaseFollowUp(
                        created.case_id,
                        seed.waiting_on ?? 'none',
                        seed.next_contact_by ?? '',
                    );
                }
                if (created.case_id && seed.note) {
                    updatedCase = await addSavedCaseNote(created.case_id, seed.note);
                }
                if (seed.open_after_load) {
                    openedCase = updatedCase;
                }
            }

            await loadRecent();
            if (openedCase) {
                setCurrentCase(openedCase);
                setCaseView('reopened');
                setInput(openedCase.source_text ?? '');
            } else if (strongestExistingCase) {
                setCurrentCase(strongestExistingCase);
                setCaseView('reopened');
                setInput(strongestExistingCase.source_text);
            }

            if (createdCount === 0) {
                message.info('演示队列已就绪');
            } else {
                message.success(`已加载 ${createdCount} 条服务记录，见下方「${officeRecentCardTitle}」`);
                recentCasesSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Could not load the founder demo queue.';
            setError(msg);
            message.error('加载演示队列失败');
        } finally {
            setDemoQueueLoading(false);
        }
    };

    const handleStatusChange = async (status: CaseStatus) => {
        if (!currentCase?.case_id) return;
        setStatusSaving(true);
        try {
            const updated = await updateSavedCaseStatus(currentCase.case_id, status);
            setCurrentCase(updated);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            message.success(`已标记为「${CASE_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? humanizeCaseStatus(status)}」`);
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Status update failed.';
            message.error(msg);
        } finally {
            setStatusSaving(false);
        }
    };

    const handleAppendMessage = async () => {
        if (!currentCase?.case_id) return;
        const trimmed = appendMessageDraft.trim();
        if (!trimmed) {
            message.warning('请先粘贴客户新消息');
            return;
        }
        setAppendSaving(true);
        setError(null);
        try {
            const updated = await appendFollowUpMessage(
                currentCase.case_id,
                trimmed,
                currentCase.client_id ?? clientId,
            );
            setCurrentCase(updated);
            setInput(updated.source_text ?? '');
            setAppendMessageDraft('');
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            message.success('已用客户新消息更新 case');
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Append failed.';
            message.error(msg);
        } finally {
            setAppendSaving(false);
        }
    };

    const handleAddNote = async () => {
        if (!currentCase?.case_id) return;
        const trimmed = noteDraft.trim();
        if (!trimmed) {
            message.warning('请先添加简短备注');
            return;
        }
        setNoteSaving(true);
        try {
            const updated = await addSavedCaseNote(currentCase.case_id, trimmed);
            setCurrentCase(updated);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            setNoteDraft('');
            message.success('备注已保存');
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Note save failed.';
            message.error(msg);
        } finally {
            setNoteSaving(false);
        }
    };

    const handleSaveFollowUp = async () => {
        if (!currentCase?.case_id) return;
        setFollowUpSaving(true);
        try {
            const updated = await updateSavedCaseFollowUp(
                currentCase.case_id,
                followUpDraft.waiting_on,
                followUpDraft.next_contact_by,
            );
            setCurrentCase(updated);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            message.success('跟进计划已保存');
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Follow-up save failed.';
            message.error(msg);
        } finally {
            setFollowUpSaving(false);
        }
    };

    const handleAttachmentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!currentCase?.case_id) return;
        const file = e.target.files?.[0];
        if (!file) return;
        setAttachmentUploading(true);
        setError(null);
        try {
            const updated = await uploadCaseAttachment(currentCase.case_id, file);
            setCurrentCase(updated);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            message.success(`已添加附件：${file.name}`);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (err as { message?: string })?.message
                ?? 'Upload failed.';
            message.error(msg);
        } finally {
            setAttachmentUploading(false);
            e.target.value = '';
        }
    };

    const renderRecentCaseCard = (savedCase: SavedCase) => {
        const attention = getCaseAttentionState(savedCase);
        const dueTag = getFollowUpDueTag(savedCase.next_contact_by);
        const readiness = getQueueReadinessLabel(savedCase);
        const compactPreview = getCompactQueuePreview(savedCase);
        const caseFocus =
            inferCaseFocusFromStructuredFields(
                savedCase.collected_fields,
                savedCase.still_needed_fields,
                savedCase.issue_category,
            ) ?? inferCaseFocusFromText(savedCase.source_text ?? '');
        return (
            <Card
                key={savedCase.case_id}
                size="small"
                styles={{ body: { padding: 12 } }}
                style={{
                    background: currentCase?.case_id === savedCase.case_id ? '#f6ffed' : undefined,
                    borderColor: currentCase?.case_id === savedCase.case_id ? '#b7eb8f' : undefined,
                }}
            >
                <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    {triageResultLooksLikeAddCar(savedCase) && (
                        <AddCarCaseStatusStrip
                            triage={savedCase}
                            phase={addCarQueueStatusPhase(savedCase)}
                            caption={officeCaseStatusStripCaption}
                        />
                    )}
                    {triageResultLooksLikeAddCar(savedCase) && (
                        <Text
                            type="secondary"
                            style={{ fontSize: 11, fontFamily: 'monospace', display: 'block' }}
                            copyable={{ text: savedCase.case_id }}
                        >
                            {officeCaseRecordLabel}：{savedCase.case_id}
                        </Text>
                    )}
                    {triageResultLooksLikeAddCar(savedCase) && (() => {
                        const formal = addCarQueueStatusPhase(savedCase) === 'submitted';
                        const ls = savedCase.lifecycle_status;
                        const t = formatPortalLocalDateTime(savedCase.updated_at);
                        const phaseLabel = formal
                            ? officeQueueScanSubmitted
                            : ls === 'handoff_pending'
                              ? officeQueueScanHandoffPending
                              : officeQueueScanCollecting;
                        return (
                            <Text type="secondary" style={{ fontSize: 11, display: 'block', lineHeight: 1.45 }}>
                                {phaseLabel}
                                {t ? ` · ${officeQueueScanRecentActivity} ${t}` : ''}
                            </Text>
                        );
                    })()}
                    <Space wrap size={[4, 4]}>
                        {caseFocus && (
                            <Tag color="blue">{getCaseFocusDisplayLabel(caseFocus) ?? caseFocus}</Tag>
                        )}
                        <Tag color={attention.color}>{attention.label}</Tag>
                        {dueTag && <Tag color={dueTag.color}>{dueTag.label}</Tag>}
                        {!triageResultLooksLikeAddCar(savedCase) &&
                            (() => {
                                const lt = getOfficeLifecycleTag(savedCase.lifecycle_status);
                                return lt ? (
                                    <Tag color={lt.color} style={{ fontSize: 10 }}>
                                        {lt.label}
                                    </Tag>
                                ) : null;
                            })()}
                        {savedCase.case_activity?.[0]?.activity_type === 'follow_up_added' && (
                            <Tag
                                color={
                                    savedCase.case_boundary === 'new_issue'
                                        ? 'volcano'
                                        : savedCase.case_boundary === 'borderline'
                                          ? 'gold'
                                          : 'cyan'
                                }
                            >
                                {savedCase.case_boundary === 'new_issue'
                                    ? '追加 · 疑似新事项'
                                    : savedCase.case_boundary === 'borderline'
                                      ? '追加 · 边界待确认'
                                      : '追加 · 同一条服务记录'}
                            </Tag>
                        )}
                        <Tag color={readiness.color}>{readiness.label}</Tag>
                        {(savedCase as SavedCase & { quote_ready_status?: string }).quote_ready_status && (
                            <Tag color={QUOTE_READY_STATUS_LABELS[(savedCase as SavedCase & { quote_ready_status: string }).quote_ready_status]?.color ?? 'default'}>
                                {QUOTE_READY_STATUS_LABELS[(savedCase as SavedCase & { quote_ready_status: string }).quote_ready_status]?.label ?? (savedCase as SavedCase & { quote_ready_status: string }).quote_ready_status}
                            </Tag>
                        )}
                        {(savedCase as SavedCase & { follow_up_type?: string }).follow_up_type === 'correction' && (
                            <Tag color="gold">客户更正</Tag>
                        )}
                        {(savedCase as SavedCase & { follow_up_type?: string }).follow_up_type === 'already_sent' && (
                            <Tag color="blue">称已发送</Tag>
                        )}
                        {((savedCase as SavedCase).quote_ready_status === 'quote_ready' || (savedCase as SavedCase).quote_ready_status === 'almost_ready') &&
                            !(savedCase as SavedCase).customer_name?.trim() && !(savedCase as SavedCase).customer_phone?.trim() && (
                            <Tag color="orange">需补联系</Tag>
                        )}
                        {(savedCase as SavedCase & { case_attachments?: unknown[] }).case_attachments?.length ? (
                            <Tag color="blue"><PaperClipOutlined /> {(savedCase as SavedCase & { case_attachments: unknown[] }).case_attachments.length}</Tag>
                        ) : null}
                        <UrgencyTag urgency={savedCase.urgency} />
                        {!caseFocus && <Tag>{humanizeCategory(savedCase.issue_category, savedCase.source_text)}</Tag>}
                    </Space>
                    {!triageResultLooksLikeAddCar(savedCase) && (
                        <Text
                            type="secondary"
                            style={{ fontSize: 11, fontFamily: 'monospace', display: 'block' }}
                            copyable={{ text: savedCase.case_id }}
                        >
                            {officeCaseRecordLabel}：{savedCase.case_id}
                        </Text>
                    )}
                    <Text strong style={{ fontSize: 13 }}>{getPreviewText(savedCase.source_text, 80)}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{compactPreview}</Text>
                    {/* Next-step preview — broker sees "what to do" without opening (OFFICE_TOOL_PROFESSIONALIZATION) */}
                    {savedCase.broker_next_step?.trim() && (
                        <Text style={{ fontSize: 12, color: '#262626', display: 'block' }}>
                            {officeWorkbenchBrokerNextPreviewLabel}
                            {getPreviewText(savedCase.broker_next_step, 60)}
                        </Text>
                    )}
                    {/* Follow-up / tracking — prominent when due or waiting_on broker */}
                    <Text type="secondary" style={{ fontSize: 11 }}>
                        {(() => {
                            const dueTag = getFollowUpDueTag(savedCase.next_contact_by);
                            const tracking = getCaseTrackingSummary(savedCase);
                            if (dueTag && (dueTag.kind === 'overdue' || dueTag.kind === 'due_today')) {
                                return (
                                    <span>
                                        <Tag color={dueTag.color} style={{ marginRight: 4 }}>{dueTag.label}</Tag>
                                        {hasSavedFollowUpTarget(savedCase) ? tracking : ''}
                                    </span>
                                );
                            }
                            const latest = getLatestUpdateForDisplay(savedCase, 60);
                            return latest ? `最近：${latest}` : tracking;
                        })()}
                    </Text>
                    <Button size="small" type="primary" onClick={() => handleOpenRecent(savedCase)}>
                        {officeOpenRecordCta}
                    </Button>
                </Space>
            </Card>
        );
    };

    return (
        <div style={{ width: '100%', padding: '4px 0 20px' }}>
            <Row gutter={[18, 18]} align="top">
                <Col xs={24} xl={9}>
                    <div
                        style={{
                            position: 'sticky',
                            top: 8,
                            maxHeight: 'calc(100vh - 96px)',
                            overflowY: 'auto',
                            paddingRight: 2,
                        }}
                    >
                    <Space direction="vertical" size={14} style={{ width: '100%' }}>
                <Card
                    size="small"
                    title="演示队列"
                    extra={<Text type="secondary">加载预设 case 用于演示</Text>}
                    style={{ borderRadius: 8 }}
                >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Row gutter={[12, 12]}>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">需立即处理</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>{actionNowCases.length}</Title>
                                    <Text type="secondary">需经纪人行动或今日到期的 case。</Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">等客户回复</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>{waitingOnClientCount}</Title>
                                    <Text type="secondary">跟进已转给客户，等回复。</Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">队列 case 数</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>{recentCases.length}</Title>
                                    <Text type="secondary">已整理、待经纪人审核的 case。</Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">高风险 case</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>{highRiskCount}</Title>
                                    <Text type="secondary">高/紧急 case 已标出。</Text>
                                </Card>
                            </Col>
                        </Row>
                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                            <Space wrap align="center">
                                <Button type="primary" onClick={() => void handleLoadFounderQueue()} loading={demoQueueLoading}>
                                    加载演示队列
                                </Button>
                                {demoQueueLoading && (
                                    <Text type="secondary" style={{ fontSize: 13 }}>加载中…约 15–30 秒</Text>
                                )}
                                <Tag color={founderQueueLoadedCount === FOUNDER_DEMO_QUEUE.length ? 'green' : 'blue'}>
                                    {founderQueueLoadedCount}/{FOUNDER_DEMO_QUEUE.length} 个 case 已就绪
                                </Tag>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 13 }}>
                                演示路径：加载队列 → 取消风险记录优先打开 → 从服务记录队列重开材料补交、加车报价。
                            </Text>
                        </Space>
                    </Space>
                </Card>

                <div ref={recentCasesSectionRef}>
                <Card
                    size="small"
                    title={officeRecentCardTitle}
                    extra={<Text type="secondary">{officeRecentCardExtra}</Text>}
                >
                    {recentLoading ? (
                        <Spin size="small" />
                    ) : recentCases.length === 0 ? (
                        <Text type="secondary">
                            {officeEmptyQueueHint}
                        </Text>
                    ) : (
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">
                                点击打开任意服务记录，继续下一步、跟进计划或草稿审核。
                            </Text>
                            <Space wrap size={[4, 4]} style={{ fontSize: 11 }}>
                                <Text type="secondary">状态：</Text>
                                <Tag color="red">立即处理</Tag>
                                <Tag color="volcano">待您处理</Tag>
                                <Tag color="green">可行动</Tag>
                                <Tag color="gold">需更多信息</Tag>
                                <Tag color="purple">等客户</Tag>
                            </Space>
                            {actionNowCases.length > 0 && (
                                <>
                                    <Text strong style={{ fontSize: 12 }}>
                                        立即处理 ({actionNowCases.length})
                                    </Text>
                                    {actionNowCases.map((savedCase) => renderRecentCaseCard(savedCase))}
                                </>
                            )}
                            {trackingCases.length > 0 && (
                                <>
                                    <Text strong style={{ fontSize: 12, marginTop: actionNowCases.length > 0 ? 8 : 0 }}>
                                        等待或暂存 ({trackingCases.length})
                                    </Text>
                                    {trackingCases.map((savedCase) => renderRecentCaseCard(savedCase))}
                                </>
                            )}
                        </Space>
                    )}
                </Card>
                </div>
                    </Space>
                    </div>
                </Col>
                <Col xs={24} xl={15}>
                    <Space direction="vertical" size={14} style={{ width: '100%' }}>
                <div style={{ marginBottom: 10, paddingBottom: 12, borderBottom: '1px solid #e8e8e8' }}>
                    <Title level={3} style={{ margin: 0, fontWeight: 600, fontSize: 22 }}>
                        <InboxOutlined /> {officeWorkbench}
                    </Title>
                    <Paragraph type="secondary" style={{ marginTop: 6, marginBottom: 0, fontSize: 13, lineHeight: 1.45 }}>
                        {officeWorkbenchSubtitle}
                    </Paragraph>
                    <Space wrap size={[6, 6]} style={{ marginTop: 8 }}>
                        <Tag color="blue">与客户报送同源</Tag>
                        <Tag color="cyan">加车报价 · 试点旗舰路径</Tag>
                        <Tag color="purple">不自动对外发送</Tag>
                    </Space>
                </div>

                <Card
                    size="small"
                    title={officePasteCardTitle}
                    extra={<Text type="secondary">原文即可，无需整理</Text>}
                    style={{ borderRadius: 8 }}
                >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Text strong>粘贴您当前收到的客户消息（与客户入口报送同等进入服务记录）。</Text>
                        <Text type="secondary">
                            客户文字、转发的通知、邮件摘录、截图 OCR 文字均可。粘贴后系统整理为服务记录，并给出下一步与草稿。
                        </Text>
                        <TextArea
                            placeholder={
                                '在此粘贴客户消息…\n\n无需整理，原文即可。\n\n例如：客户文字、转发通知、邮件摘录、截图 OCR 文字'
                            }
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            rows={8}
                            disabled={loading}
                        />
                        <Space wrap size="middle">
                            <Button
                                type="primary"
                                icon={<SendOutlined />}
                                onClick={handleSubmit}
                                loading={loading}
                            >
                                开始整理
                            </Button>
                            {input.trim() && (
                                <Button
                                    onClick={() => {
                                        setInput('');
                                        setCurrentCase(null);
                                        setError(null);
                                    }}
                                >
                                    清空
                                </Button>
                            )}
                            <Button type="text" onClick={() => setShowExamples((value) => !value)}>
                                {showExamples ? '收起示例' : '需要示例？'}
                            </Button>
                            {activeExample && (
                                <Tag color={getUrgencyColor(activeExample.urgency)}>
                                    已加载：{activeExample.label}
                                </Tag>
                            )}
                        </Space>
                        {showExamples && (
                            <Card
                                size="small"
                                title="示例 case"
                                styles={{ body: { padding: 12 } }}
                                style={{ background: '#fafafa', borderRadius: 8 }}
                            >
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                    <Text type="secondary">
                                        演示时可选用。日常使用请直接粘贴真实客户消息。
                                    </Text>
                                    {QUICK_FILL_EXAMPLES.map((example) => (
                                        <Card
                                            key={example.label}
                                            size="small"
                                            styles={{ body: { padding: 12 } }}
                                            style={{ background: activeExample?.label === example.label ? '#f6ffed' : '#fff' }}
                                        >
                                            <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                                <Space wrap>
                                                    <Text strong>{example.label}</Text>
                                                    <UrgencyTag urgency={example.urgency} />
                                                </Space>
                                                <Text type="secondary">{example.purpose}</Text>
                                                <Button size="small" onClick={() => handleQuickFill(example.text)}>
                                                    加载示例
                                                </Button>
                                            </Space>
                                        </Card>
                                    ))}
                                </Space>
                            </Card>
                        )}
                    </Space>
                </Card>

                {error && (
                    <Alert type="error" message={error} showIcon closable onClose={() => setError(null)} />
                )}

                {loading && (
                    <Card size="small">
                        <Space>
                            <Spin size="small" />
                            <Text type="secondary">正在分析消息并整理服务记录…</Text>
                        </Space>
                    </Card>
                )}

                {currentCase && !loading && (
                    <Card
                        size="small"
                        title={
                            <Space wrap>
                                <span>{caseView === 'reopened' ? '已打开的 case' : '当前 case'}</span>
                                <UrgencyTag urgency={currentCase.urgency} />
                                <Tag>{humanizeCategory(currentCase.issue_category, currentCase.source_text ?? input.trim())}</Tag>
                                {currentCase.case_id && <CaseStatusTag status={currentCase.case_status} />}
                                {(currentCase.waiting_on && currentCase.waiting_on !== 'none') && (
                                    <Tag color="purple">在等：{humanizeWaitingOn(currentCase.waiting_on)}</Tag>
                                )}
                                {currentDueTag && (
                                    <Tag color={currentDueTag.color}>
                                        {currentDueTag.label}
                                    </Tag>
                                )}
                            </Space>
                        }
                        extra={
                            <Space wrap>
                                {currentCase.case_id && (
                                    <Radio.Group
                                        size="small"
                                        optionType="button"
                                        buttonStyle="solid"
                                        value={currentCase.case_status ?? 'new'}
                                        disabled={statusSaving}
                                        options={CASE_STATUS_OPTIONS}
                                        onChange={(event) => void handleStatusChange(event.target.value as CaseStatus)}
                                    />
                                )}
                                <Button
                                    icon={<CopyOutlined />}
                                    onClick={handleCopyCaseSnapshot}
                                    title="复制 case 摘要：案件类型、下一步、已收集、还缺、草稿预览"
                                >
                                    复制 case 摘要
                                </Button>
                                <Button
                                    type="primary"
                                    icon={<CopyOutlined />}
                                    disabled={!currentCase.client_reply_draft?.trim()}
                                    onClick={handleCopyDraft}
                                >
                                    复制客户草稿
                                </Button>
                            </Space>
                        }
                        style={{ borderLeft: currentCase.manual_followup_needed ? '4px solid #fa8c16' : '4px solid #52c41a' }}
                    >
                        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                            {currentCase.case_id && (
                                <div>
                                    <Text
                                        type="secondary"
                                        style={{ fontSize: 12, fontFamily: 'monospace', display: 'block' }}
                                        copyable={{ text: currentCase.case_id }}
                                    >
                                        {officeCaseRecordLabel}：{currentCase.case_id}
                                    </Text>
                                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
                                        {officeCaseIdHint}
                                    </Text>
                                </div>
                            )}
                            {triageResultLooksLikeAddCar(currentCase) && (
                                <AddCarCaseStatusStrip
                                    triage={currentCase}
                                    phase={addCarQueueStatusPhase(currentCase)}
                                    caption={officeCaseStatusStripCaption}
                                />
                            )}
                            {triageResultLooksLikeAddCar(currentCase) && (
                                <OfficeWorkbenchAddCarSubmissionSnapshot triage={currentCase} uiCopy={uiCopy} />
                            )}
                            {currentCase &&
                                (() => {
                                    const mirror = getOfficeAddCarReadinessMirror(currentCase, uiCopy);
                                    if (!mirror) return null;
                                    return (
                                        <div
                                            style={{
                                                marginBottom: 12,
                                                padding: 12,
                                                borderRadius: 8,
                                                border: '1px solid #f0f0f0',
                                                borderLeft: `4px solid ${mirror.borderColor}`,
                                                background: mirror.background,
                                            }}
                                        >
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>
                                                {uiCopy.office_add_car_readiness_panel_title ?? '加车 · 接手就绪度（与客户入口同源）'}
                                            </Text>
                                            <Text strong style={{ fontSize: 14, display: 'block', marginBottom: 8, color: '#262626' }}>
                                                {mirror.headline}
                                            </Text>
                                            <Text style={{ fontSize: 13, lineHeight: 1.55, color: '#434343' }}>{mirror.body}</Text>
                                        </div>
                                    );
                                })()}
                            <Card
                                size="small"
                                title={
                                    <Space wrap size={[4, 4]}>
                                        <Text strong>Case 整理</Text>
                                        <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                                            — 这是什么 case、该做什么、需核实什么
                                        </Text>
                                    </Space>
                                }
                                styles={{ body: { padding: 16 } }}
                                style={{
                                    background: currentCase.manual_followup_needed ? '#fff7e6' : '#f6ffed',
                                    borderColor: currentCase.manual_followup_needed ? '#ffd591' : '#b7eb8f',
                                }}
                            >
                                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                                    {/* Context: Case created/reopened + Resume here */}
                                    <Space wrap align="center">
                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                            {caseView === 'reopened' ? '已保存的 case 重新打开。' : '从当前消息创建 case。'}
                                        </Text>
                                        {currentCase.case_activity?.[0]?.activity_type === 'follow_up_added' && (
                                            <Tag color="cyan">刚用客户新消息更新</Tag>
                                        )}
                                    </Space>
                                    {caseView === 'reopened' &&
                                        currentCase &&
                                        (hasSavedFollowUpTarget(currentCase) || getLatestUpdateForDisplay(currentCase) != null) && (
                                        <div
                                            style={{
                                                padding: 10,
                                                background: '#e6f7ff',
                                                borderRadius: 6,
                                                borderLeft: '4px solid #1890ff',
                                            }}
                                        >
                                                <Text strong style={{ fontSize: 12, color: '#0050b3' }}>
                                                续接此处
                                            </Text>
                                            <div style={{ marginTop: 4 }}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    {hasSavedFollowUpTarget(currentCase) ? currentFollowUpSummary : ''}
                                                    {hasSavedFollowUpTarget(currentCase) && getLatestUpdateForDisplay(currentCase) != null ? ' · ' : ''}
                                                    {getLatestUpdateForDisplay(currentCase) ?? ''}
                                                </Text>
                                            </div>
                                        </div>
                                    )}
                                    {/* What changed recently — prominent when present */}
                                    {currentCase.case_activity?.[0]?.activity_type === 'follow_up_added' && (
                                        <div
                                            style={{
                                                padding: 10,
                                                background: 'rgba(24, 144, 255, 0.08)',
                                                borderRadius: 6,
                                                borderLeft: '3px solid #1890ff',
                                            }}
                                        >
                                            <Text strong style={{ fontSize: 12, color: '#0050b3' }}>
                                                最近更新
                                            </Text>
                                            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                                                根据客户新消息更新了下一步、已收集、还缺。
                                            </Text>
                                        </div>
                                    )}
                                    {/* Row 1: Case focus + status + one-line summary */}
                                    <Space wrap align="center">
                                        {(() => {
                                            const focus = inferCaseFocusFromStructuredFields(currentCase.collected_fields, currentCase.still_needed_fields, currentCase.issue_category)
                                                ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim());
                                            const display = focus ? (getCaseFocusDisplayLabel(focus) ?? focus) : null;
                                            return display ? <Tag color="blue">{display}</Tag> : null;
                                        })()}
                                        {currentCase.collection_stage && (
                                            <Tag color={currentCase.collection_stage === 'enough_for_handoff' ? 'green' : 'default'} style={{ fontSize: 11 }}>
                                                {currentCase.collection_stage === 'enough_for_handoff' ? '可交办公室' : '信息收集中'}
                                            </Tag>
                                        )}
                                        {(() => {
                                            const lt = getOfficeLifecycleTag(currentCase.lifecycle_status);
                                            return lt ? (
                                                <Tag color={lt.color} style={{ fontSize: 10 }}>
                                                    {lt.label}
                                                </Tag>
                                            ) : null;
                                        })()}
                                        {currentAttention && <Tag color={currentAttention.color}>{currentAttention.label}</Tag>}
                                        <Tag color={currentCase.manual_followup_needed ? 'volcano' : 'green'}>
                                            {currentCase.manual_followup_needed ? '需要您处理' : '可审核草稿'}
                                        </Tag>
                                        {(currentCase.urgency === 'critical' || currentCase.urgency === 'high') && (
                                            <Tag color="red" icon={<ClockCircleOutlined />}>
                                                建议当日处理
                                            </Tag>
                                        )}
                                    </Space>
                                    {(() => {
                                        const focusRow =
                                            inferCaseFocusFromStructuredFields(
                                                currentCase.collected_fields,
                                                currentCase.still_needed_fields,
                                                currentCase.issue_category,
                                            ) ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim());
                                        return focusRow === 'Add car quote' ? (
                                            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4, lineHeight: 1.5 }}>
                                                加车报价事务：与客户报送入口「办理加车报价」为同一条旗舰路径，请按可交办公室状态推进出价与核实。
                                            </Text>
                                        ) : null;
                                    })()}
                                    {getCaseReportOneLiner(currentCase, input.trim()) && (
                                        <Text strong style={{ fontSize: 13, lineHeight: 1.4, color: '#262626' }}>
                                            {getCaseReportOneLiner(currentCase, input.trim())}
                                        </Text>
                                    )}
                                    {/* Your next move — handoff visibility: top of action block per HANDOFF_OFFICE_NEXT_ACTION_SPEC */}
                                    <div>
                                        <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                            您的下一步
                                        </Text>
                                        <Text strong style={{ fontSize: 17, lineHeight: 1.5, display: 'block', marginTop: 6, color: '#262626' }}>
                                            {currentCase.broker_next_step}
                                        </Text>
                                    </div>
                                    {/* Correction / context hint badge — handoff visibility */}
                                    {(() => {
                                        const ft = (currentCase.follow_up_type ?? '').trim().toLowerCase();
                                        const cat = (currentCase.issue_category ?? '').trim().toLowerCase();
                                        if (cat === 'customer_requested_human') {
                                            return (
                                                <div
                                                    style={{
                                                        padding: 8,
                                                        background: 'rgba(82, 196, 26, 0.08)',
                                                        borderRadius: 6,
                                                        borderLeft: '3px solid #52c41a',
                                                    }}
                                                >
                                                    <Tag color="green" style={{ fontSize: 11 }}>
                                                        客户要求联系人工
                                                    </Tag>
                                                </div>
                                            );
                                        }
                                        if (ft === 'correction') {
                                            return (
                                                <div
                                                    style={{
                                                        padding: 8,
                                                        background: 'rgba(250, 173, 20, 0.12)',
                                                        borderRadius: 6,
                                                        borderLeft: '3px solid #faad14',
                                                    }}
                                                >
                                                    <Tag color="gold" style={{ fontSize: 11 }}>
                                                        客户更正 / 补充说明
                                                    </Tag>
                                                </div>
                                            );
                                        }
                                        if (ft === 'already_sent') {
                                            return (
                                                <div
                                                    style={{
                                                        padding: 8,
                                                        background: 'rgba(24, 144, 255, 0.08)',
                                                        borderRadius: 6,
                                                        borderLeft: '3px solid #1890ff',
                                                    }}
                                                >
                                                    <Tag color="blue" style={{ fontSize: 11 }}>
                                                        客户称已发送
                                                    </Tag>
                                                </div>
                                            );
                                        }
                                        return null;
                                    })()}
                                    {/* Follow-up block — above fold, working case sheet (OFFICE_TOOL_PROFESSIONALIZATION) */}
                                    {(currentCase.waiting_on && currentCase.waiting_on !== 'none') || currentCase.next_contact_by?.trim() ? (
                                        <div
                                            style={{
                                                padding: 10,
                                                background: currentDueTag?.kind === 'overdue' ? 'rgba(255, 77, 79, 0.08)' : currentDueTag?.kind === 'due_today' ? 'rgba(255, 165, 0, 0.08)' : '#e6f7ff',
                                                borderRadius: 6,
                                                borderLeft: `4px solid ${currentDueTag?.kind === 'overdue' ? '#ff4d4f' : currentDueTag?.kind === 'due_today' ? '#fa8c16' : '#1890ff'}`,
                                            }}
                                        >
                                            <Text strong style={{ fontSize: 12, color: '#0050b3' }}>
                                                跟进
                                            </Text>
                                            <div style={{ marginTop: 4 }}>
                                                <Space wrap size={[4, 4]}>
                                                    {currentDueTag && <Tag color={currentDueTag.color}>{currentDueTag.label}</Tag>}
                                                    {currentCase.waiting_on && currentCase.waiting_on !== 'none' && (
                                                        <Tag color="purple">在等：{humanizeWaitingOn(currentCase.waiting_on)}</Tag>
                                                    )}
                                                    {currentCase.next_contact_by?.trim() && (
                                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                                            下次跟进：{normalizeFollowUpText(currentCase.next_contact_by)}
                                                        </Text>
                                                    )}
                                                </Space>
                                            </div>
                                        </div>
                                    ) : null}
                                    {needsHumanConfirmation(currentCase) && (
                                        <div
                                            style={{
                                                padding: 10,
                                                background: 'rgba(250, 173, 20, 0.1)',
                                                borderRadius: 6,
                                                borderLeft: '3px solid #faad14',
                                            }}
                                        >
                                            <Tag color="gold" style={{ fontSize: 11 }}>
                                                建议人工核实
                                            </Tag>
                                            {(() => {
                                                const fields = currentCase.human_confirmation_fields ?? [];
                                                if (fields.length === 0) {
                                                    return (
                                                        <Text type="secondary" style={{ fontSize: 11, marginLeft: 8, display: 'block', marginTop: 4 }}>
                                                            处理前请核实：付款状态、客户是否已发送材料、加车车架号/驾驶员等高风险字段。
                                                        </Text>
                                                    );
                                                }
                                                const label = fields
                                                    .map((f) => humanizeStructuredField(f))
                                                    .slice(0, 4)
                                                    .join('、');
                                                return (
                                                    <Text type="secondary" style={{ fontSize: 11, marginLeft: 8, display: 'block', marginTop: 4 }}>
                                                        处理前请核实：{label}
                                                    </Text>
                                                );
                                            })()}
                                        </div>
                                    )}
                                    {/* Add-car quote-ready status (ADD_CAR_REAL_INTAKE_LITE) */}
                                    {currentCase.quote_ready_status && (
                                        <div style={{ marginBottom: 8 }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                报价进度
                                            </Text>
                                            <Tag color={QUOTE_READY_STATUS_LABELS[currentCase.quote_ready_status]?.color ?? 'default'}>
                                                {QUOTE_READY_STATUS_LABELS[currentCase.quote_ready_status]?.label ?? currentCase.quote_ready_status}
                                            </Tag>
                                        </div>
                                    )}
                                    {/* Contact block (ADD_CAR_IDENTITY_CONTACT_LITE) */}
                                    {(currentCase.quote_ready_status || (currentCase.collected_fields ?? []).some((f) => f === 'name' || f === 'phone') || (currentCase.still_needed_fields ?? []).some((f) => f === 'name' || f === 'phone')) && (
                                        <div style={{ marginBottom: 8 }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                客户联系
                                            </Text>
                                            <Space wrap size={[8, 4]}>
                                                <span style={{ fontSize: 13 }}>
                                                    {currentCase.customer_name?.trim() ? (
                                                        <Text>姓名：{currentCase.customer_name}</Text>
                                                    ) : (
                                                        <Text type="secondary">待补姓名</Text>
                                                    )}
                                                </span>
                                                <span style={{ fontSize: 13 }}>
                                                    {currentCase.customer_phone?.trim() ? (
                                                        <Text>电话：{currentCase.customer_phone}</Text>
                                                    ) : (
                                                        <Text type="secondary">待补电话</Text>
                                                    )}
                                                </span>
                                            </Space>
                                        </div>
                                    )}
                                    {/* Supporting materials (ADD_CAR_ATTACHMENT_READY_LITE) */}
                                    {currentCase.case_id && (
                                        <div style={{ marginBottom: 8 }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                附加材料
                                            </Text>
                                            {((currentCase as SavedCase).case_attachments?.length ?? 0) > 0 ? (
                                                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                                                    {(currentCase as SavedCase).case_attachments!.map((att) => (
                                                        <div key={att.attachment_id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                            <PaperClipOutlined />
                                                            <a
                                                                href={getAttachmentDownloadUrl(currentCase.case_id!, att.attachment_id)}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                style={{ fontSize: 13 }}
                                                            >
                                                                {att.filename}
                                                            </a>
                                                            <Text type="secondary" style={{ fontSize: 11 }}>
                                                                ({att.type} · {(att.size_bytes / 1024).toFixed(1)} KB)
                                                            </Text>
                                                        </div>
                                                    ))}
                                                    <div>
                                                        <input
                                                            ref={fileInputRef}
                                                            type="file"
                                                            accept="image/*,.pdf"
                                                            style={{ display: 'none' }}
                                                            onChange={handleAttachmentUpload}
                                                        />
                                                        <Button
                                                            size="small"
                                                            icon={<UploadOutlined />}
                                                            loading={attachmentUploading}
                                                            onClick={() => fileInputRef.current?.click()}
                                                        >
                                                            添加附件
                                                        </Button>
                                                    </div>
                                                </Space>
                                            ) : (
                                                <Space>
                                                    <Text type="secondary" style={{ fontSize: 12 }}>可选上传登记证/保单首页等，有助于加快报价</Text>
                                                    <input
                                                        ref={fileInputRef}
                                                        type="file"
                                                        accept="image/*,.pdf"
                                                        style={{ display: 'none' }}
                                                        onChange={handleAttachmentUpload}
                                                    />
                                                    <Button
                                                        size="small"
                                                        icon={<UploadOutlined />}
                                                        loading={attachmentUploading}
                                                        onClick={() => fileInputRef.current?.click()}
                                                    >
                                                        上传
                                                    </Button>
                                                </Space>
                                            )}
                                        </div>
                                    )}
                                    {/* Collected + Still needed */}
                                    {((currentCase.collected_fields?.length ?? 0) > 0 || (currentCase.still_needed_fields?.length ?? 0) > 0) ? (
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                                            {(currentCase.collected_fields?.length ?? 0) > 0 && (
                                                <div style={{ flex: '1 1 200px' }}>
                                                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                        已收集
                                                    </Text>
                                                    <Space wrap size={[4, 4]}>
                                                        {currentCase.collected_fields!.map((f) => (
                                                            <Tag key={f} color="green">
                                                                {humanizeStructuredField(f)}
                                                            </Tag>
                                                        ))}
                                                    </Space>
                                                </div>
                                            )}
                                            {(currentCase.still_needed_fields?.length ?? 0) > 0 && (
                                                <div style={{ flex: '1 1 200px' }}>
                                                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                        还缺
                                                    </Text>
                                                    <Space wrap size={[4, 4]}>
                                                        {currentCase.still_needed_fields!.map((f) => (
                                                            <Tag key={f} color="orange">
                                                                {humanizeStructuredField(f)}
                                                            </Tag>
                                                        ))}
                                                    </Space>
                                                </div>
                                            )}
                                        </div>
                                    ) : (currentCase.conversation_summary || currentCase.secondary_issue_note || currentCase.case_boundary) && (
                                        <div style={{ fontSize: 13 }}>
                                            {currentCase.secondary_issue_note && (
                                                <Tag color="blue" style={{ marginBottom: 6 }}>
                                                    {currentCase.secondary_issue_note}
                                                </Tag>
                                            )}
                                            {currentCase.case_boundary === 'new_issue' && (
                                                <Tag color="volcano" style={{ marginBottom: 6 }}>
                                                    线索边界 · 可能新事项
                                                </Tag>
                                            )}
                                            {currentCase.case_boundary === 'borderline' && (
                                                <Tag color="gold" style={{ marginBottom: 6 }}>
                                                    线索边界 · 建议人工确认
                                                </Tag>
                                            )}
                                            {currentCase.conversation_summary?.includes('Collected:') && (
                                                <Text type="secondary" style={{ display: 'block' }}>
                                                    {currentCase.conversation_summary.match(/Collected:[^.]+\.?/)?.[0]?.trim()}
                                                </Text>
                                            )}
                                            {currentCase.conversation_summary?.includes('Still needed:') && (
                                                <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                                                    {currentCase.conversation_summary.match(/Still needed:[^.]+\.?/)?.[0]?.trim()}
                                                </Text>
                                            )}
                                        </div>
                                    )}
                                    {/* Recent customer messages — context below action block */}
                                    {(() => {
                                        const recent = getRecentCustomerMessages(currentCase, 3);
                                        if (recent.length === 0) return null;
                                        return (
                                            <div
                                                style={{
                                                    padding: 10,
                                                    background: '#fafafa',
                                                    borderRadius: 6,
                                                    borderLeft: '3px solid #1890ff',
                                                }}
                                            >
                                                <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                                    最近客户消息
                                                </Text>
                                                <div style={{ marginTop: 6 }}>
                                                    {recent.map((msg, i) => (
                                                        <div
                                                            key={i}
                                                            style={{
                                                                fontSize: 13,
                                                                lineHeight: 1.5,
                                                                marginBottom: i < recent.length - 1 ? 8 : 0,
                                                                whiteSpace: 'pre-wrap',
                                                            }}
                                                        >
                                                            {msg}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })()}
                                    <Text type="secondary" style={{ fontSize: 11 }}>{getResponseWindow(currentCase.urgency)}</Text>
                                    {currentTrackingSummary && <Text type="secondary" style={{ fontSize: 11 }}>{currentTrackingSummary}</Text>}
                                </Space>
                            </Card>

                            <Row gutter={[12, 12]}>
                                <Col xs={24} md={8}>
                                    <Card size="small" title="客户可准备" styles={{ body: { padding: 12 } }}>
                                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                            <Text>{currentCase.client_prep}</Text>
                                            <Text type="secondary">用于引导下一步向客户要什么。</Text>
                                        </Space>
                                    </Card>
                                </Col>
                                <Col xs={24} md={16}>
                                    <Card size="small" title="草稿回复（确认后再发）" styles={{ body: { padding: 12 } }}>
                                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                            <Tag color={currentCase.manual_followup_needed ? 'gold' : 'green'}>
                                                {getDraftReadinessLabel(currentCase)}
                                            </Tag>
                                            <Text type="secondary">
                                                发给客户的草稿。经纪人审核后手动发送，不自动发送。
                                            </Text>
                                            <div
                                                style={{
                                                    padding: 12,
                                                    background: '#fafafa',
                                                    borderRadius: 6,
                                                    whiteSpace: 'pre-wrap',
                                                    fontFamily: 'inherit',
                                                }}
                                            >
                                                {currentCase.client_reply_draft}
                                            </div>
                                        </Space>
                                    </Card>
                                </Col>
                            </Row>

                            <Row gutter={[12, 12]}>
                                <Col xs={24} md={12}>
                                    <Card size="small" title="当前状态" styles={{ body: { padding: 12 } }}>
                                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                            <Space wrap>
                                                {currentAttention && <Tag color={currentAttention.color}>{currentAttention.label}</Tag>}
                                                {(currentCase.urgency === 'critical' || currentCase.urgency === 'high') && (
                                                    <Tag color="red" icon={<ClockCircleOutlined />}>
                                                        建议当日处理
                                                    </Tag>
                                                )}
                                                {(currentCase.waiting_on && currentCase.waiting_on !== 'none') && (
                                                    <Tag color="purple">在等：{humanizeWaitingOn(currentCase.waiting_on)}</Tag>
                                                )}
                                                <Tag color="default">{getDueStateLabel(currentCase.next_contact_by)}</Tag>
                                            </Space>
                                            <Text strong>{currentFollowUpSummary}</Text>
                                            <Text type="secondary" style={{ display: 'block' }}>
                                                最近更新：{currentLatestContext}
                                            </Text>
                                            <Text type="secondary">最后更新 {formatDateLabel(currentCase.updated_at)}</Text>
                                        </Space>
                                    </Card>
                                </Col>
                                <Col xs={24} md={12}>
                                    <Card
                                        size="small"
                                        title={currentCase.source_text?.includes('[客户]') ? '完整对话' : '打开此 case 的消息'}
                                        styles={{ body: { padding: 12 } }}
                                    >
                                        <div style={{ whiteSpace: 'pre-wrap' }}>
                                            {currentCase.source_text || input.trim()}
                                        </div>
                                    </Card>
                                </Col>
                            </Row>

                            {caseView === 'reopened' && currentCase.case_id && (
                                <Card
                                    size="small"
                                    title="粘贴客户新消息"
                                    styles={{ body: { padding: 12 } }}
                                    style={{ marginBottom: 12, borderColor: '#d9d9d9', borderRadius: 8 }}
                                >
                                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                                        客户发了新消息？粘贴到这里，系统会更新下一步和 context。
                                    </Text>
                                    <Space direction="vertical" style={{ width: '100%' }} size={8}>
                                        <TextArea
                                            value={appendMessageDraft}
                                            onChange={(e) => setAppendMessageDraft(e.target.value)}
                                            placeholder="粘贴客户新消息，例如：我发了ZIP 90210，下周一提车"
                                            rows={2}
                                            maxLength={2000}
                                            disabled={appendSaving}
                                        />
                                        <Button
                                            type="primary"
                                            icon={<SwapOutlined />}
                                            onClick={() => void handleAppendMessage()}
                                            loading={appendSaving}
                                            disabled={!appendMessageDraft.trim()}
                                        >
                                            用新消息更新 case
                                        </Button>
                                    </Space>
                                </Card>
                            )}
                                <div>
                                <Space wrap style={{ marginBottom: 6 }}>
                                    <Text strong style={{ fontSize: 12, color: '#262626' }}>
                                        跟进此 case
                                    </Text>
                                </Space>
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    保存：case 在等谁/什么、下次跟进时间、简短备注。
                                </Text>
                                {currentCase.case_id ? (
                                    <>
                                        <Row gutter={[12, 12]} style={{ marginTop: 10 }}>
                                            <Col xs={24} md={8}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    在等
                                                </Text>
                                                <Select
                                                    style={{ width: '100%', marginTop: 6 }}
                                                    value={followUpDraft.waiting_on}
                                                    options={WAITING_ON_OPTIONS}
                                                    disabled={followUpSaving}
                                                    onChange={(value) =>
                                                        setFollowUpDraft((draft) => ({ ...draft, waiting_on: value as WaitingOn }))
                                                    }
                                                />
                                            </Col>
                                            <Col xs={24} md={10}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    下次跟进
                                                </Text>
                                                <Input
                                                    style={{ marginTop: 6 }}
                                                    value={followUpDraft.next_contact_by}
                                                    onChange={(e) =>
                                                        setFollowUpDraft((draft) => ({
                                                            ...draft,
                                                            next_contact_by: e.target.value,
                                                        }))
                                                    }
                                                    placeholder="例如 2026-03-09 或 明天上午"
                                                    maxLength={80}
                                                    disabled={followUpSaving}
                                                    onPressEnter={() => void handleSaveFollowUp()}
                                                />
                                            </Col>
                                            <Col xs={24} md={6}>
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    保存计划
                                                </Text>
                                                <Button
                                                    type="primary"
                                                    block
                                                    style={{ marginTop: 6 }}
                                                    onClick={() => void handleSaveFollowUp()}
                                                    loading={followUpSaving}
                                                >
                                                    保存跟进
                                                </Button>
                                            </Col>
                                        </Row>
                                        <Text type="secondary" style={{ display: 'block', marginTop: 10, fontSize: 12 }}>
                                            {getFollowUpSummary(followUpDraft)}
                                        </Text>
                                        <Space.Compact style={{ width: '100%', marginTop: 10 }}>
                                            <Input
                                                value={noteDraft}
                                                onChange={(e) => setNoteDraft(e.target.value)}
                                                placeholder="添加简短备注，例如：客户说明早重发驾照"
                                                maxLength={240}
                                                disabled={noteSaving}
                                                onPressEnter={() => void handleAddNote()}
                                            />
                                            <Button type="primary" onClick={() => void handleAddNote()} loading={noteSaving}>
                                                保存备注
                                            </Button>
                                        </Space.Compact>
                                    </>
                                ) : (
                                    <Alert
                                        type="info"
                                        showIcon
                                        style={{ marginTop: 10 }}
                                        message="case 保存后即可添加跟进备注。"
                                    />
                                )}
                                <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
                                    <Col xs={24} md={12}>
                                        <Card
                                            size="small"
                                            title={`经纪人备注 (${currentCase.case_notes?.length ?? 0})`}
                                            styles={{ body: { padding: 12 } }}
                                        >
                                            {currentCase.case_notes && currentCase.case_notes.length > 0 ? (
                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    {currentCase.case_notes.map((note) => (
                                                        <div
                                                            key={note.note_id}
                                                            style={{
                                                                padding: 10,
                                                                background: '#fafafa',
                                                                borderRadius: 6,
                                                            }}
                                                        >
                                                            <Text>{note.body}</Text>
                                                            <br />
                                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                                {formatDateLabel(note.created_at)}
                                                            </Text>
                                                        </div>
                                                    ))}
                                                </Space>
                                            ) : (
                                                <Text type="secondary">
                                                    暂无经纪人备注。
                                                </Text>
                                            )}
                                        </Card>
                                    </Col>
                                    <Col xs={24} md={12}>
                                        <Card
                                            size="small"
                                            title={`操作记录 (${currentCase.case_activity?.length ?? 0})`}
                                            styles={{ body: { padding: 12 } }}
                                        >
                                            {currentCase.case_activity && currentCase.case_activity.length > 0 ? (
                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    {currentCase.case_activity.map((item) => (
                                                        <div
                                                            key={item.activity_id}
                                                            style={{
                                                                padding: 10,
                                                                background: '#fafafa',
                                                                borderRadius: 6,
                                                            }}
                                                        >
                                                            <Text>{item.message}</Text>
                                                            <br />
                                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                                {formatDateLabel(item.created_at)}
                                                            </Text>
                                                        </div>
                                                    ))}
                                                </Space>
                                            ) : (
                                                <Text type="secondary">
                                                    保存 case 后，状态变更、备注、附件等会显示在这里。
                                                </Text>
                                            )}
                                        </Card>
                                    </Col>
                                </Row>
                            </div>
                        </Space>
                    </Card>
                )}
                    </Space>
                </Col>
            </Row>
        </div>
    );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

/** Pilot-ready intro: Add-Car-first scope, trust boundary. Collapsible after first read. */
const PILOT_INTRO = {
    value:
        'Add-Car-first 试点：加车报价报送是当前最成熟的主路径——客户报送后系统整理要点、缺口与业务记录，办公室核对后再出价与对外联系。账单、理赔、保单变更等也可报送，但整理深度因场景而异；不以「全能助手」为承诺。',
    trust: '不自动对外发送；由办公室确认后再联系客户。',
    does: '加车：分步收集、进度提示、交办公室、同记录追加；其他意图：基础整理与草稿（成熟度因场景而异）',
    doesNot: '不直连邮箱/微信；不替代承保系统；不是完整 CRM',
    demoPath:
        '演示建议：客户报送 → 点「办理加车报价」或填写「加车报价 · 结构化报送」→ 办公室工作台查看同一服务记录。',
};

export default function UnifiedIntakePage() {
    const { uiCopy, clientId } = useClientConfig();
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const portalBrandTagline = uiCopy.portal_brand_tagline ?? '车险报送入口 · 加车报价为当前旗舰流程';
    const portalTabCustomer = uiCopy.portal_tab_customer_label ?? '客户报送';
    const portalTabCustomerSuffix = uiCopy.portal_tab_customer_suffix ?? '报送入口（加车优先）';
    const portalTabOfficeSuffix = uiCopy.portal_tab_office_suffix ?? '加车旗舰路径 · 与客户报送同一服务记录';
    const portalTabSimulation = uiCopy.portal_tab_simulation_label ?? '场景仿真';
    const portalTabSimulationSuffix = uiCopy.portal_tab_simulation_suffix ?? '加车脚本回放 · 状态同步';

    const [activeTab, setActiveTab] = useState<string>('customer');
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [pilotIntroCollapsed, setPilotIntroCollapsed] = useState(false);
    const [headerAvatarBroken, setHeaderAvatarBroken] = useState(false);

    const handleSwitchToBroker = (caseId?: string) => {
        setBrokerInitialCaseId(caseId);
        setActiveTab('broker');
    };

    return (
        <div
            style={{
                minHeight: '100%',
                background: '#e8eaed',
                borderLeft: '1px solid #dfe3e8',
                borderRight: '1px solid #dfe3e8',
            }}
        >
            <div
                style={{
                    maxWidth: UNIFIED_INTAKE_SHELL_MAX,
                    margin: '0 auto',
                    padding: '10px 18px 28px',
                }}
            >
            <div
                style={{
                    background: '#fff',
                    borderRadius: 10,
                    border: '1px solid #e8e8e8',
                    padding: '14px 18px 16px',
                    marginBottom: 12,
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div
                        style={{
                            width: 44,
                            height: 44,
                            borderRadius: '50%',
                            overflow: 'hidden',
                            border: '1px solid #d9d9d9',
                            background: '#f5f5f5',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}
                    >
                        {!headerAvatarBroken ? (
                            <img
                                src="/chen-kui-avatar.jpg"
                                alt="陈魁团队头像"
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={() => setHeaderAvatarBroken(true)}
                            />
                        ) : (
                            <Text style={{ color: '#8c8c8c', fontSize: 14, fontWeight: 600 }}>陈魁</Text>
                        )}
                    </div>
                    <div style={{ minWidth: 0 }}>
                        <Text style={{ display: 'block', color: '#1f1f1f', fontSize: 18, lineHeight: 1.35, fontWeight: 600 }}>
                            金盾保险 · 陈魁团队
                        </Text>
                        <Text style={{ display: 'block', color: '#595959', fontSize: 14, lineHeight: 1.5, marginTop: 2 }}>
                            {portalBrandTagline}
                        </Text>
                    </div>
                </div>
            </div>
            <Alert
                type="info"
                showIcon
                closable
                onClose={() => setPilotIntroCollapsed(true)}
                style={{
                    marginBottom: 12,
                    display: pilotIntroCollapsed ? 'none' : 'block',
                }}
                message={
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text strong>{PILOT_INTRO.value}</Text>
                        <Space wrap size={[4, 4]}>
                            <Tag color="green">{PILOT_INTRO.trust}</Tag>
                            <Tag color="blue">做：{PILOT_INTRO.does}</Tag>
                            <Tag color="default">不做：{PILOT_INTRO.doesNot}</Tag>
                        </Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            {PILOT_INTRO.demoPath}
                        </Text>
                    </Space>
                }
            />
            {pilotIntroCollapsed && (
                <div style={{ marginBottom: 6, textAlign: 'right' }}>
                    <Button type="link" size="small" onClick={() => setPilotIntroCollapsed(false)} style={{ padding: 0, fontSize: 12 }}>
                        显示产品说明
                    </Button>
                </div>
            )}
            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                size="large"
                tabBarStyle={{
                    marginBottom: 12,
                    paddingLeft: 0,
                    borderBottom: '1px solid #e8e8e8',
                }}
                items={[
                    {
                        key: 'customer',
                        label: (
                            <span>
                                <CustomerServiceOutlined /> {portalTabCustomer}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabCustomerSuffix}
                                </Text>
                            </span>
                        ),
                        children: (
                            <CustomerEntryTab
                                onSwitchToBroker={handleSwitchToBroker}
                                onOpenScenarioSimulation={() => setActiveTab('simulation')}
                            />
                        ),
                    },
                    {
                        key: 'broker',
                        label: (
                            <span>
                                <InboxOutlined /> {officeWorkbench}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabOfficeSuffix}
                                </Text>
                            </span>
                        ),
                        children: <BrokerWorkbenchTab initialCaseId={brokerInitialCaseId} clientId={clientId} />,
                    },
                    {
                        key: 'simulation',
                        label: (
                            <span>
                                <PlayCircleOutlined /> {portalTabSimulation}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabSimulationSuffix}
                                </Text>
                            </span>
                        ),
                        children: <ScenarioReplayTab />,
                    },
                ]}
            />
            </div>
        </div>
    );
}
