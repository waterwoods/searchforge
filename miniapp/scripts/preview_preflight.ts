/**
 * Founder Preview preflight — fails before DevTools Preview if phone would hit localhost.
 */
import { appConfig, isLoopbackApiBase, QA_API_BASE_URL } from "../utils/config";

const token = String(appConfig.devTaskToken || "").trim();
const errors: string[] = [];

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

if (errors.length) {
  console.error("Preview preflight FAILED:");
  for (const err of errors) console.error(` - ${err}`);
  process.exit(1);
}

console.log("Preview preflight PASSED:", {
  apiProfile: appConfig.apiProfile,
  apiBaseUrl: appConfig.apiBaseUrl,
  devTaskTokenConfigured: false,
});
