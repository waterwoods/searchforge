/**
 * Guided accident-story UX helpers — unit tests.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  allFollowupsSatisfied,
  buildGuidedUiState,
  emptyGuidedUiState,
  GUIDED_TRUST_NOTE_FALLBACK,
  GUIDED_TRUST_NOTE_NORMAL,
  resolveGuidedPhase,
  resolveGuidedTrustNote,
  type AccidentStoryProposalLike,
} from "../utils/guidedAccidentStory";

const here = dirname(fileURLToPath(import.meta.url));
const startClaimWxml = readFileSync(
  join(here, "../pages/start-claim/start-claim.wxml"),
  "utf8",
);

const incompleteProposal: AccidentStoryProposalLike = {
  incident_summary: "追尾草稿",
  injury_status: "no",
  accident_time_text: "昨天",
  accident_location_text: "",
  missing_required_facts: ["accident_datetime", "accident_location"],
  followup_questions: ["事故大约发生在几点？", "事故发生在哪里？"],
  guided_view: {
    title_zh: "AI已帮您整理",
    draft_label_zh: "AI草稿，尚未确认",
    missing_count: 2,
    missing_message_zh: "还需要确认 2 项",
    fact_rows: [
      { key: "accident_type", label_zh: "事故类型", value_zh: "追尾", status: "known" },
      { key: "accident_datetime", label_zh: "事故时间", value_zh: "昨天，具体时间待确认", status: "partial" },
      { key: "accident_location", label_zh: "事故地点", value_zh: "待确认", status: "pending" },
      { key: "injury_status", label_zh: "受伤情况", value_zh: "没有受伤", status: "known" },
    ],
    followup_fields: [
      {
        field_key: "accident_datetime",
        question_zh: "事故大约发生在几点？",
        input_kind: "text",
        form_key: "accidentDatetime",
      },
      {
        field_key: "accident_location",
        question_zh: "事故发生在哪里？",
        input_kind: "text",
        form_key: "accidentLocation",
      },
    ],
    show_full_form_option: true,
    full_form_option_zh: "查看或修改全部信息",
  },
};

const completeProposal: AccidentStoryProposalLike = {
  incident_summary: "完整",
  injury_status: "no",
  accident_time_text: "昨天下午",
  accident_location_text: "San Jose",
  missing_required_facts: [],
  followup_questions: [],
  guided_view: {
    missing_count: 0,
    missing_message_zh: "信息已齐，请确认",
    fact_rows: [],
    followup_fields: [],
  },
};

describe("guidedAccidentStory", () => {
  it("incomplete story resolves to followup phase with dynamic fields only", () => {
    const phase = resolveGuidedPhase(incompleteProposal);
    assert.equal(phase, "followup");
    const ui = buildGuidedUiState(incompleteProposal, phase);
    assert.equal(ui.guidedMissingCount, 2);
    assert.match(ui.guidedMissingMessage, /还需要确认 2 项/);
    assert.equal(ui.guidedFollowupFields.length, 2);
    assert.equal(ui.guidedHideStaticFields, true);
    assert.equal(ui.guidedShowAllFields, false);
    assert.equal(ui.guidedShowConfirm, false);
    assert.ok(ui.guidedShowFullFormLink);
  });

  it("complete story goes straight to confirm", () => {
    const phase = resolveGuidedPhase(completeProposal);
    assert.equal(phase, "confirm");
    const ui = buildGuidedUiState(completeProposal, phase);
    assert.equal(ui.guidedShowConfirm, true);
    assert.equal(ui.guidedMissingCount, 0);
  });

  it("manual all forces full static fields", () => {
    const phase = resolveGuidedPhase(incompleteProposal, { forceManual: true });
    assert.equal(phase, "manual_all");
    const ui = buildGuidedUiState(incompleteProposal, phase);
    assert.equal(ui.guidedShowAllFields, true);
    assert.equal(ui.guidedHideStaticFields, false);
  });

  it("followup satisfaction tracks answered fields", () => {
    const fields = incompleteProposal.guided_view!.followup_fields!;
    assert.equal(
      allFollowupsSatisfied(fields, { accidentDatetime: "", accidentLocation: "" }),
      false,
    );
    assert.equal(
      allFollowupsSatisfied(fields, {
        accidentDatetime: "昨天下午3点",
        accidentLocation: "Oakland",
      }),
      true,
    );
  });

  it("empty guided state defaults to describe + full fields", () => {
    const empty = emptyGuidedUiState();
    assert.equal(empty.guidedPhase, "describe");
    assert.equal(empty.guidedShowAllFields, true);
  });

  it("normal guided success shows calm trust note (not fallback)", () => {
    assert.equal(resolveGuidedTrustNote(false), GUIDED_TRUST_NOTE_NORMAL);
    const ui = buildGuidedUiState(incompleteProposal, "followup");
    assert.equal(ui.guidedUsedFallback, false);
    assert.equal(ui.guidedTrustNote, GUIDED_TRUST_NOTE_NORMAL);
    assert.match(ui.guidedTrustNote, /请确认后再提交/);
    assert.doesNotMatch(ui.guidedTrustNote, /fallback|category|timeout/i);
  });

  it("used_fallback shows customer fallback copy and does not block confirm", () => {
    const fallbackProposal: AccidentStoryProposalLike = {
      ...completeProposal,
      used_fallback: true,
      guided_view: {
        ...completeProposal.guided_view,
        missing_count: 0,
        fact_rows: [
          { key: "injury_status", label_zh: "受伤情况", value_zh: "没有受伤", status: "known" },
        ],
      },
    };
    assert.equal(resolveGuidedTrustNote(true), GUIDED_TRUST_NOTE_FALLBACK);
    const ui = buildGuidedUiState(fallbackProposal, "confirm");
    assert.equal(ui.guidedUsedFallback, true);
    assert.equal(ui.guidedTrustNote, GUIDED_TRUST_NOTE_FALLBACK);
    assert.match(ui.guidedTrustNote, /仍可直接确认或手动补充/);
    assert.doesNotMatch(ui.guidedTrustNote, /fallback_reason|timeout|category/i);
    // Fallback never blocks intake — confirm CTA and edit paths remain.
    assert.equal(ui.guidedShowConfirm, true);
    assert.equal(ui.guidedAcceptLabel, "信息正确，提交");
    assert.equal(ui.guidedEditLabel, "修改");
    assert.equal(ui.guidedRedescribeLabel, "重新描述");
  });

  it("null proposal manual_all still usable with fallback trust note", () => {
    const ui = buildGuidedUiState(null, "manual_all");
    assert.equal(ui.guidedUsedFallback, true);
    assert.equal(ui.guidedTrustNote, GUIDED_TRUST_NOTE_FALLBACK);
    assert.equal(ui.guidedShowAllFields, true);
    assert.equal(ui.guidedShowConfirm, false);
  });

  it("Start Claim WXML renders trust note and one primary confirm CTA", () => {
    assert.match(startClaimWxml, /storyAssistNote/);
    assert.match(startClaimWxml, /guided-trust-note/);
    assert.match(startClaimWxml, /guidedUsedFallback/);
    const confirmStart = startClaimWxml.indexOf("<!-- Step D: confirmation review -->");
    assert.ok(confirmStart > 0);
    const confirmEnd = startClaimWxml.indexOf("errorMessage", confirmStart);
    const confirmBlock = startClaimWxml.slice(confirmStart, confirmEnd);
    // Exactly one primary button element (do not match hover-class="btn-primary-hover").
    const primaryButtons = confirmBlock.match(/(?:^|\s)class="btn-primary(?:\s|")/gm) || [];
    assert.equal(primaryButtons.length, 1);
    assert.match(confirmBlock, /onConfirmAndSubmit/);
    assert.match(confirmBlock, /guided-confirm-link/);
    assert.match(confirmBlock, /onEditFromConfirm/);
    assert.match(confirmBlock, /onRedescribe/);
    // Secondary actions are text links, not competing buttons.
    assert.doesNotMatch(confirmBlock, /btn-secondary/);
  });
});
