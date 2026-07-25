/**
 * P19H-3h-1A / P20 Cap 3A+3B — Claim H5 intake + QR landing + VIN submit.
 * Cap 3A: active Slice 1 next action → request-item screen first.
 * Cap 3B: VIN submit → server receipt → submitted_waiting (broker review).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  applySlice1ProjectionToIntake,
  fetchH5ClaimIntake,
  mapH5ClaimError,
  newCommandId,
  newSubmitIntentId,
  patchH5ClaimFields,
  submitH5ClaimIntake,
  submitH5RequestItem,
  type H5ClaimIntakeInfo,
} from '@/api/h5ClaimIntake';
import {
  CAP3B_NO_APPROVAL_DISCLAIMER,
  resolveH5ClaimLanding,
  type H5ClaimLandingDecision,
} from '@/features/claim-h5/h5ClaimLanding';
import { isCustomerSubmittableItemType } from '@/features/claim-h5/mvpCustomerSubmit';

type WizardStep = 'start' | 'injury' | 'time_location' | 'story' | 'vehicle_other_party' | 'evidence' | 'review' | 'done';

const styles = {
  page: {
    minHeight: '100vh',
    background: '#f4f6f8',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    color: '#1a1a1a',
  } as const,
  header: {
    background: '#0d3b66',
    color: '#fff',
    padding: '16px 20px',
    textAlign: 'center' as const,
  },
  body: { padding: '20px 16px 80px', maxWidth: 480, margin: '0 auto' } as const,
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: '20px 16px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    marginBottom: 16,
  } as const,
  footer: {
    position: 'fixed' as const,
    bottom: 0,
    left: 0,
    right: 0,
    background: '#fff',
    borderTop: '1px solid #e8e8e8',
    padding: '12px 16px',
    fontSize: 12,
    color: '#666',
    textAlign: 'center' as const,
  },
  btn: {
    width: '100%',
    padding: '14px 16px',
    fontSize: 16,
    fontWeight: 600,
    border: 'none',
    borderRadius: 10,
    background: '#0d3b66',
    color: '#fff',
    cursor: 'pointer',
  } as const,
  btnPrimarySubmit: {
    width: '100%',
    padding: '18px 16px',
    fontSize: 18,
    fontWeight: 700,
    border: 'none',
    borderRadius: 12,
    background: '#0d3b66',
    color: '#fff',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(13, 59, 102, 0.35)',
  } as const,
  submitBlock: {
    background: '#eef4fa',
    border: '2px solid #0d3b66',
    borderRadius: 12,
    padding: '16px 14px',
    marginBottom: 20,
  } as const,
  submitSubtext: {
    fontSize: 13,
    color: '#444',
    lineHeight: 1.55,
    marginTop: 10,
    marginBottom: 0,
    textAlign: 'center' as const,
  } as const,
  reviewWarning: {
    background: '#fff3cd',
    border: '1px solid #e6b800',
    borderRadius: 8,
    padding: '12px 14px',
    marginBottom: 16,
    fontSize: 14,
    lineHeight: 1.55,
    color: '#5c4a00',
  } as const,
  btnDisabled: { opacity: 0.55, cursor: 'not-allowed' } as const,
  btnSecondary: {
    width: '100%',
    padding: '14px 16px',
    fontSize: 16,
    fontWeight: 600,
    border: '1px solid #0d3b66',
    borderRadius: 10,
    background: '#fff',
    color: '#0d3b66',
    cursor: 'pointer',
    marginTop: 10,
  } as const,
  input: {
    width: '100%',
    padding: '12px',
    fontSize: 16,
    border: '1px solid #ccc',
    borderRadius: 8,
    marginBottom: 12,
    boxSizing: 'border-box' as const,
  },
  label: { display: 'block', marginBottom: 8, fontWeight: 500 } as const,
  error: { color: '#c0392b', fontSize: 14, marginBottom: 12 } as const,
  alert: {
    background: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    fontSize: 14,
  } as const,
  sectionTitle: { margin: '0 0 8px', fontSize: 15, fontWeight: 600 } as const,
  hint: { fontSize: 14, color: '#666', marginTop: 8 } as const,
  dashboard: {
    background: '#fff',
    borderRadius: 12,
    padding: '18px 16px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    marginBottom: 16,
    border: '1px solid #d8e3ef',
  } as const,
  dashboardTitle: { margin: '0 0 6px', fontSize: 20, fontWeight: 700, color: '#0d3b66' } as const,
  dashboardSubtitle: { margin: '0 0 14px', fontSize: 14, lineHeight: 1.55, color: '#444' } as const,
  dashboardStatus: {
    display: 'inline-block',
    background: '#eef4fa',
    color: '#0d3b66',
    padding: '6px 10px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 14,
  } as const,
  statusPill: {
    display: 'inline-block',
    background: '#eef4fa',
    color: '#0d3b66',
    padding: '6px 10px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 12,
  } as const,
  qaMarker: {
    display: 'inline-block',
    marginTop: 8,
    padding: '4px 10px',
    borderRadius: 8,
    background: 'rgba(255,255,255,0.18)',
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.2,
  } as const,
  progressLine: { fontSize: 14, color: '#444', margin: '8px 0 0' } as const,
};

function stepFromInfo(info: H5ClaimIntakeInfo): WizardStep {
  if (info.submitted) return 'done';
  const cur = info.current_step as WizardStep;
  if (cur === 'start' || !cur) return 'start';
  return cur;
}

function normalizeVinInput(value: string): string {
  return String(value || '')
    .trim()
    .toUpperCase()
    .replace(/[^A-HJ-NPR-Z0-9]/g, '');
}

function validateVinInput(value: string): string {
  const normalized = normalizeVinInput(value);
  if (!normalized) return '请填写车辆 VIN';
  if (normalized.length !== 17) return 'VIN 应为 17 位（不含 I/O/Q）';
  if (/[IOQ]/.test(normalized)) return 'VIN 不能包含字母 I、O、Q';
  return '';
}

export default function H5ClaimIntakePage() {
  const { taskToken = '' } = useParams<{ taskToken: string }>();
  const [info, setInfo] = useState<H5ClaimIntakeInfo | null>(null);
  const [step, setStep] = useState<WizardStep>('start');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOverview, setShowOverview] = useState(false);
  const [vinDraft, setVinDraft] = useState('');
  const [vinValidation, setVinValidation] = useState('');
  const submitIntentRef = useRef<string>(newSubmitIntentId());
  /** Cap 3B: stable command identity for duplicate-tap / network retry. */
  const requestItemCommandRef = useRef<{ command_id: string; idempotency_key: string } | null>(
    null,
  );
  const landingRoutedRef = useRef(false);

  const [injury, setInjury] = useState('');
  const [accidentDatetime, setAccidentDatetime] = useState('');
  const [accidentLocation, setAccidentLocation] = useState('');
  const [accidentDescription, setAccidentDescription] = useState('');
  const [ownVehicle, setOwnVehicle] = useState('');
  const [otherPartyPlate, setOtherPartyPlate] = useState('');
  const [otherPartyInfo, setOtherPartyInfo] = useState('');

  const hydrateFields = useCallback((data: H5ClaimIntakeInfo) => {
    const f = data.key_facts || {};
    if (f.injury_status) setInjury(String(f.injury_status));
    if (f.accident_datetime) setAccidentDatetime(String(f.accident_datetime));
    if (f.accident_location) setAccidentLocation(String(f.accident_location));
    if (f.accident_description) setAccidentDescription(String(f.accident_description));
    if (f.own_vehicle_info) setOwnVehicle(String(f.own_vehicle_info));
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchH5ClaimIntake(taskToken);
        if (cancelled) return;
        setInfo(data);
        hydrateFields(data);
        setStep(stepFromInfo(data));
        landingRoutedRef.current = false;
        setShowOverview(false);
      } catch (e) {
        if (!cancelled) {
          setInfo(null);
          setError(e instanceof Error ? e.message : 'load_failed');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [taskToken, hydrateFields]);

  useEffect(() => {
    if (step !== 'review' || submitting) return undefined;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [step, submitting]);

  const landing: H5ClaimLandingDecision = useMemo(
    () => resolveH5ClaimLanding({ loading, loadError: error, info }),
    [loading, error, info],
  );

  // Prevent duplicate client-side landing flips once request-item is known.
  useEffect(() => {
    if (landing.kind === 'request_item' && !landingRoutedRef.current) {
      landingRoutedRef.current = true;
      setShowOverview(false);
    }
  }, [landing.kind]);

  const progressLabel = useMemo(() => {
    if (!info) return '';
    return `${info.completed_count}/${info.step_total} 已完成`;
  }, [info]);

  const runSave = async (nextStep: WizardStep, save: () => Promise<H5ClaimIntakeInfo>) => {
    setSaving(true);
    setError(null);
    try {
      const data = await save();
      setInfo(data);
      setStep(nextStep);
    } catch (e) {
      const code = e instanceof Error ? e.message : 'save_failed';
      setError(mapH5ClaimError(code, '保存失败，请检查网络后重试。'));
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const data = await submitH5ClaimIntake(taskToken, submitIntentRef.current);
      setInfo(data);
      setStep('done');
    } catch (e) {
      const code = e instanceof Error ? e.message : 'submit_failed';
      setError(mapH5ClaimError(code, '提交失败，请重试。如果仍失败，可以继续在微信里联系陈总。'));
    } finally {
      setSubmitting(false);
    }
  };

  const refreshStatus = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const data = await fetchH5ClaimIntake(taskToken);
      setInfo(data);
      hydrateFields(data);
      landingRoutedRef.current = false;
      setShowOverview(false);
      if (data.submitted) {
        setStep('done');
      }
    } catch (e) {
      const code = e instanceof Error ? e.message : 'network_error';
      setError(mapH5ClaimError(code, '刷新失败，请检查网络后重试。'));
    } finally {
      setRefreshing(false);
    }
  };

  const retryLoad = () => {
    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchH5ClaimIntake(taskToken);
        setInfo(data);
        hydrateFields(data);
        setStep(stepFromInfo(data));
        landingRoutedRef.current = false;
        setShowOverview(false);
      } catch (e) {
        setInfo(null);
        setError(e instanceof Error ? e.message : 'load_failed');
      } finally {
        setLoading(false);
      }
    })();
  };

  const busy = saving || submitting || refreshing;

  const photoCount = info?.photo_count ?? info?.attachment_count ?? 0;

  const ensureRequestItemCommandIdentity = () => {
    if (!requestItemCommandRef.current) {
      requestItemCommandRef.current = {
        command_id: newCommandId('cmd-vin'),
        idempotency_key: newCommandId('idem-vin'),
      };
    }
    return requestItemCommandRef.current;
  };

  const handleVinPrimary = async () => {
    if (submitting || refreshing) return;
    setError(null);

    if (landing.itemType === 'vin') {
      const validation = validateVinInput(vinDraft);
      setVinValidation(validation);
      if (validation) return;

      const itemId = String(landing.nextAction?.request_item_id || '').trim();
      const expectedVersion = Number(
        info?.slice1_projection?.aggregate_version ??
          landing.nextAction?.version ??
          info?.task_contract_v1?.aggregate_version ??
          0,
      );
      if (!itemId || !info) {
        setError(mapH5ClaimError('submit_failed'));
        return;
      }

      const identity = ensureRequestItemCommandIdentity();
      const normalizedVin = normalizeVinInput(vinDraft);
      setSubmitting(true);
      try {
        const result = await submitH5RequestItem(taskToken, itemId, {
          command_id: identity.command_id,
          idempotency_key: identity.idempotency_key,
          expected_case_version: expectedVersion,
          client_draft_id: identity.command_id,
          fact: { field: 'vin', value: normalizedVin },
        });
        const outcome = String(result.outcome || '');
        if (outcome !== 'accepted' && outcome !== 'replayed') {
          setError(mapH5ClaimError(String(result.error_code || 'submit_failed')));
          return;
        }
        // Server receipt required — only advance on accepted/replayed projection.
        const projection = result.customer_projection || result.broker_projection;
        setInfo(applySlice1ProjectionToIntake(info, projection));
        requestItemCommandRef.current = null;
        setShowOverview(false);
        setVinValidation('');
      } catch (e) {
        const code = e instanceof Error ? e.message : 'submit_failed';
        // Keep command identity only for transport retries. Validation/conflict need a fresh intent.
        if (code !== 'network_error' && code !== 'submit_failed') {
          requestItemCommandRef.current = null;
        }
        if (code === 'version_conflict' || code === 'request_item_not_active' || code === 'illegal_state') {
          try {
            const refreshed = await fetchH5ClaimIntake(taskToken);
            setInfo(refreshed);
            landingRoutedRef.current = false;
          } catch {
            // keep submit error
          }
        }
        setError(mapH5ClaimError(code, '提交失败，请重试。如果仍失败，可以继续在微信里联系陈总。'));
        if (code === 'vin_invalid') {
          setVinValidation(mapH5ClaimError('vin_invalid'));
        }
      } finally {
        setSubmitting(false);
      }
      return;
    }

    if (!isCustomerSubmittableItemType(landing.itemType)) {
      setError(mapH5ClaimError('customer_submit_not_supported'));
      return;
    }

    const text = String(vinDraft || '').trim();
    setVinValidation(text ? '' : '请按陈总要求填写');
    if (text) {
      setError(mapH5ClaimError('customer_submit_not_supported'));
    }
  };

  const renderQaMarker = (marker: string | null) => {
    if (!marker) return null;
    return <div style={styles.qaMarker}>{marker}</div>;
  };

  const renderUnsupportedRequestItemScreen = () => {
    const progress = landing.progress;
    const progressText =
      progress.total > 0 ? `进度 ${progress.satisfied}/${progress.total}` : null;
    return (
      <>
        <div style={styles.card}>
          <div style={{ ...styles.statusPill, background: '#fff3cd', color: '#5c4a00' }}>
            暂不支持在线填写
          </div>
          <h2 style={{ ...styles.dashboardTitle, marginBottom: 8 }}>{landing.title}</h2>
          <p style={{ margin: '0 0 8px', fontSize: 15, lineHeight: 1.55, color: '#444' }}>
            {landing.instructions}
          </p>
          {progressText ? <p style={styles.progressLine}>{progressText}</p> : null}
        </div>
        <div style={styles.card}>
          <p style={{ margin: '0 0 12px', lineHeight: 1.6, color: '#444' }}>
            {mapH5ClaimError('customer_submit_not_supported')}
          </p>
          <button
            type="button"
            style={{ ...styles.btnSecondary, marginTop: 0 }}
            onClick={() => {
              void refreshStatus();
            }}
            disabled={refreshing}
          >
            {refreshing ? '刷新中…' : '刷新状态'}
          </button>
        </div>
      </>
    );
  };

  const renderRequestItemScreen = () => {
    const progress = landing.progress;
    const progressText =
      progress.total > 0 ? `进度 ${progress.satisfied}/${progress.total}` : '进度 0/1';
    const isVin = landing.itemType === 'vin';
    return (
      <>
        <div style={styles.card}>
          <div style={styles.statusPill}>需补充材料</div>
          <h2 style={{ ...styles.dashboardTitle, marginBottom: 8 }}>{landing.title}</h2>
          <p style={{ margin: '0 0 8px', fontSize: 15, lineHeight: 1.55, color: '#444' }}>
            {landing.instructions}
          </p>
          <p style={styles.progressLine}>{progressText}</p>
        </div>

        <div style={styles.card}>
          <label style={styles.label}>{isVin ? '车辆 VIN' : '补充说明'}</label>
          {isVin ? (
            <input
              style={styles.input}
              type="text"
              inputMode="text"
              autoCapitalize="characters"
              autoCorrect="off"
              spellCheck={false}
              maxLength={32}
              placeholder="请输入 17 位 VIN"
              value={vinDraft}
              onChange={(e) => {
                setVinDraft(e.target.value);
                if (vinValidation) setVinValidation('');
              }}
            />
          ) : (
            <textarea
              style={{ ...styles.input, minHeight: 100 }}
              placeholder="请按陈总要求填写"
              maxLength={2000}
              value={vinDraft}
              onChange={(e) => {
                setVinDraft(e.target.value);
                if (vinValidation) setVinValidation('');
              }}
            />
          )}
          {vinValidation ? <p style={styles.error}>{vinValidation}</p> : null}
          {error && error !== 'invalid_or_expired_task_link' ? (
            <p style={styles.error}>{error}</p>
          ) : null}
          <button
            type="button"
            style={{ ...styles.btn, ...(submitting ? styles.btnDisabled : {}) }}
            disabled={submitting}
            onClick={() => {
              void handleVinPrimary();
            }}
          >
            {submitting ? '提交中，请稍等…' : '提交给陈总'}
          </button>
          <button
            type="button"
            style={{ ...styles.btnSecondary, ...(submitting ? styles.btnDisabled : {}) }}
            disabled={submitting}
            onClick={() => setShowOverview(true)}
          >
            查看全部资料
          </button>
        </div>
      </>
    );
  };

  const renderSubmittedWaitingScreen = () => {
    const progress = landing.progress;
    const progressText =
      progress.total > 0 ? `进度 ${progress.satisfied}/${progress.total}` : null;
    return (
      <>
        <div style={styles.card}>
          <div style={{ ...styles.statusPill, background: '#e8f5e9', color: '#1b5e20' }}>
            已提交
          </div>
          <h2 style={{ ...styles.dashboardTitle, marginBottom: 8 }}>{landing.title}</h2>
          <p style={{ margin: '0 0 8px', fontSize: 16, lineHeight: 1.55, color: '#222' }}>
            {landing.instructions}
          </p>
          <p style={{ margin: '0 0 8px', fontSize: 14, lineHeight: 1.55, color: '#666' }}>
            {CAP3B_NO_APPROVAL_DISCLAIMER}
          </p>
          {progressText ? <p style={styles.progressLine}>{progressText}</p> : null}
        </div>
        <div style={styles.card}>
          <button
            type="button"
            style={{ ...styles.btnSecondary, marginTop: 0 }}
            onClick={() => {
              void refreshStatus();
            }}
            disabled={refreshing}
          >
            {refreshing ? '刷新中…' : '刷新状态'}
          </button>
        </div>
      </>
    );
  };

  if (landing.kind === 'loading') {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <p style={{ margin: 0 }}>加载中…</p>
        </div>
      </div>
    );
  }

  if (landing.kind === 'token_error') {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <h1 style={{ margin: 0, fontSize: 18 }}>链接已失效</h1>
        </div>
        <div style={styles.body}>
          <div style={styles.card}>
            <p>{mapH5ClaimError('invalid_or_expired_task_link')}</p>
          </div>
        </div>
        <div style={styles.footer}>此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。</div>
      </div>
    );
  }

  if (landing.kind === 'load_error' || landing.kind === 'projection_error') {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
          <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{landing.title}</h1>
          {renderQaMarker(landing.qaMarker)}
        </div>
        <div style={styles.body}>
          <div style={styles.card}>
            <p style={{ marginTop: 0, lineHeight: 1.55 }}>
              {mapH5ClaimError(landing.errorMessage, '暂时无法加载，请重试。')}
            </p>
            <button type="button" style={styles.btn} onClick={retryLoad} disabled={loading}>
              {loading ? '重试中…' : '重试'}
            </button>
          </div>
        </div>
        <div style={styles.footer}>此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。</div>
      </div>
    );
  }

  if (landing.kind === 'unsupported_request_item') {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
          <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{landing.title}</h1>
          {renderQaMarker(landing.qaMarker)}
        </div>
        <div style={styles.body}>{renderUnsupportedRequestItemScreen()}</div>
        <div style={styles.footer}>此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。</div>
      </div>
    );
  }

  if (landing.kind === 'submitted_waiting') {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
          <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{landing.title}</h1>
          {renderQaMarker(landing.qaMarker)}
        </div>
        <div style={styles.body}>{renderSubmittedWaitingScreen()}</div>
        <div style={styles.footer}>此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。</div>
      </div>
    );
  }

  const completion = info?.completion_summary;
  const dashboard = info?.dashboard_summary;
  const missingLabels =
    dashboard?.missing?.length
      ? dashboard.missing
      : completion?.missing?.length
        ? completion.missing
        : (info?.missing_info || []).map((m) => m.label).filter(Boolean);

  const handleDashboardPrimary = () => {
    if (!info) return;
    if (info.submitted) {
      if (info.upload_url) {
        window.open(info.upload_url as string, '_blank', 'noopener,noreferrer');
      }
      return;
    }
    if (step === 'done') {
      setStep('review');
      return;
    }
    if (step === 'start') {
      setStep('injury');
      return;
    }
    if (step === 'evidence' && (info.photo_count ?? 0) === 0 && info.upload_url) {
      window.open(info.upload_url as string, '_blank', 'noopener,noreferrer');
      return;
    }
    if (step === 'review') {
      void handleSubmit();
      return;
    }
  };

  const renderDashboard = () => {
    if (!dashboard) return null;
    return (
      <div style={styles.dashboard}>
        <h2 style={styles.dashboardTitle}>{dashboard.title}</h2>
        <p style={styles.dashboardSubtitle}>{dashboard.subtitle}</p>
        <div style={styles.dashboardStatus}>当前状态：{dashboard.status}</div>

        <p style={styles.sectionTitle}>已收到</p>
        {dashboard.received.length > 0 ? (
          <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0, marginBottom: 14 }}>
            {dashboard.received.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p style={{ margin: '0 0 14px', color: '#666' }}>等待您补充资料</p>
        )}

        <p style={styles.sectionTitle}>还缺</p>
        {dashboard.missing.length > 0 ? (
          <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0, marginBottom: 14, color: '#c0392b' }}>
            {dashboard.missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p style={{ margin: '0 0 14px', lineHeight: 1.6 }}>目前主要资料已收到</p>
        )}

        <p style={styles.sectionTitle}>下一步</p>
        <p style={{ margin: '0 0 14px', lineHeight: 1.6 }}>{dashboard.next_action}</p>

        <button
          type="button"
          style={{ ...styles.btn, ...(busy ? styles.btnDisabled : {}) }}
          disabled={busy}
          onClick={handleDashboardPrimary}
        >
          {dashboard.primary_cta}
        </button>
        {landing.kind === 'request_item' ? (
          <button
            type="button"
            style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
            disabled={busy}
            onClick={() => setShowOverview(false)}
          >
            返回当前任务
          </button>
        ) : (
          <button
            type="button"
            style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
            disabled={busy}
            onClick={() => {
              try {
                window.close();
              } catch {
                // ignore
              }
            }}
          >
            {dashboard.secondary_cta}
          </button>
        )}

        <p style={{ margin: '14px 0 0', fontSize: 13, lineHeight: 1.55, color: '#666' }}>
          {dashboard.warning}
        </p>
      </div>
    );
  };

  const showRequestItemFirst = landing.kind === 'request_item' && !showOverview;
  const showSecondaryOverviewOnly = landing.kind === 'request_item' && showOverview;
  const headerTitle = showRequestItemFirst
    ? landing.title
    : dashboard?.title || info?.title || '我的报案';

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
        <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{headerTitle}</h1>
        {renderQaMarker(landing.qaMarker)}
        {info && !dashboard && !showRequestItemFirst && (
          <div style={{ fontSize: 13, marginTop: 8, opacity: 0.9 }}>{progressLabel}</div>
        )}
      </div>

      <div style={styles.body}>
        {showRequestItemFirst ? (
          renderRequestItemScreen()
        ) : showSecondaryOverviewOnly ? (
          <>
            {renderDashboard()}
            {error && error !== 'invalid_or_expired_task_link' && (
              <div style={styles.error}>{error}</div>
            )}
          </>
        ) : (
          <>
            {renderDashboard()}
            {error && error !== 'invalid_or_expired_task_link' && (
              <div style={styles.error}>{error}</div>
            )}

            {step === 'start' && (
              <div style={styles.card}>
                <p>请先告诉陈总发生了什么。照片和证件不是现在必填；如需补充，陈总会再通知您。</p>
                <button
                  type="button"
                  style={{ ...styles.btn, ...(saving ? styles.btnDisabled : {}) }}
                  disabled={saving}
                  onClick={() => setStep('injury')}
                >
                  开始说明事故
                </button>
              </div>
            )}

            {step === 'injury' && (
              <div style={styles.card}>
                <p style={styles.label}>是否有人受伤？</p>
                {injury === 'yes' && (
                  <div style={styles.alert}>
                    如有人受伤且情况紧急，请先拨打 911，再继续填写。
                  </div>
                )}
                {(['no', 'yes', 'unknown'] as const).map((v) => (
                  <label key={v} style={{ display: 'block', marginBottom: 10 }}>
                    <input
                      type="radio"
                      name="injury"
                      value={v}
                      checked={injury === v}
                      onChange={() => setInjury(v)}
                    />{' '}
                    {v === 'no' ? '没有受伤' : v === 'yes' ? '有人受伤' : '不确定'}
                  </label>
                ))}
                <button
                  type="button"
                  style={{ ...styles.btn, ...(!injury || saving ? styles.btnDisabled : {}) }}
                  disabled={!injury || saving}
                  onClick={() =>
                    runSave('time_location', () =>
                      patchH5ClaimFields(taskToken, 'injury', { anyone_injured: injury }),
                    )
                  }
                >
                  {saving ? '保存中…' : '下一步'}
                </button>
              </div>
            )}

            {step === 'time_location' && (
              <div style={styles.card}>
                <label style={styles.label}>事故时间</label>
                <input
                  style={styles.input}
                  value={accidentDatetime}
                  onChange={(e) => setAccidentDatetime(e.target.value)}
                  placeholder="例如：今天上午 10:30"
                />
                <label style={styles.label}>事故地点</label>
                <input
                  style={styles.input}
                  value={accidentLocation}
                  onChange={(e) => setAccidentLocation(e.target.value)}
                  placeholder="城市 / 路口 / 停车场"
                />
                <button
                  type="button"
                  style={{
                    ...styles.btn,
                    ...(!accidentDatetime || accidentLocation.length < 3 || saving ? styles.btnDisabled : {}),
                  }}
                  disabled={!accidentDatetime || accidentLocation.length < 3 || saving}
                  onClick={() =>
                    runSave('story', () =>
                      patchH5ClaimFields(taskToken, 'time_location', {
                        accident_datetime: accidentDatetime,
                        accident_location: accidentLocation,
                      }),
                    )
                  }
                >
                  {saving ? '保存中…' : '下一步'}
                </button>
              </div>
            )}

            {step === 'story' && (
              <div style={styles.card}>
                <label style={styles.label}>事故经过</label>
                <textarea
                  style={{ ...styles.input, minHeight: 120 }}
                  value={accidentDescription}
                  onChange={(e) => setAccidentDescription(e.target.value)}
                  placeholder="例如：我停在红灯前，后车追尾撞上。请尽量写清楚谁先动、怎么撞的。"
                />
                <button
                  type="button"
                  style={{
                    ...styles.btn,
                    ...(accidentDescription.length < 10 || saving ? styles.btnDisabled : {}),
                  }}
                  disabled={accidentDescription.length < 10 || saving}
                  onClick={() =>
                    runSave('vehicle_other_party', () =>
                      patchH5ClaimFields(taskToken, 'story', {
                        accident_description: accidentDescription,
                      }),
                    )
                  }
                >
                  {saving ? '保存中…' : '下一步'}
                </button>
              </div>
            )}

            {step === 'vehicle_other_party' && (
              <div style={styles.card}>
                <p style={{ marginTop: 0, marginBottom: 12, fontSize: 14, color: '#666', lineHeight: 1.55 }}>
                  以下为选填。车辆 VIN / 证件资料如需补充，陈总会再单独请您提供。
                </p>
                <label style={styles.label}>您的车辆信息（选填）</label>
                <input
                  style={styles.input}
                  value={ownVehicle}
                  onChange={(e) => setOwnVehicle(e.target.value)}
                  placeholder="年份 / 品牌 / 车型（选填）"
                />
                <label style={styles.label}>对方车牌（选填）</label>
                <input
                  style={styles.input}
                  value={otherPartyPlate}
                  onChange={(e) => setOtherPartyPlate(e.target.value)}
                />
                <label style={styles.label}>对方信息（选填）</label>
                <input
                  style={styles.input}
                  value={otherPartyInfo}
                  onChange={(e) => setOtherPartyInfo(e.target.value)}
                  placeholder="保险公司 / 联系方式（选填）"
                />
                <button
                  type="button"
                  style={{
                    ...styles.btn,
                    ...(saving ? styles.btnDisabled : {}),
                  }}
                  disabled={saving}
                  onClick={() =>
                    runSave('evidence', () =>
                      patchH5ClaimFields(taskToken, 'vehicle_other_party', {
                        own_vehicle_info: ownVehicle,
                        other_party_plate: otherPartyPlate,
                        other_party_info: otherPartyInfo,
                      }),
                    )
                  }
                >
                  {saving ? '保存中…' : '下一步'}
                </button>
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(saving ? styles.btnDisabled : {}) }}
                  disabled={saving}
                  onClick={() => setStep('evidence')}
                >
                  跳过，继续
                </button>
              </div>
            )}

            {step === 'evidence' && info && (
              <div style={styles.card}>
                <p>
                  如有照片，请上传车损、现场、对方资料等。没有照片也可以先跳过。
                </p>
                <p style={styles.hint}>
                  当前照片：{photoCount > 0 ? `已上传 ${photoCount} 张` : '尚未上传'}
                </p>
                {info.upload_url ? (
                  <button
                    type="button"
                    style={{ ...styles.btn, ...(saving ? styles.btnDisabled : {}) }}
                    disabled={saving}
                    onClick={() => {
                      window.open(info.upload_url as string, '_blank', 'noopener,noreferrer');
                    }}
                  >
                    上传照片
                  </button>
                ) : (
                  <p style={{ fontSize: 14, color: '#666' }}>照片可通过上传入口补充</p>
                )}
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
                  disabled={busy}
                  onClick={() => refreshStatus()}
                >
                  {refreshing ? '刷新中…' : '刷新资料状态'}
                </button>
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(saving ? styles.btnDisabled : {}) }}
                  disabled={saving}
                  onClick={() => setStep('review')}
                >
                  暂时跳过，继续复核
                </button>
              </div>
            )}

            {step === 'review' && info && (
              <div style={styles.card}>
                <div style={styles.reviewWarning}>
                  还没有提交，返回微信不会把资料交给陈总。请先在下面点「提交给陈总审核」。
                </div>

                <div style={styles.submitBlock}>
                  <button
                    type="button"
                    style={{ ...styles.btnPrimarySubmit, ...(submitting ? styles.btnDisabled : {}) }}
                    disabled={submitting}
                    onClick={handleSubmit}
                  >
                    {submitting ? '提交中，请稍等…' : '提交给陈总审核'}
                  </button>
                  <p style={styles.submitSubtext}>
                    提交后，陈总会在工作台看到资料，你也会在微信收到「资料已提交」确认。
                  </p>
                </div>

                <h3 style={{ marginTop: 0 }}>请确认已填写内容</h3>
                <p style={styles.sectionTitle}>已填资料</p>
                <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0 }}>
                  <li>受伤：{injury === 'yes' ? '有人受伤' : injury === 'no' ? '没有受伤' : injury ? '不确定' : '—'}</li>
                  <li>时间：{accidentDatetime || '—'}</li>
                  <li>地点：{accidentLocation || '—'}</li>
                  <li>经过：{accidentDescription || '—'}</li>
                  <li>车辆：{ownVehicle || '—'}</li>
                  {(otherPartyPlate || otherPartyInfo) && (
                    <li>对方：{[otherPartyPlate, otherPartyInfo].filter(Boolean).join(' / ')}</li>
                  )}
                </ul>
                <p style={styles.sectionTitle}>照片</p>
                <p style={{ margin: '0 0 8px', lineHeight: 1.6 }}>
                  {photoCount > 0
                    ? `已上传 ${photoCount} 张`
                    : '尚未上传 — 可通过上传入口补充'}
                </p>
                {info.upload_url && (
                  <button
                    type="button"
                    style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
                    disabled={busy}
                    onClick={() => {
                      window.open(info.upload_url as string, '_blank', 'noopener,noreferrer');
                    }}
                  >
                    继续上传照片
                  </button>
                )}
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
                  disabled={busy}
                  onClick={() => refreshStatus()}
                >
                  {refreshing ? '刷新中…' : '刷新资料状态'}
                </button>
                <p style={styles.sectionTitle}>还缺什么</p>
                {missingLabels.length > 0 ? (
                  <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0, color: '#c0392b' }}>
                    {missingLabels.map((label) => (
                      <li key={label}>{label}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ margin: '0 0 8px', lineHeight: 1.6 }}>
                    目前主要资料已收到，陈总会进一步确认。
                  </p>
                )}
                <p style={{ margin: '12px 0 0', lineHeight: 1.6, fontSize: 13, color: '#666' }}>
                  这只是资料收集，不代表已经正式向保险公司报案。
                </p>
              </div>
            )}

            {step === 'done' && info && (
              <div style={styles.card}>
                <h2 style={{ marginTop: 0, color: '#0d3b66' }}>
                  {completion?.title || '已提交给陈总 ✅'}
                </h2>
                <p>{completion?.message || '你的事故资料已经提交给陈总审核。'}</p>

                <p style={styles.sectionTitle}>已收到</p>
                <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0 }}>
                  {(completion?.received || []).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>

                <p style={styles.sectionTitle}>还缺</p>
                {missingLabels.length > 0 ? (
                  <ul style={{ paddingLeft: 18, lineHeight: 1.7, marginTop: 0 }}>
                    {missingLabels.map((label) => (
                      <li key={label}>{label}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ margin: '0 0 8px', lineHeight: 1.6 }}>
                    {completion?.missing_clear_message || '目前主要资料已收到，陈总会进一步确认。'}
                  </p>
                )}

                <p style={styles.sectionTitle}>下一步</p>
                <p style={{ margin: '0 0 12px', lineHeight: 1.6 }}>
                  {completion?.next_step || '陈总会查看资料，如还需要补充，会通过微信联系你。'}
                </p>

                <p style={styles.sectionTitle}>提醒</p>
                <p style={{ margin: '0 0 16px', lineHeight: 1.6, fontSize: 14, color: '#666' }}>
                  {completion?.disclaimer || '这只是资料收集，不代表已经正式向保险公司报案。'}
                </p>

                {info.upload_url && (
                  <button
                    type="button"
                    style={{ ...styles.btn, ...(busy ? styles.btnDisabled : {}) }}
                    disabled={busy}
                    onClick={() => {
                      window.open(info.upload_url as string, '_blank', 'noopener,noreferrer');
                    }}
                  >
                    继续上传照片
                  </button>
                )}
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
                  disabled={busy}
                  onClick={() => refreshStatus()}
                >
                  {refreshing ? '刷新中…' : '刷新资料状态'}
                </button>
                <button
                  type="button"
                  style={{ ...styles.btnSecondary, ...(busy ? styles.btnDisabled : {}) }}
                  disabled={busy}
                  onClick={() => {
                    try {
                      window.close();
                    } catch {
                      // ignore
                    }
                  }}
                >
                  返回微信
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <div style={styles.footer}>
        {info?.safety_copy || '此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。'}
      </div>
    </div>
  );
}
