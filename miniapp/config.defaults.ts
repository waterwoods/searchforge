/**
 * Committed prototype defaults — safe to compile in WeChat DevTools.
 * Override locally via launch query `?token=h5t1...` (preferred) or config.local.ts.
 *
 * apiBaseUrl notes:
 * - DevTools simulator on same machine: http://127.0.0.1:8001
 * - WSL2 + DevTools on Windows: http://<WSL-host-ip>:8001 (grep nameserver /etc/resolv.conf)
 * - Real-device preview: http://<LAN-ip>:8001 — never use 127.0.0.1 on a phone
 */
export const config = {
  apiProfile: "local" as "local" | "qa",
  apiBaseUrl: "http://127.0.0.1:8001",
  devTaskToken: "",
  tenantDisplayName: "陈总保险办公室",
  brokerDisplayName: "陈总",
  prototypeMode: true,
  /**
   * P4 Integration 01 — Smart Claim Start wiring.
   * Pilot posture (intentional): OFF.
   * Default Founder QA walk is S1–S6 customer journey without Cap 01–03.
   * Enable only in gitignored config.local.ts when Founder validates Cap 01–03.
   */
  smartClaimStartEnabled: false,
};
