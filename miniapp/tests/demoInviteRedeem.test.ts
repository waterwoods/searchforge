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
