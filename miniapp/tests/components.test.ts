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
