/**
 * P20 Mini Program Build Gate — pure evaluator.
 *
 * SSOT: docs/product/p20_product_north_star.md §K
 * Runs before Founder Form / Navigation / physical Preview QA.
 */

export const REQUIRED_APP_ID = "wxa610932351416622";
export const REQUIRED_API_PROFILE = "qa";
/** Isolated Cloud QA (fiqa-api-qa) — P36 T5. Never Production fiqa-api. */
export const REQUIRED_QA_API_BASE_URL =
  "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app";
export const REQUIRED_REQUEST_LEGAL_DOMAIN_HOST =
  "fiqa-api-qa-g7zatxrycq-uw.a.run.app";
/** Production host — Build Gate fails if QA package points here. */
export const FORBIDDEN_PRODUCTION_API_BASE_URL =
  "https://fiqa-api-g7zatxrycq-uw.a.run.app";
export const FORBIDDEN_PRODUCTION_REQUEST_LEGAL_DOMAIN_HOST =
  "fiqa-api-g7zatxrycq-uw.a.run.app";

/** Pages that must ship in every Preview / Experience package. */
export const REQUIRED_PREVIEW_PAGES = [
  "pages/start-claim/start-claim",
  "pages/service-home/service-home",
  "pages/entry/entry",
  "pages/receipt/receipt",
] as const;

/**
 * CLI-only paths that must never enter the WeChat Preview / Experience package.
 * Regression: scripts/build_gate.ts uses Node `import.meta` — if packaged,
 * DevTools fails with "Cannot use 'import.meta' outside a module" before Preview.
 */
export const REQUIRED_PACK_IGNORE_CLI_GLOBS = [
  "scripts/**",
  "tests/**",
] as const;

export const REQUIRED_REGISTERED_PAGES = [
  "pages/start-claim/start-claim",
  "pages/start-claim-success/start-claim-success",
  "pages/service-home/service-home",
  "pages/entry/entry",
  "pages/task-home/task-home",
  "pages/request-item/request-item",
  "pages/receipt/receipt",
] as const;

export type BuildGateFileMap = Record<string, string | null>;

export type BuildGateCompileCondition = {
  pathName?: string;
  query?: string;
  name?: string;
};

export type BuildGateSnapshot = {
  appJson: {
    pages?: string[];
    lazyCodeLoading?: string;
  };
  projectConfig: {
    appid?: string;
    condition?: unknown;
    setting?: {
      ignoreDevUnusedFiles?: boolean;
      ignoreUploadUnusedFiles?: boolean;
    };
    packOptions?: {
      ignore?: Array<string | { type?: string; value?: string }>;
    };
  };
  privateConfig?: {
    setting?: {
      ignoreDevUnusedFiles?: boolean;
      ignoreUploadUnusedFiles?: boolean;
    };
    condition?: {
      miniprogram?: { list?: BuildGateCompileCondition[] };
    };
  } | null;
  /** Relative paths under miniapp/ → present (non-null) or missing (null/absent). */
  files: BuildGateFileMap;
  /** Exact-case path existence; key is relative posix path. */
  exactCaseFiles?: Record<string, boolean>;
  apiProfile?: string;
  apiBaseUrl?: string;
  devTaskToken?: string;
};

export type BuildGateResult = {
  ok: boolean;
  errors: string[];
  requiredLegalDomainHost: string;
};

function pageFiles(page: string): string[] {
  return [".ts", ".json", ".wxml", ".wxss"].map((ext) => `${page}${ext}`);
}

function componentFiles(logicalPath: string): string[] {
  const base = logicalPath.replace(/^\//, "");
  return [".ts", ".json", ".wxml", ".wxss"].map((ext) => `${base}${ext}`);
}

function ignorePatterns(
  packOptions: BuildGateSnapshot["projectConfig"]["packOptions"],
): string[] {
  const raw = packOptions?.ignore || [];
  return raw.map((entry) => {
    if (typeof entry === "string") return entry;
    return String(entry?.value || "").trim();
  }).filter(Boolean);
}

function isIgnoredByPack(page: string, patterns: string[]): boolean {
  for (const pattern of patterns) {
    if (pattern === page) return true;
    if (pattern.endsWith("/**")) {
      const prefix = pattern.slice(0, -3);
      if (page === prefix || page.startsWith(`${prefix}/`)) return true;
    }
    if (pattern.includes("*")) {
      // Only support simple ** / trailing glob used in this repo.
      continue;
    }
    if (page.startsWith(pattern.replace(/\/$/, ""))) return true;
  }
  return false;
}

function filePresent(files: BuildGateFileMap, rel: string): boolean {
  return Object.prototype.hasOwnProperty.call(files, rel) && files[rel] != null;
}

function extractUsingComponents(files: BuildGateFileMap): Array<{
  from: string;
  alias: string;
  target: string;
}> {
  const out: Array<{ from: string; alias: string; target: string }> = [];
  for (const [rel, content] of Object.entries(files)) {
    if (!rel.endsWith(".json") || content == null) continue;
    if (!rel.startsWith("pages/") && !rel.startsWith("components/")) continue;
    try {
      const parsed = JSON.parse(content) as { usingComponents?: Record<string, string> };
      if (!parsed.usingComponents || typeof parsed.usingComponents !== "object") continue;
      for (const [alias, raw] of Object.entries(parsed.usingComponents)) {
        out.push({ from: rel, alias, target: String(raw || "").trim() });
      }
    } catch {
      out.push({ from: rel, alias: "", target: "" });
    }
  }
  return out;
}

/**
 * Evaluate the permanent Mini Program Build Gate against an in-memory snapshot.
 * Used by the CLI and by regression tests that inject failing fixtures.
 */
export function evaluateMiniProgramBuildGate(snapshot: BuildGateSnapshot): BuildGateResult {
  const errors: string[] = [];
  const pages = Array.isArray(snapshot.appJson.pages) ? snapshot.appJson.pages : [];
  const exact = snapshot.exactCaseFiles || {};

  if (!pages.length) {
    errors.push("app.json pages[] is empty");
  } else if (pages[0] !== "pages/start-claim/start-claim") {
    errors.push(
      `app.json pages[0] must be pages/start-claim/start-claim (got "${pages[0] || ""}")`,
    );
  }

  for (const required of REQUIRED_REGISTERED_PAGES) {
    if (!pages.includes(required)) {
      errors.push(`app.json missing required page: ${required}`);
    }
  }

  for (const page of pages) {
    if (typeof page !== "string" || !page.trim()) {
      errors.push(`app.json invalid page entry: ${String(page)}`);
      continue;
    }
    for (const rel of pageFiles(page)) {
      if (!filePresent(snapshot.files, rel)) {
        errors.push(`missing page file: ${rel}`);
      } else if (exact[rel] === false) {
        errors.push(`casing mismatch for page file: ${rel}`);
      }
    }
  }

  for (const page of REQUIRED_PREVIEW_PAGES) {
    if (!pages.includes(page)) {
      errors.push(`Preview package missing required page registration: ${page}`);
    }
    for (const rel of pageFiles(page)) {
      if (!filePresent(snapshot.files, rel)) {
        errors.push(`Preview package missing required page file: ${rel}`);
      }
    }
  }

  const packIgnore = ignorePatterns(snapshot.projectConfig.packOptions);
  for (const page of REQUIRED_PREVIEW_PAGES) {
    if (isIgnoredByPack(page, packIgnore) || isIgnoredByPack(`pages/${page.split("/")[1]}`, packIgnore)) {
      errors.push(`packOptions.ignore excludes required Preview page: ${page}`);
    }
    // Also catch ignoring whole pages/ tree
    if (packIgnore.some((p) => p === "pages/**" || p === "pages")) {
      errors.push("packOptions.ignore excludes pages/** — Preview package cannot contain Start Claim");
    }
  }

  // Permanent regression: Node CLI scripts must never be reachable from Preview.
  for (const required of REQUIRED_PACK_IGNORE_CLI_GLOBS) {
    const covered = packIgnore.some(
      (p) => p === required || p === required.replace(/\/\*\*$/, "") || p === required.replace(/\/\*\*$/, "/"),
    );
    if (!covered) {
      errors.push(
        `packOptions.ignore must exclude CLI-only path ${required} — WeChat Preview must not compile Node scripts (import.meta)`,
      );
    }
  }

  // Runtime pages/components must never import CLI scripts.
  for (const [rel, content] of Object.entries(snapshot.files)) {
    if (content == null) continue;
    if (!rel.startsWith("pages/") && !rel.startsWith("components/")) continue;
    if (!/\.(ts|js)$/.test(rel)) continue;
    if (
      /from\s+['"][^'"]*scripts\//.test(content)
      || /require\s*\(\s*['"][^'"]*scripts\//.test(content)
      || /import\s*\(\s*['"][^'"]*scripts\//.test(content)
    ) {
      errors.push(
        `runtime file ${rel} imports scripts/ — CLI-only code must not be reachable from Preview`,
      );
    }
    if (/import\.meta/.test(content)) {
      errors.push(
        `runtime file ${rel} uses import.meta — breaks WeChat Preview ("Cannot use 'import.meta' outside a module")`,
      );
    }
  }

  for (const ref of extractUsingComponents(snapshot.files)) {
    if (!ref.target) {
      errors.push(`invalid usingComponents in ${ref.from}`);
      continue;
    }
    if (ref.target.startsWith("plugin://") || ref.target.startsWith("wx://")) {
      continue;
    }
    for (const rel of componentFiles(ref.target)) {
      if (!filePresent(snapshot.files, rel)) {
        errors.push(
          `missing usingComponents target for ${ref.alias} in ${ref.from} -> ${rel}`,
        );
      } else if (exact[rel] === false) {
        errors.push(`casing mismatch in usingComponents: ${ref.from} -> ${ref.target}`);
      }
    }
  }

  // Component completeness for every components/*/index set that exists as a directory marker.
  const componentDirs = new Set<string>();
  for (const rel of Object.keys(snapshot.files)) {
    const m = /^components\/([^/]+)\//.exec(rel);
    if (m) componentDirs.add(m[1]);
  }
  for (const name of componentDirs) {
    for (const rel of componentFiles(`/components/${name}/index`)) {
      if (!filePresent(snapshot.files, rel)) {
        errors.push(`missing component file: ${rel}`);
      }
    }
  }

  if (snapshot.appJson.lazyCodeLoading === "requiredComponents") {
    errors.push(
      'lazyCodeLoading "requiredComponents" is blocked — physical Preview wx://not-found / blank Home risk',
    );
  } else if (
    snapshot.appJson.lazyCodeLoading != null
    && String(snapshot.appJson.lazyCodeLoading).trim() !== ""
  ) {
    errors.push(
      `lazyCodeLoading must be omitted (approved value); got "${snapshot.appJson.lazyCodeLoading}"`,
    );
  }

  const setting = snapshot.projectConfig.setting || {};
  if (setting.ignoreDevUnusedFiles !== false) {
    errors.push(
      "ignoreDevUnusedFiles must be false — Preview unused-file filter caused wx://not-found",
    );
  }
  if (setting.ignoreUploadUnusedFiles !== false) {
    errors.push(
      "ignoreUploadUnusedFiles must be false — Experience packages must match Preview",
    );
  }
  if (snapshot.privateConfig?.setting?.ignoreDevUnusedFiles === true) {
    errors.push(
      "project.private.config.json ignoreDevUnusedFiles=true overrides project config → wx://not-found risk",
    );
  }
  if (snapshot.privateConfig?.setting?.ignoreUploadUnusedFiles === true) {
    errors.push(
      "project.private.config.json ignoreUploadUnusedFiles=true can omit registered pages",
    );
  }

  const publicCondition = snapshot.projectConfig.condition;
  if (
    publicCondition != null
    && !(
      typeof publicCondition === "object"
      && !Array.isArray(publicCondition)
      && Object.keys(publicCondition as object).length === 0
    )
  ) {
    errors.push("project.config.json condition must be empty {} for a clean Preview launch");
  }

  const privateList = snapshot.privateConfig?.condition?.miniprogram?.list || [];
  if (privateList.length) {
    const first = privateList[0];
    if (first?.pathName && first.pathName !== "pages/start-claim/start-claim") {
      errors.push(
        `compile condition[0] must be pages/start-claim/start-claim (got "${first.pathName}")`,
      );
    }
    for (const entry of privateList) {
      const query = String(entry?.query || "");
      if (/(?:^|[?&])token=/.test(query)) {
        errors.push(
          `stale Preview token in compile condition "${entry?.name || entry?.pathName || ""}" — token must not be baked into launch query`,
        );
      }
    }
  }

  const appid = String(snapshot.projectConfig.appid || "").trim();
  if (!appid) {
    errors.push("project.config.json appid is required");
  } else if (appid === "touristappid") {
    errors.push("project.config.json appid must not be touristappid for physical Preview");
  } else if (appid !== REQUIRED_APP_ID) {
    errors.push(`project.config.json appid must be ${REQUIRED_APP_ID} (got "${appid}")`);
  }

  const apiProfile = String(snapshot.apiProfile || "").trim();
  if (apiProfile && apiProfile !== REQUIRED_API_PROFILE) {
    errors.push(`apiProfile must be "${REQUIRED_API_PROFILE}" for Preview (got "${apiProfile}")`);
  }

  const apiBaseUrl = String(snapshot.apiBaseUrl || "").trim();
  if (apiBaseUrl) {
    if (/127\.0\.0\.1|localhost|0\.0\.0\.0/i.test(apiBaseUrl)) {
      errors.push(`apiBaseUrl must not be loopback for Preview (got "${apiBaseUrl}")`);
    }
    if (apiBaseUrl === FORBIDDEN_PRODUCTION_API_BASE_URL) {
      errors.push(
        `apiBaseUrl must not point at Production ${FORBIDDEN_PRODUCTION_API_BASE_URL}; use Cloud QA ${REQUIRED_QA_API_BASE_URL}`,
      );
    } else if (apiBaseUrl !== REQUIRED_QA_API_BASE_URL) {
      errors.push(
        `apiBaseUrl must be QA HTTPS host ${REQUIRED_QA_API_BASE_URL} (got "${apiBaseUrl}")`,
      );
    }
    try {
      const host = new URL(apiBaseUrl).hostname;
      if (host === FORBIDDEN_PRODUCTION_REQUEST_LEGAL_DOMAIN_HOST) {
        errors.push(
          `request legal domain host must not be Production ${FORBIDDEN_PRODUCTION_REQUEST_LEGAL_DOMAIN_HOST}; use ${REQUIRED_REQUEST_LEGAL_DOMAIN_HOST}`,
        );
      } else if (host !== REQUIRED_REQUEST_LEGAL_DOMAIN_HOST) {
        errors.push(
          `request legal domain host must be ${REQUIRED_REQUEST_LEGAL_DOMAIN_HOST} (got "${host}")`,
        );
      }
    } catch {
      errors.push(`apiBaseUrl is not a valid URL: ${apiBaseUrl}`);
    }
  }

  if (String(snapshot.devTaskToken || "").trim()) {
    errors.push("devTaskToken must be empty — supply token via launch query only");
  }

  return {
    ok: errors.length === 0,
    errors,
    requiredLegalDomainHost: REQUIRED_REQUEST_LEGAL_DOMAIN_HOST,
  };
}
