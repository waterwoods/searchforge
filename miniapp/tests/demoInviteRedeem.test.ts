/**
 * T4 — Demo Invite Mini Program redeem helpers (pure + API shape).
 * Run: npm test -- prefix=demoInvite  (or node with tsx via package scripts)
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import {
  hasDemoInviteLaunchQuery,
  isIntentionalStartClaimEntry,
  buildDemoInviteStartClaimUrl,
  resolveWarmDemoInviteRelaunchUrl,
} from "../utils/demoInviteLaunch";
import { resolveDemoInviteTokenFromQuery } from "../services/demoInviteApi";
import { summarizeLaunchQuery } from "../utils/qaPathLog";
import { redirectStartClaimIfActiveCase } from "../utils/startClaimEntry";

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

test("dit query helpers", () => {
  assert.equal(resolveDemoInviteTokenFromQuery({ dit: "di_abc123xyz" }), "di_abc123xyz");
  assert.equal(resolveDemoInviteTokenFromQuery({ dit: "bad" }), "");
  assert.equal(resolveDemoInviteTokenFromQuery({}), "");
  assert.equal(hasDemoInviteLaunchQuery({ dit: "di_ok" }), true);
  assert.equal(hasDemoInviteLaunchQuery({ entry: "form" }), false);
  assert.equal(isIntentionalStartClaimEntry({ entry: "form" }), true);
  assert.equal(isIntentionalStartClaimEntry({ dit: "di_ok" }), true);
  assert.equal(isIntentionalStartClaimEntry({}), false);
});

test("warm Preview dit reLaunch URL is built for new tokens only", () => {
  const url = buildDemoInviteStartClaimUrl({
    entry: "form",
    dit: "di_EoVE2RMCcyf9ZwhS0pAgIh6nGKHtc8aqZiO9GQ2TqVE",
  });
  assert.match(url, /^\/pages\/start-claim\/start-claim\?entry=form&dit=di_/);

  const coldTracked = resolveWarmDemoInviteRelaunchUrl({
    enterQuery: { entry: "form", dit: "di_newtokenAAAAAAAA" },
    lastHandledDit: "di_newtokenAAAAAAAA",
  });
  assert.equal(coldTracked.shouldRelaunch, false);

  const warmNew = resolveWarmDemoInviteRelaunchUrl({
    enterQuery: { entry: "form", dit: "di_brandnewBBBBBBBB" },
    lastHandledDit: "di_oldtokenCCCCCCCC",
  });
  assert.equal(warmNew.shouldRelaunch, true);
  assert.match(warmNew.url, /dit=di_brandnewBBBBBBBB/);

  const noDit = resolveWarmDemoInviteRelaunchUrl({
    enterQuery: { entry: "form" },
    lastHandledDit: "",
  });
  assert.equal(noDit.shouldRelaunch, false);
});

test("app.ts forces warm Demo Invite reLaunch and does not treat enter path as current page", () => {
  const src = readFileSync(join(miniappRoot, "app.ts"), "utf8");
  assert.match(src, /resolveWarmDemoInviteRelaunchUrl/);
  assert.match(src, /demo_invite_warm_relaunch/);
  assert.match(src, /demo_invite_dit_tracked_cold/);
  // Must not skip warm reLaunch merely because enter path looks like start-claim.
  assert.doesNotMatch(src, /alreadyOnStartClaim/);
});

test("qaPathLog redacts dit", () => {
  const s = summarizeLaunchQuery({ dit: "di_supersecrettokenvalue", entry: "form" });
  assert.ok(s.queryKeys.includes("dit"));
  assert.ok(s.queryRawSafe.includes("dit=(redacted)"));
  assert.ok(!s.queryRawSafe.includes("supersecret"));
  assert.equal(s.hasToken, true);
});

test("dit launch does not divert to Service Home", () => {
  const launches: string[] = [];
  const wxLike = {
    reLaunch: (opts: { url: string }) => {
      launches.push(opts.url);
    },
  };
  const diverted = redirectStartClaimIfActiveCase(wxLike, { dit: "di_abc" });
  assert.equal(diverted, false);
  assert.equal(launches.length, 0);

  const divertedHome = redirectStartClaimIfActiveCase(wxLike, {});
  assert.equal(divertedHome, true);
  assert.ok(launches.some((u) => u.includes("service-home")));
});

test("start-claim page wires redeem before smart claim", () => {
  const src = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.ts"), "utf8");
  assert.match(src, /redeemDemoInviteIfPresent/);
  assert.match(src, /resolveDemoInviteTokenFromQuery/);
  assert.match(src, /active_case_blocks_scenario_switch/);
  assert.match(src, /_demoInviteActive/);
  assert.match(src, /demo_invite_redeem_failed_no_active_case_fallback/);
  assert.match(src, /演示入口已失效或已过期/);
  assert.doesNotMatch(src, /console\.(log|info|warn).*dit/);
  // Must not persist raw token to storage helpers.
  assert.doesNotMatch(src, /setStorage.*dit/);
});

test("entry payload includes entry=form and dit", () => {
  const ui = readFileSync(
    join(miniappRoot, "../ui/src/api/demoInvite.ts"),
    "utf8",
  );
  assert.match(ui, /entry=form&dit=/);
});
