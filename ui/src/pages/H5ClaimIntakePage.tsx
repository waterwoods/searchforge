/**
 * P19H-3h-1A — Claim H5 structured intake wizard (mobile-first skeleton).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  fetchH5ClaimIntake,
  newSubmitIntentId,
  patchH5ClaimFields,
  submitH5ClaimIntake,
  type H5ClaimIntakeInfo,
} from '@/api/h5ClaimIntake';

type WizardStep = 'start' | 'injury' | 'time_location' | 'story' | 'vehicle_other_party' | 'review' | 'done';

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
  btnDisabled: { opacity: 0.55, cursor: 'not-allowed' } as const,
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
      setError(e instanceof Error ? e.message : 'save_failed');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    setSaving(true);
    setError(null);
    try {
      const data = await submitH5ClaimIntake(taskToken, submitIntentRef.current);
      setInfo(data);
      setStep('done');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'submit_failed');
    } finally {
      setSaving(false);
    }
  };

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
          <h1 style={{ margin: 0, fontSize: 18 }}>链接已过期</h1>
        </div>
        <div style={styles.body}>
          <div style={styles.card}>
            <p>请在微信回复「进度」获取新链接。</p>
          </div>
        </div>
        <div style={styles.footer}>此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。</div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={{ fontSize: 13, opacity: 0.85 }}>陈总办公室</div>
        <h1 style={{ margin: '4px 0 0', fontSize: 18 }}>{info?.title || '事故资料收集'}</h1>
        {info && <div style={{ fontSize: 13, marginTop: 8, opacity: 0.9 }}>{progressLabel}</div>}
      </div>

      <div style={styles.body}>
        {error && error !== 'invalid_or_expired_task_link' && (
          <div style={styles.error}>保存失败，请重试（{error}）</div>
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
                runSave('review', () =>
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

        {step === 'review' && info && (
          <div style={styles.card}>
            <h3 style={{ marginTop: 0 }}>请确认已填写内容</h3>
            <ul style={{ paddingLeft: 18, lineHeight: 1.7 }}>
              <li>受伤：{injury === 'yes' ? '有人受伤' : injury === 'no' ? '没有受伤' : '不确定'}</li>
              <li>时间：{accidentDatetime || '—'}</li>
              <li>地点：{accidentLocation || '—'}</li>
              <li>经过：{accidentDescription || '—'}</li>
              <li>车辆：{ownVehicle || '—'}</li>
            </ul>
            {info.missing_info.length > 0 && (
              <p style={{ color: '#c0392b', fontSize: 14 }}>
                还缺：{info.missing_info.map((m) => m.label).join('、')}
              </p>
            )}
            <button
              type="button"
              style={{ ...styles.btn, ...(saving ? styles.btnDisabled : {}) }}
              disabled={saving}
              onClick={handleSubmit}
            >
              {saving ? '提交中…' : '提交给陈总确认'}
            </button>
          </div>
        )}

        {step === 'done' && (
          <div style={styles.card}>
            <h2 style={{ marginTop: 0, color: '#0d3b66' }}>已提交给陈总 ✅</h2>
            <p>陈总会人工确认后会联系您。如有新材料可继续在微信补充。</p>
          </div>
        )}
      </div>

      <div style={styles.footer}>
        {info?.safety_copy || '此记录用于陈总办公室整理事故信息，不代表已向保险公司正式报案。'}
      </div>
    </div>
  );
}
