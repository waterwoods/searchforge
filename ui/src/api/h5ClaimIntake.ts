/**
 * P19H-3h-1A — H5 Claim structured intake API client.
 */
import { API_BASE_URL } from './config';
import type {
  Slice1CommandResult,
  Slice1NextAction,
  Slice1Projection,
  Slice1RequestProgress,
} from './inboxTriage';

export type H5ClaimDashboardSummary = {
  title: string;
  subtitle: string;
  status: string;
  received: string[];
  missing: string[];
  next_action: string;
  primary_cta: string;
  secondary_cta: string;
  submitted_supplement_allowed: boolean;
  warning: string;
};

export type H5ClaimCompletionSummary = {
  title: string;
  message: string;
  received: string[];
  missing: string[];
  missing_clear_message?: string | null;
  next_step: string;
  disclaimer: string;
};

export type H5ClaimTaskContractV1 = {
  contract_version?: string;
  task_id?: string;
  task_type?: string;
  workflow_state?: string;
  aggregate_version?: number;
  next_action?: Slice1NextAction | null;
  queued_request_items?: unknown[];
  request_progress?: Slice1RequestProgress;
  server_timestamp?: string;
};

export type H5ClaimIntakeInfo = {
  lane: string;
  flow: string;
  case_id: string;
  title: string;
  safety_copy: string;
  steps: string[];
  current_step: string;
  completed_count: number;
  step_total: number;
  submitted: boolean;
  phase: string;
  key_facts: Record<string, string | null>;
  missing_info: Array<{ key?: string; field?: string; label: string }>;
  injury_alert?: boolean;
  already_submitted?: boolean;
  submit_intent_id?: string;
  upload_url?: string | null;
  attachment_count?: number;
  photo_count?: number;
  completion_summary?: H5ClaimCompletionSummary;
  dashboard_summary?: H5ClaimDashboardSummary;
  wecom_confirmation_sent?: boolean;
  wecom_confirmation_pending?: boolean;
  /** Authoritative Slice 1 projection when enabled */
  slice1_projection?: Slice1Projection | null;
  task_contract_v1?: H5ClaimTaskContractV1 | null;
  /** True when Slice 1 was expected but live projection could not be loaded */
  slice1_projection_error?: boolean;
  /** QA/test claim only — never set for production customers */
  is_test?: boolean;
  /** Human-readable QA marker (no case IDs / PII) */
  customer_qa_marker?: string | null;
};

export type H5RequestItemSubmitPayload = {
  command_id: string;
  idempotency_key: string;
  expected_case_version: number;
  client_draft_id?: string | null;
  fact?: { field: string; value: string } | null;
  evidence?: { attachment_id: string } | null;
};

export type H5RequestItemSubmitResult = Slice1CommandResult;

const H5_ERROR_MESSAGES: Record<string, string> = {
  invalid_or_expired_task_link: '链接已失效，请回微信发送「进度」获取新的填写链接。',
  save_failed: '保存失败，请检查网络后重试。',
  submit_failed: '提交失败，请重试。如果仍失败，可以继续在微信里联系陈总。',
  network_error: '网络异常，请检查后重试。',
  projection_load_failed: '补充任务暂时无法加载，请重试。',
  load_failed: '暂时无法打开，请重试。',
  vin_invalid: 'VIN 格式不正确，请输入 17 位（不含 I/O/Q）。',
  version_conflict: '资料已更新，请刷新后重试。',
  request_item_not_active: '当前补充任务已变化，请刷新后查看。',
  illegal_state: '当前状态无法提交，请刷新后查看。',
  customer_submit_not_supported: '该项资料暂时无法在此填写，请回微信联系陈总办公室。',
  unsupported_draft_item_type_for_send: '请求中包含暂不支持客户填写的项目，请联系陈总办公室。',
};

export function mapH5ClaimError(code: string, fallback?: string): string {
  return H5_ERROR_MESSAGES[code] || fallback || code;
}

async function parseH5Error(res: Response): Promise<string> {
  const body = await res.json().catch(() => ({}));
  const detail = (body as { detail?: unknown }).detail;
  if (res.status === 403 && detail === 'invalid_or_expired_task_link') {
    return 'invalid_or_expired_task_link';
  }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const errorCode = String((detail as { error_code?: string }).error_code || '').trim();
    if (errorCode) return errorCode;
  }
  if (typeof detail === 'string' && detail.trim()) return detail;
  return `http_${res.status}`;
}

export async function fetchH5ClaimIntake(taskToken: string): Promise<H5ClaimIntakeInfo> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/intake`);
  } catch {
    throw new Error('network_error');
  }
  if (res.status === 403) {
    throw new Error('invalid_or_expired_task_link');
  }
  if (!res.ok) {
    throw new Error(await parseH5Error(res));
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

export async function patchH5ClaimFields(
  taskToken: string,
  step: string,
  fields: Record<string, string>,
): Promise<H5ClaimIntakeInfo> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/fields`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ step, fields }),
    });
  } catch {
    throw new Error('network_error');
  }
  if (!res.ok) {
    throw new Error(await parseH5Error(res));
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

export async function submitH5ClaimIntake(
  taskToken: string,
  submitIntentId: string,
): Promise<H5ClaimIntakeInfo> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Submit-Intent-Id': submitIntentId,
      },
      body: JSON.stringify({ submit_intent_id: submitIntentId }),
    });
  } catch {
    throw new Error('submit_failed');
  }
  if (!res.ok) {
    throw new Error(await parseH5Error(res));
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

/** Cap 3B: satisfy the active Slice 1 request item (e.g. VIN). */
export async function submitH5RequestItem(
  taskToken: string,
  itemId: string,
  payload: H5RequestItemSubmitPayload,
): Promise<H5RequestItemSubmitResult> {
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/request-items/${encodeURIComponent(itemId)}/submit`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      },
    );
  } catch {
    throw new Error('network_error');
  }
  if (!res.ok) {
    throw new Error(await parseH5Error(res));
  }
  return res.json() as Promise<H5RequestItemSubmitResult>;
}

/** Merge Slice 1 command projection into local H5 intake info (Cap 3B receipt). */
export function applySlice1ProjectionToIntake(
  info: H5ClaimIntakeInfo,
  projection: Slice1Projection | null | undefined,
): H5ClaimIntakeInfo {
  if (!projection || typeof projection !== 'object') return info;
  const nextAction = projection.customer_next_action ?? null;
  const priorContract = info.task_contract_v1 || {};
  return {
    ...info,
    slice1_projection: projection,
    slice1_projection_error: false,
    task_contract_v1: {
      ...priorContract,
      workflow_state: projection.workflow_state,
      aggregate_version: projection.aggregate_version,
      next_action: nextAction,
      queued_request_items: projection.queued_request_items || [],
      request_progress: projection.request_progress,
      server_timestamp: projection.server_timestamp,
    },
  };
}

export function newSubmitIntentId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `submit-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function newCommandId(prefix = 'cmd'): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
