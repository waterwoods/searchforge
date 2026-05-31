import { useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import {
    Alert,
    Button,
    Card,
    Col,
    Collapse,
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
    Tag,
    Typography,
    message,
} from 'antd';
import {
    ClockCircleOutlined,
    CopyOutlined,
    InboxOutlined,
    MoreOutlined,
    PaperClipOutlined,
    ReloadOutlined,
    SendOutlined,
    SwapOutlined,
    UploadOutlined,
} from '@ant-design/icons';
import {
    addSavedCaseNote,
    appendFollowUpMessage,
    deleteTestCase,
    getAttachmentDownloadUrl,
    getSavedCase,
    listRecentCasesPage,
    patchCaseWorkbench,
    triageMessage,
    updateSavedCaseFollowUp,
    updateSavedCaseStatus,
    uploadCaseAttachment,
    type CaseStatus,
    type SavedCase,
    type TriageResult,
    type WaitingOn,
} from '@/api/inboxTriage';
import { hasDebugSignals, pickTriageResultCore } from '@/api/triageResultContract';
import { copyToClipboard } from '@/utils/demoCopy';
import { useClientConfig } from '@/context/ClientConfigContext';
import { isUnifiedIntakeProductOnlyUi } from '@/config/productSurface';
import { API_BASE_URL } from '@/api/config';
import {
    getOfficeCaseBoundaryListTag,
    getOfficeCaseBoundaryPresentation,
} from '@/components/workbench/officeCaseBoundary';
import {
    addCarQueueStatusPhase,
    buildOfficeWorkbenchGlance,
    formatDateLabel,
    formatPortalLocalDateTime,
    formatQueueCaseIdShort,
    formatWorkbenchApiEndpointLabel,
    getCaseAttentionState,
    getCaseFocusDisplayLabel,
    getCaseReportOneLiner,
    getCaseTrackingSummary,
    getDraftReadinessLabel,
    getFollowUpDueTag,
    getFollowUpSummary,
    getLatestCaseContext,
    getLatestUpdateForDisplay,
    getOfficeLifecycleTag,
    getPreviewText,
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
import type { BrokerWorkbenchTabProps, FollowUpDraft, WorkbenchListFilter } from '@/features/intake/types';
import {
    CASE_STATUS_OPTIONS,
    FOUNDER_DEMO_QUEUE,
    QUICK_FILL_EXAMPLES,
    QUOTE_READY_STATUS_LABELS,
    WAITING_ON_OPTIONS,
} from '@/features/intake/constants';
import { AddCarCaseStatusStrip } from '@/features/intake/components/StatusStrips';
import {
    OfficeWorkbenchOneGlanceSummary,
    OfficeWorkbenchAddCarSubmissionSnapshot,
    UrgencyTag,
    CaseStatusTag,
} from '@/features/intake/components/WorkbenchSummary';
import { addCarNextOwnerLine } from '@/components/intake/AddCarRecordSummaryRail';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

/** Office queue list: server page size (must match API max limit). */
const WORKBENCH_PAGE_SIZE = 50;

// =============================================================================
// BROKER WORKBENCH TAB
// =============================================================================

const BROKER_INLINE_PRACTICE_SCENARIOS = [
    { label: '取消/付款风险', purpose: '同日紧急 — 演示核心价值', seedIndex: 0 },
    { label: '缺材料跟进', purpose: '等客户补件 — 常见跟进', seedIndex: 1 },
    { label: '加车报价', purpose: '日常报价 intake', seedIndex: 2 },
] as const;

function triageWarmupUserMessage(detail: unknown, status?: number): string | null {
    const msg = String(detail ?? '');
    if (status === 503 || /embedding|warming|not ready|unavailable/i.test(msg)) {
        return '服务正在预热，首次分析约30秒后可重试。请稍候再点「开始整理」。';
    }
    return null;
}

export function BrokerWorkbenchTab({ initialCaseId, clientId: clientIdProp }: BrokerWorkbenchTabProps) {
    const { uiCopy, clientId: contextClientId } = useClientConfig();
    const clientId = clientIdProp ?? contextClientId;
    const productOnlyUi = isUnifiedIntakeProductOnlyUi();
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
    const [demoQueueProgress, setDemoQueueProgress] = useState<{ done: number; total: number } | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [workbenchListFilter, setWorkbenchListFilter] = useState<WorkbenchListFilter>('all');
    const [workbenchPageIndex, setWorkbenchPageIndex] = useState(0);
    const [workbenchTotalCount, setWorkbenchTotalCount] = useState(0);
    /** Last successful GET /api/inbox/cases page load (office trust: "is this list current?"). */
    const [workbenchQueueLoadedAtIso, setWorkbenchQueueLoadedAtIso] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const recentCasesSectionRef = useRef<HTMLDivElement>(null);
    const caseDetailSectionRef = useRef<HTMLDivElement>(null);

    const workbenchFilterOptions = useMemo(
        () =>
            productOnlyUi
                ? [
                      { label: '全部', value: 'all' as WorkbenchListFilter },
                      { label: '需今天处理', value: 'action_today' as WorkbenchListFilter },
                      { label: '24小时内', value: 'recent24h' as WorkbenchListFilter },
                  ]
                : [
                      { label: '全部', value: 'all' as WorkbenchListFilter },
                      { label: '正式', value: 'formal' as WorkbenchListFilter },
                      { label: '测试', value: 'test' as WorkbenchListFilter },
                      { label: '旧识别', value: 'legacy' as WorkbenchListFilter },
                      { label: '镜像异常', value: 'mirror_bad' as WorkbenchListFilter },
                      { label: '24h', value: 'recent24h' as WorkbenchListFilter },
                  ],
        [productOnlyUi],
    );

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
            const ordered = orderCasesForWorkbench(cases);
            setRecentCases(ordered);
            setWorkbenchTotalCount(total_count);
            setWorkbenchQueueLoadedAtIso(new Date().toISOString());
            return { cases: ordered, total_count };
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
            return { cases: [] as SavedCase[], total_count: 0 };
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
        if (!match) return;
        void (async () => {
            try {
                const full = await getSavedCase(initialCaseId);
                setInput('');
                setCaseView('reopened');
                setCurrentCase(full);
                setNoteDraft('');
                setError(null);
            } catch (e: unknown) {
                const msg =
                    (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                    ?? (e as { message?: string })?.message
                    ?? 'Could not load case.';
                setError(String(msg));
                message.error(String(msg));
            }
        })();
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
            const ax = e as { response?: { data?: { detail?: string }; status?: number }; message?: string };
            const raw = ax?.response?.data?.detail ?? ax?.message ?? 'Triage request failed.';
            const warmup = triageWarmupUserMessage(raw, ax?.response?.status);
            setError(warmup ?? String(raw));
            if (warmup) {
                message.warning(warmup);
            }
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
        setNoteDraft('');
        setAppendMessageDraft('');
        setError(null);
        void (async () => {
            try {
                const full = await getSavedCase(savedCase.case_id);
                setCurrentCase(full);
            } catch (e: unknown) {
                const msg =
                    (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                    ?? (e as { message?: string })?.message
                    ?? 'Could not load case.';
                message.error(String(msg));
                setCurrentCase(savedCase);
            }
        })();
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
        setDemoQueueProgress(null);
        setError(null);
        try {
            const existingSourceTexts = new Set(recentCases.map((savedCase) => normalizeCaseSourceText(savedCase.source_text)));
            const seedsToCreate = FOUNDER_DEMO_QUEUE.filter(
                (seed) => !existingSourceTexts.has(normalizeCaseSourceText(seed.text)),
            );
            let openedCase: SavedCase | TriageResult | null = null;
            let createdCount = 0;
            let progressDone = 0;

            if (seedsToCreate.length > 0) {
                setDemoQueueProgress({ done: 0, total: seedsToCreate.length });
            }

            for (const seed of FOUNDER_DEMO_QUEUE) {
                if (existingSourceTexts.has(normalizeCaseSourceText(seed.text))) {
                    continue;
                }

                const created = await triageMessage(seed.text, true, undefined, undefined, undefined, clientId, true);
                createdCount += 1;
                progressDone += 1;
                setDemoQueueProgress({ done: progressDone, total: seedsToCreate.length });
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

            const { cases: refreshedCases } = await loadRecent({ page: 0 });
            const cancellationSeed = FOUNDER_DEMO_QUEUE[0];
            const cancellationMatch =
                refreshedCases.find(
                    (savedCase) =>
                        normalizeCaseSourceText(savedCase.source_text) === normalizeCaseSourceText(cancellationSeed.text),
                ) ?? null;

            const caseToOpen = cancellationMatch ?? openedCase;
            if (caseToOpen?.case_id) {
                try {
                    const full = await getSavedCase(caseToOpen.case_id);
                    setCurrentCase(full);
                } catch {
                    setCurrentCase(caseToOpen);
                }
                setCaseView('reopened');
                setInput('');
                caseDetailSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else if (caseToOpen) {
                setCurrentCase(caseToOpen);
                setCaseView('reopened');
                setInput('');
                caseDetailSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            if (createdCount === 0) {
                message.info('演示队列已就绪');
            } else {
                message.success(`已加载 ${createdCount} 条服务记录，见下方「${officeRecentCardTitle}」`);
                recentCasesSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } catch (e: unknown) {
            const ax = e as { response?: { data?: { detail?: string }; status?: number }; message?: string };
            const raw = ax?.response?.data?.detail ?? ax?.message ?? 'Could not load the founder demo queue.';
            const warmup = triageWarmupUserMessage(raw, ax?.response?.status);
            setError(warmup ?? String(raw));
            message.error(warmup ?? '加载演示队列失败');
        } finally {
            setDemoQueueLoading(false);
            setDemoQueueProgress(null);
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

    const handleAttachmentUpload = async (e: ChangeEvent<HTMLInputElement>) => {
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
        const coreCase = pickTriageResultCore(savedCase);
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
                        {hasDebugSignals(savedCase) && !productOnlyUi && (
                            <Tag style={{ fontSize: 10 }} color="default">
                                路由/指标
                            </Tag>
                        )}
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
                    {hasWorkbenchOpsTags(savedCase) && !productOnlyUi && (
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
                    {coreCase.broker_next_step?.trim() && (
                        <Text style={{ fontSize: 12, color: '#262626', display: 'block' }}>
                            {officeWorkbenchBrokerNextPreviewLabel}
                            {getPreviewText(coreCase.broker_next_step, 60)}
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
                        {!productOnlyUi && (
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
                        )}
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
                {productOnlyUi ? (
                    <Card size="small" title="快速体验（可选）">
                        <Space direction="vertical" size={8} style={{ width: '100%' }}>
                            <Space wrap align="center">
                                <Button type="primary" onClick={() => void handleLoadFounderQueue()} loading={demoQueueLoading}>
                                    加载演示队列
                                </Button>
                                {demoQueueLoading && demoQueueProgress ? (
                                    <Text type="secondary" style={{ fontSize: 13 }}>
                                        正在加载{demoQueueProgress.total}条示例 ({demoQueueProgress.done}/{demoQueueProgress.total}…)
                                    </Text>
                                ) : demoQueueLoading ? (
                                    <Text type="secondary" style={{ fontSize: 13 }}>首次分析约30秒，请稍候…</Text>
                                ) : null}
                                <Tag color={founderQueueLoadedCount === FOUNDER_DEMO_QUEUE.length ? 'green' : 'blue'}>
                                    {founderQueueLoadedCount}/{FOUNDER_DEMO_QUEUE.length} 条示例已就绪
                                </Tag>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                加载后自动打开取消/付款风险案例，查看下一步与草稿。
                            </Text>
                        </Space>
                    </Card>
                ) : (
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
                                    <Text type="secondary" style={{ fontSize: 13 }}>
                                        {demoQueueProgress
                                            ? `正在加载${demoQueueProgress.total}条示例 (${demoQueueProgress.done}/${demoQueueProgress.total}…)`
                                            : '加载中…约 15–30 秒'}
                                    </Text>
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
                )}

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
                                    {!productOnlyUi && (
                                        <>
                                            {' · '}
                                            数据接口{' '}
                                            <Text code style={{ fontSize: 10 }}>
                                                {formatWorkbenchApiEndpointLabel(API_BASE_URL)}
                                            </Text>
                                        </>
                                    )}
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
                            {!productOnlyUi && workbenchPgMirrorTrust ? (
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
                                options={workbenchFilterOptions}
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
                            {!productOnlyUi && (
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
                            )}
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
                        {productOnlyUi
                            ? '粘贴客户消息 → 查看整理结果、下一步与草稿。取消/付款风险优先。'
                            : officeWorkbenchSubtitle}
                    </Paragraph>
                    <Text type="secondary" style={{ marginTop: 8, display: 'block', fontSize: 12, lineHeight: 1.45 }}>
                        {productOnlyUi
                            ? '手动粘贴微信/通知文字 · 不自动对外发送'
                            : '与客户报送同源 · 加车为试点主线 · 不自动对外发送'}
                    </Text>
                </div>

                {productOnlyUi && (
                    <Alert
                        type="info"
                        showIcon
                        message="经纪人：请在本页粘贴客户消息"
                        description="原样粘贴微信或通知文字即可，不用整理。系统会整理 urgency、下一步与草稿，您确认后再发给客户。"
                        style={{ borderRadius: 8 }}
                    />
                )}

                {productOnlyUi && (
                    <Card size="small" title="练习场景（无需仿真页）" style={{ borderRadius: 8 }}>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                点选场景加载到下方粘贴区，再点「开始整理」体验完整流程。
                            </Text>
                            <Space wrap>
                                {BROKER_INLINE_PRACTICE_SCENARIOS.map((scenario) => {
                                    const seed = FOUNDER_DEMO_QUEUE[scenario.seedIndex];
                                    return (
                                        <Button
                                            key={scenario.label}
                                            size="small"
                                            onClick={() => handleQuickFill(seed.text)}
                                        >
                                            {scenario.label}
                                        </Button>
                                    );
                                })}
                            </Space>
                        </Space>
                    </Card>
                )}

                <Card
                    size="small"
                    title={officePasteCardTitle}
                    extra={
                        <Text type="secondary">
                            {productOnlyUi ? '原样粘贴微信/通知文字，不用整理' : '原文即可，无需整理'}
                        </Text>
                    }
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
                        <Text strong>
                            {productOnlyUi
                                ? '粘贴您收到的客户消息'
                                : '粘贴您当前收到的客户消息（与客户入口报送同等进入服务记录）。'}
                        </Text>
                        {!productOnlyUi && (
                        <Text type="secondary">
                            客户文字、转发的通知、邮件摘录、截图 OCR 文字均可。粘贴后系统整理为服务记录，并给出下一步与草稿。
                        </Text>
                        )}
                        <TextArea
                            placeholder={
                                productOnlyUi
                                    ? '原样粘贴微信/通知文字，不用整理\n\n例如：客户转发的取消通知、付款失败提醒、加车询价…'
                                    : '在此粘贴客户消息…\n\n无需整理，原文即可。\n\n例如：客户文字、转发通知、邮件摘录、截图 OCR 文字'
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
                            {!productOnlyUi && (
                            <Button type="text" onClick={() => setShowExamples((value) => !value)}>
                                {showExamples ? '收起示例' : '需要示例？'}
                            </Button>
                            )}
                            {!productOnlyUi && activeExample && (
                                <Tag color={getUrgencyColor(activeExample.urgency)}>
                                    已加载：{activeExample.label}
                                </Tag>
                            )}
                        </Space>
                        {!productOnlyUi && showExamples && (
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
                            <Text type="secondary">
                                {productOnlyUi ? '首次分析约30秒，请稍候…' : '正在生成办公室可读整理结果…'}
                            </Text>
                        </Space>
                    </Card>
                )}

                <div ref={caseDetailSectionRef}>
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
                            {currentCase.case_id && !productOnlyUi && (
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
                </div>
                    </Space>
                </Col>
            </Row>
        </div>
    );
}
