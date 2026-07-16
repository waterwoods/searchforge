/**
 * P20 Capability 2 — New Claim (incomplete) entry for Broker Workbench.
 */
import { useRef, useState } from 'react';
import { Alert, Button, Checkbox, Form, Input, Modal, Space, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { createClaimCase, getSavedCase, type SavedCase } from '@/api/inboxTriage';

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
      const result = await createClaimCase({
        command_id: ids.command_id,
        idempotency_key: ids.idempotency_key,
        is_test: Boolean(values.is_test),
        customer_name: values.customer_name,
        customer_phone: values.customer_phone,
        contact_note: values.contact_note,
        vin: values.vin,
        accident_description: values.accident_description,
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
      message.error('Create Claim failed');
    } finally {
      setSaving(false);
      inFlight.current = false;
    }
  };

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
        New Claim
      </Button>
      <Modal
        title="New Claim"
        open={open}
        onCancel={() => {
          if (!saving) setOpen(false);
        }}
        onOk={() => void handleSubmit()}
        okText="Create Claim"
        confirmLoading={saving}
        destroyOnClose
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="先记录事故理解（经过 / 时间 / 地点 / 受伤）。VIN 属于请客户补充，不是开案必填。"
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
          <Form.Item name="accident_description" label="Accident description (what happened)">
            <Input.TextArea rows={3} placeholder="Short story of the accident" maxLength={2000} />
          </Form.Item>
          <Form.Item name="accident_datetime" label="Accident date / time">
            <Input placeholder="Optional seed" maxLength={120} />
          </Form.Item>
          <Form.Item name="accident_location" label="Accident location">
            <Input placeholder="Optional seed" maxLength={500} />
          </Form.Item>
          <Form.Item name="injury_status" label="Anyone injured? (yes / no / unknown)">
            <Input placeholder="Optional seed" maxLength={32} />
          </Form.Item>
          <Form.Item name="customer_name" label="Customer name (optional)">
            <Input placeholder="Optional — QA can use placeholder" maxLength={120} />
          </Form.Item>
          <Form.Item name="customer_phone" label="Customer phone (optional)">
            <Input placeholder="Optional" maxLength={40} />
          </Form.Item>
          <Form.Item name="vin" label="VIN if already known (Request More — optional)">
            <Input placeholder="Leave blank — request later if needed" maxLength={32} />
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
