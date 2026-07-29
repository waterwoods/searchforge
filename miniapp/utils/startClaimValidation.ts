/**
 * Customer Start Claim — Must Have enablement / validation (Business Contract).
 * Pure helpers so enablement rules stay testable without Page runtime.
 */

export type StartClaimFormInput = {
  description: string;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
  /** Optional contact — only required when reachability is already unknown. */
  contact?: string;
  reachabilityKnown?: boolean;
};

/** Canonical mutable form model — must stay equal to visible bound values. */
export type StartClaimCanonicalForm = {
  description: string;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
};

export function createEmptyCanonicalForm(): StartClaimCanonicalForm {
  return {
    description: "",
    accidentDatetime: "",
    accidentLocation: "",
    injuryStatus: "",
  };
}

/**
 * Merge a field patch into canonical form without dropping siblings.
 * Used so injury selection / setData races cannot wipe description/time/location.
 */
export function mergeCanonicalForm(
  current: StartClaimCanonicalForm,
  patch: Partial<StartClaimCanonicalForm>,
): StartClaimCanonicalForm {
  return {
    description: patch.description !== undefined ? String(patch.description) : current.description,
    accidentDatetime:
      patch.accidentDatetime !== undefined
        ? String(patch.accidentDatetime)
        : current.accidentDatetime,
    accidentLocation:
      patch.accidentLocation !== undefined
        ? String(patch.accidentLocation)
        : current.accidentLocation,
    injuryStatus:
      patch.injuryStatus !== undefined ? String(patch.injuryStatus) : current.injuryStatus,
  };
}

export type StartClaimFieldKey =
  | "description"
  | "accidentDatetime"
  | "accidentLocation"
  | "injuryStatus"
  | "contact";

export type StartClaimFieldErrors = Partial<Record<StartClaimFieldKey, string>>;

export type StartClaimValidation = {
  ok: boolean;
  canSubmit: boolean;
  errors: StartClaimFieldErrors;
  /** First invalid field key for focus/scroll hints. */
  firstInvalid: StartClaimFieldKey | null;
  /** Locale-friendly datetime text sent as the authoritative accident_datetime. */
  normalizedDatetime: string;
  /** Canonical injury: yes | no | unknown */
  normalizedInjury: "yes" | "no" | "unknown" | "";
  missingHint: string;
};

const INJURY_ALIASES: Record<string, "yes" | "no" | "unknown"> = {
  yes: "yes",
  no: "no",
  unknown: "unknown",
  unsure: "unknown",
  "有人受伤": "yes",
  "没有受伤": "no",
  "不确定": "unknown",
};

/** Request More / Nice to Have — must never participate in Start Claim enablement. */
export const START_CLAIM_NON_BLOCKING_FIELDS = [
  "vin",
  "vehicle_information",
  "policy_or_insurance_card",
  "photo_evidence",
  "photos",
  "police_involved",
  "other_party_info",
] as const;

export function normalizeInjuryStatus(raw: string): "yes" | "no" | "unknown" | "" {
  const key = String(raw || "").trim().toLowerCase();
  if (!key) return "";
  if (INJURY_ALIASES[key]) return INJURY_ALIASES[key];
  const original = String(raw || "").trim();
  if (INJURY_ALIASES[original]) return INJURY_ALIASES[original];
  return "";
}

/**
 * Accept broker-readable free text (e.g. "Today 9 am", "今天上午 10:30").
 * Keeps the trimmed display text as the stable value sent to the API —
 * no large custom date system.
 */
export function normalizeAccidentDatetime(raw: string): string {
  return String(raw || "").trim().replace(/\s+/g, " ");
}

/** Normalize the canonical model before rendering and payload construction. */
export function normalizeStartClaimCanonicalForm(
  input: StartClaimCanonicalForm,
): StartClaimCanonicalForm {
  return {
    description: String(input.description || "").trim(),
    accidentDatetime: normalizeAccidentDatetime(input.accidentDatetime),
    accidentLocation: String(input.accidentLocation || "").trim(),
    injuryStatus: normalizeInjuryStatus(input.injuryStatus),
  };
}

export function isAccidentDatetimeAcceptable(raw: string): boolean {
  const value = normalizeAccidentDatetime(raw);
  if (!value) return false;
  // Reject values that are only punctuation / placeholders.
  if (!/[0-9\u4e00-\u9fffA-Za-z]/.test(value)) return false;
  return value.length >= 1;
}

export function validateStartClaimForm(input: StartClaimFormInput): StartClaimValidation {
  const description = String(input.description || "").trim();
  const accidentLocation = String(input.accidentLocation || "").trim();
  const normalizedDatetime = normalizeAccidentDatetime(input.accidentDatetime || "");
  const normalizedInjury = normalizeInjuryStatus(input.injuryStatus || "");
  const reachabilityKnown = input.reachabilityKnown !== false;
  const contact = String(input.contact || "").trim();

  const errors: StartClaimFieldErrors = {};

  if (!description) {
    errors.description = "请用一句话说明事故经过。";
  }
  if (!isAccidentDatetimeAcceptable(normalizedDatetime)) {
    errors.accidentDatetime = "请填写事故时间，例如：今天上午 9 点。";
  }
  if (!accidentLocation) {
    errors.accidentLocation = "请填写事故地点，例如：路口、停车场。";
  }
  if (!normalizedInjury) {
    errors.injuryStatus = "请选择是否有人受伤。";
  }
  if (!reachabilityKnown && !contact) {
    errors.contact = "请留下联系方式，方便陈总联系您。";
  }

  const order: StartClaimFieldKey[] = [
    "description",
    "accidentDatetime",
    "accidentLocation",
    "injuryStatus",
    "contact",
  ];
  const firstInvalid = order.find((key) => Boolean(errors[key])) || null;
  const ok = firstInvalid == null;
  const missingLabels: string[] = [];
  if (errors.description) missingLabels.push("事故经过");
  if (errors.accidentDatetime) missingLabels.push("事故时间");
  if (errors.accidentLocation) missingLabels.push("事故地点");
  if (errors.injuryStatus) missingLabels.push("是否受伤");
  if (errors.contact) missingLabels.push("联系方式");

  return {
    ok,
    canSubmit: ok,
    errors,
    firstInvalid,
    normalizedDatetime,
    normalizedInjury,
    missingHint: ok ? "" : `请先填写：${missingLabels.join("、")}`,
  };
}

export function buildStartClaimPayload(input: StartClaimFormInput): {
  accident_description: string;
  accident_datetime: string;
  accident_location: string;
  injury_status: "yes" | "no" | "unknown";
} | null {
  const v = validateStartClaimForm(input);
  if (!v.ok || !v.normalizedInjury) return null;
  return {
    accident_description: String(input.description || "").trim(),
    accident_datetime: v.normalizedDatetime,
    accident_location: String(input.accidentLocation || "").trim(),
    injury_status: v.normalizedInjury,
  };
}
