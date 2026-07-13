#!/usr/bin/env node
import { execSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

function resolveRepoRoot() {
  const cwd = process.cwd();
  if (existsSync(path.join(cwd, "miniapp")) && existsSync(path.join(cwd, ".git"))) {
    return cwd;
  }
  const parent = path.dirname(cwd);
  if (existsSync(path.join(parent, "miniapp")) && existsSync(path.join(parent, ".git"))) {
    return parent;
  }
  return cwd;
}

const repoRoot = resolveRepoRoot();
const miniappRoot = path.join(repoRoot, "miniapp");
const componentsRoot = path.join(miniappRoot, "components");
const strictGit = process.argv.includes("--strict-git");

const errors = [];
const warnings = [];

function walkJsonFiles(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      walkJsonFiles(full, out);
      continue;
    }
    if (entry.endsWith(".json")) out.push(full);
  }
  return out;
}

function parseJson(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (err) {
    errors.push(`Invalid JSON: ${path.relative(repoRoot, filePath)} (${String(err)})`);
    return null;
  }
}

function checkGate1ComponentCompleteness() {
  const componentDirs = readdirSync(componentsRoot)
    .map((entry) => path.join(componentsRoot, entry))
    .filter((entry) => statSync(entry).isDirectory());

  for (const dir of componentDirs) {
    const rel = path.relative(repoRoot, dir);
    for (const required of ["index.ts", "index.json", "index.wxml", "index.wxss"]) {
      const full = path.join(dir, required);
      if (!existsSync(full)) {
        errors.push(`Gate1 missing file: ${path.join(rel, required)}`);
      }
    }

    const indexJsonPath = path.join(dir, "index.json");
    if (!existsSync(indexJsonPath)) continue;
    const parsed = parseJson(indexJsonPath);
    if (!parsed) continue;
    if (parsed.component !== true) {
      errors.push(`Gate1 missing "component": true in ${path.relative(repoRoot, indexJsonPath)}`);
    }
  }
}

function resolveWithExactCase(baseDir, absolutePath) {
  const relative = path.relative(baseDir, absolutePath);
  const segments = relative.split(path.sep).filter(Boolean);
  let cursor = baseDir;
  for (const seg of segments) {
    if (!existsSync(cursor)) return false;
    const entries = readdirSync(cursor);
    if (!entries.includes(seg)) return false;
    cursor = path.join(cursor, seg);
  }
  return true;
}

function checkGate2UsingComponentsPaths() {
  const jsonFiles = walkJsonFiles(path.join(miniappRoot, "pages")).concat(
    walkJsonFiles(path.join(miniappRoot, "components")),
    [path.join(miniappRoot, "app.json")].filter((p) => existsSync(p)),
  );
  const seenTargets = new Set();

  for (const jsonFile of jsonFiles) {
    const parsed = parseJson(jsonFile);
    if (!parsed || !parsed.usingComponents || typeof parsed.usingComponents !== "object") continue;

    for (const [alias, raw] of Object.entries(parsed.usingComponents)) {
      if (typeof raw !== "string" || !raw.trim()) {
        errors.push(`Gate2 invalid path for ${alias} in ${path.relative(repoRoot, jsonFile)}`);
        continue;
      }
      const logicalPath = raw.trim().replace(/^\//, "");
      const targetWithoutExt = path.join(miniappRoot, logicalPath);
      seenTargets.add(targetWithoutExt);

      const expectedFiles = [".json", ".ts", ".wxml", ".wxss"].map((ext) => `${targetWithoutExt}${ext}`);
      for (const expected of expectedFiles) {
        if (!existsSync(expected)) {
          errors.push(
            `Gate2 missing target file for ${alias} in ${path.relative(repoRoot, jsonFile)} -> ${path.relative(repoRoot, expected)}`,
          );
          continue;
        }
        if (!resolveWithExactCase(miniappRoot, expected)) {
          errors.push(
            `Gate2 casing mismatch in usingComponents: ${path.relative(repoRoot, jsonFile)} -> ${raw}`,
          );
        }
      }
    }
  }

  let gitOutput = "";
  try {
    gitOutput = execSync("git status --porcelain -- miniapp/components", {
      cwd: repoRoot,
      encoding: "utf8",
    });
  } catch {
    warnings.push("Gate2 git status check unavailable.");
  }

  const untracked = gitOutput
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("?? "));

  if (untracked.length) {
    const msg = `Gate2 untracked component files detected:\n${untracked.join("\n")}`;
    if (strictGit) {
      errors.push(msg);
    } else {
      warnings.push(msg);
    }
  }

  if (!seenTargets.size) {
    warnings.push("Gate2 found no usingComponents references.");
  }
}

checkGate1ComponentCompleteness();
checkGate2UsingComponentsPaths();

if (warnings.length) {
  console.log("Component gate warnings:");
  for (const warning of warnings) {
    console.log(`- ${warning}`);
  }
}

if (errors.length) {
  console.error("Component gate validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("Component gate validation passed.");
