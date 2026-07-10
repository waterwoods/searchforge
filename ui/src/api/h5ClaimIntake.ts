/**
 * P19H-3h-1A — H5 Claim structured intake API client.
 */
import { API_BASE_URL } from './config';

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
  missing_info: Array<{ key: string; label: string }>;
  injury_alert?: boolean;
  already_submitted?: boolean;
  submit_intent_id?: string;
  upload_url?: string | null;
  attachment_count?: number;
  photo_count?: number;
};

export async function fetchH5ClaimIntake(taskToken: string): Promise<H5ClaimIntakeInfo> {
  const res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/intake`);
  if (res.status === 403) {
    throw new Error('invalid_or_expired_task_link');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || `http_${res.status}`);
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

export async function patchH5ClaimFields(
  taskToken: string,
  step: string,
  fields: Record<string, string>,
): Promise<H5ClaimIntakeInfo> {
  const res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/fields`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ step, fields }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || `http_${res.status}`);
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

export async function submitH5ClaimIntake(
  taskToken: string,
  submitIntentId: string,
): Promise<H5ClaimIntakeInfo> {
  const res = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Submit-Intent-Id': submitIntentId,
    },
    body: JSON.stringify({ submit_intent_id: submitIntentId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail || `http_${res.status}`);
  }
  return res.json() as Promise<H5ClaimIntakeInfo>;
}

export function newSubmitIntentId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `submit-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
