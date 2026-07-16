/**
 * P20 Capability 3A/3B — H5 QR landing decision (server projection SSOT).
 * Cap 3A: active Request More item → request-item screen.
 * Cap 3B: after VIN submit → submitted_waiting (broker reviewing).
 * Projection load failure → retry (never silent overview fallback).
 */
import type { Slice1NextAction, Slice1Projection, Slice1RequestProgress } from '@/api/inboxTriage';
import type { H5ClaimIntakeInfo } from '@/api/h5ClaimIntake';

export type H5ClaimLandingKind =
  | 'loading'
  | 'token_error'
  | 'load_error'
  | 'projection_error'
  | 'request_item'
  | 'submitted_waiting'
  | 'overview';

export type H5ClaimLandingDecision = {
  kind: H5ClaimLandingKind;
  nextAction: Slice1NextAction | null;
  progress: Slice1RequestProgress;
  qaMarker: string | null;
  title: string;
  instructions: string;
  itemType: string;
  retryable: boolean;
  errorMessage: string;
};

const EMPTY_PROGRESS: Slice1RequestProgress = { satisfied: 0, total: 0, remaining: 0 };

const ACTIONABLE_TYPES = new Set(['provide_fact', 'provide_evidence']);

/** Cap 3B customer success copy — received + reviewing; no approval promise. */
export const CAP3B_RECEIVED_TITLE = '资料已收到';
export const CAP3B_REVIEWING_INSTRUCTIONS = '陈总正在审核中。';
export const CAP3B_NO_APPROVAL_DISCLAIMER =
  '不代表已通过审核，也不代表已向保险公司正式报案。';

export function isActiveRequestItemAction(
  action: Slice1NextAction | null | undefined,
): action is Slice1NextAction {
  if (!action || typeof action !== 'object') return false;
  const type = String(action.action_type || '').trim();
  if (!ACTIONABLE_TYPES.has(type)) return false;
  return Boolean(String(action.request_item_id || '').trim());
}

export function isWaitingForBrokerReviewAction(
  action: Slice1NextAction | null | undefined,
): boolean {
  if (!action || typeof action !== 'object') return false;
  return String(action.action_type || '').trim() === 'wait_for_broker_review';
}

export function extractAuthoritativeNextAction(
  info: H5ClaimIntakeInfo | null | undefined,
): Slice1NextAction | null {
  if (!info) return null;
  const fromProjection = info.slice1_projection?.customer_next_action;
  if (fromProjection && typeof fromProjection === 'object') return fromProjection;
  const fromV1 = info.task_contract_v1?.next_action;
  if (fromV1 && typeof fromV1 === 'object') return fromV1;
  return null;
}

export function extractRequestProgress(
  info: H5ClaimIntakeInfo | null | undefined,
  nextAction?: Slice1NextAction | null,
): Slice1RequestProgress {
  const projection = info?.slice1_projection;
  const raw =
    projection?.request_progress ||
    projection?.open_request?.progress ||
    info?.task_contract_v1?.request_progress ||
    null;
  if (raw && typeof raw === 'object') {
    return {
      satisfied: Number(raw.satisfied || 0),
      total: Math.max(Number(raw.total || 0), 0),
      remaining: Number(raw.remaining || 0),
    };
  }
  if (nextAction && isActiveRequestItemAction(nextAction)) {
    const total = Number(nextAction.ordering?.total || 1);
    const position = Number(nextAction.ordering?.position || 1);
    return {
      satisfied: Math.max(0, position - 1),
      total: Math.max(total, 1),
      remaining: 1,
    };
  }
  return { ...EMPTY_PROGRESS };
}

export function requestItemTitle(nextAction: Slice1NextAction | null): string {
  const required = String(nextAction?.required_input || '').trim().toLowerCase();
  if (required === 'vin') return '补充车辆 VIN';
  const title = String(nextAction?.title || '').trim();
  if (title) return title;
  return '补充陈总需要的资料';
}

export function requestItemInstructions(nextAction: Slice1NextAction | null): string {
  const instructions = String(nextAction?.instructions || '').trim();
  if (instructions) return instructions;
  return '陈总需要这项资料继续处理';
}

export function resolveCustomerQaMarker(
  info: H5ClaimIntakeInfo | null | undefined,
  nextAction?: Slice1NextAction | null,
): string | null {
  if (!info) return null;
  const explicit = String(info.customer_qa_marker || '').trim();
  if (explicit) return explicit;
  if (!info.is_test) return null;
  const action = nextAction || extractAuthoritativeNextAction(info);
  const required = String(action?.required_input || '')
    .trim()
    .toLowerCase();
  if (required === 'vin') return 'TEST · Cap3A VIN QA';
  if (isWaitingForBrokerReviewAction(action)) return 'TEST · Cap3B Review QA';
  if (info.slice1_projection?.workflow_state === 'broker_review_ready') {
    return 'TEST · Cap3B Review QA';
  }
  return 'QA Test Claim';
}

/** True when rendered customer copy would leak a raw case id. */
export function customerUiLeaksCaseId(text: string, caseId?: string | null): boolean {
  const raw = String(text || '');
  if (!raw) return false;
  if (caseId && raw.includes(caseId)) return true;
  return /\bcase_[a-f0-9]{8,}\b/i.test(raw);
}

export function resolveH5ClaimLanding(args: {
  loading: boolean;
  loadError: string | null;
  info: H5ClaimIntakeInfo | null;
}): H5ClaimLandingDecision {
  const { loading, loadError, info } = args;
  if (loading) {
    return {
      kind: 'loading',
      nextAction: null,
      progress: { ...EMPTY_PROGRESS },
      qaMarker: null,
      title: '',
      instructions: '',
      itemType: '',
      retryable: false,
      errorMessage: '',
    };
  }

  if (loadError === 'invalid_or_expired_task_link') {
    return {
      kind: 'token_error',
      nextAction: null,
      progress: { ...EMPTY_PROGRESS },
      qaMarker: null,
      title: '链接已失效',
      instructions: '',
      itemType: '',
      retryable: false,
      errorMessage: loadError,
    };
  }

  if (loadError && !info) {
    return {
      kind: 'load_error',
      nextAction: null,
      progress: { ...EMPTY_PROGRESS },
      qaMarker: null,
      title: '暂时无法打开',
      instructions: '',
      itemType: '',
      retryable: true,
      errorMessage: loadError,
    };
  }

  if (info?.slice1_projection_error) {
    return {
      kind: 'projection_error',
      nextAction: null,
      progress: { ...EMPTY_PROGRESS },
      qaMarker: resolveCustomerQaMarker(info),
      title: '暂时无法加载补充任务',
      instructions: '',
      itemType: '',
      retryable: true,
      errorMessage: 'projection_load_failed',
    };
  }

  const nextAction = extractAuthoritativeNextAction(info);
  const qaMarker = resolveCustomerQaMarker(info, nextAction);
  const progress = extractRequestProgress(info, nextAction);

  if (isActiveRequestItemAction(nextAction)) {
    return {
      kind: 'request_item',
      nextAction,
      progress,
      qaMarker,
      title: requestItemTitle(nextAction),
      instructions: requestItemInstructions(nextAction),
      itemType: String(nextAction.required_input || '').trim().toLowerCase(),
      retryable: false,
      errorMessage: '',
    };
  }

  // Cap 3B: after successful VIN submit (or resume), show receipt — not overview.
  const workflowState = String(info?.slice1_projection?.workflow_state || '').trim();
  if (isWaitingForBrokerReviewAction(nextAction) || workflowState === 'broker_review_ready') {
    const title =
      String(nextAction?.title || '').trim() || CAP3B_RECEIVED_TITLE;
    const instructions =
      String(nextAction?.instructions || '').trim() || CAP3B_REVIEWING_INSTRUCTIONS;
    return {
      kind: 'submitted_waiting',
      nextAction,
      progress,
      qaMarker,
      title,
      instructions,
      itemType: '',
      retryable: false,
      errorMessage: '',
    };
  }

  return {
    kind: 'overview',
    nextAction: null,
    progress,
    qaMarker,
    title: info?.dashboard_summary?.title || info?.title || '我的事故资料',
    instructions: '',
    itemType: '',
    retryable: false,
    errorMessage: '',
  };
}

export function projectionHasActiveRequestItem(projection: Slice1Projection | null | undefined): boolean {
  return isActiveRequestItemAction(projection?.customer_next_action);
}
