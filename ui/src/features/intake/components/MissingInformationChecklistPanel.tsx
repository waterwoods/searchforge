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
  saveCaseRequestDraft,
  sendCaseRequest,
  updateCaseFactStatus,
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
import { resolveSlice1CustomerResponse } from '@/features/intake/components/StructuredRequestMorePanel';

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

function statusColorFixed(status: string): string {
  const map: Record<string, string> = {
    missing: 'magenta',
    confirmed: 'green',
    supplied_unconfirmed: 'blue',
    needs_correction: 'orange',
    not_applicable: 'default',
    unknown: 'gold',
  };
  return map[status] || 'default';
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
        userMessage: 'Case was updated. Review the refreshed draft, then send once.',
        toast: 'Case updated — refreshed. Review and send again.',
      };
    }
    if (err.kind === 'timeout') {
      return {
        kind: 'timeout',
        clearCommandIdentity: false,
        userMessage: 'Network outcome uncertain. Tap Send once more to safely replay the same request.',
        toast: 'Connection uncertain — tap Send once more to retry safely.',
      };
    }
    if (err.kind === 'validation' || err.kind === 'feature_disabled' || err.kind === 'authorization') {
      return {
        kind: 'rejected',
        clearCommandIdentity: true,
        userMessage: err.message || 'Send Request was rejected. Refresh and review before retrying.',
        toast: err.message || 'Send Request rejected',
      };
    }
    return {
      kind: 'other',
      clearCommandIdentity: false,
      userMessage: err.message || 'Could not send request. Tap again to retry with the same command.',
      toast: err.message || 'Send Request failed — tap again to retry safely',
    };
  }
  const status = (err as { response?: { status?: number }; status?: number })?.response?.status
    ?? (err as { status?: number })?.status;
  if (status === 409) {
    return {
      kind: 'version_conflict',
      clearCommandIdentity: true,
      userMessage: 'Case was updated. Review the refreshed draft, then send once.',
      toast: 'Case updated — refreshed. Review and send again.',
    };
  }
  return {
    kind: 'other',
    clearCommandIdentity: false,
    userMessage: 'Could not send request. Tap again to retry with the same command.',
    toast: 'Send Request failed — tap again to retry safely',
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
  const reviewReady =
    slice1Projection?.workflow_state === 'broker_review_ready'
    || slice1Projection?.broker_next_action?.action_type === 'review_customer_response'
    || String(access?.simple_status || '').toLowerCase().includes('ready for review')
    || (total > 0 && satisfied >= total);

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
    simpleStatus: reviewReady
      ? (access?.simple_status && String(access.simple_status).toLowerCase().includes('ready')
        ? String(access.simple_status)
        : 'Ready for Review')
      : (access?.simple_status || 'Waiting for customer'),
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
    const defaultSelected =
      sendable && (selectedKeys.size > 0 ? selectedKeys.has(key) : Boolean(item.suggested_for_request));
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
}: {
  access: CustomerAccessCard;
  draftItems: CaseIntakeRequestDraftItem[];
  slice1Projection?: Slice1Projection | null;
  onEdit?: () => void;
  showEdit?: boolean;
  onRefreshStatus?: () => Promise<void>;
  refreshing?: boolean;
}) {
  const link = access.copy_link || access.launch_url || '';
  const qrValue = access.qr_payload || link;
  const openRequest = slice1Projection?.open_request;
  const review = resolveAccessReviewState(access, slice1Projection);
  const itemSummary =
    (openRequest?.items || draftItems || []).map((item) => String(item.label || item.item_type || '')).filter(Boolean);

  return (
    <div
      style={{
        border: '1px solid #d9d9d9',
        padding: 16,
        background: review.reviewReady ? '#f6ffed' : '#fafafa',
        marginBottom: 12,
      }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <Title level={5} style={{ margin: 0 }}>
          Sent to customer
        </Title>
        <Tag color={review.reviewReady ? 'success' : 'processing'}>{review.simpleStatus}</Tag>
        <Text type="secondary">
          Progress: {review.satisfied} / {review.total}
        </Text>
        {review.submittedVin ? (
          <div style={{ padding: 8, background: '#fff', border: '1px solid #b7eb8f' }}>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>
              Customer submitted VIN
            </Text>
            <Text code copyable={{ text: review.submittedVin }}>
              {review.submittedVin}
            </Text>
          </div>
        ) : null}
        {itemSummary.length > 0 ? (
          <div>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>
              Requested
            </Text>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {itemSummary.map((label) => (
                <li key={label}>
                  <Text>{label}</Text>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <Paragraph style={{ marginBottom: 0 }}>
          {access.instruction_zh || '让客户用微信扫码并补充资料。'}
        </Paragraph>
        {qrValue && !review.reviewReady ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
            <QRCode value={qrValue} size={168} />
          </div>
        ) : null}
        {!qrValue && !review.reviewReady ? (
          <Alert
            type="warning"
            showIcon
            message={access.message || 'Request sent. Code is still preparing.'}
          />
        ) : null}
        <Space wrap>
          {onRefreshStatus ? (
            <Button onClick={() => void onRefreshStatus()} loading={Boolean(refreshing)}>
              Refresh status
            </Button>
          ) : null}
          {link && !review.reviewReady ? (
            <Button
              type="primary"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(link);
                  message.success('Link copied');
                } catch {
                  message.error('Could not copy link');
                }
              }}
            >
              Copy Link
            </Button>
          ) : null}
          {showEdit && onEdit ? (
            <Button onClick={onEdit}>Edit</Button>
          ) : null}
        </Space>
        <Collapse
          ghost
          size="small"
          items={[
            {
              key: 'advanced',
              label: 'Details',
              children: (
                <Space direction="vertical" size={4}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Channel: {access.channel || 'https_deep_link'}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Expires: {access.expires_at || '—'}
                  </Text>
                  {access.production_qr_blocker ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Production QR note: {access.production_qr_blocker}
                    </Text>
                  ) : null}
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
  const [naReason, setNaReason] = useState<Record<string, string>>({});
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

  // While waiting for customer, gently refresh authoritative detail (no aggressive churn).
  useEffect(() => {
    if (!requestSent || !refreshCase || editing) return;
    const review = resolveAccessReviewState(
      accessCard,
      caseRecord.slice1_projection || caseRecord.p20_slice1_projection,
    );
    if (review.reviewReady) return;
    const timer = setInterval(() => {
      void refreshCase();
    }, CUSTOMER_STATUS_POLL_MS);
    return () => clearInterval(timer);
  }, [
    requestSent,
    editing,
    refreshCase,
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
          setError('Case was updated elsewhere. Refresh to recover, then retry save.');
          await refreshCase?.();
          message.warning('Case updated — refreshed.');
          return { ok: false };
        }
        if (result.outcome === 'rejected') {
          autosaveRef.current.failSave(started.generation);
          setSaveStatus('failed');
          setError(result.error_code || 'Draft save rejected');
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
          setError('Case updated. Refresh, review, then retry save.');
          await refreshCase?.();
          message.warning('Stale version — refreshed.');
        } else {
          setError('Could not save request draft. Retry after refresh.');
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

  const flushAutosave = async (): Promise<{ ok: boolean; draftId?: string; aggregateVersion?: number }> => {
    clearAutosaveTimer();
    return runAutosave(true);
  };

  const refreshCustomerStatus = async () => {
    if (!refreshCase || statusRefreshing) return;
    setStatusRefreshing(true);
    try {
      await refreshCase();
      message.success('Customer status refreshed.');
    } catch {
      message.error('Could not refresh customer status.');
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
      setError('Select VIN before sending to the customer.');
      return;
    }
    if (saveStatus === 'failed') {
      setError('Save failed — retry save before sending.');
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
        setError('Waiting for draft save. Select VIN and try again.');
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
      setError('Draft not ready yet. Wait for Saved status.');
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
        setError('Case was updated. Review the refreshed draft, then send once.');
        sendCommandRef.current = null;
        if (result.broker_projection) mergeProjection(result);
        await refreshCase?.();
        message.warning('Case updated — refreshed. Review and send again.');
        return;
      }
      if (result.outcome === 'rejected') {
        const unsupported = (result as { unsupported_items?: string[] }).unsupported_items;
        setError(
          brokerSendBlockedMessage(String(result.error_code || 'Send Request rejected'), unsupported),
        );
        sendCommandRef.current = null;
        return;
      }
      mergeProjection(result);
      setEditing(false);
      sendCommandRef.current = null;
      message.success(
        result.outcome === 'replayed'
          ? 'Request already sent; showing customer access.'
          : 'Request sent to customer.',
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

  const handleMarkNotApplicable = async (fieldKey: string) => {
    if (commandInFlight.current || requestSent) return;
    const reason = (naReason[fieldKey] || '').trim();
    if (!reason) {
      message.warning('Enter a reason before marking not applicable.');
      return;
    }
    commandInFlight.current = true;
    setSaveStatus('saving');
    setError(null);
    try {
      const ids = newIds('fact_na');
      const result = await updateCaseFactStatus(caseRecord.case_id, {
        ...ids,
        expected_case_version: expectedVersion,
        field_key: fieldKey,
        status: 'not_applicable',
        reason,
      });
      if (result.outcome === 'conflict') {
        await refreshCase?.();
        message.warning('Case updated — refreshed.');
        return;
      }
      mergeProjection(result);
      message.success('Marked not applicable (audited).');
    } catch {
      setError('Could not update fact status.');
      message.error('Fact status update failed');
    } finally {
      setSaveStatus(autosaveRef.current.phase === 'saved' ? 'saved' : 'idle');
      commandInFlight.current = false;
    }
  };

  const handleNeedsCorrection = async (fieldKey: string) => {
    if (commandInFlight.current || requestSent) return;
    commandInFlight.current = true;
    setSaveStatus('saving');
    setError(null);
    try {
      const ids = newIds('fact_corr');
      const result = await updateCaseFactStatus(caseRecord.case_id, {
        ...ids,
        expected_case_version: expectedVersion,
        field_key: fieldKey,
        status: 'needs_correction',
        reason: 'Broker requested customer confirmation/correction',
      });
      if (result.outcome === 'conflict') {
        await refreshCase?.();
        message.warning('Case updated — refreshed.');
        return;
      }
      mergeProjection(result);
      message.success('Marked needs correction; prior value preserved.');
    } catch {
      setError('Could not mark needs correction.');
    } finally {
      setSaveStatus(autosaveRef.current.phase === 'saved' ? 'saved' : 'idle');
      commandInFlight.current = false;
    }
  };

  const showAccessCard = requestSent && accessCard && !editing;
  const showDraftEditor = !showAccessCard;
  const saveStatusLabel =
    saveStatus === 'saving'
      ? 'Saving…'
      : saveStatus === 'saved'
        ? 'Saved'
        : saveStatus === 'failed'
          ? 'Save failed — Retry'
          : saveStatus === 'unsaved'
            ? 'Unsaved changes'
            : '';
  const canSend =
    selectedSendableCount > 0
    && unsupportedInSavedDraft.length === 0
    && saveStatus !== 'saving'
    && saveStatus !== 'failed';

  return (
    <div style={{ marginBottom: 16 }}>
      <Space style={{ marginBottom: 8 }} wrap>
        <Text strong>Request draft</Text>
        {projection.is_test || caseRecord.workbench_test ? <Tag color="orange">TEST / QA</Tag> : null}
        {requestSent ? <Tag color="blue">Sent</Tag> : <Tag>{projection.admin_lifecycle || 'draft'}</Tag>}
      </Space>

      {showAccessCard && accessCard ? (
        <CustomerAccessReadyCard
          access={accessCard}
          draftItems={projection.request_draft?.items || []}
          slice1Projection={caseRecord.slice1_projection || caseRecord.p20_slice1_projection}
          onRefreshStatus={refreshCase ? refreshCustomerStatus : undefined}
          refreshing={statusRefreshing}
        />
      ) : null}

      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 8 }} /> : null}

      {showDraftEditor ? (
        <>
          <Paragraph type="secondary" style={{ marginBottom: 8, fontSize: 12 }}>
            Select VIN to request from the customer. Other fields are shown for context — customer
            submit support is coming later.
          </Paragraph>
          {unsupportedInSavedDraft.length > 0 ? (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 8 }}
              message={formatUnsupportedSendItems(unsupportedInSavedDraft)}
              description="Update your selection to VIN only, wait for Saved, then send again."
            />
          ) : null}
          <Space direction="vertical" style={{ width: '100%' }} size={10}>
            {rows.map((row) => {
              const sendable = isMvpSendableItemType(row.item_type);
              return (
              <div
                key={row.field_key}
                style={{
                  border: '1px solid #f0f0f0',
                  padding: 10,
                  background: row.selected ? '#fafafa' : '#fff',
                  opacity: sendable ? 1 : 0.85,
                }}
              >
                <Space wrap style={{ marginBottom: 6 }}>
                  {sendable ? (
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
                  ) : (
                    <Text>
                      {row.label}{' '}
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        (Coming later)
                      </Text>
                    </Text>
                  )}
                  <Tag color={statusColorFixed(row.status)}>{row.status}</Tag>
                </Space>
                {row.value ? (
                  <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>
                    Current value: {String(row.value)}
                  </Text>
                ) : null}
                {sendable ? (
                  <>
                    <Input
                      size="small"
                      placeholder="Customer-facing label"
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
                      placeholder="Customer instruction (optional)"
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
                ) : (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Not sendable in the current MVP — VIN only.
                  </Text>
                )}
                <Space wrap style={{ marginTop: 8 }}>
                  {row.status !== 'not_applicable' && row.status !== 'confirmed' ? (
                    <>
                      <Input
                        size="small"
                        placeholder="N/A reason"
                        value={naReason[row.field_key] || ''}
                        onChange={(e) =>
                          setNaReason((prev) => ({ ...prev, [row.field_key]: e.target.value }))
                        }
                        style={{ width: 180 }}
                      />
                      <Button
                        size="small"
                        onClick={() => void handleMarkNotApplicable(row.field_key)}
                        disabled={saveStatus === 'saving'}
                      >
                        Mark N/A
                      </Button>
                    </>
                  ) : null}
                  {row.value && row.status !== 'needs_correction' ? (
                    <Button
                      size="small"
                      onClick={() => void handleNeedsCorrection(row.field_key)}
                      disabled={saveStatus === 'saving'}
                    >
                      Needs correction
                    </Button>
                  ) : null}
                </Space>
              </div>
            );
            })}
          </Space>
          <Space style={{ marginTop: 12 }} direction="vertical" size={8}>
            {saveStatusLabel ? (
              <Text type={saveStatus === 'failed' ? 'danger' : 'secondary'} style={{ fontSize: 12 }}>
                {saveStatusLabel}
                {saveStatus === 'failed' ? (
                  <>
                    {' '}
                    <Button type="link" size="small" onClick={() => void flushAutosave()} style={{ padding: 0 }}>
                      Retry
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
                Send Request
              </Button>
              {saveStatus === 'failed' ? (
                <Button onClick={() => void flushAutosave()}>
                  Save draft now
                </Button>
              ) : null}
            </Space>
          </Space>
        </>
      ) : null}
    </div>
  );
}
