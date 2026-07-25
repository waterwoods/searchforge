/**
 * P26E — Unified production upload state machine.
 *
 * Authority:
 * - Projection (server) decides Confirmed.
 * - Client only holds local transient upload state (path, progress, transport flags).
 * - Both Insurance Card (request-item) and Accident Photos reuse this lifecycle.
 *
 * Lifecycle (exact names):
 *   Selected → Uploading → Uploaded → Confirmed
 *   any transport failure → Failed (Retry)
 */

export type UploadPhase =
  | "idle"
  | "selected"
  | "uploading"
  | "uploaded"
  | "confirmed"
  | "failed";

export const UPLOAD_PHASE_LABEL: Record<UploadPhase, string> = {
  idle: "",
  selected: "已选择",
  uploading: "上传中",
  uploaded: "已上传",
  confirmed: "已收到",
  failed: "上传失败，可重试",
};

export type UploadTransient = {
  localPath: string;
  uploading: boolean;
  /** Transport finished; awaiting projection confirmation. */
  uploaded: boolean;
  error: string;
  progress: number;
  attachmentId?: string;
  uploadIntentId?: string;
};

export type PendingUploadTransient = {
  uploadIntentId: string;
  localPath: string;
};

/**
 * Resolve display phase from Projection confirmation + local transient only.
 * Never invents Confirmed from local flags alone.
 */
export function resolveUploadPhase(args: {
  projectionConfirmed: boolean;
  transient: Pick<
    UploadTransient,
    "localPath" | "uploading" | "uploaded" | "error" | "attachmentId"
  >;
}): UploadPhase {
  if (args.projectionConfirmed) return "confirmed";
  if (args.transient.uploading) return "uploading";
  if (args.transient.error) return "failed";
  if (args.transient.attachmentId || args.transient.uploaded) return "uploaded";
  if (args.transient.localPath) return "selected";
  return "idle";
}

export function uploadPhaseDetail(
  phase: UploadPhase,
  progress = 0,
): string {
  if (phase === "selected") return "已选择，尚未上传";
  if (phase === "uploading") {
    const safe = Math.max(0, Math.min(100, Number(progress) || 0));
    return `上传中… ${safe}%`;
  }
  if (phase === "uploaded") return "已上传，正在确认";
  if (phase === "confirmed") return "陈总已能看到";
  if (phase === "failed") return "上传失败，可重试";
  return "";
}

export function uploadStatusText(args: {
  phase: UploadPhase;
  received?: number;
  required?: number;
}): string {
  const { phase } = args;
  if (phase === "failed") return UPLOAD_PHASE_LABEL.failed;
  if (phase === "uploading") return UPLOAD_PHASE_LABEL.uploading;
  if (phase === "confirmed") return "已收到";
  if (phase === "uploaded") return "正在确认是否收到";
  if (phase === "selected") return UPLOAD_PHASE_LABEL.selected;
  const received = Math.max(0, Number(args.received) || 0);
  const required = Math.max(1, Number(args.required) || 1);
  if (received > 0) return `已确认 ${received}/${required}`;
  return "待选择";
}

/**
 * Merge Projection confirmation with prior transient after reconcile/read-back.
 *
 * Root-cause fix: Accident Photos wiped `localPath` on every reconcile unless an
 * error draft existed — so after upload read-back the thumbnail/phase badges
 * disappeared even though the upload succeeded. Insurance Card kept the path via
 * draft restore. Session preview is local transient only; Projection still owns
 * Confirmed.
 */
export function mergeUploadTransientAfterReconcile(args: {
  prev?: Partial<UploadTransient> | null;
  pending?: PendingUploadTransient | null;
  projectionConfirmed: boolean;
}): UploadTransient & { canRetry: boolean; canRemove: boolean } {
  const prev = args.prev || {};
  const pending = args.pending || null;
  const hasError = Boolean(prev.error);
  const keepPending = Boolean(pending && !hasError);
  // Retain in-page session preview (prev or pending). Cleared only by explicit remove
  // or a fresh page instance — never by Projection reconcile.
  const localPath = String(prev.localPath || pending?.localPath || "").trim();
  const uploadIntentId = keepPending
    ? String(pending?.uploadIntentId || prev.uploadIntentId || "")
    : hasError
      ? String(prev.uploadIntentId || "")
      : "";

  return {
    localPath,
    uploadIntentId,
    // `uploaded` is transport-only; clear once projection confirms so "add more" stays open.
    uploaded: keepPending,
    uploading: keepPending ? Boolean(prev.uploading) : false,
    progress: hasError || keepPending
      ? Math.max(Number(prev.progress) || 0, 0)
      : args.projectionConfirmed && localPath
        ? 100
        : localPath && prev.uploaded
          ? 100
          : Math.max(Number(prev.progress) || 0, 0),
    error: hasError ? String(prev.error || "") : "",
    attachmentId: String(prev.attachmentId || ""),
    canRetry: hasError,
    canRemove: hasError && Boolean(localPath || prev.error),
  };
}
