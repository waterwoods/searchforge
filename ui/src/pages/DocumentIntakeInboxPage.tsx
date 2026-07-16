/**
 * P16 Document Intake — broker office review queue for wizard-submitted cases.
 * Chen Kui Insurance Office / CKS Insurance Agency
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Drawer,
  Modal,
  Skeleton,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  CopyOutlined,
  DeleteOutlined,
  InboxOutlined,
  PaperClipOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import {
  confirmCaseByBroker,
  deleteTestCase,
  getSavedCase,
  listRecentCasesPage,
  markClaimBrokerDone,
  patchCaseWorkbench,
  type SavedCase,
} from '@/api/inboxTriage';
import { humanizeStructuredField, isAddCarReadyForBroker, resolveCustomerDisplayName } from '@/features/intake/utils/intakePure';
import { CaseAttachmentsPanel } from '@/features/intake/components/CaseAttachmentsPanel';
import { ClaimCaseBriefPanel } from '@/features/intake/components/ClaimCaseBriefPanel';
import { ClaimEvidenceChecklist } from '@/features/intake/components/ClaimEvidenceChecklist';
import { StructuredRequestMorePanel } from '@/features/intake/components/StructuredRequestMorePanel';
import { MissingInformationChecklistPanel } from '@/features/intake/components/MissingInformationChecklistPanel';
import { NewClaimEntryButton } from '@/features/intake/components/NewClaimEntryButton';
import { countCaseAttachments, isImageAttachment, isWeComMediaIntakeLane } from '@/features/intake/utils/attachmentDisplay';
import {
  CLAIM_INTAKE_SAFETY_NOTE,
  buildClaimListSummary,
  claimBrokerDoneNextStep,
  claimDisplayStatus,
  claimLaneLabel,
  isClaimBrokerDone,
  isClaimGuidedCase,
  isClaimGuidedLane,
  resolveClaimSummary,
  resolveClaimEvidenceSummary,
} from '@/features/intake/utils/claimWorkbenchDisplay';
import {
  resolveCaseOpenErrorMessage,
  shouldFetchFormalCaseDetail,
  shouldShowCaseOpenFailureToast,
} from '@/features/intake/utils/workbenchCaseOpen';
import {
  countImagePreviews,
  createWorkbenchPerfSession,
  logCaseDetailLoaded,
  type WorkbenchPerfSession,
} from '@/features/intake/utils/workbenchPerfLog';
import { copyToClipboard } from '@/utils/demoCopy';

const { Title, Text, Paragraph } = Typography;

const OFFICE_NAME = 'Chen Kui Insurance Office';

export type P16BrokerPacket = {
  request_type?: string;
  readiness_status?: string;
  packet?: Record<string, { value?: string; source_file?: string }>;
  vehicles?: Array<{ year?: string; make?: string; model?: string; vin?: string }>;
  drivers?: Array<{ name?: string; relationship?: string }>;
  copy_text?: string;
  portal_copy_text?: string;
  opportunity_signals?: Array<{ code: string; meaning: string }>;
  broker_next_action?: { en?: string; zh?: string };
  follow_up_message_zh?: string;
  sources?: Array<{ file: string; fields: string }>;
  warnings?: string[];
};

type QueueRow = {
  key: string;
  case_id: string;
  customer_name: string;
  lane: string;
  status: string;
  summary: string;
  opportunity_badges: OpportunityBadge[];
  updated_at: string;
  attachment_count: number;
  raw: SavedCase;
};

type OpportunityBadge = {
  key: string;
  emoji: string;
  label: string;
};

const ACTION_FALLBACK: Record<string, string> = {
  READY: 'Ready for manual re-shop.',
  NEED_INFO: 'Customer needs declaration page.',
  BROKER_REVIEW: 'Broker review required.',
};

const ACTION_BANNER_STYLE: Record<string, { background: string; border: string; color: string }> = {
  READY: { background: '#f6ffed', border: '#b7eb8f', color: '#389e0d' },
  NEED_INFO: { background: '#fffbe6', border: '#ffe58f', color: '#d48806' },
  BROKER_REVIEW: { background: '#e6f4ff', border: '#91caff', color: '#0958d9' },
};

function isP16DocumentCase(c: SavedCase): boolean {
  if (c.workbench_archived) return false;
  const lane = (c.service_lane || '').trim();
  if (
    lane === 'add_car'
    || lane === 'policy_review'
    || lane === 'claim_lite'
    || lane === 'claim'
    || lane === 'coverage_risk'
  ) return true;
  if (c.demo_name === 'chen_kui_p18' && c.workbench_test) return true;
  const src = (c.source_text || '').toLowerCase();
  return src.includes('p16 add-car') || src.includes('p16 policy review');
}

/** P19H-3f-1c — broker queue: formal workflow cases only (no raw inbound). */
function isWorkbenchQueueCase(c: SavedCase): boolean {
  if (isWeComMediaIntakeLane(c.service_lane)) return false;
  if (isClaimBrokerDone(c)) return false;
  return isP16DocumentCase(c);
}

function laneLabel(c: SavedCase): string {
  const lane = (c.service_lane || '').trim();
  if (lane === 'wecom_media_intake') return '待确认材料';
  const blob = c.p16_broker_packet as P16BrokerPacket | undefined;
  const rt = blob?.request_type || '';
  if (isClaimGuidedLane(lane)) return claimLaneLabel();
  if (lane === 'policy_review' || rt === 'policy_review') return 'Policy Review';
  if (lane === 'claim_lite' || rt === 'claim_intake') return 'Claim Lite';
  if (lane === 'coverage_risk' || rt === 'coverage_risk') return 'Coverage Risk';
  if (rt === 'replace_vehicle') return 'Replace Vehicle';
  if (lane === 'add_car' || rt === 'add_vehicle') return 'Add Car';
  if ((c.workbench_tags ?? []).some((t) => /coverage risk/i.test(t))) return 'Coverage Risk';
  return 'Document Intake';
}

function laneTagColor(lane: string): string {
  if (lane === '待确认材料') return 'gold';
  if (lane === 'Add Car') return 'blue';
  if (lane === 'Policy Review') return 'purple';
  if (lane === 'Claim') return 'volcano';
  if (lane === 'Claim Lite') return 'volcano';
  if (lane === 'Coverage Risk') return 'red';
  if (lane === 'Replace Vehicle') return 'cyan';
  return 'default';
}

function readinessFromCase(c: SavedCase): string {
  const lane = (c.service_lane || '').trim();
  if (lane === 'wecom_media_intake') return 'HOLDING';
  const cat = (c.issue_category || '').toLowerCase();
  const blob = c.p16_broker_packet as P16BrokerPacket | undefined;

  if (isClaimGuidedLane(lane)) {
    if (isClaimBrokerDone(c)) return 'DONE';
    return 'BROKER_REVIEW';
  }
  if (lane === 'claim_lite' || cat === 'claim_intake') {
    return blob?.readiness_status || 'BROKER_REVIEW';
  }
  if (lane === 'coverage_risk' || cat === 'coverage_status_risk') {
    return blob?.readiness_status || 'BROKER_REVIEW';
  }
  if (lane === 'policy_review' || cat === 'premium_review') {
    if (blob?.readiness_status) return blob.readiness_status;
    return (c.still_needed_fields?.length ?? 0) > 0 ? 'BROKER_REVIEW' : 'READY';
  }
  if (lane === 'add_car' || cat === 'add_car') {
    if (!isAddCarReadyForBroker(c)) {
      const qrs = (c.quote_ready_status || '').trim();
      if (qrs === 'need_more' || (c.still_needed_fields?.length ?? 0) > 0) return 'NEED_INFO';
      return 'BROKER_REVIEW';
    }
    if (blob?.readiness_status === 'READY') return 'READY';
    if ((c.quote_ready_status || '').trim() === 'quote_ready') return 'READY';
    return blob?.readiness_status || 'BROKER_REVIEW';
  }
  if (blob?.readiness_status) return blob.readiness_status;
  const qrs = (c.quote_ready_status || '').trim();
  if (qrs === 'quote_ready' && isAddCarReadyForBroker(c)) return 'READY';
  if (qrs === 'almost_ready') return 'BROKER_REVIEW';
  if (qrs === 'need_more') return 'NEED_INFO';
  return 'BROKER_REVIEW';
}

function statusTag(status: string) {
  const s = status.toUpperCase();
  if (s === 'READY') return <Tag color="success">READY</Tag>;
  if (s === 'NEED_INFO') return <Tag color="warning">NEED_INFO</Tag>;
  if (s === 'HOLDING') return <Tag color="gold">待确认材料</Tag>;
  if (s === 'UNASSIGNED') return <Tag color="gold">待确认材料</Tag>;
  return <Tag color="processing">BROKER_REVIEW</Tag>;
}

function vehShortLabel(v: { year?: string; make?: string; model?: string }): string {
  const ymm = [v.year, v.make, v.model].filter(Boolean).join(' ');
  if (ymm) return ymm;
  const mm = [v.make, v.model].filter(Boolean).join(' ');
  return mm || v.model || v.make || '';
}

function isPolicyReviewCase(c: SavedCase): boolean {
  const lane = (c.service_lane || '').trim();
  const blob = c.p16_broker_packet as P16BrokerPacket | undefined;
  return lane === 'policy_review' || blob?.request_type === 'policy_review';
}

function hasHighLiabilityLimits(bodilyInjury: string): boolean {
  const normalized = bodilyInjury.replace(/\//g, '');
  return ['250', '300', '500'].some((x) => normalized.includes(x));
}

function buildOpportunityBadges(c: SavedCase): OpportunityBadge[] {
  if (!isPolicyReviewCase(c) || readinessFromCase(c) !== 'READY') return [];

  const blob = c.p16_broker_packet as P16BrokerPacket | undefined;
  if (!blob) return [];

  const badges: OpportunityBadge[] = [];
  const seen = new Set<string>();
  const add = (key: string, emoji: string, label: string) => {
    if (seen.has(key)) return;
    seen.add(key);
    badges.push({ key, emoji, label });
  };

  for (const signal of blob.opportunity_signals ?? []) {
    if (signal.code === 'REQUOTE_RECOMMENDED') add('reshop', '💰', 'Re-Shop');
    const meaning = (signal.meaning || '').toLowerCase();
    if (meaning.includes('home') || meaning.includes('renters') || meaning.includes('property')) {
      add('home', '🏠', 'Home');
    }
    if (meaning.includes('umbrella')) add('umbrella', '🛡', 'Umbrella');
  }

  if ((blob.vehicles?.length ?? 0) >= 2) add('multi_vehicle', '🚗', 'Multi-Vehicle');

  const bi = blob.packet?.bodily_injury?.value || '';
  if (bi && hasHighLiabilityLimits(bi)) add('umbrella', '🛡', 'Umbrella');

  return badges;
}

function resolveTopActionText(caseItem: SavedCase, blob: P16BrokerPacket | null): string {
  const fromBlob = blob?.broker_next_action?.en?.trim();
  if (fromBlob) return fromBlob;
  const fromCase = (caseItem.broker_next_step || caseItem.office_broker_next_step || '').trim();
  if (fromCase) return fromCase;
  return ACTION_FALLBACK[readinessFromCase(caseItem)] || ACTION_FALLBACK.BROKER_REVIEW;
}

function buildSummary(c: SavedCase): string {
  const lane = (c.service_lane || '').trim();
  if (lane === 'wecom_media_intake') {
    return 'WeChat photo received — classify as add car / policy / claim / DMV';
  }
  if (isClaimGuidedLane(lane)) {
    return buildClaimListSummary(c);
  }
  const blob = c.p16_broker_packet as P16BrokerPacket | undefined;

  if (blob?.request_type === 'policy_review') {
    const pkt = blob.packet || {};
    const carrier = pkt.current_carrier?.value || '';
    const premium = pkt.premium_amount?.value ? `$${pkt.premium_amount.value}` : '';
    const vehicles = blob.vehicles || [];
    let vehPart = '';
    if (vehicles.length >= 2) {
      const labels = vehicles.map(vehShortLabel).filter(Boolean);
      vehPart = labels.join(' + ');
    } else if (vehicles.length === 1) {
      vehPart = vehShortLabel(vehicles[0]);
    } else if (c.primary_vehicle_summary) {
      vehPart = c.primary_vehicle_summary;
    }
    return [carrier, premium, vehPart].filter(Boolean).join(' · ') || 'Policy review';
  }

  if (c.primary_vehicle_summary) return c.primary_vehicle_summary;
  const pkt = blob?.packet;
  if (pkt) {
    const ymm = [pkt.year?.value, pkt.make?.value, pkt.model?.value].filter(Boolean).join(' ');
    if (ymm) return ymm;
  }
  const conv = (c.conversation_summary || '').trim();
  if (readinessFromCase(c) === 'NEED_INFO' && c.still_needed_fields?.length) {
    return `Needs ${c.still_needed_fields.slice(0, 3).join(', ')}`;
  }
  if (conv) {
    return conv.replace(/^\[客户\]\s*P16\s+[^:]+:\s*/i, '').slice(0, 80) || '—';
  }
  return '—';
}

function formatUpdated(iso: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function OpportunityBadgeList({ badges }: { badges: OpportunityBadge[] }) {
  if (!badges.length) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
      {badges.map((b) => (
        <Tag
          key={b.key}
          style={{
            margin: 0,
            fontSize: 11,
            lineHeight: '18px',
            padding: '0 6px',
            borderRadius: 4,
          }}
        >
          {b.emoji} {b.label}
        </Tag>
      ))}
    </div>
  );
}

function TopActionBanner({ caseItem, blob }: { caseItem: SavedCase; blob: P16BrokerPacket | null }) {
  const status = readinessFromCase(caseItem);
  const style = ACTION_BANNER_STYLE[status] || ACTION_BANNER_STYLE.BROKER_REVIEW;
  const text = resolveTopActionText(caseItem, blob);
  return (
    <div
      style={{
        background: style.background,
        border: `1px solid ${style.border}`,
        borderRadius: 8,
        padding: '12px 14px',
        marginBottom: 12,
      }}
    >
      <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4, color: style.color }}>
        Next Step
      </Text>
      <Text style={{ fontSize: 14, lineHeight: 1.5, color: '#262626' }}>{text}</Text>
    </div>
  );
}

function MissingItemsCard({ fields }: { fields: string[] }) {
  if (!fields.length) return null;
  return (
    <Card
      size="small"
      title="Missing Items"
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: '10px 16px' } }}
    >
      {fields.map((field) => (
        <div key={field} style={{ marginBottom: 6, fontSize: 14, lineHeight: 1.5 }}>
          <Text>□ {humanizeStructuredField(field)}</Text>
        </div>
      ))}
    </Card>
  );
}

function PacketField({ label, value, source }: { label: string; value?: string; source?: string }) {
  if (!value) return null;
  return (
    <div style={{ marginBottom: 10 }}>
      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 2 }}>{label}</Text>
      <Text style={{ fontSize: 14 }}>{value}</Text>
      {source && <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>({source})</Text>}
    </div>
  );
}

function ClaimAccidentBasicsCard({ caseItem, collapsed = true }: { caseItem: SavedCase; collapsed?: boolean }) {
  const summary = resolveClaimSummary(caseItem);
  const [open, setOpen] = useState(!collapsed);
  return (
    <Card
      size="small"
      title={
        <span
          role="button"
          tabIndex={0}
          onClick={() => setOpen((v) => !v)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') setOpen((v) => !v);
          }}
          style={{ cursor: 'pointer', userSelect: 'none' }}
        >
          Accident Basics（详情）
        </span>
      }
      style={{ marginBottom: 12, opacity: 0.9 }}
      styles={{ body: { padding: open ? '12px 16px' : 0, display: open ? undefined : 'none' } }}
    >
      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
        {claimDisplayStatus(caseItem)}
      </Text>
      <PacketField label="Time" value={summary.accident_datetime ?? undefined} />
      <PacketField label="Location" value={summary.accident_location ?? undefined} />
      <PacketField label="Description" value={summary.accident_description ?? undefined} />
      <Alert
        type="info"
        showIcon
        style={{ marginTop: 8, marginBottom: 0 }}
        message={CLAIM_INTAKE_SAFETY_NOTE}
      />
    </Card>
  );
}

function BrokerCaseDetail({
  caseItem,
  blob,
  onCopyReport,
  onCopyPortal,
  onDelete,
  onConfirm,
  onClaimBrokerDone,
  onCaseChange,
  onRefreshCase,
  projectionLoading,
  projectionLoadError,
  confirmSaving,
  claimBrokerDoneSaving,
  perfSession,
}: {
  caseItem: SavedCase;
  blob: P16BrokerPacket | null;
  onCopyReport: () => void;
  onCopyPortal: () => void;
  onDelete: () => void;
  onConfirm?: () => void;
  onClaimBrokerDone?: () => void;
  onCaseChange?: (updated: SavedCase) => void;
  onRefreshCase?: () => Promise<SavedCase | null>;
  projectionLoading?: boolean;
  projectionLoadError?: string | null;
  confirmSaving?: boolean;
  claimBrokerDoneSaving?: boolean;
  perfSession?: WorkbenchPerfSession | null;
}) {
  const hasFullPacket = Boolean(blob?.packet && Object.keys(blob.packet).length > 0);
  const readiness = readinessFromCase(caseItem);
  const missingFields = caseItem.still_needed_fields ?? [];
  const knownFacts = caseItem.known_facts ?? {};
  const showConfirm = isAddCarReadyForBroker(caseItem) && !caseItem.broker_confirmed_at;
  const showClaimBrokerDone =
    isClaimGuidedCase(caseItem) && !isClaimBrokerDone(caseItem) && Boolean(onClaimBrokerDone);
  const isWeComMedia = isWeComMediaIntakeLane(caseItem.service_lane);
  const attachments = caseItem.case_attachments ?? [];

  if (!hasFullPacket) {
    return (
      <div>
        <Space style={{ marginBottom: 12 }} wrap>
          {statusTag(readiness)}
          <Tag color={laneTagColor(laneLabel(caseItem))}>{laneLabel(caseItem)}</Tag>
        </Space>
        <TopActionBanner caseItem={caseItem} blob={blob} />
        {(caseItem.workbench_test || caseItem.p20_case_intake_projection?.is_test) ? (
          <Tag color="orange" style={{ marginBottom: 8 }}>TEST / QA</Tag>
        ) : null}
        <MissingInformationChecklistPanel
          key={`intake-${caseItem.case_id}`}
          caseRecord={caseItem}
          onCaseChange={(updated) => onCaseChange?.(updated)}
          refreshCase={onRefreshCase}
        />
        {!(caseItem.customer_access?.access_ready || caseItem.p20_case_intake_projection?.customer_access?.access_ready) ? (
          <StructuredRequestMorePanel
            key={caseItem.case_id}
            caseRecord={caseItem}
            projectionLoading={projectionLoading}
            projectionLoadError={projectionLoadError}
            onCaseChange={(updated) => onCaseChange?.(updated)}
            refreshCase={onRefreshCase}
          />
        ) : null}
        {readiness === 'NEED_INFO' && missingFields.length > 0 ? (
          <MissingItemsCard fields={missingFields} />
        ) : null}
        {isClaimGuidedCase(caseItem) ? (
          <>
            <ClaimCaseBriefPanel
              brief={caseItem.claim_case_brief}
              timeline={caseItem.claim_timeline}
            />
            <ClaimAccidentBasicsCard caseItem={caseItem} collapsed />
            <ClaimEvidenceChecklist summary={resolveClaimEvidenceSummary(caseItem)} defaultCollapsed />
          </>
        ) : null}
        {isWeComMedia ? (
          <Card size="small" title="Customer" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
            <PacketField label="Name" value={resolveCustomerDisplayName(caseItem)} />
            <PacketField label="Source" value="WeCom" />
          </Card>
        ) : Object.keys(knownFacts).length > 0 && !isClaimGuidedCase(caseItem) ? (
          <Card size="small" title="Known Facts" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
            {Object.entries(knownFacts).map(([k, v]) => (
              <PacketField key={k} label={humanizeStructuredField(k)} value={String(v)} />
            ))}
          </Card>
        ) : (
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
            message="Full packet not stored for this case"
            description={
              <>
                <Paragraph style={{ marginBottom: 8 }}>
                  This case was saved before full packet persistence. Summary fields only:
                </Paragraph>
                <Text>Customer: {resolveCustomerDisplayName(caseItem)}</Text>
                <br />
                <Text>Phone: {caseItem.customer_phone || '—'}</Text>
              </>
            }
          />
        )}
        <CaseAttachmentsPanel
          caseId={caseItem.case_id}
          attachments={attachments}
          perfSession={perfSession}
        />
        {showConfirm && onConfirm ? (
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={onConfirm}
            loading={confirmSaving}
            block
            size="large"
            style={{ marginBottom: 8 }}
          >
            Confirm / Broker confirm
          </Button>
        ) : null}
        {showClaimBrokerDone ? (
          <Button
            icon={<CheckCircleOutlined />}
            onClick={onClaimBrokerDone}
            loading={claimBrokerDoneSaving}
            block
            style={{ marginBottom: 8 }}
          >
            陈总已确认 / 结束收集
          </Button>
        ) : null}
        {isClaimBrokerDone(caseItem) ? (
          <Alert
            type="success"
            showIcon
            style={{ marginBottom: 8 }}
            message={claimDisplayStatus(caseItem)}
            description={claimBrokerDoneNextStep()}
          />
        ) : null}
        {blob?.copy_text ? (
          <Button icon={<CopyOutlined />} onClick={onCopyReport} block style={{ marginBottom: 8 }}>
            Copy Report (partial)
          </Button>
        ) : null}
        <Button danger icon={<DeleteOutlined />} onClick={onDelete} block style={{ marginTop: 16 }}>
          Delete demo case / 删除测试案件
        </Button>
      </div>
    );
  }

  const pkt = blob!.packet!;
  const get = (k: string) => pkt[k]?.value || '';

  return (
    <div>
      <Space style={{ marginBottom: 12 }} wrap>
        {statusTag(blob!.readiness_status || readiness)}
        <Tag color={laneTagColor(laneLabel(caseItem))}>{laneLabel(caseItem)}</Tag>
      </Space>

      <TopActionBanner caseItem={caseItem} blob={blob} />
      {(caseItem.workbench_test || caseItem.p20_case_intake_projection?.is_test) ? (
        <Tag color="orange" style={{ marginBottom: 8 }}>TEST / QA</Tag>
      ) : null}
      <MissingInformationChecklistPanel
        key={`intake-${caseItem.case_id}`}
        caseRecord={caseItem}
        onCaseChange={(updated) => onCaseChange?.(updated)}
        refreshCase={onRefreshCase}
      />
      {!(caseItem.customer_access?.access_ready || caseItem.p20_case_intake_projection?.customer_access?.access_ready) ? (
        <StructuredRequestMorePanel
          key={caseItem.case_id}
          caseRecord={caseItem}
          projectionLoading={projectionLoading}
          projectionLoadError={projectionLoadError}
          onCaseChange={(updated) => onCaseChange?.(updated)}
          refreshCase={onRefreshCase}
        />
      ) : null}
      {readiness === 'NEED_INFO' && missingFields.length > 0 ? (
        <MissingItemsCard fields={missingFields} />
      ) : null}

      <Card size="small" title="Customer" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
        <PacketField label="Name" value={get('customer_name') || caseItem.customer_name} />
        <PacketField label="Phone" value={get('phone') || caseItem.customer_phone} />
        <PacketField label="Garaging ZIP" value={get('garaging_zip')} />
      </Card>

      {blob!.request_type === 'policy_review' ? (
        <>
          <Card size="small" title="Current Policy" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
            <PacketField label="Carrier" value={get('current_carrier')} source={pkt.current_carrier?.source_file} />
            <PacketField label="Premium" value={get('premium_amount')} source={pkt.premium_amount?.source_file} />
            <PacketField label="Policy Term" value={[get('policy_term_start'), get('policy_term_end')].filter(Boolean).join(' – ')} />
          </Card>
          {(blob!.vehicles?.length ?? 0) > 0 && (
            <Card size="small" title="Vehicles" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
              {blob!.vehicles!.map((v, i) => (
                <PacketField
                  key={i}
                  label={`Vehicle ${i + 1}`}
                  value={[v.year, v.make, v.model, v.vin ? `VIN ${v.vin}` : ''].filter(Boolean).join(' ')}
                />
              ))}
            </Card>
          )}
        </>
      ) : blob!.request_type === 'claim_intake' ? (
        <Card size="small" title="Claim Intake" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
          <PacketField label="Accident Time" value={get('accident_time')} />
          <PacketField label="Location" value={get('accident_location')} />
          <PacketField label="Other Vehicle" value={get('other_vehicle')} />
        </Card>
      ) : (
        <Card size="small" title="Vehicle" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
          <PacketField label="VIN" value={get('vin')} source={pkt.vin?.source_file} />
          <PacketField label="Year / Make / Model" value={[get('year'), get('make'), get('model')].filter(Boolean).join(' ')} />
          <PacketField label="Primary Driver" value={get('primary_driver')} />
          <PacketField
            label="Effective / Delivery Date"
            value={get('effective_date') || get('delivery_date')}
          />
        </Card>
      )}

      {blob!.follow_up_message_zh?.trim() && (
        <Card size="small" title="Chinese Follow-Up" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
          <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>{blob!.follow_up_message_zh}</Paragraph>
        </Card>
      )}

      {(blob!.sources?.length ?? 0) > 0 && (
        <Card size="small" title="Sources" style={{ marginBottom: 12 }} styles={{ body: { padding: '12px 16px' } }}>
          {blob!.sources!.map((s, i) => (
            <div key={i} style={{ fontSize: 12, marginBottom: 4 }}>
              <Text code>{s.file}</Text> → {s.fields}
            </div>
          ))}
        </Card>
      )}

      {(blob!.warnings?.length ?? 0) > 0 && (
        <Alert type="warning" showIcon message="Warnings" description={blob!.warnings!.join('; ')} style={{ marginBottom: 12 }} />
      )}

      <CaseAttachmentsPanel
        caseId={caseItem.case_id}
        attachments={attachments}
        perfSession={perfSession}
      />

      <Space direction="vertical" style={{ width: '100%' }} size={8}>
        {showConfirm && onConfirm ? (
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={onConfirm}
            loading={confirmSaving}
            block
            size="large"
          >
            Confirm / Broker confirm
          </Button>
        ) : null}
        {showClaimBrokerDone ? (
          <Button
            icon={<CheckCircleOutlined />}
            onClick={onClaimBrokerDone}
            loading={claimBrokerDoneSaving}
            block
          >
            陈总已确认 / 结束收集
          </Button>
        ) : null}
        {isClaimBrokerDone(caseItem) ? (
          <Alert
            type="success"
            showIcon
            message={claimDisplayStatus(caseItem)}
            description={claimBrokerDoneNextStep()}
          />
        ) : null}
        <Button type="primary" icon={<CopyOutlined />} onClick={onCopyReport} block size="large">
          Copy Report
        </Button>
        {blob!.portal_copy_text ? (
          <Button icon={<CopyOutlined />} onClick={onCopyPortal} block>
            Copy Portal Format
          </Button>
        ) : null}
        <Button danger icon={<DeleteOutlined />} onClick={onDelete} block style={{ marginTop: 8 }}>
          Delete demo case / 删除测试案件
        </Button>
      </Space>
    </div>
  );
}

function queueLoadErrorMessage(err: unknown): string {
  const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  if (status === 401 || detail === 'intake_api_unauthorized') {
    return 'Office queue requires API authorization — redeploy frontend with VITE_UNIFIED_INTAKE_INTAKE_API_KEY or check Cloud Run intake key.';
  }
  if (status === 403) {
    return 'Office queue blocked (403) — check X-Org-Id / office ownership settings.';
  }
  return 'Could not load office queue — check API connection and CORS.';
}

export default function DocumentIntakeInboxPage() {
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<QueueRow[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SavedCase | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailLoadError, setDetailLoadError] = useState<string | null>(null);
  const [drawerPerfSession, setDrawerPerfSession] = useState<WorkbenchPerfSession | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [confirmSaving, setConfirmSaving] = useState(false);
  const [claimBrokerDoneSaving, setClaimBrokerDoneSaving] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const resp = await listRecentCasesPage({ limit: 50, offset: 0 });
      const filtered = (resp.cases || []).filter(isWorkbenchQueueCase);
      const mapped = filtered.map((c) => ({
          key: c.case_id,
          case_id: c.case_id,
          customer_name: resolveCustomerDisplayName(c),
          lane: laneLabel(c),
          status: readinessFromCase(c),
          summary: buildSummary(c),
          opportunity_badges: buildOpportunityBadges(c),
          updated_at: c.updated_at || c.created_at || '',
          attachment_count: countCaseAttachments(c.case_attachments),
          raw: c,
        }));
      mapped.sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
      setRows(mapped);
    } catch (e) {
      const msg = queueLoadErrorMessage(e);
      setLoadError(msg);
      messageApi.error(msg);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [messageApi]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  const openCase = async (caseId: string) => {
    const stub = rows.find((r) => r.case_id === caseId)?.raw ?? null;
    const imageCount = countImagePreviews(stub?.case_attachments, isImageAttachment);
    const session = createWorkbenchPerfSession(caseId, imageCount);
    setDrawerPerfSession(session);
    setOpenId(caseId);
    setDetailLoadError(null);
    if (stub) setDetail(stub);

    if (!shouldFetchFormalCaseDetail(stub)) {
      logCaseDetailLoaded(session, 0);
      setDetailLoading(false);
      return;
    }

    setDetailLoading(true);
    const fetchStart = performance.now();
    let detailFetchFailed = false;
    try {
      const full = await getSavedCase(caseId);
      setDetail(full);
      const hydratedCount = countImagePreviews(full.case_attachments, isImageAttachment);
      if (hydratedCount !== session.imagePreviewCount) {
        session.imagePreviewCount = hydratedCount;
        session.attachmentCount = hydratedCount;
      }
      logCaseDetailLoaded(session, Math.round(performance.now() - fetchStart));
    } catch {
      detailFetchFailed = true;
      const msg = resolveCaseOpenErrorMessage(stub);
      setDetailLoadError(msg);
      if (shouldShowCaseOpenFailureToast(stub, detailFetchFailed)) {
        messageApi.error(msg);
      }
      if (!stub) setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const confirmDeleteCase = (caseId: string) => {
    Modal.confirm({
      title: 'Delete demo case / 删除测试案件',
      content: 'This will remove this demo/test case from the queue. Continue?',
      okText: 'Delete / 删除',
      okType: 'danger',
      cancelText: 'Cancel / 取消',
      onOk: async () => {
        setDeleting(true);
        try {
          await patchCaseWorkbench(caseId, { is_test: true });
          await deleteTestCase(caseId);
          messageApi.success('Case removed from queue');
          if (openId === caseId) {
            setOpenId(null);
            setDetail(null);
          }
          setRows((prev) => prev.filter((r) => r.case_id !== caseId));
        } catch (e: unknown) {
          const msg =
            (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
            ?? 'Could not delete case';
          messageApi.error(String(msg));
        } finally {
          setDeleting(false);
        }
      },
    });
  };

  const handleConfirmCase = async () => {
    if (!detail?.case_id) return;
    setConfirmSaving(true);
    try {
      const updated = await confirmCaseByBroker(detail.case_id);
      setDetail(updated);
      messageApi.success('Case confirmed');
      await loadQueue();
    } catch {
      messageApi.error('Could not confirm case');
    } finally {
      setConfirmSaving(false);
    }
  };

  const handleClaimBrokerDone = async () => {
    if (!detail?.case_id) return;
    setClaimBrokerDoneSaving(true);
    try {
      const updated = await markClaimBrokerDone(detail.case_id);
      const sent = Boolean(updated.end_card_sent);
      const skipped = Boolean(updated.end_card_send_skipped);
      messageApi.success(
        sent ? '已标记陈总确认，并发送结束提醒' : '已标记陈总确认',
      );
      if (skipped && !updated.already_done) {
        messageApi.info('结束提醒未发送（本地/测试环境）');
      }
      setOpenId(null);
      setDetail(null);
      await loadQueue();
    } catch {
      messageApi.error('无法标记陈总确认');
    } finally {
      setClaimBrokerDoneSaving(false);
    }
  };

  const syncDrawerCase = useCallback((updated: SavedCase) => {
    setDetail(updated);
    setRows((prev) =>
      prev.map((row) =>
        row.case_id === updated.case_id
          ? {
              ...row,
              status: readinessFromCase(updated),
              summary: buildSummary(updated),
              opportunity_badges: buildOpportunityBadges(updated),
              updated_at: updated.updated_at || updated.created_at || row.updated_at,
              attachment_count: countCaseAttachments(updated.case_attachments),
              raw: updated,
            }
          : row,
      ),
    );
  }, []);

  const refreshDrawerCase = useCallback(async () => {
    if (!detail?.case_id) return null;
    setDetailLoading(true);
    setDetailLoadError(null);
    try {
      const refreshed = await getSavedCase(detail.case_id);
      syncDrawerCase(refreshed);
      return refreshed;
    } catch {
      const msg = resolveCaseOpenErrorMessage(detail);
      setDetailLoadError(msg);
      messageApi.error(msg);
      return null;
    } finally {
      setDetailLoading(false);
    }
  }, [detail, messageApi, syncDrawerCase]);

  const detailBlob = useMemo((): P16BrokerPacket | null => {
    if (!detail) return null;
    const b = detail.p16_broker_packet;
    return b && typeof b === 'object' ? (b as P16BrokerPacket) : null;
  }, [detail]);

  const columns: ColumnsType<QueueRow> = [
    {
      title: 'Customer',
      dataIndex: 'customer_name',
      key: 'customer_name',
      width: 150,
      render: (name: string, row: QueueRow) => (
        <Space size={6}>
          <Text strong>{name}</Text>
          {row.raw.workbench_test || row.raw.p20_case_intake_projection?.is_test ? (
            <Tag color="orange">TEST</Tag>
          ) : null}
        </Space>
      ),
    },
    {
      title: 'Lane',
      dataIndex: 'lane',
      key: 'lane',
      width: 130,
      render: (lane: string) => <Tag color={laneTagColor(lane)}>{lane}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (s: string) => statusTag(s),
    },
    {
      title: 'Summary',
      dataIndex: 'summary',
      key: 'summary',
      ellipsis: true,
      render: (s: string, row: QueueRow) => (
        <div>
          <Text type="secondary">{s}</Text>
          <OpportunityBadgeList badges={row.opportunity_badges} />
        </div>
      ),
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 140,
      render: (v: string) => <Text style={{ fontSize: 13 }}>{formatUpdated(v)}</Text>,
    },
    {
      title: '',
      dataIndex: 'attachment_count',
      key: 'attachments',
      width: 48,
      align: 'center',
      render: (count: number) =>
        count > 0 ? (
          <Text style={{ fontSize: 13 }} title={`${count} attachment(s)`}>
            <PaperClipOutlined /> {count}
          </Text>
        ) : null,
    },
    {
      title: '',
      key: 'actions',
      width: 160,
      render: (_, row) => (
        <Space size={4}>
          <Button type="primary" size="small" onClick={() => openCase(row.case_id)}>
            Open
          </Button>
          <Button
            type="text"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => confirmDeleteCase(row.case_id)}
            title="Delete demo case / 删除测试案件"
          />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '28px 24px 48px' }}>
      {contextHolder}

      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: '0 0 6px' }}>
          <InboxOutlined style={{ marginRight: 10, color: '#1677ff' }} />
          Office Review Queue
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 14 }}>
          {OFFICE_NAME} — customer document intake cases awaiting broker review
        </Paragraph>
      </div>

      <Card
        style={{ borderRadius: 8, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}
        styles={{ body: { padding: rows.length === 0 && !loading && !loadError ? 0 : undefined } }}
        extra={
          <Space>
            <NewClaimEntryButton
              onCreated={(created) => {
                void loadQueue();
                setOpenId(created.case_id);
                setDetail(created);
                setDetailLoadError(null);
              }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadQueue} loading={loading}>
              Refresh
            </Button>
          </Space>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>
        ) : loadError ? (
          <Alert type="error" showIcon message="Could not load office queue" description={loadError} style={{ margin: 16 }} />
        ) : rows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '64px 24px' }}>
            <InboxOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
            <Title level={4} style={{ margin: '0 0 8px', fontWeight: 500 }}>No cases in queue</Title>
            <Paragraph type="secondary" style={{ maxWidth: 400, margin: '0 auto' }}>
              When a customer submits from the wizard, their case appears here for office review.
            </Paragraph>
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={rows}
            pagination={false}
            size="middle"
            rowClassName={() => 'office-queue-row'}
          />
        )}
      </Card>

      <Drawer
        title={
          detail
            ? `${resolveCustomerDisplayName(detail)} · ${laneLabel(detail)}`
            : 'Case detail'
        }
        width={520}
        open={Boolean(openId)}
        onClose={() => { setOpenId(null); setDetail(null); setDetailLoadError(null); setDrawerPerfSession(null); }}
        styles={{ body: { paddingTop: 12 } }}
        destroyOnClose
      >
        {detail ? (
          <>
            {detailLoading ? (
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>Refreshing case details…</Text>
              </div>
            ) : null}
            <BrokerCaseDetail
              caseItem={detail}
              blob={detailBlob}
              perfSession={drawerPerfSession}
              onCopyReport={async () => {
              const text = detailBlob?.copy_text || '';
              if (!text) { messageApi.warning('No copy text stored'); return; }
              const ok = await copyToClipboard(text);
              messageApi.success(ok ? 'Report copied' : 'Copy failed');
            }}
            onCopyPortal={async () => {
              const text = detailBlob?.portal_copy_text || '';
              if (!text) { messageApi.warning('No portal format stored'); return; }
              const ok = await copyToClipboard(text);
              messageApi.success(ok ? 'Portal format copied' : 'Copy failed');
            }}
            onDelete={() => confirmDeleteCase(detail.case_id)}
            onConfirm={() => void handleConfirmCase()}
            onClaimBrokerDone={() => void handleClaimBrokerDone()}
              onCaseChange={syncDrawerCase}
              onRefreshCase={refreshDrawerCase}
              projectionLoading={detailLoading}
              projectionLoadError={detailLoadError}
            confirmSaving={confirmSaving}
            claimBrokerDoneSaving={claimBrokerDoneSaving}
          />
          </>
        ) : detailLoading ? (
          <Skeleton active paragraph={{ rows: 6 }} />
        ) : null}
        {deleting && (
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Spin />
          </div>
        )}
      </Drawer>
    </div>
  );
}
