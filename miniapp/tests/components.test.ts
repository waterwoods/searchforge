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
    "loading,error": (loading: boolean, error: { blocking?: boolean } | null) => void;
  };

  const modeHistory: string[] = [];
  const ctx = {
    setData: (patch: { mode: string }) => modeHistory.push(patch.mode),
  };

  observers["loading,error"].call(ctx, true, null);
  observers["loading,error"].call(ctx, false, { blocking: true });
  observers["loading,error"].call(ctx, false, null);

  assert.deepEqual(modeHistory, ["loading", "blocking_error", "content"]);
});

test("TaskLoading provides safe default message", async () => {
  resetMiniProgramCaptures();
  await import("../components/task-loading/index");
  const component = getLatestComponent().options;
  const messageProperty = (component.properties as Record<string, { value: string }>).message;

  assert.ok(typeof messageProperty.value === "string");
  assert.ok(messageProperty.value.includes("加载"));
});
