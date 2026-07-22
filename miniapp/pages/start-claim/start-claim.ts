import { appConfig, QA_API_BASE_URL } from "../../utils/config";
import { startClaim } from "../../services/startClaimApi";
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
  busy: {
    submitting: boolean;
  };
};

type FormPatch = Partial<StartClaimCanonicalForm>;

Page({
  _submitState: null as StartClaimSubmitState | null,
  /** Synchronous canonical model — source of truth for CTA / hint / submit. */
  _form: createEmptyCanonicalForm() as StartClaimCanonicalForm,

  data: {
    ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: START_CLAIM_SAFETY_COPY,
    busy: {
      submitting: false,
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
      // P26D: capsule Home opens pages[0] (Start Claim). Active case → Task Home.
      if (redirectStartClaimIfActiveCase(wx)) {
        qaPathLog("EARLY_EXIT", {
          page: "pages/start-claim/start-claim",
          reason: "active_case_redirect_entry",
          why: "resume_token_present_in_storage",
          next: ENTRY_ROUTE,
        });
        this.setData({
          ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
          pageReady: true,
          initErrorMessage: "",
        });
        return;
      }
      qaPathLog("BOOTSTRAP", {
        page: "pages/start-claim/start-claim",
        phase: "form_init_no_api",
        why: "no_token_needed_until_submit",
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
        canSubmit: validated.canSubmit,
        missingHint: validated.missingHint || START_CLAIM_MISSING_HINT,
        pageReady: true,
        initErrorMessage: "",
        errorMessage: "",
        errorRetryable: false,
      });
    } catch {
      qaPathLog("EARLY_EXIT", {
        page: "start-claim",
        reason: "onload_throw_before_any_request",
        errorCode: "init_failed",
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
        canSubmit: validated.canSubmit,
        missingHint: validated.missingHint || START_CLAIM_MISSING_HINT,
        busy: { submitting: false },
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

  async onSubmit() {
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
      busy: { submitting: true },
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
          busy: { submitting: false },
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
      this.setData({ busy: { submitting: false } });
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
        busy: { submitting: false },
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
