import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import { choosePhoto, previewImage } from "../../services/mediaCaptureAdapter";
import type { CustomerTask } from "../../types/task";
import { ApiRequestError } from "../../utils/request";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import {
  contactBrokerModalCopy,
  mapErrorMessage,
  photoCount,
  prototypePhotoTarget,
} from "../../utils/taskMapping";

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
  progress: number;
  error: string;
  canRetry: boolean;
  canRemove: boolean;
  requiredHint: string;
  statusText: string;
};

type PageData = {
  loadingMessage: string;
  photoCount: number;
  photoTarget: number;
  uploadUrl: string;
  slots: SlotUi[];
  task: CustomerTask | null;
  errorState: typeof EMPTY_TASK_ERROR;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  retryMeta: {
    attempts: number;
    cooldownUntil: number;
  };
};

function isPhotoSlot(slot: string): boolean {
  const value = String(slot || "").trim().toLowerCase();
  return value.includes("photo") || value.includes("image");
}

function fallbackSlots(count: number, previous?: SlotUi[]): SlotUi[] {
  return SLOT_SEQUENCE.map((key, index) => {
    const prev = previous?.find((slot) => slot.key === key);
    const uploaded = count > index;
    return {
      key,
      label: SLOT_LABELS[key] || key,
      localPath: uploaded ? "" : prev?.localPath || "",
      uploaded,
      uploading: uploaded ? false : Boolean(prev?.uploading),
      progress: uploaded ? 100 : Math.max(Number(prev?.progress || 0), 0),
      error: uploaded ? "" : prev?.error || "",
      canRetry: !uploaded && Boolean(prev?.error),
      canRemove: !uploaded && Boolean(prev?.localPath || prev?.error),
      requiredHint: uploaded ? "已确认" : "请上传该照片",
      statusText: uploaded ? "已上传并确认" : "待上传",
    };
  });
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载照片资料…",
    slots: [] as SlotUi[],
    uploadUrl: "",
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    task: null as CustomerTask | null,
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: true,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    retryMeta: {
      attempts: 0,
      cooldownUntil: 0,
    },
  } as PageData,

  async onShow() {
    const token = this.requireToken();
    if (!token) return;
    const task = await this.loadTask();
    if (task) {
      this.applyTaskToPhotoState(task);
    }
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) {
        this.applyTaskToPhotoState(task);
      }
    });
  },

  applyTaskToPhotoState(task: CustomerTask) {
    const count = photoCount(task);
    const uploadUrl = String(task.upload_url || "");
    const previous = this.data.slots;
    const requirements = (task.task_contract?.evidence_requirements || []).filter((item) =>
      isPhotoSlot(item.slot),
    );
    const slots =
      requirements.length > 0
        ? requirements.map((item) => {
            const required = Math.max(Number(item.min) || 1, 1);
            const received = Math.max(Number(item.received) || 0, 0);
            const uploaded = received >= required;
            const prev = previous.find((slot) => slot.key === item.slot);
            const remaining = Math.max(required - received, 0);
            return {
              key: item.slot,
              label: item.label || SLOT_LABELS[item.slot] || item.slot || "事故照片",
              localPath: uploaded ? "" : prev?.localPath || "",
              uploaded,
              uploading: uploaded ? false : Boolean(prev?.uploading),
              progress: uploaded ? 100 : Math.max(Number(prev?.progress || 0), 0),
              error: uploaded ? "" : prev?.error || "",
              canRetry: !uploaded && Boolean(prev?.error),
              canRemove: !uploaded && Boolean(prev?.localPath || prev?.error),
              requiredHint: uploaded ? "已满足要求" : `还需 ${remaining || 1} 张`,
              statusText: uploaded ? "已上传并确认" : `已上传 ${received}/${required}`,
            } satisfies SlotUi;
          })
        : fallbackSlots(count, previous);

    const target =
      requirements.length > 0
        ? requirements.reduce((sum, item) => sum + Math.max(Number(item.min) || 1, 1), 0)
        : prototypePhotoTarget();

    this.setData({
      task,
      uploadUrl,
      photoCount: count,
      photoTarget: Math.max(target, prototypePhotoTarget()),
      slots,
    });
  },

  pickSlotByKey(slotKey: string): SlotUi | null {
    if (slotKey) {
      const found = this.data.slots.find((slot) => slot.key === slotKey);
      if (found) return found;
    }
    const pending = this.data.slots.find((slot) => !slot.uploaded);
    return pending || null;
  },

  updateSlot(slotKey: string, patch: Partial<SlotUi>) {
    const slots = this.data.slots.map((slot) =>
      slot.key === slotKey
        ? {
            ...slot,
            ...patch,
          }
        : slot,
    );
    this.setData({ slots });
  },

  async resolveUploadSlot(slotKey: string): Promise<string> {
    const uploadUrl = this.data.uploadUrl || String(this.data.task?.upload_url || "");
    if (!uploadUrl) {
      throw new ApiRequestError("invalid_upload_url");
    }
    try {
      const info = await CustomerTaskApi.getUploadTaskInfo(uploadUrl);
      const currentStep = String(info.current_step || "").trim();
      if (currentStep) return currentStep;
    } catch {
      // Fall back to requested slot key if metadata endpoint is unavailable.
    }
    return slotKey;
  },

  isReadBackConfirmed(beforeCount: number, afterTask: CustomerTask, slotKey: string): boolean {
    if (photoCount(afterTask) > beforeCount) return true;
    const afterSlot = this.data.slots.find((slot) => slot.key === slotKey);
    return Boolean(afterSlot?.uploaded);
  },

  async onAddPhoto(e: WechatMiniprogram.CustomEvent<{ slotKey?: string }>) {
    if (this.isBusy("uploading")) return;
    const slot = this.pickSlotByKey(String(e?.detail?.slotKey || ""));
    if (!slot) {
      wx.showToast({ title: "照片已上传完成", icon: "none" });
      return;
    }
    await this.uploadSlot(slot, { pickNewPhoto: true });
  },

  async onRetrySlot(e: WechatMiniprogram.CustomEvent<{ slotKey?: string }>) {
    if (this.isBusy("uploading")) return;
    const slot = this.pickSlotByKey(String(e?.detail?.slotKey || ""));
    if (!slot) return;
    await this.uploadSlot(slot, { pickNewPhoto: !slot.localPath });
  },

  onRemoveSlot(e: WechatMiniprogram.CustomEvent<{ slotKey?: string }>) {
    const slotKey = String(e?.detail?.slotKey || "");
    if (!slotKey) return;
    const slot = this.pickSlotByKey(slotKey);
    if (!slot) return;
    if (slot.uploaded) {
      wx.showToast({ title: "当前版本暂不支持删除已上传照片", icon: "none" });
      return;
    }
    this.updateSlot(slot.key, {
      localPath: "",
      error: "",
      uploading: false,
      progress: 0,
      canRetry: false,
      canRemove: false,
    });
  },

  onPreviewSlot(e: WechatMiniprogram.CustomEvent<{ localPath?: string }>) {
    const localPath = String(e?.detail?.localPath || "");
    if (!localPath) return;
    previewImage(localPath, [localPath]);
  },

  async uploadSlot(slot: SlotUi, options: { pickNewPhoto: boolean }) {
    const uploadUrl = this.data.uploadUrl || String(this.data.task?.upload_url || "");
    if (!uploadUrl) {
      wx.showToast({ title: "照片上传入口不可用", icon: "none" });
      return;
    }
    if (this.isBusy("uploading")) {
      wx.showToast({ title: "请等待当前上传完成", icon: "none" });
      return;
    }

    let localPath = slot.localPath;
    try {
      if (options.pickNewPhoto) {
        const picked = await choosePhoto();
        localPath = picked.tempFilePath;
      }
      if (!localPath) throw new Error("no_file_selected");

      this.setBusy("uploading", true);
      this.updateSlot(slot.key, {
        localPath,
        uploading: true,
        progress: 0,
        error: "",
        canRetry: false,
        canRemove: false,
      });

      const beforeCount = this.data.photoCount;
      const uploadSlot = await this.resolveUploadSlot(slot.key);
      await CustomerTaskApi.uploadPhoto(uploadUrl, localPath, uploadSlot, {
        onProgress: (progress) => {
          this.updateSlot(slot.key, { progress, uploading: progress < 100 });
        },
      });
      const readBackTask = await this.loadTask({ silent: true });
      if (!readBackTask) {
        throw new ApiRequestError("network_error");
      }
      this.applyTaskToPhotoState(readBackTask);

      const confirmed = this.isReadBackConfirmed(beforeCount, readBackTask, slot.key);
      if (!confirmed) {
        this.updateSlot(slot.key, {
          uploading: false,
          progress: 0,
          error: "上传未在服务器确认，请重试",
          canRetry: true,
          canRemove: true,
          localPath,
        });
        wx.showToast({ title: "上传未确认，请重试", icon: "none" });
        return;
      }
      wx.showToast({ title: "上传成功", icon: "success" });
    } catch (err) {
      const msg =
        err instanceof Error && err.message === "cancelled"
          ? ""
          : mapErrorMessage(err instanceof ApiRequestError ? err.code : "network_error");
      if (msg) wx.showToast({ title: msg, icon: "none" });
      this.updateSlot(slot.key, {
        uploading: false,
        progress: 0,
        error: msg || "上传失败",
        canRetry: true,
        canRemove: true,
        localPath,
      });
    } finally {
      this.setBusy("uploading", false);
    }
  },

  onBackHome() {
    if (this.isBusy("uploading")) return;
    wx.navigateBack({
      fail: () => {
        wx.redirectTo({ url: "/pages/task-home/task-home" });
      },
    });
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
      confirmText: "知道了",
    });
  },

  onDone() {
    if (this.data.photoCount < 1) {
      wx.showToast({ title: "请至少添加一张照片", icon: "none" });
      return;
    }
    this.onBackHome();
  },
});
