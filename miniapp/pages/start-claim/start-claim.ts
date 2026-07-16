import { appConfig } from "../../utils/config";
import { startClaim } from "../../services/startClaimApi";
import { ApiRequestError } from "../../utils/request";
import {
  beginStartClaimSubmit,
  createStartClaimSubmitState,
  endStartClaimSubmit,
  mapStartClaimError,
} from "../../utils/startClaimLifecycle";
import type { StartClaimSubmitState } from "../../utils/startClaimLifecycle";
import {
  buildStartClaimPayload,
  validateStartClaimForm,
} from "../../utils/startClaimValidation";
import type {
  StartClaimFieldErrors,
  StartClaimFieldKey,
} from "../../utils/startClaimValidation";
import { contactBrokerModalCopy } from "../../utils/taskMapping";
import {
  START_CLAIM_MISSING_HINT,
  START_CLAIM_SAFETY_COPY,
  START_CLAIM_SUCCESS_ROUTE,
  createEmptyStartClaimShell,
  resetStartClaimDraftState,
} from "../../utils/startClaimEntry";

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

type FormPatch = Partial<{
  description: string;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
}>;

Page({
  _submitState: null as StartClaimSubmitState | null,

  data: {
    ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: START_CLAIM_SAFETY_COPY,
    busy: {
      submitting: false,
    },
  } as PageData,

  onLoad() {
    try {
      // Prior submitted resume must not block a fresh Start Claim after Home.
      resetStartClaimDraftState();
      this._submitState = createStartClaimSubmitState();
      this.setData({
        ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
        pageReady: true,
        initErrorMessage: "",
      });
    } catch {
      this.setData({
        pageReady: true,
        initErrorMessage: "页面初始化失败，请重试或联系陈总。",
      });
    }
  },

  onShow() {
    // Home / reLaunch / resume must always show a usable form shell immediately.
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
  },

  onResetAndRetry() {
    try {
      resetStartClaimDraftState();
      this._submitState = createStartClaimSubmitState();
      this.setData({
        ...createEmptyStartClaimShell(START_CLAIM_MISSING_HINT),
        busy: { submitting: false },
        initErrorMessage: "",
        pageReady: true,
      });
    } catch {
      this.setData({
        pageReady: true,
        initErrorMessage: "页面初始化失败，请重试或联系陈总。",
      });
    }
  },

  /** Merge patch into Page.data before computing validity (avoids setData race). */
  _applyFormPatch(patch: FormPatch, options?: { showErrors?: boolean }) {
    const showErrors = Boolean(options && options.showErrors);
    const next = {
      description: patch.description !== undefined ? patch.description : this.data.description,
      accidentDatetime:
        patch.accidentDatetime !== undefined ? patch.accidentDatetime : this.data.accidentDatetime,
      accidentLocation:
        patch.accidentLocation !== undefined ? patch.accidentLocation : this.data.accidentLocation,
      injuryStatus: patch.injuryStatus !== undefined ? patch.injuryStatus : this.data.injuryStatus,
      // Mini Program cold-start has WeChat session reachability — contact not required.
      reachabilityKnown: true,
    };
    const validated = validateStartClaimForm(next);
    const dataPatch: Record<string, unknown> = {
      ...patch,
      canSubmit: validated.canSubmit,
      missingHint: validated.missingHint,
    };
    if (showErrors) {
      dataPatch.fieldErrors = validated.errors;
      dataPatch.errorMessage = validated.ok ? "" : validated.missingHint;
    } else if (validated.canSubmit) {
      dataPatch.fieldErrors = {};
      dataPatch.missingHint = "";
    } else {
      // Keep button disabled explainable without shouting on every keystroke.
      dataPatch.fieldErrors = this.data.fieldErrors || {};
    }
    this.setData(dataPatch);
    return validated;
  },

  onDescriptionInput(e: WechatMiniprogram.Input) {
    const description = e.detail.value || "";
    this._applyFormPatch({ description });
    this.setData({ charCount: description.length });
  },

  onDatetimeInput(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ accidentDatetime: e.detail.value || "" });
  },

  onLocationInput(e: WechatMiniprogram.Input) {
    this._applyFormPatch({ accidentLocation: e.detail.value || "" });
  },

  onInjurySelect(e: WechatMiniprogram.TouchEvent) {
    const injuryStatus = String(e.currentTarget.dataset.value || "");
    this._applyFormPatch({ injuryStatus }, { showErrors: Boolean(injuryStatus) });
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
    const validated = this._applyFormPatch({}, { showErrors: true });
    if (!validated.ok) {
      this._focusFirstInvalid(validated.firstInvalid);
      return;
    }
    await this.submitStartClaim({ reuseIdentity: false });
  },

  _focusFirstInvalid(field: StartClaimFieldKey | null) {
    if (!field) return;
    // Mini Program Input focus is best-effort; toast reinforces the visible field error.
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
    await this.submitStartClaim({ reuseIdentity: true });
  },

  async submitStartClaim(options: { reuseIdentity: boolean }) {
    const payload = buildStartClaimPayload({
      description: this.data.description,
      accidentDatetime: this.data.accidentDatetime,
      accidentLocation: this.data.accidentLocation,
      injuryStatus: this.data.injuryStatus,
      reachabilityKnown: true,
    });
    if (!payload) {
      this._applyFormPatch({}, { showErrors: true });
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
        const mapped = mapStartClaimError(result.error_code || "create_claim_failed");
        this.setData({
          errorMessage: mapped.message,
          errorRetryable: mapped.retryable,
          busy: { submitting: false },
        });
        endStartClaimSubmit(this._submitState, false);
        return;
      }
      endStartClaimSubmit(this._submitState, true);
      this.setData({ busy: { submitting: false } });
      wx.redirectTo({
        url: START_CLAIM_SUCCESS_ROUTE,
        fail: () => {
          wx.showToast({ title: "已提交", icon: "success" });
        },
      });
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "network_error";
      const mapped = mapStartClaimError(code);
      this.setData({
        errorMessage: mapped.message,
        errorRetryable: mapped.retryable,
        busy: { submitting: false },
      });
      // Keep command identity for uncertain/network retry.
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
