/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — simple front door for customers
 * Tab B: Broker Workbench — internal triage and case management
 *
 * Customer Entry is the default visible tab.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
    Alert,
    Button,
    Card,
    Col,
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
    SendOutlined,
    SwapOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import { SimulationAssistant } from '../components/simulation/SimulationAssistant';
import {
    addSavedCaseNote,
    appendFollowUpMessage,
    clearSessionId,
    getInProgressSession,
    getSessionId,
    listRecentCases,
    triageMessage,
    updateSavedCaseFollowUp,
    updateSavedCaseStatus,
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
    { id: 'add_car', label: '获取报价', shortLabel: '报价', starterMessage: '我想加新车报价' },
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
    { value: 'new', label: 'New' },
    { value: 'reviewing', label: 'Reviewing' },
    { value: 'waiting_client', label: 'Waiting client' },
    { value: 'done', label: 'Done' },
];

const WAITING_ON_OPTIONS: Array<{ value: WaitingOn; label: string }> = [
    { value: 'none', label: 'Nothing blocked' },
    { value: 'client', label: 'Client' },
    { value: 'broker', label: 'Broker' },
    { value: 'carrier', label: 'Carrier' },
    { value: 'underwriting', label: 'Underwriting' },
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

/** Structured field labels for broker scan — add-car, renewal, claim */
const ADD_CAR_FIELD_LABELS: Record<string, string> = {
    year: 'Year',
    make_model: 'Make/Model',
    zip: 'ZIP',
    delivery_date: 'Delivery',
    primary_driver: 'Primary driver',
    vin: 'VIN',
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

function humanizeStructuredField(field: string): string {
    return (
        ADD_CAR_FIELD_LABELS[field] ??
        RENEWAL_FIELD_LABELS[field] ??
        CLAIM_FIELD_LABELS[field] ??
        MISSING_DOC_FIELD_LABELS[field] ??
        field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    );
}

const CATEGORY_DISPLAY_LABELS: Record<string, string> = {
    cancellation_warning: 'Cancellation risk',
    payment_lapse_expiration: 'Payment / lapse risk',
    missing_document: 'Missing document',
    missing_signature: 'Missing signature',
    underwriting_followup: 'UW follow-up',
    renewal_reminder: 'Renewal reminder',
    policy_delay_pending: 'Policy pending',
    informational: 'Informational',
    unclear: 'Needs clarification',
    customer_question: 'Client request',
    customer_requested_human: '联系人工',
};

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

/** One-line handoff summary for Case Report — "Ready for handoff: X — Y" or "Collecting: X — Y" */
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
    const stage = caseItem.collection_stage === 'enough_for_handoff' ? 'Ready for handoff' : 'Collecting';
    const nextPreview = (caseItem.broker_next_step ?? '').slice(0, 60);
    const suffix = nextPreview ? ` — ${nextPreview}${nextPreview.length >= 60 ? '…' : ''}` : '';
    return focus ? `${stage}: ${focus}${suffix}` : `${stage}${suffix}`.trim() || '';
}

/** Infer case focus from structured fields when present — more reliable than text regex */
function inferCaseFocusFromStructuredFields(
    collected?: string[],
    stillNeeded?: string[],
    category?: string,
): string | null {
    if (category === 'customer_requested_human') return '联系人工';
    const fields = [...(collected ?? []), ...(stillNeeded ?? [])];
    if (fields.some((f) => ['year', 'make_model', 'zip', 'delivery_date', 'primary_driver', 'vin'].includes(f))) {
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

function humanizeCategory(cat: string, sourceText?: string): string {
    const category = (cat || '').trim();
    if (category === 'customer_requested_human') return '联系人工';
    if (category === 'customer_question' && sourceText) {
        const focus = inferCaseFocusFromText(sourceText);
        if (focus) return focus;
    }
    return CATEGORY_DISPLAY_LABELS[category] ?? category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Customer-facing (Chinese) field labels for Case Summary in Customer Entry */
const CUSTOMER_FIELD_LABELS_ZH: Record<string, string> = {
    year: '年份',
    make_model: '车型',
    zip: '邮编',
    delivery_date: '提车日期',
    primary_driver: '主驾信息',
    vin: '车架号',
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
};

function humanizeStructuredFieldForCustomer(field: string): string {
    return CUSTOMER_FIELD_LABELS_ZH[field] ?? humanizeStructuredField(field);
}

function humanizeCaseStatus(status?: string): string {
    return (status || 'new').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function humanizeWaitingOn(waitingOn?: string): string {
    if (!waitingOn || waitingOn === 'none') return 'Nothing blocked';
    return waitingOn.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
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
    return <Tag color={getCaseStatusColor(status)}>{humanizeCaseStatus(status)}</Tag>;
}

function getResponseWindow(urgency: TriageResult['urgency']): string {
    if (urgency === 'critical' || urgency === 'high') return 'Same-day broker review';
    if (urgency === 'medium') return 'Review within 1-3 business days';
    return 'Low urgency / routine follow-up';
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
    return result.manual_followup_needed ? 'Edit before sending' : 'Ready for quick broker review';
}

function formatDateLabel(value?: string): string {
    if (!value) return 'Not saved yet';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString();
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
    if (!activity) return `Latest note: ${getPreviewText(note.body?.trim() ?? '', maxLen - 14)}`;
    const noteTime = new Date(note.created_at ?? 0).getTime();
    const activityTime = new Date(activity.created_at ?? 0).getTime();
    if (activityTime >= noteTime) {
        return getPreviewText(activity.message?.trim() ?? '', maxLen);
    }
    return `Latest note: ${getPreviewText(note.body?.trim() ?? '', maxLen - 14)}`;
}

function getLatestCaseContext(caseItem: Pick<TriageResult, 'case_notes' | 'case_activity'>): string {
    const latest = getLatestUpdateForDisplay(caseItem);
    return latest ?? 'No saved follow-up yet';
}

function getFollowUpSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by'>): string {
    const waitingOn = caseItem.waiting_on ?? 'none';
    const nextContactBy = normalizeFollowUpText(caseItem.next_contact_by);
    if (waitingOn === 'none' && !nextContactBy) {
        return 'No follow-up target saved';
    }
    const parts: string[] = [];
    if (waitingOn !== 'none') {
        parts.push(`Waiting on ${humanizeWaitingOn(waitingOn)}`);
    }
    if (nextContactBy) {
        parts.push(`Next contact by ${nextContactBy}`);
    }
    return parts.join(' · ');
}

function getCaseTrackingSummary(caseItem: Pick<TriageResult, 'waiting_on' | 'next_contact_by' | 'case_notes' | 'case_activity'>): string {
    const followUpSummary = getFollowUpSummary(caseItem);
    if (followUpSummary !== 'No follow-up target saved') {
        return followUpSummary;
    }
    return getLatestCaseContext(caseItem);
}

function getFollowUpDueTag(nextContactBy?: string): { color: string; label: string } | null {
    const raw = (nextContactBy || '').trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return null;
    const dueDate = new Date(`${raw}T00:00:00`);
    if (Number.isNaN(dueDate.getTime())) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (dueDate.getTime() < today.getTime()) {
        return { color: 'red', label: 'Overdue' };
    }
    if (dueDate.getTime() === today.getTime()) {
        return { color: 'orange', label: 'Due today' };
    }
    if (dueDate.getTime() === tomorrow.getTime()) {
        return { color: 'gold', label: 'Due tomorrow' };
    }
    return null;
}

/** Due-state label for "Where this case stands" — overdue / due today / due tomorrow / no due date */
function getDueStateLabel(nextContactBy?: string): string {
    const tag = getFollowUpDueTag(nextContactBy);
    if (tag) return tag.label;
    const raw = normalizeFollowUpText(nextContactBy);
    if (raw) return `Due: ${raw}`;
    return 'No due date';
}

function getCaseAttentionState(
    caseItem: Pick<TriageResult, 'urgency' | 'manual_followup_needed' | 'waiting_on' | 'next_contact_by' | 'case_status'>,
): { label: string; color: string; reason: string; section: 'action' | 'tracking' } {
    const dueTag = getFollowUpDueTag(caseItem.next_contact_by);
    if (caseItem.case_status === 'done') {
        return {
            label: 'Closed for now',
            color: 'green',
            reason: 'Marked done, so it stays visible mainly for quick recall.',
            section: 'tracking',
        };
    }
    if (dueTag?.label === 'Overdue') {
        return {
            label: 'Action now',
            color: 'red',
            reason: 'The saved follow-up date has passed and should be reviewed now.',
            section: 'action',
        };
    }
    if (dueTag?.label === 'Due today') {
        return {
            label: 'Due today',
            color: 'orange',
            reason: 'The planned check-in is due today.',
            section: 'action',
        };
    }
    if (caseItem.waiting_on === 'broker') {
        return {
            label: 'Your move',
            color: 'volcano',
            reason: 'The case is currently blocked on broker action.',
            section: 'action',
        };
    }
    if (caseItem.manual_followup_needed && (caseItem.urgency === 'critical' || caseItem.urgency === 'high')) {
        return {
            label: 'Urgent follow-up',
            color: 'red',
            reason: 'High-risk case still needs broker follow-up.',
            section: 'action',
        };
    }
    if (caseItem.manual_followup_needed) {
        return {
            label: 'Follow up soon',
            color: 'gold',
            reason: 'Broker follow-up is still expected before the case is parked.',
            section: 'action',
        };
    }
    if (caseItem.waiting_on && caseItem.waiting_on !== 'none') {
        return {
            label: `Waiting on ${humanizeWaitingOn(caseItem.waiting_on)}`,
            color: 'purple',
            reason: 'Saved follow-up context explains who currently owns the next move.',
            section: 'tracking',
        };
    }
    if (caseItem.case_status === 'reviewing') {
        return {
            label: 'In review',
            color: 'blue',
            reason: 'This case is already open in the broker review flow.',
            section: 'tracking',
        };
    }
    return {
        label: 'Parked for now',
        color: 'default',
        reason: 'Saved for quick recall, even if no immediate action is queued.',
        section: 'tracking',
    };
}

/** Queue-level: "Ready to act" vs "Needs more info" — helps broker scan without opening */
function getQueueReadinessLabel(caseItem: SavedCase): { label: string; color: string } {
    const collected = caseItem.collected_fields ?? [];
    const stillNeeded = caseItem.still_needed_fields ?? [];
    const cat = (caseItem.issue_category ?? '').toLowerCase();
    const src = (caseItem.source_text ?? '').toLowerCase();

    if (cat === 'cancellation_warning' || cat === 'payment_lapse_expiration') {
        return { label: 'Same-day action', color: 'red' };
    }
    if (cat === 'missing_document' || cat === 'underwriting_followup') {
        const hasSent = collected.some((f) => f.includes('customer_says_sent') || f.includes('already_sent'));
        if (hasSent || /发过|already sent|sent it|上周发|又发/i.test(src)) {
            return { label: 'Verify receipt', color: 'orange' };
        }
        if (stillNeeded.some((f) => f.includes('verify_carrier'))) {
            return { label: 'Verify receipt', color: 'orange' };
        }
        return stillNeeded.length > 0 ? { label: 'Needs more info', color: 'gold' } : { label: 'Ready to act', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Add car quote' || /add.?car|加车|加一台|新车|报价/i.test(src)) {
        const hasCore = collected.some((f) => ['year', 'make_model', 'zip', 'delivery_date'].includes(f));
        const needsDriver = stillNeeded.some((f) => f.includes('driver'));
        if (hasCore && !needsDriver) return { label: 'Ready to act', color: 'green' };
        if (stillNeeded.length > 0) return { label: 'Needs more info', color: 'gold' };
        return { label: 'Ready to act', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Claim intake' || /accident|事故|claim|撞/i.test(src)) {
        return stillNeeded.length > 0 ? { label: 'Needs more info', color: 'gold' } : { label: 'Ready to act', color: 'green' };
    }
    if (inferCaseFocusFromText(caseItem.source_text ?? '') === 'Premium review' || /保费|续保|premium|renewal/i.test(src)) {
        return stillNeeded.some((f) => f.includes('renewal') || f.includes('bill')) ? { label: 'Needs more info', color: 'gold' } : { label: 'Ready to act', color: 'green' };
    }
    return { label: 'Ready to act', color: 'green' };
}

/** Compact flow-specific preview for queue cards — not full case card */
function getCompactQueuePreview(caseItem: SavedCase): string {
    const collected = (caseItem.collected_fields ?? []).map(humanizeStructuredField);
    const stillNeeded = (caseItem.still_needed_fields ?? []).map(humanizeStructuredField);
    const focus = inferCaseFocusFromText(caseItem.source_text ?? '');
    const cat = caseItem.issue_category ?? '';

    if (focus === 'Add car quote' || /add.?car|加车|加一台|新车|报价/i.test((caseItem.source_text ?? '').toLowerCase())) {
        if (collected.length > 0 || stillNeeded.length > 0) {
            return `Collected: ${collected.slice(0, 4).join(', ') || '—'}${stillNeeded.length > 0 ? ` · Missing: ${stillNeeded.slice(0, 2).join(', ')}` : ''}`;
        }
    }
    if (focus === 'Premium review' || cat === 'renewal_reminder') {
        if (collected.length > 0 || stillNeeded.length > 0) {
            return `Premium concern${collected.length > 0 ? ` · ${collected.slice(0, 2).join(', ')}` : ''}${stillNeeded.some((s) => /renewal|bill/i.test(s)) ? ' · Missing renewal notice' : ''}`;
        }
        return 'Premium concern · Review options';
    }
    if (focus === 'Claim intake' || /accident|事故|claim/i.test((caseItem.source_text ?? '').toLowerCase())) {
        if (collected.length > 0 || stillNeeded.length > 0) {
            return `Accident reported${collected.length > 0 ? ` · ${collected.slice(0, 2).join(', ')}` : ''}${stillNeeded.length > 0 ? ` · Missing: ${stillNeeded.slice(0, 2).join(', ')}` : ''}`;
        }
        return 'Accident reported · Collect photos and other driver info';
    }
    if (cat === 'missing_document' || cat === 'underwriting_followup') {
        const hasSent = (caseItem.collected_fields ?? []).some((f) => f.includes('customer_says_sent') || f.includes('already_sent'));
        if (hasSent || /发过|already sent|sent it|上周发|又发/i.test(caseItem.source_text ?? '')) {
            return 'Customer says already sent · Verify receipt';
        }
        if (stillNeeded.length > 0) {
            return `Missing: ${stillNeeded.slice(0, 2).join(', ')}`;
        }
        return 'Missing document · Verify items';
    }
    if (cat === 'cancellation_warning' || cat === 'payment_lapse_expiration') {
        return 'Same-day action · Confirm balance due';
    }
    return getPreviewText(caseItem.broker_next_step ?? '', 72);
}

function getCaseWorkbenchScore(
    caseItem: Pick<TriageResult, 'urgency' | 'manual_followup_needed' | 'waiting_on' | 'next_contact_by' | 'case_status'>,
): number {
    const attention = getCaseAttentionState(caseItem);
    let score = attention.section === 'action' ? 100 : 0;
    if (attention.label === 'Action now') score += 70;
    else if (attention.label === 'Due today') score += 60;
    else if (attention.label === 'Your move') score += 50;
    else if (attention.label === 'Urgent follow-up') score += 40;
    else if (attention.label === 'Follow up soon') score += 25;
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
};

function CustomerEntryTab({ onSwitchToBroker }: CustomerEntryTabProps) {
    const { uiCopy, clientId } = useClientConfig();
    const quickStartButtons = useMemo(
        () => (uiCopy.quick_start_buttons ? getQuickStartButtons(uiCopy) : DEFAULT_QUICK_START_BUTTONS),
        [uiCopy.quick_start_buttons],
    );
    const officeLabel = uiCopy.office_label ?? '办公室';
    const handoffDefault = uiCopy.handoff_default ?? '办公室会尽快处理，有结果会联系您。';
    const welcomeHighlight = uiCopy.welcome_highlight ?? '您的消息会直接转给办公室，我们会尽快帮您处理。';
    const welcomeHint = uiCopy.welcome_hint ?? '如需人工协助，点击「联系人工」即可，消息会直接转给办公室。';

    const [input, setInput] = useState('');
    const [turns, setTurns] = useState<ConversationTurn[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showExamples, setShowExamples] = useState(false);
    const [lastCaseId, setLastCaseId] = useState<string | undefined>();
    const [simulationAssistantOpen, setSimulationAssistantOpen] = useState(false);
    const [selectedButtonIntent, setSelectedButtonIntent] = useState<SoftRouteIntent | null>(null);
    const loadingPlaceholderRef = useRef<HTMLDivElement>(null);

    const handoffReady = turns.length > 0 && turns[turns.length - 1]?.role === 'system' && turns[turns.length - 1]?.triageResult?.handoff_ready;

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
            message.success('已恢复对话', 2);
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
            const data = await triageMessage(trimmed, true, conversationTurnsForApi, softRoute ?? undefined, undefined, clientId);
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
            if (data.case_id) {
                setLastCaseId(data.case_id);
                clearSessionId(); // Phase 2: new session for next conversation
                message.success('已收到，我们会尽快处理。');
            }
            if (data.handoff_ready) {
                message.success(handoffDefault);
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

    const handleSubmit = () => submitMessage(input.trim(), selectedButtonIntent ?? undefined);

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
        clearSessionId(); // Phase 2: fresh session for new conversation
    };

    return (
        <div style={{ padding: 32, maxWidth: 800, margin: '0 auto' }}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
                    <div style={{ flex: 1, minWidth: 280 }}>
                        <Title level={2} style={{ margin: 0, fontWeight: 600 }}>
                            <CustomerServiceOutlined /> 客户入口
                        </Title>
                        <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0, fontSize: 15, lineHeight: 1.6 }}>
                            请描述您的问题或粘贴收到的通知内容。<strong style={{ color: 'rgba(255,255,255,0.9)' }}>{welcomeHighlight}</strong>
                        </Paragraph>
                    </div>
                    <Button
                        icon={<ThunderboltOutlined />}
                        onClick={() => setSimulationAssistantOpen(true)}
                        size="small"
                        type="text"
                        style={{ color: 'rgba(255,255,255,0.55)', fontSize: 12 }}
                    >
                        模拟演示
                    </Button>
                </div>

                {/* Hybrid unified entry: welcome + quick-start buttons + free text */}
                {turns.length === 0 && (
                    <Card size="small" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8 }}>
                        <Space direction="vertical" size="large" style={{ width: '100%' }}>
                            <div>
                                <Text strong style={{ fontSize: 20, display: 'block', marginBottom: 8 }}>
                                    今天有什么可以帮您？
                                </Text>
                                <Text type="secondary" style={{ fontSize: 14, lineHeight: 1.6 }}>
                                    {welcomeHint}
                                </Text>
                            </div>
                            <div>
                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                    快速选择
                                </Text>
                                <Space wrap size={[10, 10]}>
                                    {quickStartButtons.map((btn) => (
                                        <Button
                                            key={btn.id}
                                            type={selectedButtonIntent === btn.id ? 'primary' : 'default'}
                                            onClick={() => handleButtonStarter(btn)}
                                            loading={loading}
                                            size="middle"
                                            style={selectedButtonIntent === btn.id ? undefined : { borderColor: 'rgba(255,255,255,0.2)' }}
                                        >
                                            {btn.label}
                                        </Button>
                                    ))}
                                </Space>
                            </div>
                        </Space>
                    </Card>
                )}

                <SimulationAssistant
                    open={simulationAssistantOpen}
                    onClose={() => setSimulationAssistantOpen(false)}
                />

                {turns.length > 0 && (() => {
                    const lastSystemTurn = [...turns].reverse().find((t) => t.role === 'system');
                    const latestTriage = lastSystemTurn?.triageResult;
                    return (
                        <>
                <Card
                        size="small"
                        style={{
                            background: 'rgba(255,255,255,0.02)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 8,
                            maxHeight: 360,
                            overflowY: 'auto',
                        }}
                    >
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
                                            {turn.role === 'customer' ? '您' : officeLabel}
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
                                                            ? 'Ready for handoff'
                                                            : 'Collecting info'}
                                                    </Tag>
                                                )}
                                                {turn.triageResult.follow_up_type && turn.triageResult.follow_up_type !== 'new_info' && (
                                                    <Tag color="blue" style={{ fontSize: 11 }}>
                                                        Follow-up: {turn.triageResult.follow_up_type}
                                                    </Tag>
                                                )}
                                                {turn.triageResult.human_confirmation_required && (
                                                    <Tag color="gold" style={{ fontSize: 11 }}>
                                                        Human confirmation recommended
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
                                            {officeLabel}
                                        </Text>
                                        <Space size={8}>
                                            <Spin size="small" />
                                            <Text type="secondary" style={{ fontSize: 14 }}>正在整理，马上就好...</Text>
                                        </Space>
                                    </div>
                                </div>
                            )}
                        </Space>
                    </Card>

                    {latestTriage && !handoffReady && (
                        <Card
                            size="small"
                            title={
                                <Space size={4}>
                                    <InboxOutlined />
                                    <span>整理中</span>
                                    <Text type="secondary" style={{ fontSize: 10, fontWeight: 400 }}>（实时更新）</Text>
                                </Space>
                            }
                            style={{ background: 'rgba(0,0,0,0.12)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                        >
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                {latestTriage?.issue_category && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: 11 }}>主题：</Text>
                                        <Tag color="blue">{humanizeCategory(latestTriage.issue_category, latestTriage.source_text)}</Tag>
                                    </div>
                                )}
                                {(latestTriage?.collected_fields?.length ?? 0) > 0 && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: 11 }}>已收集：</Text>
                                        <Space size={4} wrap>
                                            {latestTriage!.collected_fields!.slice(0, 6).map((f) => (
                                                <Tag key={f} color="green">{humanizeStructuredFieldForCustomer(f)}</Tag>
                                            ))}
                                        </Space>
                                    </div>
                                )}
                                {(latestTriage?.still_needed_fields?.length ?? 0) > 0 && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: 11 }}>还需：</Text>
                                        <Space size={4} wrap>
                                            {latestTriage!.still_needed_fields!.slice(0, 4).map((f) => (
                                                <Tag key={f} color="orange">{humanizeStructuredFieldForCustomer(f)}</Tag>
                                            ))}
                                        </Space>
                                    </div>
                                )}
                                {latestTriage?.next_best_question && (
                                    <div>
                                        <Text type="secondary" style={{ fontSize: 11 }}>下一步建议：</Text>
                                        <Text style={{ fontSize: 12, display: 'block', marginTop: 2 }}>
                                            {latestTriage.next_best_question.slice(0, 120)}
                                            {(latestTriage.next_best_question?.length ?? 0) > 120 ? '…' : ''}
                                        </Text>
                                    </div>
                                )}
                                {latestTriage?.lifecycle_status && (
                                    <Tag color={latestTriage.lifecycle_status === 'handoff_pending' ? 'green' : 'default'} style={{ fontSize: 10 }}>
                                        {latestTriage.lifecycle_status === 'handoff_pending' ? 'Ready to save' : 'Collecting'}
                                    </Tag>
                                )}
                            </Space>
                        </Card>
                    )}
                        </>
                    );
                })()}

                {!handoffReady && (
                    <Card size="small" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8 }}>
                        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                            {turns.length > 0 && selectedButtonIntent && (
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
                                        {QUICK_START_BUTTONS.find((b) => b.id === selectedButtonIntent)?.label ?? selectedButtonIntent}
                                    </Tag>
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                        （可点击 × 取消，直接输入会覆盖）
                                    </Text>
                                </Space>
                            )}
                            <TextArea
                                placeholder={
                                    turns.length === 0
                                        ? '请在此输入或粘贴您的问题、通知内容或截图文字...'
                                        : '继续补充信息，或直接发送'
                                }
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                rows={turns.length > 0 ? 3 : 8}
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
                                {turns.length === 0 ? '提交' : '发送'}
                            </Button>
                            <Button type="text" size="small" onClick={() => setShowExamples((v) => !v)}>
                                {showExamples ? '收起示例' : '不确定说什么？点这里看示例'}
                            </Button>
                            {showExamples && (
                                <Card size="small" style={{ background: 'rgba(0,0,0,0.2)' }}>
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

                {handoffReady && (() => {
                    const lastTurn = turns[turns.length - 1];
                    const triage = lastTurn?.role === 'system' ? lastTurn.triageResult : null;
                    const caseFocus = triage
                        ? (inferCaseFocusFromStructuredFields(triage.collected_fields, triage.still_needed_fields, triage.issue_category)
                            ?? inferCaseFocusFromText(triage.source_text ?? ''))
                        : null;
                    const oneLiner = triage ? getCaseReportOneLiner(triage, turns.find((t) => t.role === 'customer')?.content ?? '') : '';
                    return (
                        <Card
                            size="small"
                            style={{
                                borderLeft: '4px solid #52c41a',
                                background: 'rgba(82, 196, 26, 0.08)',
                            }}
                        >
                            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                {(caseFocus || oneLiner) && (
                                    <Space wrap size={[4, 4]}>
                                        {caseFocus && <Tag color="blue">{caseFocus}</Tag>}
                                        {oneLiner && (
                                            <Text type="secondary" style={{ fontSize: 13 }}>
                                                {oneLiner}
                                            </Text>
                                        )}
                                    </Space>
                                )}
                                <Text strong style={{ fontSize: 16 }}>
                                    {lastTurn?.content ?? handoffDefault}
                                </Text>
                                <Text type="secondary">
                                    {lastCaseId ? `已整理成 case，${officeLabel}会尽快跟进。` : `如有需要，${officeLabel}会主动联系您。`}
                                </Text>
                                <Space size="middle">
                                    <Button
                                        type="primary"
                                        size="large"
                                        onClick={() => onSwitchToBroker(lastCaseId)}
                                        icon={<SwapOutlined />}
                                    >
                                        查看工作台
                                    </Button>
                                    <Button onClick={handleNewConversation}>提交新问题</Button>
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
    const [demoQueueLoading, setDemoQueueLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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
        document.title = 'Unified Intake | Broker Workbench';
        return () => {
            document.title = previousTitle;
        };
    }, []);

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
            const data = await triageMessage(trimmed, true, undefined, undefined, undefined, clientId);
            setCaseView('new');
            setCurrentCase(data);
            setNoteDraft('');
            if (data.case_id) {
                message.success('Case saved to recent cases');
                await loadRecent();
            } else {
                message.warning('Case card created, but recent-case save did not complete');
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
            message.warning('No draft to copy');
            return;
        }
        const ok = await copyToClipboard(draft);
        if (ok) message.success('Client draft copied');
        else message.error('Copy failed');
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
        lines.push(`Case: ${focus ?? '—'}`);
        lines.push(`Next move: ${(currentCase.broker_next_step ?? '').trim() || '—'}`);
        if ((currentCase.collected_fields?.length ?? 0) > 0) {
            lines.push(
                `Collected: ${currentCase.collected_fields!.map(humanizeStructuredField).join(', ')}`,
            );
        }
        if ((currentCase.still_needed_fields?.length ?? 0) > 0) {
            lines.push(
                `Still needed: ${currentCase.still_needed_fields!.map(humanizeStructuredField).join(', ')}`,
            );
        }
        const draftPreview = (currentCase.client_reply_draft ?? '').trim().slice(0, 120);
        if (draftPreview) {
            lines.push(`Draft: ${draftPreview}${draftPreview.length >= 120 ? '…' : ''}`);
        }
        const snapshot = lines.join('\n');
        const ok = await copyToClipboard(snapshot);
        if (ok) message.success('Case snapshot copied');
        else message.error('Copy failed');
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

                const created = await triageMessage(seed.text, true, undefined, undefined, undefined, clientId);
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
                message.info('Founder demo queue is already ready in this local workbench');
            } else {
                message.success('Founder demo queue loaded with demo-safe saved cases');
            }
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Could not load the founder demo queue.';
            setError(msg);
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
            message.success(`Case marked ${humanizeCaseStatus(status).toLowerCase()}`);
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
            message.warning('Paste the new customer message first');
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
            message.success('Case updated with new customer follow-up');
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
            message.warning('Add a short broker note first');
            return;
        }
        setNoteSaving(true);
        try {
            const updated = await addSavedCaseNote(currentCase.case_id, trimmed);
            setCurrentCase(updated);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            setNoteDraft('');
            message.success('Broker note saved');
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
            message.success('Follow-up plan saved');
        } catch (e: unknown) {
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Follow-up save failed.';
            message.error(msg);
        } finally {
            setFollowUpSaving(false);
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
                    <Space wrap size={[4, 4]}>
                        {caseFocus && (
                            <Tag color="blue">{caseFocus}</Tag>
                        )}
                        <Tag color={attention.color}>{attention.label}</Tag>
                        {dueTag && <Tag color={dueTag.color}>{dueTag.label}</Tag>}
                        {savedCase.lifecycle_status && (
                            <Tag color={savedCase.lifecycle_status === 'handed_off' ? 'blue' : 'purple'} style={{ fontSize: 10 }}>
                                {savedCase.lifecycle_status === 'handed_off' ? 'Handed off' : 'Office follow-up'}
                            </Tag>
                        )}
                        {savedCase.case_activity?.[0]?.activity_type === 'follow_up_added' && (
                            <Tag color="cyan">Updated</Tag>
                        )}
                        <Tag color={readiness.color}>{readiness.label}</Tag>
                        <UrgencyTag urgency={savedCase.urgency} />
                        {!caseFocus && <Tag>{humanizeCategory(savedCase.issue_category, savedCase.source_text)}</Tag>}
                    </Space>
                    <Text strong style={{ fontSize: 13 }}>{getPreviewText(savedCase.source_text, 80)}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{compactPreview}</Text>
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                        {(() => {
                                            const latest = getLatestUpdateForDisplay(savedCase, 60);
                                            return latest ? `最近：${latest}` : getCaseTrackingSummary(savedCase);
                                        })()}
                                    </Text>
                    <Button size="small" type="primary" onClick={() => handleOpenRecent(savedCase)}>
                        打开 case
                    </Button>
                </Space>
            </Card>
        );
    };

    return (
        <div style={{ padding: 28, maxWidth: 1180, margin: '0 auto' }}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div>
                    <Title level={3} style={{ margin: 0, fontWeight: 600 }}>
                        <InboxOutlined /> {officeWorkbench}
                    </Title>
                    <Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0, fontSize: 14, lineHeight: 1.5 }}>
                        粘贴客户消息 → 整理成 case → 下一步动作、已收集/还缺什么、草稿回复。确认后再发。
                    </Paragraph>
                    <Space wrap size={[8, 8]} style={{ marginTop: 12 }}>
                        <Tag color="blue">粘贴 → 整理</Tag>
                        <Tag color="purple">不自动发送</Tag>
                    </Space>
                </div>

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
                            <Space wrap>
                                <Button type="primary" onClick={() => void handleLoadFounderQueue()} loading={demoQueueLoading}>
                                    加载演示队列
                                </Button>
                                <Tag color={founderQueueLoadedCount === FOUNDER_DEMO_QUEUE.length ? 'green' : 'blue'}>
                                    {founderQueueLoadedCount}/{FOUNDER_DEMO_QUEUE.length} 个 case 已就绪
                                </Tag>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 13 }}>
                                演示路径：加载队列 → 取消风险 case 优先打开 → 从最近 case 重开材料补交、加车报价。
                            </Text>
                        </Space>
                    </Space>
                </Card>

                <Card
                    size="small"
                    title="粘贴消息开始"
                    extra={<Text type="secondary">原文即可，无需整理</Text>}
                    style={{ borderRadius: 8 }}
                >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Text strong>粘贴您当前收到的客户消息。</Text>
                        <Text type="secondary">
                            客户文字、转发的通知、邮件摘录、截图 OCR 文字均可。粘贴后系统会整理成 case。
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
                                    Clear
                                </Button>
                            )}
                            <Button type="text" onClick={() => setShowExamples((value) => !value)}>
                                {showExamples ? '收起示例' : '需要示例？'}
                            </Button>
                            {activeExample && (
                                <Tag color={getUrgencyColor(activeExample.urgency)}>
                                    Example loaded: {activeExample.label}
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
                            <Text type="secondary">正在分析消息并整理 case...</Text>
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
                                    <Tag color="purple">Waiting on {humanizeWaitingOn(currentCase.waiting_on)}</Tag>
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
                                    title="复制 case 摘要：focus、下一步、已收集、还缺、草稿预览"
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
                                    {caseView === 'reopened' && (currentFollowUpSummary !== 'No follow-up target saved' || currentLatestContext !== 'No saved follow-up yet') && (
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
                                                    {currentFollowUpSummary !== 'No follow-up target saved'
                                                        ? currentFollowUpSummary
                                                        : ''}
                                                    {currentFollowUpSummary !== 'No follow-up target saved' && currentLatestContext !== 'No saved follow-up yet' ? ' · ' : ''}
                                                    {currentLatestContext !== 'No saved follow-up yet' ? currentLatestContext : ''}
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
                                        {(inferCaseFocusFromStructuredFields(currentCase.collected_fields, currentCase.still_needed_fields, currentCase.issue_category)
                                            ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim())) && (
                                            <Tag color="blue">
                                                {inferCaseFocusFromStructuredFields(currentCase.collected_fields, currentCase.still_needed_fields, currentCase.issue_category)
                                                    ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim())}
                                            </Tag>
                                        )}
                                        {currentCase.collection_stage && (
                                            <Tag color={currentCase.collection_stage === 'enough_for_handoff' ? 'green' : 'default'} style={{ fontSize: 11 }}>
                                                {currentCase.collection_stage === 'enough_for_handoff' ? 'Ready for handoff' : 'Collecting info'}
                                            </Tag>
                                        )}
                                        {currentCase.lifecycle_status && (
                                            <Tag color={currentCase.lifecycle_status === 'handed_off' ? 'blue' : 'purple'} style={{ fontSize: 10 }}>
                                                {currentCase.lifecycle_status === 'handed_off' ? 'Handed off' : 'Office follow-up'}
                                            </Tag>
                                        )}
                                        {currentAttention && <Tag color={currentAttention.color}>{currentAttention.label}</Tag>}
                                        <Tag color={currentCase.manual_followup_needed ? 'volcano' : 'green'}>
                                            {currentCase.manual_followup_needed ? 'Broker action required' : 'Ready for broker review'}
                                        </Tag>
                                        {(currentCase.urgency === 'critical' || currentCase.urgency === 'high') && (
                                            <Tag color="red" icon={<ClockCircleOutlined />}>
                                                Same-day action
                                            </Tag>
                                        )}
                                    </Space>
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
                                                        Customer corrected / clarified
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
                                                        Client says already sent
                                                    </Tag>
                                                </div>
                                            );
                                        }
                                        return null;
                                    })()}
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
                                                Human confirmation recommended
                                            </Tag>
                                            {(() => {
                                                const fields = currentCase.human_confirmation_fields ?? [];
                                                if (fields.length === 0) {
                                                    return (
                                                        <Text type="secondary" style={{ fontSize: 11, marginLeft: 8, display: 'block', marginTop: 4 }}>
                                                            Verify before acting: payment status, customer_says_sent, or add-car VIN/driver.
                                                        </Text>
                                                    );
                                                }
                                                const label = fields
                                                    .map((f) => humanizeStructuredField(f))
                                                    .slice(0, 4)
                                                    .join(', ');
                                                return (
                                                    <Text type="secondary" style={{ fontSize: 11, marginLeft: 8, display: 'block', marginTop: 4 }}>
                                                        Verify before acting: {label}
                                                    </Text>
                                                );
                                            })()}
                                        </div>
                                    )}
                                    {/* Collected + Still needed */}
                                    {((currentCase.collected_fields?.length ?? 0) > 0 || (currentCase.still_needed_fields?.length ?? 0) > 0) ? (
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                                            {(currentCase.collected_fields?.length ?? 0) > 0 && (
                                                <div style={{ flex: '1 1 200px' }}>
                                                    <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                                                        Collected
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
                                                    <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                                                        Still needed
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
                                    ) : currentCase.conversation_summary && (
                                        <div style={{ fontSize: 13 }}>
                                            {currentCase.conversation_summary.includes('Collected:') && (
                                                <Text type="secondary" style={{ display: 'block' }}>
                                                    {currentCase.conversation_summary.match(/Collected:[^.]+\.?/)?.[0]?.trim()}
                                                </Text>
                                            )}
                                            {currentCase.conversation_summary.includes('Still needed:') && (
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
                                                        Same-day action
                                                    </Tag>
                                                )}
                                                {(currentCase.waiting_on && currentCase.waiting_on !== 'none') && (
                                                    <Tag color="purple">Waiting on {humanizeWaitingOn(currentCase.waiting_on)}</Tag>
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
                                            placeholder="Paste the new customer message, e.g. 我发了ZIP 90210，下周一提车"
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
                                                                Added {formatDateLabel(note.created_at)}
                                                            </Text>
                                                        </div>
                                                    ))}
                                                </Space>
                                            ) : (
                                                <Text type="secondary">
                                                    No broker notes yet.
                                                </Text>
                                            )}
                                        </Card>
                                    </Col>
                                    <Col xs={24} md={12}>
                                        <Card
                                            size="small"
                                            title={`Activity (${currentCase.case_activity?.length ?? 0})`}
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
                                                    Activity starts after the case is saved and touched.
                                                </Text>
                                            )}
                                        </Card>
                                    </Col>
                                </Row>
                            </div>
                        </Space>
                    </Card>
                )}

                <Card
                    size="small"
                    title="最近 case"
                    extra={<Text type="secondary">工作队列</Text>}
                >
                    {recentLoading ? (
                        <Spin size="small" />
                    ) : recentCases.length === 0 ? (
                        <Text type="secondary">整理 case 后会显示在这里。粘贴消息开始，或加载演示队列。</Text>
                    ) : (
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary">
                                点击打开任意 case，继续下一步、跟进计划或草稿审核。
                            </Text>
                            <Space wrap size={[4, 4]} style={{ fontSize: 11 }}>
                                <Text type="secondary">状态：</Text>
                                <Tag color="red">立即处理</Tag>
                                <Tag color="volcano">您的行动</Tag>
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
            </Space>
        </div>
    );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

/** Pilot-ready intro: what this is, trust boundary. Collapsible after first read. */
const PILOT_INTRO = {
    value: '把客户发来的消息整理成结构化 case：下一步动作、已收集/还缺什么、草稿回复。经纪人确认后再发，不自动发送。',
    trust: '不自动发送。经纪人确认后再发。',
    does: '整理消息 → 结构化 case；多轮收集；草稿回复；本地保存',
    doesNot: '不连接邮箱/微信；不自动发送；不是完整 CRM',
    demoPath: '演示：办公室工作台 → 加载演示队列 → 取消风险 case 优先；或客户入口 → 模拟演示',
};

export default function UnifiedIntakePage() {
    const { uiCopy, clientId } = useClientConfig();
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const officeLabel = uiCopy.office_label ?? '办公室';

    const [activeTab, setActiveTab] = useState<string>('customer');
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [pilotIntroCollapsed, setPilotIntroCollapsed] = useState(false);

    const handleSwitchToBroker = (caseId?: string) => {
        setBrokerInitialCaseId(caseId);
        setActiveTab('broker');
    };

    return (
        <div style={{ paddingTop: 12, paddingBottom: 24 }}>
            <Alert
                type="info"
                showIcon
                closable
                onClose={() => setPilotIntroCollapsed(true)}
                style={{
                    marginBottom: 16,
                    maxWidth: 800,
                    marginLeft: 'auto',
                    marginRight: 'auto',
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
                <div style={{ marginBottom: 8, maxWidth: 800, marginLeft: 'auto', marginRight: 'auto', textAlign: 'right' }}>
                    <Button type="link" size="small" onClick={() => setPilotIntroCollapsed(false)} style={{ padding: 0, fontSize: 12 }}>
                        显示产品说明
                    </Button>
                </div>
            )}
            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                size="large"
                items={[
                    {
                        key: 'customer',
                        label: (
                            <span>
                                <CustomerServiceOutlined /> 客户入口
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>— 客户</Text>
                            </span>
                        ),
                        children: <CustomerEntryTab onSwitchToBroker={handleSwitchToBroker} />,
                    },
                    {
                        key: 'broker',
                        label: (
                            <span>
                                <InboxOutlined /> {officeWorkbench}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>— {officeLabel}</Text>
                            </span>
                        ),
                        children: <BrokerWorkbenchTab initialCaseId={brokerInitialCaseId} clientId={clientId} />,
                    },
                ]}
            />
        </div>
    );
}
