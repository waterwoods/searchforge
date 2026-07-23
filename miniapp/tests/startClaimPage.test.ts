import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { ApiRequestError } from "../utils/request";

installMiniProgramGlobals();

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

type CapturedPageOptions = {
  data: Record<string, unknown>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadStartClaimPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/start-claim/start-claim");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function createPageContext(page: CapturedPageOptions, overrides?: Record<string, unknown>) {
  const data = { ...(page.data || {}) } as Record<string, any>;
  // Reset Must Have fields so cached Page() options do not leak across tests.
  data.description = "";
  data.charCount = 0;
  data.accidentDatetime = "";
  data.accidentLocation = "";
  data.injuryStatus = "";
  data.canSubmit = false;
  data.missingHint = "请先填写：事故经过、事故时间、事故地点、是否受伤";
  data.fieldErrors = {};
  data.errorMessage = "";
  data.errorRetryable = false;
  data.pageReady = true;
  data.initErrorMessage = "";
  data.busy = { submitting: false, uploading: false };
  const ctx: Record<string, any> = {
    ...page,
    route: "/pages/start-claim/start-claim",
    data,
    _submitState: null,
    _form: {
      description: "",
      accidentDatetime: "",
      accidentLocation: "",
      injuryStatus: "",
    },
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...overrides,
  };
  // Keep data/form overrides coherent when tests pass nested data.
  if (overrides && overrides.data && typeof overrides.data === "object") {
    ctx.data = { ...data, ...(overrides.data as Record<string, unknown>) };
  }
  return ctx;
}

test("app.json registers start-claim pages first", () => {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
  };
  assert.equal(appJson.pages?.[0], "pages/start-claim/start-claim");
  assert.ok(appJson.pages?.includes("pages/start-claim-success/start-claim-success"));
});

test("start-claim wxml asks accident Must Have and never teaches VIN-first", () => {
  const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
  assert.match(wxml, /告诉陈总发生了什么/);
  assert.match(wxml, /事故经过/);
  assert.match(wxml, /事故时间/);
  assert.match(wxml, /事故地点/);
  assert.match(wxml, /是否有人受伤/);
  assert.match(wxml, /提交给陈总/);
  assert.match(wxml, /如需再补充会通知您/);
  assert.match(wxml, /missingHint/);
  assert.match(wxml, /fieldErrors/);
  assert.match(wxml, /Today 9 am/);
  assert.match(wxml, /onTapRecord/);
  assert.match(wxml, /showRecordBtn/);
  assert.match(wxml, /可录音转文字/);
  assert.equal(wxml.includes("Coming soon"), false);
  assert.equal(wxml.includes("Coming Later"), false);
  assert.equal(wxml.includes("请填写 VIN"), false);
  assert.equal(wxml.includes("case_id"), false);
  assert.equal(wxml.includes("aggregate_version"), false);
  assert.equal(wxml.includes("command_id"), false);
});

test("start-claim voice controls are available without wiping typed description", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page, {});
  page.onLoad.call(ctx, { entry: "form" });
  assert.equal(ctx.data.showRecordBtn, true);
  assert.equal(ctx.data.showStopBtn, false);
  assert.match(String(ctx.data.recordBtnLabel || ""), /录音/);

  page.onDescriptionInput.call(ctx, { detail: { value: "先打字填写的事故经过内容。" } });
  assert.equal(ctx.data.description, "先打字填写的事故经过内容。");
  assert.equal(ctx.data.showRecordBtn, true);

  // Mic denial keeps typed text and shows friendly Chinese copy.
  (globalThis as Record<string, any>).wx.authorize = (opts: {
    fail?: () => void;
  }) => {
    opts.fail?.();
  };
  const modals: Array<{ content: string }> = [];
  (globalThis as Record<string, any>).wx.showModal = (opts: { content: string }) => {
    modals.push(opts);
  };
  page.onTapRecord.call(ctx);
  assert.equal(ctx.data.description, "先打字填写的事故经过内容。");
  assert.match(String(ctx.data.voiceHint || ""), /麦克风|打字/);
  assert.ok(modals.some((m) => /麦克风|打字/.test(m.content)));
});

test("founder Must Have values enable CTA and send normalized payload", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  (globalThis as Record<string, any>).wx.showToast = () => {};
  const { loadResumeToken, clearResumeToken } = await import("../utils/storage");
  clearResumeToken();

  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      return Promise.resolve({
        ok: true,
        outcome: "accepted",
        resume_token: "h5t1.p26g-fresh",
      });
    },
  });
  page.onLoad.call(ctx, { entry: "form" });

  page.onDescriptionInput.call(ctx, { detail: { value: " 被车后装 " } });
  page.onDatetimeInput.call(ctx, { detail: { value: "  Today   9 am " } });
  page.onLocationInput.call(ctx, { detail: { value: " 路口 " } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "no" } } });

  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.injuryStatus, "no");
  assert.equal(ctx.data.missingHint, "");
  assert.equal(ctx.data.errorMessage, "");
  // Visible bound values == canonical `_form`.
  assert.equal(ctx.data.description, ctx._form.description);
  assert.equal(ctx.data.accidentDatetime, ctx._form.accidentDatetime);
  assert.equal(ctx.data.accidentLocation, ctx._form.accidentLocation);
  assert.equal(ctx.data.injuryStatus, ctx._form.injuryStatus);

  await page.onSubmit.call(ctx);
  assert.equal(calls.length, 1);
  assert.equal(calls[0]?.accident_description, "被车后装");
  assert.equal(calls[0]?.accident_datetime, "Today 9 am");
  assert.equal(calls[0]?.accident_location, "路口");
  assert.equal(calls[0]?.injury_status, "no");
  assert.equal(ctx.data.description, calls[0]?.accident_description);
  assert.equal(ctx.data.accidentDatetime, calls[0]?.accident_datetime);
  assert.equal(ctx.data.accidentLocation, calls[0]?.accident_location);
  assert.equal(ctx.data.injuryStatus, calls[0]?.injury_status);
  // P26G: resume token → Entry / Task Home (not dead-end success).
  assert.deepEqual(launches, ["/pages/entry/entry"]);
  assert.equal(loadResumeToken(), "h5t1.p26g-fresh");
  clearResumeToken();
});

test("founder live values complete → no missing hint + CTA enabled", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.missingHint, "");
  assert.equal(ctx.data.errorMessage, "");
});

test("injury selection preserves description/time/location", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  // Simulate stale this.data (setData race) while canonical `_form` is correct.
  ctx.data.description = "";
  ctx.data.accidentDatetime = "";
  ctx.data.accidentLocation = "";
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  assert.equal(ctx._form.description, "等红灯时被后装");
  assert.equal(ctx._form.accidentDatetime, "今天上午 9 点");
  assert.equal(ctx._form.accidentLocation, "家门口");
  assert.equal(ctx.data.description, "等红灯时被后装");
  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.errorMessage, "");
  assert.equal(ctx.data.missingHint, "");
});

test("stale missing banner clears when form becomes complete", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { entry: "form" });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  // Force the historical sticky banner shape from showErrors-on-injury.
  ctx.data.errorMessage = "请先填写：事故经过、事故时间、事故地点";
  ctx.data.errorRetryable = false;
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.missingHint, "");
  assert.equal(ctx.data.errorMessage, "");
});

test("submit uses latest typed value from blur flush before API", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => {
    redirects.push(url);
  };
  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      return Promise.resolve({ ok: true, outcome: "accepted" });
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "旧描述" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  // Latest value arrives on blur immediately before submit (device timing).
  page.onDescriptionBlur.call(ctx, { detail: { value: "等红灯时被后装" } });
  await page.onSubmit.call(ctx);
  assert.equal(calls[0]?.accident_description, "等红灯时被后装");
  assert.deepEqual(redirects, ["/pages/start-claim-success/start-claim-success"]);
});

test("local invalid submit does not call API", async () => {
  const page = await loadStartClaimPage();
  let called = 0;
  const ctx = createPageContext(page, {
    callStartClaim() {
      called += 1;
      return Promise.resolve({ ok: true, outcome: "accepted" });
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  await page.onSubmit.call(ctx);
  assert.equal(called, 0);
  assert.match(String(ctx.data.errorMessage || ctx.data.missingHint || ""), /事故时间|事故地点|是否受伤/);
});

test("transport failure maps distinctly and preserves form", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page, {
    callStartClaim() {
      throw new ApiRequestError("domain_not_allowed", 0, {
        errMsg: "request:fail url not in domain list",
      });
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  await page.onSubmit.call(ctx);
  assert.match(String(ctx.data.errorMessage), /域名未授权|报案服务/);
  assert.equal(String(ctx.data.errorMessage).includes("网络不稳定"), false);
  assert.equal(ctx.data.description, "等红灯时被后装");
  assert.equal(ctx.data.canSubmit, true);
});

test("accepted-but-replayed retry reuses identity and opens Task Home", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const { clearResumeToken, loadResumeToken } = await import("../utils/storage");
  clearResumeToken();
  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      if (calls.length === 1) {
        throw new ApiRequestError("timeout");
      }
      return Promise.resolve({
        ok: true,
        outcome: "replayed",
        resume_token: "h5t1.p26g-replay",
      });
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "等红灯时被后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "今天上午 9 点" } });
  page.onLocationInput.call(ctx, { detail: { value: "家门口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "yes" } } });
  await page.onSubmit.call(ctx);
  assert.equal(ctx.data.errorRetryable, true);
  assert.match(String(ctx.data.errorMessage), /超时|重试/);
  const firstId = String(calls[0]?.command_id || "");
  await page.onRetry.call(ctx);
  assert.equal(calls[1]?.command_id, firstId);
  assert.equal(calls[1]?.idempotency_key, calls[0]?.idempotency_key);
  assert.deepEqual(launches, ["/pages/entry/entry"]);
  assert.equal(loadResumeToken(), "h5t1.p26g-replay");
  clearResumeToken();
});

test("submit with missing injury shows field error instead of silent disable-only", async () => {
  const page = await loadStartClaimPage();
  const toasts: string[] = [];
  const scrollTargets: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => {
    toasts.push(title);
  };
  (globalThis as Record<string, any>).wx.pageScrollTo = ({ selector }: { selector: string }) => {
    scrollTargets.push(selector);
  };
  const ctx = createPageContext(page, {
    callStartClaim() {
      throw new Error("should not submit");
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(ctx, { detail: { value: "路口" } });

  assert.equal(ctx.data.canSubmit, false);
  await page.onSubmit.call(ctx);
  assert.match(String(ctx.data.fieldErrors?.injuryStatus || ""), /是否有人受伤/);
  assert.ok(toasts.length >= 1);
  assert.deepEqual(scrollTargets, ["#start-claim-injury"]);
});

test("start-claim-success wxml shows founder-facing receipt copy only", () => {
  const wxml = readFileSync(
    join(miniappRoot, "pages/start-claim-success/start-claim-success.wxml"),
    "utf8",
  );
  assert.match(wxml, /\{\{title\}\}/);
  assert.equal(wxml.includes("case_id"), false);
  assert.equal(wxml.includes("command_id"), false);
});

test("start-claim with active resume redirects to Service Home, keeps token", async () => {
  const page = await loadStartClaimPage();
  const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
  saveResumeToken("h5t1.prior-submitted");
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, {});
  assert.deepEqual(launches, ["/pages/service-home/service-home"]);
  assert.equal(loadResumeToken(), "h5t1.prior-submitted");
  assert.equal(ctx.data.pageReady, true);
});

test("start-claim cold Home without entry redirects to Service Home", async () => {
  const page = await loadStartClaimPage();
  const { clearResumeToken } = await import("../utils/storage");
  clearResumeToken();
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const clean = createPageContext(page);
  page.onLoad.call(clean, {});
  assert.deepEqual(launches, ["/pages/service-home/service-home"]);
});

test("start-claim with entry=form and no resume renders fresh form shell", async () => {
  const page = await loadStartClaimPage();
  const { clearResumeToken } = await import("../utils/storage");
  clearResumeToken();
  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const clean = createPageContext(page);
  page.onLoad.call(clean, { entry: "form" });
  assert.deepEqual(launches, []);
  assert.equal(clean.data.pageReady, true);
  assert.equal(clean.data.initErrorMessage, "");
  assert.equal(clean.data.description, "");
  assert.equal(clean.data.canSubmit, false);
  assert.match(String(clean.data.missingHint || ""), /事故经过/);
  assert.equal(clean.data.accidentDatetime, "");
  assert.equal(clean.data.accidentLocation, "");
  assert.equal(clean.data.injuryStatus, "");
});

test("initialization rejection surfaces error + retry without blanking form", async () => {
  const page = await loadStartClaimPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { entry: "form" });
  ctx.setData({
    initErrorMessage: "页面初始化失败，请重试或联系陈总。",
    pageReady: true,
  });
  assert.match(String(ctx.data.initErrorMessage), /初始化失败|重试/);
  assert.equal(ctx.data.pageReady, true);
  page.onResetAndRetry.call(ctx);
  assert.equal(ctx.data.initErrorMessage, "");
  assert.equal(ctx.data.pageReady, true);
  assert.match(String(ctx.data.missingHint || ""), /事故经过/);
});

test("Home → Start Claim still exposes required fields in wxml", () => {
  const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
  for (const label of ["事故经过", "事故时间", "事故地点", "是否有人受伤", "提交给陈总"]) {
    assert.match(wxml, new RegExp(label));
  }
});

test("start-claim submit is single-flight and retries with same identity", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  let resolveStart: ((value: { ok: boolean; outcome: string }) => void) | null = null;
  const startPromise = new Promise<{ ok: boolean; outcome: string }>((resolve) => {
    resolveStart = resolve;
  });

  const launches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    launches.push(url);
  };
  const { clearResumeToken } = await import("../utils/storage");
  clearResumeToken();

  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      return startPromise;
    },
  });
  page.onLoad.call(ctx, { entry: "form" });
  page.onDescriptionInput.call(ctx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(ctx, { detail: { value: "路口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "no" } } });

  const first = page.submitStartClaim.call(ctx, { reuseIdentity: false });
  const blocked = page.submitStartClaim.call(ctx, { reuseIdentity: false });
  await blocked;
  assert.equal(calls.length, 1);
  assert.equal(ctx.data.busy.submitting, true);

  resolveStart?.({ ok: true, outcome: "accepted", resume_token: "h5t1.p26g-flight" } as any);
  await first;
  assert.deepEqual(launches, ["/pages/entry/entry"]);
  assert.equal(ctx.data.busy.submitting, false);
  clearResumeToken();

  const retryCtx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      if (calls.length === 2) {
        throw new ApiRequestError("network_error");
      }
      return Promise.resolve({ ok: true, outcome: "replayed" });
    },
  });
  page.onLoad.call(retryCtx, { entry: "form" });
  page.onDescriptionInput.call(retryCtx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(retryCtx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(retryCtx, { detail: { value: "路口" } });
  page.onInjurySelect.call(retryCtx, { currentTarget: { dataset: { value: "no" } } });
  await page.submitStartClaim.call(retryCtx, { reuseIdentity: false });
  assert.equal(retryCtx.data.errorRetryable, true);
  const firstId = String(calls[1]?.command_id || "");
  await page.submitStartClaim.call(retryCtx, { reuseIdentity: true });
  assert.equal(calls[2]?.command_id, firstId);
  assert.equal(calls[2]?.idempotency_key, calls[1]?.idempotency_key);
});
