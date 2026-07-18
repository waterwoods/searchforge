import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import { ApiRequestError } from "../utils/request";
import { resetApiHealthCache } from "../utils/apiHealth";
import type { CustomerTask } from "../types/task";
import { setPhotoReadBackConfigForTests } from "../utils/photoReadBack";

installMiniProgramGlobals();

let cachedPage: CapturedPageOptions | null = null;

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

async function loadPhotosPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/photos/photos");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "photos", "review", "done"],
    current_step: "photos",
    completed_count: 2,
    step_total: 4,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {},
    missing_info: [],
    upload_url: "https://example.com/h5t1.upload_token",
    photo_count: 0,
    task_contract: {
      contract_version: "0",
      task_id: "task_1",
      task_type: "claim_intake",
      task_status: "collecting",
      title: "我的事故资料",
      instruction: "",
      progress: { completed: 2, total: 4 },
      sections: [],
      fields: {},
      missing_items: [],
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 0 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
      next_action: { type: "go_to_section", target: "photos", label: "继续" },
      review_ready: false,
      submit_ready: false,
      revision: 1,
      timestamps: { updated_at: "2026-07-14T00:00:00Z" },
      capabilities: { voice: false, scan: false },
      branding: { office_name: "陈总办公室", safety_copy: "" },
      error: null,
    },
    ...overrides,
  };
}

function createPageContext(page: CapturedPageOptions, overrides?: Record<string, unknown>) {
  const behavior = (page.behaviors?.[0] || {}) as {
    data?: Record<string, unknown>;
    methods?: Record<string, (...args: any[]) => any>;
  };
  const data = {
    ...(behavior.data || {}),
    ...(page.data || {}),
  } as Record<string, any>;
  const ctx: Record<string, any> = {
    route: "/pages/photos/photos",
    ...(behavior.methods || {}),
    ...page,
    ...overrides,
  };
  ctx.data = overrides?.data || data;
  if (!overrides?.setData) {
    ctx.setData = function setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    };
  }
  return ctx;
}

function flushAsync(): Promise<void> {
  return new Promise((resolve) => setImmediate(resolve));
}

function flushTimer(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function createTrackedPageContext(page: CapturedPageOptions, overrides?: Record<string, unknown>) {
  const setDataPatches: Array<Record<string, unknown>> = [];
  let setDataCallsInsideCallback = 0;
  let insideSetDataCallback = false;
  const ctx = createPageContext(page, {
    ...overrides,
    setData(patch: Record<string, unknown>, callback?: () => void) {
      if (insideSetDataCallback) {
        setDataCallsInsideCallback += 1;
      }
      setDataPatches.push(patch);
      Object.assign(this.data, patch);
      if (callback) {
        insideSetDataCallback = true;
        try {
          callback();
        } finally {
          insideSetDataCallback = false;
        }
      }
    },
  });
  return {
    ctx,
    setDataPatches,
    getSetDataCallsInsideCallback: () => setDataCallsInsideCallback,
  };
}

test("upload success confirms via read-back and clears busy uploading", async () => {
  const page = await loadPhotosPage();
  const toasts: string[] = [];
  const timingLogs: unknown[][] = [];
  const originalInfo = console.info;
  console.info = (...args: unknown[]) => timingLogs.push(args);
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);
  (globalThis as Record<string, unknown>).getApp = () => ({ taskToken: "h5t1.valid" });
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/p1.jpg", size: 1234 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  let uploadCalls = 0;
  let uploadIntentId = "";
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadCalls += 1;
    uploadIntentId = String(options?.uploadIntentId || "");
    options?.onProgress?.(45);
    options?.onProgress?.(100);
    return {
      upload_measurement: {
        request_id: "request-safe-id",
        server_duration_ms: 17,
      },
    };
  };

  const initialTask = buildTask();
  const readBackTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...initialTask.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task: initialTask,
      uploadUrl: initialTask.upload_url,
      photoCount: 0,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(uploadCalls, 1);
  assert.match(uploadIntentId, /^upl_/);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.slots[0].uploaded, false);
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(ctx.data.slots[0].uploadIntentId, "");
  assert.equal(ctx.data.slots[0].canRetry, false);
  assert.equal(ctx.data.slots[0].localPath, "/tmp/p1.jpg");
  assert.equal(ctx.data.slots[0].statusText, "已确认");
  assert.equal(ctx.data.uploadStage, "上传完成");
  assert.ok(toasts.includes("上传完成"));
  assert.equal(timingLogs.length, 1);
  assert.equal(timingLogs[0][0], "[photo_upload_timing]");
  const record = timingLogs[0][1] as Record<string, unknown>;
  assert.equal(record.event, "upload_measurement_complete");
  assert.equal(record.client_build_id, "p20-photo-measurement-v1");
  assert.equal(record.api_profile, "qa");
  assert.equal(typeof record.api_host, "string");
  assert.equal(record.original_bytes, 1234);
  assert.equal(record.compressed_bytes, 1234);
  assert.equal(record.compression_ms, 0);
  assert.equal(record.compression_applied, false);
  assert.equal(record.server_reported_ms, 17);
  assert.equal(record.server_request_id, "request-safe-id");
  assert.deepEqual(record.progress_milestones, [0, 45, 100]);
  assert.equal(typeof record.upload_ms, "number");
  assert.equal(typeof record.readback_ms, "number");
  assert.equal(typeof record.total_ms, "number");
  assert.equal(JSON.stringify(timingLogs).includes("upload_token"), false);
  assert.equal(JSON.stringify(timingLogs).includes("/tmp/p1.jpg"), false);
  assert.equal(JSON.stringify(timingLogs).includes("upl_"), false);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
  console.info = originalInfo;
});

test("upload failure shows error and enables retry", async () => {
  const page = await loadPhotosPage();
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/fail.jpg", size: 2048 }] });

  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  let uploadIntentId = "";
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadIntentId = String(options?.uploadIntentId || "");
    throw new ApiRequestError("network_error");
  };

  const task = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.match(uploadIntentId, /^upl_/);
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.slots[0].canRetry, true);
  assert.equal(ctx.data.slots[0].canRemove, true);
  assert.equal(ctx.data.slots[0].uploadIntentId, uploadIntentId);
  assert.equal(ctx.data.uploadStage, "上传失败，请重试");
  assert.ok(String(ctx.data.slots[0].error).length > 0);

  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
});

test("retry uses existing local photo without repicking", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) => {
    chooseCalls += 1;
    success?.({ tempFiles: [{ tempFilePath: "/tmp/new.jpg", size: 512 }] });
  };

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  let uploadFilePath = "";
  let uploadIntentId = "";
  CustomerTaskApi.uploadPhoto = async (_url, localPath, _slot, options) => {
    uploadFilePath = localPath;
    uploadIntentId = String(options?.uploadIntentId || "");
    return {};
  };

  const task = buildTask();
  const readBackTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...task.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 0,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "/tmp/existing.jpg",
          uploadIntentId: "upl_existing_retry",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "上传失败",
          canRetry: true,
          canRemove: true,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onRetrySlot.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.equal(uploadFilePath, "/tmp/existing.jpg");
  assert.equal(uploadIntentId, "upl_existing_retry");
  assert.equal(ctx.data.slots[0].uploaded, false);
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(ctx.data.slots[0].canRetry, false);
  assert.equal(ctx.data.slots[0].localPath, "/tmp/existing.jpg");
  assert.equal(ctx.data.slots[0].uploadIntentId, "");
  assert.equal(ctx.data.slots[0].statusText, "已确认");

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("different new photo gets a different upload_intent_id", async () => {
  const page = await loadPhotosPage();
  const timingLogs: unknown[][] = [];
  const originalInfo = console.info;
  console.info = (...args: unknown[]) => timingLogs.push(args);
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) => {
    chooseCalls += 1;
    success?.({ tempFiles: [{ tempFilePath: `/tmp/new-${chooseCalls}.jpg`, size: 512 }] });
  };

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  const uploadIntentIds: string[] = [];
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadIntentIds.push(String(options?.uploadIntentId || ""));
    throw new ApiRequestError("network_error");
  };

  const task = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 2);
  assert.equal(uploadIntentIds.length, 2);
  assert.match(uploadIntentIds[0], /^upl_/);
  assert.match(uploadIntentIds[1], /^upl_/);
  assert.notEqual(uploadIntentIds[0], uploadIntentIds[1]);
  assert.equal(ctx.data.slots[0].uploadIntentId, uploadIntentIds[1]);
  assert.equal(JSON.stringify(timingLogs).includes("upload_token"), false);
  assert.equal(JSON.stringify(timingLogs).includes("/tmp/new-"), false);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
  console.info = originalInfo;
});

test("duplicate upload is blocked while busy uploading", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) => {
    chooseCalls += 1;
    success?.({ tempFiles: [{ tempFilePath: "/tmp/new.jpg", size: 512 }] });
  };
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  let uploadCalls = 0;
  CustomerTaskApi.uploadPhoto = async () => {
    uploadCalls += 1;
    return {};
  };

  const task = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      busy: {
        ...page.data.busy,
        uploading: true,
      },
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.equal(uploadCalls, 0);

  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("completed upload cannot retry", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = () => {
    chooseCalls += 1;
  };
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  let uploadCalls = 0;
  CustomerTaskApi.uploadPhoto = async () => {
    uploadCalls += 1;
    return {};
  };

  const task = buildTask({ photo_count: 1 });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploadIntentId: "",
          uploaded: true,
          uploading: false,
          progress: 100,
          error: "",
          canRetry: true,
          canRemove: false,
          requiredHint: "已满足要求",
          statusText: "已上传并确认",
        },
      ],
    },
  });

  await page.onRetrySlot.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.equal(uploadCalls, 0);
  assert.equal(ctx.data.slots[0].uploaded, true);

  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("confirmed category still opens picker for another photo", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) => {
    chooseCalls += 1;
    success?.({ tempFiles: [{ tempFilePath: "/tmp/second.jpg", size: 900 }] });
  };

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  let uploadIntentId = "";
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadIntentId = String(options?.uploadIntentId || "");
    options?.onProgress?.(100);
    return {};
  };

  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });
  const readBackTask = buildTask({
    photo_count: 2,
    task_contract: {
      ...task.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 2 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 1,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploadIntentId: "",
          uploaded: false,
          requirementMet: true,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已满足要求 · 可添加更多",
          statusText: "已上传 1 张",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 1);
  assert.match(uploadIntentId, /^upl_/);
  assert.equal(ctx.data.photoCount, 2);
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(ctx.data.slots[0].uploaded, false);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("upload_intent_id API payload matches live multipart contract", async () => {
  resetApiHealthCache();
  installMiniProgramGlobals();
  const wxGlobal = (globalThis as Record<string, any>).wx;
  const originalRequest = wxGlobal.request;
  const originalUploadFile = wxGlobal.uploadFile;
  let capturedUpload: Record<string, any> | null = null;
  wxGlobal.request = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ statusCode: 200, data: { ok: true } });
  wxGlobal.uploadFile = (opts: Record<string, any>) => {
    capturedUpload = opts;
    opts.success?.({ statusCode: 200, data: "{}" });
    return { onProgressUpdate: () => undefined };
  };

  await CustomerTaskApi.uploadPhoto(
    "https://example.com/task/upload/h5t1.upload_token",
    "/tmp/api-contract.jpg",
    "customer_damage_photo",
    { uploadIntentId: "upl_contract_123" },
  );

  assert.deepEqual(capturedUpload?.formData, {
    slot: "customer_damage_photo",
    upload_intent_id: "upl_contract_123",
  });
  assert.equal(JSON.stringify(capturedUpload).includes("x-upload-intent-id"), false);

  wxGlobal.request = originalRequest;
  wxGlobal.uploadFile = originalUploadFile;
  resetApiHealthCache();
});

test("first entry onLoad starts exactly one initialization request", async () => {
  const page = await loadPhotosPage();
  const task = buildTask();
  let resolveLoad: (task: CustomerTask) => void = () => undefined;
  const loadGate = new Promise<CustomerTask>((resolve) => {
    resolveLoad = resolve;
  });
  let fetchCalls = 0;
  const { ctx } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      fetchCalls += 1;
      return loadGate;
    },
  });

  page.onLoad.call(ctx);
  await flushAsync();
  assert.equal(fetchCalls, 1);
  resolveLoad(task);
  await flushAsync();
  assert.equal(ctx.data.pageState, "ready");
});

test("onShow immediately after onLoad does not start a second initialization request", async () => {
  const page = await loadPhotosPage();
  const task = buildTask();
  let resolveLoad: (task: CustomerTask) => void = () => undefined;
  const loadGate = new Promise<CustomerTask>((resolve) => {
    resolveLoad = resolve;
  });
  let fetchCalls = 0;
  const { ctx } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      fetchCalls += 1;
      return loadGate;
    },
  });

  page.onLoad.call(ctx);
  const show = page.onShow.call(ctx);
  await flushAsync();
  assert.equal(fetchCalls, 1);
  resolveLoad(task);
  await show;
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(fetchCalls, 1);
});

test("terminal first render uses one ready transition and no nested setData", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({ photo_count: 1 });
  const { ctx, setDataPatches, getSetDataCallsInsideCallback } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => task,
  });

  page.onLoad.call(ctx);
  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(setDataPatches.length, 1);
  assert.equal(setDataPatches[0].pageState, "ready");
  assert.equal(getSetDataCallsInsideCallback(), 0);
});

test("timeout and late success cannot both update UI", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({ photo_count: 1 });
  let resolveLoad: (task: CustomerTask) => void = () => undefined;
  const loadGate = new Promise<CustomerTask>((resolve) => {
    resolveLoad = resolve;
  });
  const { ctx, setDataPatches } = createTrackedPageContext(page, {
    __photoInitialLoadTimeoutMs: 5,
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => loadGate,
  });

  await page.startPhotoPageRefresh.call(ctx, "test_timeout");
  assert.equal(ctx.data.pageState, "recoverable_error");
  assert.equal(setDataPatches.length, 1);
  resolveLoad(task);
  await flushAsync();
  assert.equal(ctx.data.pageState, "recoverable_error");
  assert.equal(setDataPatches.length, 1);
});

test("stale initialization request never calls setData", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({ photo_count: 1 });
  let resolveLoad: (task: CustomerTask) => void = () => undefined;
  const loadGate = new Promise<CustomerTask>((resolve) => {
    resolveLoad = resolve;
  });
  const { ctx, setDataPatches } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => loadGate,
  });

  const staleLoad = page.startPhotoPageRefresh.call(ctx, "stale");
  await flushAsync();
  page.onHide.call(ctx);
  resolveLoad(task);
  await staleLoad;
  assert.equal(setDataPatches.length, 0);
});

test("pending reconciliation begins only after ready is rendered", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
      ],
    },
  });
  let stateSeenByReconcile = "";
  const { ctx, setDataPatches } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => task,
    reconcilePendingUploads() {
      stateSeenByReconcile = this.data.pageState;
    },
  });
  page.registerPendingUpload.call(ctx, {
    slotKey: "customer_damage_photo",
    uploadIntentId: "upl_waiting_confirm",
    beforeCount: 0,
    localPath: "/tmp/private.jpg",
  });

  await page.startPhotoPageRefresh.call(ctx, "pending_ready_order");
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(stateSeenByReconcile, "");
  assert.equal(setDataPatches[0].pageState, "ready");
  await flushTimer();
  assert.equal(stateSeenByReconcile, "ready");
});

test("second onShow performs one guarded refresh", async () => {
  const page = await loadPhotosPage();
  let fetchCalls = 0;
  const { ctx } = createTrackedPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      fetchCalls += 1;
      return buildTask({ photo_count: fetchCalls });
    },
  });

  page.onLoad.call(ctx);
  await page.onShow.call(ctx);
  assert.equal(fetchCalls, 1);
  await page.onShow.call(ctx);
  assert.equal(fetchCalls, 2);
  assert.equal(ctx.data.photoCount, 2);
});

test("photo page render-bound data has no undefined fields", async () => {
  const page = await loadPhotosPage();
  const seen: string[] = [];
  const walk = (value: unknown, path: string) => {
    if (value === undefined) {
      seen.push(path);
      return;
    }
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value)) {
      value.forEach((item, index) => walk(item, `${path}[${index}]`));
      return;
    }
    for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
      walk(nested, path ? `${path}.${key}` : key);
    }
  };

  walk(page.data, "");
  assert.deepEqual(seen, []);
});

test("onShow hydrates slots from startup fetch result", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots[0].uploaded, false);
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(ctx.data.slots[1].uploaded, false);
});

test("second photo in category uses a new upload_intent_id", async () => {
  const page = await loadPhotosPage();
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/another.jpg", size: 700 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  const uploadIntentIds: string[] = [];
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadIntentIds.push(String(options?.uploadIntentId || ""));
    options?.onProgress?.(100);
    return {};
  };

  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
      ],
    },
  });
  const readBackTask = buildTask({
    photo_count: 2,
    task_contract: {
      ...task.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 2 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 1,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          requirementMet: true,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已满足要求 · 可添加更多",
          statusText: "已上传 1 张",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(uploadIntentIds.length, 1);
  assert.match(uploadIntentIds[0], /^upl_/);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("20-photo limit blocks new upload with friendly copy", async () => {
  const page = await loadPhotosPage();
  const toasts: string[] = [];
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);
  (globalThis as Record<string, any>).wx.chooseMedia = () => {
    chooseCalls += 1;
  };

  const task = buildTask({ photo_count: 20 });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 20,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          requirementMet: true,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已满足要求 · 可添加更多",
          statusText: "已上传 1 张",
        },
      ],
    },
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.ok(toasts.includes("最多上传 20 张照片"));
});

test("post-submit category can still append when under limit", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) => {
    chooseCalls += 1;
    success?.({ tempFiles: [{ tempFilePath: "/tmp/post-submit.jpg", size: 640 }] });
  };

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    options?.onProgress?.(100);
    return {};
  };

  const task = buildTask({
    submitted: true,
    phase: "broker_review",
    photo_count: 2,
    task_contract: {
      ...buildTask().task_contract!,
      task_status: "submitted",
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 1 },
      ],
    },
  });
  const readBackTask = buildTask({
    ...task,
    photo_count: 3,
    task_contract: {
      ...task.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 2 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 1 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 2,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          requirementMet: true,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已满足要求 · 可添加更多",
          statusText: "已上传 1 张",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 1);
  assert.equal(ctx.data.photoCount, 3);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("no duplicate attachment on retry of confirmed item", async () => {
  const page = await loadPhotosPage();
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.chooseMedia = () => {
    chooseCalls += 1;
  };
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  let uploadCalls = 0;
  CustomerTaskApi.uploadPhoto = async () => {
    uploadCalls += 1;
    return {};
  };

  const task = buildTask({ photo_count: 1 });
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploadIntentId: "",
          uploaded: false,
          requirementMet: true,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已满足要求 · 可添加更多",
          statusText: "已上传 1 张",
        },
      ],
    },
  });

  await page.onRetrySlot.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.equal(uploadCalls, 0);

  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("return to task home falls back to redirect when navigateBack fails", async () => {
  const page = await loadPhotosPage();
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.navigateBack = ({ fail }: { fail?: () => void }) => fail?.();
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => redirects.push(url);

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: {
        ...page.data.busy,
        uploading: false,
      },
    },
  });
  page.onBackHome.call(ctx);
  assert.deepEqual(redirects, ["/pages/task-home/task-home"]);
});

test("contact broker opens shared guidance modal, not hub escape", async () => {
  const page = await loadPhotosPage();
  const modals: Array<{ title: string; content: string }> = [];
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.showModal = (opts: {
    title: string;
    content: string;
  }) => {
    modals.push(opts);
  };
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) =>
    redirects.push(url);
  (globalThis as Record<string, any>).wx.navigateBack = () => redirects.push("back");

  page.onContactBroker.call(createPageContext(page));
  assert.equal(modals.length, 1);
  assert.equal(modals[0].title, "联系陈总");
  assert.match(modals[0].content, /返回微信/);
  assert.deepEqual(redirects, []);
});

const DEFAULT_READ_BACK_CONFIG = {
  maxAttempts: 5,
  retryMs: 1_500,
  timeoutMs: 12_000,
};

function resetReadBackConfig() {
  setPhotoReadBackConfigForTests(DEFAULT_READ_BACK_CONFIG);
}

test("upload 200 clears busy before delayed read-back confirms", async () => {
  resetReadBackConfig();
  const page = await loadPhotosPage();
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/delayed.jpg", size: 800 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    options?.onProgress?.(100);
    return { upload_measurement: { request_id: "req-delayed", server_duration_ms: 22 } };
  };

  const initialTask = buildTask();
  const readBackTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...initialTask.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });

  let releaseReadBack: () => void = () => undefined;
  const readBackGate = new Promise<void>((resolve) => {
    releaseReadBack = resolve;
  });
  let loadTaskCalls = 0;

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task: initialTask,
      uploadUrl: initialTask.upload_url,
      photoCount: 0,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    loadTask: async () => {
      loadTaskCalls += 1;
      await readBackGate;
      return readBackTask;
    },
  });

  const uploadPromise = page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.uploadStage, "已上传，正在确认");
  assert.equal(ctx.data.slots[0].uploading, false);
  assert.equal(ctx.data.slots[0].progress, 100);
  assert.equal(loadTaskCalls, 1);

  releaseReadBack();
  await uploadPromise;
  assert.equal(ctx.data.uploadStage, "上传完成");
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots[0].requirementMet, true);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("upload 200 + read-back timeout keeps confirming state without false failure", async () => {
  resetReadBackConfig();
  setPhotoReadBackConfigForTests({ maxAttempts: 2, retryMs: 1, timeoutMs: 5 });
  const page = await loadPhotosPage();
  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/timeout.jpg", size: 640 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    options?.onProgress?.(100);
    return {};
  };

  const task = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      photoCount: 0,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    loadTask: async () => task,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.uploadStage, "已上传，正在确认");
  assert.equal(ctx.data.slots[0].error, "");
  assert.equal(ctx.data.slots[0].canRetry, false);
  assert.ok(!toasts.includes("上传未确认，请重试"));

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
  resetReadBackConfig();
});

test("onShow reconciles pending upload after backgrounding", async () => {
  resetReadBackConfig();
  setPhotoReadBackConfigForTests({ maxAttempts: 1, retryMs: 1, timeoutMs: 1 });
  const page = await loadPhotosPage();
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/bg.jpg", size: 512 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    options?.onProgress?.(100);
    return {};
  };

  const initialTask = buildTask();
  const confirmedTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...initialTask.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task: initialTask,
      uploadUrl: initialTask.upload_url,
      photoCount: 0,
      busy: { ...page.data.busy, uploading: true },
      uploadStage: "已上传，正在确认",
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "/tmp/bg.jpg",
          uploadIntentId: "upl_bg_pending",
          uploaded: false,
          uploading: true,
          progress: 100,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => confirmedTask,
  });

  page.registerPendingUpload.call(ctx, {
    slotKey: "customer_damage_photo",
    uploadIntentId: "upl_bg_pending",
    beforeCount: 0,
    localPath: "/tmp/bg.jpg",
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.uploadStage, "已上传，正在确认");
  await flushTimer();
  assert.equal(ctx.data.uploadStage, "上传完成");
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(ctx.data.slots[0].uploading, false);
  assert.equal(ctx.data.slots[0].localPath, "/tmp/bg.jpg");
  assert.equal(ctx.data.slots[0].statusText, "已确认");
  assert.equal(page.hasPendingUploadForSlot.call(ctx, "customer_damage_photo"), false);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
  resetReadBackConfig();
});

test("pending upload_intent_id blocks duplicate upload", async () => {
  resetReadBackConfig();
  const page = await loadPhotosPage();
  const toasts: string[] = [];
  let chooseCalls = 0;
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);
  (globalThis as Record<string, any>).wx.chooseMedia = () => {
    chooseCalls += 1;
  };

  const task = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task,
      uploadUrl: task.upload_url,
      busy: { ...page.data.busy, uploading: false },
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "/tmp/pending.jpg",
          uploadIntentId: "upl_pending_block",
          uploaded: false,
          uploading: false,
          progress: 100,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
  });
  page.registerPendingUpload.call(ctx, {
    slotKey: "customer_damage_photo",
    uploadIntentId: "upl_pending_block",
    beforeCount: 0,
    localPath: "/tmp/pending.jpg",
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(chooseCalls, 0);
  assert.ok(toasts.includes("请等待当前上传确认"));
});

test("server-confirmed item clears pending and completes", async () => {
  resetReadBackConfig();
  const page = await loadPhotosPage();
  (globalThis as Record<string, any>).wx.chooseMedia = ({ success }: { success?: (res: unknown) => void }) =>
    success?.({ tempFiles: [{ tempFilePath: "/tmp/confirmed.jpg", size: 700 }] });

  const originalGetUploadTaskInfo = CustomerTaskApi.getUploadTaskInfo;
  const originalUploadPhoto = CustomerTaskApi.uploadPhoto;
  CustomerTaskApi.getUploadTaskInfo = async () => ({ lane: "claim", flow: "claim", case_id: "1" });
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    options?.onProgress?.(100);
    return { upload_measurement: { request_id: "req-ok", server_duration_ms: 12 } };
  };

  const initialTask = buildTask();
  const readBackTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...initialTask.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
    },
  });

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task: initialTask,
      uploadUrl: initialTask.upload_url,
      photoCount: 0,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: false,
          uploading: false,
          progress: 0,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "还需 1 张",
          statusText: "已上传 0/1",
        },
      ],
    },
    loadTask: async () => readBackTask,
  });

  await page.onAddPhoto.call(ctx, { detail: { slotKey: "customer_damage_photo" } });
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.uploadStage, "上传完成");
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(page.hasPendingUploadForSlot.call(ctx, "customer_damage_photo"), false);

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
});

test("tapping supplement photos route opens gallery via onShow", async () => {
  const page = await loadPhotosPage();
  const { CustomerTaskApi } = await import("../services/taskApi");
  const originalGetTask = CustomerTaskApi.getTask;
  const task = buildTask({
    submitted: true,
    photo_count: 2,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 2 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 1 },
      ],
    },
  });
  CustomerTaskApi.getTask = async () => task;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
  });
  await page.onShow.call(ctx);
  CustomerTaskApi.getTask = originalGetTask;
  assert.equal(ctx.data.slots.length, 2);
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.slots[0].requirementMet, true);
});

test("fresh case with no photos renders fallback slots", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({ photo_count: 0, task_contract: undefined });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => task,
  });
  await page.onShow.call(ctx);
  assert.equal(ctx.data.slots.length, 2);
  assert.equal(ctx.data.busy.loading, false);
});

test("malformed stale slots and uploadStage do not crash onShow", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({
    photo_count: 2,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 2 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 1 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      slots: undefined,
      uploadStage: undefined,
    },
    fetchTaskForPhotoPage: async () => task,
  });
  await page.onShow.call(ctx);
  assert.ok(Array.isArray(ctx.data.slots));
  assert.equal(ctx.data.slots.length, 2);
  assert.equal(ctx.data.uploadStage, "");
});

test("onShow before onLoad defaults do not crash", async () => {
  const page = await loadPhotosPage();
  const task = buildTask();
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      slots: undefined,
      uploadStage: undefined,
    },
    fetchTaskForPhotoPage: async () => task,
  });
  await page.onShow.call(ctx);
  assert.ok(Array.isArray(ctx.data.slots));
});

test("recoverable loadTask failure shows error UI not blank page", async () => {
  const page = await loadPhotosPage();
  const { CustomerTaskApi } = await import("../services/taskApi");
  const { ApiRequestError } = await import("../utils/request");
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => {
    throw new ApiRequestError("network_error");
  };
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      slots: undefined,
    },
  });
  await page.onShow.call(ctx);
  CustomerTaskApi.getTask = originalGetTask;
  assert.equal(ctx.data.busy.loading, false);
  assert.ok(ctx.data.errorState.message.length > 0);
  assert.ok(Array.isArray(ctx.data.slots));
});

test("legacy completed slot shape hydrates requirementMet", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      slots: [
        {
          key: "customer_damage_photo",
          label: "车辆受损位置",
          localPath: "",
          uploaded: true,
          uploading: false,
          progress: 100,
          error: "",
          canRetry: false,
          canRemove: false,
          requiredHint: "已确认",
          statusText: "已上传并确认",
        },
      ],
    },
    fetchTaskForPhotoPage: async () => task,
  });
  await page.onShow.call(ctx);
  assert.equal(ctx.data.slots[0].requirementMet, true);
});

test("initial task GET success exits initializing and renders gallery", async () => {
  const page = await loadPhotosPage();
  const task = buildTask({
    photo_count: 1,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
      ],
    },
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots[0].requirementMet, true);
});

test("task response with newly uploaded photo renders before pending reconciliation", async () => {
  const page = await loadPhotosPage();
  const initialTask = buildTask();
  const readBackTask = buildTask({
    photo_count: 1,
    task_contract: {
      ...initialTask.task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 1 },
      ],
    },
  });
  let stateSeenByReconcile = "";
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => readBackTask,
    reconcilePendingUploads() {
      stateSeenByReconcile = this.data.pageState;
    },
  });
  page.registerPendingUpload.call(ctx, {
    slotKey: "customer_damage_photo",
    uploadIntentId: "upl_waiting_confirm",
    beforeCount: 0,
    localPath: "/tmp/private.jpg",
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots[0].requirementMet, true);
  assert.equal(stateSeenByReconcile, "");
  await flushTimer();
  assert.equal(stateSeenByReconcile, "ready");
});

test("rejected task GET reaches recoverable error and clears loading", async () => {
  const page = await loadPhotosPage();
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      throw new ApiRequestError("network_error");
    },
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "recoverable_error");
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.errorState.retryable, true);
  assert.match(ctx.data.errorState.message, /暂时无法刷新/);
});

test("hung task GET times out and exits full-page loading", async () => {
  const page = await loadPhotosPage();
  const ctx = createPageContext(page, {
    __photoInitialLoadTimeoutMs: 5,
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => new Promise<CustomerTask | null>(() => undefined),
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "recoverable_error");
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.errorState.code, "task_load_timeout");
});

test("active task response is shared instead of starting forced overlap", async () => {
  const page = await loadPhotosPage();
  const olderTask = buildTask({ photo_count: 1 });
  let resolveOlder: (task: CustomerTask) => void = () => undefined;
  const olderGate = new Promise<CustomerTask>((resolve) => {
    resolveOlder = resolve;
  });
  let calls = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      calls += 1;
      return olderGate;
    },
  });

  const firstLoad = page.startPhotoPageRefresh.call(ctx, "first");
  await flushAsync();
  const forcedRetry = page.startPhotoPageRefresh.call(ctx, "retry");
  await flushAsync();
  assert.equal(calls, 1);
  resolveOlder(olderTask);
  await Promise.all([firstLoad, forcedRetry]);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(ctx.data.photoCount, 1);
});

test("overlapping onShow calls share one initialization request", async () => {
  const page = await loadPhotosPage();
  const task = buildTask();
  let resolveLoad: (task: CustomerTask) => void = () => undefined;
  const loadGate = new Promise<CustomerTask>((resolve) => {
    resolveLoad = resolve;
  });
  let loadCalls = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      loadCalls += 1;
      return loadGate;
    },
  });

  const first = page.onShow.call(ctx);
  const second = page.onShow.call(ctx);
  await flushAsync();
  assert.equal(loadCalls, 1);
  resolveLoad(task);
  await Promise.all([first, second]);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(ctx.data.busy.loading, false);
});

test("backgrounded load is ignored and foreground refresh wins", async () => {
  const page = await loadPhotosPage();
  const olderTask = buildTask({ photo_count: 1 });
  const foregroundTask = buildTask({
    photo_count: 3,
    task_contract: {
      ...buildTask().task_contract!,
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 3 },
      ],
    },
  });
  let resolveOlder: (task: CustomerTask) => void = () => undefined;
  const olderGate = new Promise<CustomerTask>((resolve) => {
    resolveOlder = resolve;
  });
  let calls = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    fetchTaskForPhotoPage: async () => {
      calls += 1;
      if (calls === 1) return olderGate;
      return foregroundTask;
    },
  });

  const backgroundedLoad = page.onShow.call(ctx);
  await flushAsync();
  page.onHide.call(ctx);
  resolveOlder(olderTask);
  await backgroundedLoad;
  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "ready");
  assert.equal(ctx.data.photoCount, 3);
});

test("existing gallery remains visible during refresh failure", async () => {
  const page = await loadPhotosPage();
  const existingTask = buildTask({ photo_count: 1 });
  const existingSlots = [
    {
      key: "customer_damage_photo",
      label: "车辆受损位置",
      localPath: "",
      uploaded: false,
      requirementMet: true,
      uploading: false,
      progress: 0,
      error: "",
      canRetry: false,
      canRemove: false,
      requiredHint: "已满足要求 · 可添加更多",
      statusText: "已上传 1 张",
    },
  ];
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      pageState: "ready",
      task: existingTask,
      photoCount: 1,
      slots: existingSlots,
      busy: { ...page.data.busy, loading: false },
    },
    fetchTaskForPhotoPage: async () => {
      throw new ApiRequestError("network_error");
    },
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.pageState, "recoverable_error");
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots, existingSlots);
});
