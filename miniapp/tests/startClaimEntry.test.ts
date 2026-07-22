import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { installMiniProgramGlobals } from "./miniprogramMocks";
import {
  ENTRY_ROUTE,
  SERVICE_HOME_ROUTE,
  START_CLAIM_ROUTE,
  assertStartClaimWxmlNotBlankable,
  createEmptyStartClaimShell,
  hasActiveCustomerCase,
  redirectStartClaimIfActiveCase,
  reLaunchCustomerHome,
  reLaunchEmptyStartClaimForm,
  reLaunchStartClaimHome,
  resetStartClaimDraftState,
  resolveCustomerHomeUrl,
  resolveHomeStartClaimUrl,
} from "../utils/startClaimEntry";
import {
  CONTINUE_CLAIM_TITLE,
  START_NEW_CLAIM_LABEL,
  buildServiceHomeViewModel,
} from "../utils/serviceHome";
import { loadResumeToken, saveResumeToken, saveSubmitIntentId, loadSubmitIntentId, clearResumeToken } from "../utils/storage";

installMiniProgramGlobals();

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

test("no active case → Home target is Service Home", () => {
  clearResumeToken();
  assert.equal(hasActiveCustomerCase(), false);
  assert.equal(resolveHomeStartClaimUrl(), `${START_CLAIM_ROUTE}?entry=form`);
  assert.equal(resolveCustomerHomeUrl(), SERVICE_HOME_ROUTE);
  assert.equal(SERVICE_HOME_ROUTE, "/pages/service-home/service-home");
});

test("active case/token → Home target is still Service Home (not Task Home)", () => {
  saveResumeToken("h5t1.active-camry");
  assert.equal(hasActiveCustomerCase(), true);
  assert.equal(resolveCustomerHomeUrl(), SERVICE_HOME_ROUTE);
  assert.notEqual(resolveCustomerHomeUrl(), ENTRY_ROUTE);
  clearResumeToken();
});

test("Service Home active VM exposes Continue + demoted Start New", () => {
  const vm = buildServiceHomeViewModel(true);
  assert.equal(vm.hasActiveSession, true);
  assert.equal(vm.continueTitle, CONTINUE_CLAIM_TITLE);
  assert.equal(vm.startNewClaimLabel, START_NEW_CLAIM_LABEL);
  assert.match(vm.continueTitle, /继续处理当前报案/);
  assert.match(vm.startNewClaimLabel, /开始新的报案/);
});

test("Service Home empty VM exposes Start Claim primary", () => {
  const vm = buildServiceHomeViewModel(false);
  assert.equal(vm.hasActiveSession, false);
  assert.match(vm.startClaimTitle, /开始报案/);
});

test("empty shell is pageReady with visible missing hint and no network dependency", () => {
  const shell = createEmptyStartClaimShell("请先填写：事故经过、事故时间、事故地点、是否受伤");
  assert.equal(shell.pageReady, true);
  assert.equal(shell.initErrorMessage, "");
  assert.equal(shell.canSubmit, false);
  assert.match(shell.missingHint, /事故经过/);
  assert.equal(shell.description, "");
});

test("Start New Claim resets only claim-draft resume markers", () => {
  saveResumeToken("h5t1.stale-submitted");
  saveSubmitIntentId("intent-old");
  (globalThis as Record<string, any>).wx.setStorageSync("mp_prototype_anon_session", "anon-keep");
  resetStartClaimDraftState();
  assert.equal(loadResumeToken(), "");
  assert.equal(loadSubmitIntentId(), "");
  assert.equal(
    String((globalThis as Record<string, any>).wx.getStorageSync("mp_prototype_anon_session") || ""),
    "anon-keep",
  );
});

test("reLaunchCustomerHome preserves active token and opens Service Home", () => {
  saveResumeToken("h5t1.active");
  const launches: string[] = [];
  reLaunchCustomerHome({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.deepEqual(launches, [SERVICE_HOME_ROUTE]);
  assert.equal(loadResumeToken(), "h5t1.active");
  clearResumeToken();
});

test("reLaunchStartClaimHome with active token goes Service Home and keeps resume", () => {
  saveResumeToken("h5t1.golden");
  const launches: string[] = [];
  reLaunchStartClaimHome({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.deepEqual(launches, [SERVICE_HOME_ROUTE]);
  assert.equal(loadResumeToken(), "h5t1.golden");
  clearResumeToken();
});

test("reLaunchEmptyStartClaimForm clears draft and opens form entry", () => {
  clearResumeToken();
  const launches: string[] = [];
  reLaunchEmptyStartClaimForm({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.deepEqual(launches, [`${START_CLAIM_ROUTE}?entry=form`]);
  assert.equal(loadResumeToken(), "");
});

test("capsule Home with active token → Service Home, resume survives", () => {
  saveResumeToken("h5t1.capsule-home");
  const launches: string[] = [];
  const redirected = redirectStartClaimIfActiveCase({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.equal(redirected, true);
  assert.deepEqual(launches, [SERVICE_HOME_ROUTE]);
  assert.equal(loadResumeToken(), "h5t1.capsule-home");
  clearResumeToken();
});

test("cold Start Claim without entry=form → Service Home", () => {
  clearResumeToken();
  const launches: string[] = [];
  const redirected = redirectStartClaimIfActiveCase({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.equal(redirected, true);
  assert.deepEqual(launches, [SERVICE_HOME_ROUTE]);
});

test("intentional entry=form without token stays on Start Claim", () => {
  clearResumeToken();
  const launches: string[] = [];
  const redirected = redirectStartClaimIfActiveCase(
    {
      reLaunch: ({ url }) => {
        launches.push(url);
      },
    },
    { entry: "form" },
  );
  assert.equal(redirected, false);
  assert.deepEqual(launches, []);
});

test("entry=form with active token still redirects to Service Home (P30)", () => {
  saveResumeToken("h5t1.block-second");
  const launches: string[] = [];
  const redirected = redirectStartClaimIfActiveCase(
    {
      reLaunch: ({ url }) => {
        launches.push(url);
      },
    },
    { entry: "form" },
  );
  assert.equal(redirected, true);
  assert.deepEqual(launches, [SERVICE_HOME_ROUTE]);
  assert.equal(loadResumeToken(), "h5t1.block-second");
  clearResumeToken();
});

test("start-claim wxml has no blankable full-page guard", () => {
  const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
  const failures = assertStartClaimWxmlNotBlankable(wxml);
  assert.deepEqual(failures, []);
  assert.match(wxml, /告诉陈总发生了什么/);
  assert.match(wxml, /事故经过/);
  assert.match(wxml, /事故时间/);
  assert.match(wxml, /事故地点/);
  assert.match(wxml, /是否有人受伤/);
  assert.match(wxml, /initErrorMessage/);
  assert.match(wxml, /重新加载表单/);
  // Required fields must not sit solely behind pageReady/ready.
  assert.equal(/wx:if="\{\{pageReady\}\}"/.test(wxml), false);
});

test("app.json Home page is start-claim; Service Home is registered", () => {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
    lazyCodeLoading?: string;
  };
  assert.equal(appJson.pages?.[0], "pages/start-claim/start-claim");
  assert.ok(appJson.pages?.includes("pages/service-home/service-home"));
  assert.equal(appJson.lazyCodeLoading, undefined);
});

test("Preview package must not filter unused files (wx://not-found regression)", () => {
  const project = JSON.parse(
    readFileSync(join(miniappRoot, "project.config.json"), "utf8"),
  ) as {
    setting?: { ignoreDevUnusedFiles?: boolean; ignoreUploadUnusedFiles?: boolean };
  };
  assert.equal(project.setting?.ignoreDevUnusedFiles, false);
  assert.equal(project.setting?.ignoreUploadUnusedFiles, false);

  // Private overrides public; if present it must not re-enable the filter.
  try {
    const privateConfig = JSON.parse(
      readFileSync(join(miniappRoot, "project.private.config.json"), "utf8"),
    ) as {
      setting?: { ignoreDevUnusedFiles?: boolean; ignoreUploadUnusedFiles?: boolean };
    };
    assert.notEqual(privateConfig.setting?.ignoreDevUnusedFiles, true);
    assert.notEqual(privateConfig.setting?.ignoreUploadUnusedFiles, true);
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code !== "ENOENT") throw err;
  }
});

test("receipt Start New Claim preserves active path; start-claim redirects Home", () => {
  const receiptTs = readFileSync(join(miniappRoot, "pages/receipt/receipt.ts"), "utf8");
  const successTs = readFileSync(
    join(miniappRoot, "pages/start-claim-success/start-claim-success.ts"),
    "utf8",
  );
  const startClaimTs = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.ts"), "utf8");
  const serviceHomeTs = readFileSync(
    join(miniappRoot, "pages/service-home/service-home.ts"),
    "utf8",
  );
  const receiptWxml = readFileSync(join(miniappRoot, "pages/receipt/receipt.wxml"), "utf8");
  const successWxml = readFileSync(
    join(miniappRoot, "pages/start-claim-success/start-claim-success.wxml"),
    "utf8",
  );
  const serviceHomeWxml = readFileSync(
    join(miniappRoot, "pages/service-home/service-home.wxml"),
    "utf8",
  );
  assert.match(receiptTs, /reLaunchStartClaimHome/);
  assert.match(receiptTs, /onBackHome/);
  assert.match(successTs, /reLaunchStartClaimHome/);
  assert.match(successTs, /onBackHome/);
  assert.match(startClaimTs, /redirectStartClaimIfActiveCase/);
  assert.match(serviceHomeTs, /onContinueCurrentClaim/);
  assert.match(serviceHomeTs, /ONE_ACTIVE_CASE_POLICY/);
  assert.match(serviceHomeTs, /ENTRY_ROUTE/);
  assert.match(receiptWxml, /开始新报案/);
  assert.match(successWxml, /开始新报案/);
  assert.match(serviceHomeWxml, /\{\{continueTitle\}\}/);
  assert.match(serviceHomeWxml, /\{\{startNewClaimLabel\}\}/);
  assert.match(serviceHomeWxml, /\{\{viewProgressLabel\}\}/);
  assert.match(serviceHomeWxml, /\{\{contactLabel\}\}/);
  assert.match(serviceHomeTs, /buildServiceHomeViewModel/);
  assert.match(serviceHomeTs, /onContinueCurrentClaim/);
  const serviceHomeUtil = readFileSync(join(miniappRoot, "utils/serviceHome.ts"), "utf8");
  assert.match(serviceHomeUtil, /继续处理当前报案/);
  assert.match(serviceHomeUtil, /开始新的报案/);
  assert.match(serviceHomeUtil, /查看案件进度/);
  assert.match(serviceHomeUtil, /联系保险顾问/);
});
