import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  buildVehicleInformationFactPayload,
  buildVinFactPayload,
  CLAIM_VEHICLE_COPY,
  claimUiContainsForbiddenTerminology,
  claimVehicleFormHasAnyValue,
  EMPTY_CLAIM_VEHICLE_FORM,
  hydrateClaimVehicleForm,
  isClaimVehicleItemType,
  isNeedsCorrection,
  isVehicleInformationItemType,
  parseVehicleDraft,
  parseVehicleSummaryValue,
  serializeVehicleDraft,
  switchVinUnavailableMode,
  validateVehicleInformationSubmit,
  validateVinRequestSubmit,
} from "../utils/claimVehicleForm";
import { factFieldForItemType, isVehicleInformationItemType as slice1IsVehicle } from "../utils/slice1Customer";
import { resolveRequestItemWorkSurface } from "../utils/requestItemWorkSurface";
import {
  clearRequestItemDraft,
  loadRequestItemDraft,
  saveRequestItemDraft,
} from "../utils/requestItemDraft";
import { getLatestPage, installMiniProgramGlobals, resetMiniProgramCaptures } from "./miniprogramMocks";

installMiniProgramGlobals();

const storage = new Map<string, unknown>();
(globalThis as { wx: Record<string, unknown> }).wx = {
  ...(globalThis as { wx: Record<string, unknown> }).wx,
  setStorageSync: (key: string, value: unknown) => {
    storage.set(key, value);
  },
  getStorageSync: (key: string) => storage.get(key),
  removeStorageSync: (key: string) => {
    storage.delete(key);
  },
  setNavigationBarTitle: () => undefined,
  showToast: () => undefined,
};

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");
const VALID_VIN = "1HGCM82633A004352";

test("VIN request copy helpers stay VIN-focused", () => {
  assert.equal(isClaimVehicleItemType("vin"), true);
  assert.equal(isVehicleInformationItemType("vin"), false);
  assert.equal(CLAIM_VEHICLE_COPY.vinOnlyLabel, "车辆识别码（VIN）");
  assert.equal(validateVinRequestSubmit("SHORT").ok, false);
  assert.equal(validateVinRequestSubmit("SHORT").message, CLAIM_VEHICLE_COPY.invalidVin);
  assert.equal(validateVinRequestSubmit(VALID_VIN).ok, true);
  assert.deepEqual(buildVinFactPayload(VALID_VIN), {
    field: "vin",
    value: VALID_VIN,
    vin: VALID_VIN,
    vin_unavailable: false,
    final: true,
    mode: "submit",
  });
});

test("vehicle_information rendering helpers and field field mapping", () => {
  assert.equal(isVehicleInformationItemType("vehicle_information"), true);
  assert.equal(slice1IsVehicle("vehicle_information"), true);
  assert.equal(factFieldForItemType("vehicle_information"), "vehicle_information");
  const surface = resolveRequestItemWorkSurface({
    loading: false,
    waitingForBroker: false,
    inputMode: "vehicle",
    nextAction: { request_item_id: "item_vi" },
    showWorkSurface: true,
  });
  assert.equal(surface.showWorkSurface, true);
  assert.equal(surface.showFooterCta, true);
  assert.equal(surface.emptyPage, false);
});

test("hydrates existing canonical values and legacy aliases", () => {
  const form = hydrateClaimVehicleForm({
    keyFacts: {
      vehicle_year: "2020",
      vehicle_make: "Toyota",
      vehicle_model: "Camry",
      own_vehicle_vin: VALID_VIN,
      vehicle_license_plate: "7abc123",
      vehicle_plate_state: "ca",
    },
  });
  assert.equal(form.year, "2020");
  assert.equal(form.make, "Toyota");
  assert.equal(form.model, "Camry");
  assert.equal(form.vin, VALID_VIN);
  assert.equal(form.vinUnavailable, false);
  assert.equal(form.licensePlate, "7ABC123");
  assert.equal(form.plateState, "CA");

  const legacy = hydrateClaimVehicleForm({
    keyFacts: { own_vehicle_info: "2021 Tesla Model Y" },
  });
  assert.equal(legacy.year, "2021");
  assert.equal(legacy.make, "Tesla");
  assert.equal(legacy.model, "Model Y");
  assert.equal(legacy.vinUnavailable, true);
});

test("local draft wins over server facts without clearing siblings", () => {
  const form = hydrateClaimVehicleForm({
    keyFacts: { vehicle_year: "2020", vehicle_make: "Toyota" },
    draft: { year: "2020", make: "Toyota", model: "Camry", vinUnavailable: true },
  });
  assert.equal(form.model, "Camry");
  assert.equal(form.year, "2020");
  assert.equal(form.make, "Toyota");
});

test("partial save payload does not satisfy and omits stale VIN", () => {
  const payload = buildVehicleInformationFactPayload(
    {
      ...EMPTY_CLAIM_VEHICLE_FORM,
      year: "2020",
      make: "Toyota",
      vin: "SHORT",
      vinUnavailable: true,
    },
    { final: false },
  );
  assert.equal(payload.field, "vehicle_information");
  assert.equal(payload.mode, "draft");
  assert.equal(payload.final, false);
  assert.equal(payload.vin_unavailable, true);
  assert.equal(payload.vin, undefined);
  assert.equal(payload.year, "2020");
  assert.equal(claimVehicleFormHasAnyValue({ ...EMPTY_CLAIM_VEHICLE_FORM, year: "2020" }), true);
});

test("resume draft serializes and restores structured fields", () => {
  storage.clear();
  const form = {
    ...EMPTY_CLAIM_VEHICLE_FORM,
    year: "2020",
    make: "Toyota",
    vinUnavailable: true,
  };
  saveRequestItemDraft({
    version: 1,
    case_id: "case_1",
    request_id: "req_1",
    request_item_id: "item_vi",
    item_type: "vehicle_information",
    draft_value: "",
    vehicle_draft: form,
    client_draft_id: "draft-1",
    updated_at: "2026-07-21T00:00:00Z",
  });
  const loaded = loadRequestItemDraft("case_1", "req_1", "item_vi");
  assert.equal(loaded?.vehicle_draft?.year, "2020");
  assert.equal(loaded?.vehicle_draft?.make, "Toyota");
  assert.equal(loaded?.vehicle_draft?.vinUnavailable, true);
  const parsed = parseVehicleDraft(serializeVehicleDraft(form));
  assert.equal(parsed?.year, "2020");
  clearRequestItemDraft("case_1", "req_1", "item_vi");
});

test("valid VIN submit and invalid VIN error", () => {
  assert.equal(validateVinRequestSubmit(VALID_VIN).ok, true);
  assert.equal(validateVehicleInformationSubmit({
    ...EMPTY_CLAIM_VEHICLE_FORM,
    vin: VALID_VIN,
  }).ok, true);
  const bad = validateVehicleInformationSubmit({
    ...EMPTY_CLAIM_VEHICLE_FORM,
    vin: "ABC",
  });
  assert.equal(bad.ok, false);
  assert.equal(bad.message, CLAIM_VEHICLE_COPY.invalidVin);
  assert.equal(bad.fieldErrors.vin, CLAIM_VEHICLE_COPY.invalidVin);
});

test("VIN unavailable mode requires year/make/model", () => {
  const missing = validateVehicleInformationSubmit({
    ...EMPTY_CLAIM_VEHICLE_FORM,
    vinUnavailable: true,
    year: "2020",
    make: "Toyota",
  });
  assert.equal(missing.ok, false);
  assert.equal(missing.message, CLAIM_VEHICLE_COPY.missingNoVinFields);

  const ok = validateVehicleInformationSubmit({
    ...EMPTY_CLAIM_VEHICLE_FORM,
    vinUnavailable: true,
    year: "2020",
    make: "Toyota",
    model: "Camry",
    vin: "STALEINVALIDVINXX",
    licensePlate: "7ABC123",
    plateState: "CA",
  });
  assert.equal(ok.ok, true);
  assert.equal(ok.normalized.vin, "");
  const payload = buildVehicleInformationFactPayload(ok.normalized, { final: true });
  assert.equal(payload.vin_unavailable, true);
  assert.equal(payload.vin, undefined);
  assert.equal(payload.license_plate, "7ABC123");
  assert.equal(payload.plate_state, "CA");
  assert.equal(payload.value, "2020 Toyota Camry");
});

test("switching VIN modes preserves year/make/model and clears VIN when unavailable", () => {
  const base = {
    ...EMPTY_CLAIM_VEHICLE_FORM,
    year: "2020",
    make: "Toyota",
    model: "Camry",
    vin: "SHORTVIN",
  };
  const unavailable = switchVinUnavailableMode(base, true);
  assert.equal(unavailable.vinUnavailable, true);
  assert.equal(unavailable.vin, "");
  assert.equal(unavailable.year, "2020");
  assert.equal(unavailable.make, "Toyota");
  assert.equal(unavailable.model, "Camry");
  const back = switchVinUnavailableMode(unavailable, false);
  assert.equal(back.vinUnavailable, false);
  assert.equal(back.year, "2020");
});

test("correction state detection and forbidden Add Car terminology", () => {
  assert.equal(isNeedsCorrection({ vehicle_verification_status: "needs_correction" }), true);
  assert.equal(isNeedsCorrection({ vehicle_verification_status: "confirmed" }), false);
  assert.equal(claimUiContainsForbiddenTerminology("Add Car"), true);
  assert.equal(claimUiContainsForbiddenTerminology("保单加车"), true);
  assert.equal(claimUiContainsForbiddenTerminology(CLAIM_VEHICLE_COPY.pageTitle), false);
  assert.equal(claimUiContainsForbiddenTerminology(CLAIM_VEHICLE_COPY.explanation), false);
});

test("request-item page exposes vehicle form defaults and no Add Car copy", async () => {
  resetMiniProgramCaptures();
  await import("../pages/request-item/request-item");
  const page = getLatestPage().options as { data: Record<string, unknown> };
  assert.ok(page.data.vehicleForm);
  assert.equal((page.data.vehicleForm as { vinUnavailable: boolean }).vinUnavailable, false);
  assert.equal(page.data.needsCorrection, false);

  const wxml = readFileSync(join(miniappRoot, "pages/request-item/request-item.wxml"), "utf8");
  assert.match(wxml, /inputMode === 'vehicle'/);
  assert.match(wxml, /暂时无法提供 VIN/);
  assert.match(wxml, /车辆识别码（VIN）/);
  assert.match(wxml, /车牌号（选填）/);
  assert.match(wxml, /车牌州（选填）/);
  assert.equal(wxml.includes("Add Car"), false);
  assert.equal(wxml.includes("Add Vehicle"), false);
  assert.equal(wxml.includes("Vehicle Identity"), false);
  assert.equal(wxml.includes("保单加车"), false);
  assert.equal(wxml.includes("加车"), false);

  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
  };
  assert.ok(appJson.pages?.includes("pages/request-item/request-item"));
  assert.equal(appJson.pages?.some((p) => /add-?vehicle/i.test(p)), false);
  assert.equal(existsSync(join(miniappRoot, "pages/add-vehicle")), false);
});

test("parseVehicleSummaryValue supports partial two-token summaries", () => {
  const parsed = parseVehicleSummaryValue("2020 Toyota");
  assert.equal(parsed.year, "2020");
  assert.equal(parsed.make, "Toyota");
});

test("request-item applyAuthoritativeTask hydrates vehicle_information and VIN", async () => {
  // Module is cached after the earlier page import; do not reset captures here.
  try {
    getLatestPage();
  } catch {
    await import("../pages/request-item/request-item");
  }
  const page = getLatestPage().options as {
    data: Record<string, any>;
    applyAuthoritativeTask?: (task: unknown, opts?: { restoreDraft?: boolean }) => void;
    runSubmit?: (opts: { reuseIdentity: boolean }) => Promise<void>;
    [key: string]: any;
  };

  const toasts: string[] = [];
  (globalThis as { wx: Record<string, unknown> }).wx.showToast = (opts: { title?: string }) => {
    if (opts?.title) toasts.push(String(opts.title));
  };

  storage.clear();
  saveRequestItemDraft({
    version: 1,
    case_id: "case_vi",
    request_id: "req_vi",
    request_item_id: "item_vi",
    item_type: "vehicle_information",
    draft_value: "",
    vehicle_draft: {
      year: "2020",
      make: "Toyota",
      model: "",
      vinUnavailable: false,
    },
    client_draft_id: "draft-vi",
    updated_at: "2026-07-21T00:00:00Z",
  });

  const ctx: Record<string, any> = {
    ...page,
    data: { ...page.data },
    __requestItemState: {
      clientDraftId: "draft-vi",
      commandId: "",
      idempotencyKey: "",
      expectedCaseVersion: 0,
      activeRequestItemId: "",
      requestId: "",
      caseId: "",
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
    uploadPhasePatch() {
      return { uploadPhase: "idle", uploadPhaseLabel: "", uploadStatusText: "" };
    },
  };

  page.applyAuthoritativeTask!.call(ctx, {
    lane: "claim",
    flow: "claim_intake_form",
    case_id: "case_vi",
    title: "事故",
    safety_copy: "",
    steps: [],
    current_step: "review",
    completed_count: 3,
    step_total: 4,
    submitted: true,
    phase: "broker_needs_more_info",
    key_facts: { vehicle_year: "2020", vehicle_make: "Toyota" },
    missing_info: [],
    slice1_projection: {
      case_id: "case_vi",
      workflow_state: "broker_more_requested",
      aggregate_version: 3,
      customer_next_action: {
        action_type: "provide_fact",
        request_id: "req_vi",
        request_item_id: "item_vi",
        title: "车辆信息",
        instructions: "请填写本次事故涉及车辆的信息。",
        required_input: "vehicle_information",
      },
      open_request: {
        request_id: "req_vi",
        status: "open",
        items: [
          {
            request_item_id: "item_vi",
            request_id: "req_vi",
            item_type: "vehicle_information",
            label: "车辆信息",
            instructions: "",
            required: true,
            position: 1,
            status: "active",
            actionable: true,
          },
        ],
        queued_items: [],
        progress: { satisfied: 0, total: 1, remaining: 1 },
      },
      request_progress: { satisfied: 0, total: 1, remaining: 1 },
    },
  }, { restoreDraft: true });

  assert.equal(ctx.data.inputMode, "vehicle");
  assert.equal(ctx.data.itemType, "vehicle_information");
  assert.equal(ctx.data.vehicleForm.year, "2020");
  assert.equal(ctx.data.vehicleForm.make, "Toyota");
  assert.match(String(ctx.data.nextActionTitle || ""), /车辆信息|事故/);
  assert.equal(claimUiContainsForbiddenTerminology(JSON.stringify(ctx.data)), false);

  // Double-submit prevention
  ctx.data.busy = { ...ctx.data.busy, submitting: true };
  ctx.__requestItemState.submitInFlight = true;
  let submitCalled = false;
  ctx.requireToken = () => {
    submitCalled = true;
    return "token";
  };
  await page.runSubmit!.call(ctx, { reuseIdentity: false });
  assert.equal(submitCalled, false);
});
