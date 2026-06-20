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
  EyeOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  ReloadOutlined,
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
  mock_mode: boolean;
  model_used: string;
  confirmation_notices?: string[];
  case_id?: string;
};

/** All wizard screens including new Screen 0 (intent) and Screen 4 (sent). */
type WizardStep = 'intent' | 'info' | 'upload' | 'extracting' | 'sent' | 'packet';

/** Which request the customer selected on Screen 0. */
type RequestType = 'add_vehicle' | 'replace_vehicle';

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

function computeReadinessStatus(
  packet: Record<string, FieldData>,
  vinStatus: VinStatus,
  warnings: string[],
): ReadinessStatus {
  if (vinStatus === 'warning' || warnings.length > 0) return 'broker_review';
  const criticalMissing = ['vin', 'year', 'make', 'model'].filter(k => !packet[k]?.value);
  if (criticalMissing.length > 0) return 'needs_info';
  return 'ready';
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
      <Title level={3} style={{ marginBottom: 2 }}>Upload New Car Paperwork</Title>
      <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 13 }}>
        上传新车资料 — for <Text strong>{customerName}</Text>
      </Paragraph>
      <Divider style={{ margin: '16px 0 12px' }} />

      <Paragraph type="secondary" style={{ marginBottom: 8, fontSize: 13 }}>
        Upload any of the following:
      </Paragraph>
      <ul style={{ color: 'rgba(0,0,0,0.45)', fontSize: 13, marginBottom: 20, paddingLeft: 20, lineHeight: '1.9' }}>
        <li>Purchase Agreement / 购车合同</li>
        <li>Window Sticker / 车窗贴纸</li>
        <li>Registration / 车辆登记证</li>
        <li>VIN photo / VIN 照片</li>
        <li>Insurance card / 保险卡</li>
        {requestType === 'replace_vehicle' && (
          <li>Old insurance card (optional) / 旧保险卡（可选）</li>
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

const LOADING_STEPS = [
  { label: 'Upload Complete', sublabel: '文件上传完成' },
  { label: 'Reading Documents', sublabel: '正在读取文件' },
  { label: 'Extracting Vehicle Data', sublabel: '提取车辆信息' },
  { label: 'Building Trusted Packet', sublabel: '生成数据包' },
];

const STEP_DELAYS_MS = [0, 2000, 8000, 18000];

function ExtractingStep() {
  const [activeStep, setActiveStep] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

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
        {LOADING_STEPS.map((s, i) => {
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

// ─── Screen 4: Sent to Broker (customer-facing completion) ────────────────────
// ADR-003 language contract:
//   ✅ "Sent to your broker" / "Broker will confirm"
//   ❌ Never "insurance updated" / "policy changed" / "vehicle is now covered"

function SentToBrokerStep({
  response,
  customerName,
  garagingZip,
  requestType,
  submittedAt,
  onStartOver,
  onViewBrokerPacket,
}: {
  response: PacketResponse;
  customerName: string;
  garagingZip: string;
  requestType: RequestType;
  submittedAt: string;
  onStartOver: () => void;
  onViewBrokerPacket: () => void;
}) {
  const { packet, warnings, case_id } = response;
  const get = (key: string) => packet[key]?.value || '';

  const displayName = get('customer_name') || customerName || '';
  const displayPhone = get('phone') || '';
  const vinValue = get('vin');
  const year = get('year');
  const make = get('make');
  const model = get('model');
  const vehicleLabel = [year, make, model].filter(Boolean).join(' ');
  const displayZip = get('garaging_zip') || garagingZip || '';

  const vinValidation = vinValue ? validateVin(vinValue) : null;
  const vinStatus: VinStatus = !vinValue ? 'missing' : vinValidation?.valid ? 'valid' : 'warning';
  const readinessStatus = computeReadinessStatus(packet, vinStatus, warnings);

  const criticalMissing: string[] = [];
  if (!vinValue) criticalMissing.push('VIN number');
  if (!year || !make || !model) criticalMissing.push('Vehicle Year / Make / Model');
  if (!displayZip) criticalMissing.push('Garaging ZIP');

  const requestLabel = requestType === 'replace_vehicle'
    ? 'Vehicle replacement request / 换车申请'
    : 'New car addition request / 加新车申请';

  const rowStyle: React.CSSProperties = {
    display: 'flex', gap: 12, padding: '8px 0',
    borderBottom: '1px solid #f0f0f0', alignItems: 'flex-start',
  };
  const iconStyle: React.CSSProperties = { color: '#52c41a', marginTop: 3, flexShrink: 0, fontSize: 15 };

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>

      {/* ── Success header — ADR-003 compliant language ── */}
      <div style={{
        background: '#f6ffed', border: '2px solid #95de64', borderRadius: 14,
        padding: '32px 28px 28px', marginBottom: 20, textAlign: 'center',
      }}>
        <SendOutlined style={{ color: '#52c41a', fontSize: 44, marginBottom: 14 }} />
        <Title level={3} style={{ margin: 0, marginBottom: 4, color: '#237804' }}>
          Your request has been submitted
        </Title>
        <Title level={4} style={{ margin: 0, marginBottom: 14, color: '#389e0d', fontWeight: 400 }}>
          您的申请已提交
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

        {displayZip && (
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
          {case_id && (
            <Text type="secondary" style={{ fontSize: 11 }}>Case #{case_id}</Text>
          )}
          {readinessStatus === 'ready' && (
            <Tag color="success" icon={<CheckCircleOutlined />}>Ready for broker review / 资料已准备完成</Tag>
          )}
          {readinessStatus === 'needs_info' && (
            <Tag color="error" icon={<CloseCircleOutlined />}>NEED INFO</Tag>
          )}
          {readinessStatus === 'broker_review' && (
            <Tag color="warning" icon={<WarningOutlined />}>BROKER REVIEW</Tag>
          )}
        </div>
      </Card>

      {/* ── Status-specific context message ── */}
      {readinessStatus === 'needs_info' && criticalMissing.length > 0 && (
        <Alert
          type="warning" showIcon
          style={{ marginBottom: 16 }}
          message="Your broker may contact you for more information"
          description={
            <div>
              <Text type="secondary" style={{ fontSize: 13 }}>
                经纪人可能会联系您补充以下信息：
              </Text>
              <ul style={{ margin: '6px 0 0', paddingLeft: 18, fontSize: 13 }}>
                {criticalMissing.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          }
        />
      )}

      {readinessStatus === 'broker_review' && (
        <Alert
          type="info" showIcon
          style={{ marginBottom: 16 }}
          message="Your broker needs to verify some details"
          description="经纪人将核实您的文件中的一些细节，并与您确认。"
        />
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
        <Button
          type="primary"
          size="large"
          block
          icon={<ReloadOutlined />}
          onClick={onStartOver}
          style={{ height: 52, fontSize: 16 }}
        >
          Start another request / 提交新申请
        </Button>
        <Button
          size="large"
          block
          icon={<EyeOutlined />}
          onClick={onViewBrokerPacket}
          style={{ color: 'rgba(0,0,0,0.45)', fontSize: 14 }}
        >
          View broker packet / 查看经纪人数据包
        </Button>
      </Space>
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
  const { packet, warnings, sources, mock_mode, confirmation_notices } = response;

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
  const readinessStatus = computeReadinessStatus(packet, vinStatus, warnings);
  const criticalMissingCount = ['vin', 'year', 'make', 'model'].filter(k => !packet[k]?.value).length;

  // ── Follow-Up missing keys ──
  const followUpMissingKeys: string[] = [];
  if (!vinValue) followUpMissingKeys.push('vin');
  if (!year || !make || !model) {
    if (!year) followUpMissingKeys.push('year');
    if (!make) followUpMissingKeys.push('make');
    if (!model) followUpMissingKeys.push('model');
  }
  if (!displayZip) followUpMissingKeys.push('garaging_zip');
  if (pdDefaulted) followUpMissingKeys.push('primary_driver');
  if (!effectiveDate) followUpMissingKeys.push('effective_date');

  // ── Copy text ──
  const copyText = buildCopyText(packet, warnings, sources, customerName, garagingZip, requestType, oldVehicleVin, oldVehiclePlate);

  const packetTimestamp = new Date().toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(copyText);
      messageApi.success('Packet copied to clipboard / 已复制');
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

      {/* ── Main Packet Card ── */}
      <Card style={{ marginBottom: 12 }}>

        {/* Header */}
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16, alignItems: 'flex-start' }} wrap>
          <Space align="center" size={8}>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
            <Title level={4} style={{ margin: 0 }}>Trusted Packet</Title>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>{packetTimestamp}</Text>
        </Space>

        {/* Extraction warnings — compact, before sections */}
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

        {/* ── Copy Packet — primary broker CTA ── */}
        <Button
          type="primary"
          icon={<CopyOutlined />}
          size="large"
          block
          onClick={handleCopy}
          style={{ height: 52, fontSize: 16 }}
        >
          Copy Packet / 复制数据包
        </Button>
      </Card>

      {/* ── Auto Follow-Up Message — shown when missing items exist ── */}
      {followUpMissingKeys.length > 0 && (
        <AutoFollowUpMessage missingKeys={followUpMissingKeys} uploadLink={uploadLink} />
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
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      const data: PacketResponse = await res.json();
      setPacketResponse(data);
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

      {/* Page header */}
      <div style={{ maxWidth: 640, margin: '0 auto 8px' }}>
        <Title level={2} style={{ margin: 0, marginBottom: 2 }}>
          Add-Car Intake
        </Title>
        <Text type="secondary" style={{ fontSize: 13 }}>
          上传客户文件 → Trusted Packet → 复制到运营商系统
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
          message="Something went wrong"
          description={error}
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
      {step === 'extracting' && <ExtractingStep />}

      {/* Screen 4: Sent to Broker — customer-facing completion (ADR-003) */}
      {step === 'sent' && packetResponse && (
        <SentToBrokerStep
          response={packetResponse}
          customerName={customerName}
          garagingZip={garagingZip}
          requestType={requestType}
          submittedAt={submittedAt}
          onStartOver={handleStartOver}
          onViewBrokerPacket={() => setStep('packet')}
        />
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
          <PacketStep
            response={packetResponse}
            customerName={customerName}
            garagingZip={garagingZip}
            requestType={requestType}
            oldVehicleVin={oldVehicleVin}
            oldVehiclePlate={oldVehiclePlate}
            onStartOver={handleStartOver}
          />
        </div>
      )}
    </div>
  );
}
