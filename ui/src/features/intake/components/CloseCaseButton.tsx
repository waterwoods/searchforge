/**
 * Minimal Broker Close control — Active Case → read-only History.
 */
import { useState } from 'react';
import { Button, Modal, Tag, message } from 'antd';
import { closeCase, type SavedCase } from '@/api/inboxTriage';
import { isCaseClosedHistory } from '@/features/intake/utils/caseLifecycle';

const CLOSE_WARNING =
  'Closing moves this case to read-only History. Customer can no longer edit or upload.';

export function ClosedHistoryBadge({ caseRecord }: { caseRecord: SavedCase | null | undefined }) {
  if (!isCaseClosedHistory(caseRecord)) return null;
  return (
    <Tag color="default" data-testid="closed-history-badge">
      Closed / History
    </Tag>
  );
}

export function CloseCaseButton({
  caseRecord,
  onClosed,
  block = false,
}: {
  caseRecord: SavedCase | null | undefined;
  onClosed: (updated: SavedCase) => void;
  block?: boolean;
}) {
  const [loading, setLoading] = useState(false);

  if (!caseRecord?.case_id || isCaseClosedHistory(caseRecord)) {
    return null;
  }

  const handleClick = () => {
    Modal.confirm({
      title: 'Close Case?',
      content: CLOSE_WARNING,
      okText: 'Close Case',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: async () => {
        setLoading(true);
        try {
          const result = await closeCase(caseRecord.case_id);
          const updated = result.case;
          message.success(
            result.outcome === 'already_closed'
              ? 'Case already Closed / History'
              : 'Case closed — now read-only History',
          );
          onClosed(updated);
        } catch (err) {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          message.error(typeof detail === 'string' ? detail : 'Close Case failed');
          throw err;
        } finally {
          setLoading(false);
        }
      },
    });
  };

  return (
    <Button
      danger
      loading={loading}
      onClick={handleClick}
      block={block}
      data-testid="close-case-button"
      style={block ? { marginBottom: 8 } : undefined}
    >
      Close Case
    </Button>
  );
}

export const CLOSE_CASE_WARNING_COPY = CLOSE_WARNING;
