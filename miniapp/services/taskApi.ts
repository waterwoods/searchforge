/**
 * CustomerTaskApi — channel-neutral facade over existing H5 task backend routes.
 *
 * Backend contracts (P19M-1 spike + P20 Slice 1):
 * - GET  /api/h5/tasks/{token}/intake
 * - PATCH /api/h5/tasks/{token}/fields
 * - POST /api/h5/tasks/{token}/submit
 * - POST /api/h5/tasks/{token}/request-items/{item_id}/submit
 * - GET  /api/h5/tasks/{uploadToken}
 * - POST /api/h5/tasks/{uploadToken}/upload
 */

import type {
  CustomerTask,
  Slice1CommandResult,
  Slice1SubmissionCommand,
  UploadSlotInfo,
} from "../types/task";
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
  options?: { onProgress?: (progress: number) => void; uploadIntentId?: string },
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
      ...(options?.uploadIntentId ? { upload_intent_id: options.uploadIntentId } : {}),
    },
    options,
  );
}

export function extractAttachmentId(uploadResponse: unknown): string {
  if (!uploadResponse || typeof uploadResponse !== "object") return "";
  return String((uploadResponse as { attachment_id?: unknown }).attachment_id || "").trim();
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

export async function submitRequestItem(
  token: string,
  itemId: string,
  command: Slice1SubmissionCommand,
): Promise<Slice1CommandResult> {
  const path = `/api/h5/tasks/${enc(token)}/request-items/${enc(itemId)}/submit`;
  try {
    return await requestJson<Slice1CommandResult>("POST", path, {
      command_id: command.command_id,
      idempotency_key: command.idempotency_key,
      expected_case_version: command.expected_case_version,
      client_draft_id: command.client_draft_id || null,
      fact: command.fact || null,
      evidence: command.evidence || null,
    });
  } catch (err) {
    if (err instanceof ApiRequestError) {
      const detail = err.detail;
      if (detail && typeof detail === "object" && "outcome" in (detail as object)) {
        return detail as Slice1CommandResult;
      }
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
  extractAttachmentId,
  submitTask,
  submitRequestItem,
  getOrCreateSubmitIntentId,
  extractUploadToken: extractTokenFromUrl,
};
