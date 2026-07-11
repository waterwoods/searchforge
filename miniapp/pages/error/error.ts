import { mapErrorMessage } from "../../utils/taskMapping";

Page({
  data: {
    message: "",
    code: "",
  },

  onLoad(options: Record<string, string | undefined>) {
    const code = String(options.code || "unknown");
    this.setData({
      code,
      message: mapErrorMessage(code),
    });
  },

  onRetry() {
    wx.redirectTo({ url: "/pages/entry/entry" });
  },

  onContact() {
    wx.showModal({
      title: "联系陈总",
      content: "请返回微信联系陈总。",
      showCancel: false,
    });
  },
});
