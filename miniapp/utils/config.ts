/**
 * Prototype config — uses committed defaults; optional local override via config.local.ts
 */
import { config as defaultConfig } from "../config.defaults";

type AppConfig = typeof defaultConfig;

let runtimeConfig: AppConfig = { ...defaultConfig };

try {
  // Optional gitignored local override (copy config.example.ts → config.local.ts)
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const local = require("../config.local") as { config?: Partial<AppConfig> };
  if (local?.config) {
    runtimeConfig = { ...defaultConfig, ...local.config };
  }
} catch {
  // no local override
}

export const appConfig = runtimeConfig;
