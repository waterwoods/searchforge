import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import type { CustomerTask } from "../../types/task";
import { ApiRequestError } from "../../utils/request";
import {
  resolveTaskViewModel,
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy } from "../../utils/taskMapping";
import {
  VOICE_MAX_RECORD_MS,
  initialVoiceUiData,
  logVoiceUploadDiagnostic,
  sttFailureCopy,
  voiceUiPatch,
  type VoicePhase,
  type VoiceSession,
} from "../../utils/voiceStoryInput";

type RecorderState = {
  recorder: WechatMiniprogram.RecorderManager | null;
  bound: boolean;
  startedAt: number;
};

function recorderState(page: WechatMiniprogram.Page.Instance): RecorderState {
  const target = page as WechatMiniprogram.Page.Instance & { __voiceRecorder?: RecorderState };
  if (!target.__voiceRecorder) {
    target.__voiceRecorder = { recorder: null, bound: false, startedAt: 0 };
  }
  return target.__voiceRecorder;
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载事故经过…",
    cardSubtitle: "可录音转文字，也可直接打字。确认后经纪人才会看到。",
    story: "",
    charCount: 0,
    localDirty: false,
    minLength: 10,
    ...initialVoiceUiData(),
    task: null as CustomerTask | null,
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: true,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    retryMeta: {
      attempts: 0,
      cooldownUntil: 0,
    },
  },

  async onShow() {
    const token = this.requireToken();
    if (!token) return;
    this._ensureRecorder();
    await this.loadTask({ silent: false });
    if (this.data.localDirty) return;
    const existing = String(this.data.task?.key_facts?.accident_description || "");
    this.setData({
      story: existing,
      charCount: existing.length,
      cardSubtitle: "可录音转文字，也可直接打字。确认后经纪人才会看到。",
      ...voiceUiPatch((this.data.voicePhase as VoicePhase) || "idle", this.data.busy),
    });
  },

  onUnload() {
    try {
      recorderState(this).recorder?.stop();
    } catch {
      // ignore
    }
  },

  onInput(e: WechatMiniprogram.Input) {
    const story = e.detail.value || "";
    this.setData({ story, charCount: story.length, localDirty: true });
  },

  onRetry() {
    void this.retryLoadTask();
  },

  onTapRecord() {
    if (this.data.busy.saving || this.data.voicePhase === "transcribing") return;
    const token = this.requireToken();
    if (!token) return;

    const recorder = this._ensureRecorder();
    if (!recorder) {
      this._setVoicePhase("stt_failed", "当前环境无法录音，请直接打字填写。");
      return;
    }

    wx.authorize({
      scope: "scope.record",
      success: () => {
        this._startRecording(token, recorder);
      },
      fail: () => {
        wx.showModal({
          title: "需要麦克风权限",
          content: "请允许录音后重试，或直接打字填写事故经过。",
          showCancel: false,
          confirmText: "知道了",
        });
        this._setVoicePhase("stt_failed", "未获得麦克风权限，请直接打字填写。");
      },
    });
  },

  onTapStop() {
    if (this.data.voicePhase !== "recording") return;
    try {
      recorderState(this).recorder?.stop();
    } catch {
      this._setVoicePhase("stt_failed", "停止录音失败，请直接打字填写。");
    }
  },

  async onSave() {
    if (this.data.confirmDisabled) return;
    const story = (this.data.story || "").trim();
    if (story.length < this.data.minLength) {
      wx.showToast({ title: `请至少填写${this.data.minLength}个字`, icon: "none" });
      return;
    }

    const token = this.requireToken();
    if (!token) return;

    const session = this.data.voiceSession as VoiceSession | null;
    const voiceAudit =
      session && session.rawTranscript
        ? {
            raw_transcript: session.rawTranscript,
            confirmed_story: story,
            speech_provider: session.speechProvider || "google_chirp",
            stt_latency_ms: session.sttLatencyMs,
            recording_duration_ms: session.recordingDurationMs,
          }
        : null;

    await this.saveAndReturn(async () => {
      await CustomerTaskApi.saveStory(token, story, voiceAudit);
      const readBack = await CustomerTaskApi.getTask(token);
      const app = getApp<IAppOption>();
      app.task = readBack;
      this.commitTaskViewModel(
        resolveTaskViewModel(
          readBack,
          readBack.task_contract,
          {
            route: (this as { route?: string }).route,
            busy: { ...this.data.busy, saving: true },
          },
          null,
        ),
      );
      this.setData({
        task: readBack,
        errorState: EMPTY_TASK_ERROR,
        story,
        charCount: story.length,
        localDirty: false,
        voiceHint: "",
        voiceSession: null,
        ...voiceUiPatch("idle", this.data.busy),
      });
      wx.showToast({ title: "已确认", icon: "success" });
    });
  },

  onLater() {
    wx.navigateBack();
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
      confirmText: "知道了",
    });
  },

  _setVoicePhase(phase: VoicePhase, hint: string, extra?: Record<string, unknown>) {
    this.setData({
      voiceHint: hint,
      ...voiceUiPatch(phase, this.data.busy),
      ...(extra || {}),
    });
  },

  _ensureRecorder(): WechatMiniprogram.RecorderManager | null {
    if (typeof wx === "undefined" || typeof wx.getRecorderManager !== "function") {
      return null;
    }
    const state = recorderState(this);
    if (!state.recorder) {
      state.recorder = wx.getRecorderManager();
    }
    if (!state.bound && state.recorder) {
      const recorder = state.recorder;
      recorder.onStart(() => {
        state.startedAt = Date.now();
        this._setVoicePhase("recording", "正在录音…说完后点停止");
      });
      recorder.onStop((res) => {
        void this._onRecordStop(res);
      });
      recorder.onError(() => {
        this._setVoicePhase("stt_failed", "录音失败，请直接打字填写。", {
          busy: { ...this.data.busy, uploading: false },
        });
      });
      state.bound = true;
    }
    return state.recorder;
  },

  _startRecording(token: string, recorder: WechatMiniprogram.RecorderManager) {
    void CustomerTaskApi.emitVoiceRecordStart(token);
    console.info("[p28_voice_metric]", { event: "voice_record_start" });
    this.setData({
      voiceHint: "正在录音…",
      voiceSession: null,
      ...voiceUiPatch("recording", this.data.busy),
    });
    try {
      recorder.start({
        duration: VOICE_MAX_RECORD_MS,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: "mp3",
      });
    } catch {
      this._setVoicePhase("stt_failed", "无法开始录音，请直接打字填写。");
    }
  },

  async _onRecordStop(res: WechatMiniprogram.OnStopCallbackResult) {
    const token = this.requireToken();
    const tempFilePath = String(res?.tempFilePath || "");
    const state = recorderState(this);
    const durationMs = Math.max(
      0,
      Number(res?.duration || 0) || (state.startedAt ? Date.now() - state.startedAt : 0),
    );
    if (!token || !tempFilePath) {
      this._setVoicePhase("stt_failed", "录音文件无效，请直接打字填写。");
      return;
    }

    const extMatch = tempFilePath.match(/\.([a-zA-Z0-9]+)(?:\?|$)/);
    const fileExt = extMatch ? extMatch[1].toLowerCase() : "";
    logVoiceUploadDiagnostic({
      event: "record_stop",
      has_temp_path: Boolean(tempFilePath),
      path_ext: fileExt || "unknown",
      duration_ms: durationMs,
      file_size_bytes: Number(res?.fileSize || 0) || null,
    });

    this.setData({
      voiceHint: "正在识别语音…",
      busy: { ...this.data.busy, uploading: true },
      ...voiceUiPatch("transcribing", this.data.busy),
    });

    try {
      const draft = await CustomerTaskApi.transcribeStoryAudio(token, tempFilePath, {
        recordingDurationMs: durationMs,
      });
      const text = String(draft.raw_transcript || "").trim();
      if (!text) {
        this._setVoicePhase("stt_failed", "没有识别出文字，请重录或直接打字填写。", {
          busy: { ...this.data.busy, uploading: false },
        });
        return;
      }
      logVoiceUploadDiagnostic({
        event: "transcribe_ok",
        path_ext: fileExt || "unknown",
        duration_ms: durationMs,
        transcript_chars: text.length,
        stt_latency_ms: Number(draft.stt_latency_ms || 0),
        speech_provider: draft.speech_provider || "google_chirp",
      });
      this.setData({
        story: text,
        charCount: text.length,
        localDirty: true,
        voiceHint: "已生成草稿，可修改后点确认。",
        voiceSession: {
          rawTranscript: text,
          speechProvider: draft.speech_provider || "google_chirp",
          sttLatencyMs: Number(draft.stt_latency_ms || 0),
          recordingDurationMs: durationMs,
        },
        busy: { ...this.data.busy, uploading: false },
        ...voiceUiPatch("draft", { saving: this.data.busy.saving }),
      });
    } catch (err) {
      const apiErr = err instanceof ApiRequestError ? err : null;
      logVoiceUploadDiagnostic({
        event: "transcribe_fail",
        path_ext: fileExt || "unknown",
        duration_ms: durationMs,
        http_status: apiErr?.status || 0,
        error_code: apiErr?.code || "unknown",
      });
      this._setVoicePhase("stt_failed", sttFailureCopy(err), {
        busy: { ...this.data.busy, uploading: false },
      });
    }
  },
});
