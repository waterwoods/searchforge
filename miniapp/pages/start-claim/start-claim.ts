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
import { DEFAULT_SAFETY_COPY } from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

type PageData = {
  description: string;
  charCount: number;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
  canSubmit: boolean;
  brokerName: string;
  shellSafetyCopy: string;
  errorMessage: string;
  errorRetryable: boolean;
  busy: {
    submitting: boolean;
  };
};

function computeCanSubmit(data: {
  description: string;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
}): boolean {
  return (
    String(data.description || "").trim().length >= 10
    && String(data.accidentDatetime || "").trim().length >= 2
    && String(data.accidentLocation || "").trim().length >= 3
    && ["yes", "no", "unknown"].includes(String(data.injuryStatus || "").trim())
  );
}

Page({
  _submitState: createStartClaimSubmitState() as StartClaimSubmitState,

  data: {
    description: "",
    charCount: 0,
    accidentDatetime: "",
    accidentLocation: "",
    injuryStatus: "",
    canSubmit: false,
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

  _refreshCanSubmit() {
    this.setData({ canSubmit: computeCanSubmit(this.data) });
  },

  onDescriptionInput(e: WechatMiniprogram.Input) {
    const description = e.detail.value || "";
    this.setData({ description, charCount: description.length });
    this._refreshCanSubmit();
  },

  onDatetimeInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentDatetime: e.detail.value || "" });
    this._refreshCanSubmit();
  },

  onLocationInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentLocation: e.detail.value || "" });
    this._refreshCanSubmit();
  },

  onInjurySelect(e: WechatMiniprogram.TouchEvent) {
    const injuryStatus = String(e.currentTarget.dataset.value || "");
    this.setData({ injuryStatus });
    this._refreshCanSubmit();
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
    if (!computeCanSubmit(this.data)) {
      this.setData({
        errorMessage: "请先填写事故经过、时间、地点，并确认是否有人受伤。",
        errorRetryable: false,
      });
      return;
    }
    await this.submitStartClaim({ reuseIdentity: false });
  },

  async onRetry() {
    if (!this.data.errorRetryable || this.data.busy.submitting) return;
    await this.submitStartClaim({ reuseIdentity: true });
  },

  async submitStartClaim(options: { reuseIdentity: boolean }) {
    const gate = beginStartClaimSubmit(this._submitState, {
      reuseIdentity: options.reuseIdentity,
    });
    if (!gate.started) return;

    this.setData({
      busy: { submitting: true },
      errorMessage: "",
      errorRetryable: false,
    });

    try {
      const result = await this.callStartClaim({
        command_id: gate.command_id,
        idempotency_key: gate.idempotency_key,
        accident_description: this.data.description,
        accident_datetime: this.data.accidentDatetime,
        accident_location: this.data.accidentLocation,
        injury_status: this.data.injuryStatus,
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
