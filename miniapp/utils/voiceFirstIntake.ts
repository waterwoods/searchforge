/**
 * Voice-first Guided Intake V1 — pure front-door helpers (no Page runtime).
 *
 * VOICE IS INPUT. AI IS PROPOSAL. CUSTOMER CONFIRMATION IS AUTHORITY.
 * Existing text / full-form Start Claim remains the fallback path.
 */

export type VoiceFrontDoor = "voice" | "text" | "full";

/** Customer-visible voice-door lifecycle (before guided review). */
export type VoiceFirstPhase =
  | "idle"
  | "recording"
  | "processing_speech"
  | "organizing"
  | "failed";

export type VoiceFirstFailureKind =
  | "privacy_denied"
  | "mic_denied"
  | "recording_failed"
  | "stt_failed"
  | "empty_transcript"
  | "network_failed"
  | "ai_failed"
  | "unsupported";

export const VOICE_FIRST_TITLE = "出事故了？先说一遍";
export const VOICE_FIRST_MIC_LABEL = "说一下发生了什么";
export const VOICE_FIRST_SECONDARY_TEXT = "不方便录音？文字输入";
export const VOICE_FIRST_FULL_FORM_TEXT = "使用完整表单填写";
export const VOICE_FIRST_RETRY_TEXT = "重新录音";

export const VOICE_FIRST_STATUS_COPY: Record<VoiceFirstPhase, string> = {
  idle: "按住麦克风，用普通话简单说清发生了什么。",
  recording: "正在录音…说完后点停止",
  processing_speech: "正在识别语音…",
  organizing: "AI正在整理事故信息…",
  failed: "",
};

export const VOICE_FIRST_FAILURE_COPY: Record<VoiceFirstFailureKind, string> = {
  privacy_denied: "未同意隐私授权。不方便录音？请改用文字输入，或使用完整表单。",
  mic_denied: "未获得麦克风权限，请改用文字输入，或使用完整表单。",
  recording_failed: "录音失败，请重试，或改用文字输入。",
  stt_failed: "语音识别失败，请重试，或改用文字输入。",
  empty_transcript: "没有识别出文字，请重录，或改用文字输入。",
  network_failed: "网络不稳定，请重试录音，或改用文字输入。",
  ai_failed: "AI暂时无法整理，您仍可文字补充后继续。",
  unsupported: "当前环境无法录音，请改用文字输入，或使用完整表单。",
};

export type VoiceFirstUiPatch = {
  frontDoor: VoiceFrontDoor;
  showVoiceFrontDoor: boolean;
  voiceFirstPhase: VoiceFirstPhase;
  voiceFirstTitle: string;
  voiceFirstMicLabel: string;
  voiceFirstStatus: string;
  voiceFirstSecondaryText: string;
  voiceFirstFullFormText: string;
  voiceFirstRetryText: string;
  voiceFirstShowRetry: boolean;
  voiceFirstShowStop: boolean;
  voiceFirstMicDisabled: boolean;
};

export function emptyVoiceFirstUi(
  frontDoor: VoiceFrontDoor = "voice",
): VoiceFirstUiPatch {
  const show = frontDoor === "voice";
  return {
    frontDoor,
    showVoiceFrontDoor: show,
    voiceFirstPhase: "idle",
    voiceFirstTitle: VOICE_FIRST_TITLE,
    voiceFirstMicLabel: VOICE_FIRST_MIC_LABEL,
    voiceFirstStatus: show ? VOICE_FIRST_STATUS_COPY.idle : "",
    voiceFirstSecondaryText: VOICE_FIRST_SECONDARY_TEXT,
    voiceFirstFullFormText: VOICE_FIRST_FULL_FORM_TEXT,
    voiceFirstRetryText: VOICE_FIRST_RETRY_TEXT,
    voiceFirstShowRetry: false,
    voiceFirstShowStop: false,
    voiceFirstMicDisabled: false,
  };
}

/**
 * Resolve front door from launch query + feature flag.
 * Escape hatches: mode=text|full|legacy|form, voice=0, entry=full
 */
export function resolveVoiceFrontDoor(
  options: Record<string, string | undefined> | null | undefined,
  opts?: { enabled?: boolean },
): VoiceFrontDoor {
  const enabled = opts?.enabled !== false;
  const q = options || {};
  const mode = String(q.mode || "").trim().toLowerCase();
  const voice = String(q.voice || "").trim().toLowerCase();
  const entry = String(q.entry || "").trim().toLowerCase();

  if (!enabled || voice === "0" || voice === "off" || voice === "false") {
    return mode === "full" || entry === "full" ? "full" : "text";
  }
  if (mode === "text" || mode === "legacy" || mode === "form") return "text";
  if (mode === "full" || entry === "full") return "full";
  if (mode === "voice" || mode === "voice_first" || mode === "") return "voice";
  return "voice";
}

export function voiceFirstUiPatch(
  frontDoor: VoiceFrontDoor,
  phase: VoiceFirstPhase,
  opts?: { busy?: boolean; failureKind?: VoiceFirstFailureKind | null },
): VoiceFirstUiPatch {
  const busy = Boolean(opts?.busy);
  const show = frontDoor === "voice";
  const recording = phase === "recording";
  const processing =
    phase === "processing_speech" || phase === "organizing";
  const failed = phase === "failed";
  const status = failed
    ? VOICE_FIRST_FAILURE_COPY[opts?.failureKind || "stt_failed"]
    : VOICE_FIRST_STATUS_COPY[phase];
  return {
    frontDoor,
    showVoiceFrontDoor: show,
    voiceFirstPhase: phase,
    voiceFirstTitle: VOICE_FIRST_TITLE,
    voiceFirstMicLabel: VOICE_FIRST_MIC_LABEL,
    voiceFirstStatus: show ? status : "",
    voiceFirstSecondaryText: VOICE_FIRST_SECONDARY_TEXT,
    voiceFirstFullFormText: VOICE_FIRST_FULL_FORM_TEXT,
    voiceFirstRetryText: VOICE_FIRST_RETRY_TEXT,
    voiceFirstShowRetry: show && failed,
    voiceFirstShowStop: show && recording,
    voiceFirstMicDisabled: busy || processing || recording,
  };
}

/** Map STT / recorder errors → customer failure kind (for copy + fallbacks). */
export function classifyVoiceFirstFailure(err: unknown): VoiceFirstFailureKind {
  if (!err) return "stt_failed";
  if (typeof err === "string") {
    const s = err.toLowerCase();
    if (s.includes("privacy")) {
      return "privacy_denied";
    }
    if (s.includes("mic") || s.includes("permission") || s.includes("authorize")) {
      return "mic_denied";
    }
    if (s.includes("empty")) return "empty_transcript";
    if (s.includes("network") || s.includes("timeout") || s.includes("unreachable")) {
      return "network_failed";
    }
    if (s.includes("record")) return "recording_failed";
    return "stt_failed";
  }
  const anyErr = err as {
    code?: string;
    status?: number;
    message?: string;
    detail?: { error_kind?: string; message?: string } | string;
  };
  const code = String(anyErr.code || "").toLowerCase();
  const detailMsg =
    typeof anyErr.detail === "string"
      ? anyErr.detail
      : String(
          (anyErr.detail &&
            typeof anyErr.detail === "object" &&
            (anyErr.detail.message || anyErr.detail.error_kind)) ||
            "",
        ).toLowerCase();
  const kind =
    typeof anyErr.detail === "object" && anyErr.detail
      ? String(anyErr.detail.error_kind || "").toLowerCase()
      : "";
  if (code === "backend_unreachable" || code === "network_error" || code === "timeout") {
    return "network_failed";
  }
  if (kind === "empty" || detailMsg.includes("empty_transcript") || code === "empty") {
    return "empty_transcript";
  }
  if (detailMsg.includes("unsupported") || kind === "unsupported_media") {
    return "unsupported";
  }
  return "stt_failed";
}

export function voiceFirstFailureCopy(kind: VoiceFirstFailureKind): string {
  return VOICE_FIRST_FAILURE_COPY[kind] || VOICE_FIRST_FAILURE_COPY.stt_failed;
}

/** After leaving the voice door, guided/text/full paths own the UX. */
export function leaveVoiceFrontDoor(
  next: Exclude<VoiceFrontDoor, "voice">,
): VoiceFirstUiPatch {
  return {
    ...emptyVoiceFirstUi(next),
    showVoiceFrontDoor: false,
    voiceFirstPhase: "idle",
    voiceFirstStatus: "",
  };
}
