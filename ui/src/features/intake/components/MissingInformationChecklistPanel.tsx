/**
 * P20 Capability 2 — Missing Information Checklist + Request Draft panel.
 * Broker selects/edits items and saves an explicit request draft command.
 * Does not send Request More or create customer tasks.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Checkbox,
  Input,
  Space,
  Tag,
  Typography,
  message,
} from 'antd';
import type {
  CaseIntakeProjection,
  CaseIntakeRequestDraftItem,
  SavedCase,
} from '@/api/inboxTriage';
import { saveCaseRequestDraft, updateCaseFactStatus } from '@/api/inboxTriage';

const { Text, Paragraph } = Typography;
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
      customer_next_action: null,
    };
  }
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
  const [rows, setRows] = useState<DraftEditRow[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [naReason, setNaReason] = useState<Record<string, string>>({});
  const inFlight = useRef(false);
  const expectedVersion = projection?.aggregate_version ?? 0;

  useEffect(() => {
    if (projection) setRows(rowsFromProjection(projection));
  }, [caseRecord.case_id, projection?.aggregate_version, projection?.request_draft?.draft_version]);

  const selectedCount = useMemo(() => rows.filter((r) => r.selected).length, [rows]);

  if (!projection) return null;

  const mergeProjection = (result: { broker_projection?: CaseIntakeProjection; server_timestamp?: string }) => {
    const next = result.broker_projection;
    if (!next) return;
    const updated: SavedCase = {
      ...caseRecord,
      p20_case_intake_projection: next,
      case_intake_projection: next,
      missing_information_checklist: next.missing_information_checklist,
      request_draft: next.request_draft,
      admin_lifecycle: next.admin_lifecycle,
      workbench_test: Boolean(next.is_test || caseRecord.workbench_test),
      updated_at: result.server_timestamp || caseRecord.updated_at,
    };
    onCaseChange?.(updated);
  };

  const handleSaveDraft = async () => {
    if (inFlight.current || saving) return;
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
      message.success(
        result.outcome === 'replayed'
          ? 'Request draft already saved; refreshed.'
          : 'Request draft saved. Request More is not sent yet.',
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

  const handleMarkNotApplicable = async (fieldKey: string) => {
    if (inFlight.current) return;
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
    if (inFlight.current) return;
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

  return (
    <div style={{ marginBottom: 16 }}>
      <Space style={{ marginBottom: 8 }} wrap>
        <Text strong>Missing Information Checklist</Text>
        {projection.is_test || caseRecord.workbench_test ? <Tag color="orange">TEST / QA</Tag> : null}
        <Tag>{projection.admin_lifecycle || 'draft'}</Tag>
        <Text type="secondary">v{projection.aggregate_version}</Text>
      </Space>
      <Paragraph type="secondary" style={{ marginBottom: 8, fontSize: 12 }}>
        Authoritative facts and detected gaps are shown below. Your selection becomes a request draft only —
        it does not send Request More or create a customer task.
      </Paragraph>
      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 8 }} /> : null}
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
              {row.is_authoritative_fact ? <Tag>authoritative fact</Tag> : <Tag>detected gap</Tag>}
            </Space>
            {row.value ? (
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>
                Current value: {String(row.value)}
              </Text>
            ) : null}
            {row.previous_value ? (
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>
                Previous value preserved: {String(row.previous_value)}
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
              placeholder="Customer-facing instructions (optional)"
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
                  Request correction
                </Button>
              ) : null}
            </Space>
          </div>
        ))}
      </Space>
      <Space style={{ marginTop: 12 }} wrap>
        <Button type="primary" onClick={() => void handleSaveDraft()} loading={saving} disabled={saving}>
          Save request draft ({selectedCount})
        </Button>
        {projection.request_draft ? (
          <Text type="secondary">
            Saved draft {projection.request_draft.draft_id} · v{projection.request_draft.draft_version}
          </Text>
        ) : (
          <Text type="secondary">No draft saved yet</Text>
        )}
      </Space>
      <Alert
        style={{ marginTop: 10 }}
        type="info"
        showIcon
        message="Customer next action: none. Send Request More is the next capability."
      />
    </div>
  );
}
