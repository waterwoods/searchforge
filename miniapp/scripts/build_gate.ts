/**
 * P20 Mini Program Build Gate — disk loader + CLI.
 * SSOT: docs/product/p20_product_north_star.md §K
 *
 * Run: npm run build:gate  (from miniapp/)
 */
import { execSync } from "node:child_process";
import {
  existsSync,
  readdirSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { appConfig } from "../utils/config";
import {
  evaluateMiniProgramBuildGate,
  type BuildGateFileMap,
  type BuildGateSnapshot,
} from "../utils/miniProgramBuildGate";

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");
const TOKEN_QUERY_RE = /(?:^|[?&])token=/;

/**
 * P25 — Fail-closed: clear Golden session tokens from gitignored private compile
 * conditions before Build Gate evaluation so tokens never package.
 */
export function clearGoldenSessionTokensFromPrivateConfig(): {
  ok: boolean;
  cleared: number;
  error?: string;
} {
  const privatePath = join(miniappRoot, "project.private.config.json");
  if (!existsSync(privatePath)) {
    return { ok: true, cleared: 0 };
  }
  try {
    const cfg = JSON.parse(readFileSync(privatePath, "utf8")) as {
      condition?: { miniprogram?: { list?: Array<Record<string, unknown>> } };
    };
    const list = cfg?.condition?.miniprogram?.list;
    if (!Array.isArray(list)) {
      return { ok: true, cleared: 0 };
    }
    let cleared = 0;
    for (const entry of list) {
      const query = String(entry?.query || "");
      if (TOKEN_QUERY_RE.test(query)) {
        entry.query = "";
        if (String(entry.pathName || "") === "pages/entry/entry") {
          entry.name = "pages/entry/entry (token via query only)";
        }
        cleared += 1;
      }
    }
    writeFileSync(privatePath, `${JSON.stringify(cfg, null, 2)}\n`, "utf8");
    // Verify
    const verify = JSON.parse(readFileSync(privatePath, "utf8")) as {
      condition?: { miniprogram?: { list?: Array<Record<string, unknown>> } };
    };
    for (const entry of verify?.condition?.miniprogram?.list || []) {
      if (TOKEN_QUERY_RE.test(String(entry?.query || ""))) {
        return { ok: false, cleared, error: "token_still_present_after_clear" };
      }
    }
    return { ok: true, cleared };
  } catch (err) {
    return { ok: false, cleared: 0, error: String(err) };
  }
}

function walkRelFiles(dir: string, prefix: string, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === "tests") continue;
    const full = join(dir, entry);
    const rel = prefix ? `${prefix}/${entry}` : entry;
    const st = statSync(full);
    if (st.isDirectory()) {
      walkRelFiles(full, rel, out);
      continue;
    }
    out.push(rel.replace(/\\/g, "/"));
  }
  return out;
}

function resolveWithExactCase(baseDir: string, absolutePath: string): boolean {
  const rel = relative(baseDir, absolutePath);
  const segments = rel.split(sep).filter(Boolean);
  let cursor = baseDir;
  for (const seg of segments) {
    if (!existsSync(cursor)) return false;
    if (!readdirSync(cursor).includes(seg)) return false;
    cursor = join(cursor, seg);
  }
  return true;
}

function loadJson(path: string): unknown {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function loadBuildGateSnapshotFromDisk(): BuildGateSnapshot {
  const appJson = loadJson(join(miniappRoot, "app.json")) as BuildGateSnapshot["appJson"];
  const projectConfig = loadJson(
    join(miniappRoot, "project.config.json"),
  ) as BuildGateSnapshot["projectConfig"];

  let privateConfig: BuildGateSnapshot["privateConfig"] = null;
  const privatePath = join(miniappRoot, "project.private.config.json");
  if (existsSync(privatePath)) {
    privateConfig = loadJson(privatePath) as BuildGateSnapshot["privateConfig"];
  }

  const files: BuildGateFileMap = {};
  const exactCaseFiles: Record<string, boolean> = {};
  for (const dir of ["pages", "components"]) {
    for (const rel of walkRelFiles(join(miniappRoot, dir), dir)) {
      const full = join(miniappRoot, rel);
      files[rel] = readFileSync(full, "utf8");
      exactCaseFiles[rel] = resolveWithExactCase(miniappRoot, full);
    }
  }

  return {
    appJson,
    projectConfig,
    privateConfig,
    files,
    exactCaseFiles,
    apiProfile: appConfig.apiProfile,
    apiBaseUrl: appConfig.apiBaseUrl,
    devTaskToken: String(appConfig.devTaskToken || ""),
  };
}

export function runMiniProgramBuildGate(): {
  ok: boolean;
  errors: string[];
  requiredLegalDomainHost: string;
} {
  const clearResult = clearGoldenSessionTokensFromPrivateConfig();
  if (!clearResult.ok) {
    return {
      ok: false,
      errors: [
        `Golden session token cleanup failed (fail-closed): ${clearResult.error || "unknown"}`,
      ],
      requiredLegalDomainHost: "",
    };
  }

  const snapshot = loadBuildGateSnapshotFromDisk();
  const result = evaluateMiniProgramBuildGate(snapshot);

  // Preview preflight is part of the Build Gate contract.
  try {
    execSync("node scripts/preview_preflight.mjs", {
      cwd: miniappRoot,
      stdio: "pipe",
      encoding: "utf8",
    });
  } catch (err) {
    const stderr = String((err as { stderr?: string }).stderr || err || "");
    result.errors.push(`Preview preflight failed${stderr ? `: ${stderr.trim()}` : ""}`);
    return { ok: false, errors: result.errors, requiredLegalDomainHost: result.requiredLegalDomainHost };
  }

  return result;
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
// tsx may rewrite argv; also run when executed directly.
const invokedDirectly =
  Boolean(process.argv[1])
  && (process.argv[1].endsWith("build_gate.ts") || process.argv[1].endsWith("build_gate.js"));

if (invokedDirectly || isMain) {
  const result = runMiniProgramBuildGate();
  if (!result.ok) {
    console.error("Mini Program Build Gate FAILED:");
    for (const err of result.errors) console.error(` - ${err}`);
    process.exit(1);
  }
  console.log("Mini Program Build Gate PASSED:", {
    appId: REQUIRED_DISPLAY(),
    apiProfile: appConfig.apiProfile,
    apiBaseUrl: appConfig.apiBaseUrl,
    requiredLegalDomainHost: result.requiredLegalDomainHost,
    note: "WeChat admin must whitelist requiredLegalDomainHost before physical Preview.",
  });
}

function REQUIRED_DISPLAY() {
  try {
    return (loadJson(join(miniappRoot, "project.config.json")) as { appid?: string }).appid;
  } catch {
    return "";
  }
}
