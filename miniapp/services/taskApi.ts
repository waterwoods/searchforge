/**
 * CustomerTaskApi — channel-neutral facade over existing H5 task backend routes.
 *
 * Backend contracts (P19M-1 spike):
 * - GET  /api/h5/tasks/{token}/intake     → intake_info_for_token()
 * - PATCH /api/h5/tasks/{token}/fields    → patch_intake_fields(step, fields)
 * - POST /api/h5/tasks/{token}/submit     → submit_intake_form + X-Submit-Intent-Id
 * - GET  /api/h5/tasks/{uploadToken}      → claim evidence pack slot metadata
 * - POST /api/h5/tasks/{uploadToken}/upload → ingest_h5_slot_upload(file, slot)
 *
 * Story field key: accident_description (step=story)
 * Photo uploads use separate claim_evidence_pack token from task.upload_url
 * Submit requires injury, time_location, story, vehicle_other_party complete
 * Evidence step is optional for submit
 */

import type { CustomerTask, UploadSlotInfo } from "../types/task";
import { ApiRequestError, requestJson, uploadFile } from "../utils/request";
import { extractTokenFromUrl, newSubmitIntentId } from "../utils/taskMapping";
import { saveSubmitIntentId, loadSubmitIntentId } from "../utils/storage";

function enc(token: string): string {
  return encodeURIComponent(token);
}

export async function getTask(token: string): Promise<CustomerTask> {
  return requestJson<CustomerTask>("GET", `/api/h5/tasks/${enc(token)}/intake`);
}

export async function saveStory(token: string, accidentDescription: string): Promise<CustomerTask> {
  return saveFields(token, "story", { accident_description: accidentDescription });
}

export async function saveBasics(
  token: string,
  fields: Record<string, string>,
  step: string,
): Promise<CustomerTask> {
  return saveFields(token, step, fields);
}

async function saveFields(
  token: string,
  step: string,
  fields: Record<string, string>,
): Promise<CustomerTask> {
  try {
    return await requestJson<CustomerTask>("PATCH", `/api/h5/tasks/${enc(token)}/fields`, {
      step,
      fields,
    });
  } catch (err) {
    if (err instanceof ApiRequestError) {
      throw err;
    }
    throw new ApiRequestError("save_failed");
  }
}

export async function getUploadTaskInfo(uploadUrl: string): Promise<UploadSlotInfo> {
  const uploadToken = extractTokenFromUrl(uploadUrl);
  if (!uploadToken) {
    throw new ApiRequestError("invalid_upload_url");
  }
  return requestJson<UploadSlotInfo>("GET", `/api/h5/tasks/${enc(uploadToken)}`);
}

export async function uploadPhoto(
  uploadUrl: string,
  localFilePath: string,
  slot: string,
  options?: { onProgress?: (progress: number) => void },
): Promise<unknown> {
  const uploadToken = extractTokenFromUrl(uploadUrl);
  if (!uploadToken) {
    throw new ApiRequestError("invalid_upload_url");
  }
  return uploadFile(
    `/api/h5/tasks/${enc(uploadToken)}/upload`,
    localFilePath,
    {
      slot,
    },
    options,
  );
}

export function getOrCreateSubmitIntentId(): string {
  const existing = loadSubmitIntentId();
  if (existing) return existing;
  const created = newSubmitIntentId();
  saveSubmitIntentId(created);
  return created;
}

export async function submitTask(token: string, submitIntentId?: string): Promise<CustomerTask> {
  const intent = (submitIntentId || getOrCreateSubmitIntentId()).trim();
  saveSubmitIntentId(intent);
  try {
    return await requestJson<CustomerTask>(
      "POST",
      `/api/h5/tasks/${enc(token)}/submit`,
      { submit_intent_id: intent },
      { "X-Submit-Intent-Id": intent },
    );
  } catch (err) {
    if (err instanceof ApiRequestError) {
      throw err;
    }
    throw new ApiRequestError("submit_failed");
  }
}

export const CustomerTaskApi = {
  getTask,
  saveStory,
  saveBasics,
  getUploadTaskInfo,
  uploadPhoto,
  submitTask,
  getOrCreateSubmitIntentId,
  extractUploadToken: extractTokenFromUrl,
};
