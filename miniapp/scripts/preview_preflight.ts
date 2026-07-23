/**
 * Founder Preview preflight — fails before DevTools Preview if phone would hit localhost.
 * Slice 1 readiness: confirms required customer routes and AppID/profile expectations.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { appConfig, isLoopbackApiBase, QA_API_BASE_URL } from "../utils/config";

const token = String(appConfig.devTaskToken || "").trim();
const errors: string[] = [];
const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

if (appConfig.apiProfile !== "qa") {
  errors.push(`apiProfile must be "qa" for phone Preview (got "${appConfig.apiProfile}")`);
}
if (isLoopbackApiBase(appConfig.apiBaseUrl)) {
  errors.push(`apiBaseUrl must not be loopback for phone Preview (got "${appConfig.apiBaseUrl}")`);
}
if (appConfig.apiBaseUrl !== QA_API_BASE_URL) {
  errors.push(`apiBaseUrl must be QA HTTPS host (got "${appConfig.apiBaseUrl}")`);
}
if (token.length > 0) {
  errors.push("devTaskToken must be empty — supply token via launch query only");
}

try {
  const project = JSON.parse(readFileSync(join(miniappRoot, "project.config.json"), "utf8")) as {
    appid?: string;
    setting?: { ignoreDevUnusedFiles?: boolean; ignoreUploadUnusedFiles?: boolean };
  };
  if (!String(project.appid || "").trim()) {
    errors.push("project.config.json appid is required for Preview");
  }
  // Unused-file filtering can drop page/deps from the Preview package → wx://not-found.
  if (project.setting?.ignoreDevUnusedFiles === true) {
    errors.push(
      'project.config.json ignoreDevUnusedFiles=true is blocked — Preview can package without Home page → wx://not-found',
    );
  }
  if (project.setting?.ignoreUploadUnusedFiles === true) {
    errors.push(
      "project.config.json ignoreUploadUnusedFiles=true is blocked — Experience upload can omit registered pages",
    );
  }
} catch {
  errors.push("project.config.json is missing or unreadable");
}

try {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
    lazyCodeLoading?: string;
  };
  const pages = appJson.pages || [];
  if (pages[0] !== "pages/start-claim/start-claim") {
    errors.push(
      `app.json pages[0] must be Start Claim Home target (got "${pages[0] || ""}")`,
    );
  }
  for (const required of [
    "pages/start-claim/start-claim",
    "pages/start-claim-success/start-claim-success",
    "pages/service-home/service-home",
    "pages/task-home/task-home",
    "pages/case-status/case-status",
    "pages/request-item/request-item",
    "pages/entry/entry",
  ]) {
    if (!pages.includes(required)) {
      errors.push(`app.json missing required page: ${required}`);
    }
  }
  if (appJson.lazyCodeLoading === "requiredComponents") {
    errors.push(
      'lazyCodeLoading "requiredComponents" is blocked for Preview — Home→Start Claim blank-screen risk on physical device',
    );
  }
} catch {
  errors.push("app.json is missing or unreadable");
}

try {
  const privateConfigPath = join(miniappRoot, "project.private.config.json");
  const privateRaw = readFileSync(privateConfigPath, "utf8");
  const privateConfig = JSON.parse(privateRaw) as {
    setting?: { ignoreDevUnusedFiles?: boolean; ignoreUploadUnusedFiles?: boolean };
    condition?: { miniprogram?: { list?: Array<{ pathName?: string; query?: string; name?: string }> } };
  };
  if (privateConfig.setting?.ignoreDevUnusedFiles === true) {
    errors.push(
      "project.private.config.json ignoreDevUnusedFiles=true overrides project config and can cause physical Preview wx://not-found",
    );
  }
  if (privateConfig.setting?.ignoreUploadUnusedFiles === true) {
    errors.push(
      "project.private.config.json ignoreUploadUnusedFiles=true can omit registered pages from Experience packages",
    );
  }
  const list = privateConfig.condition?.miniprogram?.list || [];
  const first = list[0];
  if (first?.pathName === "pages/entry/entry" && String(first.query || "").includes("token=")) {
    errors.push(
      "project.private.config.json default compile condition launches entry with a token — Preview will open stale Receipt instead of Start Claim",
    );
  }
} catch {
  // private config is gitignored; absence is OK
}

const requiredRouteHints = [
  "/api/h5/customer/start-claim",
  "/api/h5/tasks/{token}/intake",
  "/api/h5/tasks/{token}/request-items/{item_id}/submit",
  "/api/h5/tasks/{uploadToken}/upload",
];

if (errors.length) {
  console.error("Preview preflight FAILED:");
  for (const err of errors) console.error(` - ${err}`);
  process.exit(1);
}

console.log("Preview preflight PASSED:", {
  apiProfile: appConfig.apiProfile,
  apiBaseUrl: appConfig.apiBaseUrl,
  devTaskTokenConfigured: false,
  slice1PagesRegistered: true,
  expectedBackendRoutes: requiredRouteHints,
  note: "Slice 1 capability requires P20_SLICE1_REQUEST_MORE / case capability on backend; this preflight checks client Preview config only.",
});
