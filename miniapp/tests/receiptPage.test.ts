import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import type { CustomerTask, TaskContractV0 } from "../types/task";

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
  const data = {
    ...(behavior.data || {}),
    ...(page.data || {}),
  } as Record<string, any>;
  const ctx: Record<string, any> = {
    route: "/pages/receipt/receipt",
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

test("Receipt page uses shared taskPage behavior", async () => {
  const page = await loadReceiptPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("success render shows title, next step, and timestamp", async () => {
  const page = await loadReceiptPage();
  const task = buildTask();
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.submitted, true);
  assert.equal(ctx.data.title, "资料已提交");
  assert.equal(ctx.data.nextStep, "请耐心等待陈总回复");
  assert.ok(String(ctx.data.submittedAt).length > 0);
  assert.equal(ctx.data.photoCount, 2);
  assert.equal(ctx.data.statusTone, "done");
  assert.match(String(ctx.data.brokerContactNote), /陈总/);
  assert.match(String(ctx.data.materialsNote), /补充|材料|照片/);
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
  assert.equal(ctx.data.title, "旧标题");
  await page.onShow.call(ctx);
  assert.equal(ctx.data.title, "新标题");
  assert.equal(ctx.data.nextStep, "新下一步");
  assert.equal(ctx.data.photoCount, 3);
  assert.equal(loadCount, 2);
});

test("return home redirects to task home", async () => {
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
  assert.deepEqual(redirects, ["/pages/task-home/task-home"]);
  assert.equal(ctx.data.busy.navigating, false);
});

test("next-step display prefers completion summary", async () => {
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
  assert.equal(ctx.data.nextStep, "专属下一步文案");
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
  (globalThis as Record<string, any>).wx.navigateTo = ({ url }: { url: string }) =>
    navigations.push(url);
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
