import test from "node:test";
import assert from "node:assert/strict";

import { getLatestComponent, installMiniProgramGlobals, resetMiniProgramCaptures } from "./miniprogramMocks";

installMiniProgramGlobals();

test("TaskCTA suppresses tap when disabled or loading", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-cta/index");
  const component = getLatestComponent().options;
  const methods = component.methods as { onTap: () => void };

  let emitCount = 0;
  const ctxDisabled = {
    properties: { disabled: true, loading: false },
    triggerEvent: () => {
      emitCount += 1;
    },
  };
  methods.onTap.call(ctxDisabled);
  assert.equal(emitCount, 0);

  const ctxLoading = {
    properties: { disabled: false, loading: true },
    triggerEvent: () => {
      emitCount += 1;
    },
  };
  methods.onTap.call(ctxLoading);
  assert.equal(emitCount, 0);

  const ctxReady = {
    properties: { disabled: false, loading: false },
    triggerEvent: () => {
      emitCount += 1;
    },
  };
  methods.onTap.call(ctxReady);
  assert.equal(emitCount, 1);

  const observers = component.observers as {
    label: (value: unknown) => void;
    disabledReason: (value: unknown) => void;
  };
  const patches: Record<string, unknown>[] = [];
  const observerCtx = {
    setData: (patch: Record<string, unknown>) => patches.push(patch),
  };
  observers.label.call(observerCtx, null);
  observers.disabledReason.call(observerCtx, null);
  assert.equal(patches[0].safeLabel, "继续");
  assert.equal(patches[1].safeDisabledReason, "");
});

test("TaskError emits retry and contactBroker correctly", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-error/index");
  const component = getLatestComponent().options;
  const methods = component.methods as { onRetryTap: () => void; onContactBrokerTap: () => void };

  const emitted: string[] = [];
  const ctx = {
    properties: { retryable: true, retryDisabled: false },
    triggerEvent: (event: string) => emitted.push(event),
  };
  methods.onRetryTap.call(ctx);
  methods.onContactBrokerTap.call(ctx);
  assert.deepEqual(emitted, ["retry", "contactBroker"]);

  emitted.length = 0;
  const disabledRetryCtx = {
    properties: { retryable: true, retryDisabled: true },
    triggerEvent: (event: string) => emitted.push(event),
  };
  methods.onRetryTap.call(disabledRetryCtx);
  assert.deepEqual(emitted, []);
});

test("TaskShell selects loading/error/content mode", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-shell/index");
  const component = getLatestComponent().options;
  const observers = component.observers as {
    "loading,safeError.blocking": (loading: boolean, blocking: boolean) => void;
  };

  const modeHistory: string[] = [];
  const ctx = {
    setData: (patch: { mode: string }) => modeHistory.push(patch.mode),
  };

  observers["loading,safeError.blocking"].call(ctx, true, false);
  observers["loading,safeError.blocking"].call(ctx, false, true);
  observers["loading,safeError.blocking"].call(ctx, false, false);

  assert.deepEqual(modeHistory, ["loading", "blocking_error", "content"]);

  const stringObservers = component.observers as {
    safetyCopy: (copy: unknown) => void;
    loadingMessage: (message: unknown) => void;
    error: (error: unknown) => void;
  };
  const patches: Record<string, unknown>[] = [];
  const stringCtx = {
    setData: (patch: Record<string, unknown>) => patches.push(patch),
  };
  stringObservers.safetyCopy.call(stringCtx, null);
  stringObservers.loadingMessage.call(stringCtx, null);
  stringObservers.error.call(stringCtx, null);
  assert.equal(patches[0].safeSafetyCopy, "");
  assert.equal(patches[1].safeLoadingMessage, "正在加载资料，请稍候…");
  assert.deepEqual(patches[2].safeError, {
    code: "",
    message: "",
    retryable: false,
    blocking: false,
  });
});


test("TaskLoading provides safe default message", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-loading/index");
  const component = getLatestComponent().options;
  const messageProperty = (component.properties as Record<string, { value: string }>).message;

  assert.ok(typeof messageProperty.value === "string");
  assert.ok(messageProperty.value.includes("加载"));
});

test("TaskStatusCard normalizes empty and safe text fields", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-status-card/index");
  const component = getLatestComponent().options;
  const observers = component.observers as {
    status: (value: unknown) => void;
    instruction: (value: unknown) => void;
    received: (value: unknown) => void;
    missing: (value: unknown) => void;
  };
  const patches: Record<string, unknown>[] = [];
  const ctx = {
    setData: (patch: Record<string, unknown>) => patches.push(patch),
  };

  observers.status.call(ctx, null);
  observers.instruction.call(ctx, null);
  observers.received.call(ctx, ["事故经过", "", null]);
  observers.missing.call(ctx, [
    { label: "是否有人受伤", statusText: "未填写", actionable: true },
    { label: "", statusText: "未填写" },
  ]);

  assert.equal(patches[0].safeStatus, "进行中");
  assert.equal(patches[1].safeInstruction, "");
  assert.deepEqual(patches[2].safeReceived, ["事故经过"]);
  assert.deepEqual(patches[3].safeMissing, [
    { label: "是否有人受伤", statusText: "未填写", actionable: true, hint: "" },
  ]);
});

test("TaskProgress clamps percent and handles zero total", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-progress/index");
  const component = getLatestComponent().options;
  const observers = component.observers as {
    "completed,total": (completed: unknown, total: unknown) => void;
  };

  const patches: Record<string, unknown>[] = [];
  const ctx = {
    setData: (patch: Record<string, unknown>) => patches.push(patch),
  };

  observers["completed,total"].call(ctx, 8, 5);
  observers["completed,total"].call(ctx, 3, 0);

  assert.deepEqual(patches[0], { safeCompleted: 5, safeTotal: 5, safePercent: 100 });
  assert.deepEqual(patches[1], { safeCompleted: 0, safeTotal: 0, safePercent: 0 });
});

test("TaskChoice emits selected value and respects disabled", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-choice/index");
  const component = getLatestComponent().options;
  const methods = component.methods as {
    onTapOption: (e: WechatMiniprogram.TouchEvent) => void;
  };

  const emitted: string[] = [];
  const ctx = {
    properties: { disabled: false },
    data: { safeValue: "no" },
    setData: (patch: { safeValue: string }) => {
      ctx.data = { ...ctx.data, ...patch };
    },
    triggerEvent: (_event: string, detail: { value: string }) => emitted.push(detail.value),
  };
  methods.onTapOption.call(ctx, { currentTarget: { dataset: { value: "yes" } } } as never);
  methods.onTapOption.call(ctx, { currentTarget: { dataset: { value: "yes" } } } as never);
  assert.deepEqual(emitted, ["yes"]);

  const disabledCtx = {
    ...ctx,
    properties: { disabled: true },
  };
  methods.onTapOption.call(disabledCtx, { currentTarget: { dataset: { value: "no" } } } as never);
  assert.deepEqual(emitted, ["yes"]);
});

test("TaskPhoto normalizes slots and emits actions", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-photo/index");
  const component = getLatestComponent().options;
  const observers = component.observers as {
    slots: (value: unknown) => void;
  };
  const patches: Record<string, unknown>[] = [];
  const observerCtx = {
    setData: (patch: Record<string, unknown>) => patches.push(patch),
  };

  observers.slots.call(observerCtx, [
    { key: "customer_damage_photo", label: null, progress: 120, uploaded: 1, uploading: 0, error: null },
  ]);
  const normalized = patches[0].safeSlots as Array<{ label: string; progress: number; uploaded: boolean }>;
  assert.equal(normalized[0].label, "事故照片");
  assert.equal(normalized[0].progress, 100);
  assert.equal(normalized[0].uploaded, true);

  const methods = component.methods as {
    onAddTap: (e: WechatMiniprogram.TouchEvent) => void;
    onRetryTap: (e: WechatMiniprogram.TouchEvent) => void;
    onRemoveTap: (e: WechatMiniprogram.TouchEvent) => void;
    onPreviewTap: (e: WechatMiniprogram.TouchEvent) => void;
  };
  const emitted: Array<{ event: string; detail?: unknown }> = [];
  const ctx = {
    properties: { disabled: false },
    triggerEvent: (event: string, detail?: unknown) => emitted.push({ event, detail }),
  };
  methods.onAddTap.call(ctx, { currentTarget: { dataset: { slotKey: "slot_1" } } } as never);
  methods.onRetryTap.call(ctx, { currentTarget: { dataset: { slotKey: "slot_1" } } } as never);
  methods.onRemoveTap.call(ctx, { currentTarget: { dataset: { slotKey: "slot_1" } } } as never);
  methods.onPreviewTap.call(
    ctx,
    { currentTarget: { dataset: { slotKey: "slot_1", localPath: "/tmp/photo.jpg" } } } as never,
  );

  assert.deepEqual(
    emitted.map((entry) => entry.event),
    ["add", "retry", "remove", "preview"],
  );

  emitted.length = 0;
  const disabledCtx = {
    properties: { disabled: true },
    triggerEvent: (event: string) => emitted.push({ event }),
  };
  methods.onAddTap.call(disabledCtx, { currentTarget: { dataset: { slotKey: "slot_2" } } } as never);
  methods.onRetryTap.call(disabledCtx, { currentTarget: { dataset: { slotKey: "slot_2" } } } as never);
  methods.onRemoveTap.call(disabledCtx, { currentTarget: { dataset: { slotKey: "slot_2" } } } as never);
  assert.deepEqual(emitted, []);
});
