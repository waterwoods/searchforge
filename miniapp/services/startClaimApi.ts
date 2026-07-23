/**
 * Customer Start Claim — thin Mini Program client over Cap2 CreateClaim facade.
 * Always sends a bindable session_id (durable wx_* preferred).
 */

import { ApiRequestError, requestJson, uploadFile } from "../utils/request";
import { getCustomerSessionId, resolveStartClaimSessionId } from "./sessionIdentityAdapter";
import { appConfig } from "../utils/config";
import type { StoryTranscriptDraft } from "./taskApi";

export type CustomerStartClaimCommand = {
  command_id: string;
  idempotency_key: string;
  accident_description?: string;
  accident_datetime?: string;
  accident_location?: string;
  injury_status?: string;
  correlation_id?: string;
};

export type CustomerStartClaimResult = {
  ok: boolean;
  outcome: "accepted" | "replayed" | "resumed" | string;
  error_code?: string;
  /** P26G — opaque signed resume token; persist for Task Home / return-later. */
  resume_token?: string;
  resume_expires_at?: string;
};

export function mintStartClaimCommandIds(): {
  command_id: string;
  idempotency_key: string;
} {
  const stamp = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
  return {
    command_id: `start_claim_${stamp}`,
    idempotency_key: `start_claim_idem_${stamp}`,
  };
}

export async function startClaim(
  command: CustomerStartClaimCommand,
): Promise<CustomerStartClaimResult> {
  const sessionId = await resolveStartClaimSessionId();
  return requestJson<CustomerStartClaimResult>("POST", "/api/h5/customer/start-claim", {
    command_id: command.command_id,
    idempotency_key: command.idempotency_key,
    correlation_id: command.correlation_id || command.command_id,
    session_id: sessionId,
    accident_description: (command.accident_description || "").trim() || undefined,
    accident_datetime: (command.accident_datetime || "").trim() || undefined,
    accident_location: (command.accident_location || "").trim() || undefined,
    injury_status: (command.injury_status || "").trim() || undefined,
    is_test: Boolean(appConfig.prototypeMode),
  });
}

/** P30: same Voice Story draft STT as Story task, for Start Claim (pre-case). */
export async function transcribeStartClaimStoryAudio(
  localFilePath: string,
  options?: { recordingDurationMs?: number },
): Promise<StoryTranscriptDraft> {
  const formData: Record<string, string> = {};
  const sessionId = getCustomerSessionId();
  if (sessionId) formData.session_id = sessionId;
  if (options?.recordingDurationMs != null && Number.isFinite(options.recordingDurationMs)) {
    formData.recording_duration_ms = String(Math.max(0, Math.round(options.recordingDurationMs)));
  }
  const path = "/api/h5/customer/start-claim/story/transcribe";
  console.info("[p28_voice_upload]", {
    event: "upload_start",
    path_suffix: path,
    has_session: Boolean(sessionId),
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

export async function emitStartClaimVoiceRecordStart(): Promise<void> {
  try {
    await requestJson("POST", "/api/h5/customer/start-claim/story/voice-event", {
      event: "voice_record_start",
      session_id: getCustomerSessionId() || undefined,
    });
  } catch {
    // Metrics must not block recording.
  }
}
