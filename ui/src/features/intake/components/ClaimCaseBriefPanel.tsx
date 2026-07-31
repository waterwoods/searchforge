/**
 * P19H-3e-1 / P27-B2 — Claim conclusion panel for Workbench (one conclusion + one next action).
 * Happy Path Loop 1 — Cap2 Must Have suggestion + 确认资料已齐 CTA.
 */
import { Alert, Button, Card, Tag, Typography } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import type { ClaimCaseBrief, ClaimTimelineEvent } from '@/api/inboxTriage';
import {
  formatClaimAccidentDateTime,
  formatClaimInjuryStatus,
  formatClaimPoliceStatus,
  formatClaimTimelinePreview,
  resolveClaimCaseBrief,
} from '@/features/intake/utils/claimWorkbenchDisplay';

const { Text, Paragraph } = Typography;

export type ClaimCaseBriefPanelProps = {
  brief?: ClaimCaseBrief | null;
  timeline?: ClaimTimelineEvent[] | null;
  /** Optional office next-step override (e.g. broker_next_step). */
  nextAction?: string | null;
  /** Happy Path Loop 1 — broker accepts Cap2 Must Haves as office-ready. */
  onAcceptOfficeMaterials?: () => void;
  acceptOfficeMaterialsSaving?: boolean;
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

export function ClaimCaseBriefPanel({
  brief: briefProp,
  timeline,
  nextAction,
  onAcceptOfficeMaterials,
  acceptOfficeMaterialsSaving,
}: ClaimCaseBriefPanelProps) {
  const brief = resolveClaimCaseBrief(briefProp);
  if (!brief) {
    return (
      <Card
        size="small"
        title="理赔结论"
        style={{ marginBottom: 12 }}
        styles={{ body: { padding: '12px 16px' } }}
      >
        <Text type="secondary" style={{ fontSize: 12 }}>
          理赔结论暂未生成
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
  const canAccept = Boolean(brief.can_accept_office_materials && onAcceptOfficeMaterials);
  const suggestion =
    String(brief.office_materials_ready_suggestion || '').trim() || '建议确认资料已齐';
  const acceptedAt = String(brief.office_materials_accepted_at || '').trim();
  const claimVehicle = keyFacts.claim_vehicle;
  const vehicleSummary =
    String(claimVehicle?.summary || keyFacts.own_vehicle_info || '').trim() || '暂未提供';
  const vehicleYear = String(claimVehicle?.year || '').trim();
  const vehicleMake = String(claimVehicle?.make || '').trim();
  const vehicleModel = String(claimVehicle?.model || '').trim();
  const vehicleVin = String(claimVehicle?.vin || '').trim();
  const vehiclePlate = String(claimVehicle?.license_plate || '').trim();
  const vehiclePlateState = String(claimVehicle?.plate_state || '').trim();
  const hasStructuredVehicle = Boolean(
    claimVehicle
    && (vehicleYear || vehicleMake || vehicleModel || vehicleVin || vehiclePlate),
  );
  const otherPartyPlate = String(keyFacts.other_party_plate || '').trim() || '暂未提供';
  const otherPartyInfo = String(keyFacts.other_party_info || '').trim() || '暂未提供';
  const resolvedNext =
    String(nextAction || '').trim()
    || String(brief.next_best_question || '').trim();

  return (
    <Card
      size="small"
      title="理赔结论"
      style={{ marginBottom: 12 }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <Paragraph style={{ fontSize: 14, marginBottom: 12 }}>{brief.summary}</Paragraph>

      {canAccept ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message={suggestion}
          description="事故必填项已齐。确认后进入办公室处理；不会结束案件。"
          action={
            <Button
              type="primary"
              size="small"
              icon={<CheckCircleOutlined />}
              loading={Boolean(acceptOfficeMaterialsSaving)}
              onClick={() => onAcceptOfficeMaterials?.()}
            >
              确认资料已齐
            </Button>
          }
        />
      ) : null}
      {acceptedAt && !canAccept ? (
        <Alert
          type="success"
          showIcon
          style={{ marginBottom: 12 }}
          message="资料已齐，等待办公室处理"
        />
      ) : null}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', marginBottom: 12 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          时间
        </Text>
        <Text style={{ fontSize: 13 }}>{formatClaimAccidentDateTime(keyFacts.accident_datetime)}</Text>
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
        <Text style={{ fontSize: 13 }}>{vehicleSummary}</Text>
        {hasStructuredVehicle ? (
          <>
            {vehicleYear || vehicleMake || vehicleModel ? (
              <>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  年款 / 品牌 / 型号
                </Text>
                <Text style={{ fontSize: 13 }}>
                  {[vehicleYear, vehicleMake, vehicleModel].filter(Boolean).join(' ') || '—'}
                </Text>
              </>
            ) : null}
            {vehicleVin ? (
              <>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  VIN
                </Text>
                <Text style={{ fontSize: 13 }} copyable={{ text: vehicleVin }}>
                  {vehicleVin}
                </Text>
              </>
            ) : claimVehicle?.vin_unavailable ? (
              <>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  VIN
                </Text>
                <Text style={{ fontSize: 13 }}>暂时无法提供</Text>
              </>
            ) : null}
            {vehiclePlate ? (
              <>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  车牌
                </Text>
                <Text style={{ fontSize: 13 }}>
                  {vehiclePlateState ? `${vehiclePlateState} ` : ''}
                  {vehiclePlate}
                </Text>
              </>
            ) : null}
          </>
        ) : null}
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
            重点
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
            仍缺信息
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

      {resolvedNext ? (
        <div
          style={{
            marginBottom: timelinePreview.length > 0 ? 12 : 4,
            padding: '10px 12px',
            background: '#f0f5ff',
            border: '1px solid #adc6ff',
            borderRadius: 6,
          }}
        >
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
            下一步
          </Text>
          <Text style={{ fontSize: 14, fontWeight: 600, color: '#10239e' }}>{resolvedNext}</Text>
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
