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
  data.busy = { submitting: false };
  const ctx: Record<string, any> = {
    ...page,
    ...overrides,
    route: "/pages/start-claim/start-claim",
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
  };
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
  assert.equal(wxml.includes("Coming soon"), false);
  assert.equal(wxml.includes("Coming Later"), false);
  assert.equal(wxml.includes("请填写 VIN"), false);
  assert.equal(wxml.includes("case_id"), false);
  assert.equal(wxml.includes("aggregate_version"), false);
  assert.equal(wxml.includes("command_id"), false);
});

test("founder Must Have values enable CTA and send normalized payload", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => {
    redirects.push(url);
  };
  (globalThis as Record<string, any>).wx.showToast = () => {};

  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      return Promise.resolve({ ok: true, outcome: "accepted" });
    },
  });
  page.onLoad.call(ctx);

  page.onDescriptionInput.call(ctx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(ctx, { detail: { value: "路口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "no" } } });

  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.injuryStatus, "no");
  assert.equal(ctx.data.missingHint, "");

  await page.onSubmit.call(ctx);
  assert.equal(calls.length, 1);
  assert.equal(calls[0]?.accident_description, "被车后装");
  assert.equal(calls[0]?.accident_datetime, "Today 9 am");
  assert.equal(calls[0]?.accident_location, "路口");
  assert.equal(calls[0]?.injury_status, "no");
  assert.deepEqual(redirects, ["/pages/start-claim-success/start-claim-success"]);
});

test("submit with missing injury shows field error instead of silent disable-only", async () => {
  const page = await loadStartClaimPage();
  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => {
    toasts.push(title);
  };
  const ctx = createPageContext(page, {
    callStartClaim() {
      throw new Error("should not submit");
    },
  });
  page.onLoad.call(ctx);
  page.onDescriptionInput.call(ctx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(ctx, { detail: { value: "路口" } });

  assert.equal(ctx.data.canSubmit, false);
  await page.onSubmit.call(ctx);
  assert.match(String(ctx.data.fieldErrors?.injuryStatus || ""), /是否有人受伤/);
  assert.ok(toasts.length >= 1);
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

test("start-claim submit is single-flight and retries with same identity", async () => {
  const page = await loadStartClaimPage();
  const calls: Array<Record<string, unknown>> = [];
  let resolveStart: ((value: { ok: boolean; outcome: string }) => void) | null = null;
  const startPromise = new Promise<{ ok: boolean; outcome: string }>((resolve) => {
    resolveStart = resolve;
  });

  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => {
    redirects.push(url);
  };

  const ctx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      return startPromise;
    },
  });
  page.onLoad.call(ctx);
  page.onDescriptionInput.call(ctx, { detail: { value: "被车后装" } });
  page.onDatetimeInput.call(ctx, { detail: { value: "Today 9 am" } });
  page.onLocationInput.call(ctx, { detail: { value: "路口" } });
  page.onInjurySelect.call(ctx, { currentTarget: { dataset: { value: "no" } } });

  const first = page.submitStartClaim.call(ctx, { reuseIdentity: false });
  const blocked = page.submitStartClaim.call(ctx, { reuseIdentity: false });
  await blocked;
  assert.equal(calls.length, 1);
  assert.equal(ctx.data.busy.submitting, true);

  resolveStart?.({ ok: true, outcome: "accepted" });
  await first;
  assert.deepEqual(redirects, ["/pages/start-claim-success/start-claim-success"]);
  assert.equal(ctx.data.busy.submitting, false);

  const retryCtx = createPageContext(page, {
    callStartClaim(command: Record<string, unknown>) {
      calls.push(command);
      if (calls.length === 2) {
        throw new ApiRequestError("network_error");
      }
      return Promise.resolve({ ok: true, outcome: "replayed" });
    },
  });
  page.onLoad.call(retryCtx);
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
