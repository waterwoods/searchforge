import { appConfig, QA_API_BASE_URL } from "../../utils/config";
import {
  emitStartClaimVoiceRecordStart,
  startClaim,
  transcribeStartClaimStoryAudio,
} from "../../services/startClaimApi";
import { ApiRequestError } from "../../utils/request";
import { resetApiHealthCache } from "../../utils/apiHealth";
import { buildRequestDiagnostic } from "../../utils/requestErrors";
import {
  beginStartClaimSubmit,
  createStartClaimSubmitState,
  endStartClaimSubmit,
  mapStartClaimError,
} from "../../utils/startClaimLifecycle";
import type { StartClaimSubmitState } from "../../utils/startClaimLifecycle";
import {
  buildStartClaimPayload,
  createEmptyCanonicalForm,
  mergeCanonicalForm,
  normalizeStartClaimCanonicalForm,
  validateStartClaimForm,
} from "../../utils/startClaimValidation";
import type {
  StartClaimCanonicalForm,
  StartClaimFieldErrors,
  StartClaimFieldKey,
} from "../../utils/startClaimValidation";
import { contactBrokerModalCopy } from "../../utils/taskMapping";
import {
  ENTRY_ROUTE,
  START_CLAIM_MISSING_HINT,
  START_CLAIM_SAFETY_COPY,
  START_CLAIM_SUCCESS_ROUTE,
  createEmptyStartClaimShell,
  redirectStartClaimIfActiveCase,
  resetStartClaimDraftState,
} from "../../utils/startClaimEntry";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
import { saveResumeToken } from "../../utils/storage";
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

type PageData = {
  description: string;
  charCount: number;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
  canSubmit: boolean;
  missingHint: string;
  fieldErrors: StartClaimFieldErrors;
  brokerName: string;
  shellSafetyCopy: string;
  errorMessage: string;
  errorRetryable: boolean;
  pageReady: boolean;
  initErrorMessage: string;
  voicePhase: VoicePhase;
  voiceHint: string;
  voiceSession: VoiceSession | null;
  showRecordBtn: boolean;
  showStopBtn: boolean;
  recordBtnLabel: string;
  recordBtnDisabled: boolean;
  storyInputDisabled: boolean;
  confirmDisabled: boolean;
  busy: {
    submitting: boolean;
    uploading: boolean;
  };
};

type FormPatch = Partial<StartClaimCanonicalForm>;

Page({
  _submitState: null as StartClaimSubmitState | null,
  /** Synchronous canonical model — source of truth for CTA / hint / submit. */
  _form: createEmptyCanonicalForm() as StartClaimCanonicalForm,

  data: {
    ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
    ...initialVoiceUiData(),
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: START_CLAIM_SAFETY_COPY,
    busy: {
      submitting: false,
      uploading: false,
    },
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    qaPathLog("ENTRY", {
      page: "pages/start-claim/start-claim",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      note: "first_js_page_onload_or_redirect_target",
    });
    try {
      // Capsule Home opens pages[0] (Start Claim). Operational home → Service Home.
      // Intentional form entry uses ?entry=form (empty-state Start Claim only).
      if (redirectStartClaimIfActiveCase(wx, options || {})) {
        qaPathLog("EARLY_EXIT", {
          reason: "capsule_home_redirect_service_home",
          why: "operational_home_is_service_home",
          page: "pages/start-claim/start-claim",
          launchPath: "pages/start-claim/start-claim",
          hasToken: q.hasToken,
          queryKeys: q.queryKeys,
        });
        this.setData({
          ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
          ...initialVoiceUiData(),
          pageReady: true,
          initErrorMessage: "",
        });
        return;
      }
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "form_init_no_api",
      });
      resetStartClaimDraftState();
      this._submitState = createStartClaimSubmitState();
      this._form = createEmptyCanonicalForm();
      const validated = validateStartClaimForm({
        ...this._form,
        reachabilityKnown: true,
      });
      this.setData({
        ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
        ...initialVoiceUiData(),
        canSubmit: validated.canSubmit,
        missingHint: validated.missingHint || START_CLAIM_MISSING_HINT,
        pageReady: true,
        initErrorMessage: "",
        errorMessage: "",
        errorRetryable: false,
      });
      // Path verification: Start Claim open never reaches REQUEST_SENT.
      qaPathLog("EARLY_EXIT", {
        reason: "start_claim_no_request_until_submit",
        why: "pages0_or_compile_mode_opens_form_only_no_backend_call",
        page: "pages/start-claim/start-claim",
        launchPath: "pages/start-claim/start-claim",
        hasToken: q.hasToken,
        queryKeys: q.queryKeys,
      });
    } catch {
      qaPathLog("EARLY_EXIT", {
        reason: "onload_throw_before_any_request",
        why: "bootstrap_exception",
        page: "pages/start-claim/start-claim",
        launchPath: "pages/start-claim/start-claim",
        hasToken: false,
        queryKeys: "(none)",
      });
      this.setData({
        pageReady: true,
        initErrorMessage: "页面初始化失败，请重试或联系陈总。",
      });
    }
  },

  onShow() {
    if (!this.data.pageReady) {
      this.setData({ pageReady: true });
    }
    if (!this._submitState) {
      try {
        this._submitState = createStartClaimSubmitState();
      } catch {
        this.setData({
          initErrorMessage: "页面初始化失败，请重试或联系陈总。",
        });
      }
    }
    if (!this._form) {
      this._form = createEmptyCanonicalForm();
    }
    this._ensureRecorder();
  },

  onUnload() {
    try {
      recorderState(this).recorder?.stop();
    } catch {
      // ignore
    }
  },

  onResetAndRetry() {
    try {
      resetStartClaimDraftState();
      this._submitState = createStartClaimSubmitState();
      this._form = createEmptyCanonicalForm();
      const validated = validateStartClaimForm({
        ...this._form,
        reachabilityKnown: true,
      });
      this.setData({
        ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
        ...initialVoiceUiData(),
        canSubmit: validated.canSubmit,
        missingHint: validated.missingHint || START_CLAIM_MISSING_HINT,
        busy: { submitting: false, uploading: false },
        initErrorMessage: "",
        pageReady: true,
        errorMessage: "",
        errorRetryable: false,
      });
    } catch {
      this.setData({
        pageReady: true,
        initErrorMessage: "页面初始化失败，请重试或联系陈总。",
      });
    }
  },

  /**
   * One canonical merge + one validator for CTA, missing hint, and submit.
   * Reads/writes `_form` synchronously so setData races cannot wipe siblings.
   */
  _applyFormPatch(patch: FormPatch, options?: { showErrors?: boolean }) {
    const showErrors = Boolean(options && options.showErrors);
    this._form = mergeCanonicalForm(this._form || createEmptyCanonicalForm(), patch);
    const validated = validateStartClaimForm({
      ...this._form,
      reachabilityKnown: true,
    });
    const dataPatch: Record<string, unknown> = {
      description: this._form.description,
      accidentDatetime: this._form.accidentDatetime,
      accidentLocation: this._form.accidentLocation,
      injuryStatus: this._form.injuryStatus,
      charCount: this._form.description.length,
      canSubmit: validated.canSubmit,
      missingHint: validated.missingHint,
    };
    if (showErrors) {
      dataPatch.fieldErrors = validated.errors;
      // Validation messages use missingHint / fieldErrors — never sticky errorMessage.
      dataPatch.errorMessage = "";
      dataPatch.errorRetryable = false;
    } else if (validated.canSubmit) {
      dataPatch.fieldErrors = {};
      dataPatch.missingHint = "";
      dataPatch.errorMessage = "";
      dataPatch.errorRetryable = false;
    } else {
      dataPatch.fieldErrors = this.data.fieldErrors || {};
      // Clear stale submit/validation banners once the user edits again.
      if (this.data.errorMessage && !this.data.errorRetryable) {
        dataPatch.errorMessage = "";
      }
    }
    this.setData(dataPatch);
    return validated;
  },

  onDescriptionInput(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ description: e.detail.value || "" });
  },

  onDatetimeInput(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ accidentDatetime: e.detail.value || "" });
  },

  onLocationInput(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ accidentLocation: e.detail.value || "" });
  },

  onDescriptionBlur(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ description: (e.detail && e.detail.value) || this._form.description });
  },

  onDatetimeBlur(e: WechatMiniprogram.Input) {
    this._applyFormPatch({
      accidentDatetime: (e.detail && e.detail.value) || this._form.accidentDatetime,
    });
  },

  onLocationBlur(e: WechatMiniprogram.Input) {
    this._applyFormPatch({
      accidentLocation: (e.detail && e.detail.value) || this._form.accidentLocation,
    });
  },

  onInjurySelect(e: WechatMiniprogram.TouchEvent) {
    const injuryStatus = String(e.currentTarget.dataset.value || "");
    // Injury must not shout sibling missing fields into sticky errorMessage.
    this._applyFormPatch({ injuryStatus });
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
    });
  },

  onTapRecord() {
    if (this.data.busy.submitting || this.data.voicePhase === "transcribing") return;

    const recorder = this._ensureRecorder();
    if (!recorder) {
      this._setVoicePhase("stt_failed", "当前环境无法录音，请直接打字填写。");
      return;
    }

    wx.authorize({
      scope: "scope.record",
      success: () => {
        this._startRecording(recorder);
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

  _startRecording(recorder: WechatMiniprogram.RecorderManager) {
    void emitStartClaimVoiceRecordStart();
    console.info("[p28_voice_metric]", { event: "voice_record_start", surface: "start_claim" });
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
    const tempFilePath = String(res?.tempFilePath || "");
    const state = recorderState(this);
    const durationMs = Math.max(
      0,
      Number(res?.duration || 0) || (state.startedAt ? Date.now() - state.startedAt : 0),
    );
    if (!tempFilePath) {
      this._setVoicePhase("stt_failed", "录音文件无效，请直接打字填写。");
      return;
    }

    const extMatch = tempFilePath.match(/\.([a-zA-Z0-9]+)(?:\?|$)/);
    const fileExt = extMatch ? extMatch[1].toLowerCase() : "";
    logVoiceUploadDiagnostic({
      event: "record_stop",
      surface: "start_claim",
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
      const draft = await transcribeStartClaimStoryAudio(tempFilePath, {
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
        surface: "start_claim",
        path_ext: fileExt || "unknown",
        duration_ms: durationMs,
        transcript_chars: text.length,
        stt_latency_ms: Number(draft.stt_latency_ms || 0),
        speech_provider: draft.speech_provider || "google_chirp",
      });
      this._applyFormPatch({ description: text });
      this.setData({
        voiceHint: "已生成草稿，可修改后点提交。",
        voiceSession: {
          rawTranscript: text,
          speechProvider: draft.speech_provider || "google_chirp",
          sttLatencyMs: Number(draft.stt_latency_ms || 0),
          recordingDurationMs: durationMs,
        },
        busy: { ...this.data.busy, uploading: false },
        ...voiceUiPatch("draft", { submitting: this.data.busy.submitting }),
      });
    } catch (err) {
      const apiErr = err instanceof ApiRequestError ? err : null;
      logVoiceUploadDiagnostic({
        event: "transcribe_fail",
        surface: "start_claim",
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

  async onSubmit() {
    if (this.data.confirmDisabled) return;
    // Final flush from canonical `_form` (already updated by input/blur).
    const validated = this._applyFormPatch({}, { showErrors: true });
    if (!validated.ok) {
      this.setData({
        errorMessage: validated.missingHint,
        errorRetryable: false,
      });
      this._focusFirstInvalid(validated.firstInvalid);
      return;
    }
    await this.submitStartClaim({ reuseIdentity: false });
  },

  _focusFirstInvalid(field: StartClaimFieldKey | null) {
    if (!field) return;
    const anchors: Record<StartClaimFieldKey, string> = {
      description: "#start-claim-description",
      accidentDatetime: "#start-claim-datetime",
      accidentLocation: "#start-claim-location",
      injuryStatus: "#start-claim-injury",
      contact: "#start-claim-contact",
    };
    if (typeof wx.pageScrollTo === "function") {
      wx.pageScrollTo({
        selector: anchors[field],
        duration: 200,
      });
    }
    const messages: Record<StartClaimFieldKey, string> = {
      description: "请填写事故经过",
      accidentDatetime: "请填写事故时间",
      accidentLocation: "请填写事故地点",
      injuryStatus: "请选择是否有人受伤",
      contact: "请留下联系方式",
    };
    wx.showToast({ title: messages[field], icon: "none", duration: 2200 });
  },

  async onRetry() {
    if (!this.data.errorRetryable || this.data.busy.submitting) return;
    resetApiHealthCache();
    await this.submitStartClaim({ reuseIdentity: true });
  },

  async submitStartClaim(options: { reuseIdentity: boolean }) {
    // Render the same normalized values that will be sent.
    this._applyFormPatch(normalizeStartClaimCanonicalForm(this._form));
    const payload = buildStartClaimPayload({
      ...this._form,
      reachabilityKnown: true,
    });
    if (!payload) {
      const validated = this._applyFormPatch({}, { showErrors: true });
      this.setData({
        errorMessage: validated.missingHint,
        errorRetryable: false,
      });
      return;
    }

    if (!this._submitState) {
      this._submitState = createStartClaimSubmitState();
    }

    const gate = beginStartClaimSubmit(this._submitState, {
      reuseIdentity: options.reuseIdentity,
    });
    if (!gate.started) return;

    this.setData({
      busy: { submitting: true, uploading: this.data.busy.uploading },
      errorMessage: "",
      errorRetryable: false,
      fieldErrors: {},
      missingHint: "",
      initErrorMessage: "",
    });

    const startedAt = Date.now();
    try {
      const result = await this.callStartClaim({
        command_id: gate.command_id,
        idempotency_key: gate.idempotency_key,
        accident_description: payload.accident_description,
        accident_datetime: payload.accident_datetime,
        accident_location: payload.accident_location,
        injury_status: payload.injury_status,
      });
      if (!result.ok) {
        const errorCode = result.error_code || "create_claim_failed";
        const mapped = mapStartClaimError(errorCode);
        if (appConfig.prototypeMode) {
          console.info(
            "[start-claim] submit diagnostic",
            buildRequestDiagnostic({
              method: "POST",
              path: "/api/h5/customer/start-claim",
              apiHost: String(appConfig.apiBaseUrl || QA_API_BASE_URL),
              startedAt,
              endedAt: Date.now(),
              httpStatus: 200,
              errorCode,
              commandId: gate.command_id,
              idempotencyKey: gate.idempotency_key,
            }),
          );
        }
        this.setData({
          errorMessage: mapped.message,
          errorRetryable: mapped.retryable,
          busy: { submitting: false, uploading: false },
          // Keep completed form values — timeout/transport must not erase input.
          description: this._form.description,
          accidentDatetime: this._form.accidentDatetime,
          accidentLocation: this._form.accidentLocation,
          injuryStatus: this._form.injuryStatus,
          canSubmit: true,
        });
        endStartClaimSubmit(this._submitState, false);
        return;
      }
      endStartClaimSubmit(this._submitState, true);
      this.setData({ busy: { submitting: false, uploading: false } });
      // P26G: persist resume token and open Task Home — no broker QR required.
      const resumeToken = String(result.resume_token || "").trim();
      if (resumeToken) {
        saveResumeToken(resumeToken);
        try {
          const app = getApp<IAppOption>();
          if (app) app.taskToken = resumeToken;
        } catch {
          // Entry bootstrap rehydrates from resume storage.
        }
        wx.reLaunch({
          url: ENTRY_ROUTE,
          fail: () => {
            wx.redirectTo({
              url: ENTRY_ROUTE,
              fail: () => {
                this.setData({
                  errorMessage: "已创建案件，但打开我的资料失败。请从首页继续。",
                  errorRetryable: false,
                });
              },
            });
          },
        });
        return;
      }
      wx.redirectTo({
        url: START_CLAIM_SUCCESS_ROUTE,
        fail: () => {
          this.setData({
            errorMessage: "已提交成功，但结果页打开失败。请返回后查看，或联系陈总确认。",
            errorRetryable: false,
          });
          wx.showToast({ title: "已提交", icon: "success" });
        },
      });
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "network_error";
      const detail =
        err instanceof ApiRequestError && err.detail && typeof err.detail === "object"
          ? (err.detail as { errMsg?: string; errno?: string })
          : {};
      const mapped = mapStartClaimError(code);
      if (appConfig.prototypeMode) {
        const diag = buildRequestDiagnostic({
          method: "POST",
          path: "/api/h5/customer/start-claim",
          apiHost: String(appConfig.apiBaseUrl || QA_API_BASE_URL),
          startedAt,
          endedAt: Date.now(),
          httpStatus: err instanceof ApiRequestError ? err.status : 0,
          errorCode: code,
          errMsg: detail.errMsg || "",
          errno: detail.errno || "",
          commandId: gate.command_id,
          idempotencyKey: gate.idempotency_key,
        });
        console.info("[start-claim] submit diagnostic", diag);
      }
      this.setData({
        errorMessage: mapped.message,
        errorRetryable: mapped.retryable,
        busy: { submitting: false, uploading: false },
        description: this._form.description,
        accidentDatetime: this._form.accidentDatetime,
        accidentLocation: this._form.accidentLocation,
        injuryStatus: this._form.injuryStatus,
        charCount: this._form.description.length,
        canSubmit: true,
        missingHint: "",
      });
      // Keep command identity for uncertain/network retry (idempotent replay).
      endStartClaimSubmit(this._submitState, false);
    }
  },

  callStartClaim(command: {
    command_id: string;
    idempotency_key: string;
    accident_description?: string;
    accident_datetime?: string;
    accident_location?: string;
    injury_status?: string;
  }) {
    return startClaim(command);
  },
});
