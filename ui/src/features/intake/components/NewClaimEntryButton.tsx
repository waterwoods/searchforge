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
  vin?: string;
  accident_description?: string;
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
      const result = await createClaimCase({
        command_id: ids.command_id,
        idempotency_key: ids.idempotency_key,
        is_test: Boolean(values.is_test),
        customer_name: values.customer_name,
        customer_phone: values.customer_phone,
        contact_note: values.contact_note,
        vin: values.vin,
        accident_description: values.accident_description,
        known_facts: {
          ...(values.vin ? { vin: values.vin } : {}),
          ...(values.accident_description
            ? { accident_description: values.accident_description }
            : {}),
        },
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
          message="Create an incomplete Claim. Missing information will be reviewed next. Request More is not sent yet."
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
          <Form.Item name="customer_name" label="Customer name (optional)">
            <Input placeholder="Optional — QA can use placeholder" maxLength={120} />
          </Form.Item>
          <Form.Item name="customer_phone" label="Customer phone (optional)">
            <Input placeholder="Optional" maxLength={40} />
          </Form.Item>
          <Form.Item name="vin" label="VIN if known (optional)">
            <Input placeholder="Leave blank to appear as missing" maxLength={32} />
          </Form.Item>
          <Form.Item name="accident_description" label="Accident description if known (optional)">
            <Input.TextArea rows={3} placeholder="Optional" maxLength={2000} />
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
