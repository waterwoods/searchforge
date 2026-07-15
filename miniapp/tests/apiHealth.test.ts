import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { resetApiHealthCache, ensureApiReachable } from "../utils/apiHealth";

const ROOT = join(__dirname, "..");

test("apiHealth probes /health/live not /healthz", () => {
  const source = readFileSync(join(ROOT, "utils/apiHealth.ts"), "utf8");
  assert.match(source, /\/health\/live/);
  assert.doesNotMatch(source, /\/healthz/);
});

test("ensureApiReachable calls wx.request with /health/live URL", async () => {
  resetApiHealthCache();
  let capturedUrl = "";
  (globalThis as Record<string, unknown>).wx = {
    request(opts: { url?: string; success?: (res: { statusCode: number }) => void }) {
      capturedUrl = String(opts.url || "");
      opts.success?.({ statusCode: 200 });
    },
  };

  await ensureApiReachable();
  assert.ok(capturedUrl.endsWith("/health/live"));
  assert.ok(!capturedUrl.includes("/healthz"));
});
