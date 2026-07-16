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

function severityLabel(severity: string): string {
  switch ((severity || '').trim().toLowerCase()) {
    case 'critical':
      return '必填';
    case 'important':
      return '需补';
    default:
      return '选填';
  }
}

function highlightColor(level: string): string {
  switch ((level || '').trim().toLowerCase()) {
    case 'important':
      return 'red';
    case 'missing':
      return 'orange';
    case 'received':
      return 'green';
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
  const highlights = (brief.highlights ?? []).slice(0, 5);
  const timelinePreview = formatClaimTimelinePreview(timeline ?? [], 3);
  const photoCount = evidence.photo_count ?? 0;
  const ownVehicle = String(keyFacts.own_vehicle_info || '').trim() || '暂未提供';
  const otherPartyPlate = String(keyFacts.other_party_plate || '').trim() || '暂未提供';
  const otherPartyInfo = String(keyFacts.other_party_info || '').trim() || '暂未提供';

  return (
    <Card
      size="small"
      title="事故摘要 · 先看发生了什么"
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: '12px 16px' } }}
      extra={
        brief.confidence ? (
          <Tag color={brief.confidence === 'high' ? 'green' : brief.confidence === 'medium' ? 'blue' : 'default'}>
            事故理解 · {brief.confidence === 'high' ? '较清' : brief.confidence === 'medium' ? '部分' : '待补'}
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

      <div style={{ marginBottom: 12 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
          车辆与对方
        </Text>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          我方车辆
        </Text>
        <Text style={{ fontSize: 13 }}>{ownVehicle}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          对方车牌
        </Text>
        <Text style={{ fontSize: 13 }}>{otherPartyPlate}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          对方信息
        </Text>
        <Text style={{ fontSize: 13 }}>{otherPartyInfo}</Text>
        </div>
      </div>

      {highlights.length > 0 ? (
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            重点速览
          </Text>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {highlights.map((item, index) => (
              <Tag key={`${item.kind}-${index}`} color={highlightColor(item.level)} style={{ margin: 0 }}>
                {item.label}
              </Tag>
            ))}
          </div>
        </div>
      ) : null}

      {missing.length > 0 ? (
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            事故理解缺口
          </Text>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {missing.map((item) => (
              <li key={item.key} style={{ fontSize: 13, marginBottom: 4 }}>
                <Tag color={severityColor(item.severity)} style={{ marginRight: 6 }}>
                  {severityLabel(item.severity)}
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
