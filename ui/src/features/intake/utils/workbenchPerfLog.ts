/** P19F-1 — Workbench drawer / preview latency logs (no PII). */

export function shortenCaseId(caseId: string): string {
  const id = (caseId || '').trim();
  if (id.length <= 12) return id;
  return `${id.slice(0, 8)}…`;
}

export type WorkbenchPerfSession = {
  caseId: string;
  attachmentCount: number;
  drawerOpenAt: number;
  caseGetMs?: number;
  firstPreviewMs?: number;
  allPreviewMs?: number;
  failedPreviewCount: number;
  loadedPreviewCount: number;
  imagePreviewCount: number;
};

export function createWorkbenchPerfSession(caseId: string, imagePreviewCount: number): WorkbenchPerfSession {
  const session: WorkbenchPerfSession = {
    caseId,
    attachmentCount: imagePreviewCount,
    drawerOpenAt: performance.now(),
    failedPreviewCount: 0,
    loadedPreviewCount: 0,
    imagePreviewCount,
  };
  console.info('[WORKBENCH_DRAWER_OPEN]', {
    case_id: shortenCaseId(caseId),
    attachmentCount: imagePreviewCount,
  });
  return session;
}

export function logCaseDetailLoaded(session: WorkbenchPerfSession, caseGetMs: number): void {
  session.caseGetMs = caseGetMs;
  console.info('[WORKBENCH_CASE_DETAIL_LOADED]', {
    case_id: shortenCaseId(session.caseId),
    caseGetMs,
    attachmentCount: session.attachmentCount,
  });
}

function maybeLogAllPreviewsLoaded(session: WorkbenchPerfSession): void {
  const target = session.imagePreviewCount;
  if (target <= 0) return;
  if (session.loadedPreviewCount + session.failedPreviewCount < target) return;
  if (session.allPreviewMs != null) return;
  session.allPreviewMs = Math.round(performance.now() - session.drawerOpenAt);
  console.info('[WORKBENCH_ALL_PREVIEWS_LOADED]', {
    case_id: shortenCaseId(session.caseId),
    allPreviewMs: session.allPreviewMs,
    loadedPreviewCount: session.loadedPreviewCount,
    failedPreviewCount: session.failedPreviewCount,
  });
}

export function logPreviewLoaded(session: WorkbenchPerfSession | null | undefined): void {
  if (!session) return;
  session.loadedPreviewCount += 1;
  if (session.firstPreviewMs == null) {
    session.firstPreviewMs = Math.round(performance.now() - session.drawerOpenAt);
    console.info('[WORKBENCH_FIRST_PREVIEW_LOADED]', {
      case_id: shortenCaseId(session.caseId),
      firstPreviewMs: session.firstPreviewMs,
    });
  }
  maybeLogAllPreviewsLoaded(session);
}

export function logPreviewFailed(session: WorkbenchPerfSession | null | undefined): void {
  if (!session) return;
  session.failedPreviewCount += 1;
  console.info('[WORKBENCH_PREVIEW_FAILED]', {
    case_id: shortenCaseId(session.caseId),
    failedPreviewCount: session.failedPreviewCount,
  });
  maybeLogAllPreviewsLoaded(session);
}

export function countImagePreviews(
  attachments: Array<{ preview_available?: boolean; mime_type?: string | null; document_type?: string | null; msgtype?: string | null }> | undefined,
  isImage: (att: { mime_type?: string | null; document_type?: string | null; msgtype?: string | null }) => boolean,
): number {
  if (!attachments?.length) return 0;
  return attachments.filter((att) => att.preview_available && isImage(att)).length;
}
