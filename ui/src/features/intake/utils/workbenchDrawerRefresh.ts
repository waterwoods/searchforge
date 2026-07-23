/**
 * Workbench drawer refresh presentation — keep Waiting Customer detail stable
 * while background polling continues.
 */

export type DrawerRefreshPresentation = {
  /** True only when the drawer has no usable detail yet. */
  showSkeleton: boolean;
  /** Never flash on background poll; optional one-shot on empty initial load. */
  showRefreshingBanner: boolean;
  /** Structured Request More loading alert — initial hydrate only. */
  projectionLoading: boolean;
};

/**
 * Background refetch must not remount, clear, or replace stable drawer content
 * with an initial-loading surface.
 */
export function resolveDrawerRefreshPresentation(args: {
  hasDetail: boolean;
  initialLoading: boolean;
  backgroundRefreshing?: boolean;
}): DrawerRefreshPresentation {
  const initialEmpty = Boolean(args.initialLoading && !args.hasDetail);
  return {
    showSkeleton: initialEmpty,
    // Banner only when we have nothing to show yet — never on background poll.
    showRefreshingBanner: initialEmpty,
    projectionLoading: initialEmpty,
  };
}

/** Background poll may update fields in place; it must not clear selected detail. */
export function shouldPreserveDrawerDetailDuringRefresh(args: {
  selectedCaseId: string | null | undefined;
  incomingCaseId: string | null | undefined;
  backgroundRefreshing: boolean;
}): boolean {
  const selected = String(args.selectedCaseId || "").trim();
  const incoming = String(args.incomingCaseId || "").trim();
  if (!args.backgroundRefreshing) return true;
  if (!selected || !incoming) return false;
  return selected === incoming;
}
