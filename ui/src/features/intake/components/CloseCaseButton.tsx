/**
 * Minimal Broker Close control — Active Case → read-only History.
 */
import { useState } from 'react';
import { Button, Modal, Tag, message } from 'antd';
import { closeCase, type SavedCase } from '@/api/inboxTriage';
import { isCaseClosedHistory } from '@/features/intake/utils/caseLifecycle';

const CLOSE_WARNING =
  '关闭后案件进入只读历史。客户将无法继续编辑或上传。';

export function ClosedHistoryBadge({ caseRecord }: { caseRecord: SavedCase | null | undefined }) {
  if (!isCaseClosedHistory(caseRecord)) return null;
  return (
    <Tag color="default" data-testid="closed-history-badge">
      已关闭 / 历史
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
      title: '关闭案件？',
      content: CLOSE_WARNING,
      okText: '关闭案件',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true);
        try {
          const result = await closeCase(caseRecord.case_id);
          const updated = result.case;
          message.success(
            result.outcome === 'already_closed'
              ? '案件已是关闭 / 历史状态'
              : '案件已关闭 — 现为只读历史',
          );
          onClosed(updated);
        } catch (err) {
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          message.error(typeof detail === 'string' ? detail : '关闭案件失败');
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
      关闭案件
    </Button>
  );
}

export const CLOSE_CASE_WARNING_COPY = CLOSE_WARNING;
