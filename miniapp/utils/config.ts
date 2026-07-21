/**
 * Prototype config — uses committed defaults; optional local override via config.local.ts
 *
 * WeChat DevTools must statically import config.local.ts so the TS compiler includes it.
 * Dynamic require() is not bundled and devTaskToken silently stays empty.
 *
 * Profile selection (explicit):
 * - apiProfile "local" → localhost / LAN defaults (DevTools)
 * - apiProfile "qa" → config.qa.ts HTTPS Cloud QA host (Experience / phone Founder QA)
 * Local file wins for tokens and display names, but localhost apiBaseUrl cannot
 * silently override an explicit "qa" profile (prevents Experience→127.0.0.1 mistakes).
 * QA profile also refuses Production URL (no silent fallback to fiqa-api).
 */
import { config as defaultConfig } from "../config.defaults";
import { config as qaConfig } from "../config.qa";
import { config as localConfig } from "../config.local";

export type ApiProfile = "local" | "qa";
export type AppConfig = typeof defaultConfig & { apiProfile: ApiProfile };

/** Isolated Cloud QA host (fiqa-api-qa) — used when apiProfile is "qa". */
export const QA_API_BASE_URL = "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app";

/** Production paid-pilot host (fiqa-api) — must never be selected by QA profile. */
export const PRODUCTION_API_BASE_URL =
  "https://fiqa-api-g7zatxrycq-uw.a.run.app";

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

function normalizeApiBase(url: unknown): string {
  return String(url || "")
    .trim()
    .replace(/\/+$/, "");
}

function isProductionApiBase(url: unknown): boolean {
  return normalizeApiBase(url) === PRODUCTION_API_BASE_URL;
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

  // Explicit QA profile: refuse Production URL leftovers (no silent Production fallback).
  if (apiProfile === "qa" && isProductionApiBase(localLayer.apiBaseUrl)) {
    delete localLayer.apiBaseUrl;
  }

  const resolved: AppConfig = {
    ...defaults,
    ...profileLayer,
    ...localLayer,
    apiProfile,
  };

  if (apiProfile === "qa") {
    // Fail closed: QA must resolve to Cloud QA only.
    if (isProductionApiBase(resolved.apiBaseUrl) || isLoopbackApiBase(resolved.apiBaseUrl)) {
      resolved.apiBaseUrl = QA_API_BASE_URL;
    }
    if (normalizeApiBase(resolved.apiBaseUrl) !== QA_API_BASE_URL) {
      resolved.apiBaseUrl = QA_API_BASE_URL;
    }
  }

  return resolved;
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
