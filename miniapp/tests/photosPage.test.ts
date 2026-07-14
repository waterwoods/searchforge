import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import { ApiRequestError } from "../utils/request";
import type { CustomerTask } from "../types/task";

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
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...(behavior.methods || {}),
    ...page,
    ...overrides,
  };
  return ctx;
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
  CustomerTaskApi.uploadPhoto = async (_url, _path, _slot, options) => {
    uploadCalls += 1;
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
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.slots[0].uploaded, true);
  assert.equal(ctx.data.uploadStage, "上传完成");
  assert.ok(toasts.includes("上传完成"));
  assert.equal(timingLogs.length, 1);
  assert.equal(timingLogs[0][0], "[photo_upload_timing]");
  const record = timingLogs[0][1] as Record<string, unknown>;
  assert.equal(record.event, "upload_measurement_complete");
  assert.equal(record.client_build_id, "p20-photo-measurement-v1");
  assert.equal(record.api_profile, "qa");
  assert.equal(record.api_host, "https://fiqa-api-g7zatxrycq-uw.a.run.app");
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
  CustomerTaskApi.uploadPhoto = async () => {
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
  assert.equal(ctx.data.busy.uploading, false);
  assert.equal(ctx.data.slots[0].canRetry, true);
  assert.equal(ctx.data.slots[0].canRemove, true);
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
  CustomerTaskApi.uploadPhoto = async (_url, localPath) => {
    uploadFilePath = localPath;
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

  CustomerTaskApi.getUploadTaskInfo = originalGetUploadTaskInfo;
  CustomerTaskApi.uploadPhoto = originalUploadPhoto;
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

test("onShow hydrates slots from shared loadTask result", async () => {
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
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.photoCount, 1);
  assert.equal(ctx.data.slots[0].uploaded, true);
  assert.equal(ctx.data.slots[1].uploaded, false);
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
