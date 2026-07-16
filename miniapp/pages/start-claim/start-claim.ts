import { appConfig } from "../../utils/config";
import { startClaim } from "../../services/startClaimApi";
import { ApiRequestError } from "../../utils/request";
import {
  beginStartClaimSubmit,
  createStartClaimSubmitState,
  endStartClaimSubmit,
  mapStartClaimError,
  type StartClaimSubmitState,
} from "../../utils/startClaimLifecycle";
import {
  buildStartClaimPayload,
  validateStartClaimForm,
  type StartClaimFieldErrors,
  type StartClaimFieldKey,
} from "../../utils/startClaimValidation";
import { DEFAULT_SAFETY_COPY } from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

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
  _submitState: createStartClaimSubmitState() as StartClaimSubmitState,

  data: {
    description: "",
    charCount: 0,
    accidentDatetime: "",
    accidentLocation: "",
    injuryStatus: "",
    canSubmit: false,
    missingHint: "请先填写：事故经过、事故时间、事故地点、是否受伤",
    fieldErrors: {},
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: DEFAULT_SAFETY_COPY,
    errorMessage: "",
    errorRetryable: false,
    busy: {
      submitting: false,
    },
  } as PageData,

  onLoad() {
    this._submitState = createStartClaimSubmitState();
  },

  /** Merge patch into Page.data before computing validity (avoids setData race). */
  _applyFormPatch(patch: FormPatch, options?: { showErrors?: boolean }) {
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
    if (options?.showErrors) {
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
        url: "/pages/start-claim-success/start-claim-success",
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
