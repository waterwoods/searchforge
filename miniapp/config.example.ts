/**
 * Copy to config.local.ts for local prototype runs. Do not commit real tokens.
 *
 * Backend must bind 0.0.0.0:8001 (run_demo_local.sh does this).
 * Real-device / WSL preview: set apiBaseUrl to your machine LAN IP, not 127.0.0.1.
 */
export const config = {
  // DevTools simulator only:
  apiBaseUrl: "http://127.0.0.1:8001",
  // WSL2 example: apiBaseUrl: "http://172.21.164.252:8001",
  // Real phone on Wi-Fi: apiBaseUrl: "http://192.168.x.x:8001",
  devTaskToken: "",
  tenantDisplayName: "陈总保险办公室",
  brokerDisplayName: "陈总",
  prototypeMode: true,
};
