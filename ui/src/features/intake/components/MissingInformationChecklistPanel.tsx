/**
 * P20 Capability 2+3A — Missing Information Checklist + Request Draft + Send Request.
 * Broker selects/edits items, saves draft, then Send Request creates Slice 1 access + QR/link.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Checkbox,
  Collapse,
  Input,
  QRCode,
  Space,
  Tag,
  Typography,
  message,
} from 'antd';
import type {
  CaseIntakeProjection,
  CaseIntakeRequestDraftItem,
  CustomerAccessCard,
  SavedCase,
  Slice1Projection,
} from '@/api/inboxTriage';
import {
  Slice1RequestMoreError,
  requestMoreAiDraft,
  saveCaseRequestDraft,
  sendCaseRequest,
} from '@/api/inboxTriage';
import {
  brokerSendBlockedMessage,
  formatUnsupportedSendItems,
  isMvpSendableChecklistRow,
  isMvpSendableItemType,
} from '@/features/intake/mvpRequestTypes';
import {
  RequestDraftAutosaveController,
  type AutosavePhase,
} from '@/features/intake/components/requestDraftAutosave';
import {
  isStructuredRequestMoreTerminal,
  resolveSlice1CustomerResponse,
} from '@/features/intake/components/StructuredRequestMorePanel';
import {
  CLAIM_REQUEST_MORE_COPY,
} from '@/features/intake/utils/claimPilotCopy';
import {
  CLAIM_PRIMARY_STATUS,
  requestMoreOwnsPrimaryStatus,
} from '@/features/intake/utils/claimPrimaryStatus';
import { isClaimGuidedCase } from '@/features/intake/utils/claimWorkbenchDisplay';

const AUTOSAVE_DEBOUNCE_MS = 600;
/** Gentle while-open poll — avoid version churn / flicker. */
const CUSTOMER_STATUS_POLL_MS = 12000;

const { Text, Paragraph, Title } = Typography;
const { TextArea } = Input;

function newIds(prefix: string): { command_id: string; idempotency_key: string } {
  const stamp = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
  return {
    command_id: `${prefix}_${stamp}`,
    idempotency_key: `${prefix}_idem_${stamp}`,
  };
}

export function resolveCaseIntakeProjection(caseRecord: SavedCase | null): CaseIntakeProjection | null {
  if (!caseRecord) return null;
  const direct = caseRecord.p20_case_intake_projection || caseRecord.case_intake_projection;
  if (direct && typeof direct === 'object') return direct;
  if (Array.isArray(caseRecord.missing_information_checklist)) {
    return {
      case_id: caseRecord.case_id,
      aggregate_version: 0,
      is_test: Boolean(caseRecord.workbench_test),
      admin_lifecycle: caseRecord.admin_lifecycle,
      missing_information_checklist: caseRecord.missing_information_checklist,
      request_draft: caseRecord.request_draft || null,
      customer_access: caseRecord.customer_access || null,
      customer_next_action: null,
    };
  }
  return null;
}

export function resolveCustomerAccessCard(caseRecord: SavedCase | null): CustomerAccessCard | null {
  if (!caseRecord) return null;
  const fromCase = caseRecord.customer_access;
  if (fromCase && typeof fromCase === 'object') return fromCase;
  const fromProj = resolveCaseIntakeProjection(caseRecord)?.customer_access;
  if (fromProj && typeof fromProj === 'object') return fromProj;
  return null;
}

/**
 * Bound Mini Program customer: Request More attaches to Active Case via resume/session.
 * Primary Workbench flow should not require a new QR scan.
 */
export function isBoundMiniProgramCustomer(caseRecord: SavedCase | null): boolean {
  if (!caseRecord) return false;
  const binding = String(caseRecord.identity_binding_state || '').trim().toLowerCase();
  const source = String(caseRecord.person_link_source || '').trim().toLowerCase();
  const channel = String(
    (caseRecord as SavedCase & { entry_channel?: string; source_channel?: string }).entry_channel
      || (caseRecord as SavedCase & { source_channel?: string }).source_channel
      || '',
  )
    .trim()
    .toLowerCase();
  const actor = String(
    (caseRecord as SavedCase & { created_by_actor?: string }).created_by_actor || '',
  )
    .trim()
    .toLowerCase();
  if (binding === 'linked' && (source === 'wechat' || Boolean(caseRecord.person_link_key))) {
    return true;
  }
  if (
    channel === 'mini_program'
    || channel === 'wechat_mp'
    || channel === 'wechat_mini_program'
  ) {
    return true;
  }
  if (actor === 'customer' && source === 'wechat') {
    return true;
  }
  return false;
}

/**
 * Authoritative CAS version for Send Request.
 * Prefer the version returned by the just-completed flush/save — never a stale
 * React projection that has not re-rendered yet.
 */
export function resolveSendExpectedVersion(args: {
  flushedVersion?: number | null;
  lastAcceptedVersion?: number | null;
  projectionVersion?: number | null;
}): number {
  if (typeof args.flushedVersion === 'number' && Number.isFinite(args.flushedVersion)) {
    return args.flushedVersion;
  }
  if (typeof args.lastAcceptedVersion === 'number' && Number.isFinite(args.lastAcceptedVersion)) {
    return args.lastAcceptedVersion;
  }
  if (typeof args.projectionVersion === 'number' && Number.isFinite(args.projectionVersion)) {
    return args.projectionVersion;
  }
  return 0;
}

export type SendErrorDisposition = {
  kind: 'version_conflict' | 'timeout' | 'rejected' | 'other';
  clearCommandIdentity: boolean;
  userMessage: string;
  toast: string;
};

/** Map Send Request failures to one recoverable broker action. */
export function classifySendRequestError(err: unknown): SendErrorDisposition {
  if (err instanceof Slice1RequestMoreError) {
    if (err.kind === 'version_conflict') {
      return {
        kind: 'version_conflict',
        clearCommandIdentity: true,
        userMessage: CLAIM_REQUEST_MORE_COPY.caseUpdatedReview,
        toast: CLAIM_REQUEST_MORE_COPY.caseUpdatedToast,
      };
    }
    if (err.kind === 'timeout') {
      return {
        kind: 'timeout',
        clearCommandIdentity: false,
        userMessage: CLAIM_REQUEST_MORE_COPY.networkUncertain,
        toast: CLAIM_REQUEST_MORE_COPY.networkUncertainToast,
      };
    }
    if (err.kind === 'validation' || err.kind === 'feature_disabled' || err.kind === 'authorization') {
      return {
        kind: 'rejected',
        clearCommandIdentity: true,
        userMessage: err.message || CLAIM_REQUEST_MORE_COPY.sendRejected,
        toast: err.message || CLAIM_REQUEST_MORE_COPY.sendRejected,
      };
    }
    return {
      kind: 'other',
      clearCommandIdentity: false,
      userMessage: err.message || CLAIM_REQUEST_MORE_COPY.sendFailedRetry,
      toast: err.message || CLAIM_REQUEST_MORE_COPY.sendFailedRetry,
    };
  }
  const status = (err as { response?: { status?: number }; status?: number })?.response?.status
    ?? (err as { status?: number })?.status;
  if (status === 409) {
    return {
      kind: 'version_conflict',
      clearCommandIdentity: true,
      userMessage: CLAIM_REQUEST_MORE_COPY.caseUpdatedReview,
      toast: CLAIM_REQUEST_MORE_COPY.caseUpdatedToast,
    };
  }
  return {
    kind: 'other',
    clearCommandIdentity: false,
    userMessage: CLAIM_REQUEST_MORE_COPY.sendFailedRetry,
    toast: CLAIM_REQUEST_MORE_COPY.sendFailedRetry,
  };
}

export function resolveAccessReviewState(
  access: CustomerAccessCard | null | undefined,
  slice1Projection?: Slice1Projection | null,
): {
  reviewReady: boolean;
  satisfied: number;
  total: number;
  simpleStatus: string;
  submittedVin: string | null;
} {
  const openRequest = slice1Projection?.open_request;
  const total =
    openRequest?.progress?.total
    ?? access?.progress?.total_count
    ?? 0;
  const satisfied =
    openRequest?.progress?.satisfied
    ?? access?.progress?.satisfied_count
    ?? 0;
  const ws = String(slice1Projection?.workflow_state || '').trim().toLowerCase();
  // After「已核对补充资料」, leave waiting-office-review chrome.
  const reviewReady =
    ws !== 'broker_reviewing'
    && (
      ws === 'broker_review_ready'
      || slice1Projection?.broker_next_action?.action_type === 'review_customer_response'
      || slice1Projection?.broker_next_action?.status === 'review_ready'
      || (
        !ws
        && (
          String(access?.simple_status || '').toLowerCase().includes('ready for review')
          || (total > 0 && satisfied >= total)
        )
      )
    );

  let submittedVin: string | null = null;
  for (const item of openRequest?.items || []) {
    if (String(item.item_type || '').toLowerCase() !== 'vin') continue;
    const response = resolveSlice1CustomerResponse(item, slice1Projection || null);
    if (response?.kind === 'fact' && response.submitted_value) {
      submittedVin = String(response.submitted_value);
      break;
    }
  }

  return {
    reviewReady,
    satisfied,
    total,
    // Align Request More chrome with Claim primary-status vocabulary.
    simpleStatus: reviewReady
      ? CLAIM_PRIMARY_STATUS.waitingOfficeReview
      : CLAIM_PRIMARY_STATUS.waitingCustomer,
    submittedVin,
  };
}

type DraftEditRow = {
  field_key: string;
  item_type: string;
  label: string;
  instructions: string;
  selected: boolean;
  request_mode: string;
  status: string;
  value?: string | null;
  previous_value?: string | null;
  is_authoritative_fact?: boolean;
};

type SaveStatus = 'idle' | 'unsaved' | 'saving' | 'saved' | 'failed';

export function buildDraftItemsFromRows(rows: DraftEditRow[]): CaseIntakeRequestDraftItem[] {
  return rows
    .filter((r) => r.selected && isMvpSendableItemType(r.item_type))
    .map((r, index) => ({
      field_key: r.field_key,
      item_type: r.item_type,
      label: r.label.trim() || r.field_key,
      instructions: r.instructions.trim(),
      required: true,
      position: index + 1,
      request_mode: r.request_mode,
      selected: true,
    }));
}

function unsupportedDraftItemLabels(items: CaseIntakeRequestDraftItem[] | undefined): string[] {
  return (items || [])
    .filter((item) => !isMvpSendableItemType(item.item_type))
    .map((item) => String(item.label || item.field_key || item.item_type || '').trim())
    .filter(Boolean);
}

export function rowsFromProjection(projection: CaseIntakeProjection): DraftEditRow[] {
  const checklist = projection.missing_information_checklist || [];
  const draftItems = projection.request_draft?.items || [];
  const selectedKeys = new Set(
    draftItems.map((i) => String(i.field_key || '')).filter(Boolean),
  );
  const instructionByKey = new Map(
    draftItems.map((i) => [String(i.field_key || ''), String(i.instructions || '')] as const),
  );
  const labelByKey = new Map(
    draftItems.map((i) => [String(i.field_key || ''), String(i.label || '')] as const),
  );
  return checklist.map((item) => {
    const key = item.field_key;
    const sendable = isMvpSendableChecklistRow(item);
    // Only restore an explicit saved draft selection — never auto-check suggested
    // optional items when Cap2 Must Haves are already complete (Chen demo P1).
    const defaultSelected = sendable && selectedKeys.size > 0 && selectedKeys.has(key);
    return {
      field_key: key,
      item_type: item.item_type,
      label: labelByKey.get(key) || item.customer_label || item.label,
      instructions: instructionByKey.get(key) || '',
      selected: defaultSelected,
      request_mode: item.request_mode || 'request_missing',
      status: item.status,
      value: item.value,
      previous_value: item.previous_value,
      is_authoritative_fact: item.is_authoritative_fact,
    };
  });
}

function CustomerAccessReadyCard({
  access,
  draftItems,
  slice1Projection,
  onEdit,
  showEdit,
  onRefreshStatus,
  refreshing,
  boundMiniProgram,
}: {
  access: CustomerAccessCard;
  draftItems: CaseIntakeRequestDraftItem[];
  slice1Projection?: Slice1Projection | null;
  onEdit?: () => void;
  showEdit?: boolean;
  onRefreshStatus?: () => Promise<void>;
  refreshing?: boolean;
  boundMiniProgram?: boolean;
}) {
  const link = access.copy_link || access.launch_url || '';
  const qrValue = access.qr_payload || link;
  const openRequest = slice1Projection?.open_request;
  const review = resolveAccessReviewState(access, slice1Projection);
  const itemSummary =
    (openRequest?.items || draftItems || []).map((item) => String(item.label || item.item_type || '')).filter(Boolean);
  const showPrimaryQr = Boolean(qrValue) && !review.reviewReady && !boundMiniProgram;
  const showFallbackQr = Boolean(qrValue || link) && !review.reviewReady && Boolean(boundMiniProgram);

  return (
    <div
      style={{
        border: '1px solid #d9d9d9',
        borderRadius: 8,
        padding: 18,
        background: review.reviewReady ? '#f6ffed' : '#fafafa',
        marginBottom: 12,
      }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <Tag color={review.reviewReady ? 'success' : 'processing'}>
          {review.reviewReady
            ? CLAIM_PRIMARY_STATUS.waitingOfficeReview
            : CLAIM_PRIMARY_STATUS.waitingCustomer}
        </Tag>
        <Title level={4} style={{ margin: 0 }}>
          {review.reviewReady
            ? CLAIM_PRIMARY_STATUS.waitingOfficeReview
            : boundMiniProgram
              ? CLAIM_REQUEST_MORE_COPY.sentToMiniProgram
              : CLAIM_PRIMARY_STATUS.waitingCustomer}
        </Title>
        <Text type="secondary">
          {review.reviewReady
            ? CLAIM_REQUEST_MORE_COPY.waitingBrokerBody
            : boundMiniProgram
              ? CLAIM_REQUEST_MORE_COPY.waitingCustomerBodyBound
              : CLAIM_REQUEST_MORE_COPY.waitingCustomerBody}
        </Text>
        {itemSummary.length > 0 && !review.reviewReady ? (
          <Text>{CLAIM_REQUEST_MORE_COPY.requestedLine(itemSummary.join('、'))}</Text>
        ) : null}
        {review.submittedVin ? (
          <div style={{ padding: 12, background: '#fff', border: '1px solid #b7eb8f', borderRadius: 6 }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>
              {CLAIM_REQUEST_MORE_COPY.customerVin}
            </Text>
            <Text code copyable={{ text: review.submittedVin }}>
              {review.submittedVin}
            </Text>
          </div>
        ) : null}
        {showPrimaryQr ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
            <QRCode value={qrValue} size={168} />
          </div>
        ) : null}
        {!qrValue && !review.reviewReady && !boundMiniProgram ? (
          <Alert
            type="warning"
            showIcon
            message={access.message || CLAIM_REQUEST_MORE_COPY.codePreparing}
          />
        ) : null}
        <Space wrap>
          {link && !review.reviewReady && !boundMiniProgram ? (
            <Button
              type="primary"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(link);
                  message.success(CLAIM_REQUEST_MORE_COPY.linkCopied);
                } catch {
                  message.error(CLAIM_REQUEST_MORE_COPY.copyFailed);
                }
              }}
            >
              {CLAIM_REQUEST_MORE_COPY.copyLink}
            </Button>
          ) : null}
        </Space>
        {showFallbackQr ? (
          <Collapse
            ghost
            size="small"
            items={[
              {
                key: 'optional-qr-fallback',
                label: CLAIM_REQUEST_MORE_COPY.optionalQrFallback,
                children: (
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    {qrValue ? (
                      <div style={{ display: 'flex', justifyContent: 'center', padding: '4px 0' }}>
                        <QRCode value={qrValue} size={140} />
                      </div>
                    ) : null}
                    {link ? (
                      <Button
                        size="small"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(link);
                            message.success(CLAIM_REQUEST_MORE_COPY.linkCopied);
                          } catch {
                            message.error(CLAIM_REQUEST_MORE_COPY.copyFailed);
                          }
                        }}
                      >
                        {CLAIM_REQUEST_MORE_COPY.copyLink}
                      </Button>
                    ) : null}
                  </Space>
                ),
              },
            ]}
          />
        ) : null}
        <Collapse
          ghost
          size="small"
          items={[
            {
              key: 'request-details',
              label: CLAIM_REQUEST_MORE_COPY.requestDetails,
              children: (
                <Space direction="vertical" size={8}>
                  <Text type="secondary">
                    {CLAIM_REQUEST_MORE_COPY.progressLine(review.satisfied, review.total)}
                  </Text>
                  {itemSummary.length > 0 ? (
                    <Text>{CLAIM_REQUEST_MORE_COPY.requestedLine(itemSummary.join('、'))}</Text>
                  ) : null}
                  {!review.reviewReady ? (
                    <Paragraph style={{ marginBottom: 0 }}>
                      {boundMiniProgram
                        ? CLAIM_REQUEST_MORE_COPY.instructionBoundDefault
                        : access.instruction_zh || CLAIM_REQUEST_MORE_COPY.instructionDefault}
                    </Paragraph>
                  ) : null}
                  {onRefreshStatus ? (
                    <Button size="small" onClick={() => void onRefreshStatus()} loading={Boolean(refreshing)}>
                      {CLAIM_REQUEST_MORE_COPY.refreshStatus}
                    </Button>
                  ) : null}
                  {showEdit && onEdit ? <Button size="small" onClick={onEdit}>修改</Button> : null}
                </Space>
              ),
            },
          ]}
        />
      </Space>
    </div>
  );
}

export function MissingInformationChecklistPanel({
  caseRecord,
  onCaseChange,
  refreshCase,
}: {
  caseRecord: SavedCase;
  onCaseChange?: (updated: SavedCase) => void;
  refreshCase?: () => Promise<SavedCase | null>;
}) {
  const projection = resolveCaseIntakeProjection(caseRecord);
  const accessCard = resolveCustomerAccessCard(caseRecord);
  const [rows, setRows] = useState<DraftEditRow[]>([]);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [sending, setSending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const commandInFlight = useRef(false);
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const autosaveRef = useRef(new RequestDraftAutosaveController());
  const rowsRef = useRef<DraftEditRow[]>([]);
  const caseRecordRef = useRef(caseRecord);
  const projectionRef = useRef(projection);
  const sendCommandRef = useRef<{ command_id: string; idempotency_key: string } | null>(null);
  const savePromiseRef = useRef<Promise<{ ok: boolean; draftId?: string; aggregateVersion?: number }> | null>(null);
  const lastAcceptedVersionRef = useRef<number | null>(
    typeof projection?.aggregate_version === 'number' ? projection.aggregate_version : null,
  );
  const [statusRefreshing, setStatusRefreshing] = useState(false);
  const [aiDrafting, setAiDrafting] = useState(false);
  const [aiDraftText, setAiDraftText] = useState<string>('');
  const [aiDraftNotice, setAiDraftNotice] = useState<{ type: 'info' | 'warning'; text: string } | null>(
    null,
  );
  const expectedVersion = projection?.aggregate_version ?? 0;
  const requestSent =
    Boolean(accessCard?.access_ready || accessCard?.request_sent)
    || projection?.request_draft?.status === 'sent'
    || Boolean(projection?.open_request_more);

  rowsRef.current = rows;
  caseRecordRef.current = caseRecord;
  projectionRef.current = projection;
  if (typeof projection?.aggregate_version === 'number') {
    const current = lastAcceptedVersionRef.current;
    if (current == null || projection.aggregate_version >= current) {
      lastAcceptedVersionRef.current = projection.aggregate_version;
    }
  }

  const clearAutosaveTimer = () => {
    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
      autosaveTimerRef.current = null;
    }
    autosaveRef.current.clearTimer();
  };

  const syncPhase = (phase: AutosavePhase | SaveStatus) => {
    setSaveStatus(phase as SaveStatus);
  };

  useEffect(() => {
    return () => {
      clearAutosaveTimer();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- unmount cleanup only
  }, []);

  // Stable poll callback — parent refreshCase identity often changes after each
  // setState; do not restart the interval (avoids timer churn / drawer jitter).
  const refreshCaseRef = useRef(refreshCase);
  refreshCaseRef.current = refreshCase;

  // While waiting for customer, gently refresh authoritative detail (no aggressive churn).
  // Parent must preserve prior detail during refetch (no initial-loading flash).
  useEffect(() => {
    if (!requestSent || !refreshCaseRef.current || editing) return;
    const review = resolveAccessReviewState(
      accessCard,
      caseRecord.slice1_projection || caseRecord.p20_slice1_projection,
    );
    if (review.reviewReady) return;
    const timer = setInterval(() => {
      void refreshCaseRef.current?.();
    }, CUSTOMER_STATUS_POLL_MS);
    return () => clearInterval(timer);
  }, [
    requestSent,
    editing,
    accessCard?.simple_status,
    accessCard?.progress?.satisfied_count,
    caseRecord.slice1_projection?.workflow_state,
    caseRecord.p20_slice1_projection?.workflow_state,
  ]);

  // Case change or safe server projection refresh (never overwrite dirty local edits).
  useEffect(() => {
    if (!projection) return;
    const ctrl = autosaveRef.current;
    const serverItems = projection.request_draft?.items || [];
    const localItems = buildDraftItemsFromRows(rowsRef.current);
    const caseChanged = ctrl.getCaseId() !== caseRecord.case_id;

    if (caseChanged) {
      clearAutosaveTimer();
      ctrl.resetForCase(caseRecord.case_id, serverItems);
      setRows(rowsFromProjection(projection));
      syncPhase(ctrl.phase);
      setError(null);
      return;
    }

    if (requestSent) {
      clearAutosaveTimer();
      setRows(rowsFromProjection(projection));
      ctrl.applyServerBaseline(serverItems);
      syncPhase(ctrl.phase);
      return;
    }

    if (!ctrl.shouldApplyPoll(serverItems, localItems)) {
      return;
    }

    setRows(rowsFromProjection(projection));
    ctrl.applyServerBaseline(serverItems);
    syncPhase(ctrl.phase);
  }, [
    caseRecord.case_id,
    projection?.aggregate_version,
    projection?.request_draft?.draft_version,
    projection?.request_draft?.content_hash,
    requestSent,
  ]);

  const selectedSendableCount = useMemo(
    () => rows.filter((r) => r.selected && isMvpSendableItemType(r.item_type)).length,
    [rows],
  );

  const unsupportedInSavedDraft = useMemo(
    () => unsupportedDraftItemLabels(projection?.request_draft?.items),
    [projection?.request_draft?.draft_version, projection?.request_draft?.items],
  );

  // Deterministic missing set — the server owns this; the panel only displays it.
  const deterministicMissingItems = useMemo(
    () =>
      (projection?.missing_information_checklist || []).filter(
        (item) => item.suggested_for_request && isMvpSendableItemType(item.item_type),
      ),
    [projection?.missing_information_checklist],
  );

  if (!projection) return null;

  const mergeProjection = (result: {
    broker_projection?: CaseIntakeProjection;
    customer_access?: CustomerAccessCard | null;
    slice1_projection?: Slice1Projection | null;
    server_timestamp?: string;
  }) => {
    const next = result.broker_projection;
    if (!next) return;
    if (typeof next.aggregate_version === 'number') {
      lastAcceptedVersionRef.current = next.aggregate_version;
      projectionRef.current = { ...next, customer_access: result.customer_access || next.customer_access || accessCard };
    }
    const current = caseRecordRef.current;
    const access = result.customer_access || next.customer_access || accessCard;
    const updated: SavedCase = {
      ...current,
      p20_case_intake_projection: { ...next, customer_access: access || next.customer_access },
      case_intake_projection: { ...next, customer_access: access || next.customer_access },
      missing_information_checklist: next.missing_information_checklist,
      request_draft: next.request_draft,
      admin_lifecycle: next.admin_lifecycle,
      customer_access: access || undefined,
      workbench_test: Boolean(next.is_test || current.workbench_test),
      updated_at: result.server_timestamp || current.updated_at,
    };
    if (result.slice1_projection) {
      updated.slice1_projection = result.slice1_projection;
      updated.p20_slice1_projection = result.slice1_projection;
      if (result.slice1_projection.open_request) {
        updated.slice1_request_summary = result.slice1_projection.open_request;
        updated.p20_slice1_request_summary = result.slice1_projection.open_request;
      }
      updated.slice1_capability_version = 1;
      updated.p20_slice1_capability_version = 1;
    }
    onCaseChange?.(updated);
  };

  const runAutosave = async (allowFollowUp = true): Promise<{ ok: boolean; draftId?: string; aggregateVersion?: number }> => {
    if (savePromiseRef.current) {
      autosaveRef.current.queued = true;
      const prior = await savePromiseRef.current;
      if (!allowFollowUp) return prior;
      if (!autosaveRef.current.isDirty(buildDraftItemsFromRows(rowsRef.current))) {
        return prior;
      }
      return runAutosave(false);
    }

    const exec = async (): Promise<{ ok: boolean; draftId?: string; aggregateVersion?: number }> => {
      const proj = projectionRef.current;
      if (!proj || requestSent) return { ok: false };
      const items = buildDraftItemsFromRows(rowsRef.current);
      const started = autosaveRef.current.beginSave(items);
      if (!started) {
        syncPhase(autosaveRef.current.phase);
        return {
          ok: autosaveRef.current.phase === 'saved',
          draftId: proj.request_draft?.draft_id,
          aggregateVersion:
            lastAcceptedVersionRef.current
            ?? proj.aggregate_version
            ?? undefined,
        };
      }
      setSaveStatus('saving');
      setError(null);
      const ids = newIds('save_draft');
      const expected = resolveSendExpectedVersion({
        lastAcceptedVersion: lastAcceptedVersionRef.current,
        projectionVersion: proj.aggregate_version,
      });
      try {
        const result = await saveCaseRequestDraft(caseRecord.case_id, {
          ...ids,
          expected_case_version: expected,
          items: started.items,
          draft_id: proj.request_draft?.draft_id,
        });
        if (autosaveRef.current.isStale(started.generation)) {
          return { ok: false };
        }
        if (result.outcome === 'conflict' || result.error_code === 'version_conflict') {
          autosaveRef.current.failSave(started.generation);
          setSaveStatus('failed');
          setError(CLAIM_REQUEST_MORE_COPY.caseUpdatedReview);
          await refreshCase?.();
          message.warning(CLAIM_REQUEST_MORE_COPY.caseUpdatedToast);
          return { ok: false };
        }
        if (result.outcome === 'rejected') {
          autosaveRef.current.failSave(started.generation);
          setSaveStatus('failed');
          setError(result.error_code || CLAIM_REQUEST_MORE_COPY.saveFailed);
          return { ok: false };
        }
        const serverItems = result.broker_projection?.request_draft?.items || started.items;
        const { runFollowUp } = autosaveRef.current.acceptSave(started.generation, serverItems);
        mergeProjection(result);
        setSaveStatus('saved');
        const draftId =
          result.broker_projection?.request_draft?.draft_id || proj.request_draft?.draft_id;
        const aggregateVersion =
          typeof result.broker_projection?.aggregate_version === 'number'
            ? result.broker_projection.aggregate_version
            : lastAcceptedVersionRef.current ?? undefined;
        if (runFollowUp && allowFollowUp) {
          // At most one follow-up for newest content after in-flight edits.
          savePromiseRef.current = null;
          const follow = await runAutosave(false);
          return follow.ok ? follow : { ok: true, draftId, aggregateVersion };
        }
        return { ok: true, draftId, aggregateVersion };
      } catch (err) {
        if (autosaveRef.current.isStale(started.generation)) {
          return { ok: false };
        }
        const status = (err as { response?: { status?: number } })?.response?.status;
        autosaveRef.current.failSave(started.generation);
        if (status === 409) {
          setError(CLAIM_REQUEST_MORE_COPY.caseUpdatedReview);
          await refreshCase?.();
          message.warning(CLAIM_REQUEST_MORE_COPY.caseUpdatedToast);
        } else {
          setError('草稿未能保存。请刷新后重试。');
        }
        setSaveStatus('failed');
        return { ok: false };
      }
    };

    const promise = exec();
    savePromiseRef.current = promise;
    try {
      return await promise;
    } finally {
      if (savePromiseRef.current === promise) {
        savePromiseRef.current = null;
      }
    }
  };

  const armAutosaveTimer = () => {
    clearAutosaveTimer();
    autosaveRef.current.timerArmed = true;
    autosaveTimerRef.current = setTimeout(() => {
      autosaveTimerRef.current = null;
      autosaveRef.current.clearTimer();
      void runAutosave();
    }, AUTOSAVE_DEBOUNCE_MS);
  };

  const applyUserRowEdit = (updater: (prev: DraftEditRow[]) => DraftEditRow[]) => {
    if (requestSent) return;
    const next = updater(rowsRef.current);
    rowsRef.current = next;
    setRows(next);
    const items = buildDraftItemsFromRows(next);
    const { armTimer, phase } = autosaveRef.current.onUserEdit(items);
    syncPhase(phase);
    if (armTimer) armAutosaveTimer();
    else clearAutosaveTimer();
  };

  /**
   * Drafting help only: the server decides which items are still missing, the
   * broker still edits and still presses「发出补充请求」.
   */
  const handleAiDraft = async (preferTemplate = false) => {
    if (requestSent || aiDrafting) return;
    setAiDrafting(true);
    setAiDraftNotice(null);
    try {
      const result = await requestMoreAiDraft(caseRecord.case_id, undefined, preferTemplate);
      if (!result.ok) {
        setAiDraftText('');
        setAiDraftNotice({
          type: 'warning',
          text: result.message || CLAIM_REQUEST_MORE_COPY.aiDraftBlockedOpenRequest,
        });
        return;
      }
      if (!result.drafting_available) {
        setAiDraftText('');
        setAiDraftNotice({ type: 'info', text: CLAIM_REQUEST_MORE_COPY.aiDraftNothingMissing });
        return;
      }
      const drafted = result.items || [];
      applyUserRowEdit((prev) =>
        prev.map((row) => {
          const item = drafted.find((i) => i.field_key === row.field_key);
          if (!item) return row;
          return {
            ...row,
            selected: true,
            label: item.label || row.label,
            instructions: item.instructions || row.instructions,
          };
        }),
      );
      setAiDraftText(result.draft_text || '');
      setAiDraftNotice({
        type: result.used_fallback ? 'warning' : 'info',
        text: result.used_fallback
          ? CLAIM_REQUEST_MORE_COPY.aiDraftFallbackApplied
          : CLAIM_REQUEST_MORE_COPY.aiDraftApplied,
      });
    } catch {
      setAiDraftNotice({ type: 'warning', text: CLAIM_REQUEST_MORE_COPY.aiDraftFailed });
    } finally {
      setAiDrafting(false);
    }
  };

  const flushAutosave = async (): Promise<{ ok: boolean; draftId?: string; aggregateVersion?: number }> => {
    clearAutosaveTimer();
    return runAutosave(true);
  };

  const refreshCustomerStatus = async () => {
    if (!refreshCase || statusRefreshing) return;
    setStatusRefreshing(true);
    try {
      await refreshCase();
      message.success(CLAIM_REQUEST_MORE_COPY.statusRefreshed);
    } catch {
      message.error(CLAIM_REQUEST_MORE_COPY.statusRefreshFailed);
    } finally {
      setStatusRefreshing(false);
    }
  };

  const handleSendRequest = async () => {
    if (commandInFlight.current || sending || requestSent) return;
    if (unsupportedInSavedDraft.length > 0) {
      setError(formatUnsupportedSendItems(unsupportedInSavedDraft));
      return;
    }
    if (selectedSendableCount < 1) {
      setError(CLAIM_REQUEST_MORE_COPY.selectAtLeastOneBeforeSend);
      return;
    }
    if (saveStatus === 'failed') {
      setError(CLAIM_REQUEST_MORE_COPY.saveFailedBeforeSend);
      return;
    }
    const needsFlush =
      saveStatus === 'saving'
      || saveStatus === 'unsaved'
      || Boolean(autosaveTimerRef.current)
      || autosaveRef.current.isDirty(buildDraftItemsFromRows(rowsRef.current));
    let latestDraftId = projection.request_draft?.draft_id || caseRecord.request_draft?.draft_id;
    let flushedVersion: number | null = null;
    // Always flush once before Send so CAS uses the authoritative post-save version.
    {
      const saved = await flushAutosave();
      if (!saved.ok && (needsFlush || !latestDraftId)) {
        setError(CLAIM_REQUEST_MORE_COPY.waitingDraftSave);
        return;
      }
      if (saved.ok) {
        latestDraftId = saved.draftId || latestDraftId;
        if (typeof saved.aggregateVersion === 'number') {
          flushedVersion = saved.aggregateVersion;
        }
      }
    }
    if (!latestDraftId) {
      setError(CLAIM_REQUEST_MORE_COPY.draftNotReady);
      return;
    }

    commandInFlight.current = true;
    setSending(true);
    setError(null);
    if (!sendCommandRef.current) {
      sendCommandRef.current = newIds('send_request');
    }
    const ids = sendCommandRef.current;
    const sendExpected = resolveSendExpectedVersion({
      flushedVersion,
      lastAcceptedVersion: lastAcceptedVersionRef.current,
      projectionVersion: projectionRef.current?.aggregate_version ?? expectedVersion,
    });
    try {
      const result = await sendCaseRequest(caseRecord.case_id, {
        ...ids,
        expected_case_version: sendExpected,
        request_draft_id: latestDraftId,
      });
      if (result.outcome === 'conflict' || result.error_code === 'version_conflict') {
        setError(CLAIM_REQUEST_MORE_COPY.caseUpdatedReview);
        sendCommandRef.current = null;
        if (result.broker_projection) mergeProjection(result);
        await refreshCase?.();
        message.warning(CLAIM_REQUEST_MORE_COPY.caseUpdatedToast);
        return;
      }
      if (result.outcome === 'rejected') {
        const unsupported = (result as { unsupported_items?: string[] }).unsupported_items;
        setError(
          brokerSendBlockedMessage(String(result.error_code || 'rejected'), unsupported),
        );
        sendCommandRef.current = null;
        return;
      }
      mergeProjection(result);
      setEditing(false);
      sendCommandRef.current = null;
      message.success(
        result.outcome === 'replayed'
          ? CLAIM_REQUEST_MORE_COPY.alreadySent
          : CLAIM_REQUEST_MORE_COPY.sentSuccess,
      );
    } catch (err) {
      const disposition = classifySendRequestError(err);
      if (disposition.clearCommandIdentity) {
        sendCommandRef.current = null;
      }
      setError(disposition.userMessage);
      if (disposition.kind === 'version_conflict') {
        const conflictResult = err instanceof Slice1RequestMoreError ? err.result : undefined;
        if (conflictResult?.broker_projection) {
          mergeProjection(conflictResult);
        }
        await refreshCase?.();
        message.warning(disposition.toast);
      } else if (disposition.kind === 'timeout') {
        message.warning(disposition.toast);
      } else {
        message.error(disposition.toast);
      }
    } finally {
      setSending(false);
      commandInFlight.current = false;
    }
  };

  // Claim: Request More status card may own primary chrome only when primary is
  // waiting-customer or waiting-office-review — never beside「建议确认资料已齐」.
  const claimPrimaryOwnsAccess =
    !isClaimGuidedCase(caseRecord) || requestMoreOwnsPrimaryStatus(caseRecord);
  const showAccessCard = requestSent && accessCard && !editing && claimPrimaryOwnsAccess;
  const showDraftEditor = !showAccessCard;
  const saveStatusLabel =
    saveStatus === 'saving'
      ? CLAIM_REQUEST_MORE_COPY.saving
      : saveStatus === 'saved'
        ? CLAIM_REQUEST_MORE_COPY.saved
        : saveStatus === 'failed'
          ? CLAIM_REQUEST_MORE_COPY.saveFailed
          : saveStatus === 'unsaved'
            ? CLAIM_REQUEST_MORE_COPY.unsaved
            : '';
  const caseClosedReadOnly = isStructuredRequestMoreTerminal(caseRecord);
  const boundMiniProgram = isBoundMiniProgramCustomer(caseRecord);
  const canSend =
    !caseClosedReadOnly
    && selectedSendableCount > 0
    && unsupportedInSavedDraft.length === 0
    && saveStatus !== 'saving'
    && saveStatus !== 'failed';

  return (
    <div style={{ marginBottom: 16 }}>
      {showAccessCard && accessCard ? (
        <CustomerAccessReadyCard
          access={accessCard}
          draftItems={projection.request_draft?.items || []}
          slice1Projection={caseRecord.slice1_projection || caseRecord.p20_slice1_projection}
          onRefreshStatus={refreshCase ? refreshCustomerStatus : undefined}
          refreshing={statusRefreshing}
          boundMiniProgram={boundMiniProgram}
        />
      ) : null}

      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 8 }} /> : null}

      {caseClosedReadOnly && !showAccessCard ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 8 }}
          message="案件已关闭 / 历史案件不可再发出补充请求。"
        />
      ) : null}

      {showDraftEditor && !caseClosedReadOnly ? (
        <>
          <Title level={4} style={{ marginTop: 0, marginBottom: 4 }}>
            {CLAIM_REQUEST_MORE_COPY.panelTitle}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 8 }}>
            {CLAIM_REQUEST_MORE_COPY.panelSubtitle}
          </Paragraph>
          {(() => {
            const checklist = projection.missing_information_checklist || [];
            // Gap SSOT: only genuinely absent facts (missing/unknown/needs_correction).
            // Supplied_unconfirmed accident facts must not appear under「事故信息仍缺」.
            const mustHaveGaps = checklist.filter((item) => {
              const isMustHave =
                item.business_class === 'must_have' || item.severity === 'critical';
              if (!isMustHave || item.item_type === 'vin') return false;
              if (typeof item.is_gap === 'boolean') return item.is_gap;
              return (
                item.status === 'missing'
                || item.status === 'unknown'
                || item.status === 'needs_correction'
              );
            });
            const requestMoreCandidates = checklist.filter(
              (item) =>
                item.business_class === 'request_more'
                || item.item_type === 'vin'
                || item.item_type === 'policy_or_insurance_card'
                || item.item_type === 'photo_evidence',
            );
            return (
              <Space direction="vertical" size={6} style={{ width: '100%', marginBottom: 12 }}>
                {mustHaveGaps.length > 0 ? (
                  <Alert
                    type="info"
                    showIcon
                    message={CLAIM_REQUEST_MORE_COPY.accidentGapsTitle}
                    description={mustHaveGaps.map((i) => i.label).join(' · ')}
                  />
                ) : (
                  <Alert
                    type="success"
                    showIcon
                    message={CLAIM_REQUEST_MORE_COPY.accidentReadyTitle}
                  />
                )}
                {requestMoreCandidates.length > 0 ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {CLAIM_REQUEST_MORE_COPY.candidatesHint(
                      requestMoreCandidates.map((i) => i.label).join(' · '),
                    )}
                  </Text>
                ) : null}
                {deterministicMissingItems.length > 0 ? (
                  <Text strong style={{ fontSize: 13 }}>
                    {CLAIM_REQUEST_MORE_COPY.aiDraftMissingCount(deterministicMissingItems.length)}
                    {'：'}
                    {deterministicMissingItems.map((i) => i.customer_label || i.label).join(' · ')}
                  </Text>
                ) : null}
              </Space>
            );
          })()}
          {unsupportedInSavedDraft.length > 0 ? (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 8 }}
              message={formatUnsupportedSendItems(unsupportedInSavedDraft)}
              description={CLAIM_REQUEST_MORE_COPY.vinOnlyHint}
            />
          ) : null}
          <Space wrap style={{ marginBottom: 10 }}>
            <Button
              onClick={() => void handleAiDraft(false)}
              loading={aiDrafting}
              disabled={aiDrafting || deterministicMissingItems.length === 0}
            >
              {aiDraftText
                ? CLAIM_REQUEST_MORE_COPY.aiDraftRegenerate
                : CLAIM_REQUEST_MORE_COPY.aiDraftButton}
            </Button>
            <Button
              type="link"
              size="small"
              onClick={() => void handleAiDraft(true)}
              disabled={aiDrafting || deterministicMissingItems.length === 0}
            >
              {CLAIM_REQUEST_MORE_COPY.aiDraftUseTemplate}
            </Button>
          </Space>
          {aiDraftNotice ? (
            <Alert
              type={aiDraftNotice.type}
              showIcon
              style={{ marginBottom: 8 }}
              message={aiDraftNotice.text}
            />
          ) : null}
          {aiDraftText ? (
            <Alert
              type="info"
              style={{ marginBottom: 10 }}
              message={CLAIM_REQUEST_MORE_COPY.aiDraftPreviewTitle}
              description={
                <>
                  <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 4 }}>
                    {aiDraftText}
                  </Paragraph>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {CLAIM_REQUEST_MORE_COPY.aiDraftReviewHint}
                  </Text>
                </>
              }
            />
          ) : null}
          <Space direction="vertical" style={{ width: '100%' }} size={10}>
            {rows.filter((row) => isMvpSendableItemType(row.item_type)).map((row) => {
              return (
              <div
                key={row.field_key}
                style={{
                  border: '1px solid #f0f0f0',
                  borderRadius: 8,
                  padding: 12,
                  background: row.selected ? '#fafafa' : '#fff',
                }}
              >
                <Space wrap style={{ marginBottom: 6 }}>
                  <Checkbox
                    checked={row.selected}
                    disabled={row.status === 'confirmed' && row.request_mode === 'none'}
                    onChange={(e) =>
                      applyUserRowEdit((prev) =>
                        prev.map((r) =>
                          r.field_key === row.field_key ? { ...r, selected: e.target.checked } : r,
                        ),
                      )
                    }
                  >
                    {row.label}
                  </Checkbox>
                </Space>
                <Collapse
                  ghost
                  size="small"
                  items={[
                    {
                      key: `message-${row.field_key}`,
                      label: CLAIM_REQUEST_MORE_COPY.editMessage,
                      children: (
                        <>
                          <Input
                            size="small"
                            placeholder={CLAIM_REQUEST_MORE_COPY.customerLabelPlaceholder}
                            value={row.label}
                            onChange={(e) =>
                              applyUserRowEdit((prev) =>
                                prev.map((r) => (r.field_key === row.field_key ? { ...r, label: e.target.value } : r)),
                              )
                            }
                            style={{ marginBottom: 6 }}
                          />
                          <TextArea
                            rows={2}
                            placeholder={CLAIM_REQUEST_MORE_COPY.customerInstructionPlaceholder}
                            value={row.instructions}
                            onChange={(e) =>
                              applyUserRowEdit((prev) =>
                                prev.map((r) =>
                                  r.field_key === row.field_key ? { ...r, instructions: e.target.value } : r,
                                ),
                              )
                            }
                          />
                        </>
                      ),
                    },
                  ]}
                />
              </div>
            );
            })}
          </Space>
          <Space style={{ marginTop: 12 }} direction="vertical" size={8}>
            {saveStatus === 'failed' && saveStatusLabel ? (
              <Text type={saveStatus === 'failed' ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
                {saveStatusLabel}
                {saveStatus === 'failed' ? (
                  <>
                    {' '}
                    <Button type="link" size="small" onClick={() => void flushAutosave()} style={{ padding: 0 }}>
                      {CLAIM_REQUEST_MORE_COPY.retry}
                    </Button>
                  </>
                ) : null}
              </Text>
            ) : null}
            <Space wrap>
              <Button
                type="primary"
                onClick={() => void handleSendRequest()}
                loading={sending}
                disabled={sending || !canSend}
              >
                {CLAIM_REQUEST_MORE_COPY.sendButton}
              </Button>
              {saveStatus === 'failed' ? (
                <Button onClick={() => void flushAutosave()}>
                  {CLAIM_REQUEST_MORE_COPY.saveDraftNow}
                </Button>
              ) : null}
            </Space>
          </Space>
        </>
      ) : null}
    </div>
  );
}
