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

export type VoiceStoryAudit = {
  raw_transcript: string;
  confirmed_story: string;
  speech_provider?: string;
  stt_latency_ms?: number;
  recording_duration_ms?: number;
};

export type StoryTranscriptDraft = {
  raw_transcript: string;
  speech_provider: string;
  stt_latency_ms: number;
  recording_duration_ms?: number | null;
  audio_retained?: boolean;
};

export async function getTask(token: string): Promise<CustomerTask> {
  return requestJson<CustomerTask>("GET", `/api/h5/tasks/${enc(token)}/intake`);
}

export async function saveStory(
  token: string,
  accidentDescription: string,
  voiceAudit?: VoiceStoryAudit | null,
): Promise<CustomerTask> {
  return saveFields(token, "story", { accident_description: accidentDescription }, voiceAudit || undefined);
}

export async function transcribeStoryAudio(
  token: string,
  localFilePath: string,
  options?: { recordingDurationMs?: number },
): Promise<StoryTranscriptDraft> {
  const formData: Record<string, string> = {};
  if (options?.recordingDurationMs != null && Number.isFinite(options.recordingDurationMs)) {
    formData.recording_duration_ms = String(Math.max(0, Math.round(options.recordingDurationMs)));
  }
  const path = `/api/h5/tasks/${enc(token)}/story/transcribe`;
  console.info("[p28_voice_upload]", {
    event: "upload_start",
    path_suffix: "/api/h5/tasks/*/story/transcribe",
    has_token: Boolean(token),
    has_file: Boolean(localFilePath),
    recording_duration_ms: formData.recording_duration_ms || null,
  });
  try {
    const data = await uploadFile(path, localFilePath, formData);
    if (!data || typeof data !== "object") {
      throw new ApiRequestError("stt_failed");
    }
    const body = data as StoryTranscriptDraft;
    return {
      raw_transcript: String(body.raw_transcript || ""),
      speech_provider: String(body.speech_provider || "google_chirp"),
      stt_latency_ms: Number(body.stt_latency_ms || 0),
      recording_duration_ms: body.recording_duration_ms ?? null,
      audio_retained: Boolean(body.audio_retained),
    };
  } catch (err) {
    if (err instanceof ApiRequestError) {
      if (err.status === 404) {
        throw new ApiRequestError("stt_route_missing", 404, err.detail);
      }
      throw err;
    }
    throw new ApiRequestError("stt_failed");
  }
}

export async function emitVoiceRecordStart(token: string): Promise<void> {
  try {
    await requestJson("POST", `/api/h5/tasks/${enc(token)}/story/voice-event`, {
      event: "voice_record_start",
    });
  } catch {
    // Metrics must not block recording.
  }
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
  voiceAudit?: VoiceStoryAudit,
): Promise<CustomerTask> {
  try {
    const body: Record<string, unknown> = { step, fields };
    if (voiceAudit) {
      const roundMs = (n: unknown): number | undefined => {
        if (n == null || n === "") return undefined;
        const num = Number(n);
        if (!Number.isFinite(num) || num < 0) return undefined;
        return Math.round(num);
      };
      body.voice_audit = {
        raw_transcript: voiceAudit.raw_transcript,
        confirmed_story: voiceAudit.confirmed_story,
        speech_provider: voiceAudit.speech_provider || "google_chirp",
        stt_latency_ms: roundMs(voiceAudit.stt_latency_ms),
        recording_duration_ms: roundMs(voiceAudit.recording_duration_ms),
      };
    }
    return await requestJson<CustomerTask>("PATCH", `/api/h5/tasks/${enc(token)}/fields`, body);
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
      if (detail && typeof detail === "object") {
        const obj = detail as Record<string, unknown>;
        if ("outcome" in obj) {
          return detail as Slice1CommandResult;
        }
        // ValueError paths return { error } without outcome — treat as rejected,
        // not transport-uncertain (avoids stuck "提交结果未确认" on validation).
        const errorCode = String(obj.error_code || obj.error || "").trim();
        if (errorCode) {
          return {
            outcome: "rejected",
            command_id: command.command_id,
            idempotency_key: command.idempotency_key,
            error_code: errorCode,
          } as Slice1CommandResult;
        }
      }
      throw err;
    }
    throw new ApiRequestError("submit_failed");
  }
}

export const CustomerTaskApi = {
  getTask,
  saveStory,
  transcribeStoryAudio,
  emitVoiceRecordStart,
  saveBasics,
  getUploadTaskInfo,
  uploadPhoto,
  extractAttachmentId,
  submitTask,
  submitRequestItem,
  getOrCreateSubmitIntentId,
  extractUploadToken: extractTokenFromUrl,
};
