import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  REQUIRED_APP_ID,
  REQUIRED_PREVIEW_PAGES,
  REQUIRED_QA_API_BASE_URL,
  REQUIRED_REQUEST_LEGAL_DOMAIN_HOST,
  evaluateMiniProgramBuildGate,
  type BuildGateSnapshot,
} from "../utils/miniProgramBuildGate";
import { loadBuildGateSnapshotFromDisk } from "../scripts/build_gate";

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

function baseSnapshot(): BuildGateSnapshot {
  // Start from the real disk snapshot so PASS path stays honest.
  return loadBuildGateSnapshotFromDisk();
}

function pageBundle(page: string, body = "{}"): Record<string, string> {
  return {
    [`${page}.ts`]: "Page({})",
    [`${page}.json`]: body,
    [`${page}.wxml`]: "<view/>",
    [`${page}.wxss`]: "",
  };
}

test("Build Gate PASSes on current miniapp package", () => {
  const result = evaluateMiniProgramBuildGate(baseSnapshot());
  assert.equal(result.ok, true, result.errors.join("\n"));
  assert.equal(result.requiredLegalDomainHost, REQUIRED_REQUEST_LEGAL_DOMAIN_HOST);
});

test("Build Gate FAILs when ignoreDevUnusedFiles=true", () => {
  const snap = baseSnapshot();
  snap.projectConfig = {
    ...snap.projectConfig,
    setting: {
      ...snap.projectConfig.setting,
      ignoreDevUnusedFiles: true,
      ignoreUploadUnusedFiles: false,
    },
  };
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /ignoreDevUnusedFiles/.test(e)));
});

test("Build Gate FAILs when a registered page file is missing", () => {
  const snap = baseSnapshot();
  delete snap.files["pages/start-claim/start-claim.wxml"];
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /missing page file: pages\/start-claim\/start-claim\.wxml/.test(e)));
});

test("Build Gate FAILs when usingComponents target is missing", () => {
  const snap = baseSnapshot();
  snap.files["pages/start-claim/start-claim.json"] = JSON.stringify({
    usingComponents: {
      "task-cta": "/components/task-cta/index",
      "missing-comp": "/components/does-not-exist/index",
    },
  });
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /does-not-exist/.test(e)));
});

test("Build Gate FAILs on usingComponents casing mismatch", () => {
  const snap = baseSnapshot();
  snap.files["pages/start-claim/start-claim.json"] = JSON.stringify({
    usingComponents: {
      "task-cta": "/components/Task-Cta/index",
    },
  });
  // Mark the wrong-case path as present in the map but exact-case false.
  for (const ext of [".ts", ".json", ".wxml", ".wxss"]) {
    snap.files[`components/Task-Cta/index${ext}`] = snap.files[`components/task-cta/index${ext}`] || "";
    snap.exactCaseFiles = {
      ...snap.exactCaseFiles,
      [`components/Task-Cta/index${ext}`]: false,
    };
  }
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /casing mismatch/i.test(e)));
});

test("Build Gate FAILs on stale compile-condition Preview token", () => {
  const snap = baseSnapshot();
  snap.privateConfig = {
    ...(snap.privateConfig || {}),
    condition: {
      miniprogram: {
        list: [
          {
            name: "stale entry",
            pathName: "pages/entry/entry",
            query: "token=h5t1.stale-preview-token",
          },
        ],
      },
    },
  };
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /stale Preview token|compile condition\[0\]/.test(e)));
});

test("Build Gate FAILs when first compile condition is not Start Claim", () => {
  const snap = baseSnapshot();
  snap.privateConfig = {
    ...(snap.privateConfig || {}),
    setting: {
      ignoreDevUnusedFiles: false,
      ignoreUploadUnusedFiles: false,
    },
    condition: {
      miniprogram: {
        list: [
          {
            name: "entry",
            pathName: "pages/entry/entry",
            query: "",
          },
        ],
      },
    },
  };
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /compile condition\[0\]/.test(e)));
});

test("Build Gate FAILs when lazyCodeLoading=requiredComponents", () => {
  const snap = baseSnapshot();
  snap.appJson = { ...snap.appJson, lazyCodeLoading: "requiredComponents" };
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /lazyCodeLoading/.test(e)));
});

test("Build Gate FAILs when Preview required page is dropped from app.json", () => {
  const snap = baseSnapshot();
  snap.appJson = {
    ...snap.appJson,
    pages: (snap.appJson.pages || []).filter((p) => p !== "pages/receipt/receipt"),
  };
  // Keep files so only registration failure is asserted.
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(
    result.errors.some(
      (e) => /missing required page: pages\/receipt\/receipt|Preview package missing required page registration/.test(e),
    ),
  );
});

test("Build Gate FAILs on touristappid / wrong AppID", () => {
  const snap = baseSnapshot();
  snap.projectConfig = { ...snap.projectConfig, appid: "touristappid" };
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /touristappid|appid/.test(e)));
});

test("Build Gate FAILs on wrong apiProfile / loopback / legal-domain host", () => {
  const snap = baseSnapshot();
  snap.apiProfile = "local";
  snap.apiBaseUrl = "http://127.0.0.1:8001";
  const result = evaluateMiniProgramBuildGate(snap);
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((e) => /apiProfile/.test(e)));
  assert.ok(result.errors.some((e) => /loopback|apiBaseUrl/.test(e)));
});

test("Build Gate permanent Preview contract constants are locked", () => {
  assert.equal(REQUIRED_APP_ID, "wxa610932351416622");
  assert.equal(REQUIRED_QA_API_BASE_URL, "https://fiqa-api-g7zatxrycq-uw.a.run.app");
  assert.equal(REQUIRED_REQUEST_LEGAL_DOMAIN_HOST, "fiqa-api-g7zatxrycq-uw.a.run.app");
  assert.deepEqual([...REQUIRED_PREVIEW_PAGES], [
    "pages/start-claim/start-claim",
    "pages/entry/entry",
    "pages/receipt/receipt",
  ]);
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8"));
  assert.equal(appJson.pages?.[0], "pages/start-claim/start-claim");
  assert.equal(appJson.lazyCodeLoading, undefined);
});
