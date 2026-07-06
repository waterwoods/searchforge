/**
 * P19D-2 — H5 single-slot guided upload (Add Vehicle VIN photo only).
 * Mobile-first; one image, preview confirm, submit.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  fetchH5Task,
  uploadH5TaskImage,
  type H5TaskInfo,
  type H5UploadResult,
} from '@/api/h5TaskUpload';

type PageState = 'loading' | 'ready' | 'preview' | 'uploading' | 'success' | 'error';

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
  brand: {
    fontSize: 13,
    opacity: 0.85,
    marginBottom: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: 600,
    margin: 0,
  },
  body: {
    padding: '20px 16px 32px',
    maxWidth: 480,
    margin: '0 auto',
  },
  progress: {
    fontSize: 14,
    color: '#555',
    marginBottom: 16,
    textAlign: 'center' as const,
  },
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: '20px 16px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
    marginBottom: 16,
  },
  taskLabel: {
    fontSize: 17,
    fontWeight: 600,
    marginBottom: 8,
  },
  instruction: {
    fontSize: 14,
    lineHeight: 1.6,
    color: '#444',
    marginBottom: 16,
  },
  previewImg: {
    width: '100%',
    maxHeight: 280,
    objectFit: 'contain' as const,
    borderRadius: 8,
    background: '#eee',
    marginBottom: 16,
  },
  btn: {
    display: 'block',
    width: '100%',
    padding: '14px 16px',
    fontSize: 16,
    fontWeight: 600,
    border: 'none',
    borderRadius: 10,
    cursor: 'pointer',
    marginBottom: 10,
  },
  btnPrimary: {
    background: '#0d3b66',
    color: '#fff',
  },
  btnSecondary: {
    background: '#e8ecf0',
    color: '#333',
  },
  btnDisabled: {
    background: '#ccc',
    color: '#888',
    cursor: 'not-allowed',
  },
  progressDone: {
    fontSize: 14,
    color: '#0d6b2f',
    fontWeight: 600,
    marginBottom: 16,
    textAlign: 'center' as const,
  },
  successBox: {
    textAlign: 'center' as const,
    padding: '24px 8px',
  },
  successHeadline: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 12,
    color: '#0d6b2f',
  },
  errorBox: {
    background: '#fff3f3',
    border: '1px solid #f5c2c2',
    borderRadius: 10,
    padding: 16,
    color: '#a00',
    fontSize: 14,
    lineHeight: 1.5,
  },
  hiddenInput: {
    display: 'none',
  },
};

function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return '链接无效或已过期，请联系陈总重新获取。';
}

function tryReturnToWeChat(): void {
  const wx = (window as Window & { WeixinJSBridge?: { call: (cmd: string) => void } }).WeixinJSBridge;
  if (wx) {
    wx.call('closeWindow');
    return;
  }
  if (window.history.length > 1) {
    window.history.back();
    return;
  }
  window.close();
}

function progressLine(task: H5TaskInfo, pageState: PageState): string {
  if (pageState === 'success') {
    return `第 ${task.step_current} 步已完成 / 共 ${task.step_total} 步`;
  }
  return `第 ${task.step_current} 步 / 共 ${task.step_total} 步`;
}

export default function H5SingleSlotUploadPage() {
  const { taskToken } = useParams<{ taskToken: string }>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pageState, setPageState] = useState<PageState>('loading');
  const [task, setTask] = useState<H5TaskInfo | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<H5UploadResult | null>(null);
  const [errorText, setErrorText] = useState('');

  useEffect(() => {
    if (!taskToken) {
      setPageState('error');
      setErrorText('链接无效或已过期，请联系陈总重新获取。');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const info = await fetchH5Task(taskToken);
        if (cancelled) return;
        setTask(info);
        setPageState('ready');
      } catch (err) {
        if (cancelled) return;
        setErrorText(errorMessage(err));
        setPageState('error');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [taskToken]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    if (files.length > 1) {
      setErrorText('本步骤只能上传 1 张照片，请重新选择。');
      setPageState('error');
      return;
    }
    const file = files[0];
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    const url = URL.createObjectURL(file);
    setSelectedFile(file);
    setPreviewUrl(url);
    setPageState('preview');
    setErrorText('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [previewUrl]);

  const handleReselect = useCallback(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    setPageState('ready');
    setErrorText('');
  }, [previewUrl]);

  const handleSubmit = useCallback(async () => {
    if (!taskToken || !selectedFile) return;
    setPageState('uploading');
    setErrorText('');
    try {
      const result = await uploadH5TaskImage(taskToken, selectedFile);
      setUploadResult(result);
      setPageState('success');
    } catch (err) {
      setErrorText(errorMessage(err));
      setPageState('preview');
    }
  }, [taskToken, selectedFile]);

  const openFilePicker = () => fileInputRef.current?.click();

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.brand}>Chen Kui Insurance · 金盾保险资料补充</div>
        <h1 style={styles.title}>{task?.title || '加车资料补充'}</h1>
      </header>

      <main style={styles.body}>
        {task && pageState !== 'error' && pageState !== 'loading' && (
          <p style={pageState === 'success' ? styles.progressDone : styles.progress}>
            {progressLine(task, pageState)}
          </p>
        )}

        {pageState === 'loading' && (
          <div style={styles.card}>
            <p style={{ textAlign: 'center', color: '#666' }}>加载中…</p>
          </div>
        )}

        {pageState === 'error' && (
          <div style={styles.errorBox}>
            <strong>无法打开任务</strong>
            <p style={{ margin: '8px 0 0' }}>{errorText}</p>
          </div>
        )}

        {(pageState === 'ready' || pageState === 'preview' || pageState === 'uploading') && task && (
          <div style={styles.card}>
            <div style={styles.taskLabel}>{task.task_label}</div>
            <p style={styles.instruction}>{task.instruction}</p>

            {previewUrl && (
              <img src={previewUrl} alt="预览" style={styles.previewImg} />
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept={task.accept || 'image/jpeg,image/png,image/heic'}
              capture="environment"
              multiple={false}
              style={styles.hiddenInput}
              data-testid="h5-file-input"
              onChange={handleFileChange}
            />

            {pageState === 'ready' && (
              <button
                type="button"
                style={{ ...styles.btn, ...styles.btnPrimary }}
                onClick={openFilePicker}
              >
                选择 / 拍摄照片
              </button>
            )}

            {pageState === 'preview' && (
              <>
                <button
                  type="button"
                  style={{ ...styles.btn, ...styles.btnPrimary }}
                  onClick={handleSubmit}
                >
                  确认提交
                </button>
                <button
                  type="button"
                  style={{ ...styles.btn, ...styles.btnSecondary }}
                  onClick={handleReselect}
                >
                  重新选择
                </button>
              </>
            )}

            {pageState === 'uploading' && (
              <button type="button" style={{ ...styles.btn, ...styles.btnDisabled }} disabled>
                上传中…
              </button>
            )}

            <button
              type="button"
              style={{ ...styles.btn, ...styles.btnDisabled }}
              disabled
              title="后续版本开放"
            >
              暂时跳过 / 稍后补充
            </button>
          </div>
        )}

        {pageState === 'success' && uploadResult && task && (
          <div style={styles.card}>
            <div style={styles.successBox}>
              <p style={styles.successHeadline}>VIN 照片已收到 ✅</p>
              <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, color: '#1a1a1a' }}>
                第 {task.step_current} 步已完成
              </p>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: '#444' }}>
                {uploadResult.message_zh}
              </p>
              <p style={{ fontSize: 14, lineHeight: 1.6, color: '#666', marginTop: 12 }}>
                陈总会在 Workbench 中人工确认。
              </p>
              <button
                type="button"
                style={{ ...styles.btn, ...styles.btnPrimary, marginTop: 20 }}
                onClick={tryReturnToWeChat}
              >
                返回微信
              </button>
              <button
                type="button"
                style={{ ...styles.btn, ...styles.btnSecondary }}
                onClick={tryReturnToWeChat}
              >
                稍后继续
              </button>
            </div>
          </div>
        )}

        {pageState === 'preview' && errorText && (
          <div style={{ ...styles.errorBox, marginTop: 12 }} role="alert">
            <strong>上传未成功</strong>
            <p style={{ margin: '8px 0 0' }}>{errorText}</p>
          </div>
        )}

        {pageState === 'uploading' && errorText && (
          <div style={{ ...styles.errorBox, marginTop: 12 }} role="alert">
            <strong>上传未成功</strong>
            <p style={{ margin: '8px 0 0' }}>{errorText}</p>
          </div>
        )}
      </main>
    </div>
  );
}
