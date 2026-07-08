/**
 * P19H-3c-3B — Claim evidence checklist section for Workbench drawer.
 */
import { Card, Typography } from 'antd';
import type { ClaimEvidenceSummary } from '@/api/inboxTriage';
import {
  formatClaimEvidenceSlotLine,
  formatClaimUnassignedWecomPhotosSection,
} from '@/features/intake/utils/claimWorkbenchDisplay';

const { Text } = Typography;

export type ClaimEvidenceChecklistProps = {
  summary?: ClaimEvidenceSummary | null;
};

export function ClaimEvidenceChecklist({ summary }: ClaimEvidenceChecklistProps) {
  if (!summary || !Array.isArray(summary.slots) || summary.slots.length === 0) {
    return (
      <Card
        size="small"
        title="理赔照片 / Evidence Checklist"
        style={{ marginBottom: 12 }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Text type="secondary" style={{ fontSize: 12 }}>
          理赔照片状态暂未生成
        </Text>
      </Card>
    );
  }

  const summaryText = (summary.summary_text || '').trim();
  const brokerNextAction = (summary.broker_next_action || '').trim();
  const unassignedSection = formatClaimUnassignedWecomPhotosSection(summary);

  return (
    <Card
      size="small"
      title="理赔照片 / Evidence Checklist"
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      {summaryText ? (
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 10 }}>
          {summaryText}
        </Text>
      ) : null}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {summary.slots.map((slot) => {
          const line = formatClaimEvidenceSlotLine(slot);
          return (
            <div key={slot.slot_key}>
              <Text style={{ fontSize: 14, display: 'block' }}>
                {line.icon} {line.label}
              </Text>
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 2, paddingLeft: 20 }}>
                {line.detail}
              </Text>
            </div>
          );
        })}
      </div>

      {unassignedSection ? (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid #f0f0f0' }}>
          <Text style={{ fontSize: 14, display: 'block', marginBottom: 4 }}>
            待分类微信照片
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            {unassignedSection.summaryLine}
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            {unassignedSection.guidanceLine}
          </Text>
          {unassignedSection.items.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {unassignedSection.items.map((item) => (
                <Text key={item.key} type="secondary" style={{ fontSize: 12 }}>
                  {item.label}
                </Text>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {brokerNextAction ? (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid #f0f0f0' }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
            下一步建议
          </Text>
          <Text style={{ fontSize: 13 }}>{brokerNextAction}</Text>
        </div>
      ) : null}
    </Card>
  );
}
