/**
 * Shared Voice Story input helpers (P28/P30).
 * Same UI phase model for Story task page and Start Claim.
 */

import { ApiRequestError } from "./request";

export const VOICE_MAX_RECORD_MS = 60_000;

export type VoicePhase = "idle" | "recording" | "transcribing" | "draft" | "stt_failed";

export type VoiceSession = {
  rawTranscript: string;
  speechProvider: string;
  sttLatencyMs: number;
  recordingDurationMs: number;
};

export type VoiceUiPatch = {
  voicePhase: VoicePhase;
  showRecordBtn: boolean;
  showStopBtn: boolean;
  recordBtnLabel: string;
  recordBtnDisabled: boolean;
  storyInputDisabled: boolean;
  confirmDisabled: boolean;
};

/** Keep WXML free of complex ===/ternary — bind simple booleans/labels only. */
export function voiceUiPatch(
  phase: VoicePhase,
  busy: { saving?: boolean; submitting?: boolean },
): VoiceUiPatch {
  const recording = phase === "recording";
  const transcribing = phase === "transcribing";
  const blocked = Boolean(busy.saving) || Boolean(busy.submitting);
  return {
    voicePhase: phase,
    showRecordBtn: !recording,
    showStopBtn: recording,
    recordBtnLabel: phase === "draft" || phase === "stt_failed" ? "重新录音" : "录音",
    recordBtnDisabled: blocked || transcribing,
    storyInputDisabled: transcribing,
    confirmDisabled: blocked || recording || transcribing,
  };
}

export function initialVoiceUiData(): VoiceUiPatch & {
  voiceHint: string;
  voiceSession: VoiceSession | null;
} {
  return {
    voiceHint: "",
    voiceSession: null,
    ...voiceUiPatch("idle", {}),
  };
}

export function sttFailureCopy(err: unknown): string {
  if (err instanceof ApiRequestError) {
    const code = String(err.code || "");
    const status = Number(err.status || 0);
    const detail = err.detail;
    const kind =
      detail && typeof detail === "object"
        ? String((detail as { error_kind?: unknown; message?: unknown }).error_kind || "")
        : "";
    const message =
      detail && typeof detail === "object"
        ? String((detail as { message?: unknown }).message || "")
        : typeof detail === "string"
          ? detail
          : "";
    if (code === "backend_unreachable" || code === "network_error" || code === "timeout") {
      return "上传失败，请重试录音，或直接打字填写。";
    }
    // Exact Founder QA failure: Preview hit QA host before /story/transcribe was deployed.
    if (
      status === 404 ||
      code === "Not Found" ||
      code === "http_404" ||
      message === "Not Found" ||
      code === "stt_route_missing"
    ) {
      return "语音识别接口未开通，请直接打字填写。";
    }
    if (
      kind === "unsupported_media" ||
      code === "unsupported_media" ||
      message === "audio_too_large" ||
      message === "empty_audio"
    ) {
      return "录音格式不支持，请直接打字填写。";
    }
    if (kind === "empty" || message === "empty_transcript" || code === "empty") {
      return "没有识别出文字，请重录或直接打字填写。";
    }
    if (message === "speech_not_configured" || message === "stt_auth_failed") {
      return "语音识别暂不可用，请直接打字填写。";
    }
    return "语音识别失败，请直接打字填写。";
  }
  return "语音识别失败，请直接打字填写。";
}

export function logVoiceUploadDiagnostic(payload: Record<string, unknown>): void {
  // No token, no audio bytes, no transcript text.
  console.info("[p28_voice_upload]", payload);
}
