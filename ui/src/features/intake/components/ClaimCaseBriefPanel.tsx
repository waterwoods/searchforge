/**
 * P19H-3e-1 — Claim Case Brief hero panel for Workbench drawer.
 */
import { Card, Tag, Typography } from 'antd';
import type { ClaimCaseBrief, ClaimTimelineEvent } from '@/api/inboxTriage';
import {
  formatClaimInjuryStatus,
  formatClaimPoliceStatus,
  formatClaimTimelinePreview,
  resolveClaimCaseBrief,
} from '@/features/intake/utils/claimWorkbenchDisplay';

const { Text, Paragraph } = Typography;

export type ClaimCaseBriefPanelProps = {
  brief?: ClaimCaseBrief | null;
  timeline?: ClaimTimelineEvent[] | null;
};

function severityColor(severity: string): string {
  switch ((severity || '').trim().toLowerCase()) {
    case 'critical':
      return 'red';
    case 'important':
      return 'orange';
    default:
      return 'default';
  }
}

export function ClaimCaseBriefPanel({ brief: briefProp, timeline }: ClaimCaseBriefPanelProps) {
  const brief = resolveClaimCaseBrief(briefProp);
  if (!brief) {
    return (
      <Card
        size="small"
        title="事故摘要"
        style={{ marginBottom: 12 }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Text type="secondary" style={{ fontSize: 12 }}>
          事故摘要暂未生成
        </Text>
      </Card>
    );
  }

  const keyFacts = brief.key_facts ?? {};
  const evidence = brief.evidence_received ?? {};
  const missing = (brief.missing_info ?? []).slice(0, 5);
  const timelinePreview = formatClaimTimelinePreview(timeline ?? [], 3);
  const photoCount = evidence.photo_count ?? 0;

  return (
    <Card
      size="small"
      title="事故摘要"
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: '12px 16px' } }}
      extra={
        brief.confidence ? (
          <Tag color={brief.confidence === 'high' ? 'green' : brief.confidence === 'medium' ? 'blue' : 'default'}>
            资料完整度 · {brief.confidence === 'high' ? '较全' : brief.confidence === 'medium' ? '部分' : '待补'}
          </Tag>
        ) : null
      }
    >
      <Paragraph style={{ fontSize: 14, marginBottom: 12 }}>{brief.summary}</Paragraph>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', marginBottom: 12 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          时间
        </Text>
        <Text style={{ fontSize: 13 }}>{keyFacts.accident_datetime || '—'}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          地点
        </Text>
        <Text style={{ fontSize: 13 }}>{keyFacts.accident_location || '—'}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          受伤
        </Text>
        <Text style={{ fontSize: 13 }}>{formatClaimInjuryStatus(keyFacts.injury_status)}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          警方
        </Text>
        <Text style={{ fontSize: 13 }}>{formatClaimPoliceStatus(keyFacts.police_involved)}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          照片
        </Text>
        <Text style={{ fontSize: 13 }}>已收 {photoCount} 张</Text>
      </div>

      {missing.length > 0 ? (
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            还缺什么
          </Text>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {missing.map((item) => (
              <li key={item.key} style={{ fontSize: 13, marginBottom: 4 }}>
                <Tag color={severityColor(item.severity)} style={{ marginRight: 6 }}>
                  {item.severity === 'critical' ? '重要' : item.severity === 'important' ? '需补' : '可选'}
                </Tag>
                {item.label}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {brief.next_best_question ? (
        <div
          style={{
            marginBottom: 12,
            padding: '10px 12px',
            background: '#f6ffed',
            border: '1px solid #b7eb8f',
            borderRadius: 6,
          }}
        >
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
            建议问客户
          </Text>
          <Text style={{ fontSize: 14, fontWeight: 500 }}>{brief.next_best_question}</Text>
        </div>
      ) : null}

      {timelinePreview.length > 0 ? (
        <div style={{ marginBottom: 4 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            最近记录
          </Text>
          {timelinePreview.map((line) => (
            <Text key={line.key} type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
              {line.label}
            </Text>
          ))}
        </div>
      ) : null}
    </Card>
  );
}
