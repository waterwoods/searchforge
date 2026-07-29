/**
 * Chen Demo Invite launch helpers (pure + thin).
 * Keep token out of logs / durable storage.
 */

export const CHEN_DEMO_OFFICE_ID = "chen_kui";

export const DEMO_INVITE_ACTIVE_CASE_TITLE = "您已有一个正在处理的报案";
export const DEMO_INVITE_ACTIVE_CASE_CONTENT =
  "当前演示场景未更换。请先继续当前报案。\n\n如需切换演示客户，请联系办公室重置后再打开新入口。";

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
