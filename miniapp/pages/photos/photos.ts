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

Page({
  data: {
    slots: [] as SlotUi[],
    uploadUrl: "",
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    uploading: false,
  },

  onShow() {
    this.bootstrap();
  },

  bootstrap() {
    const app = getApp<{
      taskToken?: string;
      task?: { upload_url?: string | null; photo_count?: number };
    }>();
    const uploadUrl = String(app.task?.upload_url || "");
    const count = photoCount(app.task as import("../../types/task").CustomerTask);
    const slots: SlotUi[] = SLOT_SEQUENCE.map((key) => ({
      key,
      label: SLOT_LABELS[key] || key,
      localPath: "",
      uploaded: false,
      uploading: false,
      error: "",
    }));
    this.setData({ uploadUrl, photoCount: count, slots });
  },

  async onAddPhoto() {
    const app = getApp<{ taskToken?: string; task?: import("../../types/task").CustomerTask }>();
    const uploadUrl = this.data.uploadUrl || String(app.task?.upload_url || "");
    if (!uploadUrl) {
      wx.showToast({ title: "照片上传入口不可用", icon: "none" });
      return;
    }

    const nextIndex = this.data.slots.findIndex((s) => !s.uploaded && !s.localPath);
    if (nextIndex < 0 && this.data.photoCount >= this.data.photoTarget) {
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
      slots[idx] = { ...slots[idx], uploaded: true, uploading: false };
      this.setData({ slots, uploading: false });

      if (app.taskToken) {
        const task = await CustomerTaskApi.getTask(app.taskToken);
        app.task = task;
        this.setData({ photoCount: photoCount(task) });
      }
      wx.showToast({ title: "上传成功", icon: "success" });
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
