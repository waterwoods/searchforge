/**
 * Claim Vehicle (事故车辆) — Mini Program form helpers.
 * Request More only; not Add Car / 保单加车.
 */

import { normalizeVin, validateVin } from "./slice1Customer";

/** Frozen customer-facing copy (T4). */
export const CLAIM_VEHICLE_COPY = {
  pageTitle: "车辆信息",
  explanation: "请填写本次事故涉及车辆的信息。",
  vinLabel: "车辆识别码（VIN）",
  vinUnavailable: "暂时无法提供 VIN",
  year: "年份",
  make: "品牌",
  model: "型号",
  plate: "车牌号（选填）",
  plateState: "车牌州（选填）",
  draftSaved: "已保存，可稍后继续",
  submitSuccess: "车辆信息已提交",
  invalidVin: "请输入有效的 17 位 VIN",
  missingNoVinFields: "暂时无法提供 VIN 时，请填写年份、品牌和型号",
  correction: "这些信息需要修改，请检查后重新提交",
  vinOnlyLabel: "车辆识别码（VIN）",
  vinOnlyPlaceholder: "请输入 17 位 VIN",
} as const;

export type ClaimVehicleFormFields = {
  year: string;
  make: string;
  model: string;
  vin: string;
  vinUnavailable: boolean;
  licensePlate: string;
  plateState: string;
};

export type ClaimVehicleFactPayload = {
  field: "vin" | "vehicle_information";
  value?: string;
  year?: string;
  make?: string;
  model?: string;
  vin?: string;
  vin_unavailable?: boolean;
  license_plate?: string;
  plate_state?: string;
  final?: boolean;
  mode?: "draft" | "submit";
};

export const EMPTY_CLAIM_VEHICLE_FORM: ClaimVehicleFormFields = {
  year: "",
  make: "",
  model: "",
  vin: "",
  vinUnavailable: false,
  licensePlate: "",
  plateState: "",
};

const FORBIDDEN_CLAIM_TERMS = [
  "Vehicle Identity",
  "Add Car",
  "Add Vehicle",
  "保单加车",
  "加车",
] as const;

export function isClaimVehicleItemType(itemType?: string | null): boolean {
  const key = String(itemType || "")
    .trim()
    .toLowerCase();
  return key === "vin" || key === "vehicle_information";
}

export function isVehicleInformationItemType(itemType?: string | null): boolean {
  return (
    String(itemType || "")
      .trim()
      .toLowerCase() === "vehicle_information"
  );
}

function trimStr(value: unknown): string {
  return String(value ?? "").trim();
}

function readFact(
  facts: Record<string, unknown> | null | undefined,
  keys: string[],
): string {
  if (!facts || typeof facts !== "object") return "";
  for (const key of keys) {
    const value = trimStr(facts[key]);
    if (value) return value;
  }
  return "";
}

function parseBoolFact(raw: unknown): boolean {
  if (raw === true || raw === 1) return true;
  const text = String(raw ?? "")
    .trim()
    .toLowerCase();
  return text === "true" || text === "1" || text === "yes";
}

/** Best-effort parse of legacy summary "2020 Toyota Camry". */
export function parseVehicleSummaryValue(raw: string): Partial<ClaimVehicleFormFields> {
  const text = trimStr(raw);
  if (!text) return {};
  const parts = text.split(/\s+/);
  if (parts.length >= 3 && /^\d{4}$/.test(parts[0])) {
    return {
      year: parts[0],
      make: parts[1],
      model: parts.slice(2).join(" "),
      vinUnavailable: true,
    };
  }
  if (parts.length === 2 && /^\d{4}$/.test(parts[0])) {
    return {
      year: parts[0],
      make: parts[1],
    };
  }
  return {};
}

/**
 * Hydrate structured Claim Vehicle fields from server key_facts / aliases
 * and optional local draft. Local draft wins for non-empty fields.
 */
export function hydrateClaimVehicleForm(options: {
  keyFacts?: Record<string, unknown> | null;
  draft?: Partial<ClaimVehicleFormFields> | null;
  itemType?: string | null;
}): ClaimVehicleFormFields {
  const facts = options.keyFacts || {};
  const fromFacts: ClaimVehicleFormFields = { ...EMPTY_CLAIM_VEHICLE_FORM };

  fromFacts.year = readFact(facts, ["vehicle_year", "year"]);
  fromFacts.make = readFact(facts, ["vehicle_make", "make"]);
  fromFacts.model = readFact(facts, ["vehicle_model", "model"]);
  fromFacts.vin = normalizeVin(
    readFact(facts, ["vehicle_vin", "vin", "own_vehicle_vin"]),
  );
  fromFacts.licensePlate = readFact(facts, [
    "vehicle_license_plate",
    "license_plate",
  ]).toUpperCase();
  fromFacts.plateState = readFact(facts, [
    "vehicle_plate_state",
    "plate_state",
  ]).toUpperCase();
  fromFacts.vinUnavailable =
    parseBoolFact(facts.vehicle_vin_unavailable ?? facts.vin_unavailable) &&
    !fromFacts.vin;

  if (!fromFacts.year && !fromFacts.make && !fromFacts.model && !fromFacts.vin) {
    const summary = readFact(facts, [
      "vehicle_information",
      "own_vehicle_info",
      "primary_vehicle_summary",
    ]);
    const parsed = parseVehicleSummaryValue(summary);
    Object.assign(fromFacts, parsed);
  }

  const draft = options.draft || null;
  if (!draft) return fromFacts;

  return {
    year: trimStr(draft.year) || fromFacts.year,
    make: trimStr(draft.make) || fromFacts.make,
    model: trimStr(draft.model) || fromFacts.model,
    vin: normalizeVin(draft.vin || "") || fromFacts.vin,
    vinUnavailable:
      typeof draft.vinUnavailable === "boolean"
        ? draft.vinUnavailable
        : fromFacts.vinUnavailable,
    licensePlate: trimStr(draft.licensePlate) || fromFacts.licensePlate,
    plateState: trimStr(draft.plateState) || fromFacts.plateState,
  };
}

export function isNeedsCorrection(keyFacts?: Record<string, unknown> | null): boolean {
  const status = readFact(keyFacts || {}, [
    "vehicle_verification_status",
    "verification_status",
  ]).toLowerCase();
  return status === "needs_correction";
}

export function claimVehicleFormHasAnyValue(form: ClaimVehicleFormFields): boolean {
  return Boolean(
    trimStr(form.year) ||
      trimStr(form.make) ||
      trimStr(form.model) ||
      trimStr(form.vin) ||
      form.vinUnavailable ||
      trimStr(form.licensePlate) ||
      trimStr(form.plateState),
  );
}

export type ClaimVehicleValidation = {
  ok: boolean;
  message: string;
  fieldErrors: Partial<Record<keyof ClaimVehicleFormFields, string>>;
  normalized: ClaimVehicleFormFields;
};

/** Final-submit validation for vehicle_information. */
export function validateVehicleInformationSubmit(
  form: ClaimVehicleFormFields,
): ClaimVehicleValidation {
  const normalized: ClaimVehicleFormFields = {
    year: trimStr(form.year),
    make: trimStr(form.make),
    model: trimStr(form.model),
    vin: normalizeVin(form.vin),
    vinUnavailable: Boolean(form.vinUnavailable),
    licensePlate: trimStr(form.licensePlate).toUpperCase(),
    plateState: trimStr(form.plateState).toUpperCase(),
  };
  const fieldErrors: ClaimVehicleValidation["fieldErrors"] = {};

  if (normalized.vinUnavailable) {
    if (!normalized.year || !normalized.make || !normalized.model) {
      const message = CLAIM_VEHICLE_COPY.missingNoVinFields;
      if (!normalized.year) fieldErrors.year = message;
      if (!normalized.make) fieldErrors.make = message;
      if (!normalized.model) fieldErrors.model = message;
      return { ok: false, message, fieldErrors, normalized };
    }
    // Path B: never send stale/invalid VIN.
    normalized.vin = "";
    return { ok: true, message: "", fieldErrors, normalized };
  }

  const vinResult = validateVin(normalized.vin);
  if (!vinResult.ok) {
    const message = CLAIM_VEHICLE_COPY.invalidVin;
    fieldErrors.vin = message;
    return {
      ok: false,
      message,
      fieldErrors,
      normalized: { ...normalized, vin: vinResult.normalized },
    };
  }
  normalized.vin = vinResult.normalized;
  normalized.vinUnavailable = false;
  return { ok: true, message: "", fieldErrors, normalized };
}

/** VIN-only request final validation. */
export function validateVinRequestSubmit(vinRaw: string): ClaimVehicleValidation {
  const vinResult = validateVin(vinRaw);
  const normalized: ClaimVehicleFormFields = {
    ...EMPTY_CLAIM_VEHICLE_FORM,
    vin: vinResult.normalized,
    vinUnavailable: false,
  };
  if (!vinResult.ok) {
    return {
      ok: false,
      message: CLAIM_VEHICLE_COPY.invalidVin,
      fieldErrors: { vin: CLAIM_VEHICLE_COPY.invalidVin },
      normalized,
    };
  }
  return { ok: true, message: "", fieldErrors: {}, normalized };
}

export function buildVinFactPayload(vin: string): ClaimVehicleFactPayload {
  return {
    field: "vin",
    value: normalizeVin(vin),
    vin: normalizeVin(vin),
    vin_unavailable: false,
    final: true,
    mode: "submit",
  };
}

export function buildVehicleInformationFactPayload(
  form: ClaimVehicleFormFields,
  options: { final: boolean },
): ClaimVehicleFactPayload {
  const year = trimStr(form.year);
  const make = trimStr(form.make);
  const model = trimStr(form.model);
  const licensePlate = trimStr(form.licensePlate).toUpperCase();
  const plateState = trimStr(form.plateState).toUpperCase();
  const vinUnavailable = Boolean(form.vinUnavailable);
  const vin = vinUnavailable ? "" : normalizeVin(form.vin);

  const payload: ClaimVehicleFactPayload = {
    field: "vehicle_information",
    mode: options.final ? "submit" : "draft",
    final: options.final,
    vin_unavailable: vinUnavailable,
  };
  if (year) payload.year = year;
  if (make) payload.make = make;
  if (model) payload.model = model;
  if (vin && vin.length === 17) payload.vin = vin;
  if (licensePlate) payload.license_plate = licensePlate;
  if (plateState) payload.plate_state = plateState;
  if (options.final && vinUnavailable && year && make && model) {
    payload.value = `${year} ${make} ${model}`;
  } else if (options.final && vin) {
    payload.value = vin;
  }
  return payload;
}

/**
 * Switch VIN-available ↔ VIN-unavailable.
 * Preserves year/make/model; clears VIN when entering unavailable mode
 * so invalid VIN is never persisted.
 */
export function switchVinUnavailableMode(
  form: ClaimVehicleFormFields,
  vinUnavailable: boolean,
): ClaimVehicleFormFields {
  if (vinUnavailable) {
    return {
      ...form,
      vinUnavailable: true,
      vin: "",
    };
  }
  return {
    ...form,
    vinUnavailable: false,
  };
}

export function serializeVehicleDraft(form: ClaimVehicleFormFields): string {
  try {
    return JSON.stringify({
      year: form.year || "",
      make: form.make || "",
      model: form.model || "",
      vin: form.vin || "",
      vinUnavailable: Boolean(form.vinUnavailable),
      licensePlate: form.licensePlate || "",
      plateState: form.plateState || "",
    });
  } catch {
    return "";
  }
}

export function parseVehicleDraft(raw: string | null | undefined): ClaimVehicleFormFields | null {
  const text = String(raw || "").trim();
  if (!text) return null;
  // Plain VIN draft from older clients.
  if (!text.startsWith("{")) {
    return {
      ...EMPTY_CLAIM_VEHICLE_FORM,
      vin: normalizeVin(text),
    };
  }
  try {
    const parsed = JSON.parse(text) as Partial<ClaimVehicleFormFields>;
    if (!parsed || typeof parsed !== "object") return null;
    return {
      year: trimStr(parsed.year),
      make: trimStr(parsed.make),
      model: trimStr(parsed.model),
      vin: normalizeVin(parsed.vin || ""),
      vinUnavailable: Boolean(parsed.vinUnavailable),
      licensePlate: trimStr(parsed.licensePlate),
      plateState: trimStr(parsed.plateState),
    };
  } catch {
    return null;
  }
}

/** Guard: Claim UI must never use Add Car terminology. */
export function claimUiContainsForbiddenTerminology(text: string): boolean {
  const hay = String(text || "");
  return FORBIDDEN_CLAIM_TERMS.some((term) => hay.includes(term));
}

export function mapVehicleServerError(code: string): string {
  const key = String(code || "").trim();
  if (key === "vin_invalid" || key === "invalid_vin") {
    return CLAIM_VEHICLE_COPY.invalidVin;
  }
  if (key === "vehicle_incomplete") {
    return CLAIM_VEHICLE_COPY.missingNoVinFields;
  }
  return "";
}
