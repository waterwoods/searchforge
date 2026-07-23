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
import { clearResumeToken } from "../../utils/storage";
import {
  CASE_STATUS_ROUTE,
  SUBMIT_RECEIPT_COPY,
} from "../../utils/customerCaseSurface";
import {
  applySlice1ProjectionToTask,
  EMPTY_SLICE1_PROGRESS,
  extractSlice1Projection,
  factFieldForItemType,
  isEvidenceItemType,
  isRequestItemSubmitResolvedOnServer,
  isSlice1CustomerFlow,
  isVehicleInformationItemType,
  mapSlice1CustomerView,
  validateFreeText,
} from "../../utils/slice1Customer";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
import { contactBrokerModalCopy, mapErrorMessage } from "../../utils/taskMapping";
import {
  resolveUploadPhase,
  UPLOAD_PHASE_LABEL,
  uploadPhaseDetail,
  type UploadPhase,
} from "../../utils/uploadStateMachine";
import { resolveRequestItemWorkSurface } from "../../utils/requestItemWorkSurface";
import {
  buildVehicleInformationFactPayload,
  buildVinFactPayload,
  CLAIM_VEHICLE_COPY,
  claimVehicleFormHasAnyValue,
  EMPTY_CLAIM_VEHICLE_FORM,
  hydrateClaimVehicleForm,
  isNeedsCorrection,
  mapVehicleServerError,
  switchVinUnavailableMode,
  validateVehicleInformationSubmit,
  validateVinRequestSubmit,
  type ClaimVehicleFormFields,
} from "../../utils/claimVehicleForm";
import type { Slice1FactPayload } from "../../types/task";

/** P26G — Constitution system_default insurance without a Slice1 request row. */
function resolveSystemDefaultInsurance(task: CustomerTask | null | undefined): {
  enabled: boolean;
  title: string;
  why: string;
} {
  const customer = task?.constitution_projection?.customer;
  const tasks = Array.isArray(customer?.tasks) ? customer.tasks : [];
  const insurance = tasks.find((row) => {
    if (!row || typeof row !== "object") return false;
    const id = String((row as { task_id?: unknown }).task_id || "").trim();
    return id === "insurance_card";
  }) as
    | {
        actionable?: boolean;
        task_source?: string;
        title?: string;
        primary_action?: string;
        state?: string;
      }
    | undefined;
  if (!insurance) return { enabled: false, title: "", why: "" };
  const source = String(insurance.task_source || "system_default").trim();
  const state = String(insurance.state || "").trim();
  const actionable = Boolean(insurance.actionable) && state !== "completed" && state !== "waiting_broker";
  if (!actionable || source === "broker_requested") {
    return { enabled: false, title: "", why: "" };
  }
  return {
    enabled: true,
    title: String(insurance.primary_action || insurance.title || "上传保险卡").trim(),
    why: String(customer?.why || "请上传清晰的保险卡照片").trim(),
  };
}

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
  uploadPhase: UploadPhase;
  uploadPhaseLabel: string;
  draftValue: string;
  vehicleForm: ClaimVehicleFormFields;
  fieldErrors: Partial<Record<keyof ClaimVehicleFormFields, string>>;
  needsCorrection: boolean;
  validationMessage: string;
  retryAvailable: boolean;
  lastServerUpdate: string;
  isDestroyed: boolean;
  requestGeneration: number;
  waitingForBroker: boolean;
  inputMode: "text" | "evidence" | "vehicle" | "none";
  itemType: string;
  inputLabel: string;
  inputPlaceholder: string;
  submitLabel: string;
  submitDisabled: boolean;
  submitDisabledReason: string;
  /** Demo Polish Sprint 2 — durable in-page submit receipt (not toast-only). */
  submitReceiptVisible: boolean;
  submitReceiptText: string;
  shellSafetyCopy: string;
  /** P26H-UI — Empty Page Gate; WXML must bind these, not nextAction alone. */
  showWorkSurface: boolean;
  showFooterCta: boolean;
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
    return {
      label: CLAIM_VEHICLE_COPY.vinOnlyLabel,
      placeholder: CLAIM_VEHICLE_COPY.vinOnlyPlaceholder,
    };
  }
  if (itemType === "vehicle_information") {
    return {
      label: CLAIM_VEHICLE_COPY.pageTitle,
      placeholder: CLAIM_VEHICLE_COPY.explanation,
    };
  }
  return { label: "补充说明", placeholder: "请按陈总要求填写" };
}

function syncNavTitle(itemType: string, waitingForBroker: boolean) {
  // Never throw into submit handlers — a nav-title failure must not become "uncertain".
  try {
    if (waitingForBroker) {
      wx.setNavigationBarTitle({ title: "补充资料" });
      return;
    }
    if (itemType === "vin" || itemType === "vehicle_information") {
      wx.setNavigationBarTitle({ title: CLAIM_VEHICLE_COPY.pageTitle });
      return;
    }
    wx.setNavigationBarTitle({ title: "补充资料" });
  } catch {
    // ignore
  }
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
    uploadPhase: "idle",
    uploadPhaseLabel: "",
    draftValue: "",
    vehicleForm: { ...EMPTY_CLAIM_VEHICLE_FORM },
    fieldErrors: {},
    needsCorrection: false,
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
    submitLabel: "提交补充资料",
    submitDisabled: false,
    submitDisabledReason: "",
    submitReceiptVisible: false,
    submitReceiptText: "",
    shellSafetyCopy: "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。",
    showWorkSurface: false,
    showFooterCta: false,
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

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    qaPathLog("ENTRY", {
      page: "pages/request-item/request-item",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      note: "first_js_page_onload_or_navigated",
    });
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
          showWorkSurface: false,
          showFooterCta: false,
          pageError: {
            code: "network_error",
            message: mapErrorMessage("network_error"),
            retryable: true,
            blocking: true,
          },
        });
        return;
      }
      // P26G-Q1 — allow system_default insurance without Slice1 projection.
      // Broker request-item still requires Slice1; do not invent request rows.
      const systemDefaultInsurance = resolveSystemDefaultInsurance(task);
      if (!isSlice1CustomerFlow(task) && !systemDefaultInsurance.enabled) {
        this.safePageSetData({
          loading: false,
          showWorkSurface: false,
          showFooterCta: false,
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
    let itemType = String(nextAction?.required_input || "").trim();
    const waitingForBroker = view.waitingForBroker;
    const systemDefaultInsurance = resolveSystemDefaultInsurance(task);
    const useSystemDefaultInsurance =
      !waitingForBroker && !String(nextAction?.request_item_id || "").trim() && systemDefaultInsurance.enabled;
    if (useSystemDefaultInsurance) {
      itemType = "policy_or_insurance_card";
    }
    const evidence =
      useSystemDefaultInsurance ||
      isEvidenceItemType(itemType) ||
      String(nextAction?.action_type || "") === "provide_evidence";
    const vehicleInfo = !waitingForBroker && !evidence && isVehicleInformationItemType(itemType);
    const text =
      !waitingForBroker &&
      !evidence &&
      !vehicleInfo &&
      (itemType === "vin" || itemType === "free_text" || String(nextAction?.action_type || "") === "provide_fact");
    const copy = inputCopy(itemType);
    const internal = ensureInternal(this);
    const previousItemId = internal.activeRequestItemId;
    const nextItemId = useSystemDefaultInsurance
      ? "system_default_insurance_card"
      : String(nextAction?.request_item_id || "").trim();
    const requestId = useSystemDefaultInsurance
      ? "system_default"
      : String(nextAction?.request_id || view.openRequestId || "").trim();
    const caseId = String(task.case_id || "").trim();

    internal.caseId = caseId;
    internal.requestId = requestId;
    internal.activeRequestItemId = nextItemId;
    internal.expectedCaseVersion = view.aggregateVersion;

    const itemChanged = Boolean(previousItemId && nextItemId && previousItemId !== nextItemId);
    if (itemChanged) {
      clearRequestItemDraft(caseId, requestId, previousItemId);
      internal.commandId = "";
      internal.idempotencyKey = "";
      internal.clientDraftId = newClientDraftId();
    }

    let draftValue = "";
    let vehicleForm: ClaimVehicleFormFields = { ...EMPTY_CLAIM_VEHICLE_FORM };
    let uploadItem = { ...EMPTY_UPLOAD_ITEM };
    let localVehicleDraft: Partial<ClaimVehicleFormFields> | null = null;
    if (options?.restoreDraft && caseId && requestId && nextItemId) {
      const draft = loadRequestItemDraft(caseId, requestId, nextItemId);
      if (draft) {
        draftValue = draft.draft_value || "";
        if (draft.vehicle_draft) {
          localVehicleDraft = draft.vehicle_draft;
        }
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

    const keyFacts = (task.key_facts || {}) as Record<string, unknown>;
    if (vehicleInfo || itemType === "vin") {
      vehicleForm = hydrateClaimVehicleForm({
        keyFacts,
        draft:
          localVehicleDraft ||
          (itemType === "vin" && draftValue
            ? { vin: draftValue, vinUnavailable: false }
            : null),
        itemType,
      });
      if (itemType === "vin" && vehicleForm.vin) {
        draftValue = vehicleForm.vin;
      }
    }

    const needsCorrection = isNeedsCorrection(keyFacts);
    const submitDisabled = waitingForBroker || !nextItemId;
    const inputMode = waitingForBroker
      ? "none"
      : evidence
        ? "evidence"
        : vehicleInfo
          ? "vehicle"
          : text
            ? "text"
            : "none";
    const nextActionForUi = useSystemDefaultInsurance ? null : nextAction;
    const workSurface = resolveRequestItemWorkSurface({
      loading: false,
      waitingForBroker,
      inputMode,
      nextAction: nextActionForUi,
      pageError: EMPTY_TASK_ERROR,
    });
    syncNavTitle(itemType, waitingForBroker);

    const titleDefault =
      itemType === "vehicle_information"
        ? CLAIM_VEHICLE_COPY.pageTitle
        : waitingForBroker
          ? "补充资料已收到"
          : "";
    const instructionsDefault =
      itemType === "vehicle_information" ? CLAIM_VEHICLE_COPY.explanation : "";

    // Titles/instructions already overlay Constitution via mapSlice1CustomerView.
    this.safePageSetData({
      task,
      nextAction: nextActionForUi,
      nextActionTitle: String(
        view.constitutionToday ||
          systemDefaultInsurance.title ||
          nextAction?.title ||
          titleDefault,
      ),
      nextActionInstructions: String(
        view.constitutionWhy ||
          systemDefaultInsurance.why ||
          nextAction?.instructions ||
          instructionsDefault,
      ),
      queuedItems: view.queuedItems,
      satisfiedItems: view.satisfiedItems,
      progress: view.progress,
      brokerStatus: view.brokerStatus,
      brokerStatusLabel: brokerStatusLabel(view.brokerStatus),
      lastServerUpdate: view.lastServerUpdate,
      waitingForBroker,
      inputMode,
      itemType,
      inputLabel: copy.label,
      inputPlaceholder: copy.placeholder,
      draftValue,
      vehicleForm,
      fieldErrors: {},
      needsCorrection,
      uploadItems: [uploadItem],
      ...this.uploadPhasePatch(
        uploadItem,
        waitingForBroker
          ? "confirmed"
          : !itemChanged && this.data.submissionState === "uncertain"
            ? "uncertain"
            : "idle",
        waitingForBroker,
      ),
      validationMessage: "",
      // Preserve uncertain only while the same request item is still active.
      // Advancing to the next item (or broker wait) must clear stuck retry UI.
      submissionState: waitingForBroker
        ? "confirmed"
        : !itemChanged && this.data.submissionState === "uncertain"
          ? "uncertain"
          : "idle",
      retryAvailable: !waitingForBroker && !itemChanged && this.data.submissionState === "uncertain",
      submitLabel: waitingForBroker ? "返回我的资料" : "提交补充资料",
      submitDisabled,
      submitDisabledReason: waitingForBroker ? "" : "",
      pageError: EMPTY_TASK_ERROR,
      loading: false,
      showWorkSurface: workSurface.showWorkSurface,
      showFooterCta: workSurface.showFooterCta,
    });
  },

  uploadPhasePatch(
    upload: UploadItemUi,
    submissionState: SubmissionState,
    waitingForBroker: boolean,
  ): Pick<PageData, "uploadPhase" | "uploadPhaseLabel" | "uploadStatusText"> {
    const projectionConfirmed =
      waitingForBroker || submissionState === "confirmed";
    const phase = resolveUploadPhase({
      projectionConfirmed,
      transient: {
        localPath: upload.localPath,
        uploading: upload.uploading || submissionState === "uploading",
        uploaded: upload.uploaded,
        attachmentId: upload.attachmentId,
        error:
          upload.error ||
          (submissionState === "failed" ? mapErrorMessage("network_error") : ""),
      },
    });
    const label = UPLOAD_PHASE_LABEL[phase];
    const detail =
      phase === "uploaded"
        ? "已上传，待提交确认"
        : uploadPhaseDetail(phase, upload.progress);
    return {
      uploadPhase: phase,
      uploadPhaseLabel: label,
      uploadStatusText: detail,
    };
  },

  persistDraftSafe() {
    const internal = ensureInternal(this);
    if (!internal.caseId || !internal.requestId || !internal.activeRequestItemId) return;
    if (this.data.waitingForBroker) return;
    const upload = (this.data.uploadItems || [])[0] || EMPTY_UPLOAD_ITEM;
    const itemType = String(this.data.itemType || "");
    const vehicleForm = (this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM) as ClaimVehicleFormFields;
    const draft: RequestItemDraft = {
      version: 1,
      case_id: internal.caseId,
      request_id: internal.requestId,
      request_item_id: internal.activeRequestItemId,
      item_type: itemType,
      draft_value:
        itemType === "vin"
          ? String(this.data.draftValue || vehicleForm.vin || "")
          : String(this.data.draftValue || ""),
      vehicle_draft:
        itemType === "vehicle_information" || itemType === "vin"
          ? {
              year: vehicleForm.year || "",
              make: vehicleForm.make || "",
              model: vehicleForm.model || "",
              vin: itemType === "vin" ? String(this.data.draftValue || vehicleForm.vin || "") : vehicleForm.vin || "",
              vinUnavailable: Boolean(vehicleForm.vinUnavailable),
              licensePlate: vehicleForm.licensePlate || "",
              plateState: vehicleForm.plateState || "",
            }
          : undefined,
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
    const value = e.detail.value || "";
    const patch: Record<string, unknown> = {
      draftValue: value,
      validationMessage: "",
      fieldErrors: {},
      retryAvailable: false,
      submissionState: "idle",
    };
    if (String(this.data.itemType || "") === "vin") {
      patch.vehicleForm = {
        ...(this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM),
        vin: value,
        vinUnavailable: false,
      };
    }
    this.safePageSetData(patch);
  },

  onVehicleFieldInput(e: WechatMiniprogram.Input) {
    const internal = ensureInternal(this);
    if (this.data.submissionState !== "uncertain") {
      internal.commandId = "";
      internal.idempotencyKey = "";
    }
    const field = String((e.currentTarget as { dataset?: { field?: string } })?.dataset?.field || "");
    if (!field) return;
    const next = {
      ...(this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM),
      [field]: e.detail.value || "",
    } as ClaimVehicleFormFields;
    const fieldErrors = { ...(this.data.fieldErrors || {}) };
    delete fieldErrors[field as keyof ClaimVehicleFormFields];
    this.safePageSetData({
      vehicleForm: next,
      fieldErrors,
      validationMessage: "",
      retryAvailable: false,
      submissionState: "idle",
    });
  },

  onVinUnavailableChange(e: { detail?: { value?: boolean } }) {
    const internal = ensureInternal(this);
    if (this.data.submissionState !== "uncertain") {
      internal.commandId = "";
      internal.idempotencyKey = "";
    }
    const checked = Boolean(e?.detail?.value);
    const next = switchVinUnavailableMode(
      (this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM) as ClaimVehicleFormFields,
      checked,
    );
    this.safePageSetData({
      vehicleForm: next,
      fieldErrors: {},
      validationMessage: "",
      retryAvailable: false,
      submissionState: "idle",
    });
    this.persistDraftSafe();
  },

  async onChoosePhoto() {
    if (this.data.busy.submitting || this.data.uploadItems?.[0]?.uploading) return;
    try {
      const chosen = await choosePhoto();
      const prepared = await preparePhotoForUpload(chosen);
      const uploadItem = {
        ...EMPTY_UPLOAD_ITEM,
        localPath: prepared.tempFilePath,
      };
      this.safePageSetData({
        uploadItems: [uploadItem],
        ...this.uploadPhasePatch(uploadItem, "idle", false),
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
    const uploadingItem = { ...upload, uploading: true, error: "", progress: 0 };
    this.safePageSetData({
      submissionState: "uploading",
      uploadItems: [uploadingItem],
      ...this.uploadPhasePatch(uploadingItem, "uploading", false),
    });

    try {
      const slot =
        this.data.itemType === "policy_or_insurance_card"
          ? ensureInternal(this).activeRequestItemId === "system_default_insurance_card"
            ? "policy_or_insurance_card"
            : "other_evidence"
          : this.data.itemType === "photo_evidence"
            ? "other_evidence"
            : "other_evidence";
      const response = await CustomerTaskApi.uploadPhoto(uploadUrl, localPath, slot, {
        uploadIntentId: `slice1-${ensureInternal(this).clientDraftId}`,
        onProgress: (progress) => {
          const current = (this.data.uploadItems || [])[0] || upload;
          const next = { ...current, uploading: true, progress };
          this.safePageSetData({
            uploadItems: [next],
            ...this.uploadPhasePatch(next, "uploading", false),
          });
        },
      });
      const attachmentId = CustomerTaskApi.extractAttachmentId(response);
      if (!attachmentId) {
        throw new ApiRequestError("upload_missing_attachment_id");
      }
      const uploadedItem = {
        localPath,
        uploading: false,
        uploaded: true,
        attachmentId,
        error: "",
        progress: 100,
      };
      this.safePageSetData({
        uploadItems: [uploadedItem],
        ...this.uploadPhasePatch(uploadedItem, "idle", false),
      });
      this.persistDraftSafe();
      return attachmentId;
    } catch (error) {
      const code = error instanceof ApiRequestError ? error.code : "network_error";
      const failedItem = {
        ...upload,
        localPath,
        uploading: false,
        uploaded: false,
        attachmentId: "",
        error: mapErrorMessage(code),
        progress: 0,
      };
      this.safePageSetData({
        uploadItems: [failedItem],
        ...this.uploadPhasePatch(failedItem, "failed", false),
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

  /** Restore CTA after local validation / upload failure — never leave a stuck busy button. */
  restoreSubmitAfterFailure(patch?: Record<string, unknown>) {
    const internal = ensureInternal(this);
    internal.submitInFlight = false;
    this.setBusy("submitting", false);
    this.safePageSetData({
      submitDisabled: false,
      submitDisabledReason: "",
      submitReceiptVisible: false,
      submissionState: "failed",
      retryAvailable: false,
      ...(patch || {}),
    });
  },

  showSubmitReceipt() {
    this.safePageSetData({
      submitReceiptVisible: true,
      submitReceiptText: SUBMIT_RECEIPT_COPY,
      submissionState: "confirmed",
    });
  },

  /** Final Request More item → Case Status (Waiting Broker). Soft-freeze preserved. */
  goCaseStatusAfterSuccess() {
    if (this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    wx.redirectTo({
      url: CASE_STATUS_ROUTE,
      complete: () => this.setBusy("navigating", false),
      fail: () => {
        wx.reLaunch({
          url: CASE_STATUS_ROUTE,
          complete: () => this.setBusy("navigating", false),
        });
      },
    });
  },

  finishSubmitSuccess(args: { waitingForBroker: boolean; nextTask: CustomerTask }) {
    this.showSubmitReceipt();
    if (args.waitingForBroker) {
      try {
        const app = getApp<IAppOption>();
        app.task = args.nextTask;
      } catch {
        // ignore
      }
      // Brief in-page receipt, then land on Case Status (Loop 2).
      setTimeout(() => this.goCaseStatusAfterSuccess(), 450);
      return;
    }
  },

  async runSubmit(options: { reuseIdentity: boolean; partialVehicleSave?: boolean }) {
    const internal = ensureInternal(this);
    if (internal.submitInFlight || this.data.busy.submitting || this.data.waitingForBroker) return;
    if (!internal.activeRequestItemId) return;

    const token = this.requireToken();
    if (!token) return;

    const itemType = String(this.data.itemType || "");
    const evidenceMode = this.data.inputMode === "evidence";
    const vehicleMode = this.data.inputMode === "vehicle";
    const partialVehicleSave = Boolean(options.partialVehicleSave);
    let fact: Slice1FactPayload | undefined;
    let evidence: { attachment_id: string } | undefined;

    // Loop 1 — immediate busy on tap (before validation / upload / network).
    internal.submitInFlight = true;
    this.setBusy("submitting", true);
    this.safePageSetData({
      submissionState: "validating",
      submitDisabled: true,
      submitDisabledReason: "正在提交…",
      validationMessage: "",
      fieldErrors: {},
      pageError: EMPTY_TASK_ERROR,
      submitReceiptVisible: false,
      submitReceiptText: "",
      retryAvailable: false,
    });

    try {
      if (evidenceMode) {
        try {
          const attachmentId = await this.uploadEvidenceIfNeeded();
          evidence = { attachment_id: attachmentId };
        } catch {
          this.restoreSubmitAfterFailure({
            validationMessage: this.data.validationMessage || mapErrorMessage("network_error"),
          });
          return;
        }
      }

      // P26G — system_default insurance: upload records the slot; no Slice1 submit.
      if (internal.activeRequestItemId === "system_default_insurance_card") {
        if (!evidence?.attachment_id) {
          this.restoreSubmitAfterFailure({
            validationMessage: mapErrorMessage("evidence_required"),
          });
          return;
        }
        this.safePageSetData({
          submissionState: "submitting",
          submitDisabledReason: "正在确认…",
        });
        try {
          const refreshed = await CustomerTaskApi.getTask(token);
          const app = getApp<IAppOption>();
          app.task = refreshed;
          clearRequestItemDraft(internal.caseId, internal.requestId, internal.activeRequestItemId);
          this.applyAuthoritativeTask(refreshed, { restoreDraft: false });
          const stillOpen = resolveSystemDefaultInsurance(refreshed).enabled;
          if (!stillOpen) {
            this.finishSubmitSuccess({ waitingForBroker: true, nextTask: refreshed });
          } else {
            this.safePageSetData({
              submissionState: "uncertain",
              submitDisabled: false,
              submitDisabledReason: "",
              retryAvailable: true,
              validationMessage: "已上传，请确认状态后重试",
            });
          }
        } catch {
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
        }
        return;
      }

      if (!evidenceMode) {
        if (itemType === "vin") {
          const result = validateVinRequestSubmit(String(this.data.draftValue || ""));
          if (!result.ok) {
            this.restoreSubmitAfterFailure({
              validationMessage: result.message,
              fieldErrors: result.fieldErrors,
              draftValue: result.normalized.vin || this.data.draftValue,
              vehicleForm: {
                ...(this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM),
                vin: result.normalized.vin,
                vinUnavailable: false,
              },
            });
            return;
          }
          this.safePageSetData({
            draftValue: result.normalized.vin,
            vehicleForm: {
              ...(this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM),
              vin: result.normalized.vin,
              vinUnavailable: false,
            },
          });
          fact = buildVinFactPayload(result.normalized.vin);
        } else if (vehicleMode || itemType === "vehicle_information") {
          const form = (this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM) as ClaimVehicleFormFields;
          if (partialVehicleSave) {
            if (!claimVehicleFormHasAnyValue(form)) {
              this.restoreSubmitAfterFailure({
                validationMessage: "",
                submissionState: "idle",
              });
              return;
            }
            fact = buildVehicleInformationFactPayload(form, { final: false });
          } else {
            const result = validateVehicleInformationSubmit(form);
            if (!result.ok) {
              this.restoreSubmitAfterFailure({
                validationMessage: result.message,
                fieldErrors: result.fieldErrors,
                vehicleForm: result.normalized,
              });
              return;
            }
            this.safePageSetData({ vehicleForm: result.normalized, fieldErrors: {} });
            fact = buildVehicleInformationFactPayload(result.normalized, { final: true });
          }
        } else {
          const result = validateFreeText(String(this.data.draftValue || ""));
          if (!result.ok) {
            this.restoreSubmitAfterFailure({
              validationMessage: result.message,
            });
            return;
          }
          fact = { field: factFieldForItemType(itemType || "free_text"), value: result.normalized };
        }
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
        await this.handleSubmitResult(result, { partialVehicleSave });
      } catch (error) {
        if (error instanceof ApiRequestError && (error.code === "invalid_or_expired_task_link" || error.status === 403)) {
          this.persistDraftSafe();
          clearResumeToken();
          try {
            const app = getApp<IAppOption>();
            app.taskToken = "";
            app.task = undefined;
          } catch {
            // ignore
          }
          wx.redirectTo({ url: "/pages/error/error?code=invalid_or_expired_task_link" });
          return;
        }
        if (error instanceof ApiRequestError && error.code === "case_closed_read_only") {
          this.safePageSetData({
            submissionState: "failed",
            retryAvailable: false,
            submitDisabled: true,
            submitDisabledReason: mapErrorMessage("case_closed_read_only"),
            waitingForBroker: false,
            submitReceiptVisible: false,
            pageError: {
              code: "case_closed_read_only",
              message: mapErrorMessage("case_closed_read_only"),
              retryable: false,
              blocking: true,
            },
          });
          this.persistDraftSafe();
          return;
        }
        this.safePageSetData({
          submissionState: "uncertain",
          retryAvailable: true,
          submitDisabled: false,
          submitDisabledReason: "",
          submitReceiptVisible: false,
          pageError: {
            code: "timeout",
            message: "提交结果未确认，请重试。不会重复提交。",
            retryable: true,
            blocking: false,
          },
        });
        console.info("[slice1_submit_retry]", { reason: "uncertain_outcome" });
        this.persistDraftSafe();
        // Reconcile: if server already persisted, treat as success (idempotent retry path).
        try {
          const submittedItemId = internal.activeRequestItemId;
          const refreshed = await this.rehydrateAuthoritativeTask({ silent: true });
          if (refreshed && isSlice1CustomerFlow(refreshed)) {
            const view = mapSlice1CustomerView(refreshed);
            if (
              isRequestItemSubmitResolvedOnServer({
                submittedItemId,
                view,
              })
            ) {
              clearRequestItemDraft(internal.caseId, internal.requestId, submittedItemId);
              internal.commandId = "";
              internal.idempotencyKey = "";
              this.applyAuthoritativeTask(refreshed, { restoreDraft: true });
              const after = mapSlice1CustomerView(refreshed);
              if (after.waitingForBroker) {
                this.finishSubmitSuccess({ waitingForBroker: true, nextTask: refreshed });
              } else {
                this.safePageSetData({
                  submissionState: "idle",
                  retryAvailable: false,
                  pageError: EMPTY_TASK_ERROR,
                  submitDisabled: !String(after.nextAction?.request_item_id || "").trim(),
                  submitDisabledReason: "",
                });
                this.showSubmitReceipt();
              }
            }
          }
        } catch {
          // keep uncertain UI — retry reuses the same idempotency key
        }
      }
    } finally {
      // Keep lock only while navigating away after final success.
      if (!this.isBusy("navigating")) {
        internal.submitInFlight = false;
        this.setBusy("submitting", false);
      } else {
        internal.submitInFlight = false;
      }
    }
  },

  async handleSubmitResult(
    result: Slice1CommandResult,
    options?: { partialVehicleSave?: boolean },
  ) {
    const internal = ensureInternal(this);
    const outcome = String(result.outcome || "");
    if (outcome === "accepted" || outcome === "replayed") {
      const projection = result.customer_projection || extractSlice1Projection(this.data.task);
      const previousItemId = internal.activeRequestItemId;
      const previousRequestId = internal.requestId;
      const caseId = internal.caseId;
      const itemType = String(this.data.itemType || "");
      const preservedVehicleForm = {
        ...(this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM),
      } as ClaimVehicleFormFields;
      const preservedDraftValue = String(this.data.draftValue || "");

      let nextTask = this.data.task as CustomerTask;
      if (projection) {
        nextTask = applySlice1ProjectionToTask(nextTask || ({} as CustomerTask), projection);
        // Merge server key_facts when present on refreshed task payloads later.
        try {
          const app = getApp<IAppOption>();
          app.task = nextTask;
        } catch {
          // ignore — projection apply must still advance the page
        }
      } else {
        const refreshed = await this.rehydrateAuthoritativeTask({ silent: true });
        if (refreshed) nextTask = refreshed;
      }

      const view = mapSlice1CustomerView(nextTask);
      const stillSameItem =
        Boolean(previousItemId) &&
        String(view.nextAction?.request_item_id || "") === previousItemId;
      const partialKeepOpen =
        Boolean(options?.partialVehicleSave) ||
        (stillSameItem &&
          !view.waitingForBroker &&
          (itemType === "vehicle_information" || itemType === "vin"));

      if (partialKeepOpen) {
        internal.commandId = "";
        internal.idempotencyKey = "";
        internal.clientDraftId = newClientDraftId();
        internal.expectedCaseVersion = view.aggregateVersion;
        // Keep local fields; server authoritative facts hydrate on next full bootstrap.
        this.applyAuthoritativeTask(nextTask, { restoreDraft: false });
        const correction = isNeedsCorrection(
          ((nextTask.key_facts || {}) as Record<string, unknown>) || null,
        );
        this.safePageSetData({
          vehicleForm: preservedVehicleForm,
          draftValue: itemType === "vin" ? preservedDraftValue || preservedVehicleForm.vin : preservedDraftValue,
          submissionState: "idle",
          retryAvailable: false,
          submitDisabled: false,
          submitDisabledReason: "",
          validationMessage: correction ? CLAIM_VEHICLE_COPY.correction : "",
          fieldErrors: {},
          needsCorrection: correction,
          submitReceiptVisible: !correction,
          submitReceiptText: correction ? "" : SUBMIT_RECEIPT_COPY,
        });
        this.persistDraftSafe();
        console.info("[slice1_submit]", { outcome, partial: true, itemType, correction });
        return;
      }

      if (caseId && previousRequestId && previousItemId) {
        clearRequestItemDraft(caseId, previousRequestId, previousItemId);
      }
      internal.commandId = "";
      internal.idempotencyKey = "";
      internal.clientDraftId = newClientDraftId();

      const waiting = mapSlice1CustomerView(nextTask).waitingForBroker;
      console.info("[slice1_submit]", { outcome, waitingForBroker: waiting });

      if (waiting) {
        this.applyAuthoritativeTask(nextTask, { restoreDraft: false });
        this.finishSubmitSuccess({ waitingForBroker: true, nextTask });
        return;
      }

      this.applyAuthoritativeTask(nextTask, { restoreDraft: true });
      this.safePageSetData({
        submissionState: "idle",
        retryAvailable: false,
        submitDisabled: !String(mapSlice1CustomerView(nextTask).nextAction?.request_item_id || "").trim(),
        submitDisabledReason: "",
      });
      this.showSubmitReceipt();
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
    const vehicleMsg = mapVehicleServerError(code);
    const message = vehicleMsg || mapErrorMessage(code);
    const closed = code === "case_closed_read_only";
    this.restoreSubmitAfterFailure({
      retryAvailable: !closed,
      submitDisabled: closed,
      submitDisabledReason: closed ? message : "",
      validationMessage: closed ? "" : message || "提交未成功，请重试。",
      fieldErrors:
        code === "vin_invalid" || code === "invalid_vin"
          ? { vin: CLAIM_VEHICLE_COPY.invalidVin }
          : code === "vehicle_incomplete"
            ? { year: message, make: message, model: message }
            : {},
      pageError: {
        code,
        message: message || "提交未成功，请重试。",
        retryable: !closed,
        blocking: closed,
      },
    });
    this.persistDraftSafe();
  },

  onRetry() {
    void this.bootstrapPage({ ownerLoad: false, force: true });
  },

  async onLater() {
    const itemType = String(this.data.itemType || "");
    const form = (this.data.vehicleForm || EMPTY_CLAIM_VEHICLE_FORM) as ClaimVehicleFormFields;
    // vehicle_information: server partial save when any fields present, then leave.
    if (
      itemType === "vehicle_information" &&
      claimVehicleFormHasAnyValue(form) &&
      !this.data.waitingForBroker
    ) {
      await this.runSubmit({ reuseIdentity: false, partialVehicleSave: true });
      if (this.data.submissionState === "uncertain" || this.data.submissionState === "failed") {
        return;
      }
    } else {
      this.persistDraftSafe();
    }
    wx.navigateBack({ fail: () => wx.redirectTo({ url: "/pages/task-home/task-home" }) });
  },

  onBackHome() {
    // Waiting Broker lands on Case Status (not Task Home).
    this.goCaseStatusAfterSuccess();
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
