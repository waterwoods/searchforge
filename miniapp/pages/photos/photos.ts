import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import { choosePhoto, preparePhotoForUpload, previewImage } from "../../services/mediaCaptureAdapter";
import type { CustomerTask } from "../../types/task";
import { ApiRequestError } from "../../utils/request";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  resolveTaskViewModel,
  taskShellBindingsFromViewModel,
  taskViewModelDataPatch,
} from "../../utils/resolveTaskViewModel";
import {
  contactBrokerModalCopy,
  mapErrorMessage,
  photoCount,
  prototypePhotoTarget,
} from "../../utils/taskMapping";
import { appConfig } from "../../utils/config";
import { PHOTO_READ_BACK_CONFIG } from "../../utils/photoReadBack";

const SLOT_SEQUENCE = ["customer_damage_photo", "other_party_vehicle_photo"] as const;
const SLOT_LABELS: Record<string, string> = {
  customer_damage_photo: "车辆受损位置",
  other_party_vehicle_photo: "对方车辆 / 现场",
};
const MAX_ACTIVE_PHOTOS = 20;
const PHOTO_PAGE_INITIAL_LOAD_TIMEOUT_MS = 5_000;
const PHOTO_PAGE_REFRESH_ERROR_MESSAGE = "暂时无法刷新，点击重试";

type PhotoPageState = "initializing" | "ready" | "recoverable_error";

type SlotUi = {
  key: string;
  label: string;
  localPath: string;
  uploadIntentId?: string;
  /** True only for a confirmed in-session upload item; never set from category min/received. */
  uploaded: boolean;
  requirementMet: boolean;
  uploading: boolean;
  progress: number;
  error: string;
  canRetry: boolean;
  canRemove: boolean;
  requiredHint: string;
  statusText: string;
};

type PageData = {
  pageState: PhotoPageState;
  loadingMessage: string;
  uploadStage: string;
  photoCount: number;
  photoTarget: number;
  maxActivePhotos: number;
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

type PendingPhotoUpload = {
  slotKey: string;
  uploadIntentId: string;
  beforeCount: number;
  localPath: string;
};

type PhotosPageInternal = {
  pendingUploads: Record<string, PendingPhotoUpload>;
  requestGeneration: number;
  activeLoadPromise: Promise<void> | null;
  activeLoadGeneration: number | null;
  lifecycleInitialized: boolean;
  firstShowConsumed: boolean;
  pageDestroyed: boolean;
};

function ensurePhotosPageState(
  target: WechatMiniprogram.Page.Instance,
): PhotosPageInternal {
  const page = target as WechatMiniprogram.Page.Instance & { __photosPageState?: PhotosPageInternal };
  if (!page.__photosPageState) {
    page.__photosPageState = {
      pendingUploads: {},
      requestGeneration: 0,
      activeLoadPromise: null,
      activeLoadGeneration: null,
      lifecycleInitialized: false,
      firstShowConsumed: false,
      pageDestroyed: false,
    };
  }
  return page.__photosPageState;
}

function safeUploadStage(value: unknown): string {
  return value == null ? "" : String(value);
}

function safePreviousSlots(slots: unknown): SlotUi[] {
  return Array.isArray(slots) ? slots : [];
}

function listPendingUploads(state: PhotosPageInternal): PendingPhotoUpload[] {
  return Object.keys(state.pendingUploads).map((key) => state.pendingUploads[key]);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

function logPhotoPageState(record: Record<string, unknown>) {
  // Redacted lifecycle diagnostics only: no tokens, paths, customer text, or URLs.
  console.info("[photo_page_state]", record);
}

function initialLoadTimeoutMs(target: WechatMiniprogram.Page.Instance): number {
  const configured = Number((target as { __photoInitialLoadTimeoutMs?: number }).__photoInitialLoadTimeoutMs);
  return Number.isFinite(configured) && configured > 0 ? configured : PHOTO_PAGE_INITIAL_LOAD_TIMEOUT_MS;
}

function pendingUploadCount(target: WechatMiniprogram.Page.Instance): number {
  return listPendingUploads(ensurePhotosPageState(target)).length;
}

function safeErrorCode(err: unknown): string {
  if (err instanceof ApiRequestError) return err.code;
  if (err instanceof Error && err.message) return err.message;
  return "network_error";
}

function usableGalleryState(data: Partial<PageData>): boolean {
  return Boolean(data.task || safePreviousSlots(data.slots).length > 0);
}

function safeBusyState(value: Partial<PageData["busy"]> | undefined): PageData["busy"] {
  return {
    loading: Boolean(value?.loading),
    saving: Boolean(value?.saving),
    uploading: Boolean(value?.uploading),
    submitting: Boolean(value?.submitting),
    navigating: Boolean(value?.navigating),
    retrying: Boolean(value?.retrying),
  };
}

function photoTaskUiPatch(
  target: WechatMiniprogram.Page.Instance,
  task: CustomerTask,
): Pick<PageData, "task" | "uploadUrl" | "photoCount" | "photoTarget" | "slots"> {
  const count = photoCount(task);
  const uploadUrl = String(task.upload_url || "");
  const previous = safePreviousSlots((target.data as Partial<PageData>).slots);
  const pendingIntentIds = new Set(
    listPendingUploads(ensurePhotosPageState(target)).map((pending) => pending.uploadIntentId),
  );
  const requirements = (task.task_contract?.evidence_requirements || []).filter((item) =>
    isPhotoSlot(item.slot),
  );
  const slots =
    requirements.length > 0
      ? requirements.map((item) => {
          const required = Math.max(Number(item.min) || 1, 1);
          const received = Math.max(Number(item.received) || 0, 0);
          const requirementMet = received >= required;
          const prev = previous.find((slot) => slot.key === item.slot);
          const remaining = Math.max(required - received, 0);
          return {
            key: item.slot,
            label: item.label || SLOT_LABELS[item.slot] || item.slot || "事故照片",
            requirementMet,
            ...preserveDraftState(prev, pendingIntentIds),
            requiredHint: requirementMet ? "已满足要求 · 可添加更多" : `还需 ${remaining || 1} 张`,
            statusText: requirementMet ? `已上传 ${received} 张` : `已上传 ${received}/${required}`,
          } satisfies SlotUi;
        })
      : fallbackSlots(count, previous, pendingIntentIds);

  const targetCount =
    requirements.length > 0
      ? requirements.reduce((sum, item) => sum + Math.max(Number(item.min) || 1, 1), 0)
      : prototypePhotoTarget();

  return {
    task,
    uploadUrl,
    photoCount: count,
    photoTarget: Math.max(targetCount, prototypePhotoTarget()),
    slots,
  };
}

function readyPhotoPagePatch(
  target: WechatMiniprogram.Page.Instance,
  task: CustomerTask,
): Record<string, unknown> {
  const data = target.data as Partial<PageData>;
  const busy = {
    ...safeBusyState(data.busy),
    loading: false,
    uploading: false,
  };
  const vm = resolveTaskViewModel(task, task.task_contract, {
    route: (target as { route?: string }).route,
    busy,
  });
  return {
    pageState: "ready" as PhotoPageState,
    uploadStage: safeUploadStage(data.uploadStage),
    errorState: EMPTY_TASK_ERROR,
    busy,
    ...taskViewModelDataPatch(vm),
    ...photoTaskUiPatch(target, task),
  };
}

function recoverablePhotoPagePatch(
  target: WechatMiniprogram.Page.Instance,
  code: string,
  keepExistingGallery: boolean,
): Record<string, unknown> {
  const data = target.data as Partial<PageData>;
  const busy = {
    ...safeBusyState(data.busy),
    loading: false,
    uploading: false,
  };
  const errorState = {
    code,
    message: PHOTO_PAGE_REFRESH_ERROR_MESSAGE,
    retryable: true,
    blocking: false,
  };
  const fallbackTask = data.task || ({} as CustomerTask);
  const vm = resolveTaskViewModel(fallbackTask, fallbackTask.task_contract, {
    route: (target as { route?: string }).route,
    busy,
  }, errorState);
  return {
    pageState: "recoverable_error" as PhotoPageState,
    errorState,
    slots: keepExistingGallery ? safePreviousSlots(data.slots) : fallbackSlots(0, safePreviousSlots(data.slots)),
    uploadStage: safeUploadStage(data.uploadStage),
    busy,
    ...taskViewModelDataPatch(vm),
  };
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new ApiRequestError("task_load_timeout")), timeoutMs);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (err) => {
        clearTimeout(timer);
        reject(err);
      },
    );
  });
}

function clearSlowUploadTimer() {
  if (slowUploadTimer) {
    clearTimeout(slowUploadTimer);
    slowUploadTimer = undefined;
  }
}

function newUploadIntentId(): string {
  return `upl_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function isPhotoSlot(slot: string): boolean {
  const value = String(slot || "").trim().toLowerCase();
  return value.includes("photo") || value.includes("image");
}

function preserveDraftState(
  prev?: SlotUi,
  pendingIntentIds?: Set<string>,
): Pick<SlotUi, "localPath" | "uploadIntentId" | "uploading" | "progress" | "error" | "canRetry" | "canRemove" | "uploaded"> {
  const keepDraft = Boolean(prev?.error);
  const keepPendingConfirm = Boolean(
    prev?.uploadIntentId && !prev?.error && pendingIntentIds?.has(prev.uploadIntentId),
  );
  return {
    localPath: keepDraft ? prev?.localPath || "" : "",
    uploadIntentId: keepDraft || keepPendingConfirm ? prev?.uploadIntentId || "" : "",
    uploaded: false,
    uploading: false,
    progress: keepDraft || keepPendingConfirm ? Math.max(Number(prev?.progress || 0), 0) : 0,
    error: keepDraft ? prev?.error || "" : "",
    canRetry: keepDraft && Boolean(prev?.error),
    canRemove: keepDraft && Boolean(prev?.localPath || prev?.error),
  };
}

function fallbackSlots(_count: number, previous?: SlotUi[], pendingIntentIds?: Set<string>): SlotUi[] {
  return SLOT_SEQUENCE.map((key) => {
    const prev = previous?.find((slot) => slot.key === key);
    return {
      key,
      label: SLOT_LABELS[key] || key,
      requirementMet: false,
      ...preserveDraftState(prev, pendingIntentIds),
      requiredHint: "可添加照片",
      statusText: "待上传",
    };
  });
}

Page({
  behaviors: [taskPage],
  data: {
    pageState: "initializing" as PhotoPageState,
    loadingMessage: "正在加载照片资料…",
    uploadStage: "",
    slots: fallbackSlots(0) as SlotUi[],
    uploadUrl: "",
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    maxActivePhotos: MAX_ACTIVE_PHOTOS,
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

  onLoad() {
    const state = ensurePhotosPageState(this);
    state.pageDestroyed = false;
    if (state.lifecycleInitialized) return;
    state.lifecycleInitialized = true;
    void this.startPhotoPageRefresh("on_load");
  },

  onHide() {
    const state = ensurePhotosPageState(this);
    state.requestGeneration += 1;
    state.activeLoadPromise = null;
    state.activeLoadGeneration = null;
  },

  onUnload() {
    const state = ensurePhotosPageState(this);
    state.pageDestroyed = true;
    state.requestGeneration += 1;
    state.activeLoadPromise = null;
    state.activeLoadGeneration = null;
  },

  ensurePhotoPageDefaults() {
    const patch: Partial<PageData> = {};
    if (!Array.isArray(this.data.slots)) {
      patch.slots = [];
    }
    if (this.data.uploadStage == null) {
      patch.uploadStage = "";
    }
    if (Object.keys(patch).length > 0) {
      this.setData(patch);
    }
  },

  async onShow() {
    const state = ensurePhotosPageState(this);
    state.pageDestroyed = false;
    if (!state.firstShowConsumed) {
      state.firstShowConsumed = true;
      if (!state.lifecycleInitialized) {
        state.lifecycleInitialized = true;
        await this.startPhotoPageRefresh("on_show_initial");
        return;
      }
      if (state.activeLoadPromise) {
        await state.activeLoadPromise;
      }
      return;
    }
    await this.startPhotoPageRefresh("on_show");
  },

  onRetry() {
    void this.startPhotoPageRefresh("retry");
  },

  isCurrentPhotoRequest(generation: number): boolean {
    const state = ensurePhotosPageState(this);
    return !state.pageDestroyed && generation === state.requestGeneration;
  },

  logPhotoPageTransition(
    previous: PhotoPageState,
    nextState: PhotoPageState,
    reason: string,
    meta?: {
      requestGeneration?: number;
      taskLoadMs?: number | null;
      reconcileMs?: number | null;
      attachmentCount?: number | null;
      safeErrorCode?: string;
    },
  ) {
    logPhotoPageState({
      transition_from: previous,
      transition_to: nextState,
      reason,
      request_generation: meta?.requestGeneration ?? ensurePhotosPageState(this).requestGeneration,
      task_load_ms: meta?.taskLoadMs ?? null,
      reconcile_ms: meta?.reconcileMs ?? null,
      attachment_count: meta?.attachmentCount ?? this.data.photoCount ?? 0,
      pending_count: pendingUploadCount(this),
      safe_error_code: meta?.safeErrorCode || "",
    });
  },

  fetchTaskForPhotoPage(token: string): Promise<CustomerTask | null> {
    return CustomerTaskApi.getTask(token);
  },

  async startPhotoPageRefresh(reason: string): Promise<void> {
    const state = ensurePhotosPageState(this);
    if (state.pageDestroyed) return;
    if (state.activeLoadPromise) {
      return state.activeLoadPromise;
    }

    const token = this.requireToken();
    const previous = (this.data.pageState || "initializing") as PhotoPageState;
    if (!token) {
      const patch = recoverablePhotoPagePatch(this, "missing_token", usableGalleryState(this.data));
      this.setData(patch);
      this.logPhotoPageTransition(previous, "recoverable_error", "missing_token", {
        safeErrorCode: "missing_token",
      });
      return;
    }

    state.requestGeneration += 1;
    const generation = state.requestGeneration;
    state.activeLoadGeneration = generation;
    const refresh = this.runPhotoPageRefresh(generation, reason, token).finally(() => {
      const latest = ensurePhotosPageState(this);
      if (latest.activeLoadGeneration === generation) {
        latest.activeLoadPromise = null;
        latest.activeLoadGeneration = null;
      }
    });
    state.activeLoadPromise = refresh;
    return refresh;
  },

  async runPhotoPageRefresh(generation: number, reason: string, token: string): Promise<void> {
    const startedAt = Date.now();
    const previous = (this.data.pageState || "initializing") as PhotoPageState;
    try {
      const task = await withTimeout(
        Promise.resolve(this.fetchTaskForPhotoPage(token)),
        initialLoadTimeoutMs(this),
      );
      if (!this.isCurrentPhotoRequest(generation)) return;
      const taskLoadMs = Date.now() - startedAt;
      if (!task) {
        throw new ApiRequestError("task_load_failed");
      }
      const app = getApp<IAppOption>();
      app.task = task;
      this.setData(readyPhotoPagePatch(this, task));
      this.logPhotoPageTransition(previous, "ready", "task_loaded", {
        requestGeneration: generation,
        taskLoadMs,
        attachmentCount: photoCount(task),
      });
      this.schedulePendingReconciliation(task, generation, taskLoadMs);
    } catch (err) {
      if (!this.isCurrentPhotoRequest(generation)) return;
      const code = safeErrorCode(err);
      const keepExisting = usableGalleryState(this.data);
      this.setData(recoverablePhotoPagePatch(this, code, keepExisting));
      this.logPhotoPageTransition(
        previous,
        "recoverable_error",
        code === "task_load_timeout" ? "task_load_timeout" : "task_load_failed",
        {
          requestGeneration: generation,
          taskLoadMs: Date.now() - startedAt,
          safeErrorCode: code,
          attachmentCount: this.data.photoCount,
        },
      );
    }
  },

  schedulePendingReconciliation(task: CustomerTask, generation: number, taskLoadMs: number) {
    if (pendingUploadCount(this) < 1) return;
    setTimeout(() => {
      if (!this.isCurrentPhotoRequest(generation) || this.data.pageState !== "ready") return;
      const startedAt = Date.now();
      try {
        this.reconcilePendingUploads(task);
      } catch (err) {
        console.error("[photos_page_reconcile]", err);
      } finally {
        if (this.isCurrentPhotoRequest(generation) && this.data.pageState === "ready") {
          this.logPhotoPageTransition("ready", "ready", "pending_reconcile_complete", {
            requestGeneration: generation,
            taskLoadMs,
            reconcileMs: Date.now() - startedAt,
            attachmentCount: photoCount(task),
          });
        }
      }
    }, 0);
  },

  applyTaskToPhotoState(task: CustomerTask) {
    this.setData(photoTaskUiPatch(this, task));
  },

  pickSlotByKey(slotKey: string): SlotUi | null {
    const slots = safePreviousSlots(this.data.slots);
    if (slotKey) {
      return slots.find((slot) => slot.key === slotKey) || null;
    }
    return slots[0] || null;
  },

  updateSlot(slotKey: string, patch: Partial<SlotUi>) {
    const slots = safePreviousSlots(this.data.slots).map((slot) =>
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

  isReadBackConfirmed(beforeCount: number, afterTask: CustomerTask): boolean {
    return photoCount(afterTask) > beforeCount;
  },

  registerPendingUpload(pending: PendingPhotoUpload) {
    ensurePhotosPageState(this).pendingUploads[pending.uploadIntentId] = pending;
  },

  clearPendingUpload(uploadIntentId: string) {
    delete ensurePhotosPageState(this).pendingUploads[uploadIntentId];
  },

  hasPendingUploadForSlot(slotKey: string): boolean {
    for (const pending of listPendingUploads(ensurePhotosPageState(this))) {
      if (pending.slotKey === slotKey) return true;
    }
    return false;
  },

  async confirmUploadReadBack(
    pending: PendingPhotoUpload,
  ): Promise<{ confirmed: boolean; readBackMs: number; readBackTask: CustomerTask | null }> {
    const startedAt = Date.now();
    const deadline = startedAt + PHOTO_READ_BACK_CONFIG.timeoutMs;
    let readBackTask: CustomerTask | null = null;

    for (let attempt = 0; attempt < PHOTO_READ_BACK_CONFIG.maxAttempts; attempt += 1) {
      if (Date.now() >= deadline) break;
      const readBackStartedAt = Date.now();
      readBackTask = await this.loadTask({ silent: true });
      const readBackMs = Date.now() - readBackStartedAt;
      if (readBackTask) {
        this.applyTaskToPhotoState(readBackTask);
        if (this.isReadBackConfirmed(pending.beforeCount, readBackTask)) {
          return { confirmed: true, readBackMs, readBackTask };
        }
      }
      const remaining = deadline - Date.now();
      if (attempt < PHOTO_READ_BACK_CONFIG.maxAttempts - 1 && remaining > 0) {
        await sleep(Math.min(PHOTO_READ_BACK_CONFIG.retryMs, remaining));
      }
    }

    return { confirmed: false, readBackMs: Date.now() - startedAt, readBackTask };
  },

  reconcilePendingUploads(task: CustomerTask) {
    const state = ensurePhotosPageState(this);
    for (const [intentId, pending] of Object.entries(state.pendingUploads)) {
      if (!pending || !this.isReadBackConfirmed(pending.beforeCount, task)) continue;
      this.clearPendingUpload(intentId);
      this.applyTaskToPhotoState(task);
      this.setData({ uploadStage: "上传完成" });
    }
  },

  async onAddPhoto(e: WechatMiniprogram.CustomEvent<{ slotKey?: string }>) {
    if (this.isBusy("uploading")) return;
    if (this.data.photoCount >= MAX_ACTIVE_PHOTOS) {
      wx.showToast({ title: "最多上传 20 张照片", icon: "none" });
      return;
    }
    const slot = this.pickSlotByKey(String(e?.detail?.slotKey || ""));
    if (!slot) {
      wx.showToast({ title: "暂无可用照片分类", icon: "none" });
      return;
    }
    if (this.hasPendingUploadForSlot(slot.key)) {
      wx.showToast({ title: "请等待当前上传确认", icon: "none" });
      return;
    }
    await this.uploadSlot(slot, { pickNewPhoto: true });
  },

  async onRetrySlot(e: WechatMiniprogram.CustomEvent<{ slotKey?: string }>) {
    if (this.isBusy("uploading")) return;
    const slot = this.pickSlotByKey(String(e?.detail?.slotKey || ""));
    if (!slot) return;
    if (this.hasPendingUploadForSlot(slot.key)) {
      wx.showToast({ title: "请等待当前上传确认", icon: "none" });
      return;
    }
    if (!slot.canRetry || (!slot.localPath && !slot.error)) {
      if (!slot.error) wx.showToast({ title: "照片已上传完成", icon: "none" });
      return;
    }
    await this.uploadSlot(slot, { pickNewPhoto: false });
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
      uploadIntentId: "",
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
    if (slot.uploaded && !options.pickNewPhoto) {
      wx.showToast({ title: "照片已上传完成", icon: "none" });
      return;
    }
    if (this.isBusy("uploading")) {
      wx.showToast({ title: "请等待当前上传完成", icon: "none" });
      return;
    }

    let localPath = slot.localPath;
    let uploadIntentId = options.pickNewPhoto ? "" : slot.uploadIntentId || "";
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
        uploadIntentId = newUploadIntentId();
      }
      if (!localPath) throw new Error("no_file_selected");
      uploadIntentId = uploadIntentId || newUploadIntentId();

      this.setData({ uploadStage: "正在上传… 0%" });
      this.updateSlot(slot.key, {
        localPath,
        uploadIntentId,
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
        uploadIntentId,
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

      const pending: PendingPhotoUpload = {
        slotKey: slot.key,
        uploadIntentId,
        beforeCount,
        localPath,
      };
      this.registerPendingUpload(pending);
      this.setBusy("uploading", false);
      this.updateSlot(slot.key, {
        uploading: false,
        progress: 100,
        error: "",
        canRetry: false,
        canRemove: false,
        localPath,
        uploadIntentId,
      });
      this.setData({ uploadStage: "已上传，正在确认" });

      const readBackResult = await this.confirmUploadReadBack(pending);
      readBackMs = readBackResult.readBackMs;
      const confirmed = readBackResult.confirmed;
      if (!confirmed) {
        this.setData({ uploadStage: "已上传，正在确认" });
        return;
      }
      this.clearPendingUpload(uploadIntentId);
      if (readBackResult.readBackTask) {
        this.applyTaskToPhotoState(readBackResult.readBackTask);
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
        uploadIntentId,
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
