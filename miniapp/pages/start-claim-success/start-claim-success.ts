import { appConfig } from "../../utils/config";
import { START_CLAIM_SUCCESS_COPY } from "../../utils/startClaimLifecycle";
import { DEFAULT_SAFETY_COPY } from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

Page({
  data: {
    title: START_CLAIM_SUCCESS_COPY.title,
    bodyLines: START_CLAIM_SUCCESS_COPY.bodyLines,
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: DEFAULT_SAFETY_COPY,
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
    });
  },
});
