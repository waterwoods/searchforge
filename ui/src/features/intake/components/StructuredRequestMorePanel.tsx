import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Card, Input, Modal, Select, Space, Tag, Typography, message } from 'antd';
import {
    createCaseRequestMore,
    Slice1RequestMoreError,
    type RequestMoreDraftItem,
    type Slice1CommandResult,
    type Slice1Projection,
    type Slice1RequestItem,
    type Slice1RequestItemType,
    type Slice1RequestSummary,
    type TriageResult,
} from '@/api/inboxTriage';
import { formatPortalLocalDateTime } from '@/features/intake/utils/intakePure';

const { TextArea } = Input;
const { Text } = Typography;

const SLICE1_REQUEST_MORE_TYPES: Array<{ value: Slice1RequestItemType; label: string }> = [
    { value: 'vin', label: 'VIN' },
    { value: 'policy_or_insurance_card', label: 'Insurance card' },
    { value: 'photo_evidence', label: 'Photo / document evidence' },
    { value: 'free_text', label: 'Other confirmation' },
];

const SLICE1_REQUEST_MORE_PRESETS: Array<{
    key: string;
    label: string;
    item_type: Slice1RequestItemType;
    instructions: string;
}> = [
    { key: 'vin', label: 'VIN', item_type: 'vin', instructions: 'Please send or confirm the vehicle VIN.' },
    {
        key: 'insurance_card',
        label: 'Insurance card',
        item_type: 'policy_or_insurance_card',
        instructions: 'Please upload a clear photo of the insurance card.',
    },
    {
        key: 'damage_photos',
        label: 'Damage photos',
        item_type: 'photo_evidence',
        instructions: 'Please upload clear photos of the vehicle damage.',
    },
    {
        key: 'police_report',
        label: 'Police report',
        item_type: 'photo_evidence',
        instructions: 'If available, please upload a police report photo or document.',
    },
    {
        key: 'incident_date',
        label: 'Incident date confirmation',
        item_type: 'free_text',
        instructions: 'Please confirm the accident date and approximate time.',
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
        item_type: 'vin',
        label: 'VIN',
        instructions: 'Please send or confirm the vehicle VIN.',
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
    if (caseRecord.workbench_archived) return true;
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
    ]
        .map((value) => String(value ?? '').trim().toLowerCase())
        .filter(Boolean);
    return rawStates.some((state) =>
        ['done', 'case_complete', 'complete', 'completed', 'cancelled', 'canceled', 'rejected', 'archived'].includes(state),
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
                ? 'Claim · Request More'
                : projection.workflow_state === 'broker_review_ready'
                  ? 'Claim · Broker Review'
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
        setRequestMoreReason((reason) => reason || 'Please provide the requested claim information.');
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
                message.warning('This requested item is already in the list.');
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
            message.success(result.outcome === 'replayed' ? 'Request More already saved; refreshed current progress.' : 'Request More sent to customer.');
        } catch (error) {
            if (!mountedRef.current || seq !== requestMoreSubmitSeqRef.current) return;
            if (error instanceof Slice1RequestMoreError) {
                if (error.kind === 'version_conflict') {
                    setRequestMoreSubmitState('conflict');
                    setRequestMoreConflict('The case changed while you were editing. We refreshed the latest status. Review and submit again.');
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
                    setRequestMoreError('Network outcome is uncertain. Retry will use the same command identity.');
                    try {
                        await refreshAuthoritativeCase();
                    } catch {
                        /* keep retry available */
                    }
                    return;
                }
                const messageText =
                    error.kind === 'feature_disabled'
                        ? 'Structured Request More is not enabled for this case.'
                        : error.kind === 'authorization'
                          ? 'You are not authorized to request more on this case.'
                          : error.kind === 'validation'
                            ? 'Please review the requested items and submit again.'
                            : 'Request More failed. Please retry after refreshing the case.';
                setRequestMoreSubmitState('error');
                setRequestMoreError(messageText);
                return;
            }
            setRequestMoreSubmitState('error');
            setRequestMoreError('Request More failed. Please retry after refreshing the case.');
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
        return (
            <div key={item.request_item_id || `${item.position}-${item.label}`} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Space wrap size={[6, 4]}>
                    <Tag color={color}>#{item.position} {status || 'pending'}</Tag>
                    <Text strong style={{ fontSize: 13 }}>{item.label}</Text>
                    {item.required ? <Tag color="red">required</Tag> : <Tag>optional</Tag>}
                </Space>
                {item.instructions ? (
                    <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 4 }}>
                        {item.instructions}
                    </Text>
                ) : null}
                {item.satisfied_at ? (
                    <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 2 }}>
                        Satisfied {formatPortalLocalDateTime(item.satisfied_at) ?? item.satisfied_at}
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
                    <span>Structured Request More</span>
                    <Tag color="blue">Slice 1 enabled</Tag>
                </Space>
            }
            extra={
                canCreate ? (
                    <Button size="small" type="primary" onClick={openRequestMoreComposer}>
                        Request more
                    </Button>
                ) : null
            }
            styles={{ body: { padding: 12 } }}
            style={{ borderRadius: 8, borderColor: reviewReady ? '#b7eb8f' : '#91caff', marginBottom: 12 }}
        >
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
                {projectionLoading ? <Alert type="info" showIcon message="Loading authoritative Slice 1 projection..." /> : null}
                {projectionLoadError ? (
                    <Alert
                        type="error"
                        showIcon
                        message="Could not load authoritative Slice 1 projection."
                        description={projectionLoadError}
                        action={refreshCase ? <Button size="small" onClick={() => void refreshAuthoritativeCase()}>Retry</Button> : undefined}
                    />
                ) : null}
                {requestMoreConflict ? <Alert type="warning" showIcon message={requestMoreConflict} /> : null}
                {requestMoreSubmitState === 'success' ? <Alert type="success" showIcon message="Request More saved from server response." /> : null}
                {!summary ? (
                    <Alert
                        type={canCreate ? 'info' : 'warning'}
                        showIcon
                        message={canCreate ? 'Ready to create a structured Request More.' : 'No active structured request.'}
                        description={canCreate ? 'Create one ordered request group for the customer.' : 'Refresh the case before creating a new request.'}
                    />
                ) : (
                    <>
                        <Space wrap size={[6, 4]}>
                            <Tag color={summary.status === 'completed' ? 'green' : 'blue'}>Request {summary.status}</Tag>
                            {progress ? (
                                <Tag color={progress.remaining === 0 ? 'green' : 'gold'}>
                                    Progress {progress.satisfied}/{progress.total}
                                </Tag>
                            ) : null}
                            {projection?.workflow_state ? <Tag>{projection.workflow_state}</Tag> : null}
                        </Space>
                        {summary.reason ? (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                Customer instructions: {summary.reason}
                            </Text>
                        ) : null}
                        {activeItem ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>Active customer item</Text>
                                {renderSlice1RequestItem(activeItem)}
                            </div>
                        ) : null}
                        {queuedItems.length > 0 ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>Queued items</Text>
                                {queuedItems.map(renderSlice1RequestItem)}
                            </div>
                        ) : null}
                        {satisfiedItems.length > 0 ? (
                            <div>
                                <Text strong style={{ display: 'block', marginBottom: 4 }}>Satisfied items</Text>
                                {satisfiedItems.map(renderSlice1RequestItem)}
                            </div>
                        ) : null}
                    </>
                )}
                <div style={{ padding: 10, background: '#fafafa', borderRadius: 6 }}>
                    <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                        Customer next action: {customerAction?.title || customerAction?.action_type || '—'}
                    </Text>
                    <Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                        Broker next action: {brokerAction?.action_type === 'review_customer_response' ? 'Review customer response' : brokerAction?.action_type || (canCreate ? 'Create request' : '—')}
                    </Text>
                    {reviewReady ? (
                        <Button size="small" type="primary" style={{ marginTop: 8 }}>
                            Review customer response
                        </Button>
                    ) : null}
                    <Text type="secondary" style={{ display: 'block', fontSize: 11, marginTop: 6 }}>
                        Last server update: {projection?.server_timestamp ? (formatPortalLocalDateTime(projection.server_timestamp) ?? projection.server_timestamp) : '—'}
                    </Text>
                </div>
            </Space>
            <Modal
                title="Create Structured Request More"
                open={requestMoreOpen}
                onCancel={() => {
                    if (requestMoreSubmitState !== 'submitting') setRequestMoreOpen(false);
                }}
                okText={requestMoreSubmitState === 'retry_ready' ? 'Retry safely' : 'Send request'}
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
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        Timeout retry keeps the same command identity.
                    </Text>
                    <div>
                        <Text strong style={{ display: 'block', marginBottom: 6 }}>Customer-facing group instructions</Text>
                        <TextArea
                            value={requestMoreReason}
                            onChange={(event) => setRequestMoreReason(event.target.value)}
                            maxLength={1000}
                            rows={2}
                            disabled={requestMoreSubmitState === 'submitting'}
                        />
                    </div>
                    <Select
                        placeholder="Add preset requested item"
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
                                        onChange={(value) => updateRequestMoreItem(index, { item_type: value })}
                                        disabled={requestMoreSubmitState === 'submitting'}
                                        style={{ width: 190 }}
                                    />
                                    <Button size="small" onClick={() => moveRequestMoreItem(index, -1)} disabled={index === 0 || requestMoreSubmitState === 'submitting'}>
                                        Up
                                    </Button>
                                    <Button size="small" onClick={() => moveRequestMoreItem(index, 1)} disabled={index === requestMoreItems.length - 1 || requestMoreSubmitState === 'submitting'}>
                                        Down
                                    </Button>
                                    <Button size="small" danger onClick={() => removeRequestMoreItem(index)} disabled={requestMoreItems.length <= 1 || requestMoreSubmitState === 'submitting'}>
                                        Remove
                                    </Button>
                                </Space>
                                <Input
                                    value={item.label}
                                    placeholder="Customer-facing label"
                                    maxLength={160}
                                    onChange={(event) => updateRequestMoreItem(index, { label: event.target.value })}
                                    disabled={requestMoreSubmitState === 'submitting'}
                                />
                                <TextArea
                                    value={item.instructions}
                                    placeholder="Concise customer-facing instructions"
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
                        Add blank item
                    </Button>
                </Space>
            </Modal>
        </Card>
    );
}
