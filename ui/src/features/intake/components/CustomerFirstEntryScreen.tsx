/**
 * P16 Customer First — entry + status surface (phone return key, no login).
 */
import { useState } from 'react';
import type { CSSProperties } from 'react';
import { Button, Card, Input, Space, Spin, Typography } from 'antd';
import { PhoneOutlined, UserOutlined } from '@ant-design/icons';
import {
    lookupActiveCaseByPhone,
    type CustomerActiveCaseSummary,
} from '@/api/inboxTriage';
import {
    customerBusinessStateDisplay,
    customerStatusSurfaceFieldLabel,
    formatPhoneDisplay,
    isValidCustomerPhoneInput,
    normalizePhoneInput,
    resolveCustomerBusinessState,
} from '@/features/intake/utils/customerFirstEntry';

const { Title, Text, Paragraph } = Typography;

export type CustomerFirstEntryPhase =
    | 'entry'
    | 'checking'
    | 'no_active'
    | 'active_exists'
    | 'blocked_second_vehicle';

export type CustomerFirstEntryResult =
    | { action: 'start_new'; phone: string; name: string }
    | { action: 'continue_existing'; phone: string; name: string; caseId: string }
    | { action: 'contact_broker'; phone: string; name: string; caseId?: string };

export type CustomerFirstEntryScreenProps = {
    clientId?: string;
    onComplete: (result: CustomerFirstEntryResult) => void;
    /** When true, show one-active-case block (simulation 4 path). */
    forceActiveCaseBlock?: boolean;
    initialPhone?: string;
    initialName?: string;
};

const cardStyle: CSSProperties = {
    background: '#fff',
    border: '1px solid #e8e8e8',
    borderRadius: 10,
    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
};

const sectionLabelStyle: CSSProperties = {
    fontSize: 12,
    display: 'block',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    color: '#8c8c8c',
    marginBottom: 6,
};

function StillNeededList({ fields }: { fields: string[] }) {
    if (!fields.length) {
        return (
            <Text style={{ fontSize: 15, color: '#262626' }}>
                None — all key fields collected
                <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 4 }}>
                    关键信息已齐
                </Text>
            </Text>
        );
    }
    const labels = fields.map((f) => customerStatusSurfaceFieldLabel(f));
    return (
        <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.7 }}>
            {labels.map((label) => (
                <li key={label}>
                    <Text style={{ fontSize: 15, fontWeight: 500, color: '#262626' }}>{label}</Text>
                </li>
            ))}
        </ul>
    );
}

function BusinessStateSection({ activeCase }: { activeCase: CustomerActiveCaseSummary }) {
    const businessState = resolveCustomerBusinessState(activeCase);
    const copy = customerBusinessStateDisplay(businessState);
    return (
        <div>
            <Text style={sectionLabelStyle}>Status / 状态</Text>
            <Text style={{ fontSize: 16, fontWeight: 600, color: '#262626', display: 'block' }}>
                {copy.zh}
            </Text>
            <Text type="secondary" style={{ fontSize: 13, display: 'block', marginTop: 4 }}>
                {copy.en}
            </Text>
            {copy.hint ? (
                <Text type="secondary" style={{ fontSize: 13, display: 'block', marginTop: 6, lineHeight: 1.5 }}>
                    {copy.hint}
                </Text>
            ) : null}
        </div>
    );
}

function ActiveCaseCard({
    activeCase,
    phone,
    onContinue,
    onContactBroker,
}: {
    activeCase: CustomerActiveCaseSummary;
    phone: string;
    onContinue: () => void;
    onContactBroker: () => void;
}) {
    const stillNeeded = activeCase.still_needed_fields ?? activeCase.missing_fields ?? [];

    return (
        <Card size="small" style={{ ...cardStyle, borderColor: '#91caff', background: '#f0f7ff' }}>
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
                <div>
                    <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
                        Active Add-Car Request
                    </Title>
                    <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 15 }}>
                        进行中的加车申请
                        {activeCase.vehicle_display ? ` · ${activeCase.vehicle_display}` : ''}
                    </Text>
                </div>

                <div style={{ display: 'grid', gap: 18 }}>
                    <BusinessStateSection activeCase={activeCase} />
                    <div>
                        <Text style={sectionLabelStyle}>Still Needed / 仍缺项</Text>
                        <StillNeededList fields={stillNeeded} />
                    </div>
                </div>

                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                    <Button type="primary" size="large" block onClick={onContinue}>
                        Continue Request / 继续申请
                    </Button>
                    <Button size="large" block onClick={onContactBroker}>
                        Contact Broker / 联系经纪人
                    </Button>
                </Space>

                <Text type="secondary" style={{ fontSize: 12, textAlign: 'center', display: 'block' }}>
                    Return key: {formatPhoneDisplay(phone)}
                </Text>
            </Space>
        </Card>
    );
}

export function CustomerFirstEntryScreen({
    clientId,
    onComplete,
    initialPhone = '',
    initialName = '',
}: CustomerFirstEntryScreenProps) {
    const [phone, setPhone] = useState(initialPhone);
    const [name, setName] = useState(initialName);
    const [phase, setPhase] = useState<CustomerFirstEntryPhase>('entry');
    const [phoneError, setPhoneError] = useState<string | null>(null);
    const [activeCase, setActiveCase] = useState<CustomerActiveCaseSummary | null>(null);

    const handleContinue = async () => {
        setPhoneError(null);
        if (!isValidCustomerPhoneInput(phone)) {
            setPhoneError('请输入有效的 10 位美国手机号。Please enter a valid 10-digit phone number.');
            return;
        }
        const normalized = normalizePhoneInput(phone);
        setPhase('checking');
        try {
            const result = await lookupActiveCaseByPhone(normalized, clientId);
            if (result.has_active_case && result.active_case) {
                setActiveCase(result.active_case);
                setPhase('active_exists');
            } else {
                setPhase('no_active');
            }
        } catch {
            setPhoneError('无法验证手机号，请稍后再试。');
            setPhase('entry');
        }
    };

    const finishStartNew = () => {
        const normalized = normalizePhoneInput(phone);
        onComplete({ action: 'start_new', phone: normalized, name: name.trim() });
    };

    if (phase === 'checking') {
        return (
            <Card size="small" style={cardStyle}>
                <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                    <Spin size="large" />
                    <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
                        正在查找您的申请…
                    </Text>
                </div>
            </Card>
        );
    }

    if (phase === 'no_active') {
        return (
            <Card size="small" style={cardStyle}>
                <Space direction="vertical" size={20} style={{ width: '100%' }}>
                    <div>
                        <Title level={3} style={{ margin: 0, fontWeight: 600 }}>
                            Start New Add-Car Request
                        </Title>
                        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 15 }}>
                            开始新的加车申请 · 手机号 {formatPhoneDisplay(phone)} 将用于找回本条申请
                        </Text>
                    </div>
                    <Button type="primary" size="large" block onClick={finishStartNew}>
                        继续办理加车
                    </Button>
                    <Button type="link" block onClick={() => setPhase('entry')} style={{ fontSize: 13 }}>
                        返回修改手机号
                    </Button>
                </Space>
            </Card>
        );
    }

    if ((phase === 'active_exists' || phase === 'blocked_second_vehicle') && activeCase) {
        return (
            <ActiveCaseCard
                activeCase={activeCase}
                phone={phone}
                onContinue={() =>
                    onComplete({
                        action: 'continue_existing',
                        phone: normalizePhoneInput(phone),
                        name: name.trim(),
                        caseId: activeCase.case_id,
                    })
                }
                onContactBroker={() =>
                    onComplete({
                        action: 'contact_broker',
                        phone: normalizePhoneInput(phone),
                        name: name.trim(),
                        caseId: activeCase.case_id,
                    })
                }
            />
        );
    }

    return (
        <Card size="small" style={cardStyle}>
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
                <div
                    style={{
                        padding: '14px 16px',
                        background: 'linear-gradient(135deg, #f6ffed 0%, #e6f4ff 100%)',
                        borderRadius: 8,
                        border: '1px solid #d9f7be',
                    }}
                >
                    <Title level={2} style={{ margin: 0, fontWeight: 600, fontSize: 22 }}>
                        Add-Car Request
                    </Title>
                    <Text style={{ display: 'block', fontSize: 16, marginTop: 2, color: '#434343' }}>
                        加车申请
                    </Text>
                    <ul style={{ margin: '12px 0 0', paddingLeft: 18, lineHeight: 1.7, color: '#595959', fontSize: 14 }}>
                        <li>
                            <Text strong>No account required</Text> · 无需注册
                        </li>
                        <li>
                            <Text strong>No password required</Text> · 无需密码
                        </li>
                        <li>
                            <Text strong>Return anytime using your phone number</Text>
                            <br />
                            <Text type="secondary">可随时通过手机号继续办理</Text>
                        </li>
                    </ul>
                </div>

                <div>
                    <Text strong style={{ display: 'block', marginBottom: 8, fontSize: 15 }}>
                        Phone Number / 手机号 <Text type="danger">*</Text>
                    </Text>
                    <Input
                        size="large"
                        prefix={<PhoneOutlined />}
                        placeholder="(626) 555-0100"
                        value={phone}
                        onChange={(e) => {
                            setPhone(e.target.value);
                            setPhoneError(null);
                        }}
                        inputMode="tel"
                        autoComplete="tel"
                        autoFocus
                        status={phoneError ? 'error' : undefined}
                    />
                    <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.55 }}>
                        Use the phone number we should contact.
                        <br />
                        用于找回申请和联系您。
                    </Paragraph>
                    {phoneError ? (
                        <Text type="danger" style={{ fontSize: 13, display: 'block', marginTop: 6 }}>
                            {phoneError}
                        </Text>
                    ) : null}
                </div>

                <div>
                    <Text strong style={{ display: 'block', marginBottom: 8, fontSize: 15 }}>
                        Name (optional) / 姓名（选填）
                    </Text>
                    <Input
                        size="large"
                        prefix={<UserOutlined />}
                        placeholder="李华"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        autoComplete="name"
                    />
                    <Paragraph type="secondary" style={{ margin: '8px 0 0', fontSize: 13, lineHeight: 1.55 }}>
                        Used by your broker.
                        <br />
                        方便经纪人联系您。
                    </Paragraph>
                </div>

                <Button type="primary" size="large" block onClick={() => void handleContinue()}>
                    Continue / 继续
                </Button>
            </Space>
        </Card>
    );
}
