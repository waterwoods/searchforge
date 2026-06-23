/**
 * P16 Trust Layer — Add-Car Trusted Packet Wizard
 *
 * TurboTax-style 6-screen flow (P16 Customer Flow Blueprint):
 *   Screen 0: Intent Selector  (add_vehicle / replace_vehicle)
 *   Screen 1: Customer Info    (Name / Phone / Garaging ZIP)
 *   Screen 2: Upload Documents (PDF / JPG / PNG / HEIC, max 10)
 *   Screen 3: Extracting       (animated loading steps)
 *   Screen 4: Sent to Broker   (customer-facing completion — ADR-003 compliant)
 *   Screen 5: Trusted Packet   (broker-facing; accessible via secondary link)
 */

import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Form,
  Input,
  message,
  Space,
  Steps,
  Tag,
  Typography,
  Upload,
} from 'antd';
import type { UploadFile } from 'antd';
import {
  CalendarOutlined,
  CarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudUploadOutlined,
  CopyOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  FileTextOutlined,
  DollarOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  ReloadOutlined,
  RiseOutlined,
  SendOutlined,
  SwapOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { API_BASE_URL } from '../api/config';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

// ─── Types ────────────────────────────────────────────────────────────────────

type FieldData = {
  value: string;
  confidence: number;
  confidence_label: 'high' | 'medium' | 'low';
  source_file: string;
  is_mock: boolean;
  needs_confirmation?: boolean;
};

type PacketResponse = {
  packet: Record<string, FieldData>;
  warnings: string[];
  sources: Array<{ file: string; fields: string }>;
  copy_text: string;
  portal_copy_text?: string;
  mock_mode: boolean;
  model_used: string;
  confirmation_notices?: string[];
  case_id?: string;
  document_guidance?: string | null;
  extraction_failed?: boolean;
  message?: string;
  message_zh?: string;
  /** Policy Review lane — backend-derived readiness */
  readiness_status?: ReadinessStatus;
  follow_up_message_zh?: string;
  opportunity_signals?: Array<{ code: string; meaning: string }>;
  broker_next_action?: { en: string; zh: string };
  vehicles?: Array<{
    year?: string;
    make?: string;
    model?: string;
    vin?: string;
    vehicle_premium?: string;
    source_file?: string;
  }>;
  drivers?: Array<{
    name?: string;
    relationship?: string;
    license_state?: string;
    visible_violation_or_accident?: string;
    source_file?: string;
  }>;
  document_types_detected?: string[];
  request_type?: string;
};

/** All wizard screens including new Screen 0 (intent) and Screen 4 (sent). */
type WizardStep = 'intent' | 'info' | 'upload' | 'extracting' | 'sent' | 'packet';

/** Which request the customer selected on Screen 0. */
type RequestType = 'add_vehicle' | 'replace_vehicle' | 'policy_review';

type VinStatus = 'valid' | 'warning' | 'missing';

const STEP_INDEX: Record<WizardStep, number> = {
  intent: 0,
  info: 1,
  upload: 2,
  extracting: 3,
  sent: 4,
  packet: 4, // broker packet is a secondary view at the same progress level as sent
};

// ─── VIN Validation (client-side) ────────────────────────────────────────────

const VIN_TRANSLITERATION: Record<string, number> = {
  A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8,
  J: 1, K: 2, L: 3, M: 4, N: 5,
  P: 7, R: 9,
  S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9,
};
const VIN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2];

function validateVin(vin: string): { valid: boolean; reason: string } {
  if (!vin) return { valid: false, reason: 'VIN is empty' };
  const v = vin.toUpperCase().trim();
  if (v.length !== 17) return { valid: false, reason: `VIN must be 17 characters (got ${v.length})` };
  if (/[IOQ]/.test(v)) return { valid: false, reason: 'VIN contains invalid characters (I, O, or Q not allowed)' };
  if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(v)) return { valid: false, reason: 'VIN contains invalid characters' };
  let total = 0;
  for (let i = 0; i < 17; i++) {
    const ch = v[i];
    const val = /\d/.test(ch) ? parseInt(ch, 10) : (VIN_TRANSLITERATION[ch] ?? 0);
    total += val * VIN_WEIGHTS[i];
  }
  const rem = total % 11;
  const expected = rem === 10 ? 'X' : String(rem);
  if (v[8] !== expected) {
    return { valid: false, reason: `VIN checksum mismatch — expected '${expected}' at position 9, got '${v[8]}'` };
  }
  return { valid: true, reason: 'VIN format valid' };
}

// ─── Readiness types ─────────────────────────────────────────────────────────

type ReadinessStatus = 'ready' | 'needs_info' | 'broker_review';
type FieldStatus = 'complete' | 'needs_confirmation' | 'missing';

const FIELD_CHINESE: Record<string, string> = {
  vin: '车辆 VIN 或 Registration 照片',
  year: '车辆年份 (Year)',
  make: '车辆品牌 (Make)',
  model: '车辆型号 (Model)',
  garaging_zip: '车辆主要停放 ZIP Code',
  primary_driver: '主要驾驶人姓名',
  effective_date: '保险生效/起保日期',
};

function getFieldStatus(field: FieldData | undefined): FieldStatus {
  if (!field?.value) return 'missing';
  if (field.needs_confirmation) return 'needs_confirmation';
  return 'complete';
}

function isPolicyReview(requestType: RequestType): boolean {
  return requestType === 'policy_review';
}

function computeReadinessStatus(
  packet: Record<string, FieldData>,
  vinStatus: VinStatus,
  warnings: string[],
  documentGuidance?: string | null,
): ReadinessStatus {
  // Document Relevance Gate: no vehicle info found at all → customer must re-upload
  // NEED_INFO wins over broker_review for missing-document cases (ADR-001)
  if (documentGuidance) return 'needs_info';
  // Real broker-review conflicts: invalid VIN format when VIN exists, conflicting data, extraction errors
  if (vinStatus === 'warning' || warnings.length > 0) return 'broker_review';
  // Critical fields missing after extraction (partial result)
  const criticalMissing = ['vin', 'year', 'make', 'model'].filter(k => !packet[k]?.value);
  if (criticalMissing.length > 0) return 'needs_info';
  return 'ready';
}

function resolveReadinessStatus(
  response: PacketResponse,
  packet: Record<string, FieldData>,
  vinStatus: VinStatus,
  warnings: string[],
  documentGuidance?: string | null,
): ReadinessStatus {
  if (response.readiness_status) return response.readiness_status;
  return computeReadinessStatus(packet, vinStatus, warnings, documentGuidance);
}

const EXTRACTION_FAILED_MESSAGE =
  "We couldn't read these documents. Please try uploading clearer vehicle documents or contact your broker.";
const EXTRACTION_FAILED_MESSAGE_ZH =
  '系统未能读取这些文件。请重新上传更清晰的车辆资料，或联系您的保险经纪人。';

function buildCriticalFollowUpKeys(
  vinValue: string,
  year: string,
  make: string,
  model: string,
  displayZip: string,
): string[] {
  const keys: string[] = [];
  if (!vinValue) keys.push('vin');
  if (!year) keys.push('year');
  if (!make) keys.push('make');
  if (!model) keys.push('model');
  if (!displayZip) keys.push('garaging_zip');
  return keys;
}

function shouldShowAutoFollowUp(status: ReadinessStatus, criticalKeys: string[]): boolean {
  if (criticalKeys.length === 0) return false;
  return status === 'needs_info' || status === 'broker_review';
}

const NEXT_ACTION_COPY: Record<ReadinessStatus, { en: string; zh: string }> = {
  ready: {
    en: 'Copy packet into AMS / carrier portal and start quote.',
    zh: '下一步：复制数据包到 AMS/保险公司系统并开始报价。',
  },
  needs_info: {
    en: 'Send the follow-up message to the customer and wait for updated documents.',
    zh: '下一步：发送下方跟进消息给客户，并等待补充资料。',
  },
  broker_review: {
    en: 'Review warnings before quoting. Verify conflicting information first.',
    zh: '下一步：报价前请先查看警告，并核实冲突信息。',
  },
};

const POLICY_REVIEW_NEXT_ACTION: Record<ReadinessStatus, { en: string; zh: string }> = {
  ready: {
    en: 'Packet is substantially complete — broker can enter carrier portal for manual re-shop.',
    zh: '资料基本齐全，可以进入 carrier portal 手动重新比价。',
  },
  needs_info: {
    en: 'Send the Chinese follow-up below; ask customer for declaration page or renewal notice.',
    zh: '请先发送下方中文跟进消息，让客户补充保单首页或续保通知。',
  },
  broker_review: {
    en: 'Data has conflicts or uncertainty — verify premium, coverage, or violations before re-shopping.',
    zh: '资料存在不确定或冲突，请先人工核对保费、保额或违章信息，再决定是否比价。',
  },
};

const POLICY_REPORT_BROKER_ACTION_FALLBACK = {
  en: 'Your broker should review the extracted policy information and confirm whether more documents are needed before re-shopping.',
  zh: '经纪人应先核对已识别的保单信息，并确认是否需要更多资料后再进行比价。',
};

type PolicyOpportunityItem = {
  key: string;
  titleEn: string;
  titleZh: string;
  detailEn?: string;
  detailZh?: string;
};

type PolicyVehicleSnapshotLine = {
  primary: string;
  secondary?: string;
};

function formatPolicyTerm(start?: string, end?: string): string {
  if (start && end) return `${start} – ${end}`;
  return start || end || '';
}

function buildPolicyVehicleSnapshotLines(
  response: PacketResponse,
  packet: Record<string, FieldData>,
): PolicyVehicleSnapshotLine[] {
  const fromVehicles = (response.vehicles ?? [])
    .map((v) => {
      const primary = [v.year, v.make, v.model].filter(Boolean).join(' ');
      if (!primary) return null;
      const secondaryParts: string[] = [];
      if (v.vehicle_premium?.trim()) secondaryParts.push(v.vehicle_premium.trim());
      if (v.vin?.trim()) secondaryParts.push(`VIN ${v.vin.trim()}`);
      return {
        primary,
        secondary: secondaryParts.length ? secondaryParts.join(' · ') : undefined,
      };
    })
    .filter((line): line is PolicyVehicleSnapshotLine => line !== null);

  if (fromVehicles.length > 0) return fromVehicles;

  const summary = [packet.year?.value, packet.make?.value, packet.model?.value]
    .filter(Boolean)
    .join(' ');
  return summary ? [{ primary: summary }] : [];
}

function hasHighLiabilityLimits(bodilyInjury: string): boolean {
  const compact = bodilyInjury.replace(/\s/g, '');
  if (/100\/300|250\/500|300\/500|500\/500/.test(compact)) return true;
  return /\b(250|300|500)\b/.test(bodilyInjury);
}

function policyHasCoreFields(
  get: (key: string) => string,
  vehicles: PacketResponse['vehicles'],
  drivers: PacketResponse['drivers'],
): boolean {
  const hasVehicle = (vehicles ?? []).some((v) => v.vin || (v.year && v.make));
  const hasDriver = (drivers ?? []).some((d) => d.name?.trim());
  const coverageCount = [
    'bodily_injury',
    'property_damage',
    'uninsured_motorist',
    'comprehensive_deductible',
    'collision_deductible',
  ].filter((k) => get(k)).length;
  return !!(
    get('current_carrier')
    && get('premium_amount')
    && hasVehicle
    && hasDriver
    && coverageCount >= 2
  );
}

function buildPolicyOpportunityItems(
  response: PacketResponse,
  packet: Record<string, FieldData>,
  readinessStatus: ReadinessStatus,
): PolicyOpportunityItem[] {
  const items: PolicyOpportunityItem[] = [];
  const seen = new Set<string>();
  const get = (key: string) => packet[key]?.value || '';

  const add = (item: PolicyOpportunityItem) => {
    if (seen.has(item.key)) return;
    seen.add(item.key);
    items.push(item);
  };

  const premium = get('premium_amount');
  if (premium) {
    const period = get('premium_period');
    add({
      key: 'premium_recognized',
      titleEn: 'Current premium recognized',
      titleZh: '已识别当前保费',
      detailEn: period ? `${premium} for ${period}` : `${premium} for current term`,
      detailZh: period ? `当前周期保费 ${premium}（${period}）` : `当前周期保费 ${premium}`,
    });
  }

  const vehicles = response.vehicles ?? [];
  const drivers = response.drivers ?? [];

  if (policyHasCoreFields(get, vehicles, drivers)) {
    add({
      key: 'reshop_review',
      titleEn: 'Ready for broker re-shop review',
      titleZh: '资料基本可用于经纪人重新比价',
      detailEn: 'Carrier, premium, vehicles, drivers, and coverage were found.',
      detailZh: '已识别保险公司、保费、车辆、驾驶员及保额信息。',
    });
  }

  if (vehicles.length >= 2) {
    add({
      key: 'multi_vehicle',
      titleEn: 'Multi-vehicle household',
      titleZh: '多车家庭',
      detailEn: `${vehicles.length} vehicles found — possible bundle / umbrella discussion.`,
      detailZh: `发现 ${vehicles.length} 辆车 — 可讨论打包或 Umbrella 方案。`,
    });
  }

  const bodilyInjury = get('bodily_injury');
  if (hasHighLiabilityLimits(bodilyInjury)) {
    add({
      key: 'umbrella_review',
      titleEn: 'Umbrella review opportunity',
      titleZh: '可考虑 Umbrella 保护需求',
      detailEn: 'High liability limits found; broker may review whether umbrella coverage is appropriate.',
      detailZh: '保额限额较高；经纪人可评估是否需要 Umbrella 额外责任险。',
    });
  }

  const missingPolicyNumber = !get('policy_number');
  const missingDeductible = !get('comprehensive_deductible') && !get('collision_deductible');
  if (missingPolicyNumber || missingDeductible) {
    add({
      key: 'missing_before_quote',
      titleEn: 'Review missing details before quoting',
      titleZh: '比价前请核对缺失资料',
      detailEn: 'Policy number or deductible details were not found.',
      detailZh: '未找到保单号或免赔额信息，比价前请核对。',
    });
  }

  for (const signal of response.opportunity_signals ?? []) {
    if (signal.code === 'VIOLATION_PRESENT') {
      add({
        key: 'VIOLATION_PRESENT',
        titleEn: 'Violation or accident noted',
        titleZh: '文件显示违章或事故记录',
        detailEn: 'Broker should verify driver history before re-shopping.',
        detailZh: '经纪人应先核实驾驶员记录，再决定是否比价。',
      });
    } else if (signal.code === 'DO_NOT_OVERPROMISE') {
      add({
        key: 'DO_NOT_OVERPROMISE',
        titleEn: 'Verify before discussing options',
        titleZh: '讨论方案前请先核实',
        detailEn: 'Risk factors or unclear data present — broker should explain before discussing options.',
        detailZh: '存在不确定因素或资料不完整，经纪人应先说明情况再讨论方案。',
      });
    }
  }

  if (readinessStatus === 'needs_info' && !seen.has('missing_before_quote')) {
    add({
      key: 'needs_info_followup',
      titleEn: 'More policy details may be needed',
      titleZh: '可能还需要补充保单资料',
      detailEn: 'Declaration page, premium, vehicles, drivers, or coverage may be incomplete.',
      detailZh: '保单首页、保费、车辆、驾驶员或保额信息可能尚不完整。',
    });
  }

  return items.slice(0, 6);
}

function NextActionLine({ status, requestType, brokerNextAction }: { status: ReadinessStatus; requestType?: RequestType; brokerNextAction?: { en: string; zh: string } }) {
  const copy = brokerNextAction ?? (isPolicyReview(requestType ?? 'add_vehicle') ? POLICY_REVIEW_NEXT_ACTION[status] : NEXT_ACTION_COPY[status]);
  return (
    <div style={{
      background: '#fafafa',
      border: '1px solid #e8e8e8',
      borderRadius: 8,
      padding: '12px 16px',
      marginBottom: 16,
    }}>
      <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>
        Next Action:
      </Text>
      <Text style={{ fontSize: 14, display: 'block', lineHeight: 1.6 }}>{copy.en}</Text>
      <Text type="secondary" style={{ fontSize: 13, display: 'block', marginTop: 4, lineHeight: 1.6 }}>
        {copy.zh}
      </Text>
    </div>
  );
}

// ─── Follow-up message (Chinese) ──────────────────────────────────────────────

function buildFollowUpMessage(missingKeys: string[], uploadLink?: string): string {
  const items: string[] = [];
  let n = 1;

  const vehicleKeys = ['year', 'make', 'model'].filter(k => missingKeys.includes(k));
  const otherKeys = missingKeys.filter(k => !['year', 'make', 'model'].includes(k));

  if (vehicleKeys.length === 3) {
    items.push(`${n++}. 车辆年份、品牌、型号 (Year / Make / Model)`);
  } else {
    for (const k of vehicleKeys) {
      items.push(`${n++}. ${FIELD_CHINESE[k] ?? k}`);
    }
  }
  for (const k of otherKeys) {
    const label = FIELD_CHINESE[k];
    if (label) items.push(`${n++}. ${label}`);
  }

  if (items.length === 0) return '';

  const lines = [
    '您好，为了继续处理您的加车申请，还需要您补充以下资料：',
    '',
    ...items,
    '',
    uploadLink
      ? `请直接在这个链接补充上传，收到后我们可以继续处理，谢谢。\n${uploadLink}`
      : '请直接回复补充以上资料，收到后我们可以继续处理，谢谢。',
  ];

  return lines.join('\n');
}

// ─── Broker-friendly copy text (generated on frontend) ───────────────────────

function buildCopyText(
  packet: Record<string, FieldData>,
  warnings: string[],
  sources: Array<{ file: string; fields: string }>,
  customerName: string,
  garagingZip: string,
  requestType?: RequestType,
  oldVehicleVin?: string,
  oldVehiclePlate?: string,
): string {
  const get = (key: string) => packet[key]?.value || '';

  const name = get('customer_name') || customerName || 'MISSING';
  const phone = get('phone') || 'MISSING';
  const primaryDriver = get('primary_driver');
  const driverIsDefaulted = packet.primary_driver?.source_file === 'default_from_customer_name';

  const vin = get('vin') || 'MISSING';
  const year = get('year') || 'MISSING';
  const make = get('make') || 'MISSING';
  const model = get('model') || 'MISSING';
  const zip = get('garaging_zip') || garagingZip || 'MISSING';

  const effectiveDate = get('effective_date') || get('delivery_date') || '';
  const lienholder = get('finance_or_lienholder') || '';

  const REQUIRED_FOR_MISSING: Array<[string, string]> = [
    ['VIN', 'vin'],
    ['Year', 'year'],
    ['Make', 'make'],
    ['Model', 'model'],
    ['Effective Date', 'effective_date'],
  ];
  const missingItems = REQUIRED_FOR_MISSING.filter(([, key]) => !get(key)).map(([label]) => label);

  const driverLine = primaryDriver
    ? `  Primary Driver: ${primaryDriver}${driverIsDefaulted ? ' (defaulted from customer name — confirm)' : ''}`
    : '  Primary Driver: MISSING';

  const packetHeader = requestType === 'replace_vehicle' ? 'REPLACE-VEHICLE PACKET' : 'ADD-CAR PACKET';

  const parts: string[] = [];
  parts.push(`${packetHeader}\n`);
  parts.push('Customer:');
  parts.push(`  Name: ${name}`);
  parts.push(`  Phone: ${phone}`);
  parts.push('\nDriver:');
  parts.push(driverLine);
  parts.push('\nVehicle:');
  parts.push(`  VIN: ${vin}`);
  parts.push(`  Year: ${year}`);
  parts.push(`  Make: ${make}`);
  parts.push(`  Model: ${model}`);
  parts.push(`  Garaging ZIP: ${zip}`);
  parts.push('\nFinance & Timing:');
  parts.push(effectiveDate ? `  Effective Date: ${effectiveDate}` : '  Effective Date: not provided');
  if (lienholder) parts.push(`  Lienholder: ${lienholder}`);
  parts.push(missingItems.length > 0 ? `\nMissing Items: ${missingItems.join(', ')}` : '\nMissing Items: None');

  if (requestType === 'replace_vehicle') {
    const oldVin = oldVehicleVin?.trim() || 'MISSING';
    const oldPlate = oldVehiclePlate?.trim() || 'MISSING';
    parts.push('\nVehicle to Remove (Reference Only):');
    parts.push(`  Old VIN: ${oldVin}`);
    parts.push(`  Old Plate: ${oldPlate}`);
    if (oldVin === 'MISSING' && oldPlate === 'MISSING') {
      parts.push('  ⚠ Broker confirmation required — neither old VIN nor old plate provided');
    }
  }

  if (warnings.length > 0) {
    parts.push('\nWarnings:');
    warnings.forEach(w => parts.push(`  ⚠ ${w}`));
  } else {
    parts.push('\nWarnings: None');
  }

  if (sources.length > 0) {
    parts.push('\nSources:');
    sources.forEach(s => parts.push(`  ${s.file} → ${s.fields}`));
  }

  return parts.join('\n');
}

// ─── DetailField: shows value + source + confidence (for "Show details" panel) ─

function DetailField({ field }: { field: FieldData }) {
  const isEmpty = !field.value;
  const confidenceColor =
    field.confidence_label === 'high' ? 'green'
    : field.confidence_label === 'medium' ? 'orange'
    : 'default';
  return (
    <Space direction="vertical" size={2} style={{ width: '100%' }}>
      <Text strong style={{ color: isEmpty ? '#ff4d4f' : undefined }}>
        {field.value || 'MISSING'}
      </Text>
      {!isEmpty && (
        <Space size={4} wrap>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {field.source_file || '—'}
          </Text>
          <Tag color={confidenceColor} style={{ fontSize: 11 }}>
            {field.confidence_label}
          </Tag>
        </Space>
      )}
    </Space>
  );
}

// ─── VIN Status Pill ─────────────────────────────────────────────────────────

function VinStatusPill({ status }: { status: VinStatus }) {
  if (status === 'valid') {
    return (
      <Tag color="success" icon={<CheckCircleOutlined />} style={{ fontSize: 13, padding: '3px 10px' }}>
        VIN Valid
      </Tag>
    );
  }
  if (status === 'warning') {
    return (
      <Tag color="warning" icon={<WarningOutlined />} style={{ fontSize: 13, padding: '3px 10px' }}>
        VIN Warning
      </Tag>
    );
  }
  return (
    <Tag color="error" icon={<CloseCircleOutlined />} style={{ fontSize: 13, padding: '3px 10px' }}>
      VIN Missing
    </Tag>
  );
}

// ─── Screen 0: Intent Selector ────────────────────────────────────────────────
// P16 Customer Flow Blueprint §Screen 0
// No insurance jargon. Both languages. One decision. < 30 seconds.

function IntentStep({ onSelect }: { onSelect: (type: RequestType) => void }) {
  const [hovered, setHovered] = useState<RequestType | null>(null);

  const tileStyle = (type: RequestType): React.CSSProperties => ({
    cursor: 'pointer',
    borderRadius: 12,
    border: `2px solid ${hovered === type ? '#1677ff' : '#e8e8e8'}`,
    boxShadow: hovered === type ? '0 4px 16px rgba(22,119,255,0.12)' : '0 1px 4px rgba(0,0,0,0.04)',
    transition: 'border-color 0.18s, box-shadow 0.18s',
    marginBottom: 0,
  });

  return (
    <div style={{ maxWidth: 540, margin: '0 auto' }}>
      {/* Welcoming header */}
      <div style={{ textAlign: 'center', padding: '4px 0 36px' }}>
        <Title level={2} style={{ marginBottom: 8, fontWeight: 700 }}>
          What do you need help with?
        </Title>
        <Text style={{ fontSize: 17, color: 'rgba(0,0,0,0.50)' }}>
          您需要什么帮助？
        </Text>
      </div>

      <Space direction="vertical" size={16} style={{ width: '100%' }}>

        {/* Tile 1: Add Vehicle */}
        <Card
          style={tileStyle('add_vehicle')}
          bodyStyle={{ padding: '24px 28px' }}
          onClick={() => onSelect('add_vehicle')}
          onMouseEnter={() => setHovered('add_vehicle')}
          onMouseLeave={() => setHovered(null)}
        >
          <Space align="center" size={20}>
            <div style={{
              width: 60, height: 60, borderRadius: 14,
              background: '#e6f4ff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <CarOutlined style={{ fontSize: 30, color: '#1677ff' }} />
            </div>
            <div style={{ flex: 1 }}>
              <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
                I bought a new car
              </Title>
              <Text style={{ fontSize: 15, color: 'rgba(0,0,0,0.55)' }}>
                我买了一辆新车，需要加到保险上
              </Text>
            </div>
          </Space>
        </Card>

        {/* Tile 2: Replace Vehicle */}
        <Card
          style={tileStyle('replace_vehicle')}
          bodyStyle={{ padding: '24px 28px' }}
          onClick={() => onSelect('replace_vehicle')}
          onMouseEnter={() => setHovered('replace_vehicle')}
          onMouseLeave={() => setHovered(null)}
        >
          <Space align="center" size={20}>
            <div style={{
              width: 60, height: 60, borderRadius: 14,
              background: '#fff7e6',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <SwapOutlined style={{ fontSize: 30, color: '#fa8c16' }} />
            </div>
            <div style={{ flex: 1 }}>
              <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
                I replaced my old car with a new one
              </Title>
              <Text style={{ fontSize: 15, color: 'rgba(0,0,0,0.55)' }}>
                我换了一辆新车，需要更新保险
              </Text>
            </div>
          </Space>
        </Card>

        {/* Tile 3: Policy Review */}
        <Card
          style={tileStyle('policy_review')}
          bodyStyle={{ padding: '24px 28px' }}
          onClick={() => onSelect('policy_review')}
          onMouseEnter={() => setHovered('policy_review')}
          onMouseLeave={() => setHovered(null)}
        >
          <Space align="center" size={20}>
            <div style={{
              width: 60, height: 60, borderRadius: 14,
              background: '#f6ffed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <DollarOutlined style={{ fontSize: 30, color: '#52c41a' }} />
            </div>
            <div style={{ flex: 1 }}>
              <Title level={4} style={{ margin: 0, marginBottom: 4 }}>
                Review My Policy
              </Title>
              <Text style={{ fontSize: 14, color: 'rgba(0,0,0,0.55)', display: 'block', marginBottom: 4 }}>
                I want to check if my current premium or coverage should be reviewed.
              </Text>
              <Text style={{ fontSize: 15, color: 'rgba(0,0,0,0.55)' }}>
                帮我看看当前保单 — 我想检查现在的保费或保障是否值得重新比较。
              </Text>
            </div>
          </Space>
        </Card>

      </Space>

      <div style={{ textAlign: 'center', marginTop: 36 }}>
        <Text style={{ fontSize: 13, color: 'rgba(0,0,0,0.35)' }}>
          No login required · 无需登录 &nbsp;·&nbsp; Less than 3 minutes · 不超过3分钟
        </Text>
      </div>
    </div>
  );
}

// ─── Screen 1: Customer Info ──────────────────────────────────────────────────

function InfoStep({
  requestType,
  onNext,
}: {
  requestType: RequestType;
  onNext: (name: string, phone: string, zip: string, oldVin?: string, oldPlate?: string) => void;
}) {
  const [form] = Form.useForm();

  const handleFinish = (values: {
    name: string; phone: string; zip: string; old_vin?: string; old_plate?: string;
  }) => {
    onNext(
      values.name.trim(),
      values.phone.trim(),
      values.zip.trim(),
      values.old_vin?.trim(),
      values.old_plate?.trim(),
    );
  };

  return (
    <Card style={{ maxWidth: 480, margin: '0 auto' }}>
      <Title level={3} style={{ marginBottom: 2 }}>Your Information</Title>
      <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 13 }}>
        客户基本信息
      </Paragraph>
      <Divider style={{ margin: '16px 0 20px' }} />
      <Form form={form} layout="vertical" onFinish={handleFinish} requiredMark={false}>
        <Form.Item
          name="name"
          label="Full Name / 全名"
          rules={[{ required: true, message: 'Full name is required' }]}
        >
          <Input placeholder="e.g. Li Hua" size="large" autoComplete="name" />
        </Form.Item>
        <Form.Item
          name="phone"
          label="Phone Number / 电话号码"
          rules={[
            { required: true, message: 'Phone number is required' },
            { pattern: /^\+?[\d\s\-().]{7,}$/, message: 'Enter a valid phone number' },
          ]}
        >
          <Input placeholder="e.g. 6265550000" size="large" type="tel" autoComplete="tel" />
        </Form.Item>
        <Form.Item
          name="zip"
          label="Garaging ZIP — where the car stays at night / 车辆晚上停放的邮编"
          tooltip="ZIP where the vehicle is primarily kept (garaging ZIP affects insurance rates)"
          rules={[
            { required: true, message: 'Garaging ZIP is required' },
            { pattern: /^\d{5}(-\d{4})?$/, message: 'Enter a 5-digit ZIP code' },
          ]}
        >
          <Input placeholder="e.g. 91101" size="large" maxLength={10} />
        </Form.Item>

        {requestType === 'replace_vehicle' && (
          <>
            <Divider style={{ margin: '20px 0 16px' }} />
            <div style={{ marginBottom: 16 }}>
              <Text strong style={{ fontSize: 15 }}>Old Vehicle (Optional) / 旧车信息（可选）</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                If you know your old VIN or plate, it will help your broker identify the vehicle to remove.{' '}
                如果知道旧车 VIN 或车牌，请填写，可帮助经纪人确认需要移除的车辆。
              </Text>
            </div>
            <Form.Item name="old_vin" label="Old VIN / 旧车 VIN">
              <Input placeholder="e.g. 1HGCM82633A004352 (optional)" size="large" />
            </Form.Item>
            <Form.Item name="old_plate" label="Old License Plate / 旧车牌">
              <Input placeholder="e.g. 7ABC123 (optional)" size="large" />
            </Form.Item>
          </>
        )}

        <Form.Item style={{ marginBottom: 0 }}>
          <Button type="primary" htmlType="submit" size="large" block>
            Next — Upload Documents →
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

// ─── Screen 2: Upload ─────────────────────────────────────────────────────────

const ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/heic', 'image/heif'];
const ALLOWED_EXT = ['.pdf', '.jpg', '.jpeg', '.png', '.heic'];
const BLOCKED_EXT = ['.mp4', '.zip', '.exe', '.mov', '.avi'];

function UploadStep({
  customerName,
  requestType,
  onExtract,
  onBack,
}: {
  customerName: string;
  requestType: RequestType;
  onExtract: (files: File[]) => void;
  onBack: () => void;
}) {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [messageApi, contextHolder] = message.useMessage();

  const beforeUpload = (file: File) => {
    const name = file.name.toLowerCase();
    const ext = '.' + name.split('.').pop();
    if (BLOCKED_EXT.includes(ext)) {
      messageApi.error(`${file.name}: file type not allowed (${ext})`);
      return Upload.LIST_IGNORE;
    }
    if (!ALLOWED_EXT.includes(ext) && !ALLOWED_TYPES.includes(file.type)) {
      messageApi.error(`${file.name}: please use a supported photo or document format (PDF, JPG, PNG, or HEIC).`);
      return Upload.LIST_IGNORE;
    }
    if (fileList.length >= 10) {
      messageApi.warning('Maximum 10 files allowed.');
      return Upload.LIST_IGNORE;
    }
    return false;
  };

  const handleChange = ({ fileList: fl }: { fileList: UploadFile[] }) => {
    setFileList(fl.slice(0, 10));
  };

  const handleExtract = () => {
    const nativeFiles: File[] = fileList
      .map((f) => f.originFileObj as File | undefined)
      .filter((f): f is File => f instanceof File);
    onExtract(nativeFiles);
  };

  return (
    <Card style={{ maxWidth: 560, margin: '0 auto' }}>
      {contextHolder}
      <Title level={3} style={{ marginBottom: 2 }}>
        {isPolicyReview(requestType) ? 'Upload Policy Documents' : 'Upload New Car Paperwork'}
      </Title>
      <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 13 }}>
        {isPolicyReview(requestType)
          ? `上传保单资料 — for ${customerName}`
          : `上传新车资料 — for ${customerName}`}
      </Paragraph>
      <Divider style={{ margin: '16px 0 12px' }} />

      <Paragraph type="secondary" style={{ marginBottom: 8, fontSize: 13 }}>
        Upload any of the following:
      </Paragraph>
      <ul style={{ color: 'rgba(0,0,0,0.45)', fontSize: 13, marginBottom: 20, paddingLeft: 20, lineHeight: '1.9' }}>
        {isPolicyReview(requestType) ? (
          <>
            <li>Declaration Page / 保单首页</li>
            <li>Renewal Notice / 续保通知</li>
            <li>Insurance Card / 保险卡</li>
            <li>Current Policy PDF / 当前保单 PDF</li>
            <li>Premium screenshot / 保费截图</li>
          </>
        ) : (
          <>
            <li>Purchase Agreement / 购车合同</li>
            <li>Window Sticker / 车窗贴纸</li>
            <li>Registration / 车辆登记证</li>
            <li>VIN photo / VIN 照片</li>
            <li>Insurance card / 保险卡</li>
            {requestType === 'replace_vehicle' && (
              <li>Old insurance card (optional) / 旧保险卡（可选）</li>
            )}
          </>
        )}
      </ul>

      <Dragger
        multiple
        fileList={fileList}
        beforeUpload={beforeUpload}
        onChange={handleChange}
        accept=".pdf,.jpg,.jpeg,.png,.heic"
        style={{ marginBottom: 16 }}
      >
        <p className="ant-upload-drag-icon">
          <CloudUploadOutlined />
        </p>
        <p className="ant-upload-text">Click or drag files here / 点击或拖拽文件</p>
        <p className="ant-upload-hint">PDF · JPG · PNG · HEIC &nbsp;|&nbsp; Up to 10 files</p>
      </Dragger>

      <Paragraph type="secondary" style={{ marginBottom: 16, fontSize: 12, textAlign: 'center', lineHeight: 1.7 }}>
        Files are used only to help your broker review this request.
        <br />
        文件仅用于帮助您的保险经纪人处理本次申请。
      </Paragraph>

      {fileList.length === 0 && (
        <Alert
          style={{ marginBottom: 16 }}
          type="info"
          showIcon
          message="Add at least one document to continue."
        />
      )}

      {fileList.length > 0 && (
        <Alert
          style={{ marginBottom: 16 }}
          type="success"
          showIcon
          message={`${fileList.length} file${fileList.length !== 1 ? 's' : ''} ready`}
        />
      )}

      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Button size="large" onClick={onBack}>← Back</Button>
        <Button
          type="primary"
          size="large"
          icon={<FileTextOutlined />}
          onClick={handleExtract}
          disabled={fileList.length === 0}
        >
          Continue →
        </Button>
      </Space>
    </Card>
  );
}

// ─── Screen 3: Extracting ─────────────────────────────────────────────────────

const LOADING_STEPS_ADD_CAR = [
  { label: 'Upload Complete', sublabel: '文件上传完成' },
  { label: 'Reading Documents', sublabel: '正在读取文件' },
  { label: 'Extracting Vehicle Data', sublabel: '提取车辆信息' },
  { label: 'Preparing your submission', sublabel: '正在准备您的申请' },
];

const LOADING_STEPS_POLICY_REVIEW = [
  { label: 'Upload Complete', sublabel: '文件上传完成' },
  { label: 'Reading Documents', sublabel: '正在读取文件' },
  { label: 'Extracting Policy Snapshot', sublabel: '提取保单信息' },
  { label: 'Preparing your submission', sublabel: '正在准备您的申请' },
];

const STEP_DELAYS_MS = [0, 2000, 8000, 18000];

function ExtractingStep({ requestType }: { requestType: RequestType }) {
  const [activeStep, setActiveStep] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const loadingSteps = isPolicyReview(requestType) ? LOADING_STEPS_POLICY_REVIEW : LOADING_STEPS_ADD_CAR;

  useEffect(() => {
    STEP_DELAYS_MS.forEach((delay, i) => {
      const t = setTimeout(() => setActiveStep(i), delay);
      timersRef.current.push(t);
    });
    return () => timersRef.current.forEach(clearTimeout);
  }, []);

  return (
    <Card style={{ maxWidth: 460, margin: '0 auto', padding: '8px 0' }}>
      <div style={{ textAlign: 'center', paddingBottom: 28, paddingTop: 12 }}>
        <Title level={3} style={{ marginBottom: 4 }}>Reading your documents…</Title>
        <Text type="secondary" style={{ fontSize: 13 }}>正在读取您的文件 · This usually takes 10–30 seconds</Text>
      </div>

      <div style={{ padding: '0 16px 8px' }}>
        {loadingSteps.map((s, i) => {
          const isDone = i < activeStep;
          const isActive = i === activeStep;
          const isPending = i > activeStep;

          let icon: React.ReactNode;
          let titleColor: string;

          if (isDone) {
            icon = <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />;
            titleColor = '#52c41a';
          } else if (isActive) {
            icon = <LoadingOutlined style={{ color: '#1677ff', fontSize: 18 }} spin />;
            titleColor = '#1677ff';
          } else {
            icon = (
              <div style={{
                width: 18, height: 18, borderRadius: '50%',
                border: '2px solid rgba(0,0,0,0.15)',
                display: 'inline-block',
              }} />
            );
            titleColor = 'rgba(0,0,0,0.25)';
          }

          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 12px',
                borderRadius: 8,
                background: isActive ? '#f0f5ff' : 'transparent',
                marginBottom: 4,
                transition: 'background 0.3s',
              }}
            >
              <div style={{ flexShrink: 0, width: 22, textAlign: 'center' }}>{icon}</div>
              <div>
                <Text
                  strong={isActive || isDone}
                  style={{ color: titleColor, fontSize: 14, display: 'block' }}
                >
                  {s.label}
                </Text>
                {!isPending && (
                  <Text type="secondary" style={{ fontSize: 11 }}>{s.sublabel}</Text>
                )}
              </div>
              {isDone && (
                <Tag color="success" style={{ marginLeft: 'auto', fontSize: 11 }}>Done</Tag>
              )}
              {isActive && (
                <Tag color="processing" style={{ marginLeft: 'auto', fontSize: 11 }}>In progress</Tag>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// ─── Broker Ready Banner ──────────────────────────────────────────────────────

function BrokerReadyBanner({ status, missingCount }: { status: ReadinessStatus; missingCount: number }) {
  if (status === 'ready') {
    return (
      <div style={{
        background: '#f6ffed', border: '2px solid #95de64', borderRadius: 10,
        padding: '14px 20px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24, flexShrink: 0 }} />
        <div>
          <Text strong style={{ fontSize: 17, color: '#237804', letterSpacing: 0.3 }}>READY FOR BROKER</Text>
          <div><Text type="secondary" style={{ fontSize: 12 }}>All critical fields complete — ready to quote / 所有关键字段齐全</Text></div>
        </div>
      </div>
    );
  }
  if (status === 'broker_review') {
    return (
      <div style={{
        background: '#fff7e6', border: '2px solid #ffd591', borderRadius: 10,
        padding: '14px 20px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <WarningOutlined style={{ color: '#fa8c16', fontSize: 24, flexShrink: 0 }} />
        <div>
          <Text strong style={{ fontSize: 17, color: '#ad4e00', letterSpacing: 0.3 }}>BROKER REVIEW REQUIRED</Text>
          <div><Text type="secondary" style={{ fontSize: 12 }}>VIN conflict or data warning — verify before quoting / 数据存在警告，请核实</Text></div>
        </div>
      </div>
    );
  }
  return (
    <div style={{
      background: '#fff1f0', border: '2px solid #ffa39e', borderRadius: 10,
      padding: '14px 20px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <CloseCircleOutlined style={{ color: '#cf1322', fontSize: 24, flexShrink: 0 }} />
      <div>
        <Text strong style={{ fontSize: 17, color: '#820014', letterSpacing: 0.3 }}>NEEDS CUSTOMER INFO</Text>
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {missingCount} required field{missingCount !== 1 ? 's' : ''} missing — follow-up message below / 需要客户补充资料
          </Text>
        </div>
      </div>
    </div>
  );
}

// ─── Section Header ───────────────────────────────────────────────────────────

function SectionHeader({ title, icon }: { title: string; icon: ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, marginTop: 4, paddingBottom: 4, borderBottom: '2px solid #f0f0f0' }}>
      <span style={{ color: 'rgba(0,0,0,0.35)', fontSize: 13 }}>{icon}</span>
      <Text style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, color: 'rgba(0,0,0,0.40)', fontWeight: 600 }}>
        {title}
      </Text>
    </div>
  );
}

// ─── Readiness Field ──────────────────────────────────────────────────────────

type ReadinessFieldProps = {
  label: string;
  value?: string | null;
  status: FieldStatus;
  source?: string | null;
  note?: string;
  mono?: boolean;
  badge?: ReactNode;
};

function ReadinessField({ label, value, status, source, note, mono, badge }: ReadinessFieldProps) {
  const icon =
    status === 'complete'
      ? <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 15 }} />
      : status === 'needs_confirmation'
      ? <WarningOutlined style={{ color: '#faad14', fontSize: 15 }} />
      : <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 15 }} />;

  return (
    <div style={{ display: 'flex', gap: 10, padding: '8px 0', borderBottom: '1px solid #f5f5f5', alignItems: 'flex-start' }}>
      <div style={{ paddingTop: 3, flexShrink: 0, width: 18 }}>{icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.6, display: 'block', lineHeight: '1.4' }}>
          {label}
        </Text>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {value
            ? <Text strong style={{ fontSize: 14, fontFamily: mono ? 'monospace' : undefined, letterSpacing: mono ? 1 : undefined }}>{value}</Text>
            : <Text type="secondary" style={{ fontSize: 13, fontStyle: 'italic' }}>—</Text>
          }
          {badge}
        </div>
        {source && (
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
            from: {source}
          </Text>
        )}
        {note && (
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 2 }}>
            {note}
          </Text>
        )}
      </div>
    </div>
  );
}

// ─── Auto Follow-Up Message ───────────────────────────────────────────────────

function AutoFollowUpMessage({ missingKeys, uploadLink }: { missingKeys: string[]; uploadLink?: string }) {
  const [messageApi, contextHolder] = message.useMessage();
  const [copied, setCopied] = useState(false);

  const followUpText = buildFollowUpMessage(missingKeys, uploadLink);
  if (!followUpText) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(followUpText);
      setCopied(true);
      messageApi.success('Follow-up message copied / 跟进信息已复制');
      setTimeout(() => setCopied(false), 3000);
    } catch {
      messageApi.error('Could not copy — please select and copy manually');
    }
  };

  return (
    <Card size="small" style={{ marginTop: 12, borderColor: '#d9d9d9' }}>
      {contextHolder}
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap' as const }}>
        <Space>
          <Text strong>Auto Follow-Up / 自动跟进信息</Text>
          <Tag color="orange">Broker reviews before sending</Tag>
        </Space>
        <Button
          size="small"
          icon={<CopyOutlined />}
          onClick={handleCopy}
          type={copied ? 'primary' : 'default'}
        >
          {copied ? '✓ Copied' : 'Copy Message / 复制信息'}
        </Button>
      </Space>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
        Do not send automatically — review and edit before sharing with customer.
      </Text>
      <div style={{
        background: '#fafafa',
        border: '1px solid #e8e8e8',
        borderRadius: 6,
        padding: '14px 18px',
        fontSize: 14,
        lineHeight: 1.9,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {followUpText}
      </div>
    </Card>
  );
}

// ─── Policy Review Follow-Up (Chinese, from backend) ─────────────────────────

function PolicyReviewFollowUpMessage({ messageText }: { messageText: string }) {
  const [messageApi, contextHolder] = message.useMessage();
  const [copied, setCopied] = useState(false);

  if (!messageText.trim()) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(messageText);
      setCopied(true);
      messageApi.success('Follow-up message copied / 跟进信息已复制');
      setTimeout(() => setCopied(false), 3000);
    } catch {
      messageApi.error('Could not copy — please select and copy manually');
    }
  };

  return (
    <Card size="small" style={{ marginBottom: 16, borderColor: '#d9d9d9' }}>
      {contextHolder}
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap' as const }}>
        <Space>
          <Text strong>Chinese Follow-Up / 中文跟进消息</Text>
          <Tag color="orange">Broker reviews before sending</Tag>
        </Space>
        <Button size="small" icon={<CopyOutlined />} onClick={handleCopy} type={copied ? 'primary' : 'default'}>
          {copied ? '✓ Copied' : 'Copy Message / 复制信息'}
        </Button>
      </Space>
      <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 8 }}>
        Broker reviews before sending. / 经纪人发送前请先确认。
      </Text>
      <div style={{
        background: '#fafafa', border: '1px solid #e8e8e8', borderRadius: 6,
        padding: '14px 18px', fontSize: 14, lineHeight: 1.9, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {messageText}
      </div>
    </Card>
  );
}

// ─── Policy Opportunity Report (Policy Review final screen) ───────────────────

function PolicySnapshotRow({
  label,
  value,
  icon,
}: {
  label: string;
  value?: string;
  icon: ReactNode;
}) {
  return (
    <div style={{
      display: 'flex', gap: 12, padding: '10px 0',
      borderBottom: '1px solid #f5f5f5', alignItems: 'flex-start',
    }}>
      <span style={{ color: 'rgba(0,0,0,0.35)', marginTop: 3, flexShrink: 0, fontSize: 15 }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 2 }}>{label}</Text>
        {value
          ? <Text strong style={{ fontSize: 14 }}>{value}</Text>
          : <Text type="secondary" style={{ fontSize: 13, fontStyle: 'italic' }}>Not found yet / 暂未找到</Text>
        }
      </div>
    </div>
  );
}

function PolicyVehicleSnapshotBlock({
  lines,
  icon,
}: {
  lines: PolicyVehicleSnapshotLine[];
  icon: ReactNode;
}) {
  const label = lines.length > 1 ? 'Vehicles / 车辆' : 'Vehicle / 车辆';
  return (
    <div style={{
      display: 'flex', gap: 12, padding: '10px 0',
      borderBottom: '1px solid #f5f5f5', alignItems: 'flex-start',
    }}>
      <span style={{ color: 'rgba(0,0,0,0.35)', marginTop: 3, flexShrink: 0, fontSize: 15 }}>{icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 2 }}>{label}</Text>
        {lines.length === 0 ? (
          <Text type="secondary" style={{ fontSize: 13, fontStyle: 'italic' }}>Not found yet / 暂未找到</Text>
        ) : (
          <Space direction="vertical" size={6} style={{ width: '100%' }}>
            {lines.map((line, i) => (
              <div key={i}>
                <Text strong style={{ fontSize: 14, display: 'block' }}>{line.primary}</Text>
                {line.secondary && (
                  <Text type="secondary" style={{ fontSize: 13, display: 'block' }}>{line.secondary}</Text>
                )}
              </div>
            ))}
          </Space>
        )}
      </div>
    </div>
  );
}

function PolicyOpportunityReportStep({
  response,
  customerName,
  garagingZip,
  submittedAt,
  onStartOver,
  onGoToUpload,
}: {
  response: PacketResponse;
  customerName: string;
  garagingZip: string;
  submittedAt: string;
  onStartOver: () => void;
  onGoToUpload: () => void;
}) {
  const [messageApi, contextHolder] = message.useMessage();
  const { packet, case_id, document_guidance } = response;

  const get = (key: string) => packet[key]?.value || '';
  const displayName = get('customer_name') || customerName || '';
  const displayPhone = get('phone') || '';
  const displayZip = get('garaging_zip') || garagingZip || '';
  const vehicleSnapshotLines = buildPolicyVehicleSnapshotLines(response, packet);
  const premiumDisplay = get('premium_amount')
    ? `${get('premium_amount')}${get('premium_period') ? ` / ${get('premium_period')}` : ''}`
    : '';
  const policyTerm = formatPolicyTerm(get('policy_term_start'), get('policy_term_end'));

  const vinValue = get('vin');
  const vinValidation = vinValue ? validateVin(vinValue) : null;
  const vinStatus: VinStatus = !vinValue ? 'missing' : vinValidation?.valid ? 'valid' : 'warning';
  const readinessStatus = resolveReadinessStatus(response, packet, vinStatus, [], document_guidance);

  const handleCopyReference = async () => {
    if (!case_id) return;
    try {
      await navigator.clipboard.writeText(case_id);
      messageApi.success('Reference copied / 参考编号已复制');
    } catch {
      messageApi.error('Could not copy — please select and copy manually / 无法复制，请手动选择复制');
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      {contextHolder}

      {/* Customer confirmation header — ADR-003; no broker tools on this screen */}
      <Card
        style={{
          marginBottom: 16,
          borderRadius: 14,
          border: readinessStatus === 'needs_info' ? '2px solid #ffd591' : '2px solid #b7eb8f',
          background: readinessStatus === 'needs_info' ? '#fffbe6' : 'linear-gradient(180deg, #f6ffed 0%, #ffffff 100%)',
        }}
        bodyStyle={{ padding: '28px 24px', textAlign: 'center' }}
      >
        <SendOutlined style={{ color: readinessStatus === 'needs_info' ? '#fa8c16' : '#52c41a', fontSize: 40, marginBottom: 12 }} />
        <Title level={3} style={{ margin: 0, marginBottom: 4, color: '#237804' }}>
          {readinessStatus === 'needs_info' ? 'Request received' : 'Submitted to your broker office'}
        </Title>
        <Title level={4} style={{ margin: 0, marginBottom: 14, color: '#389e0d', fontWeight: 400 }}>
          {readinessStatus === 'needs_info' ? '已收到 · 需补充资料' : '已提交至陈奎保险办公室'}
        </Title>
        <Paragraph style={{ margin: 0, fontSize: 14, color: 'rgba(0,0,0,0.55)', lineHeight: 1.8 }}>
          Your broker will review the details and contact you to confirm next steps.
          <br />
          您的经纪人将审核资料并与您确认后续步骤。
        </Paragraph>
      </Card>

      {/* Reference # */}
      {case_id && (
        <div style={{
          marginBottom: 16,
          padding: '16px 20px',
          background: '#fff',
          border: '1.5px solid #d9d9d9',
          borderRadius: 12,
          textAlign: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            Reference # / 参考编号
          </Text>
          <Space align="center" size={8}>
            <Text strong style={{ fontSize: 20, fontFamily: 'monospace', letterSpacing: 0.8 }}>
              {case_id}
            </Text>
            <Button type="default" size="small" icon={<CopyOutlined />} onClick={handleCopyReference}>
              Copy
            </Button>
          </Space>
        </div>
      )}

      {/* Current Policy Snapshot */}
      <Card style={{ marginBottom: 16 }} title={
        <Space>
          <FileTextOutlined style={{ color: '#1677ff' }} />
          <span>Current Policy Snapshot / 当前保单摘要</span>
        </Space>
      }>
        <PolicySnapshotRow
          label="Carrier / 保险公司"
          value={get('current_carrier') || undefined}
          icon={<FileTextOutlined />}
        />
        <PolicySnapshotRow
          label="Current Premium / 当前保费"
          value={premiumDisplay || undefined}
          icon={<DollarOutlined />}
        />
        <PolicySnapshotRow
          label="Policy Term / 保单期限"
          value={policyTerm || undefined}
          icon={<CalendarOutlined />}
        />
        <PolicyVehicleSnapshotBlock
          lines={vehicleSnapshotLines}
          icon={<CarOutlined />}
        />
        <PolicySnapshotRow
          label="Garaging ZIP / 停放邮编"
          value={displayZip || undefined}
          icon={<InfoCircleOutlined />}
        />
        <PolicySnapshotRow
          label="Customer / 客户"
          value={displayName ? `${displayName}${displayPhone ? ` · ${displayPhone}` : ''}` : undefined}
          icon={<UserOutlined />}
        />
        <div style={{
          marginTop: 12, paddingTop: 10, borderTop: '1px solid #f0f0f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8,
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            <CalendarOutlined style={{ marginRight: 5 }} />
            {submittedAt}
          </Text>
          {readinessStatus === 'ready' && (
            <Tag color="success" icon={<CheckCircleOutlined />}>Ready for review / 可审核</Tag>
          )}
          {readinessStatus === 'needs_info' && (
            <Tag color="warning" icon={<ExclamationCircleOutlined />}>More info needed / 需补充资料</Tag>
          )}
          {readinessStatus === 'broker_review' && (
            <Tag color="processing" icon={<InfoCircleOutlined />}>Broker review / 经纪人核实</Tag>
          )}
        </div>
      </Card>

      {/* Document guidance */}
      {document_guidance && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="We couldn't find complete policy information / 未找到完整保单信息"
          description={<Text style={{ fontSize: 13, whiteSpace: 'pre-line' }}>{document_guidance}</Text>}
        />
      )}

      {/* ADR-003 disclaimer */}
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="This does not mean your policy has already changed."
        description={
          <Text style={{ fontSize: 13 }}>
            这不代表保险已经变更；请等待经纪人确认。
            <br />
            Your broker will confirm coverage, price, and effective date before any change takes effect.
          </Text>
        }
      />

      {/* Actions — customer only; broker tools live in office inbox */}
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {readinessStatus === 'needs_info' && (
          <Button
            type="primary"
            size="large"
            block
            icon={<CloudUploadOutlined />}
            onClick={onGoToUpload}
            style={{ height: 52, fontSize: 16, background: '#fa8c16', borderColor: '#fa8c16' }}
          >
            Upload Better Documents / 上传更合适的文件
          </Button>
        )}
        <Button
          size="large"
          block
          icon={<ReloadOutlined />}
          onClick={onStartOver}
          style={{ height: 52, fontSize: 16 }}
        >
          Start another request / 提交新申请
        </Button>
      </Space>
    </div>
  );
}

// ─── Screen 4: Sent to Broker (customer-facing completion) ────────────────────
// ADR-003 language contract:
//   ✅ "Sent to your broker" / "Broker will confirm"
//   ❌ Never "insurance updated" / "policy changed" / "vehicle is now covered"
// State-gate UX (P16 Stage-Gate fix):
//   READY        → Green  + SendOutlined        — "Submitted to your broker"
//   BROKER_REVIEW → Blue   + InfoCircleOutlined  — "Sent for broker review"
//   NEED_INFO    → Orange + ExclamationCircle   — "Request received — additional info needed"
//                  NEED_INFO must NOT say "sent to broker" or "broker received"

function SentToBrokerStep({
  response,
  customerName,
  garagingZip,
  requestType,
  submittedAt,
  onStartOver,
  onGoToUpload,
}: {
  response: PacketResponse;
  customerName: string;
  garagingZip: string;
  requestType: RequestType;
  submittedAt: string;
  onStartOver: () => void;
  onGoToUpload: () => void;
}) {
  const [messageApi, contextHolder] = message.useMessage();
  const { packet, warnings, case_id, document_guidance } = response;

  const handleCopyReference = async () => {
    if (!case_id) return;
    try {
      await navigator.clipboard.writeText(case_id);
      messageApi.success('Reference copied / 参考编号已复制');
    } catch {
      messageApi.error('Could not copy — please select and copy manually / 无法复制，请手动选择复制');
    }
  };
  const get = (key: string) => packet[key]?.value || '';

  const displayName = get('customer_name') || customerName || '';
  const displayPhone = get('phone') || '';
  const vinValue = get('vin');
  const year = get('year');
  const make = get('make');
  const model = get('model');
  const policyFirstVehicle = response.vehicles?.[0];
  const vehicleLabel = isPolicyReview(requestType)
    ? [policyFirstVehicle?.year, policyFirstVehicle?.make, policyFirstVehicle?.model].filter(Boolean).join(' ')
    : [year, make, model].filter(Boolean).join(' ');
  const displayZip = get('garaging_zip') || garagingZip || '';

  const vinValidation = vinValue ? validateVin(vinValue) : null;
  const vinStatus: VinStatus = !vinValue ? 'missing' : vinValidation?.valid ? 'valid' : 'warning';
  const readinessStatus = resolveReadinessStatus(response, packet, vinStatus, warnings, document_guidance);

  const criticalMissing: string[] = [];
  if (isPolicyReview(requestType)) {
    if (!get('current_carrier')) criticalMissing.push('Current carrier / 保险公司');
    if (!get('premium_amount')) criticalMissing.push('Premium amount / 保费');
    if (!(response.vehicles?.length)) criticalMissing.push('Vehicle information / 车辆信息');
  } else {
    if (!vinValue) criticalMissing.push('VIN number');
    if (!year || !make || !model) criticalMissing.push('Vehicle Year / Make / Model');
    if (!displayZip) criticalMissing.push('Garaging ZIP');
  }

  const requestLabel = requestType === 'policy_review'
    ? 'Policy review request / 保单检查申请'
    : requestType === 'replace_vehicle'
    ? 'Vehicle replacement request / 换车申请'
    : 'New car addition request / 加新车申请';

  const rowStyle: React.CSSProperties = {
    display: 'flex', gap: 12, padding: '8px 0',
    borderBottom: '1px solid #f0f0f0', alignItems: 'flex-start',
  };
  const iconStyle: React.CSSProperties = { color: '#52c41a', marginTop: 3, flexShrink: 0, fontSize: 15 };

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>
      {contextHolder}

      {/* ── State-specific header — Stage-Gate UX (P16 fix) ── */}
      {readinessStatus === 'ready' && (
        <div style={{
          background: '#f6ffed', border: '2px solid #95de64', borderRadius: 14,
          padding: '32px 28px 28px', marginBottom: 20, textAlign: 'center',
        }}>
          <SendOutlined style={{ color: '#52c41a', fontSize: 44, marginBottom: 14 }} />
          <Title level={3} style={{ margin: 0, marginBottom: 4, color: '#237804' }}>
            Submitted to your broker
          </Title>
          <Title level={4} style={{ margin: 0, marginBottom: 14, color: '#389e0d', fontWeight: 400 }}>
            您的申请已发送给您的保险经纪人
          </Title>
          <Paragraph style={{ margin: 0, fontSize: 14, color: 'rgba(0,0,0,0.55)', lineHeight: 1.8 }}>
            Your broker will review the details and confirm next steps with you.<br />
            您的经纪人将审核您的信息，并与您确认后续步骤。
            {requestType === 'replace_vehicle' && (
              <>
                <br /><br />
                Your broker will review your new vehicle information and confirm any vehicle replacement updates.<br />
                您的经纪人将审核您的新车信息，并确认换车保险更新。
              </>
            )}
          </Paragraph>
        </div>
      )}

      {readinessStatus === 'broker_review' && (
        <div style={{
          background: '#e6f4ff', border: '2px solid #91caff', borderRadius: 14,
          padding: '32px 28px 28px', marginBottom: 20, textAlign: 'center',
        }}>
          <InfoCircleOutlined style={{ color: '#1677ff', fontSize: 44, marginBottom: 14 }} />
          <Title level={3} style={{ margin: 0, marginBottom: 4, color: '#0958d9' }}>
            Sent for broker review
          </Title>
          <Title level={4} style={{ margin: 0, marginBottom: 14, color: '#1677ff', fontWeight: 400 }}>
            您的申请已发送，经纪人需要核实部分信息
          </Title>
          <Paragraph style={{ margin: 0, fontSize: 14, color: 'rgba(0,0,0,0.55)', lineHeight: 1.8 }}>
            Your broker needs to verify some details before proceeding.<br />
            经纪人需要核实部分信息后才能继续处理。
          </Paragraph>
        </div>
      )}

      {readinessStatus === 'needs_info' && (
        <div style={{
          background: '#fff7e6', border: '2px solid #ffd591', borderRadius: 14,
          padding: '32px 28px 28px', marginBottom: 20, textAlign: 'center',
        }}>
          <ExclamationCircleOutlined style={{ color: '#fa8c16', fontSize: 44, marginBottom: 14 }} />
          <Title level={3} style={{ margin: 0, marginBottom: 4, color: '#ad4e00' }}>
            Request received — additional information needed
          </Title>
          <Title level={4} style={{ margin: 0, marginBottom: 14, color: '#d46b08', fontWeight: 400 }}>
            您的申请已收到，但还需要补充资料
          </Title>
          <Paragraph style={{ margin: 0, fontSize: 14, color: 'rgba(0,0,0,0.55)', lineHeight: 1.8 }}>
            We received your request, but we could not find all required vehicle information.<br />
            Please provide the missing information so your broker can process your request.<br /><br />
            我们已收到您的申请，但尚未找到完整车辆资料。<br />
            请补充缺失信息，以便经纪人继续处理。
          </Paragraph>
        </div>
      )}

      {/* ── Reference number — prominent for customer follow-up ── */}
      {case_id && (
        <div style={{
          marginBottom: 20,
          padding: '18px 20px',
          background: '#fff',
          border: '1.5px solid #d9d9d9',
          borderRadius: 12,
          textAlign: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6, letterSpacing: 0.2 }}>
            Reference # / 参考编号
          </Text>
          <Space align="center" size={8}>
            <Text strong style={{ fontSize: 20, fontFamily: 'monospace', letterSpacing: 0.8, color: '#262626' }}>
              {case_id}
            </Text>
            <Button
              type="default"
              size="small"
              icon={<CopyOutlined />}
              onClick={handleCopyReference}
              aria-label="Copy reference number"
            >
              Copy
            </Button>
          </Space>
          <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 8 }}>
            Save this number if you contact your broker about this request.
            <br />
            如需联系经纪人查询进度，请保存此编号。
          </Text>
        </div>
      )}

      {/* ── What was submitted ── */}
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
          <Title level={5} style={{ margin: 0 }}>What you submitted / 您提交的信息</Title>
          <Tag color="default" style={{ fontSize: 12 }}>{requestLabel}</Tag>
        </Space>

        {displayName && (
          <div style={rowStyle}>
            <UserOutlined style={iconStyle} />
            <div>
              <Text strong>{displayName}</Text>
              {displayPhone && (
                <Text type="secondary" style={{ marginLeft: 10, fontSize: 13 }}>{displayPhone}</Text>
              )}
            </div>
          </div>
        )}

        {isPolicyReview(requestType) ? (
          <>
            {get('current_carrier') && (
              <div style={rowStyle}>
                <FileTextOutlined style={iconStyle} />
                <div>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Carrier / 保险公司</Text>
                  <Text strong>{get('current_carrier')}</Text>
                </div>
              </div>
            )}
            {get('premium_amount') && (
              <div style={rowStyle}>
                <DollarOutlined style={iconStyle} />
                <div>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Premium / 保费</Text>
                  <Text strong>{get('premium_amount')}{get('premium_period') ? ` / ${get('premium_period')}` : ''}</Text>
                </div>
              </div>
            )}
            {vehicleLabel && (
              <div style={rowStyle}>
                <CarOutlined style={iconStyle} />
                <Text strong>{vehicleLabel}</Text>
              </div>
            )}
          </>
        ) : (
          <>
            {vehicleLabel && (
              <div style={rowStyle}>
                <CarOutlined style={iconStyle} />
                <Text strong>{vehicleLabel}</Text>
              </div>
            )}

            {vinValue && (
              <div style={rowStyle}>
                <FileTextOutlined style={iconStyle} />
                <div>
                  <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>VIN</Text>
                  <Text code style={{ fontSize: 13, letterSpacing: 1 }}>{vinValue}</Text>
                </div>
              </div>
            )}
          </>
        )}

        {!isPolicyReview(requestType) && displayZip && (
          <div style={{ ...rowStyle, borderBottom: 'none' }}>
            <InfoCircleOutlined style={iconStyle} />
            <div>
              <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Garaging ZIP / 停放邮编</Text>
              <Text strong>{displayZip}</Text>
            </div>
          </div>
        )}

        {isPolicyReview(requestType) && displayZip && (
          <div style={{ ...rowStyle, borderBottom: 'none' }}>
            <InfoCircleOutlined style={iconStyle} />
            <div>
              <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>Garaging ZIP / 停放邮编</Text>
              <Text strong>{displayZip}</Text>
            </div>
          </div>
        )}

        {/* Timestamp + status badge */}
        <div style={{
          marginTop: 14, paddingTop: 12, borderTop: '1px solid #f0f0f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          flexWrap: 'wrap', gap: 8,
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            <CalendarOutlined style={{ marginRight: 5 }} />
            {submittedAt}
          </Text>
          {readinessStatus === 'ready' && (
            <Tag color="success" icon={<CheckCircleOutlined />}>Submitted / 已提交</Tag>
          )}
          {readinessStatus === 'needs_info' && (
            <Tag color="error" icon={<CloseCircleOutlined />}>Documents needed / 需补充资料</Tag>
          )}
          {readinessStatus === 'broker_review' && (
            <Tag color="warning" icon={<WarningOutlined />}>Under review / 审核中</Tag>
          )}
        </div>
      </Card>

      {/* ── Document Relevance Gate alert: uploaded docs had no vehicle info ── */}
      {document_guidance && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={
            <span>
              <strong>We couldn't find vehicle information</strong>
              <span style={{ marginLeft: 8, color: 'rgba(0,0,0,0.55)', fontWeight: 400 }}>
                未找到车辆信息
              </span>
            </span>
          }
          description={
            <Text style={{ fontSize: 13, whiteSpace: 'pre-line' }}>
              {document_guidance}
            </Text>
          }
        />
      )}

      {/* ── NEED_INFO: Missing information display (no "sent to broker" language) ── */}
      {readinessStatus === 'needs_info' && (criticalMissing.length > 0 || document_guidance) && (
        <Card
          style={{ marginBottom: 16, borderColor: '#ffd591', background: '#fffbe6' }}
          size="small"
        >
          <Space align="start" size={10}>
            <ExclamationCircleOutlined style={{ color: '#fa8c16', fontSize: 16, marginTop: 2, flexShrink: 0 }} />
            <div>
              <Text strong style={{ fontSize: 14, color: '#ad4e00', display: 'block', marginBottom: 6 }}>
                Missing information / 缺失信息
              </Text>
              {criticalMissing.length > 0 && (
                <ul style={{ margin: '0 0 4px', paddingLeft: 18, fontSize: 13, lineHeight: 1.9 }}>
                  {criticalMissing.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              )}
              <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                请上传包含以上信息的文件（例如：购车合同、车辆登记证、VIN 照片）。
              </Text>
            </div>
          </Space>
        </Card>
      )}

      {/* ── ADR-003 disclaimer: never imply policy has changed ── */}
      <Alert
        type="info" showIcon
        style={{ marginBottom: 20 }}
        message="This does not mean your policy has already changed."
        description={
          <Text style={{ fontSize: 13 }}>
            这不代表保险已经变更；请等待经纪人确认。<br />
            Your broker will confirm coverage, price, and effective date before any change takes effect.
          </Text>
        }
      />

      {/* ── Response time expectation ── */}
      <div style={{ textAlign: 'center', marginBottom: 20, padding: '12px 16px', background: '#fafafa', borderRadius: 8, border: '1px solid #f0f0f0' }}>
        <Text style={{ fontSize: 14, color: 'rgba(0,0,0,0.65)' }}>
          Most requests are reviewed within 2–4 business hours.
        </Text>
        <br />
        <Text style={{ fontSize: 14, color: 'rgba(0,0,0,0.65)' }}>
          大多数申请会在 2–4 个工作小时内获得回复。
        </Text>
      </div>

      {/* ── Contact note ── */}
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <Text type="secondary" style={{ fontSize: 14 }}>
          Questions? Contact your broker directly.
        </Text>
        <br />
        <Text type="secondary" style={{ fontSize: 14 }}>
          有问题请直接联系您的经纪人。
        </Text>
      </div>

      {/* ── Actions ── */}
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {readinessStatus === 'needs_info' && (
          <Button
            type="primary"
            size="large"
            block
            icon={<CloudUploadOutlined />}
            onClick={onGoToUpload}
            style={{ height: 52, fontSize: 16, background: '#fa8c16', borderColor: '#fa8c16' }}
          >
            Upload Better Documents / 上传更合适的文件
          </Button>
        )}
        <Button
          type={readinessStatus === 'needs_info' ? 'default' : 'primary'}
          size="large"
          block
          icon={<ReloadOutlined />}
          onClick={onStartOver}
          style={{ height: 52, fontSize: 16 }}
        >
          Start another request / 提交新申请
        </Button>
      </Space>
    </div>
  );
}

// REMOVED_VIEW_BROKER_PACKET_SENT

// ─── Screen 5: Policy Review Packet (broker-facing) ───────────────────────────

function PolicyReviewPacketStep({
  response,
  customerName,
  garagingZip,
  onStartOver,
}: {
  response: PacketResponse;
  customerName: string;
  garagingZip: string;
  onStartOver: () => void;
}) {
  const [messageApi, contextHolder] = message.useMessage();
  const { packet, warnings, mock_mode, document_guidance, case_id, copy_text, follow_up_message_zh, opportunity_signals, broker_next_action } = response;
  const vehicles = response.vehicles ?? [];
  const drivers = response.drivers ?? [];
  const get = (key: string) => packet[key]?.value || '';
  const readinessStatus = response.readiness_status ?? 'needs_info';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(copy_text || '');
      messageApi.success('Report copied / 已复制');
    } catch {
      messageApi.error('Could not copy — please copy manually');
    }
  };

  const handleCopyPortal = async () => {
    const text = response.portal_copy_text || '';
    if (!text.trim()) {
      messageApi.warning('Portal format not available');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      messageApi.success('Portal format copied / 已复制门户格式');
    } catch {
      messageApi.error('Could not copy — please copy manually');
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      {contextHolder}
      {mock_mode && import.meta.env.DEV && (
        <Alert type="warning" showIcon closable message="Development mode: mock extraction active" style={{ marginBottom: 16 }} />
      )}
      <BrokerReadyBanner status={readinessStatus} missingCount={warnings.length} />
      <NextActionLine status={readinessStatus} requestType="policy_review" brokerNextAction={broker_next_action} />

      <Card style={{ marginBottom: 12 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }} wrap>
          <Title level={4} style={{ margin: 0 }}>Policy Review Packet / 当前保单分析资料包</Title>
          {case_id && <Text type="secondary" style={{ fontSize: 11 }}>Case #{case_id}</Text>}
        </Space>

        {document_guidance && (
          <Alert type="warning" showIcon message="Missing declaration page / 缺少保单首页" description={document_guidance} style={{ marginBottom: 16 }} />
        )}
        {warnings.length > 0 && (
          <Alert type="warning" showIcon message={`${warnings.length} extraction warning(s)`} description={
            <ul style={{ margin: 0, paddingLeft: 16 }}>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
          } style={{ marginBottom: 16 }} />
        )}

        <SectionHeader title="Customer" icon={<UserOutlined />} />
        <ReadinessField label="Name" value={get('customer_name') || customerName} status={get('customer_name') ? 'complete' : 'missing'} />
        <ReadinessField label="Phone" value={get('phone')} status={get('phone') ? 'complete' : 'missing'} />
        <ReadinessField label="Garaging ZIP" value={get('garaging_zip') || garagingZip} status={(get('garaging_zip') || garagingZip) ? 'complete' : 'missing'} />

        <Divider style={{ margin: '12px 0' }} />
        <SectionHeader title="Current Policy" icon={<FileTextOutlined />} />
        <ReadinessField label="Carrier" value={get('current_carrier')} status={get('current_carrier') ? 'complete' : 'missing'} source={packet.current_carrier?.source_file} />
        <ReadinessField label="Policy Number" value={get('policy_number')} status={get('policy_number') ? 'complete' : 'needs_confirmation'} source={packet.policy_number?.source_file} />
        <ReadinessField label="Term Start" value={get('policy_term_start')} status={get('policy_term_start') ? 'complete' : 'needs_confirmation'} source={packet.policy_term_start?.source_file} />
        <ReadinessField label="Term End" value={get('policy_term_end')} status={get('policy_term_end') ? 'complete' : 'needs_confirmation'} source={packet.policy_term_end?.source_file} />

        <Divider style={{ margin: '12px 0' }} />
        <SectionHeader title="Vehicles" icon={<CarOutlined />} />
        {vehicles.length === 0 ? (
          <Text type="secondary" style={{ fontSize: 13 }}>No vehicles extracted</Text>
        ) : vehicles.map((v, i) => (
          <ReadinessField
            key={i}
            label={`Vehicle ${i + 1}`}
            value={[v.year, v.make, v.model].filter(Boolean).join(' ') || null}
            status={v.vin || v.year ? 'complete' : 'missing'}
            source={v.source_file}
            note={v.vin ? `VIN: ${v.vin}${v.vehicle_premium ? ` · Premium: ${v.vehicle_premium}` : ''}` : undefined}
            mono={!!v.vin}
          />
        ))}

        <Divider style={{ margin: '12px 0' }} />
        <SectionHeader title="Drivers" icon={<UserOutlined />} />
        {drivers.length === 0 ? (
          <Text type="secondary" style={{ fontSize: 13 }}>No drivers extracted</Text>
        ) : drivers.map((d, i) => (
          <ReadinessField
            key={i}
            label={d.relationship || `Driver ${i + 1}`}
            value={d.name || null}
            status={d.name ? 'complete' : 'missing'}
            source={d.source_file}
            note={d.visible_violation_or_accident ? `Violation/Accident: ${d.visible_violation_or_accident}` : undefined}
          />
        ))}

        <Divider style={{ margin: '12px 0' }} />
        <SectionHeader title="Coverage" icon={<FileTextOutlined />} />
        <ReadinessField label="Bodily Injury" value={get('bodily_injury')} status={get('bodily_injury') ? 'complete' : 'missing'} source={packet.bodily_injury?.source_file} />
        <ReadinessField label="Property Damage" value={get('property_damage')} status={get('property_damage') ? 'complete' : 'missing'} source={packet.property_damage?.source_file} />
        <ReadinessField label="Uninsured Motorist" value={get('uninsured_motorist')} status={get('uninsured_motorist') ? 'complete' : 'needs_confirmation'} source={packet.uninsured_motorist?.source_file} />
        <ReadinessField label="Comprehensive Deductible" value={get('comprehensive_deductible')} status={get('comprehensive_deductible') ? 'complete' : 'needs_confirmation'} source={packet.comprehensive_deductible?.source_file} />
        <ReadinessField label="Collision Deductible" value={get('collision_deductible')} status={get('collision_deductible') ? 'complete' : 'needs_confirmation'} source={packet.collision_deductible?.source_file} />

        <Divider style={{ margin: '12px 0' }} />
        <SectionHeader title="Premium" icon={<DollarOutlined />} />
        <ReadinessField label="Premium Amount" value={get('premium_amount')} status={get('premium_amount') ? 'complete' : 'missing'} source={packet.premium_amount?.source_file} />
        <ReadinessField label="Premium Period" value={get('premium_period')} status={get('premium_period') ? 'complete' : 'needs_confirmation'} source={packet.premium_period?.source_file} />

        {opportunity_signals && opportunity_signals.length > 0 && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <SectionHeader title="Opportunity Signals" icon={<InfoCircleOutlined />} />
            {opportunity_signals.map((s) => (
              <div key={s.code} style={{ padding: '6px 0', borderBottom: '1px solid #f5f5f5' }}>
                <Tag color="blue" style={{ marginBottom: 4 }}>{s.code}</Tag>
                <Text style={{ fontSize: 13, display: 'block' }}>{s.meaning}</Text>
              </div>
            ))}
          </>
        )}

        <Divider style={{ margin: '16px 0' }} />
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          <Button type="primary" icon={<CopyOutlined />} size="large" block onClick={handleCopy} style={{ height: 52, fontSize: 16 }}>
            Copy Report / 复制报告
          </Button>
          {response.portal_copy_text?.trim() && (
            <Button icon={<CopyOutlined />} size="large" block onClick={handleCopyPortal} style={{ height: 48, fontSize: 15 }}>
              Copy Portal Format / 复制门户格式
            </Button>
          )}
        </Space>
      </Card>

      {readinessStatus === 'needs_info' && follow_up_message_zh && (
        <PolicyReviewFollowUpMessage messageText={follow_up_message_zh} />
      )}

      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Button icon={<ReloadOutlined />} onClick={onStartOver}>Start another request / 提交新申请</Button>
      </div>
    </div>
  );
}

// ─── Screen 5: Trusted Packet (broker-facing) ─────────────────────────────────
// Preserved intact. Customer lands here only via the secondary "View broker packet" link.

function PacketStep({
  response,
  customerName,
  garagingZip,
  requestType,
  oldVehicleVin,
  oldVehiclePlate,
  onStartOver,
}: {
  response: PacketResponse;
  customerName: string;
  garagingZip: string;
  requestType: RequestType;
  oldVehicleVin: string;
  oldVehiclePlate: string;
  onStartOver: () => void;
}) {
  const [messageApi, contextHolder] = message.useMessage();
  const [showDetails, setShowDetails] = useState(false);
  const { packet, warnings, sources, mock_mode, confirmation_notices, document_guidance, case_id } = response;

  const get = (key: string) => packet[key]?.value || '';

  // ── VIN ──
  const vinValue = get('vin');
  const vinSource = packet.vin?.source_file || null;
  const vinValidation = vinValue ? validateVin(vinValue) : null;

  let vinStatus: VinStatus = 'missing';
  let vinWarningReason: string | undefined;
  if (vinValue) {
    if (vinValidation?.valid) {
      vinStatus = 'valid';
    } else {
      vinStatus = 'warning';
      vinWarningReason = vinValidation?.reason;
    }
  }

  const vinFieldStatus: FieldStatus =
    vinStatus === 'valid' ? 'complete' : vinStatus === 'warning' ? 'needs_confirmation' : 'missing';

  // ── Vehicle ──
  const year = get('year');
  const make = get('make');
  const model = get('model');
  const vehicleLabel = [year, make, model].filter(Boolean).join(' ') || '';
  const vehicleSource = packet.year?.source_file || packet.make?.source_file || null;
  const vehicleAllPresent = !!(year && make && model);
  const vehicleStatus: FieldStatus = vehicleAllPresent ? 'complete' : year || make || model ? 'needs_confirmation' : 'missing';

  // ── Customer / ZIP ──
  const displayZip = get('garaging_zip') || garagingZip || '';
  const displayName = get('customer_name') || customerName || '';
  const zipStatus: FieldStatus = displayZip ? 'complete' : 'missing';

  // ── Primary Driver ──
  const pdField = packet.primary_driver;
  const pdValue = pdField?.value || '';
  const pdDefaulted = pdField?.source_file === 'default_from_customer_name';
  const pdStatus: FieldStatus = pdValue ? (pdDefaulted ? 'needs_confirmation' : 'complete') : 'missing';

  // ── Finance & Timing ──
  const effectiveDate = get('effective_date') || get('delivery_date') || '';
  const effectiveDateSource = packet.effective_date?.source_file || null;
  const effectiveStatus: FieldStatus = effectiveDate ? 'complete' : 'needs_confirmation';
  const lienholder = get('finance_or_lienholder') || '';
  const lienholderStatus: FieldStatus = lienholder ? 'complete' : 'needs_confirmation';

  // ── Readiness ──
  const readinessStatus = resolveReadinessStatus(response, packet, vinStatus, warnings, document_guidance);
  const criticalMissingCount = ['vin', 'year', 'make', 'model'].filter(k => !packet[k]?.value).length;

  // ── Follow-Up missing keys (critical only — not optional fields like effective_date) ──
  const criticalFollowUpKeys = buildCriticalFollowUpKeys(vinValue, year, make, model, displayZip);
  const showAutoFollowUp = shouldShowAutoFollowUp(readinessStatus, criticalFollowUpKeys);

  // ── Copy text ──
  const copyText = buildCopyText(packet, warnings, sources, customerName, garagingZip, requestType, oldVehicleVin, oldVehiclePlate);

  const packetTimestamp = new Date().toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(copyText);
      messageApi.success('Report copied / 已复制');
    } catch {
      messageApi.error('Could not copy — please copy manually');
    }
  };

  const handleCopyPortal = async () => {
    const text = response.portal_copy_text || '';
    if (!text.trim()) {
      messageApi.warning('Portal format not available');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      messageApi.success('Portal format copied / 已复制门户格式');
    } catch {
      messageApi.error('Could not copy — please copy manually');
    }
  };

  const uploadLink = typeof window !== 'undefined' ? `${window.location.origin}/add-car` : undefined;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      {contextHolder}

      {/* Mock mode banner — only in development */}
      {mock_mode && import.meta.env.DEV && (
        <Alert
          type="warning" showIcon closable
          message="Development mode: mock extraction active"
          description="Connect a Gemini API key to enable real document reading."
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ── Broker Ready Banner ── */}
      <BrokerReadyBanner status={readinessStatus} missingCount={criticalMissingCount} />

      <NextActionLine status={readinessStatus} requestType={requestType} />

      {/* ── Main Packet Card ── */}
      <Card style={{ marginBottom: 12 }}>

        {/* Header */}
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16, alignItems: 'flex-start' }} wrap>
          <Space align="center" size={8}>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
            <Title level={4} style={{ margin: 0 }}>Trusted Packet</Title>
          </Space>
          <Space direction="vertical" size={0} style={{ textAlign: 'right' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>{packetTimestamp}</Text>
            {case_id && (
              <Text type="secondary" style={{ fontSize: 11 }}>Case #{case_id}</Text>
            )}
          </Space>
        </Space>

        {/* Document Relevance Gate note — broker sees this as a missing-document flag */}
        {document_guidance && (
          <Alert
            type="warning" showIcon
            message="Customer uploaded a document without vehicle information / 客户上传的文件中无车辆信息"
            description={
              <Text style={{ fontSize: 13, whiteSpace: 'pre-line' }}>
                {document_guidance}
              </Text>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Extraction warnings — real broker-review conflicts only */}
        {warnings.length > 0 && (
          <Alert
            type="warning" showIcon
            message={warnings.length === 1 ? warnings[0] : `${warnings.length} extraction warnings`}
            description={warnings.length > 1
              ? <ul style={{ margin: 0, paddingLeft: 16 }}>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
              : undefined
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {/* ── DRIVER Section ── */}
        <SectionHeader title="Driver" icon={<UserOutlined />} />
        <ReadinessField
          label="Customer Name"
          value={displayName || null}
          status={displayName ? 'complete' : 'missing'}
        />
        <ReadinessField
          label="Phone / 电话"
          value={get('phone') || null}
          status={get('phone') ? 'complete' : 'missing'}
        />
        <ReadinessField
          label="Primary Driver / 主要驾驶人"
          value={pdValue || null}
          status={pdStatus}
          note={pdDefaulted ? 'Defaulted from customer name — please confirm / 默认使用客户姓名，请确认' : undefined}
        />

        <Divider style={{ margin: '12px 0' }} />

        {/* ── VEHICLE Section ── */}
        <SectionHeader title="Vehicle" icon={<CarOutlined />} />
        <ReadinessField
          label="VIN"
          value={vinValue || null}
          status={vinFieldStatus}
          source={vinSource}
          note={vinWarningReason}
          mono
          badge={<VinStatusPill status={vinStatus} />}
        />
        <ReadinessField
          label="Year / Make / Model"
          value={vehicleLabel || null}
          status={vehicleStatus}
          source={vehicleSource}
        />
        <ReadinessField
          label="Garaging ZIP / 停放邮编"
          value={displayZip || null}
          status={zipStatus}
          note={!displayZip ? 'Required — ask customer for ZIP where the car stays at night' : undefined}
        />

        <Divider style={{ margin: '12px 0' }} />

        {/* ── FINANCE & TIMING Section ── */}
        <SectionHeader title="Finance & Timing" icon={<CalendarOutlined />} />
        <ReadinessField
          label="Effective / Delivery Date"
          value={effectiveDate || null}
          status={effectiveStatus}
          source={effectiveDateSource}
          note={!effectiveDate ? 'Not found in documents — confirm with customer if needed' : undefined}
        />
        <ReadinessField
          label="Lienholder / Finance Company"
          value={lienholder || null}
          status={lienholderStatus}
          note={!lienholder ? 'Not required if vehicle is paid in full' : undefined}
        />
        {confirmation_notices && confirmation_notices.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {confirmation_notices.map((notice, i) => (
              <Text key={i} type="secondary" style={{ fontSize: 12, display: 'block', padding: '4px 0' }}>
                <InfoCircleOutlined style={{ marginRight: 4 }} />{notice}
              </Text>
            ))}
          </div>
        )}

        {/* ── VEHICLE REFERENCE (Replace Vehicle only) ── */}
        {requestType === 'replace_vehicle' && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <SectionHeader title="Vehicle Reference (Optional) / 旧车参考" icon={<SwapOutlined />} />
            <ReadinessField
              label="Old VIN / 旧车 VIN"
              value={oldVehicleVin || null}
              status={oldVehicleVin ? 'complete' : 'needs_confirmation'}
              mono={!!oldVehicleVin}
              note={!oldVehicleVin ? 'Not provided' : undefined}
            />
            <ReadinessField
              label="Old License Plate / 旧车牌"
              value={oldVehiclePlate || null}
              status={oldVehiclePlate ? 'complete' : 'needs_confirmation'}
              note={!oldVehiclePlate ? 'Not provided' : undefined}
            />
            {!oldVehicleVin && !oldVehiclePlate && (
              <Alert
                type="warning"
                showIcon
                style={{ marginTop: 8, marginBottom: 0 }}
                message="Old vehicle not identified — broker must verify existing vehicle in AMS before processing removal."
                description="经纪人需在 AMS 中确认需要移除的车辆。"
              />
            )}
          </>
        )}

        <Divider style={{ margin: '12px 0 16px' }} />

        {/* ── Copy — broker CTAs ── */}
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          <Button
            type="primary"
            icon={<CopyOutlined />}
            size="large"
            block
            onClick={handleCopy}
            style={{ height: 52, fontSize: 16 }}
          >
            Copy Report / 复制报告
          </Button>
          {response.portal_copy_text?.trim() && (
            <Button
              icon={<CopyOutlined />}
              size="large"
              block
              onClick={handleCopyPortal}
              style={{ height: 48, fontSize: 15 }}
            >
              Copy Portal Format / 复制门户格式
            </Button>
          )}
        </Space>
      </Card>

      {/* ── Auto Follow-Up Message — NEED_INFO / BROKER_REVIEW when critical info missing ── */}
      {showAutoFollowUp && (
        <AutoFollowUpMessage missingKeys={criticalFollowUpKeys} uploadLink={uploadLink} />
      )}

      {/* ── Expandable field details ── */}
      <Card size="small" style={{ marginBottom: 12, marginTop: 12 }}>
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => setShowDetails(!showDetails)}
          style={{ padding: 0, color: 'rgba(0,0,0,0.45)', height: 'auto' }}
        >
          {showDetails ? 'Hide field details' : 'Show field details (source & confidence)'}
        </Button>

        {showDetails && (
          <div style={{ marginTop: 16 }}>
            <Title level={5} style={{ marginBottom: 8 }}>Customer</Title>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              {packet.customer_name && (
                <Descriptions.Item label="Name"><DetailField field={packet.customer_name} /></Descriptions.Item>
              )}
              {packet.phone && (
                <Descriptions.Item label="Phone"><DetailField field={packet.phone} /></Descriptions.Item>
              )}
              {packet.garaging_zip && (
                <Descriptions.Item label="Garaging ZIP"><DetailField field={packet.garaging_zip} /></Descriptions.Item>
              )}
            </Descriptions>

            <Title level={5} style={{ marginBottom: 8 }}>Vehicle</Title>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              {packet.vin && <Descriptions.Item label="VIN"><DetailField field={packet.vin} /></Descriptions.Item>}
              {packet.year && <Descriptions.Item label="Year"><DetailField field={packet.year} /></Descriptions.Item>}
              {packet.make && <Descriptions.Item label="Make"><DetailField field={packet.make} /></Descriptions.Item>}
              {packet.model && <Descriptions.Item label="Model"><DetailField field={packet.model} /></Descriptions.Item>}
            </Descriptions>

            <Title level={5} style={{ marginBottom: 8 }}>Coverage Details</Title>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              {packet.primary_driver && (
                <Descriptions.Item label="Primary Driver"><DetailField field={packet.primary_driver} /></Descriptions.Item>
              )}
              {packet.effective_date && (
                <Descriptions.Item label="Effective Date"><DetailField field={packet.effective_date} /></Descriptions.Item>
              )}
              {packet.finance_or_lienholder && (
                <Descriptions.Item label="Lienholder"><DetailField field={packet.finance_or_lienholder} /></Descriptions.Item>
              )}
            </Descriptions>

            {sources.length > 0 && (
              <>
                <Title level={5} style={{ marginBottom: 8 }}>Source Files</Title>
                <Descriptions column={1} size="small" bordered>
                  {sources.map((s, i) => (
                    <Descriptions.Item key={i} label={<Text code style={{ fontSize: 11 }}>{s.file}</Text>}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{s.fields}</Text>
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </>
            )}
          </div>
        )}
      </Card>

      {/* Start over */}
      <Button block onClick={onStartOver} icon={<ReloadOutlined />} size="large">
        Start Over / 重新开始
      </Button>
    </div>
  );
}

// ─── Main Wizard ──────────────────────────────────────────────────────────────

export default function AddCarPage() {
  const [step, setStep] = useState<WizardStep>('intent');
  const [requestType, setRequestType] = useState<RequestType>('add_vehicle');
  const [submittedAt, setSubmittedAt] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [garagingZip, setGaragingZip] = useState('');
  const [oldVehicleVin, setOldVehicleVin] = useState('');
  const [oldVehiclePlate, setOldVehiclePlate] = useState('');
  const [packetResponse, setPacketResponse] = useState<PacketResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [messageApi, contextHolder] = message.useMessage();

  // Screen 0: customer selects their intent
  const handleIntentSelect = (type: RequestType) => {
    setRequestType(type);
    setStep('info');
  };

  const handleInfoNext = (name: string, ph: string, zip: string, oldVin?: string, oldPlate?: string) => {
    setCustomerName(name);
    setPhone(ph);
    setGaragingZip(zip);
    setOldVehicleVin(oldVin || '');
    setOldVehiclePlate(oldPlate || '');
    setStep('upload');
  };

  const handleExtract = async (files: File[]) => {
    setStep('extracting');
    setError(null);
    try {
      const fd = new FormData();
      fd.append('customer_name', customerName);
      fd.append('phone', phone);
      fd.append('garaging_zip', garagingZip);
      fd.append('request_type', requestType);
      fd.append('old_vehicle_vin', oldVehicleVin);
      fd.append('old_vehicle_plate', oldVehiclePlate);
      for (const file of files) {
        fd.append('files', file);
      }
      const res = await fetch(`${API_BASE_URL}/api/intake/add-car/extract`, {
        method: 'POST',
        body: fd,
      });
      const data = await res.json().catch(() => null) as PacketResponse | { detail?: unknown } | null;
      if (!res.ok) {
        const detail = data && typeof data === 'object' ? (data as { detail?: unknown }).detail : undefined;
        if (detail && typeof detail === 'object' && (detail as PacketResponse).extraction_failed) {
          const failed = detail as PacketResponse;
          throw new Error(`${failed.message || EXTRACTION_FAILED_MESSAGE}\n${failed.message_zh || EXTRACTION_FAILED_MESSAGE_ZH}`);
        }
        const detailText = typeof detail === 'string' ? detail : res.statusText;
        throw new Error(detailText || `HTTP ${res.status}`);
      }
      if (!data || typeof data !== 'object' || !('packet' in data)) {
        throw new Error(EXTRACTION_FAILED_MESSAGE);
      }
      const packetData = data as PacketResponse;
      if (packetData.extraction_failed) {
        throw new Error(`${packetData.message || EXTRACTION_FAILED_MESSAGE}\n${packetData.message_zh || EXTRACTION_FAILED_MESSAGE_ZH}`);
      }
      if (packetData.mock_mode && !import.meta.env.DEV) {
        throw new Error(`${EXTRACTION_FAILED_MESSAGE}\n${EXTRACTION_FAILED_MESSAGE_ZH}`);
      }
      setPacketResponse(packetData);
      setSubmittedAt(new Date().toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: 'numeric', minute: '2-digit',
      }));
      // Customer lands on Sent to Broker screen first (ADR-003)
      setStep('sent');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      messageApi.error(`Extraction failed: ${msg}`);
      setStep('upload');
    }
  };

  const handleStartOver = () => {
    setStep('intent');
    setRequestType('add_vehicle');
    setSubmittedAt('');
    setCustomerName('');
    setPhone('');
    setGaragingZip('');
    setOldVehicleVin('');
    setOldVehiclePlate('');
    setPacketResponse(null);
    setError(null);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5', padding: '24px 16px 48px' }}>
      {contextHolder}

      {/* Page header — CKS office branding */}
      <div style={{ maxWidth: 640, margin: '0 auto 8px' }}>
        <Text type="secondary" style={{ fontSize: 12, letterSpacing: 0.4 }}>
          CKS Insurance Agency · Chen Kui Insurance Office
        </Text>
        <Title level={2} style={{ margin: '4px 0 2px' }}>
          {requestType === 'policy_review' ? 'Review My Policy' : 'Add Your New Car'}
        </Title>
        <Text type="secondary" style={{ fontSize: 13, display: 'block' }}>
          {requestType === 'policy_review' ? '当前保单检查' : '新车加保申请'}
        </Text>
        <Text type="secondary" style={{ fontSize: 13, display: 'block', marginTop: 4 }}>
          {requestType === 'policy_review'
            ? 'Upload policy docs · Your broker reviews premium & coverage'
            : 'Tell us about your car · Upload documents · Your broker confirms'}
        </Text>
        <Text type="secondary" style={{ fontSize: 13, display: 'block' }}>
          {requestType === 'policy_review'
            ? '上传保单文件 · 经纪人审核保费与保障'
            : '填写车辆信息 · 上传文件 · 经纪人确认'}
        </Text>
      </div>

      {/* Step progress indicator — Intent → Your Info → Upload → Reading → Sent */}
      <div style={{ maxWidth: 640, margin: '0 auto 28px' }}>
        <Steps
          current={STEP_INDEX[step]}
          size="small"
          items={[
            { title: 'Intent', description: '意向' },
            { title: 'Your Info', description: '您的信息' },
            { title: 'Upload', description: '上传文件' },
            { title: 'Reading', description: '读取中' },
            { title: 'Sent', description: '已发送' },
          ]}
        />
      </div>

      {/* Extraction error banner */}
      {error && (
        <Alert
          type="error"
          showIcon
          closable
          message="Something went wrong / 出现问题"
          description={<Text style={{ fontSize: 13, whiteSpace: 'pre-line' }}>{error}</Text>}
          style={{ maxWidth: 640, margin: '0 auto 16px' }}
          onClose={() => setError(null)}
        />
      )}

      {/* ── Active screen ── */}

      {/* Screen 0: Intent Selector */}
      {step === 'intent' && <IntentStep onSelect={handleIntentSelect} />}

      {/* Screen 1: Customer Info */}
      {step === 'info' && <InfoStep requestType={requestType} onNext={handleInfoNext} />}

      {/* Screen 2: Upload */}
      {step === 'upload' && (
        <UploadStep
          customerName={customerName}
          requestType={requestType}
          onExtract={handleExtract}
          onBack={() => setStep('info')}
        />
      )}

      {/* Screen 3: Extracting */}
      {step === 'extracting' && <ExtractingStep requestType={requestType} />}

      {/* Screen 4: Sent to Broker — customer-facing completion (ADR-003) */}
      {step === 'sent' && packetResponse && (
        isPolicyReview(requestType) ? (
          <PolicyOpportunityReportStep
            response={packetResponse}
            customerName={customerName}
            garagingZip={garagingZip}
            submittedAt={submittedAt}
            onStartOver={handleStartOver}
            onGoToUpload={() => setStep('upload')}
          />
        ) : (
          <SentToBrokerStep
            response={packetResponse}
            customerName={customerName}
            garagingZip={garagingZip}
            requestType={requestType}
            submittedAt={submittedAt}
            onStartOver={handleStartOver}
            onGoToUpload={() => setStep('upload')}
          />
        )
      )}

      {/* Screen 5: Trusted Packet — broker-facing; accessible via secondary link */}
      {step === 'packet' && packetResponse && (
        <div>
          {/* Back to customer confirmation view */}
          <div style={{ maxWidth: 640, margin: '0 auto 12px' }}>
            <Button
              type="link"
              onClick={() => setStep('sent')}
              style={{ padding: 0, color: 'rgba(0,0,0,0.45)', fontSize: 13 }}
            >
              ← Back to confirmation / 返回确认页
            </Button>
          </div>
          {isPolicyReview(requestType) ? (
            <PolicyReviewPacketStep
              response={packetResponse}
              customerName={customerName}
              garagingZip={garagingZip}
              onStartOver={handleStartOver}
            />
          ) : (
            <PacketStep
              response={packetResponse}
              customerName={customerName}
              garagingZip={garagingZip}
              requestType={requestType}
              oldVehicleVin={oldVehicleVin}
              oldVehiclePlate={oldVehiclePlate}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      )}
    </div>
  );
}
