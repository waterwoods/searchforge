/**
 * P26H-UI — request-item Empty Page Gate (SSOT for render visibility).
 *
 * WXML must bind to showWorkSurface / showFooterCta from this helper.
 * Do not gate the upload surface on nextAction alone — system_default
 * insurance intentionally has no Slice1 nextAction.
 */

export type RequestItemRenderState = {
  loading?: boolean | null;
  waitingForBroker?: boolean | null;
  inputMode?: string | null;
  nextAction?: unknown;
  nextActionTitle?: string | null;
  pageError?: {
    blocking?: boolean | null;
    message?: string | null;
    code?: string | null;
  } | null;
  /** Bound into WXML — when absent, treat as legacy nextAction-only (blank-page bug). */
  showWorkSurface?: boolean | null;
  showFooterCta?: boolean | null;
};

export type RequestItemWorkSurface = {
  showWorkSurface: boolean;
  showFooterCta: boolean;
  rejectedWarning: boolean;
  emptyPage: boolean;
};

function nonEmpty(value: unknown): string {
  return String(value || "").trim();
}

export function resolveRequestItemWorkSurface(
  data: RequestItemRenderState,
): RequestItemWorkSurface {
  const message = nonEmpty(data.pageError?.message);
  const rejectedWarning =
    Boolean(data.pageError?.blocking) &&
    (message.includes("无需此步骤") || nonEmpty(data.pageError?.code) === "slice1_not_enabled");
  const inputMode = nonEmpty(data.inputMode);
  const hasWorkMode = inputMode === "evidence" || inputMode === "text";
  const showWorkSurface =
    Boolean(data.waitingForBroker) || hasWorkMode || Boolean(data.nextAction);
  const showFooterCta =
    !Boolean(data.loading) &&
    !rejectedWarning &&
    (Boolean(data.waitingForBroker) || hasWorkMode || Boolean(data.nextAction));
  // Legacy blank-page defect: page computed evidence mode but WXML only bound nextAction.
  const contentBoundVisible =
    typeof data.showWorkSurface === "boolean"
      ? data.showWorkSurface
      : Boolean(data.waitingForBroker) || Boolean(data.nextAction);
  const emptyPage =
    !Boolean(data.loading) &&
    !rejectedWarning &&
    !Boolean(data.waitingForBroker) &&
    hasWorkMode &&
    !contentBoundVisible;
  return { showWorkSurface, showFooterCta, rejectedWarning, emptyPage };
}

/** True when insurance upload primary controls are renderable. */
export function insuranceUploadPrimaryUiPresent(data: RequestItemRenderState): boolean {
  const surface = resolveRequestItemWorkSurface(data);
  if (surface.rejectedWarning || surface.emptyPage) return false;
  if (Boolean(data.loading)) return false;
  return (
    surface.showWorkSurface &&
    nonEmpty(data.inputMode) === "evidence" &&
    (typeof data.showWorkSurface === "boolean"
      ? Boolean(data.showWorkSurface)
      : Boolean(data.nextAction))
  );
}
