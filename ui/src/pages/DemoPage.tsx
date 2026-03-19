import { useState, useEffect, useCallback, useMemo } from 'react';
import { buildCopyTextShort, buildCopyTextFull, buildCopyTextClientReady, copyToClipboard } from '../utils/demoCopy';
import { DemoToast } from '../components/DemoToast';
import demoFallbackData from '../assets/demo_fallback.json';
import './DemoPage.css';

function detectScenario(q: string): 'newcar' | 'suspended' | 'license' | 'savings' | 'claims' | null {
  if (/新车|最低.*保险|最低保额|最低要求/.test(q)) return 'newcar';
  if (/暂停|恢复.*注册|注册.*暂停/.test(q)) return 'suspended';
  if (/查.*合规|经纪人|保险公司.*执照|insurance\.ca\.gov/.test(q)) return 'license';
  if (/省钱|保费|折扣|优惠/.test(q)) return 'savings';
  if (/理赔|出险|车祸/.test(q)) return 'claims';
  return null;
}

/** Scenario tag for broker workflow feel */
function getScenarioTag(scenario: 'newcar' | 'suspended' | 'license' | 'savings' | 'claims' | null): string | null {
  if (!scenario) return null;
  const tags: Record<string, string> = {
    newcar: '新车投保',
    suspended: '注册恢复',
    license: '合规查询',
    savings: '省钱/折扣',
    claims: '理赔流程',
  };
  return tags[scenario] || null;
}

/** Heuristic extraction: quickAnswer, bullets (3), steps from answer text. Fallback by scenario. */
function buildHighlights(answerText: string, question: string): { quickAnswer: string; bullets: string[]; steps: string[] } {
  const STEP_KEYWORDS = /步骤|建议|需要|提交|准备|前往|联系|支付|携带|查询|在线|官网/;
  const CHINESE_SPLIT = /[。；\n]+/;

  const fallbackNewCar: { bullets: string[]; steps: string[] } = {
    bullets: ['加州最低责任险：人身伤害 15,000/30,000，财产损失 5,000', '建议加保碰撞险和综合险保护新车', '可向多家保险公司询价比较'],
    steps: ['确认加州最低责任险要求', '让客户提供车辆/驾照信息', '给 2–3 套方案并附官方链接'],
  };
  const fallbackSuspended: { bullets: string[]; steps: string[] } = {
    bullets: ['注册暂停通常因保险失效或费用未缴', '需提交保险证明并缴纳恢复费（约 $14）', '可在 DMV 官网在线提交'],
    steps: ['确认暂停原因（保险/费用）', '按 DMV 指引提交保险证明/缴费', '记录确认号'],
  };
  const fallbackLicense: { bullets: string[]; steps: string[] } = {
    bullets: ['加州保险监管局 insurance.ca.gov 可查公司/经纪人执照', '执照查询入口：insurance.ca.gov → Check a License', '建议截图保存发给客户'],
    steps: ['打开 insurance.ca.gov/0200-industry/0008-check-license-status 查执照', '截图保存', '发给客户'],
  };
  const fallbackSavings: { bullets: string[]; steps: string[] } = {
    bullets: ['保费受驾驶记录、车型、里程、居住地等影响', '常见折扣：好司机、多车、学生、安全设备、续保忠诚度（各公司政策不同）', '客户可准备：当前保单、驾照、车辆信息、多车情况'],
    steps: ['收集客户驾驶/车辆信息', '客户可准备：当前保单、驾照、多车情况、学生证明（如有）', '推荐可申请折扣，提供 2–3 家报价对比'],
  };
  const fallbackClaims: { bullets: string[]; steps: string[] } = {
    bullets: ['一般流程：确保安全 → 报警（如需要）→ 联系保险公司报案 → 提交材料 → 定损 → 理赔', '建议客户保留现场照片、对方信息、保单号', '可在线或电话报案'],
    steps: ['安抚客户', '指导在线或电话报案', '协助准备材料（驾照、保单、事故说明）'],
  };

  const text = (answerText || '').trim();
  const scenario = detectScenario(question);

  // Extract bullets: first 3 meaningful sentences (10–60 chars)
  const rawParts = text ? text.split(CHINESE_SPLIT).map((s) => s.trim()).filter(Boolean) : [];
  const meaningful = rawParts.filter((p) => p.length >= 10 && p.length <= 120);
  const deduped: string[] = [];
  for (const p of meaningful) {
    if (deduped.some((d) => d.includes(p) || p.includes(d))) continue;
    deduped.push(p);
  }
  const bullets = deduped.slice(0, 3);

  // Extract steps: lines containing step keywords
  const lines = text ? text.split(/\n+/).map((s) => s.trim()).filter(Boolean) : [];
  const stepLines = lines.filter((l) => STEP_KEYWORDS.test(l));
  let steps = stepLines.slice(0, 5).map((s) => s.replace(/^[•\-\d.)、]+/, '').trim()).filter(Boolean);

  // Ensure 客户可准备 is always surfaced when present (COPY_TO_CLIENT needs it for 您可准备)
  const CLIENT_PREP = /客户可准备/;
  const hasPrepInSteps = steps.some((s) => CLIENT_PREP.test(s));
  if (!hasPrepInSteps && CLIENT_PREP.test(text)) {
    const prepLine = lines.find((l) => CLIENT_PREP.test(l));
    if (prepLine) {
      const cleaned = prepLine.replace(/^[•\-\d.)、]+/, '').trim();
      if (cleaned) steps = [...steps, cleaned];
    }
  }

  // Fallback if extraction insufficient
  if (bullets.length < 2 || steps.length < 2) {
    const fb = scenario === 'newcar' ? fallbackNewCar
      : scenario === 'suspended' ? fallbackSuspended
      : scenario === 'license' ? fallbackLicense
      : scenario === 'savings' ? fallbackSavings
      : scenario === 'claims' ? fallbackClaims
      : null;
    if (fb) {
      const b = bullets.length >= 2 ? bullets : fb.bullets;
      const s = steps.length >= 2 ? steps : fb.steps;
      return { quickAnswer: b[0] || '', bullets: b, steps: s };
    }
  }

  if (bullets.length < 2) {
    bullets.push(...meaningful.slice(bullets.length, 3 - bullets.length));
  }
  if (steps.length < 2 && scenario) {
    const fb = scenario === 'newcar' ? fallbackNewCar : scenario === 'suspended' ? fallbackSuspended : scenario === 'license' ? fallbackLicense : scenario === 'savings' ? fallbackSavings : fallbackClaims;
    steps.push(...fb.steps.slice(steps.length, 3 - steps.length));
  }

  const b = bullets.slice(0, 3);
  // Preserve 客户可准备 when added beyond first 5 (do not slice it off)
  const s = steps.some((x) => CLIENT_PREP.test(x)) ? steps : steps.slice(0, 5);
  return { quickAnswer: b[0] || '', bullets: b, steps: s };
}

interface FallbackItem {
  question: string;
  answer: string;
  sources: { domain: string; url: string; snippet: string }[];
}

/** Default offline pack when demo_fallback.json is empty or missing. Ensures demo works with no backend.
 *  Must include 客户可准备 + 经纪人可进一步询问 for broker workflow alignment (see BROKER_DEMO_QUALITY_STANDARD). */
const DEFAULT_FALLBACK_ITEMS: FallbackItem[] = [
  {
    question: '我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？',
    answer: '加州最低责任险：人身伤害 15,000/30,000，财产损失 5,000。建议加保碰撞险和综合险保护新车。可向多家保险公司询价比较。\n\n**客户可准备**：车辆信息、驾照、VIN（如有）。\n\n**经纪人可进一步询问**：车型、用途、预算、是否贷款、是否需加保碰撞/综合险。\n\n**经纪人下一步**：确认客户车辆/驾照信息，给出 2–3 套方案并附官方链接。',
    sources: [
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/', snippet: 'California minimum liability insurance requirements for vehicle registration.' },
      { domain: 'insurance.ca.gov', url: 'https://www.insurance.ca.gov/', snippet: 'California Department of Insurance - consumer information.' },
    ],
  },
  {
    question: '我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？',
    answer: '注册暂停通常因保险失效或费用未缴。需提交保险证明并缴纳恢复费（约 $14）。可在 DMV 官网在线提交。\n\n**客户可准备**：保险证明、驾照、DMV 通知函。\n\n**经纪人可进一步询问**：暂停原因（保险失效/费用）、是否已续保、当前保单号。\n\n**经纪人下一步**：确认暂停原因，引导客户至 DMV 在线提交保险证明并缴费（约 $14）。',
    sources: [
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/vehicle-registration/insurance-requirements/suspended-vehicle-registration/', snippet: 'Vehicle Registration Suspension - submit proof of insurance, pay reinstatement fee.' },
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/', snippet: 'California DMV portal for vehicle registration services.' },
    ],
  },
  {
    question: '客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？',
    answer: '加州保险监管局 insurance.ca.gov 可查公司/经纪人执照。执照查询入口：Check a License。输入公司名或执照号即可查询。建议截图保存发给客户。\n\n**客户可准备**：公司/经纪人名称或执照号。\n\n**经纪人可进一步询问**：客户要查的是公司还是个人、是否有执照号，可引导至 insurance.ca.gov 查执照。\n\n**经纪人下一步**：打开 insurance.ca.gov 查执照，截图保存发给客户。',
    sources: [
      { domain: 'insurance.ca.gov', url: 'https://www.insurance.ca.gov/0200-industry/0008-check-license-status/index.cfm', snippet: 'California Department of Insurance - Check a License for agents and brokers.' },
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/', snippet: 'California DMV official portal.' },
    ],
  },
  {
    question: '客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？',
    answer: '保费受驾驶记录、车型、里程、居住地等影响。常见折扣：好司机、多车、学生、安全设备、续保忠诚度（各公司政策不同）。建议让客户提供信息，多家比价。\n\n**客户可准备**：当前保单、驾照、车辆信息、多车情况。\n\n**经纪人可进一步询问**：驾驶记录、多车、学生证明，推荐可申请折扣。\n\n**经纪人下一步**：收集客户信息，推荐可申请折扣，提供 2–3 家报价对比。',
    sources: [
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/', snippet: 'California DMV - vehicle and driver information.' },
      { domain: 'insurance.ca.gov', url: 'https://www.insurance.ca.gov/', snippet: 'California Department of Insurance - consumer guides.' },
    ],
  },
  {
    question: '出险后理赔流程是怎样的？',
    answer: '一般流程：确保安全 → 报警（如需要）→ 联系保险公司报案 → 提交事故信息与材料 → 定损 → 理赔。建议客户保留现场照片、对方信息、保单号。\n\n**客户可准备**：保单号、驾照、事故说明、现场照片、对方信息。\n\n**经纪人可进一步询问**：事故时间、人员伤亡、是否已报警、保单号，指导在线或电话报案。\n\n**经纪人下一步**：安抚客户，指导在线或电话报案，协助准备材料。',
    sources: [
      { domain: 'dmv.ca.gov', url: 'https://www.dmv.ca.gov/portal/', snippet: 'California DMV - accident reporting requirements.' },
      { domain: 'insurance.ca.gov', url: 'https://www.insurance.ca.gov/', snippet: 'California Department of Insurance - claims information.' },
    ],
  },
];

const INSURER_DOMAINS = [
  'geico.com', 'progressive.com', 'usaa.com', 'nationwide.com',
  'libertymutual.com', 'travelers.com', 'aaa.com', 'allstate.com', 'farmers.com',
];

function getDomainBadge(domain: string): 'GOV' | 'INSURER' | 'OTHER' {
  if (!domain) return 'OTHER';
  const lower = domain.toLowerCase();
  if (lower.endsWith('.gov') || lower.includes('ca.gov') || lower.includes('dmv.ca.gov') || lower.includes('insurance.ca.gov')) {
    return 'GOV';
  }
  if (INSURER_DOMAINS.some(d => lower.includes(d))) return 'INSURER';
  return 'OTHER';
}

function getDomainFromUrl(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return '';
  }
}

interface Source {
  doc_id: string;
  score: number;
  title: string;
  text: string;
  snippet?: string;
  title_zh?: string;
  text_zh?: string;
  domain?: string;
  translations?: {
    zh?: { title: string; text: string };
  };
  source_url?: string;
  url?: string;
}

interface QueryResponse {
  ok: boolean;
  sources: Source[];
  answer?: string;
  latency_ms?: number;
  trace_id?: string;
  question?: string;
  question_original?: string;
  question_used?: string;
  translation_applied?: boolean;
  detected_lang?: string;
}

interface ScenarioQuestion {
  q: string;
  brokerUse: string;
}

interface Scenario {
  label: string;
  questions: ScenarioQuestion[];
}

const SAMPLE_QUESTIONS: ScenarioQuestion[] = [
  {
    q: '我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？',
    brokerUse: '新车投保：快速给客户权威答复 + 官方链接',
  },
  {
    q: '我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？',
    brokerUse: '注册恢复：DMV 流程 + 材料清单',
  },
  {
    q: '客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？',
    brokerUse: '合规查询：insurance.ca.gov 执照验证',
  },
  {
    q: '客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？',
    brokerUse: '续保挽留：省钱因素与折扣说明',
  },
  {
    q: '出险后理赔流程是怎样的？',
    brokerUse: '理赔指导：步骤与材料准备',
  },
];

const SCENARIOS: Scenario[] = [
  {
    label: '新车投保/最低要求',
    questions: [
      { q: '我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？', brokerUse: '用于快速给客户一个权威答复 + 贴官方链接' },
      { q: '加州汽车保险最低保额要求是多少？', brokerUse: '快速回答合规问题' },
      { q: '新车注册需要什么保险证明？', brokerUse: '指导客户准备注册材料' },
    ],
  },
  {
    label: '续保/如何省钱/折扣',
    questions: [
      { q: '客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？', brokerUse: '介绍省钱技巧与折扣' },
      { q: '续保时如何降低保费？', brokerUse: '续保客户挽留话术' },
      { q: '多车折扣、好司机折扣怎么申请？', brokerUse: '推荐可申请的折扣' },
    ],
  },
  {
    label: '出险/理赔流程',
    questions: [
      { q: '出险后理赔流程是怎样的？', brokerUse: '安抚客户并说明步骤' },
      { q: '车祸后应该先做什么？', brokerUse: '紧急情况指导' },
      { q: '理赔需要准备哪些材料？', brokerUse: '协助客户准备材料' },
    ],
  },
  {
    label: '注册/无保险后果/暂停恢复',
    questions: [
      { q: '我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？', brokerUse: '用于快速给客户一个权威答复 + 贴官方链接' },
      { q: '如果我没有保险或者保险中断，会有什么后果？怎么恢复车辆注册？', brokerUse: '解释无保险风险与恢复流程' },
      { q: 'SR-22 是什么？什么时候需要？', brokerUse: '解释高风险客户所需文件' },
    ],
  },
  {
    label: '资质/合规查询',
    questions: [
      { q: '客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？', brokerUse: '用于快速给客户一个权威答复 + 贴官方链接' },
    ],
  },
];

export function DemoPage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [demoMode, setDemoMode] = useState(true);
  const [translateEnabled, setTranslateEnabled] = useState(true);
  const [expandedOriginals, setExpandedOriginals] = useState<Set<number>>(new Set());
  const [copyStatus, setCopyStatus] = useState<'idle' | 'success' | 'fail'>('idle');
  const [copyMessage, setCopyMessage] = useState('');
  const [expandedScenario, setExpandedScenario] = useState<number | null>(null);
  const [showRefreshInstructions, setShowRefreshInstructions] = useState(false);
  const [citationsExpanded, setCitationsExpanded] = useState(false);
  const [expandedSnippets, setExpandedSnippets] = useState<Set<number>>(new Set());

  // Status bar state (must be declared before useOfflineFallback)
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [backendLatency, setBackendLatency] = useState<number | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [translationStatus, setTranslationStatus] = useState<'ON' | 'OFF' | 'Unknown'>('Unknown');
  const [citationsStatus, setCitationsStatus] = useState<'OK' | 'Missing' | 'Unknown'>('Unknown');

  // Offline fallback: use when backend down or request failed. Never empty - use default if JSON missing.
  const loadedItems = (demoFallbackData as { items?: FallbackItem[] })?.items ?? [];
  const fallbackData = loadedItems.length >= 3 ? loadedItems : DEFAULT_FALLBACK_ITEMS;
  const useOfflineFallback = backendConnected === false || (!!error && !response);

  const healthUrl = '/healthz';

  const checkBackend = useCallback(async () => {
    setBackendError(null);
    try {
      const start = performance.now();
      const res = await fetch(healthUrl, { method: 'GET' });
      const ms = Math.round(performance.now() - start);
      setBackendLatency(ms);
      setBackendConnected(res.ok);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setBackendError(data.detail || `HTTP ${res.status}`);
      }
    } catch (err) {
      setBackendConnected(false);
      setBackendLatency(null);
      setBackendError(err instanceof Error ? err.message : 'Network error');
    }
  }, [healthUrl]);

  useEffect(() => {
    checkBackend();
    const t = setInterval(checkBackend, 15000);
    return () => clearInterval(t);
  }, [checkBackend]);

  useEffect(() => {
    if (response) {
      setTranslationStatus(
        response.translation_applied === true || response.sources?.some(s => s.text_zh || s.title_zh)
          ? 'ON'
          : response.translation_applied === false ? 'OFF' : 'Unknown'
      );
      const withUrlDomain = response.sources?.filter(s => {
        const url = s.source_url || s.url || '';
        const domain = s.domain || getDomainFromUrl(url);
        return url && domain;
      }) ?? [];
      setCitationsStatus(withUrlDomain.length >= 2 ? 'OK' : 'Missing');
    }
  }, [response]);

  const runQuery = useCallback((q: string) => {
    setQuestion(q);
    setError(null);
    setResponse(null);
    setLatency(null);
    setLoading(true);

    const requestUrl = '/api/query';
    const startTime = performance.now();

    fetch(requestUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: q.trim(),
        top_k: 5,
        mode: 'demo',
        translation_mode: 'auto',
        generate_answer: true,
      }),
    })
      .then(async (res) => {
        const requestLatency = Math.round(performance.now() - startTime);
        setLatency(requestLatency);
        if (!res.ok) {
          const errData = await res.json().catch(() => ({ detail: { error: 'Unknown error' } }));
          const errMsg = errData?.detail?.error ?? errData?.error ?? `HTTP ${res.status}`;
          throw new Error(errMsg);
        }
        return res.json();
      })
      .then((data: QueryResponse) => setResponse(data))
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Failed to query';
        if (err instanceof TypeError && msg.includes('fetch')) {
          setError(`Network error: ${msg}. 请确认后端已启动`);
        } else if (msg === 'embedding_warming' || msg.includes('embedding_warming')) {
          setError('即时检索暂时不可用。请直接点击上方 5 个推荐问题，使用预设演示答案继续。');
        } else {
          setError(msg);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleScenarioQuestionClick = (sq: ScenarioQuestion) => {
    if (useOfflineFallback) {
      const item = fallbackData.find((i) => i.question === sq.q)
        ?? DEFAULT_FALLBACK_ITEMS.find((i) => i.question === sq.q);
      if (item) {
        // Use DEFAULT_FALLBACK_ITEMS answer when item.answer is empty (e.g. snapshot ran without LLM)
        const defaultItem = DEFAULT_FALLBACK_ITEMS.find((d) => d.question === sq.q);
        const answer = (item.answer?.trim() || defaultItem?.answer || '').trim();
        setQuestion(sq.q);
        setError(null);
        setLatency(null);
        setResponse({
          ok: true,
          sources: item.sources.map((s, idx) => ({
            doc_id: `fallback-${idx}`,
            score: 1,
            title: s.domain || 'Source',
            text: s.snippet,
            snippet: s.snippet,
            domain: s.domain,
            source_url: s.url,
            url: s.url,
          })),
          answer: answer || undefined,
          question: sq.q,
        });
        return;
      }
    }
    runQuery(sq.q);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    runQuery(question.trim());
  };

  const handleCopyShort = async () => {
    if (!response?.ok || !response.sources?.length) return;
    const answer = response.answer || response.sources
      .map(s => s.text_zh || s.translations?.zh?.text || s.text)
      .filter(Boolean)
      .slice(0, 2)
      .join('\n\n') || '(检索结果见下方引用)';
    const q = response.question || response.question_original || question;
    const sources = response.sources.map(s => {
      const url = s.source_url || s.url || '';
      const domain = s.domain || getDomainFromUrl(url);
      return { domain: domain || '(unknown)', url };
    }).filter(s => s.url);
    const text = buildCopyTextShort(q, answer, sources);
    const ok = await copyToClipboard(text);
    setCopyStatus(ok ? 'success' : 'fail');
    setCopyMessage(ok ? 'Copied (Short)' : 'Copy failed');
    setTimeout(() => { setCopyStatus('idle'); setCopyMessage(''); }, 2000);
  };

  const handleCopyFull = async () => {
    if (!response?.ok || !response.sources?.length) return;
    const answer = response.answer || response.sources
      .map(s => s.text_zh || s.translations?.zh?.text || s.text)
      .filter(Boolean)
      .slice(0, 2)
      .join('\n\n') || '(检索结果见下方引用)';
    const q = response.question || response.question_original || question;
    const sources = response.sources.map(s => {
      const url = s.source_url || s.url || '';
      const domain = s.domain || getDomainFromUrl(url);
      return { domain: domain || '(unknown)', url };
    }).filter(s => s.url);
    const text = buildCopyTextFull(q, answer, sources);
    const ok = await copyToClipboard(text);
    setCopyStatus(ok ? 'success' : 'fail');
    setCopyMessage(ok ? 'Copied (Full)' : 'Copy failed');
    setTimeout(() => { setCopyStatus('idle'); setCopyMessage(''); }, 2000);
  };

  const expandAllExcerpts = () => {
    if (!response?.sources?.length) return;
    setExpandedSnippets(new Set(response.sources.map((_, i) => i)));
  };

  const collapseAllExcerpts = () => {
    setExpandedSnippets(new Set());
  };

  const sources = response?.sources ?? [];
  const hasAnswer = !!(response?.answer?.trim());
  const answerForHighlights = response?.answer?.trim()
    || sources.map((s) => s.text_zh || s.translations?.zh?.text || s.text).filter(Boolean).slice(0, 2).join('\n\n')
    || '';
  const qForHighlights = response?.question || response?.question_original || question;
  const highlights = useMemo(
    () => buildHighlights(answerForHighlights, qForHighlights),
    [answerForHighlights, qForHighlights]
  );
  const scenarioTag = useMemo(
    () => getScenarioTag(detectScenario(qForHighlights)),
    [qForHighlights]
  );

  const handleCopyClientReady = async () => {
    if (!response?.ok) return;
    const q = response.question || response.question_original || question;
    const srcs = sources.map((s) => {
      const url = s.source_url || s.url || '';
      const domain = s.domain || getDomainFromUrl(url);
      return { domain: domain || '(unknown)', url };
    }).filter((s) => s.url);
    const text = buildCopyTextClientReady(q, highlights.bullets, highlights.steps, srcs);
    const ok = await copyToClipboard(text);
    setCopyStatus(ok ? 'success' : 'fail');
    setCopyMessage(ok ? '已复制（可直接发微信）' : '复制失败');
    setTimeout(() => { setCopyStatus('idle'); setCopyMessage(''); }, 2000);
  };

  const toggleSnippet = (idx: number) => {
    setExpandedSnippets((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const visibleSources = citationsExpanded ? sources : sources.slice(0, 2);

  return (
    <div className="demo-container">
      {/* Status Bar */}
      <div className="demo-status-bar">
        <span className={`status-mode-badge status-mode-${useOfflineFallback ? 'offline' : 'live'}`}>
          {useOfflineFallback ? 'Offline' : 'Live'}
        </span>
        <span className="status-item">
          Backend:{' '}
          <span className={backendConnected === true ? 'status-ok' : backendConnected === false ? 'status-fail' : 'status-unknown'}>
            {backendConnected === true ? 'Connected' : backendConnected === false ? 'Disconnected' : '...'}
          </span>
        </span>
        {backendLatency !== null && backendConnected && (
          <span className="status-item">Latency: {backendLatency}ms</span>
        )}
        <span className="status-item">
          Translation:{' '}
          <span className={translationStatus === 'ON' ? 'status-ok' : translationStatus === 'OFF' ? 'status-fail' : 'status-unknown'}>
            {translationStatus}
          </span>
        </span>
        <span className="status-item">
          Citations:{' '}
          <span className={citationsStatus === 'OK' ? 'status-ok' : citationsStatus === 'Missing' ? 'status-fail' : 'status-unknown'}>
            {citationsStatus}
          </span>
        </span>
        {demoMode && (
          <span className="status-demo-mode">演示模式 ON</span>
        )}
      </div>

      {backendConnected === false && backendError && (
        <div className="demo-backend-error">
          <span>Backend unreachable: {backendError}</span>
          <button type="button" className="demo-retry-btn" onClick={checkBackend}>
            Retry
          </button>
        </div>
      )}

      {useOfflineFallback && (
        <div className="demo-offline-banner">
          <span className="demo-offline-badge">演示模式（预设答案）</span>
          <span className="demo-offline-hint">
            即时检索暂不可用。请点击上方推荐问题加载预设答案，演示可正常进行。
          </span>
          <button
            type="button"
            className="demo-refresh-pack-btn"
            onClick={() => setShowRefreshInstructions(true)}
            title="How to refresh offline pack"
          >
            刷新离线包
          </button>
        </div>
      )}

      {showRefreshInstructions && (
        <div className="demo-instructions-overlay" onClick={() => setShowRefreshInstructions(false)}>
          <div className="demo-instructions-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Refresh Offline Pack</h3>
            <p>Run this command (backend must be running):</p>
            <code>python3 scripts/snapshot_demo_answers.py</code>
            <button type="button" className="demo-close-btn" onClick={() => setShowRefreshInstructions(false)}>
              Close
            </button>
          </div>
        </div>
      )}

      <div className="demo-header">
        <h1>加州汽车保险经纪助手</h1>
        <p className="demo-value-prop">帮经纪快速回答客户问题，附官方 / 权威来源链接，可直接发微信</p>
        <p className="demo-source-note">数据来源：加州 DMV / 加州保险监管机构 / 主流保险公司官方页面 · 中英文均可提问</p>
      </div>

      {/* Recommended questions (broker-focused, click to answer) */}
      <div className="demo-sample-questions">
        <div className="demo-sample-label">推荐问题（经纪常用，点击即答）：</div>
        {SAMPLE_QUESTIONS.map((sq, idx) => (
          <div key={idx} className="demo-sample-item">
            <button
              type="button"
              className="demo-sample-btn"
              onClick={() => handleScenarioQuestionClick(sq)}
              disabled={loading}
            >
              {sq.q}
            </button>
            <div className="demo-sample-broker-use">{sq.brokerUse}</div>
          </div>
        ))}
      </div>

      {/* Scenario buttons above input */}
      <div className="demo-scenarios">
        <div className="demo-scenarios-label">场景（点击展开问题）：</div>
        <div className="demo-scenarios-buttons">
          {SCENARIOS.map((scenario, idx) => (
            <div key={idx} className="scenario-group">
              <button
                type="button"
                className={`scenario-btn ${expandedScenario === idx ? 'scenario-btn-active' : ''}`}
                onClick={() => setExpandedScenario(expandedScenario === idx ? null : idx)}
                disabled={loading}
              >
                {scenario.label}
              </button>
              {expandedScenario === idx && (
                <div className="scenario-questions">
                  {scenario.questions.map((sq, qidx) => (
                    <div key={qidx} className="scenario-question-item">
                      <button
                        type="button"
                        className="scenario-question-btn"
                        onClick={() => handleScenarioQuestionClick(sq)}
                        disabled={loading}
                      >
                        {sq.q}
                      </button>
                      <div className="scenario-broker-use">{sq.brokerUse}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
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
        <div className="error-message">❌ Error: {error}</div>
      )}

      {latency !== null && (
        <div className="latency-info">
          ⏱️ Request latency: {latency}ms
          {response?.latency_ms && ` (backend: ${Math.round(response.latency_ms)}ms)`}
          {response?.translation_applied && (
            <span className="translation-badge">🌐 Translation applied</span>
          )}
        </div>
      )}

      <DemoToast
        message={copyMessage || (copyStatus === 'success' ? 'Copied' : copyStatus === 'fail' ? 'Copy failed' : '')}
        type={copyStatus === 'success' ? 'success' : 'fail'}
        visible={copyStatus !== 'idle'}
      />

      {response && response.ok && (
        <div className="results-container">
          {/* A) Answer Panel - broker-useful structure: 简短结论 → 权威依据 → 下一步 → 可直接转发 */}
          {(hasAnswer || sources.length > 0) && (
            <div className="answer-panel">
              {scenarioTag && (
                <span className="answer-panel-tag">{scenarioTag}</span>
              )}
              <h2 className="answer-panel-headline">简短结论</h2>
              {highlights.quickAnswer && (
                <div className="answer-panel-quick">{highlights.quickAnswer}</div>
              )}
              <div className="answer-panel-bullets">
                {highlights.bullets.slice(1).map((b, i) => (
                  <div key={i} className="answer-panel-bullet">• {b}</div>
                ))}
              </div>
              {sources.length > 0 && (
                <div className="answer-panel-sources">
                  <span className="answer-panel-sources-label">官方/权威依据：</span>
                  {sources
                    .slice(0, 2)
                    .map((s) => s.domain || getDomainFromUrl(s.source_url || s.url || ''))
                    .filter(Boolean)
                    .join('、')}
                </div>
              )}
              <div className="answer-panel-steps">
                <div className="answer-panel-steps-label">下一步建议</div>
                {highlights.steps.map((s, i) => (
                  <div key={i} className="answer-panel-step">{i + 1}. {s}</div>
                ))}
              </div>
              <div className="answer-panel-copy">
                <button
                  type="button"
                  className="copy-client-ready-btn"
                  onClick={handleCopyClientReady}
                >
                  复制给客户（可直接发微信）
                </button>
              </div>
            </div>
          )}

          {hasAnswer && (
            <div className="answer-section">
              <h2>答案</h2>
              {(() => {
                const ans = response.answer || '';
                const brokerIdx = ans.indexOf('**客户可准备**');
                if (brokerIdx >= 0) {
                  const main = ans.slice(0, brokerIdx).trim();
                  const broker = ans.slice(brokerIdx).trim();
                  return (
                    <>
                      <div className="answer-text">{main}</div>
                      <div className="answer-broker-workflow">
                        <span className="answer-broker-workflow-label">经纪人工作流</span>
                        <div className="answer-text answer-broker-workflow-content">{broker}</div>
                      </div>
                    </>
                  );
                }
                return <div className="answer-text">{ans}</div>;
              })()}
            </div>
          )}

          {/* C) Citations - secondary, scannable */}
          <div className="sources-header">
            <h2>权威依据（可展开）</h2>
            <div className="copy-buttons-group">
              <button
                type="button"
                className="copy-wechat-btn copy-btn-short"
                onClick={handleCopyShort}
                disabled={sources.length === 0}
              >
                Copy (Short)
              </button>
              <button
                type="button"
                className="copy-wechat-btn copy-btn-full"
                onClick={handleCopyFull}
                disabled={sources.length === 0}
              >
                Copy (Full)
              </button>
            </div>
          </div>

          {sources.length > 0 && (
            <div className="citations-controls">
              {sources.length > 2 && (
                <button
                  type="button"
                  className="citations-expand-more-btn"
                  onClick={() => setCitationsExpanded(!citationsExpanded)}
                >
                  {citationsExpanded ? '收起' : `展开更多(共${sources.length}条)`}
                </button>
              )}
              <button type="button" className="citations-expand-btn" onClick={expandAllExcerpts}>
                Open all excerpts
              </button>
              <button type="button" className="citations-collapse-btn" onClick={collapseAllExcerpts}>
                Collapse all
              </button>
            </div>
          )}

          {sources.length > 0 ? (
            <div className="sources-cards">
              {visibleSources.map((source, idx) => {
                const displayTitle = source.title_zh || source.translations?.zh?.title || source.title || (source.domain || getDomainFromUrl(source.source_url || source.url || '') || 'Untitled');
                const excerpt = source.snippet || source.text_zh || source.translations?.zh?.text || source.text || 'No excerpt.';
                const url = source.source_url || source.url || '';
                const domain = source.domain || getDomainFromUrl(url);
                const badge = getDomainBadge(domain);
                const showOriginal = expandedOriginals.has(idx);
                const showSnippet = expandedSnippets.has(idx);
                const hasTranslation = !!(source.title_zh || source.text_zh || source.translations?.zh);

                return (
                  <div key={source.doc_id || idx} className="source-card">
                    <div className="source-card-header">
                      <span className={`source-badge source-badge-inline source-badge-${badge}`}>{badge}</span>
                      <span className="source-title">{displayTitle || domain}</span>
                    </div>
                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer" className="source-link source-link-block">
                        {url}
                      </a>
                    )}
                    <div className="source-excerpt-section">
                      <button
                        type="button"
                        className="show-excerpt-btn"
                        onClick={() => toggleSnippet(idx)}
                      >
                        {showSnippet ? '收起摘要' : '展开摘要'}
                      </button>
                      {showSnippet && (
                        <div className="source-excerpt">
                          {excerpt}
                        </div>
                      )}
                    </div>
                    {hasTranslation && translateEnabled && (
                      <div className="translation-indicator">
                        <button
                          className="show-original-btn"
                          onClick={() => {
                            const next = new Set(expandedOriginals);
                            if (showOriginal) next.delete(idx);
                            else next.add(idx);
                            setExpandedOriginals(next);
                          }}
                        >
                          {showOriginal ? '隐藏原文' : '显示原文'}
                        </button>
                      </div>
                    )}
                    {showOriginal && hasTranslation && (
                      <div className="original-text">
                        <strong>{source.title}</strong>
                        <br />
                        {source.text}
                      </div>
                    )}
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
