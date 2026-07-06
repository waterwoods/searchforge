/** P19B — attachment display helpers (no OCR UI). */

export function humanizeDocumentType(documentType?: string | null): string {
  const t = (documentType || '').trim().toLowerCase();
  const map: Record<string, string> = {
    unknown_document: 'Unknown document',
    vin_photo: 'VIN photo',
    registration: 'Registration',
    renewal_notice: 'Renewal notice',
    accident_photo: 'Accident photo',
    dmv_notice: 'DMV notice',
    dec_page: 'Declaration page',
    screenshot: 'Screenshot',
    image: 'WeCom image',
  };
  if (map[t]) return map[t];
  if (!t) return 'Unknown document';
  return t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function humanizeMimeLabel(mime?: string | null): string {
  const m = (mime || '').toLowerCase();
  if (m.includes('jpeg') || m.includes('jpg')) return 'JPEG';
  if (m.includes('png')) return 'PNG';
  if (m.includes('pdf')) return 'PDF';
  if (m.includes('gif')) return 'GIF';
  if (!m) return '—';
  return m.split('/').pop()?.toUpperCase() || m;
}

export function formatAttachmentSize(sizeBytes?: number | null): string {
  const n = sizeBytes ?? 0;
  if (n <= 0) return '—';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatAttachmentReceivedAt(iso?: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function ocrStatusLabel(status?: string | null): string {
  const s = (status || 'not_started').toLowerCase();
  if (s === 'not_started') return 'OCR: not started';
  if (s === 'unavailable') return 'OCR: unavailable';
  return 'OCR: pending';
}

export function isImageAttachment(att: { mime_type?: string | null; document_type?: string | null; msgtype?: string | null }): boolean {
  const mime = (att.mime_type || '').toLowerCase();
  if (mime.startsWith('image/')) return true;
  if ((att.msgtype || '').toLowerCase() === 'image') return true;
  const dt = (att.document_type || '').toLowerCase();
  return dt.includes('photo') || dt === 'screenshot' || dt === 'vin_photo';
}

export function countCaseAttachments(attachments?: unknown[] | null): number {
  if (!Array.isArray(attachments)) return 0;
  return attachments.filter((raw) => {
    if (!raw || typeof raw !== 'object') return false;
    const att = raw as { intake_status?: string };
    const status = (att.intake_status || 'promoted').toLowerCase();
    return status !== 'quarantined';
  }).length;
}

export function isQuarantinedAttachment(att: { intake_status?: string | null }): boolean {
  return (att.intake_status || '').toLowerCase() === 'quarantined';
}

export function guardrailStatusLabel(status?: string | null): string | null {
  const s = (status || '').toLowerCase();
  if (s === 'accepted') return null;
  if (s === 'bulk_confirm_needed') return 'Bulk confirm needed';
  if (s === 'bulk_upload_paused') return 'Bulk upload paused';
  if (s === 'claim_batch_confirm_needed') return 'Claim batch confirm needed';
  return null;
}

export function partitionAttachments<T extends { intake_status?: string | null }>(
  attachments: T[],
): { promoted: T[]; quarantined: T[] } {
  const promoted: T[] = [];
  const quarantined: T[] = [];
  for (const att of attachments) {
    if (isQuarantinedAttachment(att)) {
      quarantined.push(att);
    } else {
      promoted.push(att);
    }
  }
  return { promoted, quarantined };
}

export function isWeComMediaIntakeLane(serviceLane?: string | null): boolean {
  return (serviceLane || '').trim() === 'wecom_media_intake';
}
