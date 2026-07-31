/**
 * P19B — Workbench attachment panel (WeCom + web uploads).
 * P19F-1 — skeleton placeholders, lazy preview load, perf logs.
 * Read-only metadata display; no OCR, no slot editing.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Card, Image, Space, Spin, Tag, Typography } from 'antd';
import {
  FileImageOutlined,
  FilePdfOutlined,
  PaperClipOutlined,
  ReloadOutlined,
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
import type { WorkbenchPerfSession } from '@/features/intake/utils/workbenchPerfLog';
import { logPreviewFailed, logPreviewLoaded } from '@/features/intake/utils/workbenchPerfLog';

const { Text, Paragraph } = Typography;

const PREVIEW_STAGGER_MS = 120;

type Props = {
  caseId: string;
  attachments?: CaseAttachment[];
  perfSession?: WorkbenchPerfSession | null;
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
  if (s === 'h5_task') return 'H5 Task / Guided Upload';
  return 'Web';
}

function PreviewPlaceholder({
  loading,
  failed,
  onRetry,
}: {
  loading?: boolean;
  failed?: boolean;
  onRetry?: () => void;
}) {
  return (
    <div
      style={{
        width: 96,
        height: 96,
        borderRadius: 6,
        background: '#f5f5f5',
        border: '1px solid #e8e8e8',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        gap: 4,
        padding: 6,
        textAlign: 'center',
      }}
    >
      {failed ? (
        <>
          <FileImageOutlined style={{ fontSize: 24, color: '#bfbfbf' }} />
          <Text type="secondary" style={{ fontSize: 10, lineHeight: 1.3 }}>
            预览加载失败
          </Text>
          {onRetry ? (
            <Button type="link" size="small" icon={<ReloadOutlined />} onClick={onRetry} style={{ fontSize: 11, height: 'auto', padding: 0 }}>
              Retry
            </Button>
          ) : null}
        </>
      ) : loading ? (
        <>
          <Spin size="small" />
          <Text type="secondary" style={{ fontSize: 10, lineHeight: 1.3 }}>
            正在加载预览…
          </Text>
        </>
      ) : (
        <FileImageOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
      )}
    </div>
  );
}

function AttachmentThumbnail({
  caseId,
  att,
  loadDelayMs = 0,
  perfSession,
}: {
  caseId: string;
  att: CaseAttachment;
  loadDelayMs?: number;
  perfSession?: WorkbenchPerfSession | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const previewPath = att.preview_url || `/api/inbox/cases/${caseId}/attachments/${att.attachment_id}/preview`;
  const canPreview = Boolean(att.preview_available && isImageAttachment(att));

  useEffect(() => {
    if (!canPreview) return undefined;
    const el = containerRef.current;
    if (!el) return undefined;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '80px', threshold: 0.01 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [canPreview, att.attachment_id]);

  useEffect(() => {
    if (!canPreview || !inView) return undefined;
    let revoked: string | null = null;
    let cancelled = false;
    let delayTimer: ReturnType<typeof setTimeout> | undefined;

    const fetchPreview = () => {
      setLoading(true);
      setFailed(false);
      (async () => {
        try {
          const resp = await request.get(previewPath, { responseType: 'blob' });
          if (cancelled) return;
          revoked = URL.createObjectURL(resp.data);
          setBlobUrl(revoked);
          logPreviewLoaded(perfSession);
        } catch {
          if (!cancelled) {
            setFailed(true);
            logPreviewFailed(perfSession);
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    };

    if (loadDelayMs > 0) {
      delayTimer = setTimeout(fetchPreview, loadDelayMs);
    } else {
      fetchPreview();
    }

    return () => {
      cancelled = true;
      if (delayTimer) clearTimeout(delayTimer);
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [canPreview, inView, previewPath, att.attachment_id, att.mime_type, att.document_type, loadDelayMs, perfSession, retryKey]);

  const handleRetry = useCallback(() => {
    setBlobUrl(null);
    setFailed(false);
    setRetryKey((k) => k + 1);
  }, []);

  if (!canPreview) {
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

  if (failed) {
    return (
      <div ref={containerRef}>
        <PreviewPlaceholder failed onRetry={handleRetry} />
      </div>
    );
  }

  if (!blobUrl) {
    return (
      <div ref={containerRef}>
        <PreviewPlaceholder loading={inView || loading} />
      </div>
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

function AttachmentCard({
  caseId,
  att,
  quarantined = false,
  previewIndex = 0,
  perfSession,
}: {
  caseId: string;
  att: CaseAttachment;
  quarantined?: boolean;
  previewIndex?: number;
  perfSession?: WorkbenchPerfSession | null;
}) {
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
      <AttachmentThumbnail
        caseId={caseId}
        att={att}
        loadDelayMs={previewIndex * PREVIEW_STAGGER_MS}
        perfSession={perfSession}
      />
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

export function CaseAttachmentsPanel({ caseId, attachments, perfSession }: Props) {
  const items = attachments ?? [];
  const { promoted, quarantined } = partitionAttachments(items);
  let previewIndex = 0;

  return (
    <Card
      size="small"
      title={
        <Space size={6}>
          <PaperClipOutlined />
          <span>已上传附件（{promoted.length}）</span>
        </Space>
      }
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: items.length > 0 ? '4px 16px 8px' : '12px 16px' } }}
    >
      {items.length === 0 ? (
        <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 13 }}>
          暂无上传附件。
          <br />
          客户可通过小程序继续补充照片。
        </Paragraph>
      ) : (
        <>
          {promoted.map((att) => {
            const staggerIdx =
              att.preview_available && isImageAttachment(att) ? previewIndex++ : 0;
            return (
              <AttachmentCard
                key={att.attachment_id}
                caseId={caseId}
                att={att}
                previewIndex={staggerIdx}
                perfSession={perfSession}
              />
            );
          })}
          {quarantined.length > 0 ? (
            <div style={{ marginTop: promoted.length > 0 ? 12 : 0 }}>
              <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
                Quarantined Uploads ({quarantined.length})
              </Text>
              {quarantined.map((att) => {
                const staggerIdx =
                  att.preview_available && isImageAttachment(att) ? previewIndex++ : 0;
                return (
                  <AttachmentCard
                    key={att.attachment_id}
                    caseId={caseId}
                    att={att}
                    quarantined
                    previewIndex={staggerIdx}
                    perfSession={perfSession}
                  />
                );
              })}
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
