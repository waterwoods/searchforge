/**
 * VIN / request-item submit reliability — uncertain reconcile + retry + closed.
 */
import test from "node:test";
import assert from "node:assert/strict";

import { installMiniProgramGlobals, getLatestPage } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import { ApiRequestError } from "../utils/request";
import { applySlice1ProjectionToTask, mapSlice1CustomerView } from "../utils/slice1Customer";
import { mapErrorMessage } from "../utils/taskMapping";
import type { CustomerTask, Slice1Projection } from "../types/task";

installMiniProgramGlobals();

const VALID_VIN = "1HGCM82633A004352";
const appState: { taskToken: string; task?: CustomerTask } = {
  taskToken: "token_vin",
  task: undefined,
};
(globalThis as Record<string, unknown>).getApp = () => appState;
(globalThis as { wx: Record<string, unknown> }).wx.setNavigationBarTitle = () => undefined;

function projectionThreeItems(satisfiedVin = false): Slice1Projection {
  return {
    case_id: "case_vin",
    workflow_state: satisfiedVin ? "customer_continuing" : "broker_more_requested",
    aggregate_version: satisfiedVin ? 4 : 2,
    customer_next_action: satisfiedVin
      ? {
          action_type: "provide_fact",
          request_id: "req_3",
          request_item_id: "item_vehicle",
          title: "车辆信息",
          instructions: "请填写车辆信息",
          required_input: "vehicle_information",
        }
      : {
          action_type: "provide_fact",
          request_id: "req_3",
          request_item_id: "item_vin",
          title: "Vehicle VIN",
          instructions: "请填写 VIN",
          required_input: "vin",
        },
    open_request: {
      request_id: "req_3",
      status: "open",
      items: [
        {
          request_item_id: "item_vin",
          request_id: "req_3",
          item_type: "vin",
          label: "Vehicle VIN",
          instructions: "",
          required: true,
          position: 1,
          status: satisfiedVin ? "satisfied" : "active",
          actionable: !satisfiedVin,
        },
        {
          request_item_id: "item_vehicle",
          request_id: "req_3",
          item_type: "vehicle_information",
          label: "Vehicle Information",
          instructions: "",
          required: true,
          position: 2,
          status: satisfiedVin ? "active" : "queued",
          actionable: satisfiedVin,
        },
        {
          request_item_id: "item_card",
          request_id: "req_3",
          item_type: "policy_or_insurance_card",
          label: "Insurance Card",
          instructions: "",
          required: true,
          position: 3,
          status: "queued",
          actionable: false,
        },
      ],
      queued_items: [],
      progress: {
        satisfied: satisfiedVin ? 1 : 0,
        total: 3,
        remaining: satisfiedVin ? 2 : 3,
      },
    },
    request_progress: {
      satisfied: satisfiedVin ? 1 : 0,
      total: 3,
      remaining: satisfiedVin ? 2 : 3,
    },
    queued_request_items: [],
    server_timestamp: "2026-07-22T00:00:00Z",
  };
}

function taskFrom(projection: Slice1Projection): CustomerTask {
  return applySlice1ProjectionToTask(
    {
      lane: "claim",
      flow: "claim_intake_form",
      case_id: "case_vin",
      title: "事故",
      safety_copy: "",
      steps: [],
      current_step: "review",
      completed_count: 3,
      step_total: 4,
      submitted: true,
      phase: "broker_needs_more_info",
      key_facts: {},
      missing_info: [],
    },
    projection,
  );
}

async function loadPage(): Promise<Record<string, any>> {
  try {
    return getLatestPage().options as Record<string, any>;
  } catch {
    await import("../pages/request-item/request-item");
    return getLatestPage().options as Record<string, any>;
  }
}

function pageHarness(page: Record<string, any>, task: CustomerTask) {
  appState.task = task;
  const ctx: Record<string, any> = {
    ...page,
    data: {
      ...page.data,
      task,
      submissionState: "idle",
      retryAvailable: false,
      submitDisabled: false,
      submitDisabledReason: "",
      draftValue: VALID_VIN,
      itemType: "vin",
      inputMode: "text",
      waitingForBroker: false,
      busy: { submitting: false, uploading: false, loading: false },
      pageError: { code: "", message: "", retryable: false, blocking: false },
      vehicleForm: { year: "", make: "", model: "", vin: VALID_VIN, vinUnavailable: false },
      fieldErrors: {},
      uploadItems: [],
      progress: mapSlice1CustomerView(task).progress,
    },
    __requestItemState: {
      clientDraftId: "draft_vin",
      commandId: "cmd_vin_1",
      idempotencyKey: "idem_vin_1",
      expectedCaseVersion: 2,
      activeRequestItemId: "item_vin",
      requestId: "req_3",
      caseId: "case_vin",
      submitInFlight: false,
      firstShowConsumed: true,
      pageDestroyed: false,
    },
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    safePageSetData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    setBusy() {},
    persistDraftSafe() {},
    uploadPhasePatch() {
      return { uploadPhase: "idle", uploadPhaseLabel: "", uploadStatusText: "" };
    },
    requireToken() {
      return "token_vin";
    },
    ensureCommandIdentity() {},
  };
  return ctx;
}

test("VIN progress starts 0/3 and advances to 1/3 after accepted submit", async () => {
  const page = await loadPage();
  const before = taskFrom(projectionThreeItems(false));
  assert.equal(mapSlice1CustomerView(before).progress.satisfied, 0);
  assert.equal(mapSlice1CustomerView(before).progress.total, 3);

  const ctx = pageHarness(page, before);
  const afterProjection = projectionThreeItems(true);
  const originalSubmit = CustomerTaskApi.submitRequestItem;
  CustomerTaskApi.submitRequestItem = async () =>
    ({
      outcome: "accepted",
      command_id: "cmd_vin_1",
      idempotency_key: "idem_vin_1",
      aggregate_version: 4,
      customer_projection: afterProjection,
    }) as any;

  try {
    await page.runSubmit.call(ctx, { reuseIdentity: false });
    assert.equal(ctx.data.progress.satisfied, 1);
    assert.equal(ctx.data.progress.total, 3);
    assert.equal(ctx.data.itemType, "vehicle_information");
    assert.notEqual(ctx.data.submissionState, "uncertain");
    assert.equal(ctx.data.retryAvailable, false);
    assert.equal(ctx.data.submitDisabled, false);
  } finally {
    CustomerTaskApi.submitRequestItem = originalSubmit;
  }
});

test("uncertain response reconciles against server and advances 1/3", async () => {
  const page = await loadPage();
  const ctx = pageHarness(page, taskFrom(projectionThreeItems(false)));
  const after = taskFrom(projectionThreeItems(true));

  const originalSubmit = CustomerTaskApi.submitRequestItem;
  CustomerTaskApi.submitRequestItem = async () => {
    throw new ApiRequestError("timeout", 0);
  };
  ctx.rehydrateAuthoritativeTask = async () => after;

  try {
    await page.runSubmit.call(ctx, { reuseIdentity: false });
    assert.equal(ctx.data.progress.satisfied, 1);
    assert.equal(ctx.data.progress.total, 3);
    assert.notEqual(ctx.data.submissionState, "uncertain");
    assert.equal(ctx.data.retryAvailable, false);
    assert.equal(String(ctx.data.pageError?.message || "").includes("未确认"), false);
    assert.equal(ctx.__requestItemState.activeRequestItemId, "item_vehicle");
  } finally {
    CustomerTaskApi.submitRequestItem = originalSubmit;
  }
});

test("retry after uncertain reuses same idempotency key and treats replay as success", async () => {
  const page = await loadPage();
  const ctx = pageHarness(page, taskFrom(projectionThreeItems(false)));
  ctx.data.submissionState = "uncertain";
  ctx.data.retryAvailable = true;
  const calls: Array<{ command_id: string; idempotency_key: string }> = [];
  const after = projectionThreeItems(true);

  const originalSubmit = CustomerTaskApi.submitRequestItem;
  CustomerTaskApi.submitRequestItem = async (_t, _id, command) => {
    calls.push({
      command_id: String(command.command_id),
      idempotency_key: String(command.idempotency_key),
    });
    return {
      outcome: "replayed",
      command_id: command.command_id,
      idempotency_key: command.idempotency_key,
      aggregate_version: 4,
      customer_projection: after,
    } as any;
  };

  try {
    await page.runSubmit.call(ctx, { reuseIdentity: true });
    assert.equal(calls.length, 1);
    assert.equal(calls[0].command_id, "cmd_vin_1");
    assert.equal(calls[0].idempotency_key, "idem_vin_1");
    assert.equal(ctx.data.progress.satisfied, 1);
    assert.notEqual(ctx.data.submissionState, "uncertain");
  } finally {
    CustomerTaskApi.submitRequestItem = originalSubmit;
  }
});

test("closed case shows read-only and does not leave endless uncertain retry", async () => {
  const page = await loadPage();
  const ctx = pageHarness(page, taskFrom(projectionThreeItems(false)));

  const originalSubmit = CustomerTaskApi.submitRequestItem;
  CustomerTaskApi.submitRequestItem = async () => {
    throw new ApiRequestError("case_closed_read_only", 409);
  };

  try {
    await page.runSubmit.call(ctx, { reuseIdentity: false });
    assert.equal(ctx.data.submissionState, "failed");
    assert.equal(ctx.data.retryAvailable, false);
    assert.equal(ctx.data.submitDisabled, true);
    assert.match(String(ctx.data.pageError?.message || ""), /关闭/);
    assert.equal(mapErrorMessage("case_closed_read_only").includes("关闭"), true);
  } finally {
    CustomerTaskApi.submitRequestItem = originalSubmit;
  }
});

test("app reopen restores completed VIN and shows next item", () => {
  const restored = taskFrom(projectionThreeItems(true));
  const view = mapSlice1CustomerView(restored);
  assert.equal(view.progress.satisfied, 1);
  assert.equal(view.progress.total, 3);
  assert.equal(view.nextAction?.request_item_id, "item_vehicle");
  assert.equal(view.satisfiedItems.some((i) => i.request_item_id === "item_vin"), true);
});
