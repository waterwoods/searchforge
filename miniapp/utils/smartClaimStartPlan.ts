/**
 * Pure helpers for P4 Integration 01 Smart Claim Start presentation.
 * Cap 03 plan is SSOT for mode/chips/confirms; page owns form draft.
 */

import type {
  SmartClaimConfirmStep,
  SmartClaimKnownChip,
  SmartClaimStartPlan,
} from "../services/smartClaimStartApi";

export type SmartClaimUiMode =
  | "legacy"
  | "continue_active"
  | "contact_broker"
  | "matched"
  | "blank_degrade";

export type SmartClaimUiState = {
  uiMode: SmartClaimUiMode;
  planMode: string;
  headlineZh: string;
  subtitleZh: string;
  confidenceSignal: string;
  knownChips: SmartClaimKnownChip[];
  confirmSteps: SmartClaimConfirmStep[];
  showAccidentForm: boolean;
  showKnownSection: boolean;
  showConfirmSection: boolean;
  primaryCtaZh: string;
  secondaryCtaZh: string;
  whyAskTime: string;
  whyAskPhotos: string;
  /** Confirm step_id → selected option */
  confirmSelections: Record<string, string>;
  confirmsComplete: boolean;
  canShowAccidentBlock: boolean;
};

const WHY_ASK_TIME = "用于帮助确认事故顺序。";
const WHY_ASK_PHOTOS = "现在可以跳过，之后也可以补交。";

const BANNED_DISPLAY_FRAGMENTS = [
  "openid",
  "person_link",
  "wx_mock",
  "case_mock",
  "POL-MOCK",
  "mock_veh",
  "mock_cust",
  "vehicle_ref",
  "case_id",
];

export function sanitizeChipValue(value: unknown): string {
  const text = String(value || "").trim();
  if (!text) return "";
  const lower = text.toLowerCase();
  for (const frag of BANNED_DISPLAY_FRAGMENTS) {
    if (lower.includes(frag.toLowerCase())) return "";
  }
  return text;
}

export function sanitizeChips(chips: SmartClaimKnownChip[] | undefined): SmartClaimKnownChip[] {
  const out: SmartClaimKnownChip[] = [];
  for (const chip of chips || []) {
    const value = sanitizeChipValue(chip.value);
    const label = String(chip.label_zh || "").trim();
    if (!value || !label) continue;
    out.push({
      field_key: String(chip.field_key || ""),
      label_zh: label,
      value,
      editability: chip.editability,
    });
  }
  return out;
}

export function planHasBannedIdentityLeak(plan: SmartClaimStartPlan | null | undefined): boolean {
  if (!plan) return false;
  const blob = JSON.stringify(plan).toLowerCase();
  return (
    blob.includes("openid") ||
    blob.includes("person_link_key") ||
    /"case_id"\s*:/.test(blob)
  );
}

export function confirmsAreComplete(
  steps: SmartClaimConfirmStep[],
  selections: Record<string, string>,
): boolean {
  for (const step of steps || []) {
    if (!step.required_before_accident) continue;
    const chosen = String(selections[step.step_id] || "").trim();
    if (!chosen) return false;
    // Stale-policy "联系顾问" is a contact path, not accident progress.
    if (step.step_id === "confirm_policy" && /联系/.test(chosen)) {
      return false;
    }
  }
  return true;
}

export function policyConfirmWantsBroker(selections: Record<string, string>): boolean {
  const chosen = String(selections.confirm_policy || "").trim();
  return Boolean(chosen) && /联系/.test(chosen);
}

export function emptySmartClaimUiState(): SmartClaimUiState {
  return {
    uiMode: "legacy",
    planMode: "",
    headlineZh: "",
    subtitleZh: "",
    confidenceSignal: "",
    knownChips: [],
    confirmSteps: [],
    showAccidentForm: true,
    showKnownSection: false,
    showConfirmSection: false,
    primaryCtaZh: "提交给陈总",
    secondaryCtaZh: "",
    whyAskTime: "",
    whyAskPhotos: "",
    confirmSelections: {},
    confirmsComplete: true,
    canShowAccidentBlock: true,
  };
}

export function buildSmartClaimUiState(
  plan: SmartClaimStartPlan | null | undefined,
  confirmSelections?: Record<string, string>,
): SmartClaimUiState {
  if (!plan || !plan.mode) {
    return emptySmartClaimUiState();
  }

  const mode = String(plan.mode || "");
  const selections = { ...(confirmSelections || {}) };
  const confirmSteps = Array.isArray(plan.confirm_steps) ? plan.confirm_steps : [];
  const chips = sanitizeChips(plan.known_chips);
  const confirmsComplete = confirmsAreComplete(confirmSteps, selections);
  const wantsBroker = policyConfirmWantsBroker(selections);

  if (mode === "CONTINUE_ACTIVE") {
    return {
      ...emptySmartClaimUiState(),
      uiMode: "continue_active",
      planMode: mode,
      headlineZh: plan.headline_zh || "您已有一个正在处理的报案",
      subtitleZh: plan.subtitle_zh || "请先继续当前报案。",
      confidenceSignal: plan.confidence_signal || "",
      showAccidentForm: false,
      showKnownSection: false,
      showConfirmSection: false,
      primaryCtaZh: plan.primary_cta_zh || "继续当前报案",
      secondaryCtaZh: plan.secondary_cta_zh || "联系陈总",
      confirmsComplete: true,
      canShowAccidentBlock: false,
    };
  }

  if (mode === "CONTACT_BROKER" || wantsBroker) {
    return {
      ...emptySmartClaimUiState(),
      uiMode: "contact_broker",
      planMode: mode || "CONTACT_BROKER",
      headlineZh: wantsBroker
        ? "请联系陈总更新保单"
        : plan.headline_zh || "需要陈总协助确认身份",
      subtitleZh: wantsBroker
        ? "确认后再继续报案，可避免用错保单。"
        : plan.subtitle_zh || "请先联系陈总后再报案。",
      confidenceSignal: plan.confidence_signal || "",
      showAccidentForm: false,
      primaryCtaZh: "联系陈总",
      secondaryCtaZh: "",
      confirmSelections: selections,
      confirmsComplete: false,
      canShowAccidentBlock: false,
    };
  }

  const matched = mode.startsWith("MATCHED_");
  const blank = mode === "BLANK_DEGRADE";
  const showConfirm = confirmSteps.length > 0;
  const canShowAccident = !showConfirm || confirmsComplete;

  return {
    uiMode: matched ? "matched" : blank ? "blank_degrade" : "legacy",
    planMode: mode,
    headlineZh: plan.headline_zh || "今天发生了什么？",
    subtitleZh: plan.subtitle_zh || "",
    confidenceSignal: plan.confidence_signal || "",
    knownChips: chips,
    confirmSteps,
    showAccidentForm: true,
    showKnownSection: chips.length > 0,
    showConfirmSection: showConfirm,
    primaryCtaZh: plan.primary_cta_zh || "提交给陈总",
    secondaryCtaZh: String(plan.secondary_cta_zh || ""),
    whyAskTime: WHY_ASK_TIME,
    whyAskPhotos: WHY_ASK_PHOTOS,
    confirmSelections: selections,
    confirmsComplete,
    canShowAccidentBlock: canShowAccident,
  };
}

/** Parse Founder QA launch query `scs=S3` / `mock_scenario=S3`. */
export function resolveMockScenarioFromQuery(
  options?: Record<string, string | undefined>,
): string {
  const raw = String(options?.scs || options?.mock_scenario || "").trim();
  return raw.slice(0, 64);
}
