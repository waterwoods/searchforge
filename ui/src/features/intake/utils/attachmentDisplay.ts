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
  return Array.isArray(attachments) ? attachments.length : 0;
}

export function isWeComMediaIntakeLane(serviceLane?: string | null): boolean {
  return (serviceLane || '').trim() === 'wecom_media_intake';
}
