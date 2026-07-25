import test from "node:test";
import assert from "node:assert/strict";

import {
  getLatestPage,
  installMiniProgramGlobals,
} from "./miniprogramMocks";
import type { TaskViewModel } from "../types/task";
import {
  DEFAULT_SAFETY_COPY,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../utils/resolveTaskViewModel";

installMiniProgramGlobals();

let cachedPage: CapturedPageOptions | null = null;

async function loadTaskHomePage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/task-home/task-home");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

function buildVm(overrides?: Partial<TaskViewModel>): TaskViewModel {
  return {
    source: "contract",
    shellMode: "content",
    title: "我的事故资料",
    instruction: "请继续完善资料",
    statusLabel: "进行中",
    statusTone: "active",
    progress: { completed: 2, total: 5, percent: 40 },
    cta: {
      label: "继续填写",
      actionType: "go_to_section",
      target: "story",
      disabled: false,
      loading: false,
      disabledReason: "",
    },
    missingItems: [
      {
        key: "accident_description",
        label: "事故经过",
        statusText: "未填写",
        actionable: true,
        route: "/pages/story/story",
        hint: "",
      },
    ],
    evidenceRequirements: [],
    reviewReady: false,
    submitReady: false,
    safetyCopy: "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。",
    error: null,
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
    route: "/pages/task-home/task-home",
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

test("initial merged page data exposes string shell bindings", async () => {
  const page = await loadTaskHomePage();
  const ctx = createPageContext(page);

  assert.equal(typeof ctx.data.shellSafetyCopy, "string");
  assert.equal(typeof ctx.data.ctaDisabledReason, "string");
  assert.equal(ctx.data.shellSafetyCopy, DEFAULT_SAFETY_COPY);
  assert.equal(ctx.data.ctaDisabledReason, "");
});

test("initial render bindings stay strings when nested vm fields are absent", async () => {
  const page = await loadTaskHomePage();
  const brokenVm = { ...EMPTY_TASK_VIEW_MODEL } as TaskViewModel & {
    safetyCopy?: string | null;
    cta: { disabledReason?: string | null };
  };
  delete (brokenVm as { safetyCopy?: string }).safetyCopy;
  brokenVm.cta = { ...brokenVm.cta, disabledReason: undefined };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: brokenVm,
      ...taskShellBindingsFromViewModel(brokenVm),
    },
  });

  assert.equal(typeof ctx.data.shellSafetyCopy, "string");
  assert.equal(typeof ctx.data.ctaDisabledReason, "string");
});

test("onShow delegates loading to shared behavior", async () => {
  const page = await loadTaskHomePage();
  let loadCalled = 0;
  const ctx = createPageContext(page, {
    loadTask: async () => {
      loadCalled += 1;
      return null;
    },
  });

  page.onShow.call(ctx);
  await Promise.resolve();
  assert.equal(loadCalled, 1);
});

test("onShow clears stale navigation and upload busy flags", async () => {
  const page = await loadTaskHomePage();
  let loadCalled = 0;
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: {
        loading: false,
        saving: false,
        uploading: true,
        submitting: false,
        navigating: true,
        retrying: false,
      },
    },
    setBusy(key: string, value: boolean) {
      ctx.data.busy = { ...ctx.data.busy, [key]: value };
    },
    loadTask: async () => {
      loadCalled += 1;
      return null;
    },
  });

  page.onShow.call(ctx);
  assert.equal(ctx.data.busy.navigating, false);
  assert.equal(ctx.data.busy.uploading, false);
  await Promise.resolve();
  assert.equal(loadCalled, 1);
});

test("primary action navigates from view model CTA", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: buildVm({
        cta: {
          label: "继续填写",
          actionType: "go_to_section",
          target: "photos",
          disabled: false,
          loading: false,
          disabledReason: "",
        },
      }),
    },
    isBusy: () => false,
    setBusy: () => undefined,
  });
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
    complete?.();
  };

  page.onPrimaryAction.call(ctx);
  assert.deepEqual(routes, ["/pages/photos/photos"]);
});

test("post-submit 继续补充资料 navigates to Basics (not Review)", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: buildVm({
        cta: {
          label: "继续补充资料",
          actionType: "go_to_section",
          target: "/pages/basics/basics",
          disabled: false,
          loading: false,
          disabledReason: "",
        },
      }),
    },
    isBusy: () => false,
    setBusy: () => undefined,
  });
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
    complete?.();
  };

  page.onPrimaryAction.call(ctx);
  assert.deepEqual(routes, ["/pages/basics/basics"]);
  assert.ok(!routes.some((url) => url.includes("review")));
});

test("post-submit primary CTA opens unified supplement action sheet", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  let actionSheetShown = 0;
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showActionSheet = ({
    success,
  }: {
    itemList: string[];
    success?: (res: { tapIndex: number }) => void;
  }) => {
    actionSheetShown += 1;
    success?.({ tapIndex: 1 });
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      task: {
        submitted: true,
        current_step: "done",
      },
      taskViewModel: buildVm({
        cta: {
          label: "查看提交结果",
          actionType: "go_to_section",
          target: "/pages/receipt/receipt",
          disabled: false,
          loading: false,
          disabledReason: "",
        },
      }),
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
    isBusy: () => false,
    setBusy: () => undefined,
  });

  page.onPrimaryAction.call(ctx);
  assert.equal(actionSheetShown, 1);
  assert.deepEqual(routes, ["/pages/basics/basics"]);
});

test("post-submit unified supplement sheet includes photo route", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showActionSheet = ({
    success,
  }: {
    itemList: string[];
    success?: (res: { tapIndex: number }) => void;
  }) => {
    success?.({ tapIndex: 3 });
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
    isBusy: () => false,
    setBusy: () => undefined,
  });

  page.onEditSupplementInfo.call(ctx);
  assert.deepEqual(routes, ["/pages/photos/photos"]);
});

test("submitted secondary CTA opens receipt", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
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
    isBusy: () => false,
    setBusy: () => undefined,
  });

  page.onViewReceipt.call(ctx);
  assert.deepEqual(routes, ["/pages/receipt/receipt"]);
});

test("retry button delegates to shared retryLoadTask", async () => {
  const page = await loadTaskHomePage();
  let retried = 0;
  const ctx = createPageContext(page, {
    retryLoadTask: async () => {
      retried += 1;
      return null;
    },
  });

  page.onRetry.call(ctx);
  await Promise.resolve();
  assert.equal(retried, 1);
});

test("navigation guard blocks duplicate CTA taps", async () => {
  const page = await loadTaskHomePage();
  let navigateCount = 0;
  (globalThis as Record<string, any>).wx.navigateTo = () => {
    navigateCount += 1;
  };

  const ctx = createPageContext(page, {
    isBusy: () => true,
    data: {
      ...page.data,
      taskViewModel: buildVm(),
    },
  });
  page.onPrimaryAction.call(ctx);
  assert.equal(navigateCount, 0);
});

/** Mirrors task-home.wxml CTA loading binding. */
function taskHomeCtaLoading(busy: { navigating: boolean; submitting: boolean }): boolean {
  return Boolean(busy.navigating || busy.submitting);
}

test("initial task home cta loading is false after load", async () => {
  const page = await loadTaskHomePage();
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
      taskViewModel: buildVm(),
    },
  });

  assert.equal(taskHomeCtaLoading(ctx.data.busy), false);
});

test("stale view model cta loading does not spin when busy flags are idle", async () => {
  const page = await loadTaskHomePage();
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
      taskViewModel: buildVm({
        cta: {
          label: "提交给陈总审核",
          actionType: "submit",
          target: "review",
          disabled: false,
          loading: true,
          disabledReason: "",
        },
      }),
    },
  });

  assert.equal(taskHomeCtaLoading(ctx.data.busy), false);
});

test("returning from photos after upload keeps cta loading false", async () => {
  const behaviorModule = await import("../behaviors/taskPage");
  const behavior = behaviorModule.taskPage as {
    data: Record<string, unknown>;
    methods: Record<string, (...args: any[]) => any>;
  };
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const task = {
    lane: "claim",
    flow: "claim_intake",
    case_id: "internal_case",
    title: "我的事故资料",
    safety_copy: "安全提示",
    steps: [],
    current_step: "review",
    completed_count: 4,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {},
    missing_info: [],
    task_contract: {
      contract_version: "0",
      task_id: "task_1",
      task_type: "claim_intake",
      task_status: "collecting",
      title: "我的事故资料",
      instruction: "请检查并提交",
      progress: { completed: 4, total: 5 },
      sections: [],
      fields: {},
      missing_items: [],
      evidence_requirements: [{ slot: "customer_damage_photo", label: "车损照片", min: 1, received: 2 }],
      next_action: { type: "submit", target: "review", label: "提交给陈总审核" },
      review_ready: true,
      submit_ready: true,
      revision: 1,
      timestamps: { updated_at: "2026-07-13T00:00:00Z" },
      capabilities: { voice: false, scan: false },
      branding: { office_name: "陈总办公室", safety_copy: "" },
      error: null,
    },
  };

  const { CustomerTaskApi } = await import("../services/taskApi");
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => task as any;

  const page = await loadTaskHomePage();
  const data = JSON.parse(JSON.stringify({ ...behavior.data, ...page.data }));
  const ctx: Record<string, any> = {
    route: "/pages/task-home/task-home",
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...behavior.methods,
    setBusy(key: string, value: boolean) {
      this.data.busy = { ...this.data.busy, [key]: value };
    },
  };

  ctx.data.busy.navigating = true;
  ctx.data.busy.uploading = true;
  behavior.methods.setBusy.call(ctx, "navigating", false);
  behavior.methods.setBusy.call(ctx, "uploading", false);
  await behavior.methods.loadTask.call(ctx);

  assert.equal((ctx.data.busy as { loading: boolean; navigating: boolean }).loading, false);
  assert.equal((ctx.data.busy as { navigating: boolean }).navigating, false);
  assert.equal(taskHomeCtaLoading(ctx.data.busy), false);
  assert.equal(
    (ctx.data.taskViewModel as { evidenceRequirements: Array<{ received: number }> }).evidenceRequirements[0]
      .received,
    2,
  );

  CustomerTaskApi.getTask = originalGetTask;
});

test("navigateOnce clears navigating after transition completes", async () => {
  const page = await loadTaskHomePage();
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
    setBusy(key: string, value: boolean) {
      ctx.data.busy = { ...ctx.data.busy, [key]: value };
    },
    isBusy: (key?: string) => (key ? Boolean(ctx.data.busy[key]) : Object.values(ctx.data.busy).some(Boolean)),
  });

  (globalThis as Record<string, any>).wx.navigateTo = ({ complete }: { complete?: () => void }) => {
    complete?.();
  };

  page.navigateOnce.call(ctx, "/pages/photos/photos");
  assert.equal(ctx.data.busy.navigating, false);
  assert.equal(taskHomeCtaLoading(ctx.data.busy), false);
});

test("navigateOnce blocks duplicate tap while navigating", async () => {
  const page = await loadTaskHomePage();
  let navigateCount = 0;
  (globalThis as Record<string, any>).wx.navigateTo = () => {
    navigateCount += 1;
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: true,
        retrying: false,
      },
    },
    setBusy(key: string, value: boolean) {
      ctx.data.busy = { ...ctx.data.busy, [key]: value };
    },
    isBusy: (key?: string) => (key ? Boolean(ctx.data.busy[key]) : Object.values(ctx.data.busy).some(Boolean)),
  });

  page.navigateOnce.call(ctx, "/pages/review/review");
  assert.equal(navigateCount, 0);
});

test("contact broker opens guidance modal, not safety disclaimer", async () => {
  const page = await loadTaskHomePage();
  const modals: Array<{ title: string; content: string }> = [];
  (globalThis as Record<string, any>).wx.showModal = (opts: {
    title: string;
    content: string;
  }) => {
    modals.push(opts);
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: buildVm({
        safetyCopy: "这是免责声明，不应出现在联系弹窗。",
      }),
    },
  });

  page.onContactBroker.call(ctx);
  assert.equal(modals.length, 1);
  assert.equal(modals[0].title, "联系陈总");
  assert.match(modals[0].content, /打开微信/);
  assert.equal(modals[0].content.includes("免责声明"), false);
});
