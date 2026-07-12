/**
 * Prototype config — uses committed defaults; optional local override via config.local.ts
 *
 * WeChat DevTools must statically import config.local.ts so the TS compiler includes it.
 * Dynamic require() is not bundled and devTaskToken silently stays empty.
 */
import { config as defaultConfig } from "../config.defaults";
import { config as localConfig } from "../config.local";

type AppConfig = typeof defaultConfig;

export const appConfig: AppConfig = {
  ...defaultConfig,
  ...localConfig,
};

/** Prototype-only diagnostics — colocated here to avoid a separate devLog module. */
export function devLog(...args: unknown[]): void {
  if (appConfig.prototypeMode) {
    console.info(...args);
  }
}

const devTaskToken = String(appConfig.devTaskToken || "").trim();
devLog("[prototype] appConfig loaded", {
  apiBaseUrl: appConfig.apiBaseUrl,
  devTaskTokenConfigured: devTaskToken.length > 0,
});
