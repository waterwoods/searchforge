/**
 * P3-B Slice 1 — Broker Workbench findability helpers (document-intake).
 * Prefer server workbench_list projection; fall back to local derivation.
 */

import type { SavedCase } from '@/api/inboxTriage';
import { resolveWorkbenchClientEnv } from '@/config/workbenchEnv';
import { shortCaseId } from './caseIdDisplay';

export type WorkbenchListProjection = {
  case_ref?: string | null;
  customer_display_name?: string | null;
  phone_last_four?: string | null;
  policy_suffix?: string | null;
  vehicle_summary?: string | null;
  qa_label?: string | null;
  is_test?: boolean;
  customer_current_action_label?: string | null;
  broker_next_action_label?: string | null;
  latest_meaningful_summary?: string | null;
  updated_at?: string | null;
  filter_bucket?: 'active' | 'waiting_customer' | 'waiting_broker' | string | null;
};

export type WorkbenchTestFilter = 'hide' | 'show' | 'only';
export type WorkbenchStatusFilter = 'all' | 'active' | 'waiting_customer' | 'waiting_broker';

const PLACEHOLDER_NAMES = new Set([
  '',
  'qa customer',
  'founder qa customer',
  'test customer',
  'wecom customer',
  '企业微信客户',
  '微信客户',
]);

export function getWorkbenchList(caseItem: SavedCase): WorkbenchListProjection {
  const wl = (caseItem as SavedCase & { workbench_list?: WorkbenchListProjection }).workbench_list;
  return wl && typeof wl === 'object' ? wl : {};
}

export function resolveCaseRef(caseItem: SavedCase): string {
  const fromList = String(getWorkbenchList(caseItem).case_ref || '').trim();
  if (fromList) return fromList;
  const top = String((caseItem as SavedCase & { case_ref?: string }).case_ref || '').trim();
  return top;
}

function phoneLastFour(phone?: string | null): string | null {
  const digits = String(phone || '').replace(/\D/g, '');
  if (digits.length < 4) return null;
  return digits.slice(-4);
}

function personLinkSuffix(caseItem: SavedCase): string | null {
  const key = String((caseItem as SavedCase & { person_link_key?: string | null }).person_link_key || '').trim();
  if (!key) return null;
  const alnum = key.replace(/[^A-Za-z0-9]/g, '');
  if (alnum.length >= 4) return alnum.slice(-4).toLowerCase();
  return key.slice(-4).toLowerCase();
}

function looksLikeTechnicalIdentity(name: string): boolean {
  const trimmed = name.trim();
  if (!trimmed) return false;
  const lower = trimmed.toLowerCase();
  if (lower.startsWith('wx_') || lower.startsWith('plk_') || lower.startsWith('sim_')) return true;
  if (lower.includes('openid')) return true;
  if (/^o[\w-]{20,}$/.test(trimmed)) return true;
  return false;
}

function isRealCustomerName(name: string): boolean {
  const trimmed = name.trim();
  if (!trimmed) return false;
  if (PLACEHOLDER_NAMES.has(trimmed.toLowerCase())) return false;
  if (trimmed.startsWith('微信客户 ·') || trimmed.startsWith('微信客户·')) return false;
  if (looksLikeTechnicalIdentity(trimmed)) return false;
  return true;
}

function identityFromCase(caseItem: SavedCase): Record<string, unknown> {
  const extra = (caseItem as SavedCase & { extra?: { customer_identity?: Record<string, unknown> } }).extra;
  const identity = extra?.customer_identity;
  return identity && typeof identity === 'object' ? identity : {};
}

export function resolveFindabilityCustomerName(caseItem: SavedCase): string {
  const fromList = String(getWorkbenchList(caseItem).customer_display_name || '').trim();
  if (fromList && !looksLikeTechnicalIdentity(fromList)) return fromList;

  const identity = identityFromCase(caseItem);
  for (const key of ['broker_manual_display_name', 'wecom_remark'] as const) {
    const remark = String(identity[key] || '').trim();
    if (isRealCustomerName(remark)) return remark.slice(0, 80);
  }

  const name = String(caseItem.customer_name || '').trim();
  if (isRealCustomerName(name)) return name;

  const nickname = String(identity.wecom_nickname || '').trim();
  if (isRealCustomerName(nickname)) return nickname.slice(0, 80);

  const suffix = personLinkSuffix(caseItem);
  if (suffix) return `微信客户 · ${suffix}`;
  const last4 = phoneLastFour(caseItem.customer_phone);
  if (last4) return `微信客户 · ${last4}`;
  return '微信客户';
}

export function resolveFindabilityPhoneLastFour(caseItem: SavedCase): string | null {
  const fromList = String(getWorkbenchList(caseItem).phone_last_four || '').trim();
  if (fromList) return fromList;
  return phoneLastFour(caseItem.customer_phone);
}

export function resolveQaLabel(caseItem: SavedCase): string | null {
  const fromList = String(getWorkbenchList(caseItem).qa_label || '').trim();
  if (fromList) return fromList;
  const facts = caseItem.known_facts || {};
  const label = String(facts.qa_label || '').trim();
  return label || null;
}

export function resolveIsTestCase(caseItem: SavedCase): boolean {
  const wl = getWorkbenchList(caseItem);
  if (typeof wl.is_test === 'boolean') return wl.is_test;
  return Boolean(caseItem.workbench_test || caseItem.p20_case_intake_projection?.is_test);
}

export function resolveVehicleContext(caseItem: SavedCase): string {
  const fromList = String(getWorkbenchList(caseItem).vehicle_summary || '').trim();
  if (fromList) return fromList;
  const facts = caseItem.known_facts || {};
  const fromFacts = String(facts.own_vehicle_info || facts.vehicle_summary || '').trim();
  if (fromFacts) return fromFacts;
  return String(caseItem.primary_vehicle_summary || '').trim();
}

export function resolveCurrentActionLabel(caseItem: SavedCase): string {
  // Broker Workbench list: prefer broker next action (what to do without opening).
  const idle = new Set(['暂无动作', '无动作', '—', '-']);
  const broker = String(getWorkbenchList(caseItem).broker_next_action_label || '').trim();
  if (broker && !idle.has(broker)) return broker;
  const fromList = String(getWorkbenchList(caseItem).customer_current_action_label || '').trim();
  if (fromList && !idle.has(fromList)) return fromList;
  const display = String(caseItem.display_status || '').trim();
  if (display && !['BROKER_REVIEW', 'READY', 'NEED_INFO', 'DONE', 'HOLDING'].includes(display.toUpperCase())) {
    return display;
  }
  const waiting = String(caseItem.waiting_on || '').trim().toLowerCase();
  if (waiting === 'client') return '等待客户补充';
  if (waiting === 'broker') return '等待办公室审核';
  return '打开案件核对';
}

export function resolveLatestSummary(caseItem: SavedCase): string {
  const fromList = String(getWorkbenchList(caseItem).latest_meaningful_summary || '').trim();
  if (fromList) return fromList;
  return String(caseItem.conversation_summary || caseItem.demo_summary || '').trim();
}

export function resolveFilterBucket(caseItem: SavedCase): WorkbenchStatusFilter | 'active' {
  const bucket = String(getWorkbenchList(caseItem).filter_bucket || '').trim();
  if (bucket === 'waiting_customer' || bucket === 'waiting_broker' || bucket === 'active') {
    return bucket;
  }
  return 'active';
}

export function defaultTestFilterForEnv(
  env = resolveWorkbenchClientEnv(),
): WorkbenchTestFilter {
  // Production Workbench hides TEST by default; QA/local show them.
  return env === 'production' ? 'hide' : 'show';
}

export function matchesWorkbenchSearch(caseItem: SavedCase, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const wl = getWorkbenchList(caseItem);
  const parts = [
    resolveCaseRef(caseItem),
    caseItem.case_id,
    shortCaseId(caseItem.case_id),
    resolveFindabilityCustomerName(caseItem),
    caseItem.customer_name,
    caseItem.customer_phone,
    resolveFindabilityPhoneLastFour(caseItem),
    wl.policy_suffix,
    caseItem.policy_number,
    resolveVehicleContext(caseItem),
    resolveQaLabel(caseItem),
    resolveLatestSummary(caseItem),
    resolveCurrentActionLabel(caseItem),
    wl.broker_next_action_label,
    wl.customer_current_action_label,
    (caseItem as SavedCase & { contact_note?: string | null }).contact_note,
  ]
    .map((v) => String(v || '').toLowerCase())
    .filter(Boolean);
  const blob = parts.join(' ');
  const digits = q.replace(/\D/g, '');
  if (digits && blob.replace(/\D/g, '').includes(digits)) return true;
  return blob.includes(q);
}

export function matchesWorkbenchFilters(
  caseItem: SavedCase,
  opts: { status: WorkbenchStatusFilter; testFilter: WorkbenchTestFilter },
): boolean {
  const isTest = resolveIsTestCase(caseItem);
  if (opts.testFilter === 'hide' && isTest) return false;
  if (opts.testFilter === 'only' && !isTest) return false;
  if (opts.status === 'all') return true;
  return resolveFilterBucket(caseItem) === opts.status;
}

/** Relative updated_at label for Workbench rows. */
export function formatRelativeUpdated(iso: string | null | undefined, nowMs = Date.now()): string {
  const raw = String(iso || '').trim();
  if (!raw) return '—';
  const t = Date.parse(raw);
  if (Number.isNaN(t)) return raw;
  const deltaSec = Math.max(0, Math.floor((nowMs - t) / 1000));
  if (deltaSec < 45) return '刚刚';
  if (deltaSec < 3600) return `${Math.floor(deltaSec / 60)}分钟前`;
  if (deltaSec < 86400) return `${Math.floor(deltaSec / 3600)}小时前`;
  if (deltaSec < 86400 * 7) return `${Math.floor(deltaSec / 86400)}天前`;
  try {
    return new Date(t).toLocaleString();
  } catch {
    return raw;
  }
}
