import { appConfig } from "../../utils/config";
import { START_CLAIM_SUCCESS_COPY } from "../../utils/startClaimLifecycle";
import {
  START_CLAIM_SAFETY_COPY,
  reLaunchStartClaimHome,
} from "../../utils/startClaimEntry";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

Page({
  data: {
    title: START_CLAIM_SUCCESS_COPY.title,
    bodyLines: START_CLAIM_SUCCESS_COPY.bodyLines,
    brokerName: appConfig.brokerDisplayName || "陈总",
    shellSafetyCopy: START_CLAIM_SAFETY_COPY,
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
    });
  },

  /** Explicit Home / Start New Claim — never leave user on a dead-end receipt. */
  onBackHome() {
    reLaunchStartClaimHome(wx);
  },
});
