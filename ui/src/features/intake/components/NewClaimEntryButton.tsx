/**
 * QA-only Manual Intake seed — Create Test Case.
 * Must not imply a bound customer can open a second Active Case.
 */
import { useRef, useState } from 'react';
import { Alert, Button, Checkbox, Form, Input, Modal, Select, Space, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { createClaimCase, getSavedCase, type SavedCase } from '@/api/inboxTriage';
import { isQaToolsEnabled } from '@/config/productSurface';

type FormValues = {
  is_test: boolean;
  customer_name?: string;
  customer_phone?: string;
  contact_note?: string;
  accident_description?: string;
  accident_datetime?: string;
  accident_location?: string;
  injury_status?: string;
  vin?: string;
  qa_label?: string;
};

export function NewClaimEntryButton({
  onCreated,
}: {
  onCreated: (caseRecord: SavedCase) => void;
}) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form] = Form.useForm<FormValues>();
  const inFlight = useRef(false);
  const lastCommand = useRef<{ command_id: string; idempotency_key: string } | null>(null);

  const handleSubmit = async () => {
    if (inFlight.current || saving) return;
    const values = await form.validateFields();
    inFlight.current = true;
    setSaving(true);
    setError(null);
    const stamp = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    const ids = lastCommand.current || {
      command_id: `create_claim_${stamp}`,
      idempotency_key: `create_claim_idem_${stamp}`,
    };
    lastCommand.current = ids;
    try {
      const knownFacts: Record<string, string> = {};
      if (values.accident_description) knownFacts.accident_description = values.accident_description;
      if (values.accident_datetime) knownFacts.accident_datetime = values.accident_datetime;
      if (values.accident_location) knownFacts.accident_location = values.accident_location;
      if (values.injury_status) {
        knownFacts.injury_status = values.injury_status;
        knownFacts.anyone_injured = values.injury_status;
      }
      if (values.vin) knownFacts.vin = values.vin;
      if (values.qa_label?.trim()) knownFacts.qa_label = values.qa_label.trim();
      const result = await createClaimCase({
        command_id: ids.command_id,
        idempotency_key: ids.idempotency_key,
        is_test: Boolean(values.is_test),
        customer_name: values.customer_name,
        customer_phone: values.customer_phone,
        contact_note: values.contact_note,
        vin: values.vin,
        accident_description: values.accident_description,
        qa_label: values.qa_label?.trim() || undefined,
        known_facts: knownFacts,
      });
      const caseId = String(result.case_id || result.broker_projection?.case_id || '').trim();
      if (!caseId) {
        setError('Create succeeded but case id missing.');
        return;
      }
      const created = await getSavedCase(caseId);
      message.success(
        result.outcome === 'replayed'
          ? 'Claim already created; reopened existing result.'
          : values.is_test
            ? 'QA Claim created (TEST).'
            : 'Claim created.',
      );
      lastCommand.current = null;
      setOpen(false);
      form.resetFields();
      onCreated(created);
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown }; status?: number } })?.response;
      if (detail?.status === 503) {
        setError('Case intake requires Postgres service-record storage.');
      } else {
        setError('Could not create claim. Retry — duplicate clicks reuse the same draft key.');
      }
      message.error('Create Test Case failed');
    } finally {
      setSaving(false);
      inFlight.current = false;
    }
  };

  if (!isQaToolsEnabled()) {
    return null;
  }

  return (
    <>
      <Button type="default" icon={<PlusOutlined />} onClick={() => setOpen(true)} data-testid="create-test-case-button">
        Create Test Case
      </Button>
      <Modal
        title="Create Test Case"
        open={open}
        onCancel={() => {
          if (!saving) setOpen(false);
        }}
        onOk={() => void handleSubmit()}
        okText="Create Test Case"
        confirmLoading={saving}
        destroyOnClose
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="QA Manual Intake only. Does not create a second Active Case for a customer-bound identity. Seed accident basics; VIN is optional."
        />
        {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 12 }} /> : null}
        <Form
          form={form}
          layout="vertical"
          initialValues={{ is_test: true, customer_name: '', customer_phone: '', contact_note: '' }}
        >
          <Form.Item name="is_test" valuePropName="checked">
            <Checkbox>Mark as TEST / QA Claim (no real customer PII required)</Checkbox>
          </Form.Item>
          <Form.Item
            name="qa_label"
            label="QA label (optional)"
            tooltip="Physical-device QA marker, e.g. Founder-iPhone. Shown in Workbench; not a real customer name."
          >
            <Input placeholder="Founder-iPhone" maxLength={80} />
          </Form.Item>
          <Form.Item name="accident_description" label="事故经过">
            <Input.TextArea rows={3} placeholder="简要说明事故经过" maxLength={2000} />
          </Form.Item>
          <Form.Item name="accident_datetime" label="事故时间">
            <Input placeholder="可选" maxLength={120} />
          </Form.Item>
          <Form.Item name="accident_location" label="事故地点">
            <Input placeholder="可选" maxLength={500} />
          </Form.Item>
          <Form.Item name="injury_status" label="是否有人受伤（是 / 否 / 未知）">
            <Select
              allowClear
              placeholder="请选择"
              options={[
                { label: '是', value: 'yes' },
                { label: '否', value: 'no' },
                { label: '未知', value: 'unknown' },
              ]}
            />
          </Form.Item>
          <Form.Item name="customer_name" label="Customer name (optional)">
            <Input placeholder="Optional — QA can use placeholder" maxLength={120} />
          </Form.Item>
          <Form.Item name="customer_phone" label="Customer phone (optional)">
            <Input placeholder="Optional" maxLength={40} />
          </Form.Item>
          <Form.Item name="vin" label="VIN（如已知，可选）">
            <Input placeholder="可留空，稍后请客户补充" maxLength={32} />
          </Form.Item>
          <Form.Item name="contact_note" label="Internal note (optional)">
            <Input.TextArea rows={2} maxLength={200} />
          </Form.Item>
        </Form>
        <Space>
          <span style={{ fontSize: 12, color: '#8c8c8c' }}>
            Duplicate clicks reuse the same idempotency key until success.
          </span>
        </Space>
      </Modal>
    </>
  );
}
