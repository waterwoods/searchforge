/**
 * Committed HTTPS Cloud QA profile for Experience Version / phone Founder QA.
 * Selected when apiProfile is "qa" (via gitignored config.local.ts at upload time).
 *
 * P36 T5: targets isolated Cloud QA (fiqa-api-qa) — never Production fiqa-api.
 *
 * Safe to commit: public Cloud Run URL only — no tokens, no AppID, no secrets.
 * Local DevTools should keep apiProfile "local" (defaults / config.local.ts).
 * Before Experience upload: set apiProfile "qa", clear devTaskToken, confirm Console
 * shows this HTTPS host, then compile/upload. Do not leave apiProfile on "local".
 * Do not upload/publish a Production Mini Program release from this QA profile.
 */
export const config = {
  apiBaseUrl: "https://fiqa-api-qa-g7zatxrycq-uw.a.run.app",
  // Prefer launch query `?token=h5t1...` — never commit a real token here.
  devTaskToken: "",
  tenantDisplayName: "陈总保险办公室",
  brokerDisplayName: "陈总",
  prototypeMode: true,
  // Founder QA may enable via config.local.ts — keep committed QA default OFF.
  smartClaimStartEnabled: false,
};
