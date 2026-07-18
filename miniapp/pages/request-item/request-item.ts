import { taskPage } from "../../behaviors/taskPage";
import { choosePhoto, preparePhotoForUpload, previewImage } from "../../services/mediaCaptureAdapter";
import { CustomerTaskApi } from "../../services/taskApi";
import type {
  CustomerTask,
  Slice1CommandResult,
  Slice1CustomerNextAction,
  Slice1RequestItem,
  Slice1RequestProgress,
} from "../../types/task";
import { ApiRequestError } from "../../utils/request";
import {
  clearRequestItemDraft,
  loadRequestItemDraft,
  newClientDraftId,
  newCommandIdentity,
  saveRequestItemDraft,
  type RequestItemDraft,
} from "../../utils/requestItemDraft";
import {
  applySlice1ProjectionToTask,
  EMPTY_SLICE1_PROGRESS,
  extractSlice1Projection,
  factFieldForItemType,
  isEvidenceItemType,
  isSlice1CustomerFlow,
  mapSlice1CustomerView,
  validateFreeText,
  validateVin,
} from "../../utils/slice1Customer";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy, mapErrorMessage } from "../../utils/taskMapping";

type SubmissionState =
  | "idle"
  | "validating"
  | "uploading"
  | "submitting"
  | "confirmed"
  | "failed"
  | "uncertain";

type UploadItemUi = {
  localPath: string;
  uploading: boolean;
  uploaded: boolean;
  attachmentId: string;
  error: string;
  progress: number;
};

type PageData = {
  loading: boolean;
  loadingMessage: string;
  pageError: typeof EMPTY_TASK_ERROR;
  task: CustomerTask | null;
  nextAction: Slice1CustomerNextAction | null;
  nextActionTitle: string;
  nextActionInstructions: string;
  queuedItems: Slice1RequestItem[];
  satisfiedItems: Slice1RequestItem[];
  progress: Slice1RequestProgress;
  brokerStatus: string;
  brokerStatusLabel: string;
  submissionState: SubmissionState;
  uploadItems: UploadItemUi[];
  uploadStatusText: string;
  draftValue: string;
  validationMessage: string;
  retryAvailable: boolean;
  lastServerUpdate: string;
  isDestroyed: boolean;
  requestGeneration: number;
  waitingForBroker: boolean;
  inputMode: "text" | "evidence" | "none";
  itemType: string;
  inputLabel: string;
  inputPlaceholder: string;
  submitLabel: string;
  submitDisabled: boolean;
  submitDisabledReason: string;
  shellSafetyCopy: string;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  taskViewModel: typeof EMPTY_TASK_VIEW_MODEL;
  errorState: typeof EMPTY_TASK_ERROR;
  retryMeta: {
    attempts: number;
    cooldownUntil: number;
  };
};

type PageInternal = {
  clientDraftId: string;
  commandId: string;
  idempotencyKey: string;
  expectedCaseVersion: number;
  activeRequestItemId: string;
  requestId: string;
  caseId: string;
  submitInFlight: boolean;
  firstShowConsumed: boolean;
  pageDestroyed: boolean;
};

const EMPTY_UPLOAD_ITEM: UploadItemUi = {
  localPath: "",
  uploading: false,
  uploaded: false,
  attachmentId: "",
  error: "",
  progress: 0,
};

function ensureInternal(page: WechatMiniprogram.Page.Instance): PageInternal {
  const target = page as WechatMiniprogram.Page.Instance & { __requestItemState?: PageInternal };
  if (!target.__requestItemState) {
    target.__requestItemState = {
      clientDraftId: newClientDraftId(),
      commandId: "",
      idempotencyKey: "",
      expectedCaseVersion: 0,
      activeRequestItemId: "",
      requestId: "",
      caseId: "",
      submitInFlight: false,
      firstShowConsumed: false,
      pageDestroyed: false,
    };
  }
  return target.__requestItemState;
}

function brokerStatusLabel(status: string): string {
  if (status === "waiting_for_customer" || status === "wait_for_customer_item") return "等待您补充";
  if (status === "review_ready" || status === "review_customer_response") return "等待经纪人审核";
  if (status === "reviewing" || status === "create_request") return "经纪人处理中";
  return "";
}

function inputCopy(itemType: string): { label: string; placeholder: string } {
  if (itemType === "vin") {
    return { label: "车辆 VIN", placeholder: "请输入 17 位 VIN" };
  }
  return { label: "补充说明", placeholder: "请按陈总要求填写" };
}

Page({
  behaviors: [taskPage],
  data: {
    loading: true,
    loadingMessage: "正在加载补充要求…",
    pageError: EMPTY_TASK_ERROR,
    task: null,
    nextAction: null,
    nextActionTitle: "",
    nextActionInstructions: "",
    queuedItems: [],
    satisfiedItems: [],
    progress: { ...EMPTY_SLICE1_PROGRESS },
    brokerStatus: "",
    brokerStatusLabel: "",
    submissionState: "idle",
    uploadItems: [{ ...EMPTY_UPLOAD_ITEM }],
    uploadStatusText: "",
    draftValue: "",
    validationMessage: "",
    retryAvailable: false,
    lastServerUpdate: "",
    isDestroyed: false,
    requestGeneration: 0,
    waitingForBroker: false,
    inputMode: "none",
    itemType: "",
    inputLabel: "",
    inputPlaceholder: "",
    submitLabel: "提交给陈总",
    submitDisabled: false,
    submitDisabledReason: "",
    shellSafetyCopy: "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。",
    busy: {
      loading: true,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
    errorState: EMPTY_TASK_ERROR,
    retryMeta: {
      attempts: 0,
      cooldownUntil: 0,
    },
  } as PageData,

  onLoad() {
    const internal = ensureInternal(this);
    internal.pageDestroyed = false;
    this.setData({ isDestroyed: false, loading: true });
    void this.bootstrapPage({ ownerLoad: true });
  },

  onShow() {
    const internal = ensureInternal(this);
    if (internal.pageDestroyed) return;
    if (!internal.firstShowConsumed) {
      internal.firstShowConsumed = true;
      return;
    }
    void this.bootstrapPage({ ownerLoad: false });
  },

  onHide() {
    this.persistDraftSafe();
  },

  onUnload() {
    const internal = ensureInternal(this);
    internal.pageDestroyed = true;
    this.persistDraftSafe();
    this.markTaskPageDestroyed();
    this.setData({
      isDestroyed: true,
      requestGeneration: Number(this.data.requestGeneration || 0) + 1,
    });
  },

  onPullDownRefresh() {
    void this.bootstrapPage({ ownerLoad: false, force: true }).finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  safePageSetData(patch: Record<string, unknown>) {
    if (ensureInternal(this).pageDestroyed || this.data.isDestroyed) return;
    this.setData(patch);
  },

  async bootstrapPage(options?: { ownerLoad?: boolean; force?: boolean }) {
    const generation = Number(this.data.requestGeneration || 0) + 1;
    this.safePageSetData({
      requestGeneration: generation,
      loading: true,
      pageError: EMPTY_TASK_ERROR,
    });
    this.setBusy("loading", true);

    try {
      const task = options?.force
        ? await this.rehydrateAuthoritativeTask()
        : await this.ensureTaskInitialized({ ownerLoad: Boolean(options?.ownerLoad) });
      if (ensureInternal(this).pageDestroyed || generation !== this.data.requestGeneration) {
        return;
      }
      if (!task) {
        this.safePageSetData({
          loading: false,
          pageError: {
            code: "network_error",
            message: mapErrorMessage("network_error"),
            retryable: true,
            blocking: true,
          },
        });
        return;
      }
      if (!isSlice1CustomerFlow(task)) {
        this.safePageSetData({
          loading: false,
          pageError: {
            code: "slice1_not_enabled",
            message: "当前任务无需此步骤，请返回我的资料继续。",
            retryable: false,
            blocking: true,
          },
        });
        return;
      }
      this.applyAuthoritativeTask(task, { restoreDraft: true });
    } catch {
      if (ensureInternal(this).pageDestroyed || generation !== this.data.requestGeneration) {
        return;
      }
      this.safePageSetData({
        loading: false,
        pageError: {
          code: "network_error",
          message: mapErrorMessage("network_error"),
          retryable: true,
          blocking: true,
        },
      });
    } finally {
      if (!ensureInternal(this).pageDestroyed && generation === this.data.requestGeneration) {
        this.setBusy("loading", false);
        this.safePageSetData({ loading: false });
      }
    }
  },

  applyAuthoritativeTask(task: CustomerTask, options?: { restoreDraft?: boolean }) {
    const view = mapSlice1CustomerView(task);
    const nextAction = view.nextAction;
    const itemType = String(nextAction?.required_input || "").trim();
    const waitingForBroker = view.waitingForBroker;
    const evidence = isEvidenceItemType(itemType) || String(nextAction?.action_type || "") === "provide_evidence";
    const text = !waitingForBroker && !evidence && (itemType === "vin" || itemType === "free_text" || String(nextAction?.action_type || "") === "provide_fact");
    const copy = inputCopy(itemType);
    const internal = ensureInternal(this);
    const previousItemId = internal.activeRequestItemId;
    const nextItemId = String(nextAction?.request_item_id || "").trim();
    const requestId = String(nextAction?.request_id || view.openRequestId || "").trim();
    const caseId = String(task.case_id || "").trim();

    internal.caseId = caseId;
    internal.requestId = requestId;
    internal.activeRequestItemId = nextItemId;
    internal.expectedCaseVersion = view.aggregateVersion;

    if (previousItemId && nextItemId && previousItemId !== nextItemId) {
      clearRequestItemDraft(caseId, requestId, previousItemId);
      internal.commandId = "";
      internal.idempotencyKey = "";
      internal.clientDraftId = newClientDraftId();
    }

    let draftValue = "";
    let uploadItem = { ...EMPTY_UPLOAD_ITEM };
    if (options?.restoreDraft && caseId && requestId && nextItemId) {
      const draft = loadRequestItemDraft(caseId, requestId, nextItemId);
      if (draft) {
        draftValue = draft.draft_value || "";
        internal.clientDraftId = draft.client_draft_id || internal.clientDraftId;
        if (draft.command_id && draft.idempotency_key) {
          internal.commandId = draft.command_id;
          internal.idempotencyKey = draft.idempotency_key;
          if (typeof draft.expected_case_version === "number") {
            internal.expectedCaseVersion = draft.expected_case_version;
          }
        }
        if (draft.attachment_id) {
          uploadItem = {
            ...EMPTY_UPLOAD_ITEM,
            attachmentId: draft.attachment_id,
            uploaded: true,
            localPath: draft.local_file_path || "",
          };
        } else if (draft.local_file_path) {
          uploadItem = {
            ...EMPTY_UPLOAD_ITEM,
            localPath: draft.local_file_path,
          };
        }
      }
    }

    const submitDisabled = waitingForBroker || !nextItemId;
    // Titles/instructions already overlay Constitution via mapSlice1CustomerView.
    this.safePageSetData({
      task,
      nextAction,
      nextActionTitle: String(
        view.constitutionToday ||
          nextAction?.title ||
          (waitingForBroker ? "资料已提交，等待经纪人审核" : ""),
      ),
      nextActionInstructions: String(
        view.constitutionWhy || nextAction?.instructions || "",
      ),
      queuedItems: view.queuedItems,
      satisfiedItems: view.satisfiedItems,
      progress: view.progress,
      brokerStatus: view.brokerStatus,
      brokerStatusLabel: brokerStatusLabel(view.brokerStatus),
      lastServerUpdate: view.lastServerUpdate,
      waitingForBroker,
      inputMode: waitingForBroker ? "none" : evidence ? "evidence" : text ? "text" : "none",
      itemType,
      inputLabel: copy.label,
      inputPlaceholder: copy.placeholder,
      draftValue,
      uploadItems: [uploadItem],
      uploadStatusText: uploadItem.uploaded
        ? "照片已上传，待提交确认"
        : uploadItem.localPath
          ? "已选择照片，尚未上传"
          : "",
      validationMessage: "",
      submissionState: waitingForBroker ? "confirmed" : this.data.submissionState === "uncertain" ? "uncertain" : "idle",
      retryAvailable: this.data.submissionState === "uncertain",
      submitLabel: waitingForBroker ? "返回我的资料" : "提交给陈总",
      submitDisabled,
      submitDisabledReason: waitingForBroker ? "" : "",
      pageError: EMPTY_TASK_ERROR,
      loading: false,
    });
  },

  persistDraftSafe() {
    const internal = ensureInternal(this);
    if (!internal.caseId || !internal.requestId || !internal.activeRequestItemId) return;
    if (this.data.waitingForBroker) return;
    const upload = (this.data.uploadItems || [])[0] || EMPTY_UPLOAD_ITEM;
    const draft: RequestItemDraft = {
      version: 1,
      case_id: internal.caseId,
      request_id: internal.requestId,
      request_item_id: internal.activeRequestItemId,
      item_type: String(this.data.itemType || ""),
      draft_value: String(this.data.draftValue || ""),
      client_draft_id: internal.clientDraftId,
      command_id: internal.commandId || undefined,
      idempotency_key: internal.idempotencyKey || undefined,
      expected_case_version: internal.expectedCaseVersion,
      attachment_id: upload.attachmentId || undefined,
      local_file_path: upload.localPath || undefined,
      updated_at: new Date().toISOString(),
    };
    saveRequestItemDraft(draft);
  },

  onDraftInput(e: WechatMiniprogram.Input) {
    const internal = ensureInternal(this);
    if (this.data.submissionState !== "uncertain") {
      internal.commandId = "";
      internal.idempotencyKey = "";
    }
    this.safePageSetData({
      draftValue: e.detail.value || "",
      validationMessage: "",
      retryAvailable: false,
      submissionState: "idle",
    });
  },

  async onChoosePhoto() {
    if (this.data.busy.submitting || this.data.uploadItems?.[0]?.uploading) return;
    try {
      const chosen = await choosePhoto();
      const prepared = await preparePhotoForUpload(chosen);
      this.safePageSetData({
        uploadItems: [
          {
            ...EMPTY_UPLOAD_ITEM,
            localPath: prepared.tempFilePath,
          },
        ],
        uploadStatusText: "已选择照片，尚未上传",
        validationMessage: "",
        submissionState: "idle",
        retryAvailable: false,
      });
      this.persistDraftSafe();
    } catch {
      this.safePageSetData({
        validationMessage: "选择照片失败，请重试",
      });
    }
  },

  onPreviewUpload() {
    const path = String(this.data.uploadItems?.[0]?.localPath || "");
    if (!path) return;
    previewImage(path, [path]);
  },

  ensureCommandIdentity() {
    const internal = ensureInternal(this);
    if (!internal.commandId || !internal.idempotencyKey) {
      const ids = newCommandIdentity("cmd_request_item");
      internal.commandId = ids.command_id;
      internal.idempotencyKey = ids.idempotency_key;
    }
    return {
      command_id: internal.commandId,
      idempotency_key: internal.idempotencyKey,
      expected_case_version: internal.expectedCaseVersion,
      client_draft_id: internal.clientDraftId,
    };
  },

  async uploadEvidenceIfNeeded(): Promise<string> {
    const upload = (this.data.uploadItems || [])[0] || EMPTY_UPLOAD_ITEM;
    if (upload.attachmentId) return upload.attachmentId;
    const localPath = String(upload.localPath || "");
    if (!localPath) {
      throw new ApiRequestError("evidence_required");
    }
    const task = this.data.task as CustomerTask | null;
    const uploadUrl = String(task?.upload_url || "").trim();
    if (!uploadUrl) {
      throw new ApiRequestError("invalid_upload_url");
    }

    this.setBusy("uploading", true);
    this.safePageSetData({
      submissionState: "uploading",
      uploadStatusText: "正在上传…",
      uploadItems: [{ ...upload, uploading: true, error: "", progress: 0 }],
    });

    try {
      const slot =
        this.data.itemType === "policy_or_insurance_card" || this.data.itemType === "photo_evidence"
          ? "other_evidence"
          : "other_evidence";
      const response = await CustomerTaskApi.uploadPhoto(uploadUrl, localPath, slot, {
        uploadIntentId: `slice1-${ensureInternal(this).clientDraftId}`,
        onProgress: (progress) => {
          const current = (this.data.uploadItems || [])[0] || upload;
          this.safePageSetData({
            uploadItems: [{ ...current, uploading: true, progress }],
          });
        },
      });
      const attachmentId = CustomerTaskApi.extractAttachmentId(response);
      if (!attachmentId) {
        throw new ApiRequestError("upload_missing_attachment_id");
      }
      this.safePageSetData({
        uploadItems: [
          {
            localPath,
            uploading: false,
            uploaded: true,
            attachmentId,
            error: "",
            progress: 100,
          },
        ],
        uploadStatusText: "照片已上传，待提交确认",
      });
      this.persistDraftSafe();
      return attachmentId;
    } catch (error) {
      const code = error instanceof ApiRequestError ? error.code : "network_error";
      this.safePageSetData({
        uploadItems: [
          {
            ...upload,
            localPath,
            uploading: false,
            uploaded: false,
            attachmentId: "",
            error: mapErrorMessage(code),
            progress: 0,
          },
        ],
        uploadStatusText: "上传失败，可重试",
        validationMessage: mapErrorMessage(code),
        submissionState: "failed",
        retryAvailable: true,
      });
      throw error;
    } finally {
      this.setBusy("uploading", false);
    }
  },

  async onSubmit() {
    await this.runSubmit({ reuseIdentity: false });
  },

  async onRetrySubmit() {
    await this.runSubmit({ reuseIdentity: true });
  },

  async runSubmit(options: { reuseIdentity: boolean }) {
    const internal = ensureInternal(this);
    if (internal.submitInFlight || this.data.busy.submitting || this.data.waitingForBroker) return;
    if (!internal.activeRequestItemId) return;

    const token = this.requireToken();
    if (!token) return;

    const itemType = String(this.data.itemType || "");
    const evidenceMode = this.data.inputMode === "evidence";
    let fact: { field: string; value: string } | undefined;
    let evidence: { attachment_id: string } | undefined;

    this.safePageSetData({
      submissionState: "validating",
      validationMessage: "",
      pageError: EMPTY_TASK_ERROR,
    });

    if (evidenceMode) {
      try {
        const attachmentId = await this.uploadEvidenceIfNeeded();
        evidence = { attachment_id: attachmentId };
      } catch {
        return;
      }
    } else if (itemType === "vin") {
      const result = validateVin(String(this.data.draftValue || ""));
      if (!result.ok) {
        this.safePageSetData({
          validationMessage: result.message,
          submissionState: "failed",
          draftValue: result.normalized || this.data.draftValue,
        });
        return;
      }
      this.safePageSetData({ draftValue: result.normalized });
      fact = { field: factFieldForItemType("vin"), value: result.normalized };
    } else {
      const result = validateFreeText(String(this.data.draftValue || ""));
      if (!result.ok) {
        this.safePageSetData({
          validationMessage: result.message,
          submissionState: "failed",
        });
        return;
      }
      fact = { field: factFieldForItemType(itemType || "free_text"), value: result.normalized };
    }

    if (!options.reuseIdentity && this.data.submissionState !== "uncertain") {
      // Fresh attempt: mint identity once when absent. Uncertain retry reuses the same IDs.
      if (!internal.commandId || !internal.idempotencyKey) {
        const ids = newCommandIdentity("cmd_request_item");
        internal.commandId = ids.command_id;
        internal.idempotencyKey = ids.idempotency_key;
      }
    } else {
      this.ensureCommandIdentity();
    }

    const identity = {
      command_id: internal.commandId,
      idempotency_key: internal.idempotencyKey,
      expected_case_version: internal.expectedCaseVersion,
      client_draft_id: internal.clientDraftId,
    };
    internal.submitInFlight = true;
    this.setBusy("submitting", true);
    this.safePageSetData({
      submissionState: "submitting",
      submitDisabled: true,
      submitDisabledReason: "正在提交…",
      retryAvailable: false,
    });
    this.persistDraftSafe();

    try {
      const result = await CustomerTaskApi.submitRequestItem(token, internal.activeRequestItemId, {
        command_id: identity.command_id,
        idempotency_key: identity.idempotency_key,
        expected_case_version: identity.expected_case_version,
        client_draft_id: identity.client_draft_id,
        fact,
        evidence,
      });
      await this.handleSubmitResult(result);
    } catch (error) {
      if (error instanceof ApiRequestError && (error.code === "invalid_or_expired_task_link" || error.status === 403)) {
        this.persistDraftSafe();
        wx.redirectTo({ url: "/pages/error/error?code=invalid_or_expired_task_link" });
        return;
      }
      this.safePageSetData({
        submissionState: "uncertain",
        retryAvailable: true,
        submitDisabled: false,
        submitDisabledReason: "",
        pageError: {
          code: "timeout",
          message: "提交结果未确认，请重试。不会重复提交。",
          retryable: true,
          blocking: false,
        },
      });
      console.info("[slice1_submit_retry]", { reason: "uncertain_outcome" });
      this.persistDraftSafe();
      // Reconcile with authoritative state when uncertain.
      try {
        const refreshed = await this.rehydrateAuthoritativeTask({ silent: true });
        if (refreshed && isSlice1CustomerFlow(refreshed)) {
          const view = mapSlice1CustomerView(refreshed);
          const stillActive = view.nextAction?.request_item_id === internal.activeRequestItemId;
          if (!stillActive) {
            clearRequestItemDraft(internal.caseId, internal.requestId, internal.activeRequestItemId);
            internal.commandId = "";
            internal.idempotencyKey = "";
            this.applyAuthoritativeTask(refreshed, { restoreDraft: true });
            wx.showToast({ title: "已同步最新状态", icon: "none" });
          }
        }
      } catch {
        // keep uncertain UI
      }
    } finally {
      internal.submitInFlight = false;
      this.setBusy("submitting", false);
    }
  },

  async handleSubmitResult(result: Slice1CommandResult) {
    const internal = ensureInternal(this);
    const outcome = String(result.outcome || "");
    if (outcome === "accepted" || outcome === "replayed") {
      const projection = result.customer_projection || extractSlice1Projection(this.data.task);
      const previousItemId = internal.activeRequestItemId;
      const previousRequestId = internal.requestId;
      const caseId = internal.caseId;
      if (caseId && previousRequestId && previousItemId) {
        clearRequestItemDraft(caseId, previousRequestId, previousItemId);
      }
      internal.commandId = "";
      internal.idempotencyKey = "";
      internal.clientDraftId = newClientDraftId();

      let nextTask = this.data.task as CustomerTask;
      if (projection) {
        nextTask = applySlice1ProjectionToTask(nextTask || ({} as CustomerTask), projection);
        const app = getApp<IAppOption>();
        app.task = nextTask;
      } else {
        const refreshed = await this.rehydrateAuthoritativeTask({ silent: true });
        if (refreshed) nextTask = refreshed;
      }
      this.applyAuthoritativeTask(nextTask, { restoreDraft: true });
      this.safePageSetData({
        submissionState: "confirmed",
        retryAvailable: false,
        submitDisabled: false,
        submitDisabledReason: "",
      });
      console.info("[slice1_submit]", {
        outcome,
        waitingForBroker: mapSlice1CustomerView(nextTask).waitingForBroker,
      });
      wx.showToast({
        title: mapSlice1CustomerView(nextTask).waitingForBroker ? "已提交，等待审核" : "已提交下一项",
        icon: "none",
      });
      return;
    }

    if (outcome === "conflict") {
      const projection = result.customer_projection;
      if (projection) {
        const nextTask = applySlice1ProjectionToTask(this.data.task as CustomerTask, projection);
        const app = getApp<IAppOption>();
        app.task = nextTask;
        internal.commandId = "";
        internal.idempotencyKey = "";
        this.applyAuthoritativeTask(nextTask, { restoreDraft: true });
      } else {
        const refreshed = await this.rehydrateAuthoritativeTask();
        if (refreshed) {
          internal.commandId = "";
          internal.idempotencyKey = "";
          this.applyAuthoritativeTask(refreshed, { restoreDraft: true });
        }
      }
      this.safePageSetData({
        submissionState: "failed",
        retryAvailable: false,
        submitDisabled: false,
        submitDisabledReason: "",
        pageError: {
          code: "version_conflict",
          message: "资料状态已更新，请查看最新要求后再提交。",
          retryable: false,
          blocking: false,
        },
      });
      return;
    }

    // rejected / validation
    const code = String(result.error_code || "validation_rejected");
    this.safePageSetData({
      submissionState: "failed",
      retryAvailable: false,
      submitDisabled: false,
      submitDisabledReason: "",
      validationMessage: mapErrorMessage(code),
      pageError: {
        code,
        message: mapErrorMessage(code),
        retryable: false,
        blocking: false,
      },
    });
    this.persistDraftSafe();
  },

  onRetry() {
    void this.bootstrapPage({ ownerLoad: false, force: true });
  },

  onLater() {
    this.persistDraftSafe();
    wx.navigateBack({ fail: () => wx.redirectTo({ url: "/pages/task-home/task-home" }) });
  },

  onBackHome() {
    if (this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    wx.redirectTo({
      url: "/pages/task-home/task-home",
      complete: () => this.setBusy("navigating", false),
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
});
