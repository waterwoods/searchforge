/**
 * P19H-3a — Claim guided lane display helpers for Workbench document intake.
 * P19H-3c-3B — Claim evidence checklist formatting.
 */
import type { ClaimCaseBrief, ClaimEvidenceSlot, ClaimEvidenceSummary, ClaimTimelineEvent, SavedCase } from '@/api/inboxTriage';
import { CLAIM_PILOT_STATUS, normalizeClaimPilotStatus } from './claimPilotCopy';

export const SERVICE_LANE_CLAIM = 'claim';

export type ClaimSummary = {
  accident_datetime?: string | null;
  accident_location?: string | null;
  accident_description?: string | null;
};

/** Broker-safe copy must not appear in UI output */
export const CLAIM_EVIDENCE_FORBIDDEN_PHRASES = [
  '已报案',
  'claim 已正式提交',
  '已联系保险公司',
  '是对方责任',
  '一定会赔',
] as const;

const SKIP_REASON_LABELS: Record<string, string> = {
  no_other_party: '没有对方车辆 / 单方事故',
  not_available: '当时无法拍摄',
  hit_and_run: '对方逃逸',
  customer_not_safe_to_collect: '当时不安全未能拍摄',
};

export function isClaimGuidedLane(lane?: string | null): boolean {
  return (lane || '').trim() === SERVICE_LANE_CLAIM;
}

export function isClaimGuidedCase(c: Pick<SavedCase, 'service_lane'>): boolean {
  return isClaimGuidedLane(c.service_lane);
}

export const CLAIM_BROKER_DONE_PHASE = 'broker_done';

export function isClaimBrokerDone(c: Pick<SavedCase, 'workflow_phase' | 'display_status' | 'service_lane'>): boolean {
  if (!isClaimGuidedCase(c)) return false;
  const phase = (c.workflow_phase || '').trim().toLowerCase();
  if (phase === CLAIM_BROKER_DONE_PHASE) return true;
  const status = (c.display_status || '').trim();
  return status.includes('已确认') || status.includes('已交接');
}

export function claimBrokerDoneNextStep(): string {
  return '收集已结束。今日无需再向客户索取材料。';
}

export function claimLaneLabel(): string {
  return '理赔 · 处理中';
}

export function resolveClaimSummary(c: SavedCase): ClaimSummary {
  const fromApi = c.claim_summary;
  if (fromApi && typeof fromApi === 'object') {
    return {
      accident_datetime: fromApi.accident_datetime ?? null,
      accident_location: fromApi.accident_location ?? null,
      accident_description: fromApi.accident_description ?? null,
    };
  }
  const facts = c.known_facts ?? {};
  return {
    accident_datetime: facts.accident_datetime ?? null,
    accident_location: facts.accident_location ?? null,
    accident_description: facts.accident_description ?? null,
  };
}

export function buildClaimListSummary(c: SavedCase): string {
  const summary = resolveClaimSummary(c);
  const parts = [
    formatClaimAccidentDateTime(summary.accident_datetime),
    summary.accident_location,
    summary.accident_description,
  ].filter((v): v is string => Boolean((v || '').trim()) && v !== '—');
  if (parts.length) return parts.join(' · ');
  return (c.display_title || '').trim() || '理赔收件';
}

export function claimDisplayStatus(c: SavedCase): string {
  const status = (c.display_status || '').trim();
  if (status) {
    const frozen = normalizeClaimPilotStatus(status);
    if (frozen) return frozen;
    return status;
  }
  return '事故基本信息已收到';
}

/** Stage 2 — distinguish customer-confirmed linked policy from uploaded insurance card. */
export function policyContextEvidenceLabel(caseItem: {
  policy_context?: { status?: string; customer_choice?: string } | null;
  claim_attachment_slots?: Record<string, { status?: string } | undefined> | null;
  case_attachments?: Array<{ slot_assignment?: string; document_type?: string; evidence_category?: string }>;
} | null | undefined): string | null {
  if (!caseItem) return null;
  const slots = caseItem.claim_attachment_slots || {};
  const slot = slots.policy_or_insurance_card;
  if (slot && String(slot.status || '').toLowerCase() === 'received') {
    return '客户上传了保险卡';
  }
  const atts = Array.isArray(caseItem.case_attachments) ? caseItem.case_attachments : [];
  for (const att of atts) {
    const keys = [att.slot_assignment, att.document_type, att.evidence_category]
      .map((v) => String(v || '').toLowerCase());
    if (keys.some((k) => k === 'policy_or_insurance_card' || k === 'insurance_card' || k === 'insurance_card_photo')) {
      return '客户上传了保险卡';
    }
  }
  const pc = caseItem.policy_context;
  if (
    pc
    && String(pc.status || '').toLowerCase() === 'confirmed'
    && String(pc.customer_choice || '').toLowerCase() === 'correct'
  ) {
    return '已有保单资料，客户已确认';
  }
  return null;
}

export const CLAIM_INTAKE_SAFETY_NOTE =
  '当前仅为收件整理。正式报案前须由经纪人确认。';

export function resolveClaimEvidenceSummary(
  c: Pick<SavedCase, 'claim_evidence_summary'>,
): ClaimEvidenceSummary | null {
  const summary = c.claim_evidence_summary;
  if (!summary || typeof summary !== 'object' || !Array.isArray(summary.slots)) {
    return null;
  }
  return summary;
}

export function resolveClaimCaseBrief(
  brief?: ClaimCaseBrief | null,
): ClaimCaseBrief | null {
  if (!brief || typeof brief !== 'object' || !(brief.summary || '').trim()) {
    return null;
  }
  return brief;
}

export function formatClaimInjuryStatus(status?: string | null): string {
  switch ((status || '').trim().toLowerCase()) {
    case 'yes':
      return '有人受伤';
    case 'no':
      return '没有受伤';
    case 'unknown':
      return '尚未确认';
    default:
      return '尚未确认';
  }
}

export function formatClaimPoliceStatus(status?: string | null): string {
  switch ((status || '').trim().toLowerCase()) {
    case 'yes':
      return '已报警 / 提及';
    case 'no':
      return '未报警';
    case 'unknown':
      return '尚未确认';
    default:
      return '尚未确认';
  }
}

const TIMELINE_TYPE_LABELS: Record<string, string> = {
  claim_started: '开始记录',
  customer_text: '客户文字',
  customer_photo: '客户照片',
  customer_voice_stub: '语音消息',
  basics_complete: '基本信息齐全',
  broker_done: '陈总已确认',
  broker_office_materials_accepted: '资料已齐',
  evidence_uploaded: '已上传证据',
  evidence_received: '已收到证据',
  h5_step_complete: '客户已补充',
  request_sent: '已发出补充请求',
  field_saved: '客户已填写',
};

function formatTimelineWhen(iso?: string | null): string {
  const raw = String(iso || '').trim();
  if (!raw) return '';
  const t = Date.parse(raw);
  if (Number.isNaN(t)) return '';
  try {
    return new Date(t).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' });
  } catch {
    return '';
  }
}

/** Broker-facing accident datetime — local readable, never raw ISO UTC. */
export function formatClaimAccidentDateTime(raw?: string | null): string {
  const text = String(raw || '').trim();
  if (!text) return '—';
  const normalized = text.includes('T') ? text : text.replace(' ', 'T');
  const t = Date.parse(normalized);
  if (!Number.isNaN(t)) {
    try {
      return new Date(t).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' });
    } catch {
      /* fall through */
    }
  }
  // Already human-entered local text (keep); strip trailing Z/UTC markers if present.
  return text.replace(/Z$/i, '').replace(/\+00:00$/, '').trim() || '—';
}

export function formatClaimTimelinePreview(
  events: ClaimTimelineEvent[],
  limit = 3,
): Array<{ key: string; label: string }> {
  const sorted = [...(events || [])].sort((a, b) =>
    String(a.created_at || '').localeCompare(String(b.created_at || '')),
  );
  const recent = sorted.slice(-limit).reverse();
  return recent.map((event, index) => {
    const typeKey = String(event.event_type || '').trim();
    const typeLabel = TIMELINE_TYPE_LABELS[typeKey] || (typeKey ? '案件记录' : '记录');
    const text = (event.text || '').trim();
    const preview = text ? `：${text.slice(0, 48)}${text.length > 48 ? '…' : ''}` : '';
    const when = formatTimelineWhen(event.created_at);
    const whenSuffix = when ? ` · ${when}` : '';
    return {
      key: event.event_id || `evt-${index}`,
      label: `${typeLabel}${preview}${whenSuffix}`,
    };
  });
}

export function formatClaimUnassignedWecomPhotosSection(summary: ClaimEvidenceSummary): {
  summaryLine: string;
  guidanceLine: string;
  items: Array<{ key: string; label: string }>;
} | null {
  const block = summary.unassigned_wecom_photos;
  if (!block || typeof block !== 'object' || !block.count) {
    return null;
  }
  const count = block.count;
  const items = (block.items || []).map((item, index) => {
    const filename = (item.filename || 'wecom_image.jpg').trim();
    const receivedAt = (item.received_at || '').trim();
    const detail = receivedAt ? `${filename} · ${receivedAt}` : filename;
    return {
      key: item.attachment_id || `unassigned-${index}`,
      label: detail,
    };
  });
  return {
    summaryLine: `已收到 ${count} 张微信照片。`,
    guidanceLine:
      '这些照片已进入本理赔记录，但还没有归类到：自己车损 / 对方车辆车牌 / 现场照片。请陈总人工确认。',
    items,
  };
}

export function formatClaimEvidenceStatusIcon(status: string): string {
  switch ((status || '').trim().toLowerCase()) {
    case 'received':
      return '✅';
    case 'skipped':
      return '—';
    case 'needs_retake':
      return '↻';
    case 'missing':
    default:
      return '○';
  }
}

export function formatClaimEvidenceStatusLabel(status: string): string {
  switch ((status || '').trim().toLowerCase()) {
    case 'received':
      return '已收到';
    case 'skipped':
      return '已跳过';
    case 'needs_retake':
      return '需重传';
    case 'missing':
    default:
      return '还缺';
  }
}

export function formatClaimEvidenceRequiredLevel(level: string): string {
  switch ((level || '').trim().toLowerCase()) {
    case 'required':
      return '必需';
    case 'soft_required':
      return '建议补充';
    case 'optional':
      return '可选';
    default:
      return level || '';
  }
}

export function formatClaimEvidenceSource(channel: string): string {
  switch ((channel || '').trim().toLowerCase()) {
    case 'h5_task':
      return 'H5 上传';
    case 'wecom':
      return '微信上传';
    case 'broker_upload':
      return '经纪人上传';
    case 'none':
      return '未上传';
    default:
      return channel || '其他';
  }
}

export function formatClaimEvidenceSkipReason(reason: string | null | undefined): string {
  const key = (reason || '').trim();
  if (!key) return '';
  return SKIP_REASON_LABELS[key] || key;
}

export function formatClaimEvidenceSlotDetail(slot: ClaimEvidenceSlot): string {
  const status = (slot.status || '').trim().toLowerCase();
  const requiredLevel = (slot.required_level || '').trim().toLowerCase();

  if (status === 'received') {
    const source = formatClaimEvidenceSource(slot.source_channel);
    const count = slot.attachment_count > 0 ? slot.attachment_count : 1;
    return `已收到 · ${source} · ${count} 张`;
  }

  if (status === 'skipped') {
    const reason = formatClaimEvidenceSkipReason(slot.skip_reason);
    return reason ? `已跳过 · 原因：${reason}` : '已跳过';
  }

  if (status === 'needs_retake') {
    return '需重传 · 请陈总确认后联系客户补充';
  }

  if (status === 'missing') {
    if (requiredLevel === 'soft_required') {
      return '还缺 · 可补充，或记录无法提供原因';
    }
    if (requiredLevel === 'optional') {
      return '可选 · 有的话可以补充';
    }
    return '还缺 · 请客户补充';
  }

  return formatClaimEvidenceStatusLabel(status);
}

export function formatClaimEvidenceSlotLine(slot: ClaimEvidenceSlot): {
  icon: string;
  label: string;
  detail: string;
  statusLabel: string;
  requiredLevelLabel: string;
} {
  return {
    icon: formatClaimEvidenceStatusIcon(slot.status),
    label: slot.label,
    detail: formatClaimEvidenceSlotDetail(slot),
    statusLabel: formatClaimEvidenceStatusLabel(slot.status),
    requiredLevelLabel: formatClaimEvidenceRequiredLevel(slot.required_level),
  };
}

export function claimEvidenceCopyIsBrokerSafe(text: string): boolean {
  const content = text || '';
  return !CLAIM_EVIDENCE_FORBIDDEN_PHRASES.some((phrase) => content.includes(phrase));
}
