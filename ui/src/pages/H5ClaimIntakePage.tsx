/**
 * P19H-3h-1A — Claim H5 structured intake wizard (mobile-first skeleton).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  fetchH5ClaimIntake,
  mapH5ClaimError,
  newSubmitIntentId,
  patchH5ClaimFields,
  submitH5ClaimIntake,
  type H5ClaimIntakeInfo,
} from '@/api/h5ClaimIntake';

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
};

function stepFromInfo(info: H5ClaimIntakeInfo): WizardStep {
  if (info.submitted) return 'done';
  const cur = info.current_step as WizardStep;
  if (cur === 'start' || !cur) return 'start';
  return cur;
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
  const submitIntentRef = useRef<string>(newSubmitIntentId());

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
      try {
        const data = await fetchH5ClaimIntake(taskToken);
        if (cancelled) return;
        setInfo(data);
        hydrateFields(data);
        setStep(stepFromInfo(data));
      } catch (e) {
        if (!cancelled) {
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

  const busy = saving || submitting || refreshing;

  const photoCount = info?.photo_count ?? info?.attachment_count ?? 0;

  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.header}>
          <p style={{ margin: 0 }}>加载中…</p>
        </div>
      </div>
    );
  }

  if (error === 'invalid_or_expired_task_link') {
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

  const completion = info?.completion_summary;
  const missingLabels =
    completion?.missing?.length
      ? completion.missing
      : (info?.missing_info || []).map((m) => m.label).filter(Boolean);

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
        <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{info?.title || '事故资料收集'}</h1>
        {info && <div style={{ fontSize: 13, marginTop: 8, opacity: 0.9 }}>{progressLabel}</div>}
      </div>

      <div style={styles.body}>
        {error && error !== 'invalid_or_expired_task_link' && (
          <div style={styles.error}>{error}</div>
        )}

        {step === 'start' && (
          <div style={styles.card}>
            <p>我是陈总办公室的值班助手。请按步骤填写，陈总会人工确认。</p>
            <button
              type="button"
              style={{ ...styles.btn, ...(saving ? styles.btnDisabled : {}) }}
              disabled={saving}
              onClick={() => setStep('injury')}
            >
              开始填写
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
            <label style={styles.label}>您的车辆信息</label>
            <input
              style={styles.input}
              value={ownVehicle}
              onChange={(e) => setOwnVehicle(e.target.value)}
              placeholder="年份 / 品牌 / 车型"
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
              placeholder="保险公司 / 联系方式"
            />
            <button
              type="button"
              style={{
                ...styles.btn,
                ...(ownVehicle.length < 2 || saving ? styles.btnDisabled : {}),
              }}
              disabled={ownVehicle.length < 2 || saving}
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
      </div>

      <div style={styles.footer}>
        {info?.safety_copy || '此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。'}
      </div>
    </div>
  );
}
