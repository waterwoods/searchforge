import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import type { CustomerTask, Slice1Projection, TaskContractV0 } from "../types/task";
import { REQUEST_ITEM_ROUTE } from "../utils/slice1Customer";
import {
  createLoadFlightState,
  runSingleFlightLoad,
} from "../utils/slice1Lifecycle";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadReceiptPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/receipt/receipt");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function buildSlice1Projection(overrides?: Partial<Slice1Projection>): Slice1Projection {
  return {
    case_id: "case_1",
    workflow_state: "broker_more_requested",
    aggregate_version: 2,
    customer_next_action: {
      action_type: "provide_fact",
      request_id: "req_1",
      request_item_id: "item_1",
      title: "请提供 VIN",
      instructions: "请填写车辆 VIN",
      required_input: "vin",
      status: "active",
      ordering: { position: 1, total: 1 },
      allowed_actions: ["submit_request_item"],
      version: 2,
      last_updated_at: "2026-07-15T00:00:00Z",
    },
    broker_next_action: {
      action_type: "wait_for_customer_item",
      status: "waiting_for_customer",
      request_id: "req_1",
      version: 2,
    },
    open_request: {
      request_id: "req_1",
      status: "open",
      reason: "QA",
      active_item: {
        request_item_id: "item_1",
        request_id: "req_1",
        item_type: "vin",
        label: "VIN",
        instructions: "请填写车辆 VIN",
        required: true,
        position: 1,
        status: "active",
        actionable: true,
      },
      queued_items: [],
      items: [
        {
          request_item_id: "item_1",
          request_id: "req_1",
          item_type: "vin",
          label: "VIN",
          instructions: "请填写车辆 VIN",
          required: true,
          position: 1,
          status: "active",
          actionable: true,
        },
      ],
      progress: { satisfied: 0, total: 1, remaining: 1 },
    },
    queued_request_items: [],
    request_progress: { satisfied: 0, total: 1, remaining: 1 },
    server_timestamp: "2026-07-15T00:00:00Z",
    latest_events: [],
    ...overrides,
  };
}

function buildContract(overrides?: Partial<TaskContractV0>): TaskContractV0 {
  return {
    contract_version: "0",
    task_id: "task_1",
    task_type: "claim_intake",
    task_status: "submitted",
    title: "我的事故资料",
    instruction: "资料已提交",
    progress: { completed: 4, total: 4 },
    sections: [],
    fields: {},
    missing_items: [],
    evidence_requirements: [],
    next_action: { type: "view_status", label: "查看状态" },
    review_ready: true,
    submit_ready: false,
    revision: 2,
    timestamps: { updated_at: "2026-07-14T18:30:00.000Z" },
    capabilities: { voice: false, scan: false },
    branding: { office_name: "陈总办公室", safety_copy: "安全文案" },
    error: null,
    ...overrides,
  };
}

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "story", "basics", "photos", "review", "done"],
    current_step: "done",
    completed_count: 5,
    step_total: 5,
    submitted: true,
    phase: "submitted",
    key_facts: {
      accident_description: "我在红灯前被追尾。",
    },
    missing_info: [],
    photo_count: 2,
    completion_summary: {
      title: "资料已提交",
      message: "陈总会尽快查看您的资料。",
      received: ["事故经过", "事故照片"],
      missing: [],
      next_step: "请耐心等待陈总回复",
      disclaimer: "这只是资料收集，不代表已向保险公司正式报案。",
    },
    dashboard_summary: {
      title: "我的事故资料",
      subtitle: "已提交",
      status: "已提交",
      received: ["事故经过", "事故照片"],
      missing: [],
      next_action: "等待陈总查看",
      primary_cta: "查看提交结果",
      secondary_cta: "",
      submitted_supplement_allowed: false,
      warning: "",
    },
    task_contract: buildContract(),
    ...overrides,
  };
}

function createPageContext(page: CapturedPageOptions, overrides?: Record<string, unknown>) {
  const behavior = (page.behaviors?.[0] || {}) as {
    data?: Record<string, unknown>;
    methods?: Record<string, (...args: any[]) => any>;
  };
  const overrideData =
    overrides && typeof overrides === "object" && overrides.data && typeof overrides.data === "object"
      ? (overrides.data as Record<string, unknown>)
      : {};
  const data = {
    ...(behavior.data || {}),
    ...(page.data || {}),
    ...overrideData,
  } as Record<string, any>;
  // Deep-clone busy/retry defaults so tests do not share mutable page.data.
  data.busy = {
    loading: false,
    saving: false,
    uploading: false,
    submitting: false,
    navigating: false,
    retrying: false,
    ...(data.busy || {}),
  };
  data.retryMeta = {
    attempts: 0,
    cooldownUntil: 0,
    ...(data.retryMeta || {}),
  };
  data.errorState = {
    code: "",
    message: "",
    retryable: false,
    blocking: false,
    ...(data.errorState || {}),
  };
  const { data: _ignoredData, ...restOverrides } = (overrides || {}) as Record<string, unknown>;
  const ctx: Record<string, any> = {
    route: "/pages/receipt/receipt",
    ...(behavior.methods || {}),
    ...page,
    ...restOverrides,
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
  };
  return ctx;
}

test("Receipt page uses shared taskPage behavior", async () => {
  const page = await loadReceiptPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("success render shows calm three-line landing", async () => {
  const page = await loadReceiptPage();
  const task = buildTask();
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.submitted, true);
  assert.equal(ctx.data.title, "已收到");
  assert.match(String(ctx.data.message), /陈总.*联系您/);
  assert.equal(ctx.data.nextStep, "先不用操作");
  assert.equal(ctx.data.showSupplement, false);
  assert.equal(ctx.data.photoCount, 2);
  assert.equal(ctx.data.statusTone, "done");
  assert.match(String(ctx.data.brokerContactNote), /陈总/);
  assert.equal(String(ctx.data.materialsNote || ""), "");
});

test("reload refreshes from server and does not keep stale title", async () => {
  const page = await loadReceiptPage();
  const first = buildTask({
    completion_summary: {
      title: "旧标题",
      message: "旧消息",
      received: [],
      missing: [],
      next_step: "旧下一步",
      disclaimer: "旧声明",
    },
  });
  const second = buildTask({
    completion_summary: {
      title: "新标题",
      message: "新消息",
      received: [],
      missing: [],
      next_step: "新下一步",
      disclaimer: "新声明",
    },
    photo_count: 3,
  });

  let loadCount = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => {
      loadCount += 1;
      return loadCount === 1 ? first : second;
    },
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.title, "已收到");
  assert.equal(ctx.data.nextStep, "先不用操作");
  await page.onShow.call(ctx);
  // Waiting calm landing stays stable; photo count still refreshes from server.
  assert.equal(ctx.data.title, "已收到");
  assert.equal(ctx.data.nextStep, "先不用操作");
  assert.equal(ctx.data.photoCount, 3);
  assert.equal(loadCount, 2);
});

test("return home delegates through Entry Customer Context", async () => {
  const page = await loadReceiptPage();
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    redirects.push(url);
    complete?.();
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
  });
  page.onViewStatus.call(ctx);
  // No task on context → Waiting/Case Status surface (not Task Home dead-end).
  assert.deepEqual(redirects, ["/pages/entry/entry"]);
  assert.equal(ctx.data.busy.navigating, false);
});

test("Submit Result Home handler relaunches Service Home and keeps resume", async () => {
  const page = await loadReceiptPage();
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
  saveResumeToken("h5t1.stale-receipt");

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
  });
  page.onBackHome.call(ctx);
  assert.deepEqual(launches, ["/pages/service-home/service-home"]);
  assert.equal(loadResumeToken(), "h5t1.stale-receipt");
  assert.equal(ctx.data.busy.navigating, false);
});

test("waiting receipt prefers calm next step over dense summary copy", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    completion_summary: {
      title: "资料已提交",
      message: "已收到",
      received: [],
      missing: [],
      next_step: "专属下一步文案",
      disclaimer: "声明",
    },
    dashboard_summary: {
      ...buildTask().dashboard_summary!,
      next_action: "仪表盘下一步",
    },
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.title, "已收到");
  assert.equal(ctx.data.nextStep, "先不用操作");
});

test("submitted receipt uses unified supplement action sheet", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    missing_info: [{ key: "customer_damage_photo", label: "请补充车损照片" }],
    dashboard_summary: {
      ...buildTask().dashboard_summary!,
      submitted_supplement_allowed: true,
      missing: ["请补充车损照片"],
    },
  });
  const navigations: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({ url }: { url: string }) =>
    navigations.push(url);

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.showSupplement, true);
  assert.equal(ctx.data.submitted, true);
  assert.match(String(ctx.data.supplementHint), /车损|照片|补充/);
  (globalThis as Record<string, any>).wx.showActionSheet = ({
    success,
  }: {
    itemList: string[];
    success?: (res: { tapIndex: number }) => void;
  }) => success?.({ tapIndex: 0 });
  page.onEditSupplementInfo.call(ctx);
  assert.deepEqual(navigations, ["/pages/story/story"]);
});

test("receipt unified supplement action can open photos", async () => {
  const page = await loadReceiptPage();
  const task = buildTask();
  const navigations: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showActionSheet = ({
    success,
  }: {
    itemList: string[];
    success?: (res: { tapIndex: number }) => void;
  }) => success?.({ tapIndex: 3 });

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  page.onEditSupplementInfo.call(ctx);
  assert.deepEqual(navigations, ["/pages/photos/photos"]);
});

test("active VIN Slice 1 task routes directly to request-item", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    slice1_projection: buildSlice1Projection(),
  });
  const navigations: string[] = [];
  let actionSheetShown = 0;
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showActionSheet = () => {
    actionSheetShown += 1;
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.slice1Enabled, true);
  assert.equal(ctx.data.slice1PrimaryActionable, true);
  assert.equal(ctx.data.slice1LoadFailed, false);
  page.onEditSupplementInfo.call(ctx);
  assert.deepEqual(navigations, [REQUEST_ITEM_ROUTE]);
  assert.equal(actionSheetShown, 0);
});

test("no active Slice 1 task uses legacy supplement menu", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    missing_info: [{ key: "customer_damage_photo", label: "请补充车损照片" }],
    dashboard_summary: {
      ...buildTask().dashboard_summary!,
      submitted_supplement_allowed: true,
      missing: ["请补充车损照片"],
    },
  });
  const navigations: string[] = [];
  let actionSheetShown = 0;
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showActionSheet = ({
    itemList,
    success,
  }: {
    itemList: string[];
    success?: (res: { tapIndex: number }) => void;
  }) => {
    actionSheetShown += 1;
    assert.deepEqual(itemList, [
      "修改事故经过",
      "修改基本资料",
      "修改车辆及对方信息",
      "补充照片",
    ]);
    success?.({ tapIndex: 0 });
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.slice1Enabled, false);
  page.onEditSupplementInfo.call(ctx);
  assert.equal(actionSheetShown, 1);
  assert.deepEqual(navigations, ["/pages/story/story"]);
});

test("projection error shows retry, not legacy fallback", async () => {
  const page = await loadReceiptPage();
  let actionSheetShown = 0;
  let retryCalls = 0;
  (globalThis as Record<string, any>).wx.showActionSheet = () => {
    actionSheetShown += 1;
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => null,
    data: {
      ...page.data,
      slice1LoadFailed: true,
      errorState: {
        code: "network_error",
        message: "网络异常，请重试",
        retryable: true,
        blocking: false,
      },
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
    onRetry() {
      retryCalls += 1;
    },
  });

  page.onEditSupplementInfo.call(ctx);
  assert.equal(actionSheetShown, 0);
  assert.equal(retryCalls, 1);
});

test("duplicate CTA tap produces one navigation", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    slice1_projection: buildSlice1Projection(),
  });
  const navigations: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    // Intentionally delay complete so the second tap hits the navigating guard.
    setTimeout(() => complete?.(), 0);
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  page.onEditSupplementInfo.call(ctx);
  page.onEditSupplementInfo.call(ctx);
  assert.deepEqual(navigations, [REQUEST_ITEM_ROUTE]);
});

test("stale projection response cannot replace newer state", async () => {
  const state = createLoadFlightState();
  let resolveOlder: ((value: string) => void) | null = null;
  const older = new Promise<string>((resolve) => {
    resolveOlder = resolve;
  });
  const newer = Promise.resolve("newer");

  const first = runSingleFlightLoad(state, async () => older, { joinInFlight: false });
  const second = runSingleFlightLoad(state, async () => newer, { force: true, joinInFlight: false });
  resolveOlder?.("older");
  const olderResult = await first;
  const newerResult = await second;

  assert.equal(olderResult.ignored, true);
  assert.equal(olderResult.value, null);
  assert.equal(newerResult.ignored, false);
  assert.equal(newerResult.value, "newer");
  assert.equal(state.latestRequestSeq, 2);
});

test("destroyed receipt page does not apply later setData", async () => {
  const page = await loadReceiptPage();
  const task = buildTask({
    slice1_projection: buildSlice1Projection(),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.slice1Enabled, true);
  page.onUnload.call(ctx);
  ctx.safeSetData({ title: "should-not-apply" });
  assert.notEqual(ctx.data.title, "should-not-apply");
});
