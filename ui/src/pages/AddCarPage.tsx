/**
 * P16 Trust Layer — Add-Car Trusted Packet Wizard
 *
 * TurboTax-style 4-screen flow:
 *   1. Customer Info (Name / Phone / Garaging ZIP)
 *   2. Upload Documents (PDF / JPG / PNG / HEIC, max 10)
 *   3. Extracting (animated loading steps)
 *   4. Trusted Packet (VIN pill + vehicle identity + copy button)
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
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudUploadOutlined,
  CopyOutlined,
  EyeOutlined,
  FileTextOutlined,
  LoadingOutlined,
  ReloadOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useEffect, useRef, useState } from 'react';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

// ─── Types ────────────────────────────────────────────────────────────────────

type FieldData = {
  value: string;
  confidence: number;
  confidence_label: 'high' | 'medium' | 'low';
  source_file: string;
  is_mock: boolean;
};

type PacketResponse = {
  packet: Record<string, FieldData>;
  warnings: string[];
  sources: Array<{ file: string; fields: string }>;
  copy_text: string;
  mock_mode: boolean;
  model_used: string;
};

type WizardStep = 'info' | 'upload' | 'extracting' | 'packet';
type VinStatus = 'valid' | 'warning' | 'missing';

const STEP_INDEX: Record<WizardStep, number> = {
  info: 0,
  upload: 1,
  extracting: 2,
  packet: 3,
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

// ─── Broker-friendly copy text (generated on frontend) ───────────────────────

function buildCopyText(
  packet: Record<string, FieldData>,
  warnings: string[],
  sources: Array<{ file: string; fields: string }>,
): string {
  const get = (key: string) => packet[key]?.value || '';

  const vin = get('vin') || 'MISSING';
  const vehicle = [get('year'), get('make'), get('model')].filter(Boolean).join(' ') || 'MISSING';
  const zip = get('garaging_zip') || 'MISSING';
  const customer = [get('customer_name'), get('phone')].filter(Boolean).join(' — ') || 'MISSING';

  const REQUIRED_FIELDS: Array<[string, string]> = [
    ['VIN', 'vin'],
    ['Year', 'year'],
    ['Make', 'make'],
    ['Model', 'model'],
    ['Primary Driver', 'primary_driver'],
    ['Effective Date', 'effective_date'],
  ];
  const missing = REQUIRED_FIELDS.filter(([, key]) => !get(key)).map(([label]) => label);

  const lines = [
    `VIN: ${vin}`,
    `Vehicle: ${vehicle}`,
    `ZIP: ${zip}`,
    `Customer: ${customer}`,
    missing.length > 0 ? `Missing: ${missing.join(', ')}` : 'Missing: None',
    warnings.length > 0 ? `Warnings: ${warnings.join(' | ')}` : 'Warnings: None',
  ];

  if (sources.length > 0) {
    lines.push('Sources:');
    for (const s of sources) {
      lines.push(`  ${s.file} → ${s.fields}`);
    }
  }

  return lines.join('\n');
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

// ─── Screen 1: Customer Info ──────────────────────────────────────────────────

function InfoStep({ onNext }: { onNext: (name: string, phone: string, zip: string) => void }) {
  const [form] = Form.useForm();

  const handleFinish = (values: { name: string; phone: string; zip: string }) => {
    onNext(values.name.trim(), values.phone.trim(), values.zip.trim());
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
  onExtract,
  onBack,
}: {
  customerName: string;
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

// ─── Screen 4: Trusted Packet ─────────────────────────────────────────────────

function PacketStep({
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
  const [showDetails, setShowDetails] = useState(false);
  const { packet, warnings, sources, mock_mode } = response;

  const get = (key: string) => packet[key]?.value || '';

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

  const year = get('year');
  const make = get('make');
  const model = get('model');
  const vehicleLabel = [year, make, model].filter(Boolean).join(' ') || '—';

  const displayZip = get('garaging_zip') || garagingZip || '—';
  const displayName = get('customer_name') || customerName || '—';

  const REQUIRED_FIELDS: Array<[string, string]> = [
    ['VIN', 'vin'],
    ['Year', 'year'],
    ['Make', 'make'],
    ['Model', 'model'],
    ['Primary Driver', 'primary_driver'],
    ['Effective Date', 'effective_date'],
  ];
  const missingFields = REQUIRED_FIELDS.filter(([, key]) => !get(key)).map(([label]) => label);

  const copyText = buildCopyText(packet, warnings, sources);

  const packetTimestamp = new Date().toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(copyText);
      messageApi.success('Packet copied to clipboard');
    } catch {
      messageApi.error('Could not copy — please copy manually');
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      {contextHolder}

      {/* Mock mode banner — only shown in development */}
      {mock_mode && import.meta.env.DEV && (
        <Alert
          type="warning"
          showIcon
          closable
          message="Development mode: mock extraction active"
          description="Connect a Gemini API key to enable real document reading."
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ── Above-fold summary card ── */}
      <Card style={{ marginBottom: 12 }}>

        {/* Header */}
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 4, alignItems: 'flex-start' }} wrap>
          <Space align="center" size={8}>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 22 }} />
            <Title level={3} style={{ margin: 0 }}>Trusted Packet</Title>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>{packetTimestamp}</Text>
        </Space>

        {/* Customer name — above fold */}
        <div style={{ marginBottom: 16, marginTop: 4 }}>
          <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8 }}>
            Customer
          </Text>
          <div>
            <Title level={4} style={{ margin: '2px 0 0' }}>{displayName}</Title>
          </div>
        </div>

        {/* VIN pill + value + source attribution */}
        <div style={{ marginBottom: 16 }}>
          <Space align="center" wrap>
            <VinStatusPill status={vinStatus} />
            {vinValue
              ? <Text code style={{ fontSize: 14, letterSpacing: 1 }}>{vinValue}</Text>
              : <Text type="secondary" style={{ fontSize: 13 }}>No VIN found — verify manually</Text>
            }
          </Space>
          {vinValue && vinSource && (
            <div style={{ marginTop: 4 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                from: {vinSource}
              </Text>
            </div>
          )}
          {vinStatus === 'warning' && vinWarningReason && (
            <div style={{ marginTop: 4 }}>
              <Text type="warning" style={{ fontSize: 12 }}>
                <WarningOutlined style={{ marginRight: 4 }} />
                {vinWarningReason}
              </Text>
            </div>
          )}
        </div>

        {/* Warnings from extraction — shown BEFORE vehicle fields */}
        {warnings.length > 0 && (
          <Alert
            type="warning"
            showIcon
            message={warnings.length === 1 ? warnings[0] : `${warnings.length} warnings`}
            description={warnings.length > 1
              ? <ul style={{ margin: 0, paddingLeft: 16 }}>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
              : undefined
            }
            style={{ marginBottom: 12 }}
          />
        )}

        {/* Missing fields callout — shown BEFORE vehicle fields */}
        {missingFields.length > 0 && (
          <Alert
            type="error"
            showIcon
            message={`Missing: ${missingFields.join(', ')}`}
            description="Ask the customer to provide these items or upload additional documents."
            style={{ marginBottom: 12 }}
          />
        )}

        <Divider style={{ margin: '12px 0' }} />

        {/* Vehicle identity */}
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8 }}>
            Vehicle
          </Text>
          <div>
            <Title level={4} style={{ margin: '2px 0 0' }}>{vehicleLabel}</Title>
          </div>
        </div>

        {/* Garaging ZIP */}
        <div style={{ marginBottom: 20 }}>
          <Text type="secondary" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8 }}>
            Garaging ZIP / 停放邮编
          </Text>
          <div>
            <Text strong style={{ fontSize: 16 }}>{displayZip}</Text>
          </div>
        </div>

        <Divider style={{ margin: '0 0 16px' }} />

        {/* Copy Packet — primary CTA */}
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

      {/* ── Expandable field details ── */}
      <Card size="small" style={{ marginBottom: 12 }}>
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
                <Descriptions.Item label="Name">
                  <DetailField field={packet.customer_name} />
                </Descriptions.Item>
              )}
              {packet.phone && (
                <Descriptions.Item label="Phone">
                  <DetailField field={packet.phone} />
                </Descriptions.Item>
              )}
              {packet.garaging_zip && (
                <Descriptions.Item label="Garaging ZIP">
                  <DetailField field={packet.garaging_zip} />
                </Descriptions.Item>
              )}
            </Descriptions>

            <Title level={5} style={{ marginBottom: 8 }}>Vehicle</Title>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              {packet.vin && (
                <Descriptions.Item label="VIN">
                  <DetailField field={packet.vin} />
                </Descriptions.Item>
              )}
              {packet.year && (
                <Descriptions.Item label="Year">
                  <DetailField field={packet.year} />
                </Descriptions.Item>
              )}
              {packet.make && (
                <Descriptions.Item label="Make">
                  <DetailField field={packet.make} />
                </Descriptions.Item>
              )}
              {packet.model && (
                <Descriptions.Item label="Model">
                  <DetailField field={packet.model} />
                </Descriptions.Item>
              )}
            </Descriptions>

            <Title level={5} style={{ marginBottom: 8 }}>Coverage Details</Title>
            <Descriptions column={1} size="small" bordered style={{ marginBottom: 16 }}>
              {packet.primary_driver && (
                <Descriptions.Item label="Primary Driver">
                  <DetailField field={packet.primary_driver} />
                </Descriptions.Item>
              )}
              {packet.effective_date && (
                <Descriptions.Item label="Effective Date">
                  <DetailField field={packet.effective_date} />
                </Descriptions.Item>
              )}
              {packet.finance_or_lienholder && (
                <Descriptions.Item label="Finance / Lienholder">
                  <DetailField field={packet.finance_or_lienholder} />
                </Descriptions.Item>
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
  const [step, setStep] = useState<WizardStep>('info');
  const [customerName, setCustomerName] = useState('');
  const [phone, setPhone] = useState('');
  const [garagingZip, setGaragingZip] = useState('');
  const [packetResponse, setPacketResponse] = useState<PacketResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [messageApi, contextHolder] = message.useMessage();

  const handleInfoNext = (name: string, ph: string, zip: string) => {
    setCustomerName(name);
    setPhone(ph);
    setGaragingZip(zip);
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
      for (const file of files) {
        fd.append('files', file);
      }
      const res = await fetch('/api/intake/add-car/extract', {
        method: 'POST',
        body: fd,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      const data: PacketResponse = await res.json();
      setPacketResponse(data);
      setStep('packet');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      messageApi.error(`Extraction failed: ${msg}`);
      setStep('upload');
    }
  };

  const handleStartOver = () => {
    setStep('info');
    setCustomerName('');
    setPhone('');
    setGaragingZip('');
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

      {/* Step progress indicator */}
      <div style={{ maxWidth: 640, margin: '0 auto 28px' }}>
        <Steps
          current={STEP_INDEX[step]}
          size="small"
          items={[
            { title: 'Info', description: '客户信息' },
            { title: 'Upload', description: '上传文件' },
            { title: 'Reading', description: '读取中' },
            { title: 'Packet', description: '数据包' },
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

      {/* Active screen */}
      {step === 'info' && <InfoStep onNext={handleInfoNext} />}

      {step === 'upload' && (
        <UploadStep
          customerName={customerName}
          onExtract={handleExtract}
          onBack={() => setStep('info')}
        />
      )}

      {step === 'extracting' && <ExtractingStep />}

      {step === 'packet' && packetResponse && (
        <PacketStep
          response={packetResponse}
          customerName={customerName}
          garagingZip={garagingZip}
          onStartOver={handleStartOver}
        />
      )}
    </div>
  );
}
