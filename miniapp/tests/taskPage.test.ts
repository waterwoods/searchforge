import test from "node:test";
import assert from "node:assert/strict";

import { installMiniProgramGlobals } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask } from "../types/task";

installMiniProgramGlobals();

type TaskPageBehavior = {
  data: Record<string, unknown>;
  methods: Record<string, (...args: any[]) => any>;
};

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "internal_case",
    title: "我的事故资料",
    safety_copy: "安全提示",
    steps: ["start", "injury", "time_location", "story", "vehicle_other_party", "review", "done"],
    current_step: "story",
    completed_count: 2,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {},
    missing_info: [],
    ...overrides,
  };
}

function createContext(behavior: TaskPageBehavior, overrides?: Record<string, unknown>) {
  const data = JSON.parse(JSON.stringify(behavior.data));
  const ctx: Record<string, any> = {
    data,
    route: "/pages/task-home/task-home",
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...behavior.methods,
    ...overrides,
  };
  return ctx;
}

function installGetApp(appState: Record<string, unknown>) {
  (globalThis as Record<string, unknown>).getApp = () => appState;
}

test("missing token redirects to entry", async () => {
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => redirects.push(url);

  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const appState: Record<string, unknown> = {};
  installGetApp(appState);
  const ctx = createContext(behavior);

  const token = behavior.methods.requireToken.call(ctx);
  assert.equal(token, null);
  assert.deepEqual(redirects, ["/pages/entry/entry"]);
});

test("successful load updates app task and view model", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid" };
  installGetApp(appState);

  const task = buildTask();
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => task;

  const ctx = createContext(behavior);
  const loaded = await behavior.methods.loadTask.call(ctx);

  assert.equal(loaded?.case_id, "internal_case");
  assert.equal((appState.task as CustomerTask).case_id, "internal_case");
  assert.equal((ctx.data.taskViewModel as { source: string }).source, "legacy");
  assert.equal(ctx.data.errorState, null);

  CustomerTaskApi.getTask = originalGetTask;
});

test("retryable failure uses cached task fallback", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const cachedTask = buildTask({ case_id: "cached_case" });
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid", task: cachedTask };
  installGetApp(appState);

  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => {
    const err = new Error("network_error") as Error & { code: string };
    err.code = "network_error";
    throw err;
  };

  const ctx = createContext(behavior);
  await behavior.methods.loadTask.call(ctx);
  const errorState = ctx.data.errorState as { retryable: boolean; blocking: boolean };

  assert.equal((ctx.data.task as CustomerTask).case_id, "cached_case");
  assert.equal(errorState.retryable, true);
  assert.equal(errorState.blocking, false);

  CustomerTaskApi.getTask = originalGetTask;
});

test("blocking failure exposes safe error state", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid" };
  installGetApp(appState);

  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => {
    const err = new Error("invalid_or_expired_task_link") as Error & { code: string };
    err.code = "invalid_or_expired_task_link";
    throw err;
  };

  const ctx = createContext(behavior);
  await behavior.methods.loadTask.call(ctx);
  const errorState = ctx.data.errorState as { code: string; blocking: boolean };

  assert.equal(errorState.code, "network_error");
  assert.equal(errorState.blocking, true);

  CustomerTaskApi.getTask = originalGetTask;
});

test("bounded retry and cooldown are enforced", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid", task: buildTask() };
  installGetApp(appState);

  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);

  const ctx = createContext(behavior, {
    loadTask: async () => null,
  });
  ctx.data.retryMeta.attempts = 3;
  ctx.data.retryMeta.cooldownUntil = 0;

  await behavior.methods.retryLoadTask.call(ctx);
  assert.equal(toasts.includes("网络暂时不可用，请稍后重试或联系陈总。"), false);
  assert.equal((ctx.data.errorState as { blocking: boolean }).blocking, true);

  ctx.data.retryMeta.attempts = 0;
  ctx.data.retryMeta.cooldownUntil = Date.now() + 5000;
  await behavior.methods.retryLoadTask.call(ctx);
  assert.ok(toasts.includes("请稍候再试"));
});

test("stale responses are ignored", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const appState: Record<string, unknown> = { taskToken: "h5t1.valid" };
  installGetApp(appState);

  let resolveFirst: ((value: CustomerTask) => void) | null = null;
  const firstPromise = new Promise<CustomerTask>((resolve) => {
    resolveFirst = resolve;
  });
  const secondTask = buildTask({ case_id: "second_case" });

  const originalGetTask = CustomerTaskApi.getTask;
  let callCount = 0;
  CustomerTaskApi.getTask = async () => {
    callCount += 1;
    if (callCount === 1) {
      return firstPromise;
    }
    return secondTask;
  };

  const ctx = createContext(behavior);
  const p1 = behavior.methods.loadTask.call(ctx);
  const p2 = behavior.methods.loadTask.call(ctx);
  await p2;
  resolveFirst?.(buildTask({ case_id: "first_case" }));
  await p1;

  assert.equal((ctx.data.task as CustomerTask).case_id, "second_case");

  CustomerTaskApi.getTask = originalGetTask;
});

test("busy guard and saveAndReturn sequencing", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  installGetApp({ taskToken: "h5t1.valid" });

  const steps: string[] = [];
  (globalThis as Record<string, any>).wx.navigateBack = ({
    success,
  }: {
    success?: () => void;
  }) => {
    steps.push("navigate");
    success?.();
  };

  const ctx = createContext(behavior);
  const saveFn = async () => {
    steps.push("save");
  };
  const ok = await behavior.methods.saveAndReturn.call(ctx, saveFn);
  assert.equal(ok, true);
  assert.deepEqual(steps, ["save", "navigate"]);

  ctx.data.busy.saving = true;
  const blocked = await behavior.methods.saveAndReturn.call(ctx, saveFn);
  assert.equal(blocked, false);
});

test("track is no-op and never marks manual pass", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as TaskPageBehavior;
  const ctx = createContext(behavior);
  behavior.methods.track.call(ctx, "manual_item_pass", { status: "PASS" });
  assert.equal(typeof behavior.methods.track, "function");
  assert.equal(ctx.data.errorState, null);
});
