/**
 * P19D-2 — H5 guided single-slot upload API client.
 */
import { API_BASE_URL } from './config';

export type H5TaskInfo = {
  lane: string;
  slot: string;
  title: string;
  task_label: string;
  instruction: string;
  step_current: number;
  step_total: number;
  max_images: number;
  accept: string;
};

export type H5UploadResult = {
  attachment_id: string;
  slot_assignment: string;
  status: string;
  next_step: string;
  message_zh: string;
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
): Promise<H5UploadResult> {
  const form = new FormData();
  form.append('file', file, file.name || 'upload.jpg');
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/upload`, {
    method: 'POST',
    body: form,
  });
  if (!resp.ok) {
    throw new Error(await readApiError(resp));
  }
  return resp.json();
}
