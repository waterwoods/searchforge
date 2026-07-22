/**
 * Prove pages/entry/entry is a complete WeChat page quartet and registered in app.json.
 * Prevents "Page has not been registered yet" from missing files / wrong index layout.
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";

const ROOT = join(__dirname, "..");
const ENTRY_DIR = join(ROOT, "pages/entry");

test("app.json registers pages/entry/entry", () => {
  const appJson = JSON.parse(readFileSync(join(ROOT, "app.json"), "utf8")) as {
    pages?: string[];
  };
  assert.ok(appJson.pages?.includes("pages/entry/entry"));
});

test("entry uses page-name files (not pages/entry/entry/index.*)", () => {
  // WeChat path pages/entry/entry → entry.ts/json/wxml/wxss (not index.ts).
  assert.equal(existsSync(join(ENTRY_DIR, "index.ts")), false);
  assert.equal(existsSync(join(ENTRY_DIR, "index.js")), false);
  for (const file of ["entry.ts", "entry.json", "entry.wxml", "entry.wxss"]) {
    const full = join(ENTRY_DIR, file);
    assert.ok(existsSync(full), `missing ${file}`);
    assert.ok(statSync(full).size > 0, `${file} must be non-empty for packaging`);
  }
});

test("entry.ts calls Page( so the route can register", () => {
  const src = readFileSync(join(ENTRY_DIR, "entry.ts"), "utf8");
  assert.match(src, /\bPage\s*\(/);
  assert.match(src, /behaviors:\s*\[\s*taskPage\s*\]/);
});

test("entry.json usingComponents paths resolve", () => {
  const json = JSON.parse(readFileSync(join(ENTRY_DIR, "entry.json"), "utf8")) as {
    usingComponents?: Record<string, string>;
  };
  const shell = json.usingComponents?.["task-shell"];
  assert.equal(shell, "/components/task-shell/index");
  for (const file of ["index.ts", "index.json", "index.wxml", "index.wxss"]) {
    assert.ok(existsSync(join(ROOT, "components/task-shell", file)), file);
  }
});
