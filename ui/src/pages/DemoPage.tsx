import { useState } from 'react';
import { API_BASE_URL } from '../api/config';
import './DemoPage.css';

interface Source {
  doc_id: string;
  score: number;
  title: string;
  text: string;
  title_zh?: string;
  text_zh?: string;
  translations?: {
    zh?: {
      title: string;
      text: string;
    };
  };
  source_url: string;
}

interface QueryResponse {
  ok: boolean;
  sources: Source[];
  latency_ms?: number;
  trace_id?: string;
  question?: string;
  question_original?: string;
  question_used?: string;
  translation_applied?: boolean;
  detected_lang?: string;
}

export function DemoPage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [translateEnabled, setTranslateEnabled] = useState(false);
  const [expandedOriginals, setExpandedOriginals] = useState<Set<number>>(new Set());
  const [demoMode, setDemoMode] = useState(false);

  // Example questions
  const exampleQuestions = [
    "我刚买了新车，在加州最低需要买哪些保险？",
    "如果我出过一次事故，保费一般会涨多少？可以怎么降低？",
    "SR-22 是什么？什么情况下需要？"
  ];

  const handleExampleClick = (exampleQ: string) => {
    setQuestion(exampleQ);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setLatency(null);

    const startTime = performance.now();

    // Use Vite proxy in dev (relative path) or full URL in production
    // Vite proxy is configured to forward /api/* to http://localhost:8000
    const useProxy = !API_BASE_URL || API_BASE_URL.includes('localhost');
    const requestUrl = useProxy ? '/api/query' : `${API_BASE_URL}/api/query`;
    
    // Debug: Log API configuration
    console.log('[DemoPage] API_BASE_URL:', API_BASE_URL);
    console.log('[DemoPage] Using proxy:', useProxy);
    console.log('[DemoPage] Request URL:', requestUrl);
    console.log('[DemoPage] Request payload:', { question: question.trim(), top_k: 5 });

    try {
      const res = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          top_k: 5,
          translation_mode: translateEnabled ? 'auto' : undefined,
          mode: demoMode ? 'demo' : undefined,
        }),
      });

      console.log('[DemoPage] Response status:', res.status, res.statusText);
      console.log('[DemoPage] Response headers:', Object.fromEntries(res.headers.entries()));

      const endTime = performance.now();
      const requestLatency = Math.round(endTime - startTime);
      setLatency(requestLatency);

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `HTTP ${res.status}`);
      }

      const data: QueryResponse = await res.json();
      console.log('[DemoPage] Response data:', data);
      setResponse(data);
    } catch (err) {
      console.error('[DemoPage] Error details:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to query';
      console.error('[DemoPage] Error message:', errorMessage);
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setError(`Network error: ${errorMessage}. Check if backend is running at ${API_BASE_URL}`);
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="demo-container">
      <div className="demo-header">
        <h1>加州汽车保险智能助手（权威来源 Demo）</h1>
        <p>Ask questions about car insurance in California (中英文均可)</p>
        <p className="demo-source-note">数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面</p>
      </div>

      <form onSubmit={handleSubmit} className="demo-form">
        <div className="input-group">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="例如: 加州最低汽车保险要求是什么？"
            className="question-input"
            disabled={loading}
          />
          <button type="submit" className="ask-button" disabled={loading || !question.trim()}>
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </div>
        
        {/* Example Questions */}
        <div className="example-questions">
          <div className="example-questions-label">示例问题：</div>
          <div className="example-questions-buttons">
            {exampleQuestions.map((exampleQ, idx) => (
              <button
                key={idx}
                type="button"
                className="example-question-btn"
                onClick={() => handleExampleClick(exampleQ)}
                disabled={loading}
              >
                {exampleQ}
              </button>
            ))}
          </div>
        </div>

        <div className="demo-toggles">
          <div className="translation-toggle">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={translateEnabled}
                onChange={(e) => setTranslateEnabled(e.target.checked)}
                disabled={loading}
              />
              <span>Translate results to Chinese (中文显示)</span>
            </label>
          </div>
          <div className="demo-mode-toggle">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
                disabled={loading}
              />
              <span>演示模式（只使用权威来源）</span>
            </label>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">
          ❌ Error: {error}
        </div>
      )}

      {latency !== null && (
        <div className="latency-info">
          ⏱️ Request latency: {latency}ms
          {response?.latency_ms && ` (backend: ${Math.round(response.latency_ms)}ms)`}
          {response?.translation_applied && (
            <span className="translation-badge">🌐 Translation applied</span>
          )}
          {response?.detected_lang && response.detected_lang !== 'en' && (
            <span className="lang-badge">Language: {response.detected_lang.toUpperCase()}</span>
          )}
        </div>
      )}

      {response && response.ok && (
        <div className="results-container">
          <h2>Results ({response.sources?.length || 0})</h2>
          {response.sources && response.sources.length > 0 ? (
            <div className="sources-list">
              {response.sources.map((source, idx) => {
                // Prefer translated fields if available
                const displayTitle = source.title_zh || source.translations?.zh?.title || source.title || 'Untitled';
                const displayText = source.text_zh || source.translations?.zh?.text || source.text || 'No text available';
                const hasTranslation = !!(source.title_zh || source.text_zh || source.translations?.zh);
                const showOriginal = expandedOriginals.has(idx);
                
                return (
                  <div key={source.doc_id || idx} className="source-item">
                    <div className="source-header">
                      <span className="source-title">{displayTitle}</span>
                      <span className="source-score">Score: {source.score.toFixed(3)}</span>
                    </div>
                    {hasTranslation && translateEnabled && (
                      <div className="translation-indicator">
                        <span className="translation-label">中文翻译</span>
                        <button
                          className="show-original-btn"
                          onClick={() => {
                            const newExpanded = new Set(expandedOriginals);
                            if (showOriginal) {
                              newExpanded.delete(idx);
                            } else {
                              newExpanded.add(idx);
                            }
                            setExpandedOriginals(newExpanded);
                          }}
                        >
                          {showOriginal ? '隐藏原文' : '显示原文'}
                        </button>
                      </div>
                    )}
                    <div className="source-text">
                      {displayText}
                    </div>
                    {hasTranslation && translateEnabled && showOriginal && (
                      <div className="original-text">
                        <div className="original-label">Original (English):</div>
                        <div className="original-content">
                          <strong>{source.title}</strong>
                          <br />
                          {source.text}
                        </div>
                      </div>
                    )}
                    {source.source_url && (
                      <div className="source-url">
                        {(() => {
                          const urlObj = new URL(source.source_url);
                          const domain = urlObj.hostname;
                          const isOfficial = domain.includes('dmv.ca.gov') || 
                                           domain.includes('insurance.ca.gov') || 
                                           domain.includes('.gov') ||
                                           domain.includes('geico.com') ||
                                           domain.includes('progressive.com') ||
                                           domain.includes('statefarm.com');
                          return (
                            <>
                              <a href={source.source_url} target="_blank" rel="noopener noreferrer">
                                🔗 {source.source_url}
                              </a>
                              <span className="source-domain"> ({domain})</span>
                              {isOfficial && (
                                <span className="authoritative-badge">权威来源</span>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    )}
                    <div className="source-id">Doc ID: {source.doc_id}</div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="no-results">No results found.</div>
          )}
        </div>
      )}
    </div>
  );
}
