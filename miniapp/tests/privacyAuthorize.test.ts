import test from "node:test";
import assert from "node:assert/strict";

import { installMiniProgramGlobals } from "./miniprogramMocks";
import {
  ensureMicrophoneReady,
  ensurePrivacyAuthorized,
  resetPrivacyAuthorizeInFlightForTests,
} from "../utils/privacyAuthorize";
import { choosePhoto } from "../services/mediaCaptureAdapter";
import {
  classifyVoiceFirstFailure,
  VOICE_FIRST_FAILURE_COPY,
  VOICE_FIRST_SECONDARY_TEXT,
} from "../utils/voiceFirstIntake";

installMiniProgramGlobals();

function wxMock(): Record<string, any> {
  return (globalThis as Record<string, any>).wx;
}

function resetPrivacyMocks(): void {
  resetPrivacyAuthorizeInFlightForTests();
  const wx = wxMock();
  delete wx.getPrivacySetting;
  delete wx.requirePrivacyAuthorize;
  wx.authorize = (opts?: { success?: () => void; fail?: () => void }) => {
    opts?.success?.();
  };
  wx.showModal = (opts?: {
    success?: (res: { confirm?: boolean; cancel?: boolean }) => void;
  }) => {
    opts?.success?.({ confirm: true });
  };
  wx.chooseMedia = ({
    success,
  }: {
    success?: (res: { tempFiles: Array<{ tempFilePath: string; size: number }> }) => void;
  }) => {
    success?.({ tempFiles: [{ tempFilePath: "/tmp/privacy-photo.jpg", size: 1200 }] });
  };
}

test("privacy already authorized → microphone proceeds", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  let authorizeCalls = 0;
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: false });
  };
  wx.authorize = (opts: { scope: string; success?: () => void }) => {
    authorizeCalls += 1;
    assert.equal(opts.scope, "scope.record");
    opts.success?.();
  };

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, true);
  assert.equal(ready.stage, "ready");
  assert.equal(ready.privacyStatus, "already_authorized");
  assert.equal(authorizeCalls, 1);
});

test("privacy authorization required → approve → microphone proceeds", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  const modals: string[] = [];
  let requireCalls = 0;
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: true });
  };
  wx.showModal = (opts: {
    content?: string;
    success?: (res: { confirm?: boolean }) => void;
  }) => {
    modals.push(String(opts.content || ""));
    opts.success?.({ confirm: true });
  };
  wx.requirePrivacyAuthorize = (opts: { success?: () => void }) => {
    requireCalls += 1;
    opts.success?.();
  };

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, true);
  assert.equal(ready.stage, "ready");
  assert.equal(ready.privacyStatus, "authorized");
  assert.equal(requireCalls, 1);
  assert.ok(modals.some((c) => c.includes("麦克风") && c.includes("事故描述")));
});

test("privacy declined → recording does not start (ensureMicrophoneReady fails at privacy)", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  let authorizeCalls = 0;
  let requireCalls = 0;
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: true });
  };
  wx.showModal = (opts: { success?: (res: { confirm?: boolean }) => void }) => {
    opts.success?.({ confirm: false });
  };
  wx.requirePrivacyAuthorize = (opts: { success?: () => void; fail?: () => void }) => {
    requireCalls += 1;
    opts.fail?.();
  };
  wx.authorize = () => {
    authorizeCalls += 1;
  };

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, false);
  assert.equal(ready.stage, "privacy");
  assert.equal(ready.reason, "privacy_denied");
  assert.equal(authorizeCalls, 0);
  assert.equal(requireCalls, 0);
});

test("privacy_denied failure copy keeps text fallback available", () => {
  assert.match(VOICE_FIRST_FAILURE_COPY.privacy_denied, /文字输入/);
  assert.match(VOICE_FIRST_SECONDARY_TEXT, /不方便录音/);
  assert.equal(classifyVoiceFirstFailure("privacy_denied"), "privacy_denied");
});

test("scope.record denied → bounded scope failure after privacy ok", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: false });
  };
  wx.authorize = (opts: { fail?: () => void }) => {
    opts.fail?.();
  };

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, false);
  assert.equal(ready.stage, "scope");
  assert.equal(ready.reason, "scope_denied");
});

test("privacy approved but microphone denied → safe fallback", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: true });
  };
  wx.showModal = (opts: { success?: (res: { confirm?: boolean }) => void }) => {
    opts.success?.({ confirm: true });
  };
  wx.requirePrivacyAuthorize = (opts: { success?: () => void }) => {
    opts.success?.();
  };
  wx.authorize = (opts: { fail?: () => void }) => {
    opts.fail?.();
  };

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, false);
  assert.equal(ready.stage, "scope");
  assert.equal(ready.reason, "scope_denied");
  assert.equal(ready.privacyStatus, "authorized");
});

test("privacy API unavailable/older runtime → supported compatibility proceed", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  delete wx.getPrivacySetting;
  delete wx.requirePrivacyAuthorize;

  const privacy = await ensurePrivacyAuthorized("record");
  assert.equal(privacy.ok, true);
  assert.equal(privacy.status, "unsupported");

  const ready = await ensureMicrophoneReady();
  assert.equal(ready.ok, true);
  assert.equal(ready.privacyStatus, "unsupported");
});

test("repeated tap does not create multiple privacy flows", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  let settingCalls = 0;
  let resolveSetting: ((res: { needAuthorization: boolean }) => void) | null = null;
  wx.getPrivacySetting = ({
    success,
  }: {
    success?: (res: { needAuthorization: boolean }) => void;
  }) => {
    settingCalls += 1;
    resolveSetting = success || null;
  };

  const first = ensurePrivacyAuthorized("record");
  const second = await ensurePrivacyAuthorized("record");
  assert.equal(second.ok, false);
  assert.equal(second.status, "busy");
  assert.equal(settingCalls, 1);

  resolveSetting?.({ needAuthorization: false });
  const firstResult = await first;
  assert.equal(firstResult.ok, true);
  assert.equal(firstResult.status, "already_authorized");
});

test("recording gate still ready after successful authorization", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: true });
  };
  wx.showModal = (opts: { success?: (res: { confirm?: boolean }) => void }) => {
    opts.success?.({ confirm: true });
  };
  wx.requirePrivacyAuthorize = (opts: { success?: () => void }) => {
    opts.success?.();
  };

  const first = await ensureMicrophoneReady();
  assert.equal(first.ok, true);

  // Second session: already authorized — no disclosure loop.
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: false });
  };
  let modalCalls = 0;
  wx.showModal = () => {
    modalCalls += 1;
  };
  const second = await ensureMicrophoneReady();
  assert.equal(second.ok, true);
  assert.equal(second.privacyStatus, "already_authorized");
  assert.equal(modalCalls, 0);
});

test("photo/media path remains safe when privacy declined", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  let chooseCalls = 0;
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: true });
  };
  wx.showModal = (opts: { success?: (res: { confirm?: boolean }) => void }) => {
    opts.success?.({ confirm: false });
  };
  wx.chooseMedia = () => {
    chooseCalls += 1;
  };

  await assert.rejects(() => choosePhoto(), /privacy_denied/);
  assert.equal(chooseCalls, 0);
});

test("photo/media path proceeds after privacy already authorized", async () => {
  resetPrivacyMocks();
  const wx = wxMock();
  wx.getPrivacySetting = ({ success }: { success?: (res: { needAuthorization: boolean }) => void }) => {
    success?.({ needAuthorization: false });
  };

  const photo = await choosePhoto();
  assert.equal(photo.tempFilePath, "/tmp/privacy-photo.jpg");
});
