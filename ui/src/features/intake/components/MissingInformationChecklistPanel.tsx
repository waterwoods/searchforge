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
import { saveCaseRequestDraft, sendCaseRequest, updateCaseFactStatus } from '@/api/inboxTriage';

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

function rowsFromProjection(projection: CaseIntakeProjection): DraftEditRow[] {
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
    const defaultSelected =
      selectedKeys.size > 0 ? selectedKeys.has(key) : Boolean(item.suggested_for_request);
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
}: {
  access: CustomerAccessCard;
  draftItems: CaseIntakeRequestDraftItem[];
  slice1Projection?: Slice1Projection | null;
  onEdit?: () => void;
  showEdit?: boolean;
}) {
  const link = access.copy_link || access.launch_url || '';
  const qrValue = access.qr_payload || link;
  const openRequest = slice1Projection?.open_request;
  const total =
    access.progress?.total_count
    ?? openRequest?.progress?.total
    ?? draftItems.length
    ?? 0;
  const satisfied =
    access.progress?.satisfied_count
    ?? openRequest?.progress?.satisfied
    ?? 0;
  const itemSummary =
    (openRequest?.items || draftItems || []).map((item) => String(item.label || item.item_type || '')).filter(Boolean);

  return (
    <div
      style={{
        border: '1px solid #d9d9d9',
        padding: 16,
        background: '#fafafa',
        marginBottom: 12,
      }}
    >
      <Space direction="vertical" size={10} style={{ width: '100%' }}>
        <Title level={5} style={{ margin: 0 }}>
          Sent to customer
        </Title>
        <Tag color="processing">{access.simple_status || 'Waiting for customer'}</Tag>
        <Text type="secondary">
          Progress: {satisfied} / {total}
        </Text>
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
        {qrValue ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
            <QRCode value={qrValue} size={168} />
          </div>
        ) : (
          <Alert
            type="warning"
            showIcon
            message={access.message || 'Request sent. Code is still preparing.'}
          />
        )}
        <Space wrap>
          {link ? (
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
          ) : (
            <Button disabled>Copy Link</Button>
          )}
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
              label: 'Advanced / Developer',
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
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [naReason, setNaReason] = useState<Record<string, string>>({});
  const inFlight = useRef(false);
  const sendCommandRef = useRef<{ command_id: string; idempotency_key: string } | null>(null);
  const expectedVersion = projection?.aggregate_version ?? 0;
  const requestSent =
    Boolean(accessCard?.access_ready || accessCard?.request_sent)
    || projection?.request_draft?.status === 'sent'
    || Boolean(projection?.open_request_more);

  useEffect(() => {
    if (projection) setRows(rowsFromProjection(projection));
  }, [caseRecord.case_id, projection?.aggregate_version, projection?.request_draft?.draft_version]);

  const selectedCount = useMemo(() => rows.filter((r) => r.selected).length, [rows]);

  if (!projection) return null;

  const mergeProjection = (result: {
    broker_projection?: CaseIntakeProjection;
    customer_access?: CustomerAccessCard | null;
    slice1_projection?: Slice1Projection | null;
    server_timestamp?: string;
  }) => {
    const next = result.broker_projection;
    if (!next) return;
    const access = result.customer_access || next.customer_access || accessCard;
    const updated: SavedCase = {
      ...caseRecord,
      p20_case_intake_projection: { ...next, customer_access: access || next.customer_access },
      case_intake_projection: { ...next, customer_access: access || next.customer_access },
      missing_information_checklist: next.missing_information_checklist,
      request_draft: next.request_draft,
      admin_lifecycle: next.admin_lifecycle,
      customer_access: access || undefined,
      workbench_test: Boolean(next.is_test || caseRecord.workbench_test),
      updated_at: result.server_timestamp || caseRecord.updated_at,
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

  const handleSaveDraft = async () => {
    if (inFlight.current || saving || requestSent) return;
    inFlight.current = true;
    setSaving(true);
    setError(null);
    const ids = newIds('save_draft');
    const items: CaseIntakeRequestDraftItem[] = rows
      .filter((r) => r.selected)
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
    try {
      const result = await saveCaseRequestDraft(caseRecord.case_id, {
        ...ids,
        expected_case_version: expectedVersion,
        items,
        draft_id: projection.request_draft?.draft_id,
      });
      if (result.outcome === 'conflict' || result.error_code === 'version_conflict') {
        setError('Case was updated elsewhere. Refreshing…');
        await refreshCase?.();
        message.warning('Version conflict — case refreshed. Review and save again.');
        return;
      }
      if (result.outcome === 'rejected') {
        setError(result.error_code || 'Draft save rejected');
        return;
      }
      mergeProjection(result);
      setEditing(false);
      message.success(
        result.outcome === 'replayed'
          ? 'Request draft already saved; refreshed.'
          : 'Request draft saved.',
      );
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setError('Version conflict. Refreshing case…');
        await refreshCase?.();
        message.warning('Stale version — refreshed. Save again if needed.');
      } else {
        setError('Could not save request draft. Retry after refresh.');
        message.error('Request draft save failed');
      }
    } finally {
      setSaving(false);
      inFlight.current = false;
    }
  };

  const handleSendRequest = async () => {
    if (inFlight.current || sending || !projection.request_draft?.draft_id) return;
    inFlight.current = true;
    setSending(true);
    setError(null);
    if (!sendCommandRef.current) {
      sendCommandRef.current = newIds('send_request');
    }
    const ids = sendCommandRef.current;
    try {
      const result = await sendCaseRequest(caseRecord.case_id, {
        ...ids,
        expected_case_version: expectedVersion,
        request_draft_id: projection.request_draft.draft_id,
      });
      if (result.outcome === 'conflict' || result.error_code === 'version_conflict') {
        setError('Case was updated elsewhere. Refreshing…');
        sendCommandRef.current = null;
        await refreshCase?.();
        message.warning('Version conflict — case refreshed. Review and send again.');
        return;
      }
      if (result.outcome === 'rejected') {
        setError(result.error_code || 'Send Request rejected');
        sendCommandRef.current = null;
        return;
      }
      mergeProjection(result);
      setEditing(false);
      message.success(
        result.outcome === 'replayed'
          ? 'Request already sent; showing customer access.'
          : 'Request sent to customer.',
      );
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        sendCommandRef.current = null;
        setError('Version conflict. Refreshing case…');
        await refreshCase?.();
        message.warning('Stale version — refreshed.');
      } else {
        // Keep same command identity for retry after transport loss.
        setError('Could not send request. Retry uses the same command.');
        message.error('Send Request failed — tap again to retry safely');
      }
    } finally {
      setSending(false);
      inFlight.current = false;
    }
  };

  const handleMarkNotApplicable = async (fieldKey: string) => {
    if (inFlight.current || requestSent) return;
    const reason = (naReason[fieldKey] || '').trim();
    if (!reason) {
      message.warning('Enter a reason before marking not applicable.');
      return;
    }
    inFlight.current = true;
    setSaving(true);
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
        message.warning('Version conflict — refreshed.');
        return;
      }
      mergeProjection(result);
      message.success('Marked not applicable (audited).');
    } catch {
      setError('Could not update fact status.');
      message.error('Fact status update failed');
    } finally {
      setSaving(false);
      inFlight.current = false;
    }
  };

  const handleNeedsCorrection = async (fieldKey: string) => {
    if (inFlight.current || requestSent) return;
    inFlight.current = true;
    setSaving(true);
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
        message.warning('Version conflict — refreshed.');
        return;
      }
      mergeProjection(result);
      message.success('Marked needs correction; prior value preserved.');
    } catch {
      setError('Could not mark needs correction.');
    } finally {
      setSaving(false);
      inFlight.current = false;
    }
  };

  const showAccessCard = requestSent && accessCard && !editing;
  const showDraftEditor = !showAccessCard;

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
        />
      ) : null}

      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 8 }} /> : null}

      {showDraftEditor ? (
        <>
          <Paragraph type="secondary" style={{ marginBottom: 8, fontSize: 12 }}>
            Select what the customer should provide. Save the draft, then send the request.
          </Paragraph>
          <Space direction="vertical" style={{ width: '100%' }} size={10}>
            {rows.map((row) => (
              <div
                key={row.field_key}
                style={{
                  border: '1px solid #f0f0f0',
                  padding: 10,
                  background: row.selected ? '#fafafa' : '#fff',
                }}
              >
                <Space wrap style={{ marginBottom: 6 }}>
                  <Checkbox
                    checked={row.selected}
                    disabled={row.status === 'confirmed' && row.request_mode === 'none'}
                    onChange={(e) =>
                      setRows((prev) =>
                        prev.map((r) =>
                          r.field_key === row.field_key ? { ...r, selected: e.target.checked } : r,
                        ),
                      )
                    }
                  >
                    {row.label}
                  </Checkbox>
                  <Tag color={statusColorFixed(row.status)}>{row.status}</Tag>
                </Space>
                {row.value ? (
                  <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>
                    Current value: {String(row.value)}
                  </Text>
                ) : null}
                <Input
                  size="small"
                  placeholder="Customer-facing label"
                  value={row.label}
                  onChange={(e) =>
                    setRows((prev) =>
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
                    setRows((prev) =>
                      prev.map((r) =>
                        r.field_key === row.field_key ? { ...r, instructions: e.target.value } : r,
                      ),
                    )
                  }
                />
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
                      <Button size="small" onClick={() => void handleMarkNotApplicable(row.field_key)} disabled={saving}>
                        Mark N/A
                      </Button>
                    </>
                  ) : null}
                  {row.value && row.status !== 'needs_correction' ? (
                    <Button size="small" onClick={() => void handleNeedsCorrection(row.field_key)} disabled={saving}>
                      Needs correction
                    </Button>
                  ) : null}
                </Space>
              </div>
            ))}
          </Space>
          <Space style={{ marginTop: 12 }} wrap>
            {projection.request_draft && !editing ? (
              <>
                <Button
                  type="primary"
                  onClick={() => void handleSendRequest()}
                  loading={sending}
                  disabled={sending || !projection.request_draft.items?.length}
                >
                  Send Request
                </Button>
                <Button onClick={() => setEditing(true)} disabled={sending}>
                  Edit
                </Button>
              </>
            ) : (
              <Button type="primary" onClick={() => void handleSaveDraft()} loading={saving} disabled={saving}>
                Save request draft ({selectedCount})
              </Button>
            )}
          </Space>
        </>
      ) : null}
    </div>
  );
}
