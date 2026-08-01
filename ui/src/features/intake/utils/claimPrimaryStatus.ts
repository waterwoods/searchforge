/**
 * Claim Workbench — one canonical primary next-action presentation.
 *
 * Completeness remains Cap2 checklist SSOT. This helper only chooses which
 * single primary status label Workbench surfaces (queue / header / Brief /
 * Request More card). Optional gaps never become the primary.
 */

import type { SavedCase, Slice1Projection } from '@/api/inboxTriage';
import { isCaseClosedHistory } from '@/features/intake/utils/caseLifecycle';
import { isClaimGuidedCase } from '@/features/intake/utils/claimWorkbenchDisplay';

/** Frozen primary labels — use exactly these strings on Claim Workbench. */
export const CLAIM_PRIMARY_STATUS = {
  closed: '已关闭 / 历史',
  waitingCustomer: '等待客户补充',
  waitingOfficeReview: '等待办公室审核',
  officeProcessing: '办公室处理中',
  suggestAccept: '建议确认资料已齐',
} as const;

export type ClaimPrimaryStatusKey =
  | 'closed'
  | 'waiting_customer'
  | 'waiting_office_review'
  | 'office_processing'
  | 'suggest_accept'
  | 'collect_missing';

export type ClaimPrimaryStatus = {
  key: ClaimPrimaryStatusKey;
  label: string;
};

function slice1Of(caseItem: SavedCase): Slice1Projection | null | undefined {
  return caseItem.slice1_projection || caseItem.p20_slice1_projection;
}

function slice1WorkflowState(caseItem: SavedCase): string {
  return String(slice1Of(caseItem)?.workflow_state || '').trim().toLowerCase();
}

/** Active unresolved Request More — customer still owes work. */
export function hasActiveUnresolvedRequestMore(caseItem: SavedCase): boolean {
  const waiting = String(caseItem.waiting_on || '').trim().toLowerCase();
  if (waiting === 'client') return true;

  const ws = slice1WorkflowState(caseItem);
  if (['broker_more_requested', 'customer_continuing'].includes(ws)) return true;

  const slice1 = slice1Of(caseItem);
  const openRequest = slice1?.open_request;
  if (openRequest) {
    const items = openRequest.items || [];
    const hasOpenItem = items.some((item) => {
      const st = String(item.status || '').trim().toLowerCase();
      return st === '' || st === 'active' || st === 'queued' || st === 'in_progress';
    });
    if (hasOpenItem) return true;
    const total = openRequest.progress?.total ?? 0;
    const satisfied = openRequest.progress?.satisfied ?? 0;
    if (total > 0 && satisfied < total) return true;
  }

  const display = String(caseItem.display_status || '').trim();
  if (display === '等待客户' || display.includes('等待客户')) return true;
  return false;
}

/** Broker clicked「已核对补充资料」— one idempotent timeline stamp. */
export function hasBrokerSupplementReviewed(caseItem: SavedCase): boolean {
  const timeline = caseItem.claim_timeline || [];
  return timeline.some(
    (event) => String(event.event_type || '').trim() === 'broker_supplement_reviewed',
  );
}

/**
 * Request More items were submitted; broker has not finished review.
 * Must beat Cap2-complete「建议确认资料已齐」so queue/header/Brief agree.
 *
 * After「已核对补充资料」, Slice1 leaves broker_review_ready — do not keep
 * trapping on satisfied open_request progress alone.
 */
export function hasRequestMoreAwaitingOfficeReview(caseItem: SavedCase): boolean {
  if (hasActiveUnresolvedRequestMore(caseItem)) return false;

  const slice1 = slice1Of(caseItem);
  const ws = slice1WorkflowState(caseItem);
  if (ws === 'broker_review_ready') return true;
  // Post-ack Slice1 state — Cap2 suggest-accept / missing step may take over.
  if (ws === 'broker_reviewing') return false;

  const brokerAction = slice1?.broker_next_action;
  const actionType = String(brokerAction?.action_type || '').trim().toLowerCase();
  const actionStatus = String(brokerAction?.status || '').trim().toLowerCase();
  if (actionType === 'review_customer_response' || actionStatus === 'review_ready') {
    return true;
  }

  // Ack stamp clears stale access / progress heuristics until a new review-ready cycle.
  if (hasBrokerSupplementReviewed(caseItem)) return false;

  const access = caseItem.customer_access || caseItem.p20_case_intake_projection?.customer_access;
  if (String(access?.simple_status || '').toLowerCase().includes('ready for review')) {
    return true;
  }

  const openRequest = slice1?.open_request;
  if (openRequest) {
    const total = openRequest.progress?.total ?? 0;
    const satisfied = openRequest.progress?.satisfied ?? 0;
    // Only when Slice1 state is unknown — never after explicit broker_reviewing.
    if (!ws && total > 0 && satisfied >= total) return true;
  }

  const waiting = String(caseItem.waiting_on || '').trim().toLowerCase();
  if (
    !ws
    && waiting === 'broker'
    && Boolean(openRequest || access?.request_sent || access?.access_ready)
  ) {
    return true;
  }

  return false;
}

/** Cap2 Must Haves present — checklist/Brief SSOT, not a second completeness engine. */
export function cap2MustHavesPresentForOffice(caseItem: SavedCase): boolean {
  const brief = caseItem.claim_case_brief;
  if (brief && typeof brief.can_accept_office_materials === 'boolean') {
    return Boolean(brief.can_accept_office_materials);
  }
  const facts = (caseItem.known_facts || {}) as Record<string, unknown>;
  const filled = (key: string) => Boolean(String(facts[key] ?? '').trim());
  return (
    filled('accident_description')
    && filled('accident_datetime')
    && filled('accident_location')
    && filled('injury_status')
  );
}

function collectMissingLabel(caseItem: SavedCase): string {
  const brief = caseItem.claim_case_brief;
  const next = String(brief?.next_best_question || '').trim();
  if (next && !next.includes('建议确认资料已齐')) return next;

  const missing = (brief?.missing_info || []).filter((item) => {
    const sev = String(item.severity || '').trim().toLowerCase();
    return sev === 'critical' || sev === 'important';
  });
  if (missing.length > 0) {
    return `请补充：${missing.map((m) => m.label).filter(Boolean).slice(0, 2).join('、')}`;
  }

  const display = String(caseItem.display_status || '').trim();
  if (
    display
    && !['BROKER_REVIEW', 'READY', 'NEED_INFO', 'DONE', 'HOLDING'].includes(display.toUpperCase())
    && !display.includes('办公室处理中')
  ) {
    return display;
  }
  return '打开案件核对';
}

/**
 * Precedence (Claim cases only):
 * 1. Closed / History
 * 2. Active unresolved Request More → 等待客户补充
 * 3. Customer submitted Request More, awaiting review → 等待办公室审核
 * 4. office_materials_accepted_at → 办公室处理中
 * 5. Cap2 Must Have gaps empty → 建议确认资料已齐
 * 6. Otherwise → genuine Cap2 missing next step
 *
 * Notes:
 * - office accept overrides「建议确认资料已齐」.
 * - Active Request More overrides passive office-processing.
 */
export function resolveClaimPrimaryStatus(caseItem: SavedCase): ClaimPrimaryStatus {
  if (isCaseClosedHistory(caseItem)) {
    return { key: 'closed', label: CLAIM_PRIMARY_STATUS.closed };
  }

  if (hasActiveUnresolvedRequestMore(caseItem)) {
    return { key: 'waiting_customer', label: CLAIM_PRIMARY_STATUS.waitingCustomer };
  }

  if (hasRequestMoreAwaitingOfficeReview(caseItem)) {
    return { key: 'waiting_office_review', label: CLAIM_PRIMARY_STATUS.waitingOfficeReview };
  }

  if (String(caseItem.office_materials_accepted_at || '').trim()) {
    return { key: 'office_processing', label: CLAIM_PRIMARY_STATUS.officeProcessing };
  }

  const display = String(caseItem.display_status || '').trim();
  if (display === '办公室处理中' || display.includes('办公室处理中')) {
    return { key: 'office_processing', label: CLAIM_PRIMARY_STATUS.officeProcessing };
  }

  if (cap2MustHavesPresentForOffice(caseItem)) {
    return { key: 'suggest_accept', label: CLAIM_PRIMARY_STATUS.suggestAccept };
  }

  return { key: 'collect_missing', label: collectMissingLabel(caseItem) };
}

/** Whether Request More access card may own the primary status chrome. */
export function requestMoreOwnsPrimaryStatus(caseItem: SavedCase): boolean {
  if (!isClaimGuidedCase(caseItem)) return true;
  const key = resolveClaimPrimaryStatus(caseItem).key;
  return key === 'waiting_customer' || key === 'waiting_office_review';
}
