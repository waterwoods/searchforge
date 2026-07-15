import test from "node:test";
import assert from "node:assert/strict";

import {
  beginLogicalSubmit,
  createLoadFlightState,
  endLogicalSubmit,
  runSingleFlightLoad,
  shouldStartShowInitialization,
} from "../utils/slice1Lifecycle";
import { newCommandIdentity } from "../utils/requestItemDraft";

test("onLoad starts one initialization and immediate onShow does not duplicate", async () => {
  const state = createLoadFlightState();
  let loads = 0;
  const load = () =>
    runSingleFlightLoad(state, async () => {
      loads += 1;
      await new Promise((r) => setTimeout(r, 20));
      return "task";
    });

  const first = load();
  const showMode = shouldStartShowInitialization(state);
  assert.equal(showMode, "join_or_start");
  const second = load(); // joins in-flight
  const [a, b] = await Promise.all([first, second]);
  assert.equal(loads, 1);
  assert.equal(a.value, "task");
  assert.equal(b.value, "task");
});

test("later onShow requests rehydrate", () => {
  const state = createLoadFlightState();
  assert.equal(shouldStartShowInitialization(state), "join_or_start");
  assert.equal(shouldStartShowInitialization(state), "rehydrate");
});

test("pull-to-refresh force supersedes older response", async () => {
  const state = createLoadFlightState();
  let resolveSlow: (value: string) => void = () => undefined;
  const slow = runSingleFlightLoad(
    state,
    () =>
      new Promise<string>((resolve) => {
        resolveSlow = resolve;
      }),
    { force: true, joinInFlight: false },
  );
  const fast = runSingleFlightLoad(state, async () => "fresh", {
    force: true,
    joinInFlight: false,
  });
  const fastResult = await fast;
  resolveSlow("stale");
  const slowResult = await slow;
  assert.equal(fastResult.ignored, false);
  assert.equal(fastResult.value, "fresh");
  assert.equal(slowResult.ignored, true);
  assert.equal(slowResult.value, null);
});

test("stale response ignored after destroy", async () => {
  const state = createLoadFlightState();
  let resolveLoad: (value: string) => void = () => undefined;
  const pending = runSingleFlightLoad(
    state,
    () =>
      new Promise<string>((resolve) => {
        resolveLoad = resolve;
      }),
    { force: true, joinInFlight: false },
  );
  state.pageAlive = false;
  state.latestRequestSeq += 1;
  resolveLoad("late");
  const result = await pending;
  assert.equal(result.ignored, true);
  assert.equal(result.value, null);
});

test("loading terminates on success and failure", async () => {
  const okState = createLoadFlightState();
  const ok = await runSingleFlightLoad(okState, async () => "ok", { force: true });
  assert.equal(ok.value, "ok");
  assert.equal(okState.activeLoadPromise, null);

  const failState = createLoadFlightState();
  await assert.rejects(
    () =>
      runSingleFlightLoad(
        failState,
        async () => {
          throw new Error("timeout");
        },
        { force: true },
      ),
    /timeout/,
  );
  assert.equal(failState.activeLoadPromise, null);
});

test("one submit produces one logical command; duplicate tap blocked", () => {
  const state = { submitInFlight: false, commandId: "", idempotencyKey: "" };
  const first = beginLogicalSubmit(state, () => newCommandIdentity("cmd_request_item"));
  const second = beginLogicalSubmit(state, () => newCommandIdentity("cmd_request_item"));
  assert.equal(first.started, true);
  assert.equal(second.started, false);
  assert.equal(second.command_id, first.command_id);
  endLogicalSubmit(state, false);
  const retry = beginLogicalSubmit(state, () => newCommandIdentity("cmd_request_item"), {
    reuseIdentity: true,
  });
  assert.equal(retry.started, true);
  assert.equal(retry.command_id, first.command_id);
  endLogicalSubmit(state, true);
  const next = beginLogicalSubmit(state, () => newCommandIdentity("cmd_request_item"));
  assert.notEqual(next.command_id, first.command_id);
});
