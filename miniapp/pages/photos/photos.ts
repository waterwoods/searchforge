import { CustomerTaskApi } from "../../services/taskApi";
import { choosePhoto } from "../../services/mediaCaptureAdapter";
import { mapErrorMessage, photoCount, prototypePhotoTarget } from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";

const SLOT_SEQUENCE = ["customer_damage_photo", "other_party_vehicle_photo"] as const;
const SLOT_LABELS: Record<string, string> = {
  customer_damage_photo: "车辆受损位置",
  other_party_vehicle_photo: "对方车辆 / 现场",
};

type SlotUi = {
  key: string;
  label: string;
  localPath: string;
  uploaded: boolean;
  uploading: boolean;
  error: string;
};

function slotsFromPhotoCount(count: number): SlotUi[] {
  return SLOT_SEQUENCE.map((key, index) => ({
    key,
    label: SLOT_LABELS[key] || key,
    localPath: "",
    uploaded: count > index,
    uploading: false,
    error: "",
  }));
}

Page({
  data: {
    slots: [] as SlotUi[],
    uploadUrl: "",
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    uploading: false,
    loading: true,
  },

  onShow() {
    this.refreshFromServer();
  },

  async refreshFromServer() {
    const app = getApp<IAppOption>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setData({ loading: true });
    try {
      const task = await CustomerTaskApi.getTask(token);
      app.task = task;
      const count = photoCount(task);
      const uploadUrl = String(task.upload_url || "");
      this.setData({
        uploadUrl,
        photoCount: count,
        slots: slotsFromPhotoCount(count),
        loading: false,
      });
    } catch {
      this.setData({ loading: false });
      wx.showToast({ title: "无法刷新照片状态", icon: "none" });
    }
  },

  async onAddPhoto() {
    const app = getApp<IAppOption>();
    const uploadUrl = this.data.uploadUrl || String(app.task?.upload_url || "");
    if (!uploadUrl) {
      wx.showToast({ title: "照片上传入口不可用", icon: "none" });
      return;
    }

    if (this.data.photoCount >= this.data.photoTarget) {
      wx.navigateBack();
      return;
    }

    try {
      const picked = await choosePhoto();
      const slots = [...this.data.slots];
      const idx = slots.findIndex((s) => !s.uploaded);
      if (idx < 0) return;
      slots[idx] = { ...slots[idx], localPath: picked.tempFilePath, uploading: true, error: "" };
      this.setData({ slots, uploading: true });

      let slotKey = slots[idx].key;
      try {
        const info = await CustomerTaskApi.getUploadTaskInfo(uploadUrl);
        if (info.current_step) {
          slotKey = info.current_step;
        }
      } catch {
        // use default slot sequence
      }

      await CustomerTaskApi.uploadPhoto(uploadUrl, picked.tempFilePath, slotKey);
      wx.showToast({ title: "上传成功", icon: "success" });
      await this.refreshFromServer();
    } catch (err) {
      const msg =
        err instanceof Error && err.message === "cancelled"
          ? ""
          : mapErrorMessage(err instanceof ApiRequestError ? err.code : "network_error");
      if (msg) wx.showToast({ title: msg, icon: "none" });
      const slots = [...this.data.slots];
      const idx = slots.findIndex((s) => s.uploading);
      if (idx >= 0) {
        slots[idx] = { ...slots[idx], uploading: false, error: msg || "上传失败" };
      }
      this.setData({ slots, uploading: false });
    }
  },

  onContinue() {
    if (this.data.photoCount < 1) {
      wx.showToast({ title: "请至少添加一张照片", icon: "none" });
      return;
    }
    wx.navigateBack();
  },

  onRetrySlot(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index);
    const slots = [...this.data.slots];
    if (slots[index]) {
      slots[index] = { ...slots[index], localPath: "", uploaded: false, error: "" };
      this.setData({ slots });
    }
    this.onAddPhoto();
  },
});
