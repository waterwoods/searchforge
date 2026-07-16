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
  photoComingSoon: boolean;
  brokerName: string;
  shellSafetyCopy: string;
  errorMessage: string;
  errorRetryable: boolean;
  busy: {
    submitting: boolean;
  };
};

Page({
  _submitState: createStartClaimSubmitState() as StartClaimSubmitState,

  data: {
    description: "",
    charCount: 0,
    photoComingSoon: true,
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

  onDescriptionInput(e: WechatMiniprogram.Input) {
    const description = e.detail.value || "";
    this.setData({ description, charCount: description.length });
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
  }) {
    return startClaim(command);
  },
});
