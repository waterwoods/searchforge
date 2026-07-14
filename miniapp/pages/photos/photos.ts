import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import { choosePhoto, preparePhotoForUpload, previewImage } from "../../services/mediaCaptureAdapter";
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
import { appConfig } from "../../utils/config";

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
  uploadStage: string;
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

const SLOW_UPLOAD_NOTICE_MS = 8_000;
const PHOTO_MEASUREMENT_BUILD_ID = "p20-photo-measurement-v1";
let slowUploadTimer: ReturnType<typeof setTimeout> | undefined;

type UploadMeasurementResponse = {
  upload_measurement?: {
    request_id?: string;
    server_duration_ms?: number;
  };
};

function logPhotoTiming(record: Record<string, unknown>) {
  // Never include task tokens, local file paths, image data, or storage URLs.
  console.info("[photo_upload_timing]", record);
}

function clearSlowUploadTimer() {
  if (slowUploadTimer) {
    clearTimeout(slowUploadTimer);
    slowUploadTimer = undefined;
  }
}

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
    uploadStage: "",
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
    let originalSize: number | null = null;
    let uploadSize: number | null = null;
    let compressionMs: number | null = null;
    let compressionApplied: boolean | null = null;
    let uploadMs: number | null = null;
    let readBackMs: number | null = null;
    let serverReportedMs: number | null = null;
    let serverRequestId: string | null = null;
    const progressMilestones = [0];
    const totalStartedAt = Date.now();
    try {
      // Lock before opening the native picker so a second tap cannot queue another upload.
      this.setBusy("uploading", true);
      if (options.pickNewPhoto) {
        this.setData({ uploadStage: "正在打开照片资料…" });
        const picked = await choosePhoto();
        this.setData({ uploadStage: "正在准备照片…" });
        const prepared = await preparePhotoForUpload(picked);
        localPath = prepared.tempFilePath;
        originalSize = prepared.originalSize;
        uploadSize = prepared.uploadSize;
        compressionMs = prepared.compressionDurationMs;
        compressionApplied = prepared.compressed;
      }
      if (!localPath) throw new Error("no_file_selected");

      this.setData({ uploadStage: "正在上传… 0%" });
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
      const uploadStartedAt = Date.now();
      clearSlowUploadTimer();
      slowUploadTimer = setTimeout(() => {
        this.setData({ uploadStage: "照片较大，仍在上传，请稍候…" });
      }, SLOW_UPLOAD_NOTICE_MS);
      const uploadResponse = (await CustomerTaskApi.uploadPhoto(uploadUrl, localPath, uploadSlot, {
        onProgress: (progress) => {
          const safeProgress = Math.max(0, Math.min(100, Number(progress) || 0));
          this.setData({ uploadStage: `正在上传… ${safeProgress}%` });
          this.updateSlot(slot.key, { progress: safeProgress, uploading: safeProgress < 100 });
          if (!progressMilestones.includes(safeProgress)) {
            progressMilestones.push(safeProgress);
          }
        },
      })) as UploadMeasurementResponse;
      clearSlowUploadTimer();
      uploadMs = Date.now() - uploadStartedAt;
      serverReportedMs = Number.isFinite(uploadResponse?.upload_measurement?.server_duration_ms)
        ? Number(uploadResponse.upload_measurement?.server_duration_ms)
        : null;
      serverRequestId = String(uploadResponse?.upload_measurement?.request_id || "") || null;
      this.setData({ uploadStage: "正在确认上传结果…" });
      const readBackStartedAt = Date.now();
      const readBackTask = await this.loadTask({ silent: true });
      if (!readBackTask) {
        throw new ApiRequestError("network_error");
      }
      readBackMs = Date.now() - readBackStartedAt;
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
        this.setData({ uploadStage: "上传失败，请重试" });
        wx.showToast({ title: "上传未确认，请重试", icon: "none" });
        return;
      }
      this.setData({ uploadStage: "上传完成" });
      logPhotoTiming({
        event: "upload_measurement_complete",
        client_build_id: PHOTO_MEASUREMENT_BUILD_ID,
        api_profile: appConfig.apiProfile,
        api_host: appConfig.apiBaseUrl,
        original_bytes: originalSize,
        compressed_bytes: uploadSize,
        compression_ms: compressionMs,
        compression_applied: compressionApplied,
        upload_ms: uploadMs,
        server_reported_ms: serverReportedMs,
        server_request_id: serverRequestId,
        readback_ms: readBackMs,
        total_ms: Date.now() - totalStartedAt,
        progress_milestones: progressMilestones,
      });
      wx.showToast({ title: "上传完成", icon: "success" });
    } catch (err) {
      clearSlowUploadTimer();
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
      if (msg) this.setData({ uploadStage: "上传失败，请重试" });
      if (msg) {
        logPhotoTiming({
          event: "upload_measurement_failed",
          client_build_id: PHOTO_MEASUREMENT_BUILD_ID,
          api_profile: appConfig.apiProfile,
          api_host: appConfig.apiBaseUrl,
          original_bytes: originalSize,
          compressed_bytes: uploadSize,
          compression_ms: compressionMs,
          compression_applied: compressionApplied,
          upload_ms: uploadMs,
          server_reported_ms: serverReportedMs,
          server_request_id: serverRequestId,
          readback_ms: readBackMs,
          total_ms: Date.now() - totalStartedAt,
          progress_milestones: progressMilestones,
          error_code: err instanceof ApiRequestError ? err.code : "network_error",
        });
      }
    } finally {
      clearSlowUploadTimer();
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
