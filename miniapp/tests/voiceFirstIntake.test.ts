/**
 * Voice-first Guided Intake V1 — pure util + Start Claim front-door regression.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { ApiRequestError } from "../utils/request";
import {
  classifyVoiceFirstFailure,
  emptyVoiceFirstUi,
  leaveVoiceFrontDoor,
  resolveVoiceFrontDoor,
  VOICE_FIRST_MIC_LABEL,
  VOICE_FIRST_SECONDARY_TEXT,
  voiceFirstFailureCopy,
  voiceFirstUiPatch,
} from "../utils/voiceFirstIntake";
import {
  buildGuidedUiState,
  resolveGuidedPhase,
  type AccidentStoryProposalLike,
} from "../utils/guidedAccidentStory";

installMiniProgramGlobals();

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

describe("voiceFirstIntake resolveFrontDoor", () => {
  it("defaults to voice when flag enabled", () => {
    assert.equal(resolveVoiceFrontDoor({ entry: "form" }, { enabled: true }), "voice");
    assert.equal(resolveVoiceFrontDoor({}, { enabled: true }), "voice");
  });

  it("mode=text|legacy|form keeps existing text intake", () => {
    assert.equal(resolveVoiceFrontDoor({ mode: "text" }, { enabled: true }), "text");
    assert.equal(resolveVoiceFrontDoor({ mode: "legacy" }, { enabled: true }), "text");
    assert.equal(resolveVoiceFrontDoor({ mode: "form" }, { enabled: true }), "text");
  });

  it("mode=full and voice=0 preserve full / text fallbacks", () => {
    assert.equal(resolveVoiceFrontDoor({ mode: "full" }, { enabled: true }), "full");
    assert.equal(resolveVoiceFrontDoor({ voice: "0" }, { enabled: true }), "text");
    assert.equal(resolveVoiceFrontDoor({ entry: "form" }, { enabled: false }), "text");
  });
});

describe("voiceFirstIntake failure fallbacks", () => {
  it("classifies mic / network / empty STT failures", () => {
    assert.equal(
      classifyVoiceFirstFailure(new ApiRequestError("network_error")),
      "network_failed",
    );
    assert.equal(
      classifyVoiceFirstFailure(new ApiRequestError("empty", 400, { error_kind: "empty" })),
      "empty_transcript",
    );
    assert.equal(classifyVoiceFirstFailure("mic permission denied"), "mic_denied");
  });

  it("every failure copy offers retry or text/full path language", () => {
    for (const kind of [
      "mic_denied",
      "recording_failed",
      "stt_failed",
      "empty_transcript",
      "network_failed",
      "ai_failed",
      "unsupported",
    ] as const) {
      const copy = voiceFirstFailureCopy(kind);
      assert.ok(copy.length > 0);
      assert.match(copy, /文字|表单|重试|重录|补充/);
    }
  });

  it("failed UI keeps secondary fallbacks visible", () => {
    const ui = voiceFirstUiPatch("voice", "failed", { failureKind: "stt_failed" });
    assert.equal(ui.showVoiceFrontDoor, true);
    assert.equal(ui.voiceFirstShowRetry, true);
    assert.equal(ui.voiceFirstSecondaryText, VOICE_FIRST_SECONDARY_TEXT);
    assert.match(ui.voiceFirstStatus, /文字/);
  });

  it("leaveVoiceFrontDoor hides mic shell for text/full", () => {
    assert.equal(leaveVoiceFrontDoor("text").showVoiceFrontDoor, false);
    assert.equal(leaveVoiceFrontDoor("full").frontDoor, "full");
    assert.equal(emptyVoiceFirstUi("voice").voiceFirstMicLabel, VOICE_FIRST_MIC_LABEL);
  });
});

describe("voiceFirstIntake guided missing-fact contract", () => {
  it("complete story → confirm, no unnecessary follow-ups", () => {
    const proposal: AccidentStoryProposalLike = {
      missing_required_facts: [],
      followup_questions: [],
      guided_view: { missing_count: 0, followup_fields: [], fact_rows: [] },
    };
    assert.equal(resolveGuidedPhase(proposal), "confirm");
    const ui = buildGuidedUiState(proposal, "confirm");
    assert.equal(ui.guidedShowConfirm, true);
    assert.equal(ui.guidedFollowupFields.length, 0);
  });

  it("incomplete story → <=3 follow-up fields", () => {
    const proposal: AccidentStoryProposalLike = {
      missing_required_facts: ["accident_datetime", "accident_location", "injury_status", "extra"],
      followup_questions: ["q1", "q2", "q3", "q4"],
      guided_view: {
        missing_count: 3,
        followup_fields: [
          { field_key: "accident_datetime", question_zh: "几点？", input_kind: "text", form_key: "accidentDatetime" },
          { field_key: "accident_location", question_zh: "哪里？", input_kind: "text", form_key: "accidentLocation" },
          { field_key: "injury_status", question_zh: "受伤？", input_kind: "injury", form_key: "injuryStatus" },
          { field_key: "extra", question_zh: "extra", input_kind: "text", form_key: "extra" },
        ],
      },
    };
    const ui = buildGuidedUiState(proposal, resolveGuidedPhase(proposal));
    assert.equal(ui.guidedPhase, "followup");
    assert.ok(ui.guidedFollowupFields.length <= 3);
  });
});

describe("voiceFirstIntake Start Claim page wiring", () => {
  it("wxml keeps voice door + text/full escapes + old form", () => {
    const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
    assert.match(wxml, /showVoiceFrontDoor/);
    assert.match(wxml, /onChooseTextInput/);
    assert.match(wxml, /onChooseFullForm/);
    assert.match(wxml, /voice-first-mic/);
    assert.match(wxml, /事故经过/);
    assert.match(wxml, /guidedShowConfirm/);
  });

  it("default entry=form opens voice front door; mode=text keeps classic form", async () => {
    await import("../pages/start-claim/start-claim");
    const page = getLatestPage().options as Record<string, any>;
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    (globalThis as { getApp?: () => Record<string, unknown> }).getApp = () => ({
      taskToken: "",
      task: undefined,
    });
    wx.login = (opts: any) => opts.success?.({ code: "sim:voice-first" });
    wx.request = (opts: any) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
      else if (url.includes("/customer/session")) {
        opts.success?.({ statusCode: 200, data: { ok: true, session_id: "wx_vf_01" } });
      } else if (url.includes("/customer/context")) {
        opts.success?.({
          statusCode: 200,
          data: { has_active_case: false, resume_token: "", next_action: "START_NEW_CLAIM" },
        });
      } else opts.success?.({ statusCode: 500, data: {} });
    };

    const baseData = { ...(page.data || {}) };
    const mkCtx = (launch: Record<string, string>) => {
      const data = { ...baseData };
      const ctx: Record<string, any> = {
        ...page,
        data,
        _submitState: null,
        _divertedToHome: false,
        _gateInFlight: false,
        _navigatingAway: false,
        _launchOptions: launch,
        _smartPlan: null,
        _confirmSelections: {},
        _demoInviteActive: false,
        _storyProposal: null,
        _guidedConfirmed: false,
        _forceManualAll: false,
        _voiceFirstFailure: null,
        _form: {
          description: "",
          accidentDatetime: "",
          accidentLocation: "",
          injuryStatus: "",
        },
        setData(patch: Record<string, unknown>) {
          Object.assign(this.data, patch);
        },
      };
      return ctx;
    };

    const voiceCtx = mkCtx({ entry: "form" });
    await page.onLoad.call(voiceCtx, { entry: "form" });
    assert.equal(voiceCtx.data.formAuthorized, true);
    assert.equal(voiceCtx.data.showVoiceFrontDoor, true);
    assert.equal(voiceCtx.data.frontDoor, "voice");
    assert.match(String(voiceCtx.data.voiceFirstMicLabel || ""), /说一下发生了什么/);

    // Mic denied → stay on door with text fallback (no dead end).
    wx.authorize = (opts: { fail?: () => void }) => opts.fail?.();
    wx.showModal = () => {};
    await page.onTapRecord.call(voiceCtx);
    assert.equal(voiceCtx.data.showVoiceFrontDoor, true);
    assert.equal(voiceCtx.data.voiceFirstPhase, "failed");
    assert.match(String(voiceCtx.data.voiceFirstStatus || ""), /文字|表单/);

    page.onChooseTextInput.call(voiceCtx);
    assert.equal(voiceCtx.data.showVoiceFrontDoor, false);
    assert.equal(voiceCtx.data.frontDoor, "text");

    // Privacy declined → no recording; text fallback remains.
    const privacyCtx = mkCtx({ entry: "form" });
    await page.onLoad.call(privacyCtx, { entry: "form" });
    privacyCtx.data.description = "已有文字草稿";
    wx.getPrivacySetting = (opts: { success?: (res: { needAuthorization: boolean }) => void }) => {
      opts.success?.({ needAuthorization: true });
    };
    wx.showModal = (opts: { success?: (res: { confirm?: boolean }) => void }) => {
      opts.success?.({ confirm: false });
    };
    let started = 0;
    wx.getRecorderManager = () => ({
      start: () => {
        started += 1;
      },
      stop: () => undefined,
      onStart: () => undefined,
      onStop: () => undefined,
      onError: () => undefined,
    });
    await page.onTapRecord.call(privacyCtx);
    assert.equal(started, 0);
    assert.equal(privacyCtx.data.description, "已有文字草稿");
    assert.equal(privacyCtx.data.showVoiceFrontDoor, true);
    assert.equal(privacyCtx.data.voiceFirstPhase, "failed");
    assert.match(String(privacyCtx.data.voiceFirstStatus || ""), /隐私|文字/);
    assert.match(String(privacyCtx.data.voiceFirstSecondaryText || ""), /不方便录音/);

    const textCtx = mkCtx({ entry: "form", mode: "text" });
    await page.onLoad.call(textCtx, { entry: "form", mode: "text" });
    assert.equal(textCtx.data.showVoiceFrontDoor, false);
    assert.equal(textCtx.data.frontDoor, "text");

    const fullCtx = mkCtx({ entry: "form", mode: "full" });
    await page.onLoad.call(fullCtx, { entry: "form", mode: "full" });
    assert.equal(fullCtx.data.showVoiceFrontDoor, false);
    assert.equal(fullCtx.data.frontDoor, "full");
    assert.equal(fullCtx.data.guidedShowAllFields, true);
  });

  it("STT success path fills editable transcript then leaves voice door after organize", async () => {
    await import("../pages/start-claim/start-claim");
    const page = getLatestPage().options as Record<string, any>;
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    (globalThis as { getApp?: () => Record<string, unknown> }).getApp = () => ({
      taskToken: "",
      task: undefined,
    });
    wx.login = (opts: any) => opts.success?.({ code: "sim:voice-stt" });
    wx.request = (opts: any) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
      else if (url.includes("/customer/session")) {
        opts.success?.({ statusCode: 200, data: { ok: true, session_id: "wx_vf_stt" } });
      } else if (url.includes("/customer/context")) {
        opts.success?.({
          statusCode: 200,
          data: { has_active_case: false, resume_token: "", next_action: "START_NEW_CLAIM" },
        });
      } else if (url.includes("/accident-story/propose")) {
        opts.success?.({
          statusCode: 200,
          data: {
            ok: true,
            proposal: {
              incident_summary: "追尾草稿",
              injury_status: "no",
              accident_time_text: "昨天",
              accident_location_text: "",
              missing_required_facts: ["accident_datetime", "accident_location"],
              followup_questions: ["事故大约发生在几点？", "事故发生在哪里？"],
              authority_note: "ai_proposed_until_customer_confirms",
              guided_view: {
                missing_count: 2,
                missing_message_zh: "还需要确认 2 项",
                fact_rows: [
                  { key: "what_happened", label_zh: "发生了什么", value_zh: "追尾", status: "known" },
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
              },
            },
          },
        });
      } else opts.success?.({ statusCode: 500, data: {} });
    };
    wx.uploadFile = (opts: any) => {
      opts.success?.({
        statusCode: 200,
        data: JSON.stringify({
          raw_transcript: "昨天在路口被追尾，没有人受伤。",
          speech_provider: "google_chirp",
          stt_latency_ms: 120,
        }),
      });
    };

    const data = { ...(page.data || {}) };
    const ctx: Record<string, any> = {
      ...page,
      data,
      _submitState: null,
      _divertedToHome: false,
      _gateInFlight: false,
      _navigatingAway: false,
      _launchOptions: { entry: "form" },
      _smartPlan: null,
      _confirmSelections: {},
      _demoInviteActive: false,
      _storyProposal: null,
      _guidedConfirmed: false,
      _forceManualAll: false,
      _voiceFirstFailure: null,
      _form: {
        description: "",
        accidentDatetime: "",
        accidentLocation: "",
        injuryStatus: "",
      },
      setData(patch: Record<string, unknown>) {
        Object.assign(this.data, patch);
      },
    };
    await page.onLoad.call(ctx, { entry: "form" });
    assert.equal(ctx.data.showVoiceFrontDoor, true);

    await page._onRecordStop.call(ctx, {
      tempFilePath: "wxfile://tmp/voice.mp3",
      duration: 2500,
      fileSize: 4096,
    });

    assert.match(String(ctx.data.description || ""), /追尾/);
    assert.equal(ctx.data.showVoiceFrontDoor, false);
    assert.ok(ctx._storyProposal);
    assert.equal(ctx._guidedConfirmed, false);
    assert.equal(ctx.data.guidedPhase, "followup");
    assert.ok((ctx.data.guidedFollowupFields || []).length <= 3);
    assert.equal(String(ctx._storyProposal.authority_note || ""), "ai_proposed_until_customer_confirms");
  });

  it("STT failure stays on voice door with text fallback", async () => {
    await import("../pages/start-claim/start-claim");
    const page = getLatestPage().options as Record<string, any>;
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    (globalThis as { getApp?: () => Record<string, unknown> }).getApp = () => ({
      taskToken: "",
      task: undefined,
    });
    wx.login = (opts: any) => opts.success?.({ code: "sim:voice-fail" });
    wx.request = (opts: any) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
      else if (url.includes("/customer/session")) {
        opts.success?.({ statusCode: 200, data: { ok: true, session_id: "wx_vf_fail" } });
      } else if (url.includes("/customer/context")) {
        opts.success?.({
          statusCode: 200,
          data: { has_active_case: false, resume_token: "", next_action: "START_NEW_CLAIM" },
        });
      } else opts.success?.({ statusCode: 500, data: {} });
    };
    wx.uploadFile = (opts: any) => {
      opts.fail?.({ errMsg: "uploadFile:fail" });
    };

    const data = { ...(page.data || {}) };
    const ctx: Record<string, any> = {
      ...page,
      data,
      _submitState: null,
      _divertedToHome: false,
      _gateInFlight: false,
      _navigatingAway: false,
      _launchOptions: { entry: "form" },
      _smartPlan: null,
      _confirmSelections: {},
      _demoInviteActive: false,
      _storyProposal: null,
      _guidedConfirmed: false,
      _forceManualAll: false,
      _voiceFirstFailure: null,
      _form: {
        description: "",
        accidentDatetime: "",
        accidentLocation: "",
        injuryStatus: "",
      },
      setData(patch: Record<string, unknown>) {
        Object.assign(this.data, patch);
      },
    };
    await page.onLoad.call(ctx, { entry: "form" });
    await page._onRecordStop.call(ctx, {
      tempFilePath: "wxfile://tmp/voice.mp3",
      duration: 1000,
      fileSize: 1024,
    });
    assert.equal(ctx.data.showVoiceFrontDoor, true);
    assert.equal(ctx.data.voiceFirstPhase, "failed");
    assert.match(String(ctx.data.voiceFirstStatus || ctx.data.voiceHint || ""), /文字|识别|网络|失败/);
  });
});
