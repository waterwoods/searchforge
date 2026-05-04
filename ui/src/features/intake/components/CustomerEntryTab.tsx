import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
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
    Row,
    Space,
    Spin,
    Tag,
    Typography,
    message,
} from 'antd';
import {
    ClockCircleOutlined,
    CustomerServiceOutlined,
    InboxOutlined,
    MoreOutlined,
    PlayCircleOutlined,
    SendOutlined,
    SwapOutlined,
} from '@ant-design/icons';
import { userFacingCaseTitle } from "@/components/intake/UserCaseListProgressPanel";
import { AddCarFlowExplanation } from "@/components/intake/AddCarFlowExplanation";
import {
    AddCarHandoffGroupedSnapshot,
    AddCarRecordSummaryRail,
    computeAddCarFlowStep,
    isFormalSubmissionToOfficeComplete,
} from "@/components/intake/AddCarRecordSummaryRail";
import {
    appendFollowUpMessage,
    clearSessionId,
    fetchWeChatBindingStart,
    getInProgressSession,
    getOrCreateSessionId,
    getSessionId,
    listRecentCasesPage,
    postWeChatBindingSimulateComplete,
    triageMessage,
    type IdentityBindingState,
    type SoftRouteIntent,
    type TriageResult,
} from "@/api/inboxTriage";
import { useClientConfig } from "@/context/ClientConfigContext";
import {
    caseLifecycleTagColor,
    caseLifecycleUserLabel,
    isAddCarReadyForFormalSubmit,
    resolveCaseLifecycle,
} from "@/components/intake/caseLifecycleDisplay";
import type { ConversationTurn, CustomerEntryTabProps } from "@/features/intake/types";
import {
    CUSTOMER_ENTRY_EXAMPLES,
    DEFAULT_QUICK_START_BUTTONS,
    QUOTE_READY_STATUS_LABELS,
} from "@/features/intake/constants";
import {
    composeAddCarStructuredIntakeMessage,
    customerEntryIsAddCarActive,
    formatPortalLocalDateTime,
    getCaseFocusDisplayLabel,
    getCaseReportOneLiner,
    getCustomerUrgencyNote,
    getQuickStartButtons,
    humanizeCategory,
    humanizeStructuredFieldForCustomer,
    inferCaseFocusFromStructuredFields,
    inferCaseFocusFromText,
    triageResultLooksLikeAddCar,
} from "@/features/intake/utils";
import { AddCarCaseStatusStrip, GenericIntakeStatusStrip, IntakeFlowStepTrack } from "@/features/intake/components/StatusStrips";

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

export function CustomerEntryTab({ onSwitchToBroker, onOpenScenarioSimulation, onOpenMyRequests }: CustomerEntryTabProps) {
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

    const cardStyle: CSSProperties = {
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
