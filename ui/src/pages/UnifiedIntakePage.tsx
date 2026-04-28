/**
 * Unified Intake MVP — Customer Entry + Broker Workbench
 *
 * Tab A: Customer Entry — customer-facing intake
 * Tab B: My requests — user-facing case list + progress (persisted cases)
 * Tab C: Broker Workbench — office tool for triage, case sheet, follow-up, and drafts
 * Tab D: Scenario replay (simulation)
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
    Dropdown,
    Input,
    Modal,
    Pagination,
    Radio,
    Row,
    Segmented,
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
    MoreOutlined,
    PaperClipOutlined,
    PlayCircleOutlined,
    ReloadOutlined,
    SendOutlined,
    SwapOutlined,
    UnorderedListOutlined,
    UploadOutlined,
} from '@ant-design/icons';
import { ScenarioReplayTab } from '../components/simulation/ScenarioReplayTab';
import { UserCaseListProgressPanel, userFacingCaseTitle } from '../components/intake/UserCaseListProgressPanel';
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
    fetchWeChatBindingStart,
    getInProgressSession,
    getOrCreateSessionId,
    getSessionId,
    getAttachmentDownloadUrl,
    deleteTestCase,
    listRecentCasesPage,
    patchCaseWorkbench,
    postWeChatBindingSimulateComplete,
    triageMessage,
    updateSavedCaseFollowUp,
    updateSavedCaseStatus,
    uploadCaseAttachment,
    type CaseStatus,
    type IdentityBindingState,
    type SavedCase,
    type SoftRouteIntent,
    type TriageResult,
    type WaitingOn,
} from '../api/inboxTriage';
import { copyToClipboard } from '../utils/demoCopy';
import { useClientConfig } from '../context/ClientConfigContext';
import type { UiCopy } from '../api/clientConfig';
import { API_BASE_URL } from '../api/config';
import {
    getOfficeCaseBoundaryListTag,
    getOfficeCaseBoundaryPresentation,
    getOfficeCaseBoundaryPreviewSuffix,
} from '../components/workbench/officeCaseBoundary';
import {
    caseLifecycleTagColor,
    caseLifecycleUserLabel,
    isAddCarReadyForFormalSubmit,
    resolveCaseLifecycle,
} from '../components/intake/caseLifecycleDisplay';

import type {
    BrokerWorkbenchTabProps,
    ConversationTurn,
    CustomerEntryTabProps,
    FollowUpDraft,
    WorkbenchListFilter,
} from '@/features/intake/types';
import {
    CASE_STATUS_OPTIONS,
    CUSTOMER_ENTRY_EXAMPLES,
    DEFAULT_QUICK_START_BUTTONS,
    FOUNDER_DEMO_QUEUE,
    QUICK_FILL_EXAMPLES,
    QUOTE_READY_STATUS_LABELS,
    WAITING_ON_OPTIONS,
} from '@/features/intake/constants';
import {
    addCarQueueStatusPhase,
    buildAddCarVehicleGlanceLine,
    buildOfficeWorkbenchGlance,
    composeAddCarStructuredIntakeMessage,
    customerEntryIsAddCarActive,
    formatDateLabel,
    formatPortalLocalDateTime,
    formatQueueCaseIdShort,
    formatWorkbenchApiEndpointLabel,
    getCaseAttentionState,
    getCaseFocusDisplayLabel,
    getCaseReportOneLiner,
    getCaseStatusColor,
    getCaseTrackingSummary,
    getCaseWorkbenchScore,
    getCompactQueuePreview,
    getCustomerFollowUpNote,
    getCustomerUrgencyNote,
    getDraftReadinessLabel,
    getDueStateLabel,
    getFollowUpDueTag,
    getFollowUpSummary,
    getLatestCaseContext,
    getLatestUpdateForDisplay,
    getOfficeLifecycleTag,
    getPreviewText,
    getQuickStartButtons,
    getQueueReadinessLabel,
    getRecentCustomerMessages,
    getResponseWindow,
    getUrgencyColor,
    hasSavedFollowUpTarget,
    hasWorkbenchOpsTags,
    humanizeCaseStatus,
    humanizeCategory,
    humanizeServiceLaneOffice,
    humanizeStructuredField,
    humanizeStructuredFieldForCustomer,
    humanizeUrgencyLabel,
    humanizeWaitingOn,
    inferCaseFocusFromStructuredFields,
    inferCaseFocusFromText,
    isWithinLast24Hours,
    needsHumanConfirmation,
    normalizeCaseSourceText,
    normalizeFollowUpText,
    orderCasesForWorkbench,
    passesWorkbenchListFilter,
    triageResultLooksLikeAddCar,
    workbenchLaneLabel,
    workbenchPgMirrorLabel,
    workbenchPgMirrorTagColor,
    workbenchPgMirrorTrustLine,
} from '@/features/intake/utils';
import { AddCarCaseStatusStrip, GenericIntakeStatusStrip, IntakeFlowStepTrack } from '@/features/intake/components/StatusStrips';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

/** Office queue list: server page size (must match API max limit). */
const WORKBENCH_PAGE_SIZE = 50;

/** Shared chrome width for unified intake (light island inside dark app shell). */
const UNIFIED_INTAKE_SHELL_MAX = 1280;

function UrgencyTag({ urgency }: { urgency: string }) {
    return <Tag color={getUrgencyColor(urgency)}>{humanizeUrgencyLabel(urgency)}</Tag>;
}

function CaseStatusTag({ status }: { status?: string }) {
    const opt = CASE_STATUS_OPTIONS.find((o) => o.value === status);
    return <Tag color={getCaseStatusColor(status)}>{opt?.label ?? humanizeCaseStatus(status)}</Tag>;
}

// =============================================================================
// CUSTOMER ENTRY TAB — Same-page conversational intake
// =============================================================================

function CustomerEntryTab({ onSwitchToBroker, onOpenScenarioSimulation, onOpenMyRequests }: CustomerEntryTabProps) {
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
    const [resumePortalHint, setResumePortalHint] = useState<{
        mode: 'none' | 'single' | 'multi';
        caseId?: string;
        title?: string;
    }>({ mode: 'none' });
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
    const [postHandoffBoundaryBlocked, setPostHandoffBoundaryBlocked] = useState<{
        reason: string;
        serviceType?: string;
        vehicleKey?: string | null;
    } | null>(null);
    /** LIGHT_IDENTITY_ENTRY_STUB — optional strip near formal submit (client-pack gated; not auth) */
    const [identityBindingState, setIdentityBindingState] = useState<IdentityBindingState>('unbound');
    const [identityWechatModalOpen, setIdentityWechatModalOpen] = useState(false);
    const [wechatBindingBusy, setWechatBindingBusy] = useState(false);
    const [identityStripDismissed, setIdentityStripDismissed] = useState(false);
    const loadingPlaceholderRef = useRef<HTMLDivElement>(null);
    const wechatBindingLive = uiCopy.light_identity?.wechat_binding_mode === 'live';

    useEffect(() => {
        try {
            setIdentityStripDismissed(sessionStorage.getItem(`unified_intake_li_dismiss_${clientId}`) === '1');
        } catch {
            setIdentityStripDismissed(false);
        }
    }, [clientId]);

    /** Empty-state: suggest continuing an in-progress Add-Car case (no forced modal). */
    useEffect(() => {
        if (turns.length > 0) {
            setResumePortalHint({ mode: 'none' });
            return;
        }
        let cancelled = false;
        void (async () => {
            try {
                const { cases } = await listRecentCasesPage({ limit: 15, offset: 0 });
                const visible = cases.filter((c) => {
                    if (c.workbench_test || c.workbench_archived) return false;
                    const cid = (c.client_id || '').trim();
                    if (cid && clientId && cid !== clientId) return false;
                    return true;
                });
                const ongoing = visible.filter(
                    (c) => triageResultLooksLikeAddCar(c) && resolveCaseLifecycle(c) !== 'submitted',
                );
                if (cancelled) return;
                if (ongoing.length >= 2) {
                    setResumePortalHint({ mode: 'multi', title: userFacingCaseTitle(ongoing[0]) });
                } else if (ongoing.length === 1) {
                    setResumePortalHint({
                        mode: 'single',
                        caseId: ongoing[0].case_id,
                        title: userFacingCaseTitle(ongoing[0]),
                    });
                } else {
                    setResumePortalHint({ mode: 'none' });
                }
            } catch {
                if (!cancelled) setResumePortalHint({ mode: 'none' });
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [turns.length, clientId]);

    const lastSystemTurnForFlowStep = useMemo(
        () => [...turns].reverse().find((t) => t.role === 'system'),
        [turns],
    );
    /** Quote-ready conversion: structural slots filled; only contact remains — chat-first, not formal-queue CTA. */
    const contactOnlyHandoffGap = useMemo(() => {
        const lt = lastSystemTurnForFlowStep?.triageResult;
        if (!customerEntryIsAddCarActive(turns, selectedButtonIntent)) return false;
        if (!lt || lt.quote_ready_status !== 'quote_ready') return false;
        if (!lt.conversion_layer_active) return false;
        const sn = lt.still_needed_fields?.filter(Boolean) ?? [];
        if (!sn.length) return false;
        return sn.every((f) => f === 'name' || f === 'phone');
    }, [turns, selectedButtonIntent, lastSystemTurnForFlowStep?.triageResult]);
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
        if (contactOnlyHandoffGap) {
            return uiCopy.portal_contact_only_primary_label ?? '发送消息（先回称呼/手机）';
        }
        if (addCarLaneActive && lt && isAddCarReadyForFormalSubmit(lt)) {
            return uiCopy.portal_submit_handoff_pending ?? '正式提交办公室';
        }
        return portalSubmitFollowup;
    }, [
        turns,
        selectedButtonIntent,
        lastSystemTurnForFlowStep?.triageResult,
        customerSubmitAddCarLabel,
        uiCopy.portal_submit_handoff_pending,
        uiCopy.portal_contact_only_primary_label,
        portalSubmitFollowup,
        contactOnlyHandoffGap,
    ]);

    const inputPlaceholderResolved = useMemo(() => {
        if (turns.length === 0) return portalInputEmpty;
        const addCarLaneActive = customerEntryIsAddCarActive(turns, selectedButtonIntent);
        const lt = lastSystemTurnForFlowStep?.triageResult;
        if (contactOnlyHandoffGap) {
            return (
                uiCopy.portal_contact_only_input_hint ??
                '请在本对话直接回复称呼与手机号；回完后再点「正式提交办公室」。'
            );
        }
        if (addCarLaneActive && lt && isAddCarReadyForFormalSubmit(lt)) {
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
        uiCopy.portal_contact_only_input_hint,
        contactOnlyHandoffGap,
    ]);

    const showHandoffPendingHint = useMemo(
        () =>
            customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
            isAddCarReadyForFormalSubmit(lastSystemTurnForFlowStep?.triageResult) &&
            !contactOnlyHandoffGap,
        [turns, selectedButtonIntent, lastSystemTurnForFlowStep?.triageResult, contactOnlyHandoffGap],
    );

    const preSubmitStillNeededFields = useMemo(
        () => lastSystemTurnForFlowStep?.triageResult?.still_needed_fields?.filter(Boolean) ?? [],
        [lastSystemTurnForFlowStep?.triageResult],
    );
    const showAddCarPreSubmitGapAlert = useMemo(
        () =>
            customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
            !formalSubmissionComplete &&
            preSubmitStillNeededFields.length > 0 &&
            !isAddCarReadyForFormalSubmit(lastSystemTurnForFlowStep?.triageResult),
        [
            turns,
            selectedButtonIntent,
            formalSubmissionComplete,
            preSubmitStillNeededFields.length,
            lastSystemTurnForFlowStep?.triageResult,
        ],
    );
    const showAddCarHandoffPendingGapAlert = useMemo(
        () =>
            showHandoffPendingHint &&
            preSubmitStillNeededFields.length > 0,
        [showHandoffPendingHint, preSubmitStillNeededFields.length],
    );

    const portalHandoffPendingCtaHint =
        uiCopy.portal_handoff_pending_cta_hint ??
        '当前为「资料已齐 · 待正式提交」：下方按钮将把本条服务记录送达办公室，不是普通「继续补充」。若还要改要点，请先写在输入框再与提交一并送达。';

    const lightIdentityStripLine = useMemo(() => {
        const custom = uiCopy.light_identity?.strip_primary_line?.trim();
        if (custom) return custom;
        if (uiCopy.light_identity?.binding_copy_profile === 'wechat_preferred') {
            return '若希望下次更容易在同一入口继续本条进展，可预留微信（可选，不等同于登录）。';
        }
        return '若希望便于后续跟进，可预留联系方式（可选）。';
    }, [uiCopy.light_identity?.binding_copy_profile, uiCopy.light_identity?.strip_primary_line]);

    const lightIdentityWechatCta = uiCopy.light_identity?.wechat_cta_label?.trim() || '微信续接（可选）';
    const lightIdentityDeferCta = uiCopy.light_identity?.defer_cta_label?.trim() || '下次再说';
    const lightIdentityDismissCta = uiCopy.light_identity?.dismiss_cta_label?.trim() || '不再显示';
    const lightIdentityModalTitle = uiCopy.light_identity?.modal_title?.trim() || '微信续接（演示占位）';
    const lightIdentityModalBody =
        uiCopy.light_identity?.modal_body?.trim() ||
        '真实微信绑定尚未接入。后续接入后用于在同一入口延续本条服务记录；此处不收集账号，也不是登录门槛。';
    const lightIdentityPhoneEmailHint =
        uiCopy.light_identity?.phone_email_fallback_hint?.trim() || '手机 / 邮箱等方式将后续支持';

    const dismissIdentityStrip = () => {
        try {
            sessionStorage.setItem(`unified_intake_li_dismiss_${clientId}`, '1');
        } catch {
            /* ignore */
        }
        setIdentityStripDismissed(true);
    };

    const lightIdentityModalBodyLive =
        '将前往微信授权页面，完成后返回本入口。仅用于续接本条办理进度（非登录）；正式提交仍需按规则填写业务联系信息。';

    const handleWeChatBindingStart = async () => {
        const sid = getOrCreateSessionId();
        if (!sid) {
            message.error('无法建立会话，请刷新后重试。');
            return;
        }
        setWechatBindingBusy(true);
        try {
            const r = await fetchWeChatBindingStart(sid, clientId);
            if (r.dev_simulate) {
                await postWeChatBindingSimulateComplete(sid, clientId);
                setIdentityBindingState('linked');
                message.success('微信续接已记录（开发模拟）。正式提交后将写入服务记录。');
                setIdentityWechatModalOpen(false);
                return;
            }
            if (r.authorize_url) {
                window.location.assign(r.authorize_url);
                return;
            }
            message.error('未返回授权地址。');
        } catch (e: unknown) {
            const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            message.error(typeof detail === 'string' ? detail : '无法开始微信续接');
        } finally {
            setWechatBindingBusy(false);
        }
    };

    /** Return from WeChat OAuth / simulate: query flags + clean URL */
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const wb = params.get('wechat_binding');
        if (wb === 'linked') {
            message.success('微信续接已记录（可选）。正式提交后将写入本条服务记录。', 4);
            setIdentityBindingState('linked');
            params.delete('wechat_binding');
            params.delete('reason');
            const q = params.toString();
            window.history.replaceState({}, '', `${window.location.pathname}${q ? `?${q}` : ''}`);
        } else if (wb === 'error') {
            message.warning('微信续接未完成，可稍后重试或跳过；不影响正式提交。', 4);
            params.delete('wechat_binding');
            params.delete('reason');
            const q = params.toString();
            window.history.replaceState({}, '', `${window.location.pathname}${q ? `?${q}` : ''}`);
        }
    }, []);

    /** In-progress persistence: restore conversation on mount when session_id exists */
    useEffect(() => {
        const sid = getSessionId();
        if (!sid) return;
        getInProgressSession(sid).then((data) => {
            if (data?.light_identity_binding?.identity_binding_state === 'linked') {
                setIdentityBindingState('linked');
            }
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
            const snFormal = ltFormal?.still_needed_fields?.filter(Boolean) ?? [];
            const contactOnlyFormal =
                !!ltFormal &&
                ltFormal.quote_ready_status === 'quote_ready' &&
                !!ltFormal.conversion_layer_active &&
                snFormal.length > 0 &&
                snFormal.every((f) => f === 'name' || f === 'phone');
            const formalSubmit =
                addCarLaneActive &&
                ltFormal &&
                isAddCarReadyForFormalSubmit(ltFormal) &&
                !contactOnlyFormal;
            const lightIdentityEnabled = Boolean(uiCopy.light_identity?.show_optional_binding);
            const identityPayload =
                formalSubmit && lightIdentityEnabled
                    ? { identity_binding_state: identityBindingState }
                    : undefined;
            const data = await triageMessage(
                trimmed,
                true,
                conversationTurnsForApi,
                softRoute ?? undefined,
                undefined,
                clientId,
                formalSubmit,
                lastCaseId,
                identityPayload,
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
                    addCarFlow && isAddCarReadyForFormalSubmit(data);
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
            addCarLaneActive && lt && isAddCarReadyForFormalSubmit(lt) && !contactOnlyHandoffGap;
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
        setPostHandoffBoundaryBlocked(null);
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
            if (updated.append_blocked_new_issue && updated.case_boundary_action === 'requires_new_case') {
                const sysReply = (updated.client_reply_draft || '').trim() || handoffDefault;
                setTurns((prev) => [
                    ...prev,
                    { role: 'customer', content: text },
                    { role: 'system', content: sysReply, triageResult: updated as TriageResult },
                ]);
                setPostHandoffBoundaryBlocked({
                    reason: updated.boundary_reason || '系统判断这条消息属于新事项，不应追加到当前记录。',
                    serviceType: updated.service_type,
                    vehicleKey: updated.vehicle_key,
                });
                setPostHandoffAppendDraft('');
                message.warning('未追加到原服务记录：系统判断这是新事项，请点击「提交新问题」单独发起。');
                return;
            }
            setPostHandoffBoundaryBlocked(null);
            const sysReply = (updated.client_reply_draft || '').trim() || handoffDefault;
            setTurns((prev) => [
                ...prev,
                { role: 'customer', content: text },
                { role: 'system', content: sysReply, triageResult: updated as TriageResult },
            ]);
            setPostHandoffAppendDraft('');
            if (updated.case_boundary === 'borderline') {
                message.info('已追加并落库。边界不够明确时，办公室建议再确认是否仍属同一条事项。');
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
                            {resumePortalHint.mode === 'single' && resumePortalHint.caseId && (
                                <div
                                    style={{
                                        marginTop: 10,
                                        paddingTop: 10,
                                        borderTop: '1px solid #f0f0f0',
                                    }}
                                >
                                    <Text type="secondary" style={{ fontSize: 12, display: 'block', lineHeight: 1.55 }}>
                                        继续上次的申请：{resumePortalHint.title}
                                    </Text>
                                    <Button
                                        type="link"
                                        size="small"
                                        style={{ padding: 0, height: 'auto', marginTop: 4 }}
                                        onClick={() => {
                                            setLastCaseId(resumePortalHint.caseId);
                                            setSelectedButtonIntent('add_car');
                                        }}
                                    >
                                        用这条记录继续
                                    </Button>
                                </div>
                            )}
                            {resumePortalHint.mode === 'multi' && (
                                <div
                                    style={{
                                        marginTop: 10,
                                        paddingTop: 10,
                                        borderTop: '1px solid #f0f0f0',
                                    }}
                                >
                                    <Text type="secondary" style={{ fontSize: 12, display: 'block', lineHeight: 1.55 }}>
                                        您有多条进行中的请求。到「我的办理」选择要继续的一条即可。
                                    </Text>
                                    {onOpenMyRequests ? (
                                        <Button
                                            type="link"
                                            size="small"
                                            style={{ padding: 0, height: 'auto', marginTop: 4 }}
                                            onClick={() => onOpenMyRequests()}
                                        >
                                            打开我的办理
                                        </Button>
                                    ) : null}
                                </div>
                            )}
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
                                {(() => {
                                    const addCarBtn =
                                        quickStartButtons.find((b) => b.id === 'add_car') ??
                                        DEFAULT_QUICK_START_BUTTONS.find((b) => b.id === 'add_car')!;
                                    const talkBtn =
                                        quickStartButtons.find((b) => b.id === 'talk_to_agent') ??
                                        DEFAULT_QUICK_START_BUTTONS.find((b) => b.id === 'talk_to_agent')!;
                                    const more = quickStartButtons.filter((b) => !['add_car', 'talk_to_agent'].includes(b.id));
                                    const moreItems = more.map((b) => ({
                                        key: b.id,
                                        label: b.label,
                                        onClick: () => handleButtonStarter(b),
                                    }));
                                    const addCarPrimary = selectedButtonIntent === 'add_car' || selectedButtonIntent === null;
                                    const talkPrimary = selectedButtonIntent === 'talk_to_agent';
                                    return (
                                        <Row gutter={[12, 12]} align="middle">
                                            <Col xs={24} sm={12} md={8}>
                                                <Button
                                                    type={addCarPrimary ? 'primary' : 'default'}
                                                    onClick={() => handleButtonStarter(addCarBtn)}
                                                    loading={loading}
                                                    size="large"
                                                    block
                                                    style={
                                                        addCarPrimary
                                                            ? { backgroundColor: '#1677ff', borderColor: '#1677ff' }
                                                            : { borderColor: '#d9d9d9', color: '#262626', background: '#fff' }
                                                    }
                                                >
                                                    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
                                                        {addCarBtn.label}
                                                        {selectedButtonIntent === null ? (
                                                            <Tag color="processing" style={{ margin: 0, fontSize: 11 }}>
                                                                {uiCopy.portal_add_car_button_badge ?? '推荐主路径'}
                                                            </Tag>
                                                        ) : null}
                                                    </span>
                                                </Button>
                                            </Col>
                                            <Col xs={24} sm={12} md={8}>
                                                <Button
                                                    type={talkPrimary ? 'primary' : 'default'}
                                                    onClick={() => handleButtonStarter(talkBtn)}
                                                    loading={loading}
                                                    size="large"
                                                    block
                                                    style={
                                                        talkPrimary
                                                            ? { backgroundColor: '#1677ff', borderColor: '#1677ff' }
                                                            : { borderColor: '#d9d9d9', color: '#262626', background: '#fff' }
                                                    }
                                                >
                                                    {talkBtn.label}
                                                </Button>
                                            </Col>
                                            <Col xs={24} md={8}>
                                                <Dropdown
                                                    trigger={['click']}
                                                    menu={{
                                                        items: moreItems,
                                                    }}
                                                >
                                                    <Button size="large" block icon={<MoreOutlined />}>
                                                        其他事项（可选）
                                                    </Button>
                                                </Dropdown>
                                            </Col>
                                        </Row>
                                    );
                                })()}
                            </div>
                            {/* Hybrid add-car: structured short card + same conversational pipeline (flagship hardening) */}
                            <div
                                style={{
                                    marginTop: 8,
                                    paddingTop: 16,
                                    borderTop: '1px solid #f0f0f0',
                                }}
                            >
                                <Collapse
                                    bordered={false}
                                    style={{ background: 'transparent' }}
                                    items={[
                                        {
                                            key: 'add_car_quick',
                                            label: (
                                                <Text strong style={{ fontSize: 14, color: '#262626' }}>
                                                    {portalAddCarQuickTitle}
                                                </Text>
                                            ),
                                            children: (
                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
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
                                                        style={{ marginTop: 4 }}
                                                        onClick={handleStartWithAddCarStructured}
                                                        loading={loading}
                                                        disabled={loading}
                                                    >
                                                        {portalAddCarQuickCta}
                                                    </Button>
                                                </Space>
                                            ),
                                        },
                                    ]}
                                />
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
                            : addCarActiveHere && latestTriage && isAddCarReadyForFormalSubmit(latestTriage)
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
                                                {turn.triageResult && (
                                                    <Tag
                                                        color={caseLifecycleTagColor(resolveCaseLifecycle(turn.triageResult))}
                                                        style={{ fontSize: 11 }}
                                                    >
                                                        {caseLifecycleUserLabel(resolveCaseLifecycle(turn.triageResult))}
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
                                {latestTriage && !addCarActiveHere && (
                                    <Tag
                                        color={caseLifecycleTagColor(resolveCaseLifecycle(latestTriage))}
                                        style={{ fontSize: 10 }}
                                    >
                                        {caseLifecycleUserLabel(resolveCaseLifecycle(latestTriage))}
                                    </Tag>
                                )}
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
                                    可先点选办理类型，或直接输入说明；提交后办公室按记录跟进。
                                </Text>
                            )}
                            {showHandoffPendingHint && (
                                <Alert
                                    type="info"
                                    showIcon
                                    message={uiCopy.portal_handoff_pending_alert_title ?? '资料已齐 · 待正式送达办公室'}
                                    description={
                                        <Text style={{ fontSize: 13, lineHeight: 1.55, margin: 0 }}>
                                            {portalHandoffPendingCtaHint}
                                        </Text>
                                    }
                                />
                            )}
                            {showHandoffPendingHint &&
                                uiCopy.light_identity?.show_optional_binding &&
                                !identityStripDismissed && (
                                    <div
                                        style={{
                                            padding: '6px 0 2px',
                                            borderTop: '1px solid #f0f0f0',
                                        }}
                                    >
                                        <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.65, display: 'block' }}>
                                            {lightIdentityStripLine}{' '}
                                            <Button
                                                type="link"
                                                size="small"
                                                style={{ padding: 0, height: 'auto', fontSize: 12 }}
                                                onClick={() => {
                                                    setIdentityBindingState('prompted');
                                                    setIdentityWechatModalOpen(true);
                                                }}
                                            >
                                                {lightIdentityWechatCta}
                                            </Button>
                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                {' · '}
                                            </Text>
                                            <Button
                                                type="link"
                                                size="small"
                                                style={{ padding: 0, height: 'auto', fontSize: 12 }}
                                                onClick={() => setIdentityBindingState('deferred')}
                                            >
                                                {lightIdentityDeferCta}
                                            </Button>
                                            <Text type="secondary" style={{ fontSize: 12 }}>
                                                {' · '}
                                            </Text>
                                            <Button
                                                type="link"
                                                size="small"
                                                style={{ padding: 0, height: 'auto', fontSize: 12 }}
                                                onClick={dismissIdentityStrip}
                                            >
                                                {lightIdentityDismissCta}
                                            </Button>
                                        </Text>
                                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
                                            {lightIdentityPhoneEmailHint}
                                        </Text>
                                    </div>
                                )}
                            <Modal
                                title={
                                    wechatBindingLive
                                        ? uiCopy.light_identity?.modal_title?.trim() || '微信续接（可选）'
                                        : lightIdentityModalTitle
                                }
                                open={identityWechatModalOpen}
                                onCancel={() => setIdentityWechatModalOpen(false)}
                                footer={
                                    wechatBindingLive ? (
                                        <>
                                            <Button key="cancel" onClick={() => setIdentityWechatModalOpen(false)}>
                                                取消
                                            </Button>
                                            <Button
                                                key="go"
                                                type="primary"
                                                loading={wechatBindingBusy}
                                                onClick={() => void handleWeChatBindingStart()}
                                            >
                                                开始微信续接
                                            </Button>
                                        </>
                                    ) : (
                                        [
                                            <Button
                                                key="ok"
                                                type="primary"
                                                onClick={() => setIdentityWechatModalOpen(false)}
                                            >
                                                知道了
                                            </Button>,
                                        ]
                                    )
                                }
                            >
                                <Paragraph style={{ marginBottom: 0 }}>
                                    {wechatBindingLive ? lightIdentityModalBodyLive : lightIdentityModalBody}
                                </Paragraph>
                            </Modal>
                            {showAddCarPreSubmitGapAlert && (
                                <Alert
                                    type="warning"
                                    showIcon
                                    message="提交前 · 系统仍标注这些待补项"
                                    description={
                                        <div>
                                            <Text style={{ fontSize: 13, lineHeight: 1.55, display: 'block', marginBottom: 8 }}>
                                                建议先在下方输入框补充说明（写入同一条服务记录），减少办公室来回追问。若暂时只能先聊到这一步，也可继续发送消息后再等系统标为可提交。
                                            </Text>
                                            <Space size={4} wrap>
                                                {preSubmitStillNeededFields.slice(0, 8).map((f) => (
                                                    <Tag key={f} color="orange">
                                                        {humanizeStructuredFieldForCustomer(f)}
                                                    </Tag>
                                                ))}
                                                {preSubmitStillNeededFields.length > 8 ? <Tag>…</Tag> : null}
                                            </Space>
                                        </div>
                                    }
                                />
                            )}
                            {showAddCarHandoffPendingGapAlert && (
                                <Alert
                                    type="info"
                                    showIcon
                                    message="仍可补充后再正式提交"
                                    description={
                                        <div>
                                            <Text style={{ fontSize: 13, lineHeight: 1.55, display: 'block', marginBottom: 8 }}>
                                                系统已标「资料已齐」，但仍有结构化待补项。若方便，请先在输入框写好再点正式提交，办公室接手时更省事。
                                            </Text>
                                            <Space size={4} wrap>
                                                {preSubmitStillNeededFields.slice(0, 8).map((f) => (
                                                    <Tag key={f} color="orange">
                                                        {humanizeStructuredFieldForCustomer(f)}
                                                    </Tag>
                                                ))}
                                            </Space>
                                        </div>
                                    }
                                />
                            )}
                            {customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
                                !formalSubmissionComplete &&
                                contactOnlyHandoffGap && (
                                    <Alert
                                        type="info"
                                        showIcon
                                        message={uiCopy.conversion_ui_ready_title ?? '报价信息已就绪'}
                                        description={
                                            <Text style={{ fontSize: 13, lineHeight: 1.55, margin: 0 }}>
                                                {uiCopy.portal_contact_only_input_hint ??
                                                    '请在本对话直接回复称呼与手机号；回完后再点「正式提交办公室」。'}
                                            </Text>
                                        }
                                    />
                                )}
                            {customerEntryIsAddCarActive(turns, selectedButtonIntent) &&
                                !formalSubmissionComplete &&
                                !contactOnlyHandoffGap &&
                                (() => {
                                    const msg =
                                        lastSystemTurnForFlowStep?.triageResult?.case_draft?.completion_message?.trim() ??
                                        '';
                                    if (!msg) return null;
                                    return <Alert type="success" showIcon message={msg} />;
                                })()}
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
                                                        {postHandoffBoundaryBlocked && (
                                                            <Alert
                                                                type="warning"
                                                                showIcon
                                                                message="检测到新事项，未写入当前记录"
                                                                description={
                                                                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                                                                        <Text style={{ fontSize: 12 }}>
                                                                            {postHandoffBoundaryBlocked.reason}
                                                                        </Text>
                                                                        <Button type="primary" onClick={handleNewConversation}>
                                                                            提交新问题
                                                                        </Button>
                                                                    </Space>
                                                                }
                                                            />
                                                        )}
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

function OfficeWorkbenchOneGlanceSummary({
    triage,
    inputFallback,
    uiCopy,
}: {
    triage: TriageResult;
    inputFallback: string;
    uiCopy: UiCopy;
}) {
    const g = buildOfficeWorkbenchGlance(triage, inputFallback);
    const addCar = triageResultLooksLikeAddCar(triage);
    const formal = addCar && addCarQueueStatusPhase(triage) === 'submitted';
    const u = uiCopy;
    const qFormal = u.office_workbench_formal_to_office_question ?? '正式送达办公室';
    const yes = u.office_workbench_formal_to_office_yes ?? '是';
    const no = u.office_workbench_formal_to_office_no ?? '否';
    const stateLabel = u.office_workbench_current_handoff_state_label ?? '当前接手状态';
    const lt = addCar ? getOfficeLifecycleTag(triage.lifecycle_status) : null;

    return (
        <div
            style={{
                marginBottom: 4,
                padding: 14,
                borderRadius: 8,
                border: '1px solid #d6e4ff',
                borderLeft: '4px solid #2f54eb',
                background: 'linear-gradient(180deg, #f0f5ff 0%, #ffffff 100%)',
            }}
        >
            <Text strong style={{ fontSize: 13, color: '#1d39c4', display: 'block', marginBottom: 4 }}>
                整理结果（办公室一眼）· 三步扫读
            </Text>
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 12, lineHeight: 1.45 }}>
                系统已把客户原文整理为可接手结论；需要核对原文时在下方「完整对话」展开。
            </Text>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                {g.missingLine ? (
                    <div
                        style={{
                            padding: '10px 12px',
                            borderRadius: 8,
                            background: '#fff7e6',
                            border: '1px solid #ffd591',
                            borderLeft: '4px solid #fa8c16',
                        }}
                    >
                        <Text strong style={{ fontSize: 12, color: '#ad4e00', display: 'block', marginBottom: 4 }}>
                            还缺什么（首要）
                        </Text>
                        <Text style={{ fontSize: 14, color: '#434343', lineHeight: 1.55, display: 'block' }}>{g.missingLine}</Text>
                    </div>
                ) : null}
                <div>
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ① 案子（谁 · 办什么）
                    </Text>
                    <Text style={{ fontSize: 13, color: '#262626', display: 'block', lineHeight: 1.55 }}>{g.contactLine}</Text>
                    <Text style={{ fontSize: 13, color: '#262626', display: 'block', lineHeight: 1.55 }}>{g.matterLine}</Text>
                    {g.vehicleLine ? (
                        <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55 }}>{g.vehicleLine}</Text>
                    ) : null}
                </div>

                <div
                    style={{
                        padding: 10,
                        borderRadius: 8,
                        background: 'rgba(0, 0, 0, 0.02)',
                        border: '1px solid #f0f0f0',
                    }}
                >
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ② 状态与缺口（信任）
                    </Text>
                    <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55 }}>{g.stageLine}</Text>
                    {addCar ? (
                        <div
                            style={{
                                marginTop: 8,
                                display: 'flex',
                                flexWrap: 'wrap',
                                alignItems: 'center',
                                gap: 8,
                            }}
                        >
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                {qFormal}：
                            </Text>
                            <Tag color={formal ? 'success' : 'warning'}>{formal ? yes : no}</Tag>
                            {lt ? (
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    {stateLabel}：{lt.label}
                                </Text>
                            ) : null}
                        </div>
                    ) : null}
                    {g.quotePrepLine ? (
                        <Text style={{ fontSize: 13, color: '#434343', display: 'block', lineHeight: 1.55, marginTop: 8 }}>
                            {g.quotePrepLine}
                        </Text>
                    ) : null}
                    {!g.missingLine ? (
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                            结构化缺项：当前未标「还缺」（仍以办公室核实为准）
                        </Text>
                    ) : (
                        <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 8 }}>
                            字段级明细可在下方「结构化字段」展开核对。
                        </Text>
                    )}
                </div>

                <div style={{ paddingTop: 4, borderTop: '1px solid #e6ebf5' }}>
                    <Text
                        type="secondary"
                        style={{ fontSize: 11, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}
                    >
                        ③ 行动与对外
                    </Text>
                    {g.latestCustomerLine ? (
                        <Text
                            type="secondary"
                            style={{ fontSize: 11, display: 'block', lineHeight: 1.45, marginBottom: 8 }}
                        >
                            {g.latestCustomerLine}
                        </Text>
                    ) : null}
                    <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                        主行动（办公室）
                    </Text>
                    <Text strong style={{ fontSize: 15, color: '#10239e', lineHeight: 1.5, display: 'block' }}>
                        {g.nextStep}
                    </Text>
                    {(() => {
                        const hasFu = hasSavedFollowUpTarget(triage);
                        const due = getFollowUpDueTag(triage.next_contact_by);
                        const wo = triage.waiting_on ?? 'none';
                        const ncb = normalizeFollowUpText(triage.next_contact_by);
                        if (!hasFu) return null;
                        return (
                            <div
                                style={{
                                    marginTop: 10,
                                    padding: '8px 10px',
                                    borderRadius: 6,
                                    background: due?.kind === 'overdue'
                                        ? 'rgba(255, 77, 79, 0.06)'
                                        : due?.kind === 'due_today'
                                          ? 'rgba(250, 140, 22, 0.08)'
                                          : 'rgba(24, 144, 255, 0.06)',
                                    border: '1px solid #f0f0f0',
                                }}
                            >
                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                    跟进计划（与主行动对齐）
                                </Text>
                                <Space wrap size={[4, 4]}>
                                    {due ? <Tag color={due.color}>{due.label}</Tag> : null}
                                    {wo !== 'none' ? (
                                        <Tag color="purple">在等：{humanizeWaitingOn(wo)}</Tag>
                                    ) : null}
                                    {ncb ? (
                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                            下次跟进：{ncb}
                                        </Text>
                                    ) : null}
                                </Space>
                            </div>
                        );
                    })()}
                    {(() => {
                        const d = (triage.client_reply_draft ?? '').trim();
                        if (!d) return null;
                        return (
                            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 10, lineHeight: 1.5 }}>
                                客户草稿预览：{getPreviewText(d, 96)}
                            </Text>
                        );
                    })()}
                </div>
            </Space>
        </div>
    );
}

function BrokerWorkbenchTab({ initialCaseId, clientId: clientIdProp }: BrokerWorkbenchTabProps) {
    const { uiCopy, clientId: contextClientId } = useClientConfig();
    const clientId = clientIdProp ?? contextClientId;
    const officeWorkbench = uiCopy.office_workbench ?? '办公室工作台';
    const officeWorkbenchSubtitle =
        uiCopy.office_workbench_subtitle ??
        '先从队列选案，再看结论，最后执行下一步动作。';
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
    const officeActiveCaseLabel = uiCopy.office_workbench_active_case_label ?? '当前处理';
    const officeQueueOpenAnchorPrefix = uiCopy.office_workbench_queue_open_anchor_prefix ?? '当前打开';
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
    const [recentLoading, setRecentLoading] = useState(true);
    const [statusSaving, setStatusSaving] = useState(false);
    const [noteSaving, setNoteSaving] = useState(false);
    const [followUpSaving, setFollowUpSaving] = useState(false);
    const [appendMessageDraft, setAppendMessageDraft] = useState('');
    const [appendSaving, setAppendSaving] = useState(false);
    const [attachmentUploading, setAttachmentUploading] = useState(false);
    const [demoQueueLoading, setDemoQueueLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [workbenchListFilter, setWorkbenchListFilter] = useState<WorkbenchListFilter>('all');
    const [workbenchPageIndex, setWorkbenchPageIndex] = useState(0);
    const [workbenchTotalCount, setWorkbenchTotalCount] = useState(0);
    /** Last successful GET /api/inbox/cases page load (office trust: "is this list current?"). */
    const [workbenchQueueLoadedAtIso, setWorkbenchQueueLoadedAtIso] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const recentCasesSectionRef = useRef<HTMLDivElement>(null);

    const activeExample = useMemo(
        () => QUICK_FILL_EXAMPLES.find((example) => example.text === input.trim()) ?? null,
        [input],
    );
    const workbenchFilteredCases = useMemo(
        () => recentCases.filter((c) => passesWorkbenchListFilter(c, workbenchListFilter)),
        [recentCases, workbenchListFilter],
    );
    const actionNowCases = useMemo(
        () => workbenchFilteredCases.filter((savedCase) => getCaseAttentionState(savedCase).section === 'action'),
        [workbenchFilteredCases],
    );
    const trackingCases = useMemo(
        () => workbenchFilteredCases.filter((savedCase) => getCaseAttentionState(savedCase).section !== 'action'),
        [workbenchFilteredCases],
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
    const workbenchPgMirrorTrust = useMemo(() => workbenchPgMirrorTrustLine(recentCases), [recentCases]);

    const loadRecent = async (opts?: { page?: number }) => {
        const page = opts?.page ?? workbenchPageIndex;
        if (opts?.page !== undefined) {
            setWorkbenchPageIndex(opts.page);
        }
        setRecentLoading(true);
        try {
            const { cases, total_count } = await listRecentCasesPage({
                limit: WORKBENCH_PAGE_SIZE,
                offset: page * WORKBENCH_PAGE_SIZE,
            });
            setRecentCases(orderCasesForWorkbench(cases));
            setWorkbenchTotalCount(total_count);
            setWorkbenchQueueLoadedAtIso(new Date().toISOString());
        } catch (e: unknown) {
            const ax = e as { response?: { data?: { detail?: string } }; message?: string; code?: string };
            const raw =
                ax?.response?.data?.detail ?? ax?.message ?? 'Could not load recent cases.';
            const msg =
                typeof raw === 'string' && /network error/i.test(raw)
                    ? `${raw}（若控制台有 CORS 提示，请确认地址栏域名与后端 ALLOWED_ORIGINS 一致，优先打开生产别名 URL。）`
                    : raw;
            setError((current) => current ?? String(msg));
            message.error(String(msg));
        } finally {
            setRecentLoading(false);
        }
    };

    useEffect(() => {
        void loadRecent({ page: 0 });
        // eslint-disable-next-line react-hooks/exhaustive-deps -- initial queue load only
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
            setInput('');
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
        // Workbench safety: if an existing saved case is already opened from the queue,
        // do not allow "开始整理" to create a second persisted record for the same item.
        if (caseView === 'reopened' && (currentCase?.case_id ?? '').trim()) {
            message.info('已打开本条服务记录。如需补充，请使用下方「追加客户补充」或更新跟进信息。');
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
                message.success('服务记录已保存到队列');
                await loadRecent({ page: 0 });
            } else {
                message.warning('已整理，但未写入队列（请检查网络或稍后重试）');
            }
            setInput('');
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
        setInput('');
        setCaseView('reopened');
        setCurrentCase(savedCase);
        setNoteDraft('');
        setAppendMessageDraft('');
        setError(null);
    };

    const handlePatchWorkbench = async (caseId: string, patch: { is_test?: boolean; archived?: boolean }) => {
        try {
            const updated = await patchCaseWorkbench(caseId, patch);
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== caseId)]));
            if (currentCase?.case_id === caseId) {
                setCurrentCase(updated);
            }
            message.success('已保存');
        } catch (e: unknown) {
            const msg =
                (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? '更新失败';
            message.error(msg);
        }
    };

    const handleDeleteTestCase = (caseId: string) => {
        Modal.confirm({
            title: '删除此测试记录？',
            content:
                '将从持久化队列中移除（不可恢复）。正式记录请使用「归档隐藏」；仅已标为测试的记录可删除。',
            okText: '删除',
            okType: 'danger',
            cancelText: '取消',
            onOk: async () => {
                try {
                    await deleteTestCase(caseId);
                    message.success('已删除测试记录');
                    if (currentCase?.case_id === caseId) {
                        setCurrentCase(null);
                        setCaseView('new');
                    }
                    await loadRecent({ page: workbenchPageIndex });
                } catch (e: unknown) {
                    const msg =
                        (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                        ?? (e as { message?: string })?.message
                        ?? '删除失败';
                    message.error(msg);
                }
            },
        });
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
        const textFallback = (input.trim() || currentCase.source_text || '').trim();
        const glance = buildOfficeWorkbenchGlance(currentCase, textFallback);
        const focus =
            inferCaseFocusFromStructuredFields(
                currentCase.collected_fields,
                currentCase.still_needed_fields,
                currentCase.issue_category,
            ) ?? inferCaseFocusFromText(currentCase.source_text ?? textFallback);
        const lines: string[] = [];
        const focusDisplay = focus ? (getCaseFocusDisplayLabel(focus) ?? focus) : null;
        lines.push(`【服务记录摘要】`);
        lines.push(glance.contactLine);
        lines.push(glance.matterLine);
        lines.push(glance.stageLine);
        if (glance.vehicleLine) lines.push(glance.vehicleLine);
        if (glance.quotePrepLine) lines.push(glance.quotePrepLine);
        if (glance.missingLine) lines.push(glance.missingLine);
        if (glance.latestCustomerLine) lines.push(glance.latestCustomerLine);
        lines.push(`建议办公室下一步：${glance.nextStep}`);
        lines.push(`—`);
        lines.push(`事项（结构化）：${focusDisplay ?? '—'}`);
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
        if (ok) message.success('摘要已复制');
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

            await loadRecent({ page: 0 });
            if (openedCase) {
                setCurrentCase(openedCase);
                setCaseView('reopened');
                setInput('');
            } else if (strongestExistingCase) {
                setCurrentCase(strongestExistingCase);
                setCaseView('reopened');
                setInput('');
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
            if (updated.append_blocked_new_issue && updated.case_boundary_action === 'requires_new_case') {
                message.warning('未更新原记录：该消息被判定为新事项，请新开一条服务记录。');
                setAppendMessageDraft('');
                return;
            }
            setCurrentCase(updated);
            setInput('');
            setAppendMessageDraft('');
            setRecentCases((cases) => orderCasesForWorkbench([updated, ...cases.filter((item) => item.case_id !== updated.case_id)]));
            if (updated.case_boundary === 'borderline') {
                message.info('已追加并落库。边界不够明确时，请在详情区查看「案件边界」建议。');
            } else {
                message.success('已用客户新消息更新本条服务记录');
            }
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
        const isActive = currentCase?.case_id === savedCase.case_id;
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
                styles={{ body: { padding: 14 } }}
                style={{
                    background: isActive ? '#e6f4ff' : '#ffffff',
                    border: isActive ? '1px solid #91caff' : '1px solid #c9c9c9',
                    borderLeft: isActive ? '4px solid #1677ff' : undefined,
                    borderRadius: 10,
                    boxShadow: isActive
                        ? '0 0 0 1px rgba(22, 119, 255, 0.2), 0 2px 8px rgba(22, 119, 255, 0.08)'
                        : '0 1px 3px rgba(0, 0, 0, 0.05)',
                }}
            >
                <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    {isActive && (
                        <Text
                            style={{
                                fontSize: 12,
                                fontWeight: 600,
                                color: '#1677ff',
                                letterSpacing: 0.2,
                                display: 'block',
                                lineHeight: 1.2,
                            }}
                        >
                            {officeActiveCaseLabel}
                        </Text>
                    )}
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
                        <UrgencyTag urgency={savedCase.urgency} />
                        <span
                            style={
                                !isActive
                                    ? { opacity: 0.66, display: 'inline-flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }
                                    : { display: 'inline-flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }
                            }
                        >
                            {!triageResultLooksLikeAddCar(savedCase) &&
                                (() => {
                                    const lt = getOfficeLifecycleTag(savedCase.lifecycle_status);
                                    return lt ? (
                                        <Tag color={lt.color} style={{ fontSize: 10 }}>
                                            {lt.label}
                                        </Tag>
                                    ) : null;
                                })()}
                            {(() => {
                                const bt = getOfficeCaseBoundaryListTag(savedCase);
                                return bt ? (
                                    <Tag color={bt.color}>{bt.label}</Tag>
                                ) : null;
                            })()}
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
                            {!caseFocus && <Tag>{humanizeCategory(savedCase.issue_category, savedCase.source_text)}</Tag>}
                        </span>
                    </Space>
                    {triageResultLooksLikeAddCar(savedCase) && (savedCase.still_needed_fields?.filter(Boolean).length ?? 0) > 0 && (
                        <Text style={{ fontSize: 12, color: '#d46b08', lineHeight: 1.5, display: 'block' }}>
                            待补问：
                            {savedCase
                                .still_needed_fields!.filter(Boolean)
                                .slice(0, 5)
                                .map((f) => humanizeStructuredField(f))
                                .join('、')}
                            {(savedCase.still_needed_fields!.filter(Boolean).length ?? 0) > 5 ? '…' : ''}
                        </Text>
                    )}
                    {hasWorkbenchOpsTags(savedCase) && (
                        <Space
                            wrap
                            size={[4, 4]}
                            align="center"
                            style={!isActive ? { opacity: 0.72 } : undefined}
                        >
                            <Text type="secondary" style={{ fontSize: 11 }}>
                                工作台
                            </Text>
                            {savedCase.workbench_test ? <Tag color="orange">测试</Tag> : null}
                            {savedCase.workbench_archived ? <Tag>已归档</Tag> : null}
                            {savedCase.workbench_lane_kind ? (
                                <Tag style={{ fontSize: 10 }}>{workbenchLaneLabel(savedCase.workbench_lane_kind)}</Tag>
                            ) : null}
                            {savedCase.pg_mirror_state ? (
                                <Tag color={workbenchPgMirrorTagColor(savedCase.pg_mirror_state)} style={{ fontSize: 10 }}>
                                    {workbenchPgMirrorLabel(savedCase.pg_mirror_state)}
                                </Tag>
                            ) : null}
                        </Space>
                    )}
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
                    <Space size="small" wrap>
                        <Dropdown
                            menu={{
                                items: [
                                    {
                                        key: 'test',
                                        label: savedCase.workbench_test ? '取消测试标记' : '标为测试',
                                        onClick: () => {
                                            void handlePatchWorkbench(savedCase.case_id, { is_test: !savedCase.workbench_test });
                                        },
                                    },
                                    {
                                        key: 'arch',
                                        label: savedCase.workbench_archived ? '取消归档' : '归档隐藏',
                                        onClick: () => {
                                            void handlePatchWorkbench(savedCase.case_id, {
                                                archived: !savedCase.workbench_archived,
                                            });
                                        },
                                    },
                                    ...(savedCase.workbench_test
                                        ? [
                                              {
                                                  key: 'del',
                                                  danger: true,
                                                  label: '删除测试记录…',
                                                  onClick: () => handleDeleteTestCase(savedCase.case_id),
                                              },
                                          ]
                                        : []),
                                ],
                            }}
                            trigger={['click']}
                        >
                            <Button size="small" icon={<MoreOutlined />}>
                                管理
                            </Button>
                        </Dropdown>
                        <Button size="small" type="primary" onClick={() => handleOpenRecent(savedCase)}>
                            {officeOpenRecordCta}
                        </Button>
                    </Space>
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
                {error && (
                    <Alert type="error" message={error} showIcon closable onClose={() => setError(null)} />
                )}
                <Collapse
                    size="small"
                    items={[
                        {
                            key: 'secondary-ops',
                            label: '演示与运营信号（次要）',
                            children: (
                                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Row gutter={[12, 12]}>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">需立即处理（本页）</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>
                                        {recentLoading ? <Spin size="small" /> : actionNowCases.length}
                                    </Title>
                                    <Text type="secondary">本页列表内：需经纪人行动或今日到期。</Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">等客户回复（本页）</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>
                                        {recentLoading ? <Spin size="small" /> : waitingOnClientCount}
                                    </Title>
                                    <Text type="secondary">本页列表内：跟进已转给客户，等回复。</Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">队列（全部）</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>
                                        {recentLoading ? <Spin size="small" /> : workbenchTotalCount}
                                    </Title>
                                    <Text type="secondary">
                                        持久化服务记录总数。本页已加载 {recentCases.length} 条（第 {workbenchPageIndex + 1} 页）。
                                    </Text>
                                </Card>
                            </Col>
                            <Col xs={12} md={6}>
                                <Card size="small" styles={{ body: { padding: 12 } }}>
                                    <Text type="secondary">高风险（本页）</Text>
                                    <Title level={3} style={{ margin: '6px 0 0' }}>
                                        {recentLoading ? <Spin size="small" /> : highRiskCount}
                                    </Title>
                                    <Text type="secondary">本页列表内：高/紧急已标出。</Text>
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
                            ),
                        },
                    ]}
                />

                <div ref={recentCasesSectionRef}>
                <Card
                    size="small"
                    title={officeRecentCardTitle}
                    extra={<Text type="secondary">{officeRecentCardExtra}</Text>}
                >
                    <div
                        style={{
                            marginBottom: 10,
                            padding: '8px 10px',
                            borderRadius: 8,
                            background: '#fafafa',
                            border: '1px solid #f0f0f0',
                        }}
                    >
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                            <Space wrap size={[8, 4]} align="center" style={{ width: '100%' }}>
                                <ClockCircleOutlined style={{ color: '#8c8c8c' }} />
                                <Text type="secondary" style={{ fontSize: 11, flex: 1, minWidth: 200 }}>
                                    {recentLoading && !workbenchQueueLoadedAtIso
                                        ? '正在从服务器加载队列…'
                                        : workbenchQueueLoadedAtIso ? `队列已于 ${formatPortalLocalDateTime(workbenchQueueLoadedAtIso) ?? workbenchQueueLoadedAtIso} 刷新（本机时间）`
                                          : '尚未成功加载队列'}
                                    {' · '}
                                    数据接口{' '}
                                    <Text code style={{ fontSize: 10 }}>
                                        {formatWorkbenchApiEndpointLabel(API_BASE_URL)}
                                    </Text>
                                </Text>
                                <Button
                                    size="small"
                                    type="default"
                                    icon={<ReloadOutlined />}
                                    loading={recentLoading}
                                    onClick={() => void loadRecent({ page: workbenchPageIndex })}
                                >
                                    刷新列表
                                </Button>
                            </Space>
                            {workbenchPgMirrorTrust ? (
                                <Text
                                    type="secondary"
                                    style={{ fontSize: 11, display: 'block', paddingLeft: 22, lineHeight: 1.45 }}
                                >
                                    {workbenchPgMirrorTrust}
                                </Text>
                            ) : null}
                        </Space>
                    </div>
                    {recentLoading ? (
                        <Spin size="small" />
                    ) : recentCases.length === 0 ? (
                        <Text type="secondary">
                            {officeEmptyQueueHint}
                        </Text>
                    ) : (
                        <Space direction="vertical" size={10} style={{ width: '100%' }}>
                            <Text type="secondary">
                                点击打开任意服务记录，继续下一步、跟进计划或草稿审核。
                            </Text>
                            <Segmented<WorkbenchListFilter>
                                size="small"
                                value={workbenchListFilter}
                                onChange={(v) => setWorkbenchListFilter(v as WorkbenchListFilter)}
                                options={[
                                    { label: '全部', value: 'all' },
                                    { label: '正式', value: 'formal' },
                                    { label: '测试', value: 'test' },
                                    { label: '旧识别', value: 'legacy' },
                                    { label: '镜像异常', value: 'mirror_bad' },
                                    { label: '24h', value: 'recent24h' },
                                ]}
                                style={{ width: '100%', maxWidth: '100%' }}
                            />
                            {workbenchListFilter !== 'all' && (
                                <Text type="secondary" style={{ fontSize: 11 }}>
                                    显示 {workbenchFilteredCases.length} / {recentCases.length} 条（本页已加载；筛选不跨页）
                                </Text>
                            )}
                            {workbenchTotalCount > WORKBENCH_PAGE_SIZE ? (
                                <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
                                    共 {workbenchTotalCount} 条持久化记录，已分页。下方筛选与分组仅作用于本页。
                                </Text>
                            ) : null}
                            {currentCase?.case_id ? (
                                <div
                                    style={{
                                        padding: '6px 10px',
                                        borderRadius: 8,
                                        background: 'linear-gradient(90deg, #f0f5ff 0%, #ffffff 100%)',
                                        border: '1px solid #adc6ff',
                                        borderLeft: '3px solid #1677ff',
                                    }}
                                >
                                    <Text style={{ fontSize: 12, color: '#262626', display: 'block', lineHeight: 1.45 }}>
                                        <Text strong style={{ color: '#1677ff' }}>{officeQueueOpenAnchorPrefix}</Text>
                                        <Text type="secondary" style={{ fontFamily: 'monospace', fontSize: 11, marginLeft: 6 }}>
                                            {formatQueueCaseIdShort(currentCase.case_id)}
                                        </Text>
                                    </Text>
                                    <Text
                                        type="secondary"
                                        style={{ fontSize: 11, display: 'block', marginTop: 2, lineHeight: 1.45 }}
                                        ellipsis={{ tooltip: getPreviewText(currentCase.source_text ?? '', 200) }}
                                    >
                                        {getPreviewText(currentCase.source_text ?? '', 52) || '（无摘要 — 见右侧详情）'}
                                    </Text>
                                </div>
                            ) : null}
                            <Collapse
                                size="small"
                                items={[
                                    {
                                        key: 'queue-secondary-help',
                                        label: '测试管理与图例（次要）',
                                        children: (
                                            <Space direction="vertical" size={2}>
                                                <Text type="secondary" style={{ fontSize: 11 }}>
                                                    轻量测试管理：用「管理」标记测试/归档；测试记录可删除清理。正式记录请归档隐藏。
                                                </Text>
                                                <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.55, display: 'block' }}>
                                                    图例：工作台标签含测试、归档、识别与 PG 状态；状态含立即处理、待您、可行动、需更多信息、等客户等。
                                                </Text>
                                            </Space>
                                        ),
                                    },
                                ]}
                            />
                            {actionNowCases.length > 0 && (
                                <>
                                    <Text strong style={{ fontSize: 12 }}>
                                        立即处理 · 本页 ({actionNowCases.length})
                                    </Text>
                                    {actionNowCases.map((savedCase) => renderRecentCaseCard(savedCase))}
                                </>
                            )}
                            {trackingCases.length > 0 && (
                                <>
                                    <Text strong style={{ fontSize: 12, marginTop: actionNowCases.length > 0 ? 8 : 0 }}>
                                        等待或暂存 · 本页 ({trackingCases.length})
                                    </Text>
                                    {trackingCases.map((savedCase) => renderRecentCaseCard(savedCase))}
                                </>
                            )}
                            {!recentLoading && workbenchTotalCount > 0 ? (
                                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 4 }}>
                                    <Pagination
                                        simple
                                        size="small"
                                        current={workbenchPageIndex + 1}
                                        pageSize={WORKBENCH_PAGE_SIZE}
                                        total={workbenchTotalCount}
                                        onChange={(page) => void loadRecent({ page: page - 1 })}
                                        showSizeChanger={false}
                                    />
                                </div>
                            ) : null}
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
                    <Text type="secondary" style={{ marginTop: 8, display: 'block', fontSize: 12, lineHeight: 1.45 }}>
                        与客户报送同源 · 加车为试点主线 · 不自动对外发送
                    </Text>
                </div>

                <Card
                    size="small"
                    title={officePasteCardTitle}
                    extra={<Text type="secondary">原文即可，无需整理</Text>}
                    style={{ borderRadius: 8 }}
                >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        {currentCase && !loading ? (
                            <Text type="secondary" style={{ fontSize: 12, display: 'block', lineHeight: 1.5 }}>
                                {caseView === 'reopened'
                                    ? '已打开队列中的记录：完整原文在下方「完整对话」展开查看。若要再整理另一条客户消息，请先点「清空」释放本条，再粘贴新原文。'
                                    : '本条已整理：完整原文在下方「完整对话」备查；此处可继续粘贴下一条并「开始整理」。'}
                            </Text>
                        ) : null}
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
                                disabled={caseView === 'reopened' && Boolean((currentCase?.case_id ?? '').trim())}
                            >
                                {caseView === 'reopened' && Boolean((currentCase?.case_id ?? '').trim()) ? '已打开' : '开始整理'}
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

                {loading && (
                    <Card size="small">
                        <Space>
                            <Spin size="small" />
                            <Text type="secondary">正在生成办公室可读整理结果…</Text>
                        </Space>
                    </Card>
                )}

                {currentCase && !loading && (
                    <Card
                        size="small"
                        title={
                            <Space wrap>
                                <span>{caseView === 'reopened' ? '已打开的服务记录' : '当前服务记录'}</span>
                                <UrgencyTag urgency={currentCase.urgency} />
                                {currentCase.case_id && <CaseStatusTag status={currentCase.case_status} />}
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
                                    title="复制服务记录摘要：整理结果 + 正式送达/时间（加车）+ 字段与草稿"
                                >
                                    复制摘要
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
                            <OfficeWorkbenchOneGlanceSummary
                                triage={currentCase}
                                inputFallback={(input.trim() || currentCase.source_text || '').trim()}
                                uiCopy={uiCopy}
                            />
                            {currentCase.case_id && (
                                <Collapse
                                    bordered={false}
                                    style={{ background: 'transparent' }}
                                    defaultActiveKey={[]}
                                    items={[
                                        {
                                            key: 'wb_meta',
                                            label: (
                                                <Text style={{ fontSize: 12 }}>
                                                    记录管理 / 镜像 / 车道
                                                    <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                                                        （展开）
                                                    </Text>
                                                </Text>
                                            ),
                                            children: (
                                                <div style={{ paddingTop: 4 }}>
                                                    <Space wrap size={[4, 4]} align="center">
                                                        {currentCase.workbench_lane_kind ? (
                                                            <Tag style={{ fontSize: 10 }}>
                                                                {workbenchLaneLabel(currentCase.workbench_lane_kind)}
                                                            </Tag>
                                                        ) : null}
                                                        {currentCase.pg_mirror_state ? (
                                                            <Tag
                                                                color={workbenchPgMirrorTagColor(currentCase.pg_mirror_state)}
                                                                style={{ fontSize: 10 }}
                                                            >
                                                                {workbenchPgMirrorLabel(currentCase.pg_mirror_state)}
                                                            </Tag>
                                                        ) : null}
                                                        {humanizeServiceLaneOffice(currentCase.service_lane) ? (
                                                            <Tag style={{ fontSize: 10 }} color="blue">
                                                                车道：{humanizeServiceLaneOffice(currentCase.service_lane)}
                                                            </Tag>
                                                        ) : null}
                                                        {currentCase.workbench_test ? <Tag color="orange">测试</Tag> : null}
                                                        {currentCase.workbench_archived ? <Tag>归档</Tag> : null}
                                                        <Dropdown
                                                            menu={{
                                                                items: [
                                                                    {
                                                                        key: 'test',
                                                                        label: currentCase.workbench_test ? '取消测试标记' : '标为测试',
                                                                        onClick: () => {
                                                                            void handlePatchWorkbench(currentCase.case_id!, {
                                                                                is_test: !currentCase.workbench_test,
                                                                            });
                                                                        },
                                                                    },
                                                                    {
                                                                        key: 'arch',
                                                                        label: currentCase.workbench_archived ? '取消归档' : '归档隐藏',
                                                                        onClick: () => {
                                                                            void handlePatchWorkbench(currentCase.case_id!, {
                                                                                archived: !currentCase.workbench_archived,
                                                                            });
                                                                        },
                                                                    },
                                                                    ...(currentCase.workbench_test
                                                                        ? [
                                                                              {
                                                                                  key: 'del',
                                                                                  danger: true,
                                                                                  label: '删除测试记录…',
                                                                                  onClick: () =>
                                                                                      handleDeleteTestCase(currentCase.case_id!),
                                                                              },
                                                                          ]
                                                                        : []),
                                                                ],
                                                            }}
                                                            trigger={['click']}
                                                        >
                                                            <Button
                                                                size="small"
                                                                type="link"
                                                                icon={<MoreOutlined />}
                                                                style={{ padding: 0, height: 'auto' }}
                                                            >
                                                                管理
                                                            </Button>
                                                        </Dropdown>
                                                    </Space>
                                                </div>
                                            ),
                                        },
                                    ]}
                                />
                            )}
                            {triageResultLooksLikeAddCar(currentCase) && (
                                <Collapse
                                    bordered={false}
                                    style={{ background: 'transparent' }}
                                    defaultActiveKey={[]}
                                    items={[
                                        {
                                            key: 'add_car_submission_detail',
                                            label: (
                                                <Text style={{ fontSize: 12 }}>
                                                    报送与时间戳说明
                                                    <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                                                        （展开核对）
                                                    </Text>
                                                </Text>
                                            ),
                                            children: (
                                                <OfficeWorkbenchAddCarSubmissionSnapshot triage={currentCase} uiCopy={uiCopy} />
                                            ),
                                        },
                                    ]}
                                />
                            )}
                            <Card
                                size="small"
                                title={
                                    <Space wrap size={[4, 4]}>
                                        <Text strong>Case 整理明细</Text>
                                        <Text type="secondary" style={{ fontSize: 12, fontWeight: 'normal' }}>
                                            — 核对标签与材料；主结论在上方「整理结果」
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
                                    <Collapse
                                        bordered={false}
                                        style={{ background: 'transparent' }}
                                        defaultActiveKey={[]}
                                        items={[
                                            {
                                                key: 'case_sheet_tags',
                                                label: (
                                                    <Text style={{ fontSize: 12 }}>
                                                        更多状态标签（事项/收集/生命周期/跟进）
                                                        <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                                                            （展开）
                                                        </Text>
                                                    </Text>
                                                ),
                                                children: (
                                                    <Space wrap align="center">
                                                        {(() => {
                                                            const focus =
                                                                inferCaseFocusFromStructuredFields(
                                                                    currentCase.collected_fields,
                                                                    currentCase.still_needed_fields,
                                                                    currentCase.issue_category,
                                                                ) ?? inferCaseFocusFromText(currentCase.source_text ?? input.trim());
                                                            const display = focus ? (getCaseFocusDisplayLabel(focus) ?? focus) : null;
                                                            return display ? <Tag color="blue">{display}</Tag> : null;
                                                        })()}
                                                        {currentCase.collection_stage && (
                                                            <Tag
                                                                color={
                                                                    currentCase.collection_stage === 'enough_for_handoff' ? 'green' : 'default'
                                                                }
                                                                style={{ fontSize: 11 }}
                                                            >
                                                                {currentCase.collection_stage === 'enough_for_handoff'
                                                                    ? '可交办公室'
                                                                    : '信息收集中'}
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
                                                        {currentAttention && (
                                                            <Tag color={currentAttention.color}>{currentAttention.label}</Tag>
                                                        )}
                                                        <Tag color={currentCase.manual_followup_needed ? 'volcano' : 'green'}>
                                                            {currentCase.manual_followup_needed ? '需要您处理' : '可审核草稿'}
                                                        </Tag>
                                                        {(currentCase.urgency === 'critical' || currentCase.urgency === 'high') && (
                                                            <Tag color="red" icon={<ClockCircleOutlined />}>
                                                                建议当日处理
                                                            </Tag>
                                                        )}
                                                    </Space>
                                                ),
                                            },
                                        ]}
                                    />
                                    <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
                                        办公室主行动与跟进预览见上方「整理结果」第三步；此处为标签、字段与草稿全文核对。
                                    </Text>
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
                                    {(() => {
                                        const ob = getOfficeCaseBoundaryPresentation(currentCase);
                                        if (!ob) return null;
                                        return (
                                            <div
                                                style={{
                                                    padding: 10,
                                                    marginBottom: 8,
                                                    background:
                                                        ob.badgeColor === 'volcano'
                                                            ? 'rgba(255, 77, 79, 0.06)'
                                                            : ob.badgeColor === 'gold'
                                                              ? 'rgba(250, 173, 20, 0.1)'
                                                              : 'rgba(19, 194, 194, 0.08)',
                                                    borderRadius: 6,
                                                    borderLeft: `3px solid ${
                                                        ob.badgeColor === 'volcano'
                                                            ? '#ff4d4f'
                                                            : ob.badgeColor === 'gold'
                                                              ? '#faad14'
                                                              : '#13c2c2'
                                                    }`,
                                                }}
                                            >
                                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                    案件边界（追加判定）
                                                </Text>
                                                <Space wrap size={[6, 4]}>
                                                    <Tag color={ob.badgeColor} style={{ marginInlineEnd: 0 }}>
                                                        {ob.badgeLabel}
                                                    </Tag>
                                                </Space>
                                                <Text style={{ fontSize: 12, display: 'block', marginTop: 6, color: '#262626' }}>
                                                    {ob.summaryLine}
                                                </Text>
                                                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                                                    {ob.actionLine}
                                                </Text>
                                                {currentCase.boundary_reason?.trim() ? (
                                                    <Text
                                                        type="secondary"
                                                        style={{ fontSize: 11, display: 'block', marginTop: 6, fontFamily: 'monospace' }}
                                                    >
                                                        {currentCase.boundary_reason}
                                                    </Text>
                                                ) : null}
                                            </div>
                                        );
                                    })()}
                                    {/* Add-car quote-ready status (ADD_CAR_REAL_INTAKE_LITE) — skipped for加车 when already in一眼摘要 */}
                                    {currentCase.quote_ready_status && !triageResultLooksLikeAddCar(currentCase) && (
                                        <div style={{ marginBottom: 8 }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                报价进度
                                            </Text>
                                            <Tag color={QUOTE_READY_STATUS_LABELS[currentCase.quote_ready_status]?.color ?? 'default'}>
                                                {QUOTE_READY_STATUS_LABELS[currentCase.quote_ready_status]?.label ?? currentCase.quote_ready_status}
                                            </Tag>
                                        </div>
                                    )}
                                    {/* Contact block (ADD_CAR_IDENTITY_CONTACT_LITE) — skipped for加车 when已在摘要「①」 */}
                                    {!triageResultLooksLikeAddCar(currentCase) &&
                                    (currentCase.quote_ready_status || (currentCase.collected_fields ?? []).some((f) => f === 'name' || f === 'phone') || (currentCase.still_needed_fields ?? []).some((f) => f === 'name' || f === 'phone')) && (
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
                                    {/* Optional light binding (Stage-1 continuity; not contact identity) */}
                                    {currentCase.identity_binding_state === 'linked' &&
                                        (currentCase.person_link_key?.trim() || currentCase.person_link_source) && (
                                            <div style={{ marginBottom: 8 }}>
                                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                    可选续接（连续性，非登录）
                                                </Text>
                                                <Space wrap size={[8, 4]}>
                                                    <Tag color="default" style={{ fontSize: 11 }}>
                                                        {currentCase.person_link_source === 'wechat'
                                                            ? '微信续接标识已记录'
                                                            : '续接标识已记录'}
                                                    </Tag>
                                                    {currentCase.person_link_key?.trim() ? (
                                                        <Text type="secondary" style={{ fontSize: 11, fontFamily: 'monospace' }}>
                                                            {currentCase.person_link_key.length > 18
                                                                ? `${currentCase.person_link_key.slice(0, 14)}…`
                                                                : currentCase.person_link_key}
                                                        </Text>
                                                    ) : null}
                                                    {typeof currentCase.person_link_confidence === 'number' ? (
                                                        <Text type="secondary" style={{ fontSize: 11 }}>
                                                            置信 {Math.round(currentCase.person_link_confidence * 100)}%
                                                        </Text>
                                                    ) : null}
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
                                    {/* Collected + Still needed — folded by default to avoid duplicating the glance “还缺什么” wall */}
                                    {((currentCase.collected_fields?.length ?? 0) > 0 || (currentCase.still_needed_fields?.length ?? 0) > 0) ? (
                                        <Collapse
                                            bordered={false}
                                            style={{ background: 'transparent' }}
                                            defaultActiveKey={[]}
                                            items={[
                                                {
                                                    key: 'wb_structured_fields',
                                                    label: (
                                                        <Text style={{ fontSize: 12 }}>
                                                            结构化字段明细（已收集 / 待补标签）
                                                            <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
                                                                （展开核对 · 缺口摘要已在上方）
                                                            </Text>
                                                        </Text>
                                                    ),
                                                    children: (
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
                                                                        结构化待补（跟客户入口同源）
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
                                                    ),
                                                },
                                            ]}
                                        />
                                    ) : (currentCase.conversation_summary || currentCase.secondary_issue_note) && (
                                        <div style={{ fontSize: 13 }}>
                                            {currentCase.secondary_issue_note && (
                                                <Tag color="blue" style={{ marginBottom: 6 }}>
                                                    {currentCase.secondary_issue_note}
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
                                    <Collapse
                                        bordered={false}
                                        style={{ background: 'transparent' }}
                                        defaultActiveKey={[]}
                                        items={[
                                            {
                                                key: 'wb_draft_full',
                                                label: (
                                                    <Space wrap size={[6, 4]} align="center">
                                                        <Text style={{ fontSize: 12 }}>草稿全文（确认后再发）</Text>
                                                        <Tag
                                                            color={currentCase.manual_followup_needed ? 'gold' : 'green'}
                                                            style={{ marginInlineEnd: 0 }}
                                                        >
                                                            {getDraftReadinessLabel(currentCase)}
                                                        </Tag>
                                                    </Space>
                                                ),
                                                children: (
                                                    <div style={{ paddingTop: 4 }}>
                                                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                                                            审核后手动发送；顶部可一键复制。
                                                        </Text>
                                                        <div
                                                            style={{
                                                                padding: 12,
                                                                background: '#fafafa',
                                                                borderRadius: 6,
                                                                whiteSpace: 'pre-wrap',
                                                                fontFamily: 'inherit',
                                                                fontSize: 13,
                                                            }}
                                                        >
                                                            {currentCase.client_reply_draft}
                                                        </div>
                                                    </div>
                                                ),
                                            },
                                        ]}
                                    />
                                </Col>
                            </Row>

                            <Collapse
                                bordered={false}
                                style={{ background: 'transparent' }}
                                defaultActiveKey={[]}
                                items={[
                                    {
                                        key: 'wb_full_thread',
                                        label: (
                                            <Space wrap align="center">
                                                <Text strong style={{ fontSize: 13 }}>
                                                    {currentCase.source_text?.includes('[客户]') ? '完整对话（备查）' : '本条消息原文（备查）'}
                                                </Text>
                                                <Text type="secondary" style={{ fontSize: 11 }}>
                                                    默认收起 · 主结论在上方整理结果
                                                </Text>
                                            </Space>
                                        ),
                                        children: (
                                            <Card size="small" styles={{ body: { padding: 12 } }} style={{ marginTop: 4 }}>
                                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
                                                    最后更新 {formatDateLabel(currentCase.updated_at)}
                                                    {currentLatestContext ? ` · ${currentLatestContext}` : ''}
                                                </Text>
                                                <div style={{ whiteSpace: 'pre-wrap' }}>
                                                    {currentCase.source_text || input.trim()}
                                                </div>
                                            </Card>
                                        ),
                                    },
                                ]}
                            />

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
    const portalTabMyRequests = uiCopy.portal_tab_my_requests_label ?? '我的办理';
    const portalTabMyRequestsSuffix =
        uiCopy.portal_tab_my_requests_suffix ?? '进行中的请求与待补充项';

    const [activeTab, setActiveTab] = useState<string>('customer');
    const [brokerInitialCaseId, setBrokerInitialCaseId] = useState<string | undefined>();
    const [pilotIntroCollapsed, setPilotIntroCollapsed] = useState(false);
    const [headerAvatarBroken, setHeaderAvatarBroken] = useState(false);

    const portalHeroTitle = uiCopy.portal_hero_title ?? '加车报价 · 客户统一报送';
    const officeWorkbenchDocumentTitle = uiCopy.office_workbench_document_title ?? '加车报价试点 · 办公室工作台';
    const simulationTabTitle =
        (uiCopy.portal_tab_simulation_label ?? '场景仿真') + ' · ' + (uiCopy.portal_brand_tagline ?? '车险报送入口');
    const myRequestsDocumentTitle =
        (uiCopy.portal_tab_my_requests_label ?? '我的办理') + ' · ' + (uiCopy.portal_brand_tagline ?? '车险报送入口');

    useEffect(() => {
        if (activeTab === 'customer') {
            document.title = portalHeroTitle;
        } else if (activeTab === 'my_requests') {
            document.title = myRequestsDocumentTitle;
        } else if (activeTab === 'broker') {
            document.title = officeWorkbenchDocumentTitle;
        } else {
            document.title = simulationTabTitle;
        }
    }, [activeTab, portalHeroTitle, myRequestsDocumentTitle, officeWorkbenchDocumentTitle, simulationTabTitle]);

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
                                onOpenMyRequests={() => setActiveTab('my_requests')}
                            />
                        ),
                    },
                    {
                        key: 'my_requests',
                        forceRender: true,
                        label: (
                            <span>
                                <UnorderedListOutlined /> {portalTabMyRequests}
                                <Text type="secondary" style={{ marginLeft: 6, fontSize: 12, fontWeight: 400 }}>
                                    — {portalTabMyRequestsSuffix}
                                </Text>
                            </span>
                        ),
                        children: (
                            <UserCaseListProgressPanel onContinueInCustomerPortal={() => setActiveTab('customer')} />
                        ),
                    },
                    {
                        key: 'broker',
                        /** Prefetch queue on page load: inactive tab bodies start unmounted (rc-tabs + rc-motion); without this, GET /api/inbox/cases only runs after first opening Office tab, and summary tiles briefly show 0. */
                        forceRender: true,
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
