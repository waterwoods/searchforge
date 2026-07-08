/**
 * P19H-3a — Claim guided lane display helpers for Workbench document intake.
 * P19H-3c-3B — Claim evidence checklist formatting.
 */
import type { ClaimEvidenceSlot, ClaimEvidenceSummary, SavedCase } from '@/api/inboxTriage';

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

export function claimLaneLabel(): string {
  return 'Claim';
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
    summary.accident_datetime,
    summary.accident_location,
    summary.accident_description,
  ].filter((v): v is string => Boolean((v || '').trim()));
  if (parts.length) return parts.join(' · ');
  return (c.display_title || '').trim() || 'Claim intake';
}

export function claimDisplayStatus(c: SavedCase): string {
  const status = (c.display_status || '').trim();
  if (status) return status;
  return 'Claim Step 1 complete · Accident basics received';
}

export const CLAIM_INTAKE_SAFETY_NOTE =
  'This is intake only. Broker must confirm before any filing.';

export function resolveClaimEvidenceSummary(
  c: Pick<SavedCase, 'claim_evidence_summary'>,
): ClaimEvidenceSummary | null {
  const summary = c.claim_evidence_summary;
  if (!summary || typeof summary !== 'object' || !Array.isArray(summary.slots)) {
    return null;
  }
  return summary;
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
      return 'Broker 上传';
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
