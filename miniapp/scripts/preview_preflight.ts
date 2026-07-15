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
  };
  if (!String(project.appid || "").trim()) {
    errors.push("project.config.json appid is required for Preview");
  }
} catch {
  errors.push("project.config.json is missing or unreadable");
}

try {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
  };
  const pages = appJson.pages || [];
  for (const required of [
    "pages/task-home/task-home",
    "pages/request-item/request-item",
    "pages/entry/entry",
  ]) {
    if (!pages.includes(required)) {
      errors.push(`app.json missing required page: ${required}`);
    }
  }
} catch {
  errors.push("app.json is missing or unreadable");
}

const requiredRouteHints = [
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
