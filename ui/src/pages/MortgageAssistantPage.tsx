// frontend/src/pages/MortgageAssistantPage.tsx
import React, { useState, useEffect } from 'react';
import {
    Card,
    Typography,
    Input,
    InputNumber,
    Button,
    Row,
    Col,
    Form,
    App,
    Spin,
    Tag,
    List,
    Divider,
    Alert,
    Space,
    Select,
    Tabs,
    Table,
} from 'antd';
import { BankOutlined, BulbOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { API_BASE_URL } from '../api/config';
import {
    MortgageAgentResponse,
    MortgagePlan,
    MortgageProperty,
    MortgageCompareRequest,
    MortgageCompareResponse,
} from '../types/api.types';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

export const MortgageAssistantPage = () => {
    const { message } = App.useApp();
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<MortgageAgentResponse | null>(null);
    const [properties, setProperties] = useState<MortgageProperty[]>([]);
    const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);
    const [loadingProperties, setLoadingProperties] = useState(false);

    // ========================================
    // A/B Property Comparison Feature
    // ========================================
    // [CHANGE] Added state for A/B property comparison
    const [propertyIdA, setPropertyIdA] = useState<string | null>(null);
    const [propertyIdB, setPropertyIdB] = useState<string | null>(null);
    const [compareResult, setCompareResult] = useState<MortgageCompareResponse | null>(null);
    const [compareLoading, setCompareLoading] = useState(false);
    const [compareError, setCompareError] = useState<string | null>(null);

    // [NEXT_ACTION] State for next action buttons loading
    const [nextActionLoading, setNextActionLoading] = useState(false);
    const [autoCompareNote, setAutoCompareNote] = useState<string | null>(null);

    // Load properties on mount
    useEffect(() => {
        const loadProperties = async () => {
            try {
                setLoadingProperties(true);
                const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/properties`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                });

                if (!res.ok) {
                    throw new Error(`Failed to load properties: ${res.status}`);
                }

                const data: MortgageProperty[] = await res.json();
                setProperties(data);
            } catch (err) {
                console.error('Failed to load properties:', err);
                message.warning('Failed to load property list. You can still enter a custom purchase price.');
            } finally {
                setLoadingProperties(false);
            }
        };

        loadProperties();
    }, [message]);

    const handlePropertyChange = (propertyId: string | null) => {
        setSelectedPropertyId(propertyId);
        if (propertyId) {
            const property = properties.find(p => p.id === propertyId);
            if (property) {
                // Sync purchase_price with selected property
                form.setFieldsValue({ purchase_price: property.purchase_price });
            }
        }
    };

    // [CHANGE] Handle A/B property comparison - calls POST /api/mortgage-agent/compare
    const handleCompare = async () => {
        try {
            const values = await form.validateFields(['income', 'debts', 'down_payment_pct']);
            if (!propertyIdA || !propertyIdB) {
                message.warning('Please select both Property A and Property B');
                return;
            }

            setCompareLoading(true);
            setCompareError(null);
            setCompareResult(null);
            // [NEXT_ACTION] Clear auto compare note when manually comparing
            setAutoCompareNote(null);

            const payload: MortgageCompareRequest = {
                income: values.income,
                monthly_debts: values.debts || 0,
                down_payment_pct: (values.down_payment_pct || 20) / 100,
                state: values.state || undefined,
                property_ids: [propertyIdA, propertyIdB],
            };

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                throw new Error(`API request failed with status ${res.status}`);
            }

            const data: MortgageCompareResponse = await res.json();

            if (!data.ok) {
                throw new Error(data.error || 'Unknown error occurred');
            }

            setCompareResult(data);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setCompareError(errorMessage);
            setCompareResult(null);
            message.error(`Compare failed: ${errorMessage}`);
            console.error('Property compare error:', err);
        } finally {
            setCompareLoading(false);
        }
    };

    // [NEXT_ACTION] Extract common run agent logic for reuse
    const runAgent = async (purchasePrice?: number, propertyId?: string | null) => {
        try {
            const values = await form.validateFields();
            setLoading(true);
            setResponse(null);

            const requestBody = {
                user_message: values.user_message || 'Can I afford this home?',
                profile: 'us_default_simplified',
                inputs: {
                    income: values.income,
                    debts: values.debts || 0,
                    purchase_price: purchasePrice !== undefined ? purchasePrice : values.purchase_price,
                    down_payment_pct: (values.down_payment_pct || 20) / 100,
                    state: values.state || 'WA',
                },
                ...(propertyId !== undefined ? (propertyId ? { property_id: propertyId } : {}) : (selectedPropertyId ? { property_id: selectedPropertyId } : {})),
            };

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (!res.ok) {
                throw new Error(`API request failed with status ${res.status}`);
            }

            const data: MortgageAgentResponse = await res.json();

            if (!data.ok) {
                throw new Error(data.error || 'Unknown error occurred');
            }

            setResponse(data);
            return data;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            message.error(`Error: ${errorMessage}`);
            console.error('Mortgage agent error:', err);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        await runAgent();
    };

    // [NEXT_ACTION] Handler for button A: Re-run at safe max price
    const handleRunAtSafePrice = async () => {
        if (!response?.max_affordability?.max_home_price) {
            message.warning('Missing affordability data. Please run an analysis first.');
            return;
        }

        try {
            setNextActionLoading(true);
            const safePrice = Math.round(response.max_affordability.max_home_price);

            // Update form field
            form.setFieldsValue({ purchase_price: safePrice });

            // Re-run agent with safe price
            await runAgent(safePrice, selectedPropertyId);

            message.success(`Re-calculated plans at safe max price: ${formatCurrency(safePrice)}`);
        } catch (err) {
            // Error already handled in runAgent
        } finally {
            setNextActionLoading(false);
        }
    };

    // [NEXT_ACTION] Handler for button B: Compare with a cheaper property
    const handleCompareWithCheaperProperty = async () => {
        if (!selectedPropertyId) {
            message.warning('Please select a current property as Property A first.');
            return;
        }

        const currentProperty = properties.find(p => p.id === selectedPropertyId);
        if (!currentProperty) {
            message.warning('Current selected property not found.');
            return;
        }

        // Find cheaper properties
        const cheaperProperties = properties
            .filter(p => p.id !== selectedPropertyId && p.purchase_price < currentProperty.purchase_price)
            .sort((a, b) => a.purchase_price - b.purchase_price);

        if (cheaperProperties.length === 0) {
            message.info('No cheaper sample properties available than the current one.');
            return;
        }

        const cheaperProperty = cheaperProperties[0];

        try {
            setNextActionLoading(true);
            setCompareLoading(true);
            setCompareError(null);
            setCompareResult(null);

            // Set property A and B for comparison
            setPropertyIdA(selectedPropertyId);
            setPropertyIdB(cheaperProperty.id);

            const values = await form.validateFields(['income', 'debts', 'down_payment_pct']);
            const payload: MortgageCompareRequest = {
                income: values.income,
                monthly_debts: values.debts || 0,
                down_payment_pct: (values.down_payment_pct || 20) / 100,
                state: values.state || undefined,
                property_ids: [selectedPropertyId, cheaperProperty.id],
            };

            const res = await fetch(`${API_BASE_URL}/api/mortgage-agent/compare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                throw new Error(`API request failed with status ${res.status}`);
            }

            const data: MortgageCompareResponse = await res.json();

            if (!data.ok) {
                throw new Error(data.error || 'Unknown error occurred');
            }

            setCompareResult(data);
            // [NEXT_ACTION] Set auto compare note for display
            setAutoCompareNote(`Automatically selected cheaper property for comparison: ${currentProperty.name} vs ${cheaperProperty.name}`);
            message.success(`Automatically selected cheaper property for comparison: ${currentProperty.name} vs ${cheaperProperty.name}`);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
            setCompareError(errorMessage);
            setCompareResult(null);
            message.error(`Comparison failed: ${errorMessage}`);
            console.error('Property compare error:', err);
        } finally {
            setNextActionLoading(false);
            setCompareLoading(false);
        }
    };

    const getRiskTagColor = (risk: 'low' | 'medium' | 'high') => {
        switch (risk) {
            case 'low':
                return 'success';
            case 'medium':
                return 'warning';
            case 'high':
                return 'error';
            default:
                return 'default';
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    const formatPercent = (value: number) => {
        return `${value.toFixed(2)}%`;
    };

    return (
        <div style={{ padding: '24px' }}>
            <Title level={2} style={{ marginBottom: '8px' }}>
                <BankOutlined /> Mortgage Assistant
            </Title>
            <Paragraph style={{ marginBottom: '24px', color: '#999' }}>
                Get mortgage plan comparisons based on your financial profile.
            </Paragraph>

            <Row gutter={24}>
                {/* Left Column: Input Form */}
                <Col xs={24} lg={10}>
                    <Card title="Financial Information" bordered={false}>
                        <Form
                            form={form}
                            layout="vertical"
                            initialValues={{
                                user_message: 'Can I afford a $800k home with 150k income?',
                                income: 150000,
                                debts: 500,
                                purchase_price: 800000,
                                down_payment_pct: 20,
                                state: 'WA',
                            }}
                        >
                            <Form.Item
                                name="user_message"
                                label="Question (optional)"
                                help="Describe your mortgage question"
                            >
                                <TextArea
                                    rows={3}
                                    placeholder="Can I afford a $800k home with 150k income?"
                                />
                            </Form.Item>

                            <Divider orientation="left" style={{ margin: '16px 0' }}>
                                Select a Sample Property (Optional)
                            </Divider>

                            <Form.Item
                                label="Property"
                                help="Choose a sample property to see mortgage plans for that specific home"
                            >
                                <Select
                                    placeholder="Select a property (optional)"
                                    allowClear
                                    loading={loadingProperties}
                                    value={selectedPropertyId}
                                    onChange={handlePropertyChange}
                                    style={{ width: '100%' }}
                                >
                                    {properties.map((prop) => (
                                        <Select.Option key={prop.id} value={prop.id}>
                                            {prop.name} – {formatCurrency(prop.purchase_price)} ({prop.city}, {prop.state})
                                        </Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>

                            {/* [CHANGE] A/B Property Comparison UI Section */}
                            <Divider orientation="left" style={{ margin: '24px 0 16px 0' }}>
                                A/B Property Comparison
                            </Divider>

                            <Form.Item
                                label="Property A"
                                help="Select first property to compare"
                            >
                                <Select
                                    placeholder="Select Property A"
                                    allowClear
                                    loading={loadingProperties}
                                    value={propertyIdA}
                                    onChange={setPropertyIdA}
                                    style={{ width: '100%' }}
                                >
                                    {properties.map((prop) => (
                                        <Select.Option key={prop.id} value={prop.id}>
                                            {prop.city}, {prop.state} - {prop.name} ({formatCurrency(prop.purchase_price)})
                                        </Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>

                            <Form.Item
                                label="Property B"
                                help="Select second property to compare"
                            >
                                <Select
                                    placeholder="Select Property B"
                                    allowClear
                                    loading={loadingProperties}
                                    value={propertyIdB}
                                    onChange={setPropertyIdB}
                                    style={{ width: '100%' }}
                                >
                                    {properties.map((prop) => (
                                        <Select.Option key={prop.id} value={prop.id}>
                                            {prop.city}, {prop.state} - {prop.name} ({formatCurrency(prop.purchase_price)})
                                        </Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>

                            <Form.Item>
                                <Button
                                    type="default"
                                    size="large"
                                    onClick={handleCompare}
                                    loading={compareLoading}
                                    disabled={
                                        compareLoading ||
                                        !propertyIdA ||
                                        !propertyIdB ||
                                        !form.getFieldValue('income') ||
                                        form.getFieldValue('income') <= 0 ||
                                        form.getFieldValue('debts') === undefined ||
                                        form.getFieldValue('down_payment_pct') === undefined
                                    }
                                    block
                                >
                                    Compare A vs B
                                </Button>
                            </Form.Item>

                            <Form.Item
                                name="income"
                                label="Annual Income"
                                rules={[
                                    { required: true, message: 'Please enter your annual income' },
                                    { type: 'number', min: 0, message: 'Income must be positive' },
                                ]}
                            >
                                <InputNumber
                                    style={{ width: '100%' }}
                                    prefix="$"
                                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                                    placeholder="150000"
                                />
                            </Form.Item>

                            <Form.Item
                                name="debts"
                                label="Monthly Debts"
                                rules={[
                                    { required: true, message: 'Please enter your monthly debts' },
                                    { type: 'number', min: 0, message: 'Debts must be non-negative' },
                                ]}
                            >
                                <InputNumber
                                    style={{ width: '100%' }}
                                    prefix="$"
                                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                                    placeholder="500"
                                />
                            </Form.Item>

                            <Form.Item
                                name="purchase_price"
                                label="Target Home Price"
                                rules={[
                                    { required: true, message: 'Please enter the purchase price' },
                                    { type: 'number', min: 0, message: 'Price must be positive' },
                                ]}
                            >
                                <InputNumber
                                    style={{ width: '100%' }}
                                    prefix="$"
                                    formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                                    parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                                    placeholder="800000"
                                />
                            </Form.Item>

                            <Form.Item
                                name="down_payment_pct"
                                label="Down Payment %"
                                rules={[
                                    { required: true, message: 'Please enter down payment percentage' },
                                    { type: 'number', min: 0, max: 100, message: 'Must be between 0 and 100' },
                                ]}
                            >
                                <InputNumber
                                    style={{ width: '100%' }}
                                    suffix="%"
                                    min={0}
                                    max={100}
                                    placeholder="20"
                                />
                            </Form.Item>

                            <Form.Item
                                name="state"
                                label="State (optional)"
                            >
                                <Input placeholder="WA" maxLength={2} />
                            </Form.Item>

                            <Form.Item>
                                <Button
                                    type="primary"
                                    size="large"
                                    onClick={handleSubmit}
                                    loading={loading}
                                    block
                                    icon={<BankOutlined />}
                                >
                                    Run Mortgage Agent
                                </Button>
                            </Form.Item>
                        </Form>
                    </Card>
                </Col>

                {/* Right Column: Results */}
                <Col xs={24} lg={14}>
                    {loading && (
                        <Card bordered={false}>
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                <Spin size="large" />
                                <div style={{ marginTop: '16px' }}>Analyzing mortgage plans...</div>
                            </div>
                        </Card>
                    )}

                    {!loading && response && (
                        <Tabs defaultActiveKey="borrower" size="small">
                            {/* Borrower View Tab - Simplified: Warning + Plans + Affordability + Property Info */}
                            <Tabs.TabPane tab="Borrower View" key="borrower">
                                {/* Card 1: Hard Warning + Disclaimer */}
                                {response.hard_warning && (
                                    <Alert
                                        message="⚠️ High Risk Warning"
                                        description={response.hard_warning}
                                        type="error"
                                        showIcon
                                        style={{ marginBottom: '16px' }}
                                    />
                                )}
                                <Alert
                                    message="Disclaimer"
                                    description={response.disclaimer}
                                    type="info"
                                    showIcon
                                    style={{ marginBottom: '16px' }}
                                />

                                {/* [NEXT_ACTION] Next Actions Button Area */}
                                <Card
                                    title="Next Actions"
                                    bordered={false}
                                    size="small"
                                    style={{ marginBottom: '24px', backgroundColor: '#fafafa' }}
                                >
                                    <Space size="middle" wrap>
                                        <Button
                                            type="default"
                                            onClick={handleRunAtSafePrice}
                                            disabled={
                                                !response?.max_affordability?.max_home_price ||
                                                loading ||
                                                nextActionLoading
                                            }
                                            loading={nextActionLoading && !compareLoading}
                                        >
                                            Re-run at safe max price
                                        </Button>
                                        <Button
                                            type="default"
                                            onClick={handleCompareWithCheaperProperty}
                                            disabled={
                                                !selectedPropertyId ||
                                                properties.length === 0 ||
                                                loading ||
                                                compareLoading ||
                                                nextActionLoading
                                            }
                                            loading={nextActionLoading && compareLoading}
                                        >
                                            Compare with a cheaper home
                                        </Button>
                                    </Space>
                                </Card>

                                {/* Card 2: Monthly Payment Plans */}
                                <Title level={4} style={{ marginTop: '0px', marginBottom: '16px' }}>
                                    💳 Monthly Payment Plans ({response.plans.length})
                                </Title>
                                {response.plans.map((plan: MortgagePlan) => {
                                    const linkedProperty = plan.property_id
                                        ? properties.find(p => p.id === plan.property_id)
                                        : null;

                                    return (
                                        <Card
                                            key={plan.plan_id}
                                            title={plan.name}
                                            bordered={false}
                                            style={{ marginBottom: '16px' }}
                                            extra={
                                                <Tag color={getRiskTagColor(plan.risk_level)}>
                                                    {plan.risk_level.toUpperCase()} Risk
                                                </Tag>
                                            }
                                        >
                                            <Row gutter={16}>
                                                <Col xs={24} sm={12}>
                                                    <Paragraph>
                                                        <Text strong>Monthly Payment:</Text>{' '}
                                                        <Text style={{ fontSize: '18px', color: '#1890ff' }}>
                                                            {formatCurrency(plan.monthly_payment)}
                                                        </Text>
                                                    </Paragraph>
                                                </Col>
                                                <Col xs={24} sm={12}>
                                                    <Paragraph>
                                                        <Text strong>Interest Rate:</Text>{' '}
                                                        <Text>{formatPercent(plan.interest_rate)}</Text>
                                                    </Paragraph>
                                                </Col>
                                                <Col xs={24} sm={12}>
                                                    <Paragraph>
                                                        <Text strong>Loan Amount:</Text>{' '}
                                                        <Text>{formatCurrency(plan.loan_amount)}</Text>
                                                    </Paragraph>
                                                </Col>
                                                <Col xs={24} sm={12}>
                                                    <Paragraph>
                                                        <Text strong>Term:</Text>{' '}
                                                        <Text>{plan.term_years} years</Text>
                                                    </Paragraph>
                                                </Col>
                                                {plan.dti_ratio !== null && plan.dti_ratio !== undefined && (
                                                    <Col xs={24}>
                                                        <Paragraph>
                                                            <Text strong>Debt-to-Income Ratio:</Text>{' '}
                                                            <Text>{formatPercent(plan.dti_ratio * 100)}</Text>
                                                        </Paragraph>
                                                    </Col>
                                                )}
                                            </Row>

                                            {/* Simplified Pros/Cons - Show only first 2 items */}
                                            {(plan.pros.length > 0 || plan.cons.length > 0) && (
                                                <>
                                                    <Divider style={{ margin: '16px 0' }} />
                                                    <Row gutter={16}>
                                                        {plan.pros.length > 0 && (
                                                            <Col xs={24} sm={12}>
                                                                <Paragraph strong>Key Advantages:</Paragraph>
                                                                <List
                                                                    size="small"
                                                                    dataSource={plan.pros.slice(0, 2)}
                                                                    renderItem={(item) => (
                                                                        <List.Item style={{ padding: '4px 0' }}>
                                                                            <Text type="success">✓</Text>{' '}
                                                                            <Text style={{ marginLeft: '8px' }}>{item}</Text>
                                                                        </List.Item>
                                                                    )}
                                                                />
                                                                {plan.pros.length > 2 && (
                                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                                        + {plan.pros.length - 2} more
                                                                    </Text>
                                                                )}
                                                            </Col>
                                                        )}
                                                        {plan.cons.length > 0 && (
                                                            <Col xs={24} sm={12}>
                                                                <Paragraph strong>Key Considerations:</Paragraph>
                                                                <List
                                                                    size="small"
                                                                    dataSource={plan.cons.slice(0, 2)}
                                                                    renderItem={(item) => (
                                                                        <List.Item style={{ padding: '4px 0' }}>
                                                                            <Text type="warning">⚠</Text>{' '}
                                                                            <Text style={{ marginLeft: '8px' }}>{item}</Text>
                                                                        </List.Item>
                                                                    )}
                                                                />
                                                                {plan.cons.length > 2 && (
                                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                                        + {plan.cons.length - 2} more
                                                                    </Text>
                                                                )}
                                                            </Col>
                                                        )}
                                                    </Row>
                                                </>
                                            )}
                                        </Card>
                                    );
                                })}

                                {/* Card 3: Maximum Affordability */}
                                {response.max_affordability && (
                                    <Card
                                        title="💰 Maximum Affordability"
                                        bordered={false}
                                        style={{ marginTop: '24px', marginBottom: '16px' }}
                                        headStyle={{ backgroundColor: '#f0f9ff', borderBottom: '2px solid #1890ff' }}
                                    >
                                        <Row gutter={16}>
                                            <Col xs={24} sm={12} md={8}>
                                                <Paragraph style={{ marginBottom: '8px' }}>
                                                    <Text strong>Max Home Price:</Text>
                                                </Paragraph>
                                                <Paragraph style={{ fontSize: '20px', color: '#1890ff', fontWeight: 'bold' }}>
                                                    {formatCurrency(response.max_affordability.max_home_price)}
                                                </Paragraph>
                                            </Col>
                                            <Col xs={24} sm={12} md={8}>
                                                <Paragraph style={{ marginBottom: '8px' }}>
                                                    <Text strong>Max Loan Amount:</Text>
                                                </Paragraph>
                                                <Paragraph style={{ fontSize: '18px', color: '#52c41a' }}>
                                                    {formatCurrency(response.max_affordability.max_loan_amount)}
                                                </Paragraph>
                                            </Col>
                                            <Col xs={24} sm={12} md={8}>
                                                <Paragraph style={{ marginBottom: '8px' }}>
                                                    <Text strong>Max Monthly Payment:</Text>
                                                </Paragraph>
                                                <Paragraph style={{ fontSize: '18px', color: '#fa8c16' }}>
                                                    {formatCurrency(response.max_affordability.max_monthly_payment)}
                                                </Paragraph>
                                            </Col>
                                        </Row>
                                        <Divider style={{ margin: '12px 0' }} />
                                        <Row gutter={16}>
                                            <Col xs={24} sm={12}>
                                                <Paragraph style={{ marginBottom: '4px' }}>
                                                    <Text type="secondary">Assumed Interest Rate:</Text>{' '}
                                                    <Text>{formatPercent(response.max_affordability.assumed_interest_rate)}</Text>
                                                </Paragraph>
                                            </Col>
                                            <Col xs={24} sm={12}>
                                                <Paragraph style={{ marginBottom: '4px' }}>
                                                    <Text type="secondary">Target DTI:</Text>{' '}
                                                    <Text>{formatPercent(response.max_affordability.target_dti * 100)}</Text>
                                                </Paragraph>
                                            </Col>
                                        </Row>
                                        <Alert
                                            message="Note"
                                            description="This calculation does not include property taxes, insurance, HOA fees, or PMI. Actual affordability may vary."
                                            type="warning"
                                            showIcon
                                            style={{ marginTop: '12px' }}
                                        />
                                    </Card>
                                )}

                                {/* Card 4: Current Property Information (if property_id exists) */}
                                {(() => {
                                    // Find the first plan with a property_id, or use selectedPropertyId
                                    const propertyId = response.plans.find(p => p.property_id)?.property_id || selectedPropertyId;
                                    const currentProperty = propertyId ? properties.find(p => p.id === propertyId) : null;

                                    if (currentProperty) {
                                        return (
                                            <Card
                                                title="🏠 Current Property Information"
                                                bordered={false}
                                                style={{ marginTop: '24px', marginBottom: '16px' }}
                                                headStyle={{ backgroundColor: '#f0f9ff', borderBottom: '2px solid #1890ff' }}
                                            >
                                                <Row gutter={16}>
                                                    <Col xs={24}>
                                                        <Paragraph style={{ marginBottom: '8px' }}>
                                                            <Text strong>Property Name:</Text>{' '}
                                                            <Text style={{ fontSize: '16px' }}>{currentProperty.name}</Text>
                                                        </Paragraph>
                                                    </Col>
                                                    <Col xs={24} sm={12}>
                                                        <Paragraph style={{ marginBottom: '8px' }}>
                                                            <Text strong>Location:</Text>{' '}
                                                            <Text>{currentProperty.city}, {currentProperty.state}</Text>
                                                        </Paragraph>
                                                    </Col>
                                                    <Col xs={24} sm={12}>
                                                        <Paragraph style={{ marginBottom: '8px' }}>
                                                            <Text strong>Listing Price:</Text>{' '}
                                                            <Text style={{ fontSize: '18px', color: '#1890ff' }}>
                                                                {formatCurrency(currentProperty.purchase_price)}
                                                            </Text>
                                                        </Paragraph>
                                                    </Col>
                                                    {currentProperty.hoa_monthly > 0 && (
                                                        <Col xs={24} sm={12}>
                                                            <Paragraph style={{ marginBottom: '8px' }}>
                                                                <Text strong>HOA (Monthly):</Text>{' '}
                                                                <Text>{formatCurrency(currentProperty.hoa_monthly)}</Text>
                                                            </Paragraph>
                                                        </Col>
                                                    )}
                                                    {currentProperty.note && (
                                                        <Col xs={24}>
                                                            <Paragraph style={{ marginBottom: '0px' }}>
                                                                <Text type="secondary" style={{ fontSize: '13px' }}>
                                                                    {currentProperty.note}
                                                                </Text>
                                                            </Paragraph>
                                                        </Col>
                                                    )}
                                                </Row>
                                            </Card>
                                        );
                                    }
                                    return null;
                                })()}
                            </Tabs.TabPane>

                            {/* Loan Officer View Tab - Professional Summary + Key Metrics */}
                            <Tabs.TabPane tab="Loan Officer View" key="lo">
                                {/* Borrower Snapshot */}
                                <Card title="Borrower Snapshot" bordered={false} style={{ marginBottom: '16px' }} size="small">
                                    <Row gutter={16}>
                                        <Col xs={24} sm={8}>
                                            <Paragraph style={{ marginBottom: '4px' }}>
                                                <Text type="secondary">Annual Income:</Text>
                                            </Paragraph>
                                            <Paragraph style={{ marginBottom: '0px' }}>
                                                <Text strong>{formatCurrency(form.getFieldValue('income') || 0)}</Text>
                                            </Paragraph>
                                        </Col>
                                        <Col xs={24} sm={8}>
                                            <Paragraph style={{ marginBottom: '4px' }}>
                                                <Text type="secondary">Monthly Debts:</Text>
                                            </Paragraph>
                                            <Paragraph style={{ marginBottom: '0px' }}>
                                                <Text strong>{formatCurrency(form.getFieldValue('debts') || 0)}</Text>
                                            </Paragraph>
                                        </Col>
                                        <Col xs={24} sm={8}>
                                            <Paragraph style={{ marginBottom: '4px' }}>
                                                <Text type="secondary">State:</Text>
                                            </Paragraph>
                                            <Paragraph style={{ marginBottom: '0px' }}>
                                                <Text strong>{form.getFieldValue('state') || 'N/A'}</Text>
                                            </Paragraph>
                                        </Col>
                                        {response.max_affordability && (
                                            <Col xs={24} sm={8} style={{ marginTop: '12px' }}>
                                                <Paragraph style={{ marginBottom: '4px' }}>
                                                    <Text type="secondary">Max Home Price:</Text>
                                                </Paragraph>
                                                <Paragraph style={{ marginBottom: '0px' }}>
                                                    <Text strong style={{ color: '#1890ff' }}>
                                                        {formatCurrency(response.max_affordability.max_home_price)}
                                                    </Text>
                                                </Paragraph>
                                            </Col>
                                        )}
                                    </Row>
                                </Card>

                                {/* Plan Metrics Table */}
                                {response.plans && response.plans.length > 0 && (
                                    <Card title="Plan Metrics" bordered={false} style={{ marginBottom: '16px' }} size="small">
                                        <Table
                                            dataSource={response.plans}
                                            rowKey="plan_id"
                                            pagination={false}
                                            size="small"
                                            columns={[
                                                {
                                                    title: 'Plan Name',
                                                    dataIndex: 'name',
                                                    key: 'name',
                                                    render: (text: string) => <Text strong>{text}</Text>,
                                                },
                                                {
                                                    title: 'Monthly Payment',
                                                    dataIndex: 'monthly_payment',
                                                    key: 'monthly_payment',
                                                    render: (value: number) => formatCurrency(value),
                                                    align: 'right',
                                                },
                                                {
                                                    title: 'DTI Ratio',
                                                    dataIndex: 'dti_ratio',
                                                    key: 'dti_ratio',
                                                    render: (value: number | null) =>
                                                        value !== null && value !== undefined ? formatPercent(value * 100) : 'N/A',
                                                    align: 'right',
                                                },
                                                {
                                                    title: 'Risk Level',
                                                    dataIndex: 'risk_level',
                                                    key: 'risk_level',
                                                    render: (risk: 'low' | 'medium' | 'high') => (
                                                        <Tag color={getRiskTagColor(risk)}>{risk.toUpperCase()}</Tag>
                                                    ),
                                                    align: 'center',
                                                },
                                                {
                                                    title: 'Loan Amount',
                                                    dataIndex: 'loan_amount',
                                                    key: 'loan_amount',
                                                    render: (value: number) => formatCurrency(value),
                                                    align: 'right',
                                                },
                                                {
                                                    title: 'Term (Years)',
                                                    dataIndex: 'term_years',
                                                    key: 'term_years',
                                                    align: 'right',
                                                },
                                            ]}
                                        />
                                    </Card>
                                )}

                                {/* LO Summary */}
                                {response.lo_summary && response.lo_summary.trim() ? (
                                    <Card title="Loan Officer Summary" bordered={false} size="small">
                                        <Typography.Paragraph
                                            type="secondary"
                                            style={{
                                                whiteSpace: 'pre-wrap',
                                                fontFamily: 'monospace',
                                                fontSize: '13px',
                                                lineHeight: '1.8',
                                            }}
                                        >
                                            {response.lo_summary}
                                        </Typography.Paragraph>
                                    </Card>
                                ) : (
                                    <Card bordered={false} size="small">
                                        <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                            <Paragraph type="secondary">
                                                No LO summary available.
                                            </Paragraph>
                                        </div>
                                    </Card>
                                )}
                            </Tabs.TabPane>

                            {/* Agent Steps Tab - Only Agent Workflow Steps */}
                            <Tabs.TabPane tab="Agent Steps" key="steps">
                                {response.agent_steps && response.agent_steps.length > 0 ? (
                                    <Card title="Agent Workflow Steps" bordered={false} size="small">
                                        <Table
                                            dataSource={response.agent_steps}
                                            rowKey="step_id"
                                            pagination={false}
                                            size="small"
                                            columns={[
                                                {
                                                    title: 'Step Name',
                                                    dataIndex: 'step_name',
                                                    key: 'step_name',
                                                    render: (text: string) => <Text strong>{text}</Text>,
                                                },
                                                {
                                                    title: 'Status',
                                                    dataIndex: 'status',
                                                    key: 'status',
                                                    render: (status: string) => {
                                                        const getStatusColor = (s: string) => {
                                                            switch (s) {
                                                                case 'completed':
                                                                    return 'success';
                                                                case 'failed':
                                                                    return 'error';
                                                                case 'in_progress':
                                                                    return 'processing';
                                                                default:
                                                                    return 'default';
                                                            }
                                                        };
                                                        return (
                                                            <Tag color={getStatusColor(status)}>
                                                                {status.toUpperCase()}
                                                            </Tag>
                                                        );
                                                    },
                                                    align: 'center',
                                                },
                                                {
                                                    title: 'Duration',
                                                    dataIndex: 'duration_ms',
                                                    key: 'duration_ms',
                                                    render: (value: number | null) => {
                                                        if (value === null || value === undefined) return 'N/A';
                                                        if (value < 0.01) return '< 0.01 ms';
                                                        if (value < 1) return value.toFixed(3) + ' ms';
                                                        if (value < 1000) return value.toFixed(1) + ' ms';
                                                        return (value / 1000).toFixed(2) + ' s';
                                                    },
                                                    align: 'right',
                                                },
                                                {
                                                    title: 'Timestamp',
                                                    dataIndex: 'timestamp',
                                                    key: 'timestamp',
                                                    render: (text: string) => (
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>
                                                            {text}
                                                        </Text>
                                                    ),
                                                },
                                            ]}
                                            expandable={{
                                                expandedRowRender: (step) => {
                                                    const formatJsonPreview = (obj: any, maxLength: number = 150) => {
                                                        if (!obj) return 'N/A';
                                                        const str = JSON.stringify(obj, null, 2);
                                                        return str.length > maxLength
                                                            ? str.substring(0, maxLength) + '...'
                                                            : str;
                                                    };

                                                    return (
                                                        <div style={{ padding: '8px 0' }}>
                                                            <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                                                                <Text type="secondary">Step ID: </Text>
                                                                <Text code>{step.step_id}</Text>
                                                            </Paragraph>
                                                            {step.inputs && (
                                                                <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                                                                    <Text type="secondary" strong>Inputs:</Text>
                                                                    <pre
                                                                        style={{
                                                                            marginTop: '4px',
                                                                            padding: '8px',
                                                                            backgroundColor: '#f5f5f5',
                                                                            borderRadius: '4px',
                                                                            fontSize: '11px',
                                                                            overflow: 'auto',
                                                                            maxHeight: '150px',
                                                                        }}
                                                                    >
                                                                        {formatJsonPreview(step.inputs)}
                                                                    </pre>
                                                                </Paragraph>
                                                            )}
                                                            {step.outputs && (
                                                                <Paragraph style={{ marginBottom: '8px', fontSize: '12px' }}>
                                                                    <Text type="secondary" strong>Outputs:</Text>
                                                                    <pre
                                                                        style={{
                                                                            marginTop: '4px',
                                                                            padding: '8px',
                                                                            backgroundColor: '#f5f5f5',
                                                                            borderRadius: '4px',
                                                                            fontSize: '11px',
                                                                            overflow: 'auto',
                                                                            maxHeight: '150px',
                                                                        }}
                                                                    >
                                                                        {formatJsonPreview(step.outputs)}
                                                                    </pre>
                                                                </Paragraph>
                                                            )}
                                                            {step.error && (
                                                                <Alert
                                                                    message="Error"
                                                                    description={step.error}
                                                                    type="error"
                                                                    style={{ marginTop: '8px', fontSize: '12px' }}
                                                                />
                                                            )}
                                                        </div>
                                                    );
                                                },
                                            }}
                                        />
                                    </Card>
                                ) : (
                                    <Card bordered={false}>
                                        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                            <Paragraph type="secondary">
                                                No agent steps to display yet.
                                            </Paragraph>
                                        </div>
                                    </Card>
                                )}
                            </Tabs.TabPane>
                        </Tabs>
                    )}

                    {!loading && !response && (
                        <Card bordered={false}>
                            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                                <BankOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                                <Paragraph>Fill out the form on the left and click "Run Mortgage Agent" to see mortgage plan comparisons.</Paragraph>
                            </div>
                        </Card>
                    )}

                    {/* [CHANGE] A/B Property Comparison Results Display */}
                    <Divider orientation="left" style={{ marginTop: '32px', marginBottom: '16px' }}>
                        Property A vs B Comparison
                    </Divider>

                    {/* [NEXT_ACTION] Auto compare note */}
                    {autoCompareNote && compareResult && (
                        <Alert
                            message="Auto Comparison"
                            description={autoCompareNote}
                            type="info"
                            showIcon
                            closable
                            onClose={() => setAutoCompareNote(null)}
                            style={{ marginBottom: '16px' }}
                        />
                    )}

                    {compareError && (
                        <Alert
                            message="Comparison Error"
                            description={compareError}
                            type="error"
                            showIcon
                            style={{ marginBottom: '16px' }}
                        />
                    )}

                    {!compareResult && !compareError && (
                        <Card bordered={false}>
                            <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                <Paragraph>Select two properties (A and B) and click "Compare A vs B" to see the comparison.</Paragraph>
                            </div>
                        </Card>
                    )}

                    {compareResult && compareResult.ok && (
                        <Card
                            title="Property Comparison Results"
                            bordered={false}
                            style={{ marginBottom: '16px' }}
                            headStyle={{ backgroundColor: '#f0f9ff', borderBottom: '2px solid #1890ff' }}
                        >
                            {/* Borrower Summary */}
                            <Paragraph style={{ fontSize: '12px', color: '#999', marginBottom: '16px' }}>
                                {compareResult.borrower_profile_summary}
                            </Paragraph>

                            {/* Max Affordability Summary */}
                            {compareResult.max_affordability && (
                                <Alert
                                    message="Maximum Affordability"
                                    description={
                                        `Based on your financial profile, the system estimates you can afford a home price up to approximately ${formatCurrency(compareResult.max_affordability.max_home_price)} (Target DTI: ${formatPercent(compareResult.max_affordability.target_dti * 100)})`
                                    }
                                    type="info"
                                    showIcon
                                    style={{ marginBottom: '16px' }}
                                />
                            )}

                            {/* Two-column comparison layout */}
                            {compareResult.properties.length >= 2 && (() => {
                                // Match properties by ID to ensure correct A/B ordering
                                const propertyA = compareResult.properties.find(p => p.property.property_id === propertyIdA);
                                const propertyB = compareResult.properties.find(p => p.property.property_id === propertyIdB);

                                if (!propertyA || !propertyB) return null;

                                return (
                                    <Row gutter={16}>
                                        {/* Property A */}
                                        <Col xs={24} md={12}>
                                            <Card
                                                title={
                                                    <span>
                                                        Property A: {propertyA.property.display_name}
                                                    </span>
                                                }
                                                bordered
                                                style={{ marginBottom: '16px' }}
                                            >
                                                <Paragraph>
                                                    <Text strong>Location: </Text>
                                                    <Text>
                                                        {propertyA.property.city || 'N/A'}, {propertyA.property.state || 'N/A'}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Price: </Text>
                                                    <Text style={{ fontSize: '18px', color: '#1890ff' }}>
                                                        {formatCurrency(propertyA.property.listing_price)}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Monthly Payment: </Text>
                                                    <Text style={{ fontSize: '16px', color: '#52c41a' }}>
                                                        {formatCurrency(propertyA.metrics.monthly_payment)}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>DTI Ratio: </Text>
                                                    <Text>{formatPercent(propertyA.metrics.dti_ratio * 100)}</Text>
                                                    {' '}
                                                    <Tag color={getRiskTagColor(propertyA.metrics.risk_level)}>
                                                        {propertyA.metrics.risk_level.toUpperCase()} Risk
                                                    </Tag>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Affordable: </Text>
                                                    {propertyA.metrics.within_affordability ? (
                                                        <Tag color="success">✅ Yes</Tag>
                                                    ) : (
                                                        <Tag color="error">❌ No</Tag>
                                                    )}
                                                </Paragraph>
                                            </Card>
                                        </Col>

                                        {/* Property B */}
                                        <Col xs={24} md={12}>
                                            <Card
                                                title={
                                                    <span>
                                                        Property B: {propertyB.property.display_name}
                                                    </span>
                                                }
                                                bordered
                                                style={{ marginBottom: '16px' }}
                                            >
                                                <Paragraph>
                                                    <Text strong>Location: </Text>
                                                    <Text>
                                                        {propertyB.property.city || 'N/A'}, {propertyB.property.state || 'N/A'}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Price: </Text>
                                                    <Text style={{ fontSize: '18px', color: '#1890ff' }}>
                                                        {formatCurrency(propertyB.property.listing_price)}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Monthly Payment: </Text>
                                                    <Text style={{ fontSize: '16px', color: '#52c41a' }}>
                                                        {formatCurrency(propertyB.metrics.monthly_payment)}
                                                    </Text>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>DTI Ratio: </Text>
                                                    <Text>{formatPercent(propertyB.metrics.dti_ratio * 100)}</Text>
                                                    {' '}
                                                    <Tag color={getRiskTagColor(propertyB.metrics.risk_level)}>
                                                        {propertyB.metrics.risk_level.toUpperCase()} Risk
                                                    </Tag>
                                                </Paragraph>
                                                <Paragraph>
                                                    <Text strong>Affordable: </Text>
                                                    {propertyB.metrics.within_affordability ? (
                                                        <Tag color="success">✅ Yes</Tag>
                                                    ) : (
                                                        <Tag color="error">❌ No</Tag>
                                                    )}
                                                </Paragraph>
                                            </Card>
                                        </Col>
                                    </Row>
                                );
                            })()}

                            {/* Best Property Recommendation */}
                            {compareResult.best_property_id && (
                                <Alert
                                    message="Recommendation"
                                    description={
                                        (() => {
                                            const isPropertyA = compareResult.best_property_id === propertyIdA;
                                            const propertyLabel = isPropertyA ? 'Property A' : 'Property B';
                                            return `Based on your financial profile, ${propertyLabel} is the better option (lower DTI ratio and within affordability range).`;
                                        })()
                                    }
                                    type="success"
                                    showIcon
                                    style={{ marginTop: '16px' }}
                                />
                            )}

                            {!compareResult.best_property_id && (
                                <Alert
                                    message="Caution"
                                    description="Both properties present relatively high risk for your financial situation. Please consider carefully before making a decision."
                                    type="warning"
                                    showIcon
                                    style={{ marginTop: '16px' }}
                                />
                            )}
                        </Card>
                    )}
                </Col>
            </Row>
        </div>
    );
};

