/**
 * Chen Demo Invite launch helpers (pure + thin).
 * Keep token out of logs / durable storage.
 */

export const CHEN_DEMO_OFFICE_ID = "chen_kui";

export const DEMO_INVITE_ACTIVE_CASE_TITLE = "您已有一个正在处理的报案";
export const DEMO_INVITE_ACTIVE_CASE_CONTENT =
  "当前演示场景未更换。请先继续当前报案。\n\n如需切换演示客户，请联系办公室重置后再打开新入口。";

export const START_CLAIM_ROUTE_PATH = "/pages/start-claim/start-claim";

export function hasDemoInviteLaunchQuery(
  options?: Record<string, string | undefined> | null,
): boolean {
  const dit = String(options?.dit || "").trim();
  return Boolean(dit && dit.startsWith("di_"));
}

/** Intentional Start Claim form entry: Service Home ?entry=form OR Demo Invite dit=. */
export function isIntentionalStartClaimEntry(
  options?: Record<string, string | undefined> | null,
): boolean {
  if (String(options?.entry || "").trim() === "form") return true;
  return hasDemoInviteLaunchQuery(options);
}

/**
 * Normalize enter/launch query for Demo Invite routing.
 * WeChat may pass query as Record<string, any>.
 */
export function normalizeLaunchQuery(
  query?: Record<string, unknown> | null,
): Record<string, string | undefined> {
  const out: Record<string, string | undefined> = {};
  if (!query || typeof query !== "object") return out;
  for (const [k, v] of Object.entries(query)) {
    if (v == null) continue;
    out[k] = String(v);
  }
  return out;
}

/**
 * Build Start Claim URL for a Demo Invite Preview / QR enter.
 * Pure — used by App.onShow warm-start reLaunch so an already-open Case Status
 * page stack cannot ignore a new Preview `dit=`.
 */
export function buildDemoInviteStartClaimUrl(
  query?: Record<string, string | undefined> | null,
): string {
  const dit = String(query?.dit || "").trim();
  if (!dit || !dit.startsWith("di_")) return "";
  const entry = String(query?.entry || "form").trim() || "form";
  return `${START_CLAIM_ROUTE_PATH}?entry=${encodeURIComponent(entry)}&dit=${encodeURIComponent(dit)}`;
}

/**
 * Decide whether App.onShow must force-reLaunch into the new Preview path.
 * Returns the target URL when a new dit arrives while the JS runtime may still
 * be sitting on a prior Case Status / Task page.
 */
export function resolveWarmDemoInviteRelaunchUrl(params: {
  enterQuery?: Record<string, unknown> | null;
  lastHandledDit?: string | null;
}): { shouldRelaunch: boolean; dit: string; url: string } {
  const q = normalizeLaunchQuery(params.enterQuery);
  const dit = String(q.dit || "").trim();
  if (!dit || !dit.startsWith("di_")) {
    return { shouldRelaunch: false, dit: "", url: "" };
  }
  const last = String(params.lastHandledDit || "").trim();
  if (last && last === dit) {
    return { shouldRelaunch: false, dit, url: "" };
  }
  const url = buildDemoInviteStartClaimUrl(q);
  return { shouldRelaunch: Boolean(url), dit, url };
}
