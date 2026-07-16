import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { installMiniProgramGlobals } from "./miniprogramMocks";
import {
  START_CLAIM_ROUTE,
  assertStartClaimWxmlNotBlankable,
  createEmptyStartClaimShell,
  reLaunchStartClaimHome,
  resetStartClaimDraftState,
  resolveHomeStartClaimUrl,
} from "../utils/startClaimEntry";
import { loadResumeToken, saveResumeToken, saveSubmitIntentId, loadSubmitIntentId } from "../utils/storage";

installMiniProgramGlobals();

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

test("Home target is Start Claim route", () => {
  assert.equal(resolveHomeStartClaimUrl(), START_CLAIM_ROUTE);
  assert.equal(START_CLAIM_ROUTE, "/pages/start-claim/start-claim");
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

test("reLaunchStartClaimHome clears draft and relaunches Start Claim", () => {
  saveResumeToken("h5t1.stale");
  const launches: string[] = [];
  reLaunchStartClaimHome({
    reLaunch: ({ url }) => {
      launches.push(url);
    },
  });
  assert.deepEqual(launches, [START_CLAIM_ROUTE]);
  assert.equal(loadResumeToken(), "");
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

test("app.json Home page is start-claim and lazyCodeLoading is off", () => {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
    lazyCodeLoading?: string;
  };
  assert.equal(appJson.pages?.[0], "pages/start-claim/start-claim");
  assert.equal(appJson.lazyCodeLoading, undefined);
});

test("receipt and success pages wire Home to Start Claim helper", () => {
  const receiptTs = readFileSync(join(miniappRoot, "pages/receipt/receipt.ts"), "utf8");
  const successTs = readFileSync(
    join(miniappRoot, "pages/start-claim-success/start-claim-success.ts"),
    "utf8",
  );
  const receiptWxml = readFileSync(join(miniappRoot, "pages/receipt/receipt.wxml"), "utf8");
  const successWxml = readFileSync(
    join(miniappRoot, "pages/start-claim-success/start-claim-success.wxml"),
    "utf8",
  );
  assert.match(receiptTs, /reLaunchStartClaimHome/);
  assert.match(receiptTs, /onBackHome/);
  assert.match(successTs, /reLaunchStartClaimHome/);
  assert.match(successTs, /onBackHome/);
  assert.match(receiptWxml, /开始新报案/);
  assert.match(successWxml, /开始新报案/);
});
