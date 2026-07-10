/**
 * P19H-3h-1A — H5 Claim structured intake API client.
 */
import { API_BASE_URL } from './config';

export type H5ClaimCompletionSummary = {
  title: string;
  message: string;
  received: string[];
  missing: string[];
  missing_clear_message?: string | null;
  next_step: string;
  disclaimer: string;
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
  wecom_confirmation_sent?: boolean;
  wecom_confirmation_pending?: boolean;
};

const H5_ERROR_MESSAGES: Record<string, string> = {
  invalid_or_expired_task_link: '链接已失效，请回微信发送「进度」获取新的填写链接。',
  save_failed: '保存失败，请检查网络后重试。',
  submit_failed: '提交失败，请重试。如果仍失败，可以继续在微信里联系陈总。',
  network_error: '保存失败，请检查网络后重试。',
};

export function mapH5ClaimError(code: string, fallback?: string): string {
  return H5_ERROR_MESSAGES[code] || fallback || code;
}

async function parseH5Error(res: Response): Promise<string> {
  const body = await res.json().catch(() => ({}));
  const detail = (body as { detail?: string }).detail || `http_${res.status}`;
  if (res.status === 403 && detail === 'invalid_or_expired_task_link') {
    return 'invalid_or_expired_task_link';
  }
  return detail;
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

export function newSubmitIntentId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `submit-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
