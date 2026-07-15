/**
 * QA / Experience profile freeze proofs.
 * Proves apiProfile "qa" resolves to committed HTTPS QA host — never localhost —
 * even when a leftover DevTools loopback apiBaseUrl remains in the local layer.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { config as defaultConfig } from "../config.defaults";
import { config as qaConfig } from "../config.qa";
import {
  QA_API_BASE_URL,
  isLoopbackApiBase,
  resolveAppConfig,
  type AppConfig,
} from "../utils/config";

const ROOT = join(__dirname, "..");

test("committed config.qa.ts uses exact HTTPS QA host and empty token", () => {
  assert.equal(qaConfig.apiBaseUrl, QA_API_BASE_URL);
  assert.equal(qaConfig.apiBaseUrl, "https://fiqa-api-g7zatxrycq-uw.a.run.app");
  assert.equal(String(qaConfig.devTaskToken || "").trim(), "");
  assert.ok(!isLoopbackApiBase(qaConfig.apiBaseUrl));
  assert.ok(qaConfig.apiBaseUrl.startsWith("https://"));
});

test("defaults stay local/loopback for DevTools without changing QA commit", () => {
  assert.equal((defaultConfig as AppConfig).apiProfile, "local");
  assert.ok(isLoopbackApiBase(defaultConfig.apiBaseUrl));
  assert.equal(String(defaultConfig.devTaskToken || "").trim(), "");
});

test("Experience qa package ignores leftover localhost apiBaseUrl", () => {
  const resolved = resolveAppConfig(defaultConfig as AppConfig, qaConfig, {
    apiProfile: "qa",
    apiBaseUrl: "http://127.0.0.1:8001",
    devTaskToken: "",
  });
  assert.equal(resolved.apiProfile, "qa");
  assert.equal(resolved.apiBaseUrl, QA_API_BASE_URL);
  assert.ok(!isLoopbackApiBase(resolved.apiBaseUrl));
  assert.ok(resolved.apiBaseUrl.startsWith("https://"));
  assert.equal(resolved.devTaskToken, "");
});

test("Experience qa package ignores localhost hostname leftover", () => {
  const resolved = resolveAppConfig(defaultConfig as AppConfig, qaConfig, {
    apiProfile: "qa",
    apiBaseUrl: "http://localhost:8001",
    devTaskToken: "",
  });
  assert.equal(resolved.apiBaseUrl, QA_API_BASE_URL);
});

test("local DevTools profile can still use localhost without touching QA file", () => {
  const resolved = resolveAppConfig(defaultConfig as AppConfig, qaConfig, {
    apiProfile: "local",
    apiBaseUrl: "http://127.0.0.1:8001",
    devTaskToken: "",
  });
  assert.equal(resolved.apiProfile, "local");
  assert.equal(resolved.apiBaseUrl, "http://127.0.0.1:8001");
});

test("qa profile does not embed a customer task token from committed layers", () => {
  const qaFile = readFileSync(join(ROOT, "config.qa.ts"), "utf8");
  const defaultsFile = readFileSync(join(ROOT, "config.defaults.ts"), "utf8");
  // Real tokens look like h5t1.<jwt>.<sig> — allow commentary that mentions h5t1...
  assert.doesNotMatch(qaFile, /h5t1\.[A-Za-z0-9_-]+\./);
  assert.doesNotMatch(defaultsFile, /h5t1\.[A-Za-z0-9_-]+\./);
  assert.match(qaFile, /devTaskToken:\s*""/);
  assert.match(defaultsFile, /devTaskToken:\s*""/);
});
