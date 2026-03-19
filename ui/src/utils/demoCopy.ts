/**
 * Copy demo answer + citations to clipboard for WeChat/客户分享
 */

export interface CopySource {
  domain: string;
  url: string;
}

const INSURER_DOMAINS = [
  'geico.com', 'progressive.com', 'usaa.com', 'nationwide.com',
  'libertymutual.com', 'travelers.com', 'allstate.com', 'aaa.com',
];

function isGovDomain(domain: string): boolean {
  const d = domain.toLowerCase();
  return d.endsWith('.ca.gov') || d.includes('dmv.ca.gov') || d.includes('insurance.ca.gov');
}

function isInsurerDomain(domain: string): boolean {
  const d = domain.toLowerCase();
  return INSURER_DOMAINS.some((ins) => d.includes(ins));
}

/** Short format: 1-line summary + 3 bullets + grouped links (官方来源/保险公司来源, max 3) */
export function buildCopyTextShort(
  question: string,
  answer: string,
  sources: CopySource[]
): string {
  const lines = answer
    ? answer
        .split(/\n+/)
        .map((line) => line.trim())
        .filter(Boolean)
    : [];
  const summary = lines[0] || '(检索结果见下方引用)';
  const bullets = lines.slice(1, 4).map((line) => `• ${line}`);
  const bulletBlock = bullets.length > 0 ? '\n' + bullets.join('\n') : '';

  const govLinks: string[] = [];
  const insurerLinks: string[] = [];
  const otherLinks: string[] = [];
  for (const s of sources) {
    if (!s.url) continue;
    const domain = s.domain || 'unknown';
    const link = `${domain}: ${s.url}`;
    if (isGovDomain(domain)) govLinks.push(link);
    else if (isInsurerDomain(domain)) insurerLinks.push(link);
    else otherLinks.push(link);
  }
  const allLinks = [...govLinks, ...insurerLinks, ...otherLinks].slice(0, 3);
  const linkBlock =
    allLinks.length > 0
      ? '\n\n【官方来源/保险公司来源】\n' + allLinks.map((l, i) => `${i + 1}) ${l}`).join('\n')
      : '';

  return `【问题】\n${question}\n\n【答案】\n${summary}${bulletBlock}${linkBlock}`;
}

/** Full format: question + full answer + up to 5 citations */
export function buildCopyTextFull(
  question: string,
  answer: string,
  sources: CopySource[]
): string {
  const lines: string[] = [];
  lines.push('【问题】');
  lines.push(question);
  lines.push('');
  lines.push('【答案】');
  lines.push(answer || '(检索结果见下方引用)');
  lines.push('');
  lines.push('【引用】');
  sources.slice(0, 5).forEach((s, i) => {
    lines.push(`${i + 1}) ${s.domain} - ${s.url}`);
  });
  return lines.join('\n');
}

/** Broker-only markers: exclude from client-ready copy. Extend when adding new broker-internal phrases. */
const BROKER_ONLY_MARKERS = ['经纪人可进一步询问', '经纪人下一步'] as const;

function containsBrokerOnly(text: string): boolean {
  return BROKER_ONLY_MARKERS.some((m) => text.includes(m));
}

/** Client-prep marker: extract and surface as dedicated "您可准备" section (client-facing tone) */
const CLIENT_PREP_MARKER = '客户可准备';

/** Client-ready format for WeChat: broker-friendly,可直接转发给客户 */
export function buildCopyTextClientReady(
  question: string,
  bullets: string[],
  steps: string[],
  sources: CopySource[]
): string {
  // Exclude broker-only content from client copy (客户可准备 is client-useful; 经纪人可进一步询问 is broker-internal)
  const clientBullets = bullets.filter((b) => !containsBrokerOnly(b));
  const clientSteps = steps.filter((s) => !containsBrokerOnly(s));

  // Extract 客户可准备 → surface as dedicated "您可准备" section (more natural for client)
  const prepFromBullets = clientBullets.filter((b) => b.includes(CLIENT_PREP_MARKER));
  const prepFromSteps = clientSteps.filter((s) => s.includes(CLIENT_PREP_MARKER));
  const clientPrepItems = [...prepFromBullets, ...prepFromSteps];
  const bulletsNoPrep = clientBullets.filter((b) => !b.includes(CLIENT_PREP_MARKER));
  const stepsNoPrep = clientSteps.filter((s) => !s.includes(CLIENT_PREP_MARKER));

  const lines: string[] = [];
  lines.push('【可直接转发给客户】');
  lines.push('');
  // 简短结论：第一句作为快速答复
  const quickAnswer = bulletsNoPrep[0] || clientBullets[0] || '';
  if (quickAnswer) {
    lines.push(quickAnswer);
    lines.push('');
  }
  // 补充要点（客户易懂，不含客户可准备，已移至下方）
  const extraBullets = bulletsNoPrep.slice(1, 3);
  if (extraBullets.length > 0) {
    extraBullets.forEach((b) => lines.push(`• ${b}`));
    lines.push('');
  }
  // 您可准备：dedicated section for what client should bring (natural client-facing phrasing)
  if (clientPrepItems.length > 0) {
    const prepText = clientPrepItems[0]
      .replace(/\*\*客户可准备\*\*[：:]\s*/g, '')
      .replace(/客户可准备[：:]\s*/g, '')
      .trim();
    if (prepText) {
      lines.push('您可准备：');
      lines.push(prepText);
      lines.push('');
    }
  }
  // 建议您：下一步建议（客户可操作）
  if (stepsNoPrep.length > 0) {
    lines.push('建议您：');
    stepsNoPrep.slice(0, 4).forEach((s, i) => lines.push(`${i + 1}. ${s}`));
    lines.push('');
  }
  // 官方链接（增强可信度）
  const govLinks = sources.filter((s) => isGovDomain(s.domain));
  const otherLinks = sources.filter((s) => !isGovDomain(s.domain));
  const top2 = [...govLinks, ...otherLinks].slice(0, 2);
  if (top2.length > 0) {
    lines.push('官方参考：');
    top2.forEach((s) => lines.push(s.url));
  }
  return lines.join('\n');
}

/** @deprecated Use buildCopyTextShort or buildCopyTextFull */
export function buildCopyText(
  question: string,
  answer: string,
  sources: CopySource[]
): string {
  return buildCopyTextFull(question, answer, sources);
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
