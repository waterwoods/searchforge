/**
 * Temporary QA path tracer for real-device Preview (Remote Debug Console).
 * Never logs tokens, VIN, or PII — only booleans / codes / hosts.
 */

export function qaPathLog(
  step:
    | "ENTRY"
    | "BOOTSTRAP"
    | "REQUEST_START"
    | "REQUEST_SENT"
    | "REQUEST_FAIL"
    | "REQUEST_SUCCESS"
    | "EARLY_EXIT",
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
  console.info(`[QA_PATH] ${step}`, safe);
}
