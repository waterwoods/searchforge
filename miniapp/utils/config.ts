/**
 * Prototype config — uses committed defaults; optional local override via config.local.ts
 *
 * WeChat DevTools must statically import config.local.ts so the TS compiler includes it.
 * Dynamic require() is not bundled and devTaskToken silently stays empty.
 *
 * Profile selection (explicit):
 * - apiProfile "local" → localhost / LAN defaults (DevTools)
 * - apiProfile "qa" → config.qa.ts HTTPS QA host (Experience / phone)
 * Local file wins for tokens and display names, but localhost apiBaseUrl cannot
 * silently override an explicit "qa" profile (prevents Experience→127.0.0.1 mistakes).
 */
import { config as defaultConfig } from "../config.defaults";
import { config as qaConfig } from "../config.qa";
import { config as localConfig } from "../config.local";

export type ApiProfile = "local" | "qa";
export type AppConfig = typeof defaultConfig & { apiProfile: ApiProfile };

/** Committed QA host — used by Experience package when apiProfile is "qa". */
export const QA_API_BASE_URL = "https://fiqa-api-g7zatxrycq-uw.a.run.app";

export function resolveProfile(raw: unknown): ApiProfile {
  return String(raw || "local").trim().toLowerCase() === "qa" ? "qa" : "local";
}

export function isLoopbackApiBase(url: unknown): boolean {
  const value = String(url || "")
    .trim()
    .toLowerCase();
  return (
    value.includes("127.0.0.1") ||
    value.includes("localhost") ||
    value.startsWith("http://0.0.0.0")
  );
}

/**
 * Pure merge used by runtime and unit tests.
 * Experience upload must pass apiProfile "qa" (via gitignored config.local.ts).
 */
export function resolveAppConfig(
  defaults: AppConfig,
  qa: Partial<AppConfig> | typeof qaConfig,
  local: Partial<AppConfig>,
): AppConfig {
  const localLayer = { ...local } as Partial<AppConfig>;
  const apiProfile = resolveProfile(
    localLayer.apiProfile ?? defaults.apiProfile,
  );
  const profileLayer = apiProfile === "qa" ? qa : {};

  // Explicit QA profile: ignore leftover localhost apiBaseUrl from a DevTools local file.
  if (apiProfile === "qa" && isLoopbackApiBase(localLayer.apiBaseUrl)) {
    delete localLayer.apiBaseUrl;
  }

  return {
    ...defaults,
    ...profileLayer,
    ...localLayer,
    apiProfile,
  };
}

export const appConfig: AppConfig = resolveAppConfig(
  defaultConfig as AppConfig,
  qaConfig,
  localConfig as Partial<AppConfig>,
);

/** Prototype-only diagnostics — colocated here to avoid a separate devLog module. */
export function devLog(...args: unknown[]): void {
  if (appConfig.prototypeMode) {
    console.info(...args);
  }
}

const devTaskToken = String(appConfig.devTaskToken || "").trim();
devLog("[prototype] appConfig loaded", {
  apiProfile: appConfig.apiProfile,
  apiBaseUrl: appConfig.apiBaseUrl,
  devTaskTokenConfigured: devTaskToken.length > 0,
});
