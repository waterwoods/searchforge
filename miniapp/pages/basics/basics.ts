import { CustomerTaskApi } from "../../services/taskApi";
import { mapErrorMessage } from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";

Page({
  data: {
    anyoneInjured: "",
    accidentDatetime: "",
    accidentLocation: "",
    ownVehicleInfo: "",
    saving: false,
    injuryOptions: [
      { value: "no", label: "没有人受伤" },
      { value: "yes", label: "有人受伤" },
      { value: "unknown", label: "不确定" },
    ],
  },

  onShow() {
    const app = getApp<{ task?: { key_facts?: Record<string, string | null> } }>();
    const facts = app.task?.key_facts || {};
    this.setData({
      anyoneInjured: String(facts.anyone_injured || facts.injury_status || ""),
      accidentDatetime: String(facts.accident_datetime || ""),
      accidentLocation: String(facts.accident_location || ""),
      ownVehicleInfo: String(facts.own_vehicle_info || ""),
    });
  },

  onInjurySelect(e: WechatMiniprogram.TouchEvent) {
    this.setData({ anyoneInjured: String(e.currentTarget.dataset.value || "") });
  },

  onDatetimeInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentDatetime: e.detail.value || "" });
  },

  onLocationInput(e: WechatMiniprogram.Input) {
    this.setData({ accidentLocation: e.detail.value || "" });
  },

  onVehicleInput(e: WechatMiniprogram.Input) {
    this.setData({ ownVehicleInfo: e.detail.value || "" });
  },

  async onSave() {
    const { anyoneInjured, accidentDatetime, accidentLocation, ownVehicleInfo } = this.data;
    if (!anyoneInjured) {
      wx.showToast({ title: "请选择受伤情况", icon: "none" });
      return;
    }
    if (!accidentDatetime.trim() || !accidentLocation.trim()) {
      wx.showToast({ title: "请填写事故时间和地点", icon: "none" });
      return;
    }
    if (ownVehicleInfo.trim().length < 2) {
      wx.showToast({ title: "请填写您的车辆信息", icon: "none" });
      return;
    }

    const app = getApp<{ taskToken?: string; task?: unknown }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setData({ saving: true });
    try {
      let task = await CustomerTaskApi.saveBasics(token, { anyone_injured: anyoneInjured }, "injury");
      app.task = task;
      task = await CustomerTaskApi.saveBasics(
        token,
        {
          accident_datetime: accidentDatetime.trim(),
          accident_location: accidentLocation.trim(),
        },
        "time_location",
      );
      app.task = task;
      task = await CustomerTaskApi.saveBasics(
        token,
        { own_vehicle_info: ownVehicleInfo.trim() },
        "vehicle_other_party",
      );
      app.task = task;
      wx.showToast({ title: "已保存", icon: "success" });
      setTimeout(() => wx.navigateBack(), 400);
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "save_failed";
      wx.showToast({ title: mapErrorMessage(code), icon: "none" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onLater() {
    wx.navigateBack();
  },
});
