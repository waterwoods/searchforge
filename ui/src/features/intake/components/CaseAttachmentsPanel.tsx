/**
 * P19B — Workbench attachment panel (WeCom + web uploads).
 * Read-only metadata display; no OCR, no slot editing.
 */
import { useCallback, useEffect, useState } from 'react';
import { Button, Card, Image, Space, Tag, Typography } from 'antd';
import {
  FileImageOutlined,
  FilePdfOutlined,
  PaperClipOutlined,
} from '@ant-design/icons';
import type { CaseAttachment } from '@/api/inboxTriage';
import request from '@/api/request';
import { API_BASE_URL } from '@/api/config';
import {
  formatAttachmentReceivedAt,
  formatAttachmentSize,
  guardrailStatusLabel,
  humanizeDocumentType,
  humanizeMimeLabel,
  isImageAttachment,
  isQuarantinedAttachment,
  ocrStatusLabel,
  partitionAttachments,
} from '@/features/intake/utils/attachmentDisplay';

const { Text, Paragraph } = Typography;

type Props = {
  caseId: string;
  attachments?: CaseAttachment[];
};

function bindingTagColor(confidence: string): string {
  const c = (confidence || '').toLowerCase();
  if (c === 'high') return 'success';
  if (c === 'medium') return 'processing';
  return 'default';
}

function sourceLabel(source?: string): string {
  const s = (source || '').toLowerCase();
  if (s === 'wecom') return 'WeCom';
  if (s === 'h5_task') return 'H5 Task';
  return 'Web';
}

function AttachmentThumbnail({ caseId, att }: { caseId: string; att: CaseAttachment }) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const previewPath = att.preview_url || `/api/inbox/cases/${caseId}/attachments/${att.attachment_id}/preview`;

  useEffect(() => {
    if (!att.preview_available || !isImageAttachment(att)) {
      return undefined;
    }
    let revoked: string | null = null;
    let cancelled = false;
    (async () => {
      try {
        const resp = await request.get(previewPath, { responseType: 'blob' });
        if (cancelled) return;
        revoked = URL.createObjectURL(resp.data);
        setBlobUrl(revoked);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [att.attachment_id, att.preview_available, previewPath, att.mime_type, att.document_type]);

  if (!att.preview_available || !isImageAttachment(att) || failed) {
    const Icon = (att.mime_type || '').includes('pdf') ? FilePdfOutlined : FileImageOutlined;
    return (
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: 6,
          background: '#fafafa',
          border: '1px solid #f0f0f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Icon style={{ fontSize: 32, color: '#bfbfbf' }} />
      </div>
    );
  }

  if (!blobUrl) {
    return (
      <div
        style={{
          width: 96,
          height: 96,
          borderRadius: 6,
          background: '#fafafa',
          border: '1px solid #f0f0f0',
          flexShrink: 0,
        }}
      />
    );
  }

  return (
    <Image
      src={blobUrl}
      alt={humanizeDocumentType(att.document_type)}
      width={96}
      height={96}
      style={{ objectFit: 'cover', borderRadius: 6, flexShrink: 0 }}
      preview={{ src: blobUrl }}
    />
  );
}

async function openAttachmentPreview(caseId: string, att: CaseAttachment): Promise<void> {
  const previewPath = att.preview_url || `/api/inbox/cases/${caseId}/attachments/${att.attachment_id}/preview`;
  const resp = await request.get(previewPath, { responseType: 'blob' });
  const url = URL.createObjectURL(resp.data);
  const w = window.open(url, '_blank', 'noopener,noreferrer');
  if (!w) {
    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.click();
  }
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function AttachmentCard({ caseId, att, quarantined = false }: { caseId: string; att: CaseAttachment; quarantined?: boolean }) {
  const [opening, setOpening] = useState(false);
  const docType = humanizeDocumentType(att.document_type);
  const needsClassification = (att.document_type || '').toLowerCase() === 'unknown_document';
  const guardLabel = guardrailStatusLabel(att.guardrail_status);

  const handleOpen = useCallback(async () => {
    if (!att.preview_available) return;
    setOpening(true);
    try {
      await openAttachmentPreview(caseId, att);
    } finally {
      setOpening(false);
    }
  }, [caseId, att]);

  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '10px 0',
        borderBottom: '1px solid #f0f0f0',
        background: quarantined ? '#fffbe6' : undefined,
        borderRadius: quarantined ? 6 : undefined,
      }}
    >
      <AttachmentThumbnail caseId={caseId} att={att} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text strong style={{ fontSize: 14, display: 'block' }}>
          {docType}
        </Text>
        {needsClassification ? (
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
            Needs broker classification
          </Text>
        ) : null}
        <Space size={4} wrap style={{ marginBottom: 6 }}>
          <Tag style={{ margin: 0 }}>{sourceLabel(att.source)}</Tag>
          {att.intake_status === 'unassigned' ? (
            <Tag color="warning" style={{ margin: 0 }}>Unassigned</Tag>
          ) : null}
          {quarantined || isQuarantinedAttachment(att) ? (
            <>
              <Tag color="warning" style={{ margin: 0 }}>Needs Review</Tag>
              {guardLabel ? <Tag color="orange" style={{ margin: 0 }}>{guardLabel}</Tag> : null}
              <Tag style={{ margin: 0 }}>Not eligible for OCR</Tag>
            </>
          ) : (
            <>
              <Tag color="success" style={{ margin: 0 }}>Accepted</Tag>
              {att.eligible_for_ocr ? (
                <Tag color="processing" style={{ margin: 0 }}>Eligible for OCR later</Tag>
              ) : null}
            </>
          )}
          <Tag color={bindingTagColor(att.binding_confidence || 'unknown')} style={{ margin: 0 }}>
            Binding: {att.binding_confidence || 'unknown'}
          </Tag>
          <Tag style={{ margin: 0 }}>{ocrStatusLabel(att.ocr_status)}</Tag>
          {att.storage_status === 'stored' ? (
            <Tag color="success" style={{ margin: 0 }}>Stored</Tag>
          ) : null}
        </Space>
        <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
          {formatAttachmentReceivedAt(att.received_at)} · {humanizeMimeLabel(att.mime_type)} ·{' '}
          {formatAttachmentSize(att.size_bytes)}
        </Text>
        {att.broker_confirmed === false ? (
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
            Broker confirmed: no
          </Text>
        ) : null}
        {att.preview_available ? (
          <Button type="link" size="small" style={{ padding: 0, marginTop: 4 }} loading={opening} onClick={() => void handleOpen()}>
            Preview / Open full
          </Button>
        ) : (
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
            Preview unavailable
          </Text>
        )}
      </div>
    </div>
  );
}

export function CaseAttachmentsPanel({ caseId, attachments }: Props) {
  const items = attachments ?? [];
  const { promoted, quarantined } = partitionAttachments(items);

  return (
    <Card
      size="small"
      title={
        <Space size={6}>
          <PaperClipOutlined />
          <span>Uploaded Documents / Attachments ({promoted.length})</span>
        </Space>
      }
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: items.length > 0 ? '4px 16px 8px' : '12px 16px' } }}
    >
      {items.length === 0 ? (
        <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 13 }}>
          No uploaded documents yet.
          <br />
          Customer can send photos through WeCom.
        </Paragraph>
      ) : (
        <>
          {promoted.map((att) => (
            <AttachmentCard key={att.attachment_id} caseId={caseId} att={att} />
          ))}
          {quarantined.length > 0 ? (
            <div style={{ marginTop: promoted.length > 0 ? 12 : 0 }}>
              <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                Quarantined Uploads ({quarantined.length})
              </Text>
              {quarantined.map((att) => (
                <AttachmentCard key={att.attachment_id} caseId={caseId} att={att} quarantined />
              ))}
            </div>
          ) : null}
        </>
      )}
    </Card>
  );
}

/** Resolve full preview URL for API-relative paths (auth fetch uses axios base). */
export function resolveAttachmentPreviewPath(previewUrl: string): string {
  const p = (previewUrl || '').trim();
  if (p.startsWith('http')) return p;
  const base = API_BASE_URL.replace(/\/+$/, '');
  return `${base}${p.startsWith('/') ? p : `/${p}`}`;
}

export function attachmentCountLabel(count: number): string | null {
  if (count <= 0) return null;
  return `📎 ${count}`;
}
