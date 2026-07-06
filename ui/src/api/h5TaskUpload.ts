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

export async function fetchH5Task(taskToken: string): Promise<H5TaskInfo> {
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}`);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    const detail = (body as { detail?: string }).detail || resp.statusText;
    throw new Error(detail);
  }
  return resp.json();
}

export async function uploadH5TaskImage(
  taskToken: string,
  file: File,
): Promise<H5UploadResult> {
  const form = new FormData();
  form.append('file', file, file.name);
  const resp = await fetch(`${API_BASE_URL}/api/h5/tasks/${encodeURIComponent(taskToken)}/upload`, {
    method: 'POST',
    body: form,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    const detail = (body as { detail?: string }).detail || resp.statusText;
    throw new Error(detail);
  }
  return resp.json();
}
