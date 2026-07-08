/**
 * P19D-2 / P19D-4A — H5 guided upload API client.
 */
import { API_BASE_URL } from './config';

export type H5FlowStep = {
  slot: string;
  label: string;
  instruction: string;
  required: boolean;
  status: 'pending' | 'completed' | 'skipped';
  required_level?: string;
  skippable?: boolean;
};

export type H5SkipReason = {
  key: string;
  label: string;
};

export type H5TaskInfo = {
  lane: string;
  title: string;
  task_label: string;
  instruction: string;
  max_images: number;
  accept: string;
  /** v1 single-slot */
  slot?: string;
  step_current?: number;
  step_total?: number;
  /** v2 photo flow */
  flow?: string;
  case_id?: string;
  flow_complete?: boolean;
  current_step?: string | null;
  step_index?: number;
  steps?: H5FlowStep[];
  /** Claim evidence pack */
  slot_key?: string;
  slot_label?: string;
  slot_title?: string;
  required_level?: string;
  skippable?: boolean;
  skip_reasons?: H5SkipReason[];
  accepted_media_types?: string[];
  safety_copy?: string;
  eligible_for_ocr?: boolean;
  next_slot?: string | null;
};

export type H5UploadResult = {
  attachment_id?: string | null;
  slot_assignment: string;
  status: string;
  next_step: string;
  message_zh: string;
  flow_complete?: boolean;
  next_slot?: string;
};

const H5_API_ERROR_ZH: Record<string, string> = {
  invalid_or_expired_task_link: '链接无效或已过期，请联系陈总重新获取。',
  lane_mismatch: '任务与当前服务事项不匹配，请返回微信重新获取加车链接。',
  user_ref_mismatch: '链接与账号不匹配，请返回微信重新获取加车链接。',
  case_mismatch: '任务与当前服务事项不匹配，请联系陈总。',
  case_not_found: '找不到对应的服务事项，请联系陈总。',
  empty_file: '未收到图片，请重新选择一张照片。',
  file_too_large: '图片超过 5MB，请压缩后重试。',
  not_an_image: '请上传照片（JPG/PNG/HEIC）。',
  unsupported_image_type: '图片格式不支持，请换 JPG/PNG/HEIC 后重试。',
  case_persist_failed: '保存失败，请稍后重试或联系陈总。',
  slot_required: '请按当前步骤上传照片。',
  wrong_slot_order: '请按顺序完成当前步骤的照片上传。',
  flow_already_complete: '照片步骤已完成，请返回微信补充文字信息。',
  slot_not_skippable: '此步骤不能跳过。',
  skip_not_supported: '此任务不支持跳过。',
};

function mapH5ApiError(detail: string, status: number): string {
  const code = (detail || '').trim();
  if (code && H5_API_ERROR_ZH[code]) return H5_API_ERROR_ZH[code];
  if (status === 403) return H5_API_ERROR_ZH.invalid_or_expired_task_link;
  if (status >= 500) return '服务器繁忙，请稍后重试。';
  return code || '上传失败，请稍后重试。';
}

async function readApiError(resp: Response): Promise<string> {
  const body = await resp.json().catch(() => ({}));
  const detail = String((body as { detail?: string }).detail || resp.statusText || '');
  return mapH5ApiError(detail, resp.status);
}

export function isPhotoFlowTask(task: H5TaskInfo): boolean {
  return Boolean(task.flow);
}

export async function fetchH5Task(taskToken: string): Promise<H5TaskInfo> {
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}`);
  if (!resp.ok) {
    throw new Error(await readApiError(resp));
  }
  return resp.json();
}

export async function uploadH5TaskImage(
  taskToken: string,
  file: File,
  slot?: string,
): Promise<H5UploadResult> {
  const form = new FormData();
  form.append('file', file, file.name || 'upload.jpg');
  if (slot) {
    form.append('slot', slot);
  }
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/upload`, {
    method: 'POST',
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readApiError(resp));
  }
  return resp.json();
}

export async function skipH5TaskSlot(
  taskToken: string,
  slot: string,
): Promise<H5UploadResult> {
  const form = new FormData();
  form.append('slot', slot);
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/skip`, {
    method: 'POST',
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readApiError(resp));
  }
  return resp.json();
}
