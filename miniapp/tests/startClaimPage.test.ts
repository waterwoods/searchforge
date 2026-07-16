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
  const ctx: Record<string, any> = {
    route: "/pages/start-claim/start-claim",
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...page,
    ...overrides,
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

test("start-claim wxml uses Coming soon photo placeholder and no internal ids", () => {
  const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
  assert.match(wxml, /Coming soon/);
  assert.match(wxml, /提交/);
  assert.equal(wxml.includes("case_id"), false);
  assert.equal(wxml.includes("aggregate_version"), false);
  assert.equal(wxml.includes("command_id"), false);
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
  await page.submitStartClaim.call(retryCtx, { reuseIdentity: false });
  assert.equal(retryCtx.data.errorRetryable, true);
  const firstId = String(calls[1]?.command_id || "");
  await page.submitStartClaim.call(retryCtx, { reuseIdentity: true });
  assert.equal(calls[2]?.command_id, firstId);
  assert.equal(calls[2]?.idempotency_key, calls[1]?.idempotency_key);
});
