import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Card, Input, Modal, Select, Space, Tag, Typography, message } from 'antd';
import {
    createCaseRequestMore,
    Slice1RequestMoreError,
    type RequestMoreDraftItem,
    type Slice1CommandResult,
    type Slice1CustomerResponse,
    type Slice1Projection,
    type Slice1RequestItem,
    type Slice1RequestItemType,
    type Slice1RequestSummary,
    type TriageResult,
} from '@/api/inboxTriage';
import { formatPortalLocalDateTime } from '@/features/intake/utils/intakePure';
import {
    CLAIM_PILOT_STATUS,
    CLAIM_REQUEST_MORE_COPY,
} from '@/features/intake/utils/claimPilotCopy';

const { TextArea } = Input;
const { Text } = Typography;

const SLICE1_REQUEST_MORE_TYPES: Array<{ value: Slice1RequestItemType; label: string }> = [
    { value: 'vehicle_information', label: '车辆信息' },
    { value: 'vin', label: '车辆 VIN' },
    { value: 'policy_or_insurance_card', label: '保险卡' },
    { value: 'photo_evidence', label: '照片 / 文件' },
    { value: 'free_text', label: '其他确认' },
];

const SLICE1_REQUEST_MORE_PRESETS: Array<{
    key: string;
    label: string;
    item_type: Slice1RequestItemType;
    instructions: string;
}> = [
    {
        key: 'vehicle_information',
        label: '车辆信息',
        item_type: 'vehicle_information',
        instructions: '请补充本次事故车辆的基本信息（年份 / 品牌 / 型号；如有 VIN 也可一并提供）。',
    },
    { key: 'vin', label: '车辆 VIN', item_type: 'vin', instructions: '请发送或确认车辆 VIN。' },
    {
        key: 'insurance_card',
        label: '保险卡',
        item_type: 'policy_or_insurance_card',
        instructions: '请上传清晰的保险卡照片。',
    },
    {
        key: 'damage_photos',
        label: '车损照片',
        item_type: 'photo_evidence',
        instructions: '请上传清晰的车辆受损照片。',
    },
    {
        key: 'police_report',
        label: '报警回执 / 报告',
        item_type: 'photo_evidence',
        instructions: '如有，请上传报警回执或相关文件照片。',
    },
    {
        key: 'incident_date',
        label: '事故时间确认',
        item_type: 'free_text',
        instructions: '请确认事故日期与大概时间。',
    },
];

type RequestMoreSubmitState = 'idle' | 'submitting' | 'retry_ready' | 'conflict' | 'success' | 'error';

type RequestMoreCommandIdentity = {
    command_id: string;
    idempotency_key: string;
    request_id: string;
    expected_case_version: number;
};

export type StructuredRequestMoreCaseRecord = Partial<TriageResult> & {
    case_id?: string;
    case_status?: string;
    slice1_capability_version?: number;
    p20_slice1_capability_version?: number;
    slice1_projection?: Slice1Projection;
    p20_slice1_projection?: Slice1Projection;
    slice1_request_summary?: Slice1RequestSummary;
    p20_slice1_request_summary?: Slice1RequestSummary;
    workbench_archived?: boolean;
    broker_done_at?: string | null;
    claim_broker_done_at?: string | null;
    broker_confirmed_done_at?: string | null;
    end_card_sent_at?: string | null;
    end_card_sent?: boolean;
    known_facts?: Record<string, unknown>;
};

type StructuredRequestMorePanelProps<TCase extends StructuredRequestMoreCaseRecord> = {
    caseRecord: TCase | null;
    projectionLoading?: boolean;
    projectionLoadError?: string | null;
    onCaseChange: (updated: TCase) => void;
    refreshCase?: () => Promise<TCase | null>;
};

function makeRequestMoreCommandIdentity(caseId: string, expectedCaseVersion: number): RequestMoreCommandIdentity {
    const random = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    const suffix = `${caseId || 'case'}_${random}`.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 96);
    return {
        command_id: `cmd_request_more_${suffix}`,
        idempotency_key: `idem_request_more_${suffix}`,
        request_id: `req_${random}`.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 128),
        expected_case_version: expectedCaseVersion,
    };
}

function defaultRequestMoreItem(position = 1): RequestMoreDraftItem {
    return {
        item_type: 'vehicle_information',
        label: '车辆信息',
        instructions: '请补充本次事故车辆的基本信息（年份 / 品牌 / 型号；如有 VIN 也可一并提供）。',
        required: true,
        position,
    };
}

export function normalizeSlice1Projection(caseRecord: StructuredRequestMoreCaseRecord | null): Slice1Projection | null {
    const projection = caseRecord?.slice1_projection ?? caseRecord?.p20_slice1_projection;
    return projection && typeof projection === 'object' ? projection : null;
}

export function normalizeSlice1RequestSummary(caseRecord: StructuredRequestMoreCaseRecord | null): Slice1RequestSummary | null {
    const projection = normalizeSlice1Projection(caseRecord);
    const summary = projection?.open_request ?? caseRecord?.slice1_request_summary ?? caseRecord?.p20_slice1_request_summary;
    return summary && typeof summary === 'object' ? summary : null;
}

export function slice1EnabledForWorkbenchCase(caseRecord: StructuredRequestMoreCaseRecord | null): boolean {
    const version = Number(caseRecord?.slice1_capability_version ?? caseRecord?.p20_slice1_capability_version ?? 0);
    return caseRecord?.service_lane === 'claim' && (version >= 1 || normalizeSlice1Projection(caseRecord) !== null);
}

export function isStructuredRequestMoreSupportedCase(caseRecord: StructuredRequestMoreCaseRecord | null): boolean {
    return caseRecord?.service_lane === 'claim';
}

export function isStructuredRequestMoreTerminal(caseRecord: StructuredRequestMoreCaseRecord | null): boolean {
    if (!caseRecord) return true;
    // Soft archive is queue filter only — Request More stays available until Broker Close.
    const historyState = String((caseRecord as { case_history_state?: string }).case_history_state || '')
        .trim()
        .toLowerCase();
    if (historyState === 'history') return true;
    if (String((caseRecord as { closed_at?: string }).closed_at || '').trim()) return true;
    if (
        caseRecord.broker_done_at
        || caseRecord.claim_broker_done_at
        || caseRecord.broker_confirmed_done_at
        || caseRecord.end_card_sent_at
        || caseRecord.end_card_sent
    ) return true;
    const rawStates = [
        caseRecord.case_status,
        caseRecord.workflow_phase,
        (caseRecord as { claim_phase?: string }).claim_phase,
        caseRecord.display_status,
        (caseRecord as { admin_lifecycle?: string }).admin_lifecycle,
    ]
        .map((value) => String(value ?? '').trim().toLowerCase())
        .filter(Boolean);
    return rawStates.some((state) =>
        ['done', 'case_complete', 'complete', 'completed', 'cancelled', 'canceled', 'rejected', 'closed', 'history'].includes(state),
    );
}

export function slice1CaseVersion(caseRecord: StructuredRequestMoreCaseRecord | null): number {
    return Number(normalizeSlice1Projection(caseRecord)?.aggregate_version ?? 0);
}

export function slice1CanCreateRequest(caseRecord: StructuredRequestMoreCaseRecord | null): boolean {
    if (!slice1EnabledForWorkbenchCase(caseRecord)) return false;
    if (isStructuredRequestMoreTerminal(caseRecord)) return false;
    const projection = normalizeSlice1Projection(caseRecord);
    if (projection?.broker_next_action?.action_type === 'create_request') return true;
    if (normalizeSlice1RequestSummary(caseRecord)?.status === 'open') return false;
    const phase = String(caseRecord?.workflow_phase ?? (caseRecord as { claim_phase?: string } | null)?.claim_phase ?? '').trim();
    return !projection && phase === 'broker_review';
}

export function orderedSlice1Items(summary: Slice1RequestSummary | null): Slice1RequestItem[] {
    return [...(summary?.items ?? [])].sort((a, b) => Number(a.position || 0) - Number(b.position || 0));
}

function canonicalVinFromKnownFacts(knownFacts: Record<string, unknown> | undefined): string | null {
    if (!knownFacts || typeof knownFacts !== 'object') return null;
    for (const key of ['vin', 'vehicle_vin', 'own_vehicle_vin']) {
        const value = String(knownFacts[key] ?? '').trim();
        if (value) return value;
    }
    return null;
}

function canonicalVehicleFromKnownFacts(knownFacts: Record<string, unknown> | undefined): string | null {
    if (!knownFacts || typeof knownFacts !== 'object') return null;
    for (const key of [
        'vehicle_information',
        'own_vehicle_info',
        'primary_vehicle_summary',
        'vehicle_vin',
        'vin',
        'own_vehicle_vin',
    ]) {
        const value = String(knownFacts[key] ?? '').trim();
        if (value) return value;
    }
    return null;
}

function canonicalFactLabelForItemType(itemType: string | undefined): string {
    return String(itemType || '').trim().toLowerCase() === 'vin' ? '案件 VIN' : '案件车辆';
}

/**
 * Resolve the broker-visible customer response for one request item.
 * Prefers authoritative item.customer_response; falls back to latest_events.
 */
export function resolveSlice1CustomerResponse(
    item: Slice1RequestItem,
    projection: Slice1Projection | null,
    knownFacts?: Record<string, unknown>,
): Slice1CustomerResponse | null {
    const embedded = item.customer_response;
    if (embedded && typeof embedded === 'object') {
        if (embedded.kind === 'fact' && !embedded.canonical_value) {
            const itemType = String(item.item_type || '').trim().toLowerCase();
            const canonical = itemType === 'vin'
                ? canonicalVinFromKnownFacts(knownFacts)
                : itemType === 'vehicle_information'
                  ? canonicalVehicleFromKnownFacts(knownFacts)
                  : null;
            if (canonical) {
                return { ...embedded, canonical_value: canonical, applied_to_canonical_facts: false };
            }
        }
        return embedded;
    }

    const itemId = String(item.request_item_id || '').trim();
    if (!itemId) return null;
    const events = projection?.latest_events ?? [];
    let receipt: Record<string, unknown> | null = null;
    for (const event of events) {
        if (!event || typeof event !== 'object') continue;
        const evidence = (event.evidence && typeof event.evidence === 'object')
            ? (event.evidence as Record<string, unknown>)
            : {};
        if (String(evidence.request_item_id || '') !== itemId) continue;
        const eventType = String(event.event_type || '');
        if (eventType === 'field_saved' || eventType === 'evidence_received') {
            receipt = event as Record<string, unknown>;
        }
    }

    if (!receipt) {
        if (String(item.status || '') === 'satisfied') {
            return {
                kind: 'missing',
                review_status: 'satisfied_missing_response',
                submitted_at: item.satisfied_at ?? null,
                applied_to_canonical_facts: false,
                message: 'Item is marked satisfied, but the submitted response value is missing from the event log.',
            };
        }
        return null;
    }

    const evidence = (receipt.evidence && typeof receipt.evidence === 'object')
        ? (receipt.evidence as Record<string, unknown>)
        : {};
    const submittedAt = String(receipt.created_at || item.satisfied_at || '') || null;
    const actor = String(receipt.actor || '') || null;
    const actorIdentity = String(receipt.actor_identity || '') || null;
    const receiptEventId = String(receipt.event_id || '') || null;
    const reviewStatus = String(item.status || '') === 'satisfied' ? 'satisfied' : String(item.status || '');
    const eventType = String(receipt.event_type || '');

    if (eventType === 'field_saved') {
        const submittedValue = evidence.value == null ? '' : String(evidence.value);
        const itemType = String(item.item_type || '').trim().toLowerCase();
        const canonical = itemType === 'vin'
            ? canonicalVinFromKnownFacts(knownFacts)
            : itemType === 'vehicle_information'
              ? canonicalVehicleFromKnownFacts(knownFacts)
              : null;
        return {
            kind: 'fact',
            field_id: String(evidence.field_id || '') || null,
            submitted_value: submittedValue,
            canonical_value: canonical,
            submitted_at: submittedAt,
            submitted_by_actor: actor,
            submitted_by: actorIdentity,
            receipt_event_id: receiptEventId,
            review_status: reviewStatus,
            applied_to_canonical_facts: Boolean(canonical),
        };
    }

    const attachmentId = String(evidence.attachment_id || '').trim();
    return {
        kind: 'evidence',
        attachment_id: attachmentId || null,
        evidence_ref: attachmentId || null,
        submitted_at: submittedAt,
        submitted_by_actor: actor,
        submitted_by: actorIdentity,
        receipt_event_id: receiptEventId,
        review_status: reviewStatus,
        applied_to_canonical_facts: false,
    };
}

export function formatSlice1ResponseSource(response: Slice1CustomerResponse | null): string {
    if (!response) return '—';
    const actor = String(response.submitted_by_actor || '').trim();
    const identity = String(response.submitted_by || '').trim();
    if (actor && identity) return `${actor} · ${identity}`;
    return identity || actor || '—';
}

export function mergeSlice1ProjectionIntoCaseRecord<TCase extends StructuredRequestMoreCaseRecord>(
    caseRecord: TCase,
    result: Pick<Slice1CommandResult, 'broker_projection' | 'request_summary' | 'server_timestamp'>,
): TCase | null {
    const projection = result.broker_projection;
    if (!projection || !caseRecord.case_id) return null;
    return {
        ...caseRecord,
        slice1_capability_version: 1,
        p20_slice1_capability_version: 1,
        slice1_projection: projection,
        p20_slice1_projection: projection,
        slice1_request_summary: result.request_summary ?? projection.open_request ?? undefined,
        p20_slice1_request_summary: result.request_summary ?? projection.open_request ?? undefined,
        workflow_phase:
            projection.workflow_state === 'broker_more_requested'
                ? 'broker_more_requested'
                : projection.workflow_state === 'broker_review_ready'
                  ? 'intake_ready_for_broker'
                  : caseRecord.workflow_phase,
        display_status:
            projection.workflow_state === 'broker_more_requested'
                ? CLAIM_PILOT_STATUS.waitingCustomer
                : projection.workflow_state === 'broker_review_ready'
                  ? CLAIM_PILOT_STATUS.waitingBroker
                  : caseRecord.display_status,
        updated_at: result.server_timestamp ?? caseRecord.updated_at,
    } as TCase;
}

export function getStructuredRequestMoreVisibility(caseRecord: StructuredRequestMoreCaseRecord | null): {
    supported: boolean;
    enabled: boolean;
    terminal: boolean;
    canCreate: boolean;
} {
    return {
        supported: isStructuredRequestMoreSupportedCase(caseRecord),
        enabled: slice1EnabledForWorkbenchCase(caseRecord),
        terminal: isStructuredRequestMoreTerminal(caseRecord),
        canCreate: slice1CanCreateRequest(caseRecord),
    };
}

export function StructuredRequestMorePanel<TCase extends StructuredRequestMoreCaseRecord>({
    caseRecord,
    projectionLoading = false,
    projectionLoadError = null,
    onCaseChange,
    refreshCase,
}: StructuredRequestMorePanelProps<TCase>) {
    const [requestMoreOpen, setRequestMoreOpen] = useState(false);
    const [requestMoreReason, setRequestMoreReason] = useState('');
    const [requestMoreItems, setRequestMoreItems] = useState<RequestMoreDraftItem[]>([defaultRequestMoreItem()]);
    const [requestMoreSubmitState, setRequestMoreSubmitState] = useState<RequestMoreSubmitState>('idle');
    const [requestMoreError, setRequestMoreError] = useState<string | null>(null);
    const [requestMoreConflict, setRequestMoreConflict] = useState<string | null>(null);
    const [requestMoreCommandIdentity, setRequestMoreCommandIdentity] = useState<RequestMoreCommandIdentity | null>(null);
    const mountedRef = useRef(true);
    const requestMoreSubmitSeqRef = useRef(0);

    useEffect(() => {
        mountedRef.current = true;
        return () => {
            mountedRef.current = false;
        };
    }, []);

    if (!caseRecord || !isStructuredRequestMoreSupportedCase(caseRecord)) return null;

    const enabled = slice1EnabledForWorkbenchCase(caseRecord);
    if (!enabled || isStructuredRequestMoreTerminal(caseRecord)) return null;

    const projection = normalizeSlice1Projection(caseRecord);
    const summary = normalizeSlice1RequestSummary(caseRecord);
    const orderedItems = orderedSlice1Items(summary);
    const activeItem = summary?.active_item ?? orderedItems.find((item) => item.status === 'active') ?? null;
    const queuedItems = orderedItems.filter((item) => item.status === 'queued');
    const satisfiedItems = orderedItems.filter((item) => item.status === 'satisfied');
    const progress = summary?.progress ?? projection?.request_progress;
    const brokerAction = projection?.broker_next_action;
    const customerAction = projection?.customer_next_action;
    const canCreate = !projectionLoading && !projectionLoadError && slice1CanCreateRequest(caseRecord);
    const reviewReady = projection?.workflow_state === 'broker_review_ready' || brokerAction?.action_type === 'review_customer_response';
    const satisfiedMissingResponse = satisfiedItems.some((item) => {
        const response = resolveSlice1CustomerResponse(
            item,
            projection,
            caseRecord.known_facts as Record<string, unknown> | undefined,
        );
        if (!response || response.kind === 'missing') return true;
        if (response.kind === 'fact') return !String(response.submitted_value ?? '').length;
        if (response.kind === 'evidence') {
            return !String(response.evidence_ref || response.attachment_id || '').length;
        }
        return false;
    });

    const validateRequestMoreDraft = (): string | null => {
        if (!requestMoreItems.length) return 'Add at least one requested item.';
        const seen = new Set<string>();
        for (const item of requestMoreItems) {
            const label = item.label.trim();
            const instructions = item.instructions.trim();
            if (!label) return 'Each requested item needs a customer-facing label.';
            if (!instructions) return `Add concise instructions for "${label}".`;
            if (!SLICE1_REQUEST_MORE_TYPES.some((option) => option.value === item.item_type)) {
                return `Unsupported request item type for "${label}".`;
            }
            const duplicateKey = `${item.item_type}:${label.toLowerCase()}`;
            if (seen.has(duplicateKey)) return `Duplicate requested item: ${label}.`;
            seen.add(duplicateKey);
        }
        return null;
    };

    const openRequestMoreComposer = () => {
        if (!caseRecord.case_id || !canCreate) return;
        setRequestMoreItems((items) => (items.length ? items : [defaultRequestMoreItem()]));
        setRequestMoreReason((reason) => reason || '请按以下说明补充理赔所需资料。');
        setRequestMoreError(null);
        setRequestMoreConflict(null);
        setRequestMoreSubmitState('idle');
        setRequestMoreCommandIdentity(null);
        setRequestMoreOpen(true);
    };

    const addRequestMorePreset = (presetKey: string) => {
        const preset = SLICE1_REQUEST_MORE_PRESETS.find((item) => item.key === presetKey);
        if (!preset) return;
        setRequestMoreItems((items) => {
            const duplicate = items.some(
                (item) => item.item_type === preset.item_type && item.label.trim().toLowerCase() === preset.label.toLowerCase(),
            );
            if (duplicate) {
                message.warning('该项已在列表中。');
                return items;
            }
            return [
                ...items,
                {
                    item_type: preset.item_type,
                    label: preset.label,
                    instructions: preset.instructions,
                    required: true,
                    position: items.length + 1,
                },
            ];
        });
    };

    const updateRequestMoreItem = (index: number, patch: Partial<RequestMoreDraftItem>) => {
        setRequestMoreItems((items) =>
            items
                .map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item))
                .map((item, itemIndex) => ({ ...item, position: itemIndex + 1 })),
        );
    };

    const moveRequestMoreItem = (index: number, direction: -1 | 1) => {
        setRequestMoreItems((items) => {
            const nextIndex = index + direction;
            if (nextIndex < 0 || nextIndex >= items.length) return items;
            const next = [...items];
            const [item] = next.splice(index, 1);
            next.splice(nextIndex, 0, item);
            return next.map((row, rowIndex) => ({ ...row, position: rowIndex + 1 }));
        });
    };

    const removeRequestMoreItem = (index: number) => {
        setRequestMoreItems((items) => {
            if (items.length <= 1) return items;
            return items
                .filter((_, itemIndex) => itemIndex !== index)
                .map((item, itemIndex) => ({ ...item, position: itemIndex + 1 }));
        });
    };

    const mergeResultIntoCase = (result: Pick<Slice1CommandResult, 'broker_projection' | 'request_summary' | 'server_timestamp'>) => {
        const merged = mergeSlice1ProjectionIntoCaseRecord(caseRecord, result);
        if (!merged) return null;
        onCaseChange(merged);
        return merged;
    };

    const refreshAuthoritativeCase = async () => {
        if (!refreshCase) return null;
        const refreshed = await refreshCase();
        if (!mountedRef.current || !refreshed) return null;
        onCaseChange(refreshed);
        return refreshed;
    };

    const handleSubmitRequestMore = async () => {
        if (!caseRecord.case_id) return;
        if (requestMoreSubmitState === 'submitting') return;
        const validation = validateRequestMoreDraft();
        if (validation) {
            setRequestMoreError(validation);
            return;
        }
        const identity = requestMoreCommandIdentity ?? makeRequestMoreCommandIdentity(caseRecord.case_id, slice1CaseVersion(caseRecord));
        const seq = ++requestMoreSubmitSeqRef.current;
        setRequestMoreCommandIdentity(identity);
        setRequestMoreSubmitState('submitting');
        setRequestMoreError(null);
        setRequestMoreConflict(null);
        try {
            const result = await createCaseRequestMore(caseRecord.case_id, {
                ...identity,
                correlation_id: identity.command_id,
                expected_case_version: identity.expected_case_version,
                reason: requestMoreReason,
                requested_items: requestMoreItems.map((item, index) => ({
                    ...item,
                    label: item.label.trim(),
                    instructions: item.instructions.trim(),
                    position: index + 1,
                })),
            });
            if (!mountedRef.current || seq !== requestMoreSubmitSeqRef.current) return;
            mergeResultIntoCase(result);
            setRequestMoreSubmitState('success');
            setRequestMoreCommandIdentity(null);
            setRequestMoreOpen(false);
            message.success(
                result.outcome === 'replayed'
                    ? CLAIM_REQUEST_MORE_COPY.structuredAlreadySaved
                    : CLAIM_REQUEST_MORE_COPY.structuredSent,
            );
        } catch (error) {
            if (!mountedRef.current || seq !== requestMoreSubmitSeqRef.current) return;
            if (error instanceof Slice1RequestMoreError) {
                if (error.kind === 'version_conflict') {
                    setRequestMoreSubmitState('conflict');
                    setRequestMoreConflict(CLAIM_REQUEST_MORE_COPY.structuredConflict);
                    if (error.result) {
                        mergeResultIntoCase(error.result);
                    }
                    try {
                        await refreshAuthoritativeCase();
                    } catch {
                        /* conflict response already carried the authoritative projection */
                    }
                    setRequestMoreCommandIdentity(null);
                    return;
                }
                if (error.kind === 'timeout') {
                    setRequestMoreSubmitState('retry_ready');
                    setRequestMoreError(CLAIM_REQUEST_MORE_COPY.structuredTimeout);
                    try {
                        await refreshAuthoritativeCase();
                    } catch {
                        /* keep retry available */
                    }
                    return;
                }
                const messageText =
                    error.kind === 'feature_disabled'
                        ? CLAIM_REQUEST_MORE_COPY.structuredNotEnabled
                        : error.kind === 'authorization'
                          ? CLAIM_REQUEST_MORE_COPY.structuredUnauthorized
                          : error.kind === 'validation'
                            ? CLAIM_REQUEST_MORE_COPY.structuredValidation
                            : CLAIM_REQUEST_MORE_COPY.structuredFailed;
                setRequestMoreSubmitState('error');
                setRequestMoreError(messageText);
                return;
            }
            setRequestMoreSubmitState('error');
            setRequestMoreError(CLAIM_REQUEST_MORE_COPY.structuredFailed);
        }
    };

    const renderSlice1RequestItem = (item: Slice1RequestItem) => {
        const status = String(item.status || '').trim();
        const color =
            status === 'active'
                ? 'blue'
                : status === 'queued'
                  ? 'default'
                  : status === 'satisfied'
                    ? 'green'
                    : 'orange';
        const response = resolveSlice1CustomerResponse(
            item,
            projection,
            caseRecord.known_facts as Record<string, unknown> | undefined,
        );
        const showResponseBlock = status === 'satisfied' || Boolean(response);
        const submittedAt = response?.submitted_at || item.satisfied_at || null;
        const missingResponse = status === 'satisfied' && (
            !response
            || response.kind === 'missing'
            || (response.kind === 'fact' && !String(response.submitted_value ?? '').length)
            || (response.kind === 'evidence' && !String(response.evidence_ref || response.attachment_id || '').length)
        );

        return (
            <div key={item.request_item_id || `${item.position}-${item.label}`} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Space wrap size={[6, 4]}>
                    <Tag color={color}>#{item.position} {status || 'pending'}</Tag>
                    <Tag>{item.item_type || 'item'}</Tag>
                    <Text strong style={{ fontSize: 13 }}>{item.label}</Text>
                    {item.required
                        ? <Tag color="red">{CLAIM_REQUEST_MORE_COPY.required}</Tag>
                        : <Tag>{CLAIM_REQUEST_MORE_COPY.optional}</Tag>}
                </Space>
                {item.instructions ? (
                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                        {item.instructions}
                    </Text>
                ) : null}
                {showResponseBlock ? (
                    <div style={{ marginTop: 8, padding: 8, background: '#fafafa', borderRadius: 6 }}>
                        {missingResponse ? (
                            <Alert
                                type="warning"
                                showIcon
                                message="客户提交内容尚未显示"
                                description={response?.message || '请刷新案件。在看到客户提交内容前，请勿当作已可核对。'}
                                style={{ marginBottom: 6 }}
                            />
                        ) : null}
                        {response?.kind === 'fact' && !missingResponse ? (
                            <>
                                <Text style={{ display: 'block', fontSize: 13 }}>
                                    {CLAIM_REQUEST_MORE_COPY.submittedValue}：{' '}
                                    <Text code copyable={{ text: String(response.submitted_value ?? '') }}>
                                        {String(response.submitted_value ?? '')}
                                    </Text>
                                </Text>
                                {response.canonical_value ? (
                                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 2 }}>
                                        {canonicalFactLabelForItemType(item.item_type)}：
                                        <Text code>{String(response.canonical_value)}</Text>
                                        {String(response.canonical_value) !== String(response.submitted_value ?? '')
                                            ? '（与客户提交不一致）'
                                            : null}
                                    </Text>
                                ) : null}
                            </>
                        ) : null}
                        {response?.kind === 'evidence' && !missingResponse ? (
                            <Text style={{ display: 'block', fontSize: 13 }}>
                                附件：{' '}
                                <Text code>{String(response.evidence_ref || response.attachment_id || '已上传')}</Text>
                                {caseRecord.case_id && (response.attachment_id || response.evidence_ref) ? (
                                    <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 2 }}>
                                        请在案件附件中查看。
                                    </Text>
                                ) : null}
                            </Text>
                        ) : null}
                        <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 4 }}>
                            {CLAIM_REQUEST_MORE_COPY.submittedAt}{' '}
                            {submittedAt ? (formatPortalLocalDateTime(submittedAt) ?? submittedAt) : '—'}
                            {' · '}
                            {CLAIM_REQUEST_MORE_COPY.source} {formatSlice1ResponseSource(response)}
                        </Text>
                    </div>
                ) : item.satisfied_at ? (
                    <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 2 }}>
                        已提交 {formatPortalLocalDateTime(item.satisfied_at) ?? item.satisfied_at}
                    </Text>
                ) : null}
            </div>
        );
    };

    return (
        <Card
            size="small"
            title={
                <Space wrap>
                    <span>{CLAIM_REQUEST_MORE_COPY.structuredPanelTitle}</span>
                    {reviewReady ? (
                        <Tag color="success">{CLAIM_PILOT_STATUS.waitingBroker}</Tag>
                    ) : summary ? (
                        <Tag color="processing">{CLAIM_PILOT_STATUS.waitingCustomer}</Tag>
                    ) : (
                        <Tag color="default">{CLAIM_PILOT_STATUS.needMaterials}</Tag>
                    )}
                </Space>
            }
            extra={
                canCreate ? (
                    <Button size="small" type="primary" onClick={openRequestMoreComposer}>
                        {CLAIM_REQUEST_MORE_COPY.structuredCreate}
                    </Button>
                ) : null
            }
            styles={{ body: { padding: 12 } }}
            style={{ borderRadius: 8, borderColor: reviewReady ? '#b7eb8f' : '#91caff', marginBottom: 12 }}
        >
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
                {projectionLoading ? <Alert type="info" showIcon message={CLAIM_REQUEST_MORE_COPY.loading} /> : null}
                {projectionLoadError ? (
                    <Alert
                        type="error"
                        showIcon
                        message={CLAIM_REQUEST_MORE_COPY.loadFailed}
                        description={projectionLoadError}
                        action={refreshCase ? <Button size="small" onClick={() => void refreshAuthoritativeCase()}>{CLAIM_REQUEST_MORE_COPY.retryLoad}</Button> : undefined}
                    />
                ) : null}
                {requestMoreConflict ? <Alert type="warning" showIcon message={requestMoreConflict} /> : null}
                {requestMoreSubmitState === 'success' ? (
                    <Alert type="success" showIcon message={CLAIM_REQUEST_MORE_COPY.structuredSent} />
                ) : null}
                {!summary ? (
                    <Alert
                        type={canCreate ? 'info' : 'warning'}
                        showIcon
                        message={canCreate ? CLAIM_REQUEST_MORE_COPY.structuredReady : CLAIM_REQUEST_MORE_COPY.structuredEmpty}
                        description={canCreate ? CLAIM_REQUEST_MORE_COPY.structuredCreateHint : CLAIM_REQUEST_MORE_COPY.structuredRefreshHint}
                    />
                ) : (
                    <>
                        <Space wrap size={[6, 4]}>
                            <Tag color={summary.status === 'completed' ? 'green' : 'blue'}>
                                {summary.status === 'completed'
                                    ? CLAIM_PILOT_STATUS.completed
                                    : CLAIM_PILOT_STATUS.waitingCustomer}
                            </Tag>
                            {progress ? (
                                <Tag color={progress.remaining === 0 ? 'green' : 'gold'}>
                                    {CLAIM_REQUEST_MORE_COPY.progressLine(progress.satisfied, progress.total)}
                                </Tag>
                            ) : null}
                        </Space>
                        {summary.reason ? (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                给客户的说明：{summary.reason}
                            </Text>
                        ) : null}
                        {activeItem ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>{CLAIM_REQUEST_MORE_COPY.activeItem}</Text>
                                {renderSlice1RequestItem(activeItem)}
                            </div>
                        ) : null}
                        {queuedItems.length > 0 ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>{CLAIM_REQUEST_MORE_COPY.queuedItems}</Text>
                                {queuedItems.map(renderSlice1RequestItem)}
                            </div>
                        ) : null}
                        {satisfiedItems.length > 0 ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>{CLAIM_REQUEST_MORE_COPY.satisfiedItems}</Text>
                                {satisfiedItems.map(renderSlice1RequestItem)}
                            </div>
                        ) : null}
                    </>
                )}
                <div style={{ padding: 10, background: '#fafafa', borderRadius: 6 }}>
                    <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                        {CLAIM_REQUEST_MORE_COPY.customerNext}：{customerAction?.title || customerAction?.action_type || '—'}
                    </Text>
                    <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                        {CLAIM_REQUEST_MORE_COPY.brokerNext}：{' '}
                        {brokerAction?.action_type === 'review_customer_response'
                            ? CLAIM_REQUEST_MORE_COPY.brokerNextReview
                            : brokerAction?.action_type || (canCreate ? CLAIM_REQUEST_MORE_COPY.brokerNextCreate : '—')}
                    </Text>
                    {reviewReady && satisfiedMissingResponse ? (
                        <Alert
                            type="error"
                            showIcon
                            style={{ marginTop: 8 }}
                            message="暂不能核对：客户提交内容未显示"
                            description="进度显示已齐，但至少一项已提交内容未显示。请先刷新案件。"
                        />
                    ) : null}
                    {reviewReady && !satisfiedMissingResponse ? (
                        <Alert
                            type="success"
                            showIcon
                            style={{ marginTop: 8 }}
                            message={CLAIM_REQUEST_MORE_COPY.reviewReady}
                            description={CLAIM_REQUEST_MORE_COPY.reviewReadyBody}
                        />
                    ) : null}
                    <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 6 }}>
                        {CLAIM_REQUEST_MORE_COPY.lastUpdated}：{' '}
                        {projection?.server_timestamp
                            ? (formatPortalLocalDateTime(projection.server_timestamp) ?? projection.server_timestamp)
                            : '—'}
                    </Text>
                </div>
            </Space>
            <Modal
                title={CLAIM_REQUEST_MORE_COPY.modalTitle}
                open={requestMoreOpen}
                onCancel={() => {
                    if (requestMoreSubmitState !== 'submitting') setRequestMoreOpen(false);
                }}
                okText={requestMoreSubmitState === 'retry_ready' ? CLAIM_REQUEST_MORE_COPY.modalRetry : CLAIM_REQUEST_MORE_COPY.modalOk}
                okButtonProps={{
                    loading: requestMoreSubmitState === 'submitting',
                    disabled: requestMoreSubmitState === 'submitting',
                }}
                cancelButtonProps={{ disabled: requestMoreSubmitState === 'submitting' }}
                onOk={() => void handleSubmitRequestMore()}
                destroyOnClose={false}
            >
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    {requestMoreError ? (
                        <Alert type={requestMoreSubmitState === 'retry_ready' ? 'warning' : 'error'} showIcon message={requestMoreError} />
                    ) : null}
                    {requestMoreConflict ? <Alert type="warning" showIcon message={requestMoreConflict} /> : null}
                    <div>
                        <Text strong style={{ display: 'block', marginBottom: 6 }}>{CLAIM_REQUEST_MORE_COPY.groupInstructions}</Text>
                        <TextArea
                            value={requestMoreReason}
                            onChange={(event) => setRequestMoreReason(event.target.value)}
                            maxLength={1000}
                            rows={2}
                            disabled={requestMoreSubmitState === 'submitting'}
                        />
                    </div>
                    <Select
                        placeholder={CLAIM_REQUEST_MORE_COPY.addPreset}
                        options={SLICE1_REQUEST_MORE_PRESETS.map((preset) => ({ value: preset.key, label: preset.label }))}
                        onSelect={(value) => addRequestMorePreset(String(value))}
                        value={undefined}
                        disabled={requestMoreSubmitState === 'submitting'}
                        style={{ width: '100%' }}
                    />
                    {requestMoreItems.map((item, index) => (
                        <Card key={`${index}-${item.position}`} size="small" styles={{ body: { padding: 10 } }}>
                            <Space direction="vertical" size={8} style={{ width: '100%' }}>
                                <Space wrap>
                                    <Tag>#{index + 1}</Tag>
                                    <Select
                                        value={item.item_type}
                                        options={SLICE1_REQUEST_MORE_TYPES}
                                        onChange={(value) => {
                                            const meta = SLICE1_REQUEST_MORE_TYPES.find((option) => option.value === value);
                                            updateRequestMoreItem(index, {
                                                item_type: value,
                                                ...(meta ? { label: meta.label } : {}),
                                            });
                                        }}
                                        disabled={requestMoreSubmitState === 'submitting'}
                                        style={{ width: 190 }}
                                    />
                                    <Button size="small" onClick={() => moveRequestMoreItem(index, -1)} disabled={index === 0 || requestMoreSubmitState === 'submitting'}>
                                        上移
                                    </Button>
                                    <Button size="small" onClick={() => moveRequestMoreItem(index, 1)} disabled={index === requestMoreItems.length - 1 || requestMoreSubmitState === 'submitting'}>
                                        下移
                                    </Button>
                                    <Button size="small" danger onClick={() => removeRequestMoreItem(index)} disabled={requestMoreItems.length <= 1 || requestMoreSubmitState === 'submitting'}>
                                        移除
                                    </Button>
                                </Space>
                                <Input
                                    value={item.label}
                                    placeholder={CLAIM_REQUEST_MORE_COPY.customerLabelPlaceholder}
                                    maxLength={160}
                                    onChange={(event) => updateRequestMoreItem(index, { label: event.target.value })}
                                    disabled={requestMoreSubmitState === 'submitting'}
                                />
                                <TextArea
                                    value={item.instructions}
                                    placeholder={CLAIM_REQUEST_MORE_COPY.customerInstructionPlaceholder}
                                    maxLength={1000}
                                    rows={2}
                                    onChange={(event) => updateRequestMoreItem(index, { instructions: event.target.value })}
                                    disabled={requestMoreSubmitState === 'submitting'}
                                />
                            </Space>
                        </Card>
                    ))}
                    <Button
                        onClick={() => setRequestMoreItems((items) => [...items, defaultRequestMoreItem(items.length + 1)])}
                        disabled={requestMoreSubmitState === 'submitting'}
                    >
                        {CLAIM_REQUEST_MORE_COPY.addBlank}
                    </Button>
                </Space>
            </Modal>
        </Card>
    );
}
