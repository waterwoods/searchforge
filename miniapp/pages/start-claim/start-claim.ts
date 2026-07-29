import { appConfig, QA_API_BASE_URL } from "../../utils/config";
import {
  emitStartClaimVoiceRecordStart,
  startClaim,
  transcribeStartClaimStoryAudio,
} from "../../services/startClaimApi";
import {
  fetchSmartClaimStartPlan,
  type SmartClaimStartPlan,
} from "../../services/smartClaimStartApi";
import { resolveCustomerContext } from "../../services/sessionIdentityAdapter";
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
import { routeForCustomerNextAction } from "../../utils/customerContextRoute";
import {
  ENTRY_ROUTE,
  ONE_ACTIVE_CASE_POLICY_CONTACT,
  ONE_ACTIVE_CASE_POLICY_CONTENT,
  ONE_ACTIVE_CASE_POLICY_CONTINUE,
  ONE_ACTIVE_CASE_POLICY_TITLE,
  START_CLAIM_MISSING_HINT,
  START_CLAIM_SAFETY_COPY,
  START_CLAIM_SUCCESS_ROUTE,
  createEmptyStartClaimShell,
  redirectStartClaimIfActiveCase,
  resetStartClaimDraftState,
} from "../../utils/startClaimEntry";
import {
  buildSmartClaimUiState,
  emptySmartClaimUiState,
  resolveMockScenarioFromQuery,
  type SmartClaimUiState,
} from "../../utils/smartClaimStartPlan";
import {
  DEMO_INVITE_ACTIVE_CASE_CONTENT,
  DEMO_INVITE_ACTIVE_CASE_TITLE,
  hasDemoInviteLaunchQuery,
} from "../../utils/demoInviteLaunch";
import {
  redeemDemoInviteToken,
  resolveDemoInviteTokenFromQuery,
} from "../../services/demoInviteApi";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
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

type ContextPhase = "checking" | "ready" | "error";

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
  /** Form fields render only after Customer Context says START_NEW_CLAIM. */
  formAuthorized: boolean;
  contextPhase: ContextPhase;
  voicePhase: VoicePhase;
  voiceHint: string;
  voiceSession: VoiceSession | null;
  showRecordBtn: boolean;
  showStopBtn: boolean;
  recordBtnLabel: string;
  recordBtnDisabled: boolean;
  storyInputDisabled: boolean;
  confirmDisabled: boolean;
  /** P4 Integration 01 — Smart Claim Start presentation (legacy when flag off). */
  smartUi: SmartClaimUiState;
  smartClaimEnabled: boolean;
  formTitle: string;
  formSubtitle: string;
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
  _launchOptions: {} as Record<string, string | undefined>,
  _divertedToHome: false,
  _gateInFlight: false,
  _navigatingAway: false,
  _smartPlan: null as SmartClaimStartPlan | null,
  _confirmSelections: {} as Record<string, string>,
  /** Successful Demo Invite redeem this page lifetime — enables Smart Claim chips. */
  _demoInviteActive: false,

  data: {
    ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
    ...initialVoiceUiData(),
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: START_CLAIM_SAFETY_COPY,
    formAuthorized: false,
    contextPhase: "checking",
    pageReady: true,
    smartUi: emptySmartClaimUiState(),
    smartClaimEnabled: Boolean(appConfig.smartClaimStartEnabled),
    formTitle: "告诉陈总发生了什么",
    formSubtitle:
      "可录音转文字，也可直接打字。先说清楚事故情况即可。VIN、保险卡等证件资料，如需再补充会通知您。",
    busy: {
      submitting: false,
      uploading: false,
    },
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    this._launchOptions = options || {};
    this._divertedToHome = false;
    this._navigatingAway = false;
    this._demoInviteActive = false;
    qaPathLog("ENTRY", {
      page: "pages/start-claim/start-claim",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      hasDit: hasDemoInviteLaunchQuery(options),
      note: "first_js_page_onload_or_redirect_target",
    });
    try {
      // Capsule Home opens pages[0] (Start Claim). Operational home → Service Home.
      // Demo Invite dit= counts as intentional form entry (see startClaimEntry).
      if (redirectStartClaimIfActiveCase(wx, options || {})) {
        this._divertedToHome = true;
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
          formAuthorized: false,
          contextPhase: "checking",
          pageReady: true,
          initErrorMessage: "",
        });
        return;
      }
      return this.authorizeFormEntry({ preserveDraft: false });
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
        formAuthorized: false,
        contextPhase: "error",
        initErrorMessage: "页面初始化失败，请重试或联系陈总。",
      });
    }
  },

  onShow() {
    if (this._divertedToHome || this._navigatingAway) return;
    const intentional =
      String(this._launchOptions?.entry || "").trim() === "form" ||
      hasDemoInviteLaunchQuery(this._launchOptions);
    if (!intentional) return;
    void this.authorizeFormEntry({ preserveDraft: Boolean(this.data.formAuthorized) });
    this._ensureRecorder();
  },

  /**
   * Server Customer Context gate: form only when next_action is START_NEW_CLAIM.
   */
  async authorizeFormEntry(options: { preserveDraft: boolean }) {
    if (this._gateInFlight || this._navigatingAway || this._divertedToHome) return;
    this._gateInFlight = true;
    this.setData({
      contextPhase: "checking",
      formAuthorized: options.preserveDraft ? this.data.formAuthorized : false,
      initErrorMessage: "",
      pageReady: true,
    });
    try {
      // T4: redeem Demo Invite before context/plan — soft-fail to blank path.
      await this.redeemDemoInviteIfPresent();

      const context = await resolveCustomerContext();
      if (context.nextAction !== "START_NEW_CLAIM") {
        this._navigatingAway = true;
        if (context.resumeToken) {
          try {
            const app = getApp<IAppOption>();
            app.taskToken = context.resumeToken;
            app.task = undefined;
          } catch {
            // ignore
          }
        }
        const target = routeForCustomerNextAction(context.nextAction);
        qaPathLog("EARLY_EXIT", {
          reason: "start_claim_blocked_by_customer_context",
          why: String(context.nextAction || ""),
          page: "pages/start-claim/start-claim",
          next: target,
          demoInviteActive: Boolean(this._demoInviteActive),
        });
        this.setData({ formAuthorized: false, contextPhase: "checking" });
        wx.reLaunch({
          url: target,
          fail: () => {
            wx.redirectTo({
              url: target,
              fail: () => {
                this._navigatingAway = false;
                this.setData({
                  contextPhase: "error",
                  formAuthorized: false,
                  initErrorMessage: "您已有进行中的报案，但打开失败。请重试或联系陈总。",
                });
              },
            });
          },
        });
        return;
      }

      if (!options.preserveDraft || !this.data.formAuthorized) {
        resetStartClaimDraftState();
        this._submitState = createStartClaimSubmitState();
        this._form = createEmptyCanonicalForm();
        this._smartPlan = null;
        this._confirmSelections = {};
        const validated = validateStartClaimForm({
          ...this._form,
          reachabilityKnown: true,
        });
        this.setData({
          ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
          ...initialVoiceUiData(),
          canSubmit: validated.canSubmit,
          missingHint: validated.missingHint || START_CLAIM_MISSING_HINT,
          formAuthorized: true,
          contextPhase: "ready",
          pageReady: true,
          initErrorMessage: "",
          errorMessage: "",
          errorRetryable: false,
          smartUi: emptySmartClaimUiState(),
          smartClaimEnabled:
            Boolean(appConfig.smartClaimStartEnabled) || Boolean(this._demoInviteActive),
          formTitle: "告诉陈总发生了什么",
          formSubtitle:
            "可录音转文字，也可直接打字。先说清楚事故情况即可。VIN、保险卡等证件资料，如需再补充会通知您。",
        });
        await this.loadSmartClaimStartPlan();
      } else {
        this.setData({
          formAuthorized: true,
          contextPhase: "ready",
          pageReady: true,
          initErrorMessage: "",
        });
      }
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "form_authorized_by_customer_context",
        demoInviteActive: Boolean(this._demoInviteActive),
      });
    } catch {
      this.setData({
        formAuthorized: false,
        contextPhase: "error",
        pageReady: true,
        initErrorMessage: "暂时无法确认是否可以开始新的报案，请重试或联系陈总。",
      });
    } finally {
      this._gateInFlight = false;
    }
  },

  /**
   * T4 — redeem dit= once; soft-fail blank; Active Case switch shows friendly warning.
   */
  async redeemDemoInviteIfPresent() {
    const dit = resolveDemoInviteTokenFromQuery(this._launchOptions);
    if (!dit) {
      this._demoInviteActive = false;
      return;
    }
    const result = await redeemDemoInviteToken(dit);
    if (result.ok) {
      this._demoInviteActive = true;
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "demo_invite_redeemed",
        status: String(result.status || "ok"),
      });
      return;
    }

    this._demoInviteActive = false;
    qaPathLog("BOOTSTRAP", {
      page: "pages/start-claim/start-claim",
      phase: "demo_invite_redeem_soft_fail",
      status: String(result.status || result.error_code || "invalid"),
      fallback: String(result.fallback || "blank_claim"),
    });

    if (result.error_code === "active_case_blocks_scenario_switch") {
      try {
        wx.showModal({
          title: DEMO_INVITE_ACTIVE_CASE_TITLE,
          content: DEMO_INVITE_ACTIVE_CASE_CONTENT,
          showCancel: false,
          confirmText: "知道了",
        });
      } catch {
        // ignore
      }
    }
    // Drop dit so retries / onShow do not re-spam redeem with a dead token.
    if (this._launchOptions && this._launchOptions.dit) {
      const next = { ...this._launchOptions };
      delete next.dit;
      this._launchOptions = next;
    }
  },

  /**
   * P4 Integration 01 — Cap 01→02→03 plan. Fail-open to legacy form.
   * Demo Invite overlay enables Smart Claim even when the pilot flag is OFF.
   */
  async loadSmartClaimStartPlan() {
    const demoActive = Boolean(this._demoInviteActive);
    if (!appConfig.smartClaimStartEnabled && !demoActive) {
      this._smartPlan = null;
      this._confirmSelections = {};
      this.setData({
        smartClaimEnabled: false,
        smartUi: emptySmartClaimUiState(),
      });
      return;
    }
    try {
      // Overlay is server-authoritative after redeem; client mock_scenario is DevTools-only.
      const mockScenario = demoActive
        ? undefined
        : resolveMockScenarioFromQuery(this._launchOptions) || undefined;
      const res = await fetchSmartClaimStartPlan({
        mockScenario,
      });
      const plan = res && res.plan ? res.plan : null;
      this._smartPlan = plan;
      this._confirmSelections = {};
      const smartUi = buildSmartClaimUiState(plan, this._confirmSelections);
      const matched = smartUi.uiMode === "matched";
      this.setData({
        smartClaimEnabled: true,
        smartUi,
        formTitle: matched || smartUi.uiMode === "blank_degrade" ? "事故事实" : "告诉陈总发生了什么",
        formSubtitle: matched
          ? "只需补充今天的事故情况。照片现在可以跳过，之后也可以补交。"
          : "可录音转文字，也可直接打字。先说清楚事故情况即可。VIN、保险卡等证件资料，如需再补充会通知您。",
      });
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "smart_claim_start_plan",
        mode: smartUi.planMode || "legacy",
        identitySource: String(res?.identity_source || ""),
        demoInviteActive: demoActive,
      });
    } catch {
      // S6 / network: never dead-end — keep existing accident form.
      this._smartPlan = null;
      this._confirmSelections = {};
      this.setData({
        smartClaimEnabled: true,
        smartUi: emptySmartClaimUiState(),
        formTitle: "告诉陈总发生了什么",
        formSubtitle:
          "可录音转文字，也可直接打字。先说清楚事故情况即可。VIN、保险卡等证件资料，如需再补充会通知您。",
      });
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "smart_claim_start_degraded",
      });
    }
  },

  _applySmartUiFromSelections() {
    const smartUi = buildSmartClaimUiState(this._smartPlan, this._confirmSelections);
    this.setData({ smartUi });
  },

  onSmartConfirmSelect(e: WechatMiniprogram.CustomEvent) {
    const stepId = String((e.detail && e.detail.stepId) || "").trim();
    const option = String((e.detail && e.detail.option) || "").trim();
    if (!stepId || !option) return;
    this._confirmSelections = { ...this._confirmSelections, [stepId]: option };
    this._applySmartUiFromSelections();
  },

  onSmartPrimaryTap() {
    const mode = String(this.data.smartUi?.uiMode || "");
    if (mode === "continue_active") {
      // Mock or real One Active Case — never create a duplicate claim.
      this.interruptResumedActiveCase("");
      return;
    }
    if (mode === "contact_broker") {
      this.onContactBroker();
      return;
    }
  },

  onSmartSecondaryTap() {
    const mode = String(this.data.smartUi?.uiMode || "");
    if (mode === "continue_active") {
      this.onContactBroker();
      return;
    }
    // Matched "修改我的信息" — lightweight contact path; no identity redesign.
    this.onContactBroker();
  },

  onUnload() {
    try {
      recorderState(this).recorder?.stop();
    } catch {
      // ignore
    }
  },

  onResetAndRetry() {
    return this.authorizeFormEntry({ preserveDraft: false });
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
    if (!this.data.formAuthorized || this.data.contextPhase !== "ready") return;
    if (this.data.confirmDisabled) return;
    const smartUi = this.data.smartUi || emptySmartClaimUiState();
    // Never create a claim from continue / contact gates.
    if (smartUi.uiMode === "continue_active" || smartUi.uiMode === "contact_broker") {
      return;
    }
    if (smartUi.showConfirmSection && !smartUi.confirmsComplete) {
      this.setData({
        errorMessage: "请先确认车辆或保单信息，再填写事故事实。",
        errorRetryable: false,
      });
      return;
    }
    if (smartUi.showAccidentForm && !smartUi.canShowAccidentBlock) {
      return;
    }
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

      // P0: silent resume must never look like a successful new claim.
      if (String(result.outcome || "").trim() === "resumed") {
        endStartClaimSubmit(this._submitState, false);
        this.setData({
          busy: { submitting: false, uploading: false },
          description: this._form.description,
          accidentDatetime: this._form.accidentDatetime,
          accidentLocation: this._form.accidentLocation,
          injuryStatus: this._form.injuryStatus,
          canSubmit: true,
          errorMessage: "",
          errorRetryable: false,
        });
        this.interruptResumedActiveCase(String(result.resume_token || "").trim());
        return;
      }

      endStartClaimSubmit(this._submitState, true);
      this.setData({ busy: { submitting: false, uploading: false } });
      // Entry re-reads server Customer Context before navigating. It alone
      // persists the returned resume token cache and selects the destination.
      const resumeToken = String(result.resume_token || "").trim();
      if (resumeToken) {
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

  /**
   * Honest Active Case interrupt — never treat resume as a new-claim success.
   */
  interruptResumedActiveCase(resumeToken: string) {
    if (resumeToken) {
      try {
        const app = getApp<IAppOption>();
        app.taskToken = resumeToken;
        app.task = undefined;
      } catch {
        // ignore
      }
    }
    wx.showModal({
      title: ONE_ACTIVE_CASE_POLICY_TITLE,
      content: ONE_ACTIVE_CASE_POLICY_CONTENT,
      confirmText: ONE_ACTIVE_CASE_POLICY_CONTINUE,
      cancelText: ONE_ACTIVE_CASE_POLICY_CONTACT,
      success: (res) => {
        if (res.cancel) {
          this.onContactBroker();
          return;
        }
        this._navigatingAway = true;
        wx.reLaunch({
          url: ENTRY_ROUTE,
          fail: () => {
            wx.redirectTo({
              url: ENTRY_ROUTE,
              fail: () => {
                this._navigatingAway = false;
                this.setData({
                  errorMessage: "您已有进行中的报案。请从首页继续当前报案。",
                  errorRetryable: false,
                });
              },
            });
          },
        });
      },
      fail: () => {
        this._navigatingAway = true;
        wx.reLaunch({ url: ENTRY_ROUTE });
      },
    });
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
