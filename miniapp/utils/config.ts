/**
 * Prototype config loader — falls back to example values when config.ts is absent.
 */
let runtimeConfig: {
  apiBaseUrl: string;
  devTaskToken: string;
  tenantDisplayName: string;
  brokerDisplayName: string;
  prototypeMode: boolean;
};

try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  runtimeConfig = require("../config").config;
} catch {
  runtimeConfig = {
    apiBaseUrl: "https://fiqa-api-g7zatxrycq-uw.a.run.app",
    devTaskToken: "",
    tenantDisplayName: "陈总保险办公室",
    brokerDisplayName: "陈总",
    prototypeMode: true,
  };
}

export const appConfig = runtimeConfig;
