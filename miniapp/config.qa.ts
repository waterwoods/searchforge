/**
 * Committed HTTPS QA profile for Experience Version / phone pilot.
 * Selected when apiProfile is "qa" (via gitignored config.local.ts at upload time).
 *
 * Safe to commit: public Cloud Run URL only — no tokens, no AppID, no secrets.
 * Local DevTools should keep apiProfile "local" (defaults / config.local.ts).
 * Before Experience upload: set apiProfile "qa", clear devTaskToken, confirm Console
 * shows this HTTPS host, then compile/upload. Do not leave apiProfile on "local".
 */
export const config = {
  apiBaseUrl: "https://fiqa-api-g7zatxrycq-uw.a.run.app",
  // Prefer launch query `?token=h5t1...` — never commit a real token here.
  devTaskToken: "",
  tenantDisplayName: "陈总保险办公室",
  brokerDisplayName: "陈总",
  prototypeMode: true,
};
