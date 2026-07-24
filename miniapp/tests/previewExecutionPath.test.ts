/**
 * P36 QA Preview — execution path verification ONLY.
 * Proves checkpoint order and first abort before REQUEST_SENT.
 * Does not call backend.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { appConfig } from "../utils/config";
import type { QaPathStep } from "../utils/qaPathLog";

installMiniProgramGlobals();

type Captured = {
  step: QaPathStep;
  detail: Record<string, string | number | boolean>;
};

function installPathCapture(): { steps: Captured[]; restore: () => void } {
  const steps: Captured[] = [];
  const original = console.info;
  console.info = (...args: unknown[]) => {
    const tag = String(args[0] || "");
    if (tag.startsWith("[QA_PATH] ")) {
      const step = tag.slice("[QA_PATH] ".length) as QaPathStep;
      const detail = (args[1] || {}) as Record<string, string | number | boolean>;
      steps.push({ step, detail });
    }
  };
  return {
    steps,
    restore: () => {
      console.info = original;
    },
  };
}

function stepNames(steps: Captured[]): string[] {
  return steps.map((s) => s.step);
}

function first(steps: Captured[], name: QaPathStep): Captured | undefined {
  return steps.find((s) => s.step === name);
}

test("instrumentation emits LAUNCH from app.ts", () => {
  const appTs = readFileSync(join(__dirname, "../app.ts"), "utf8");
  assert.match(appTs, /qaPathLog\("LAUNCH"/);
  assert.match(appTs, /getLaunchOptionsSync|onLaunch/);
});

test("frozen Preview defaults: pages[0] is start-claim with empty token config", () => {
  const appJson = JSON.parse(readFileSync(join(__dirname, "../app.json"), "utf8"));
  assert.equal(appJson.pages[0], "pages/start-claim/start-claim");
  assert.equal(String(appConfig.devTaskToken || "").trim(), "");
});

test("PATH A — default/pages[0] Start Claim: stops before REQUEST_SENT", async () => {
  const { steps, restore } = installPathCapture();
  try {
    const { clearPrototypeSession } = await import("../utils/storage");
    clearPrototypeSession();
    // Simulate App LAUNCH for pages[0]
    const { qaPathLog, summarizeLaunchQuery } = await import("../utils/qaPathLog");
    const q = summarizeLaunchQuery({});
    qaPathLog("LAUNCH", {
      source: "test.pages0",
      path: "pages/start-claim/start-claim",
      queryKeys: q.queryKeys,
      hasToken: q.hasToken,
    });

    await import("../pages/start-claim/start-claim");
    const page = getLatestPage().options as {
      onLoad: (opts: Record<string, string | undefined>) => void;
      data: Record<string, unknown>;
      setData: (patch: Record<string, unknown>) => void;
      [key: string]: unknown;
    };
    const ctx: Record<string, any> = {
      data: { ...(page.data || {}), pageReady: false },
      setData(patch: Record<string, unknown>) {
        Object.assign(this.data, patch);
      },
      _submitState: null,
      _form: null,
      _applyFormPatch() {
        return { canSubmit: false };
      },
    };
    // Bind page methods
    Object.assign(ctx, page);
    // Cold pages[0] without ?entry=form → Service Home (D-008); no create API.
    page.onLoad.call(ctx, {});

    const names = stepNames(steps);
    assert.ok(names.includes("LAUNCH"), `missing LAUNCH: ${names.join(",")}`);
    assert.ok(names.includes("ENTRY"), `missing ENTRY: ${names.join(",")}`);
    assert.ok(names.includes("EARLY_EXIT"), `missing EARLY_EXIT: ${names.join(",")}`);
    assert.equal(names.includes("REQUEST_START"), false);
    assert.equal(names.includes("REQUEST_SENT"), false);

    const entry = first(steps, "ENTRY")!;
    assert.equal(entry.detail.page, "pages/start-claim/start-claim");
    assert.equal(entry.detail.hasToken, false);

    const abort = first(steps, "EARLY_EXIT")!;
    assert.equal(abort.detail.reason, "capsule_home_redirect_service_home");
    assert.equal(abort.detail.hasToken, false);
    assert.equal(abort.detail.page, "pages/start-claim/start-claim");
    assert.equal(abort.detail.launchPath, "pages/start-claim/start-claim");

    // Intentional form entry: Customer Context gate runs; create-claim never fires.
    steps.length = 0;
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts: any) => opts.success?.({ code: "sim:path-a-form" });
    wx.request = (opts: any) => {
      if (opts.url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
      else if (opts.url.includes("/customer/session")) {
        opts.success?.({ statusCode: 200, data: { session_id: "wx_path_a_form_01" } });
      } else if (opts.url.includes("/customer/context")) {
        opts.success?.({
          statusCode: 200,
          data: { has_active_case: false, next_action: "START_NEW_CLAIM" },
        });
      } else {
        opts.fail?.({ errMsg: "unexpected" });
      }
    };
    Object.assign(ctx, page);
    ctx._divertedToHome = false;
    ctx._gateInFlight = false;
    ctx._navigatingAway = false;
    await page.onLoad.call(ctx, { entry: "form" });
    const formNames = stepNames(steps);
    assert.ok(formNames.includes("BOOTSTRAP"), `missing BOOTSTRAP: ${formNames.join(",")}`);
    assert.equal(ctx.data.formAuthorized, true);
    assert.equal(
      steps.some((s) => String(s.detail.path || "").includes("/customer/start-claim")),
      false,
    );
    assert.equal(first(steps, "BOOTSTRAP")!.detail.phase, "form_authorized_by_customer_context");
  } finally {
    restore();
  }
});

test("PATH B — Entry compile mode with empty query resolves Customer Context", async () => {
  const { steps, restore } = installPathCapture();
  try {
    const { qaPathLog, summarizeLaunchQuery } = await import("../utils/qaPathLog");
    const q = summarizeLaunchQuery({});
    qaPathLog("LAUNCH", {
      source: "test.entry_compile",
      path: "pages/entry/entry",
      queryKeys: q.queryKeys,
      hasToken: q.hasToken,
    });

    const { resetMiniProgramCaptures } = await import("./miniprogramMocks");
    resetMiniProgramCaptures();
    await import("../pages/entry/entry");
    const page = getLatestPage().options as {
      onLoad: (opts: Record<string, string | undefined>) => void;
      bootstrap: (opts: Record<string, string | undefined>) => Promise<void>;
      data: Record<string, any>;
      behaviors?: Array<Record<string, any>>;
      [key: string]: any;
    };

    const behavior = (page.behaviors?.[0] || {}) as {
      data?: Record<string, unknown>;
      methods?: Record<string, (...args: any[]) => any>;
    };
    const ctx: Record<string, any> = {
      route: "pages/entry/entry",
      data: {
        ...(behavior.data || {}),
        ...(page.data || {}),
        busy: {
          loading: false,
          saving: false,
          uploading: false,
          submitting: false,
          navigating: false,
          retrying: false,
        },
        launchSource: "",
        errorState: { code: "", message: "", retryable: false, blocking: false },
        retryMeta: { attempts: 0, cooldownUntil: 0 },
      },
      setData(patch: Record<string, unknown>) {
        Object.assign(this.data, patch);
      },
      ...(behavior.methods || {}),
      ...page,
    };

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts: any) => opts.success?.({ code: "sim:path-b-entry" });
    wx.request = (opts: any) => {
      if (opts.url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
      else if (opts.url.includes("/customer/session")) {
        opts.success?.({ statusCode: 200, data: { session_id: "wx_path_b_entry_01" } });
      } else if (opts.url.includes("/customer/context")) {
        opts.success?.({
          statusCode: 200,
          data: { has_active_case: false, next_action: "START_NEW_CLAIM" },
        });
      } else {
        opts.fail?.({ errMsg: "unexpected" });
      }
    };
    wx.reLaunch = () => undefined;
    await page.onLoad.call(ctx, {});

    const names = stepNames(steps);
    assert.ok(names.includes("LAUNCH"));
    assert.ok(names.includes("ENTRY"));
    assert.ok(names.includes("BOOTSTRAP"));
    assert.ok(names.includes("REQUEST_START"));
    assert.ok(names.includes("REQUEST_SENT"));
  } finally {
    restore();
  }
});
