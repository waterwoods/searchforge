/**
 * Temporary QA path tracer for real-device Preview (Remote Debug Console).
 * Focus: prove launch page + query + EARLY_EXIT reason.
 * Never logs tokens, VIN, or PII — only booleans / codes / hosts / keys.
 *
 * Avoid URL / URLSearchParams — not relied on for page registration safety.
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
  try {
    const safe: Record<string, string | number | boolean> = {};
    if (detail) {
      for (const key of Object.keys(detail)) {
        const value = detail[key];
        if (value == null) continue;
        if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
          safe[key] = value;
        }
      }
    }
    console.info(`[QA_PATH] ${step}`, safe);
  } catch (_err) {
    // ignore
  }
}

function parseQueryString(raw: string): Record<string, string> {
  const out: Record<string, string> = {};
  const s = raw.charAt(0) === "?" ? raw.slice(1) : raw;
  if (!s) return out;
  const parts = s.split("&");
  for (let i = 0; i < parts.length; i += 1) {
    const part = parts[i];
    if (!part) continue;
    const eq = part.indexOf("=");
    const key = eq >= 0 ? part.slice(0, eq) : part;
    const value = eq >= 0 ? part.slice(eq + 1) : "";
    if (!key) continue;
    try {
      out[decodeURIComponent(key)] = decodeURIComponent(value || "");
    } catch (_err) {
      out[key] = value || "";
    }
  }
  return out;
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

  let obj: Record<string, unknown>;
  if (typeof query === "string") {
    obj = parseQueryString(query);
  } else {
    obj = query;
  }

  const keys = Object.keys(obj).sort();
  const hasToken = Boolean(String(obj.token || "").trim());
  const hasDit = Boolean(String(obj.dit || "").trim());
  const parts = keys.map((key) => {
    if (key === "token" || key === "dit") return `${key}=(redacted)`;
    const v = String(obj[key] ?? "");
    return `${key}=${v.length > 40 ? `${v.slice(0, 40)}…` : v}`;
  });
  return {
    queryKeys: keys.length ? keys.join(",") : "(none)",
    queryRawSafe: parts.length ? parts.join("&") : "(empty)",
    hasToken: hasToken || hasDit,
  };
}
