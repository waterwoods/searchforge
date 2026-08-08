/**
 * Guided accident-story UX helpers — pure, testable (no Page runtime).
 * Maps LangGraph guided_view → customer-visible phases.
 */

export type GuidedPhase =
  | "describe"
  | "assist"
  | "followup"
  | "confirm"
  | "manual_all";

export type GuidedFactRow = {
  key: string;
  label_zh: string;
  value_zh: string;
  status: string;
};

export type GuidedFollowupField = {
  field_key: string;
  question_zh: string;
  input_kind: string;
  form_key: string;
};

export type GuidedView = {
  title_zh?: string;
  draft_label_zh?: string;
  fact_rows?: GuidedFactRow[];
  missing_count?: number;
  missing_message_zh?: string;
  followup_questions?: string[];
  followup_fields?: GuidedFollowupField[];
  conflicts?: string[];
  conflict_message_zh?: string;
  show_full_form_option?: boolean;
  full_form_option_zh?: string;
  confirm_title_zh?: string;
  confirm_actions?: {
    accept_zh?: string;
    edit_zh?: string;
    redescribe_zh?: string;
  };
};

export type AccidentStoryProposalLike = {
  incident_summary?: string;
  injury_status?: string;
  accident_time_text?: string;
  accident_location_text?: string;
  followup_questions?: string[];
  missing_required_facts?: string[];
  warnings?: string[];
  conflicts?: string[];
  used_fallback?: boolean;
  guided_view?: GuidedView;
  raw_story?: string;
  proposal_version?: number;
  proposal_id?: string;
};

export type GuidedUiState = {
  guidedPhase: GuidedPhase;
  guidedTitle: string;
  guidedDraftLabel: string;
  guidedFactRows: GuidedFactRow[];
  guidedMissingMessage: string;
  guidedMissingCount: number;
  guidedFollowupFields: GuidedFollowupField[];
  guidedConflictMessage: string;
  guidedShowFullFormLink: boolean;
  guidedFullFormLinkLabel: string;
  guidedConfirmTitle: string;
  guidedAcceptLabel: string;
  guidedEditLabel: string;
  guidedRedescribeLabel: string;
  /** When true, render only follow-up inputs (not the full static form). */
  guidedHideStaticFields: boolean;
  /** When true, show full static Must Have fields. */
  guidedShowAllFields: boolean;
  /** When true, show confirmation review card. */
  guidedShowConfirm: boolean;
};

const EMPTY_GUIDED: GuidedUiState = {
  guidedPhase: "describe",
  guidedTitle: "AI已帮您整理",
  guidedDraftLabel: "AI草稿，尚未确认",
  guidedFactRows: [],
  guidedMissingMessage: "",
  guidedMissingCount: 0,
  guidedFollowupFields: [],
  guidedConflictMessage: "",
  guidedShowFullFormLink: false,
  guidedFullFormLinkLabel: "查看或修改全部信息",
  guidedConfirmTitle: "请确认这些事故事实",
  guidedAcceptLabel: "信息正确，提交",
  guidedEditLabel: "修改",
  guidedRedescribeLabel: "重新描述",
  guidedHideStaticFields: false,
  guidedShowAllFields: true,
  guidedShowConfirm: false,
};

export function emptyGuidedUiState(): GuidedUiState {
  return { ...EMPTY_GUIDED };
}

export function resolveGuidedPhase(
  proposal: AccidentStoryProposalLike | null | undefined,
  opts?: { forceManual?: boolean; forceConfirm?: boolean; confirmed?: boolean },
): GuidedPhase {
  if (opts?.forceManual) return "manual_all";
  if (opts?.forceConfirm || opts?.confirmed) return "confirm";
  if (!proposal) return "describe";
  const guided = proposal.guided_view;
  const missing = Number(
    guided?.missing_count ??
      (Array.isArray(proposal.missing_required_facts)
        ? proposal.missing_required_facts.length
        : 0),
  );
  if (missing > 0) return "followup";
  return "confirm";
}

export function buildGuidedUiState(
  proposal: AccidentStoryProposalLike | null | undefined,
  phase: GuidedPhase,
): GuidedUiState {
  if (!proposal) {
    return {
      ...emptyGuidedUiState(),
      guidedPhase: phase === "manual_all" ? "manual_all" : "describe",
      guidedShowAllFields: true,
      guidedHideStaticFields: false,
      guidedShowConfirm: false,
    };
  }
  const g = proposal.guided_view || {};
  const fields = Array.isArray(g.followup_fields)
    ? g.followup_fields.slice(0, 3)
    : [];
  const missingCount = Number(g.missing_count ?? fields.length) || 0;
  const actions = g.confirm_actions || {};

  const showConfirm = phase === "confirm";
  const showAll = phase === "manual_all" || phase === "describe";
  const hideStatic =
    phase === "followup" || phase === "assist" || phase === "confirm";

  return {
    guidedPhase: phase,
    guidedTitle: String(g.title_zh || "AI已帮您整理"),
    guidedDraftLabel: String(g.draft_label_zh || "AI草稿，尚未确认"),
    guidedFactRows: Array.isArray(g.fact_rows) ? g.fact_rows.slice(0, 8) : [],
    guidedMissingMessage: String(
      g.missing_message_zh ||
        (missingCount > 0 ? `还需要确认 ${missingCount} 项` : "信息已齐，请确认"),
    ),
    guidedMissingCount: missingCount,
    guidedFollowupFields: fields,
    guidedConflictMessage: String(g.conflict_message_zh || ""),
    guidedShowFullFormLink: phase !== "manual_all" && phase !== "describe",
    guidedFullFormLinkLabel: String(g.full_form_option_zh || "查看或修改全部信息"),
    guidedConfirmTitle: String(g.confirm_title_zh || "请确认这些事故事实"),
    guidedAcceptLabel: String(actions.accept_zh || "信息正确，提交"),
    guidedEditLabel: String(actions.edit_zh || "修改"),
    guidedRedescribeLabel: String(actions.redescribe_zh || "重新描述"),
    guidedHideStaticFields: hideStatic && !showAll,
    guidedShowAllFields: showAll,
    guidedShowConfirm: showConfirm,
  };
}

/** Apply known AI proposal values into form only when customer field is empty. */
export function proposalToFormPatch(proposal: AccidentStoryProposalLike): {
  accidentDatetime?: string;
  accidentLocation?: string;
  injuryStatus?: string;
} {
  const patch: {
    accidentDatetime?: string;
    accidentLocation?: string;
    injuryStatus?: string;
  } = {};
  if (proposal.accident_time_text) {
    patch.accidentDatetime = String(proposal.accident_time_text);
  }
  if (proposal.accident_location_text) {
    patch.accidentLocation = String(proposal.accident_location_text);
  }
  if (proposal.injury_status === "yes" || proposal.injury_status === "no") {
    patch.injuryStatus = String(proposal.injury_status);
  }
  return patch;
}

export function followupFieldSatisfied(
  field: GuidedFollowupField,
  form: {
    accidentDatetime?: string;
    accidentLocation?: string;
    injuryStatus?: string;
    description?: string;
  },
): boolean {
  const key = field.form_key || field.field_key;
  if (key === "accidentDatetime" || field.field_key === "accident_datetime") {
    return Boolean(String(form.accidentDatetime || "").trim());
  }
  if (key === "accidentLocation" || field.field_key === "accident_location") {
    return Boolean(String(form.accidentLocation || "").trim());
  }
  if (key === "injuryStatus" || field.field_key === "injury_status") {
    const v = String(form.injuryStatus || "").trim();
    return v === "yes" || v === "no" || v === "unknown";
  }
  if (key === "description" || field.field_key === "accident_description") {
    return Boolean(String(form.description || "").trim());
  }
  return true;
}

export function allFollowupsSatisfied(
  fields: GuidedFollowupField[],
  form: {
    accidentDatetime?: string;
    accidentLocation?: string;
    injuryStatus?: string;
    description?: string;
  },
): boolean {
  if (!fields.length) return true;
  return fields.every((f) => followupFieldSatisfied(f, form));
}
