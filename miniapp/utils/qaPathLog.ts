/**
 * Temporary QA path tracer for real-device Preview (Remote Debug Console).
 * Focus: prove launch page + query + EARLY_EXIT reason.
 * Never logs tokens, VIN, or PII — only booleans / codes / hosts / keys.
 */

export type QaPathStep =
  | "LAUNCH"
  | "ENTRY"
  | "BOOTSTRAP"
  | "EARLY_EXIT"
  | "REQUEST_START"
  | "REQUEST_SENT"
  | "REQUEST_FAIL"
  | "REQUEST_SUCCESS";

export function qaPathLog(
  step: QaPathStep,
  detail?: Record<string, string | number | boolean | undefined | null>,
): void {
  const safe: Record<string, string | number | boolean> = {};
  if (detail) {
    for (const [key, value] of Object.entries(detail)) {
      if (value == null) continue;
      if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
        safe[key] = value;
      }
    }
  }
  // Loud single-line prefix for Remote Debug filter: QA_PATH
  console.info(`[QA_PATH] ${step}`, safe);
}

/** Summarize launch/page query without exposing token values. */
export function summarizeLaunchQuery(
  query: Record<string, unknown> | string | undefined | null,
): {
  queryKeys: string;
  queryRawSafe: string;
  hasToken: boolean;
} {
  if (query == null || query === "") {
    return { queryKeys: "(none)", queryRawSafe: "(empty)", hasToken: false };
  }

  if (typeof query === "string") {
    const params = new URLSearchParams(query.startsWith("?") ? query.slice(1) : query);
    const keys = Array.from(params.keys()).sort();
    const hasToken = Boolean(String(params.get("token") || "").trim());
    const parts: string[] = [];
    params.forEach((value, key) => {
      if (key === "token") {
        parts.push("token=(redacted)");
        return;
      }
      // Keep non-secret short values for compile-mode debugging.
      const v = String(value || "");
      parts.push(`${key}=${v.length > 40 ? `${v.slice(0, 40)}…` : v}`);
    });
    return {
      queryKeys: keys.length ? keys.join(",") : "(none)",
      queryRawSafe: parts.length ? parts.join("&") : "(empty)",
      hasToken,
    };
  }

  const keys = Object.keys(query).sort();
  const hasToken = Boolean(String(query.token || "").trim());
  const parts = keys.map((key) => {
    if (key === "token") return "token=(redacted)";
    const v = String(query[key] ?? "");
    return `${key}=${v.length > 40 ? `${v.slice(0, 40)}…` : v}`;
  });
  return {
    queryKeys: keys.length ? keys.join(",") : "(none)",
    queryRawSafe: parts.length ? parts.join("&") : "(empty)",
    hasToken,
  };
}
