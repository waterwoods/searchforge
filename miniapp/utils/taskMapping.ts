import type { CustomerTask, NextAction } from "../types/task";

const FIELD_LABELS: Record<string, string> = {
  anyone_injured: "是否有人受伤",
  injury_status: "是否有人受伤",
  accident_datetime: "事故时间",
  accident_location: "事故地点",
  accident_description: "事故经过",
  own_vehicle_info: "您的车辆信息",
  other_party_plate: "对方车牌",
  other_party_info: "对方信息",
  customer_damage_photo: "事故照片",
  other_party_vehicle_photo: "事故照片",
  scene_photo: "事故现场照片",
  photos: "事故照片",
  police_involved: "是否报警",
  police_reported: "是否报警",
};

export type MissingItemAction =
  | "ACTIONABLE_NOW"
  | "DISPLAY_ONLY_PROTOTYPE"
  | "COMPLETED"
  | "UNSUPPORTED";

export type MissingItemNav = {
  action: MissingItemAction;
  route?: string;
  statusText: string;
  hint?: string;
};

export type SupplementTaskRow = {
  key: string;
  label: string;
  statusText: string;
  actionable: boolean;
  route?: string;
  hint?: string;
};

const PHOTO_KEYS = new Set([
  "customer_damage_photo",
  "other_party_vehicle_photo",
  "scene_photo",
  "photos",
]);

const BASICS_KEYS = new Set([
  "anyone_injured",
  "injury_status",
  "police_involved",
  "police_reported",
  "accident_datetime",
  "accident_location",
  "own_vehicle_info",
]);

const UNSUPPORTED_KEYS = new Set([
  "other_party_plate",
  "other_party_info",
]);

const ACTIONABLE_ROUTES: Record<string, string> = {
  accident_description: "/pages/story/story",
  anyone_injured: "/pages/basics/basics",
  injury_status: "/pages/basics/basics",
  police_involved: "/pages/basics/basics",
  police_reported: "/pages/basics/basics",
  accident_datetime: "/pages/basics/basics",
  accident_location: "/pages/basics/basics",
  own_vehicle_info: "/pages/basics/basics",
  customer_damage_photo: "/pages/photos/photos",
  other_party_vehicle_photo: "/pages/photos/photos",
  scene_photo: "/pages/photos/photos",
  photos: "/pages/photos/photos",
};

/** Known section route for a missing-item key (after alias normalize). */
export function routeForMissingKey(rawKey: string): string | undefined {
  const key = normalizeMissingKey(rawKey);
  if (!key) return undefined;
  return ACTIONABLE_ROUTES[key] || ACTIONABLE_ROUTES[rawKey];
}

/**
 * Map a server-listed missing item to a UI row.
 * If the contract/checklist still lists the field, keep an edit path even when
 * local facts look complete (e.g. client treats "unknown" as filled while
 * backend still reports the item missing). Does not change submit-ready rules.
 */
export function mapServerMissingItem(
  item: { key?: string; field?: string; label?: string },
  task: CustomerTask,
): SupplementTaskRow | null {
  const rawKey = String(item.key || item.field || "").trim();
  const label = missingItemLabel(item);
  if (!rawKey && !label) return null;

  const nav = resolveMissingItemNav(rawKey, task);
  const key = rawKey || normalizeMissingKey(rawKey) || label;
  const route = nav.route || routeForMissingKey(rawKey);

  if (nav.action === "DISPLAY_ONLY_PROTOTYPE" || nav.action === "UNSUPPORTED") {
    return {
      key,
      label,
      statusText: nav.statusText,
      actionable: false,
      route: undefined,
      hint: nav.hint,
    };
  }

  if (nav.action === "COMPLETED") {
    if (!route) return null;
    return {
      key,
      label,
      statusText: nav.statusText || "待确认",
      actionable: true,
      route,
    };
  }

  return {
    key,
    label,
    statusText: nav.statusText,
    actionable: nav.action === "ACTIONABLE_NOW" && Boolean(route),
    route,
    hint: nav.hint,
  };
}

const INTAKE_STEPS_BEFORE_REVIEW = [
  "injury",
  "time_location",
  "story",
  "vehicle_other_party",
] as const;

export function maskToken(token: string): string {
  const t = (token || "").trim();
  if (t.length <= 12) return "h5t1…";
  return `${t.slice(0, 8)}…`;
}

export function extractTokenFromUrl(url: string): string {
  const raw = (url || "").trim();
  if (!raw) return "";
  const withoutQuery = raw.split("?")[0];
  const segment = withoutQuery.split("/").filter(Boolean).pop() || "";
  if (segment.startsWith("h5t1.")) return segment;
  return "";
}

export function missingItemLabel(item: { key?: string; field?: string; label?: string }): string {
  if (item.label) return item.label;
  const key = item.key || item.field || "";
  return FIELD_LABELS[key] || key || "待补充资料";
}

export function storyComplete(task: CustomerTask): boolean {
  const desc = String(task.key_facts?.accident_description || "").trim();
  return desc.length >= 10;
}

export function basicsComplete(task: CustomerTask): boolean {
  const facts = task.key_facts || {};
  const injury = String(facts.anyone_injured || facts.injury_status || "").trim();
  const hasInjury = ["yes", "no", "unknown"].includes(injury.toLowerCase());
  const hasTime = Boolean(String(facts.accident_datetime || "").trim());
  const hasLocation = Boolean(String(facts.accident_location || "").trim());
  const hasVehicle = String(facts.own_vehicle_info || "").trim().length >= 2;
  return hasInjury && hasTime && hasLocation && hasVehicle;
}

export function photoCount(task: CustomerTask): number {
  return Number(task.photo_count ?? task.attachment_count ?? 0);
}

export function prototypePhotoTarget(): number {
  return 2;
}

export function photosSatisfiedForPrototype(task: CustomerTask): boolean {
  return photoCount(task) >= prototypePhotoTarget();
}

export function isSubmitted(task: CustomerTask): boolean {
  return Boolean(task.submitted || task.current_step === "done");
}

export function isBrokerDonePhase(phase: string): boolean {
  return phase === "broker_done";
}

export function isNeedsMoreInfoPhase(phase: string): boolean {
  return phase === "broker_needs_more_info";
}

export function normalizeMissingKey(key: string): string {
  const raw = (key || "").trim();
  if (raw === "anyone_injured") return "injury_status";
  if (raw === "police_reported") return "police_involved";
  if (PHOTO_KEYS.has(raw)) return "photos";
  return raw;
}

export type ReviewSupplementAction = {
  route: string;
  label: string;
};

/** Deterministic page order when multiple missing items are actionable. */
const SUPPLEMENT_ROUTE_PRIORITY = [
  "/pages/story/story",
  "/pages/basics/basics",
  "/pages/photos/photos",
] as const;

/** Customer-facing CTA copy for a known supplement route (no internal jargon). */
export function supplementCtaLabelForRoute(route: string): string {
  const path = String(route || "").trim();
  if (path.includes("/pages/basics/basics")) return "去补充基本资料";
  if (path.includes("/pages/story/story")) return "去填写事故经过";
  if (path.includes("/pages/photos/photos")) return "去补充事故照片";
  return "去补充资料";
}

/**
 * Central supplement router: first actionable missing-item page.
 * Multiple Basics-related items collapse to one Basics route.
 * Submitted status must not block this — only formal re-submit is blocked.
 */
export function resolveSupplementAction(
  missingItems: Array<{ actionable?: boolean; route?: string }>,
): ReviewSupplementAction | null {
  const routes = missingItems
    .filter((item) => Boolean(item?.actionable) && Boolean(item?.route))
    .map((item) => String(item.route).trim())
    .filter(Boolean);
  if (!routes.length) return null;

  const uniqueRoutes = Array.from(new Set(routes));
  const route =
    SUPPLEMENT_ROUTE_PRIORITY.find((candidate) => uniqueRoutes.includes(candidate)) ||
    uniqueRoutes[0];
  return {
    route,
    label: supplementCtaLabelForRoute(route),
  };
}

/** @deprecated Prefer resolveSupplementAction — kept for existing Review call sites. */
export function resolveReviewSupplementAction(
  missingItems: Array<{ actionable?: boolean; route?: string }>,
): ReviewSupplementAction | null {
  return resolveSupplementAction(missingItems);
}

function injuryComplete(task: CustomerTask): boolean {
  const v = String(
    task.key_facts?.anyone_injured || task.key_facts?.injury_status || "",
  )
    .trim()
    .toLowerCase();
  return ["yes", "no", "unknown"].includes(v);
}

function injuryStatusText(task: CustomerTask): string {
  const v = String(
    task.key_facts?.anyone_injured || task.key_facts?.injury_status || "",
  )
    .trim()
    .toLowerCase();
  if (v === "yes") return "有人受伤";
  if (v === "no") return "没有受伤";
  if (v === "unknown") return "不确定";
  return "未填写";
}

function policeComplete(task: CustomerTask): boolean {
  const v = String(task.key_facts?.police_involved || "")
    .trim()
    .toLowerCase();
  return ["yes", "no", "unknown"].includes(v);
}

function policeStatusText(task: CustomerTask): string {
  const v = String(task.key_facts?.police_involved || "")
    .trim()
    .toLowerCase();
  if (v === "yes") return "已经报警";
  if (v === "no") return "没有报警";
  if (v === "unknown") return "不确定";
  return "未填写";
}

function photoStatusText(task: CustomerTask): string {
  const count = photoCount(task);
  if (count === 0) return "未添加";
  const target = prototypePhotoTarget();
  if (count >= target) return `${count} 张`;
  return `${count}/${target} 张`;
}

export function resolveMissingItemNav(
  rawKey: string,
  task: CustomerTask,
): MissingItemNav {
  const key = normalizeMissingKey(rawKey);

  if (key === "accident_description") {
    if (storyComplete(task)) {
      return { action: "COMPLETED", statusText: "已填写" };
    }
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.accident_description,
      statusText: "未填写",
    };
  }

  if (key === "injury_status") {
    if (injuryComplete(task)) {
      return { action: "COMPLETED", statusText: injuryStatusText(task) };
    }
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.injury_status,
      statusText: "未填写",
    };
  }

  if (key === "police_involved") {
    if (policeComplete(task)) {
      return { action: "COMPLETED", statusText: policeStatusText(task) };
    }
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.police_involved,
      statusText: "未填写",
    };
  }

  if (key === "accident_datetime") {
    const value = String(task.key_facts?.accident_datetime || "").trim();
    if (value) return { action: "COMPLETED", statusText: value };
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.accident_datetime,
      statusText: "未填写",
    };
  }

  if (key === "accident_location") {
    const value = String(task.key_facts?.accident_location || "").trim();
    if (value) return { action: "COMPLETED", statusText: value };
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.accident_location,
      statusText: "未填写",
    };
  }

  if (key === "own_vehicle_info") {
    const value = String(task.key_facts?.own_vehicle_info || "").trim();
    if (value.length >= 2) return { action: "COMPLETED", statusText: "已填写" };
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.own_vehicle_info,
      statusText: "未填写",
    };
  }

  if (key === "photos" || PHOTO_KEYS.has(key)) {
    if (photosSatisfiedForPrototype(task)) {
      return { action: "COMPLETED", statusText: photoStatusText(task) };
    }
    return {
      action: "ACTIONABLE_NOW",
      route: ACTIONABLE_ROUTES.photos,
      statusText: photoStatusText(task),
    };
  }

  if (UNSUPPORTED_KEYS.has(key)) {
    return {
      action: "DISPLAY_ONLY_PROTOTYPE",
      statusText: "暂不支持",
      hint: "请联系陈总补充",
    };
  }

  const route = ACTIONABLE_ROUTES[key];
  if (route) {
    return { action: "ACTIONABLE_NOW", route, statusText: "待补充" };
  }

  return {
    action: "UNSUPPORTED",
    statusText: "待确认",
    hint: "请联系陈总",
  };
}

type ChecklistItem = {
  key: string;
  label: string;
  isComplete: (task: CustomerTask) => boolean;
  statusText: (task: CustomerTask) => string;
  route: string;
};

const SUPPLEMENT_CHECKLIST: ChecklistItem[] = [
  {
    key: "accident_description",
    label: "事故经过",
    isComplete: storyComplete,
    statusText: (task) => (storyComplete(task) ? "已填写" : "未填写"),
    route: "/pages/story/story",
  },
  {
    key: "injury_status",
    label: "是否受伤",
    isComplete: injuryComplete,
    statusText: injuryStatusText,
    route: "/pages/basics/basics",
  },
  {
    key: "police_involved",
    label: "是否报警",
    isComplete: policeComplete,
    statusText: policeStatusText,
    route: "/pages/basics/basics",
  },
  {
    key: "accident_datetime",
    label: "事故时间",
    isComplete: (task) => Boolean(String(task.key_facts?.accident_datetime || "").trim()),
    statusText: (task) =>
      String(task.key_facts?.accident_datetime || "").trim() || "未填写",
    route: "/pages/basics/basics",
  },
  {
    key: "accident_location",
    label: "事故地点",
    isComplete: (task) => Boolean(String(task.key_facts?.accident_location || "").trim()),
    statusText: (task) =>
      String(task.key_facts?.accident_location || "").trim() || "未填写",
    route: "/pages/basics/basics",
  },
  {
    key: "own_vehicle_info",
    label: "您的车辆",
    isComplete: (task) =>
      String(task.key_facts?.own_vehicle_info || "").trim().length >= 2,
    statusText: (task) =>
      String(task.key_facts?.own_vehicle_info || "").trim().length >= 2
        ? "已填写"
        : "未填写",
    route: "/pages/basics/basics",
  },
  {
    key: "photos",
    label: "事故照片",
    isComplete: photosSatisfiedForPrototype,
    statusText: photoStatusText,
    route: "/pages/photos/photos",
  },
];

export function buildSupplementRows(task: CustomerTask): SupplementTaskRow[] {
  const rows: SupplementTaskRow[] = [];
  const seen = new Set<string>();

  for (const item of SUPPLEMENT_CHECKLIST) {
    if (item.isComplete(task)) continue;
    // Submitted status must not block supplement editing — only formal re-submit is blocked.
    seen.add(item.key);
    rows.push({
      key: item.key,
      label: item.label,
      statusText: item.statusText(task),
      actionable: true,
      route: item.route,
    });
  }

  for (const item of task.missing_info || []) {
    const key = normalizeMissingKey(item.key || item.field || "");
    if (!key || seen.has(key)) continue;
    const row = mapServerMissingItem(item, task);
    if (!row) continue;
    seen.add(row.key);
    rows.push(row);
  }

  return rows;
}

export function firstActionableMissingRoute(task: CustomerTask): string | undefined {
  const row = buildSupplementRows(task).find((item) => item.actionable && item.route);
  return row?.route;
}

export function progressPercent(task: CustomerTask): number {
  const total = Math.max(task.step_total || 1, 1);
  const done = Math.min(task.completed_count || 0, total);
  return Math.round((done / total) * 100);
}

function stepIncomplete(task: CustomerTask, step: string): boolean {
  const facts = task.key_facts || {};
  if (step === "injury") {
    const v = String(facts.anyone_injured || facts.injury_status || "").trim().toLowerCase();
    return !["yes", "no", "unknown"].includes(v);
  }
  if (step === "time_location") {
    return (
      !String(facts.accident_datetime || "").trim() ||
      !String(facts.accident_location || "").trim()
    );
  }
  if (step === "story") {
    return !storyComplete(task);
  }
  if (step === "vehicle_other_party") {
    return String(facts.own_vehicle_info || "").trim().length < 2;
  }
  return false;
}

export function firstIncompleteBasicsStep(task: CustomerTask): string | null {
  for (const step of INTAKE_STEPS_BEFORE_REVIEW) {
    if (step === "story") continue;
    if (stepIncomplete(task, step)) return step;
  }
  return null;
}

export function resolveNextAction(task: CustomerTask): NextAction {
  const dash = task.dashboard_summary;
  const submitted = isSubmitted(task);
  const supplementRoute = firstActionableMissingRoute(task);

  if (submitted || task.current_step === "done") {
    if (supplementRoute) {
      return {
        kind: "supplement",
        primaryCta: "继续补充资料",
        route: supplementRoute,
      };
    }
    return {
      kind: "receipt",
      primaryCta: "查看提交结果",
      route: "/pages/receipt/receipt",
    };
  }

  if (isBrokerDonePhase(task.phase)) {
    return {
      kind: "done",
      primaryCta: "查看完成状态",
      route: "/pages/receipt/receipt",
    };
  }

  if (isNeedsMoreInfoPhase(task.phase)) {
    return {
      kind: "supplement",
      primaryCta: "补充陈总需要的资料",
      route: supplementRoute || "/pages/photos/photos",
    };
  }

  if (!storyComplete(task)) {
    return {
      kind: "story",
      primaryCta: "填写事故经过",
      route: "/pages/story/story",
    };
  }

  if (!basicsComplete(task)) {
    return {
      kind: "basics",
      primaryCta: "继续补充资料",
      route: "/pages/basics/basics",
    };
  }

  if (!photosSatisfiedForPrototype(task)) {
    return {
      kind: "photos",
      primaryCta: "添加事故照片",
      route: "/pages/photos/photos",
    };
  }

  if (task.current_step === "review" || (dash && dash.primary_cta.includes("提交"))) {
    return {
      kind: "review",
      primaryCta: "检查并提交",
      route: "/pages/review/review",
    };
  }

  if (dash?.primary_cta?.includes("补充")) {
    return {
      kind: "supplement",
      primaryCta: dash.primary_cta,
      route: supplementRoute || "/pages/basics/basics",
    };
  }

  return {
    kind: "review",
    primaryCta: "检查并提交",
    route: "/pages/review/review",
  };
}

export function mapErrorMessage(code: string): string {
  const messages: Record<string, string> = {
    invalid_or_expired_task_link: "链接已失效，请联系陈总获取新的入口。",
    token_missing: "未找到资料入口，请从微信任务卡片重新打开。",
    navigation_failed: "页面打开失败，请重试。",
    // Real-device Preview enforces WeChat legal domains; DevTools often bypasses.
    domain_not_allowed:
      "当前预览环境无法连接报案服务（域名未授权）。请联系陈总办公室配置后再试。",
    tls_error: "安全连接配置失败，请联系陈总办公室处理。",
    dns_error: "无法解析报案服务地址，请稍后重试。如仍失败，请联系陈总办公室。",
    backend_unreachable: "暂时无法连接，请检查网络。",
    network_error: "网络暂时不可用，请稍后再试。",
    timeout: "网络暂时不可用，请稍后再试。",
    internal_error: "暂时无法完成操作，请稍后再试。",
    save_failed: "保存失败，请稍后重试。",
    submit_failed: "提交失败，请稍后重试。",
    missing_required_fields: "还有必填资料未完成，请先补充。",
    already_submitted: "资料已提交，无需重复提交。",
    version_conflict: "资料状态已更新，请查看最新要求后再提交。",
    request_item_not_active: "当前补充项已变更，请按最新要求继续。",
    slice1_not_enabled: "当前任务仍使用原流程，请返回我的报案继续。",
    fact_payload_invalid: "填写内容无效，请修改后重试。",
    evidence_payload_invalid: "请先上传有效照片后再提交。",
    evidence_required: "请先选择需要上传的照片。",
    invalid_upload_url: "暂时无法上传，请稍后重试或联系陈总。",
    upload_missing_attachment_id: "上传未完成确认，请重试。",
    validation_rejected: "提交未通过校验，请修改后重试。",
    vin_invalid: "请输入有效的 17 位 VIN",
    invalid_vin: "请输入有效的 17 位 VIN",
    vehicle_incomplete: "暂时无法提供 VIN 时，请填写年份、品牌和型号",
    vehicle_rejected: "这些信息需要修改，请检查后重新提交",
    case_closed_read_only: "案件已关闭，当前只能查看，不能再提交。",
  };
  return messages[code] || "暂时无法完成操作，请稍后再试。";
}

/** Shared contact broker copy for Entry / Error / TaskShell recovery. */
export function contactBrokerModalCopy(): { title: string; content: string } {
  return {
    title: "联系陈总",
    content:
      "请打开微信，给陈总发一条消息说明您的情况。陈总会帮您继续办理。",
  };
}

export function newSubmitIntentId(): string {
  const random = Math.random().toString(36).slice(2, 10);
  return `mp-${Date.now()}-${random}`;
}

/** Node-testable export of pure logic */
export const taskMapping = {
  extractTokenFromUrl,
  missingItemLabel,
  normalizeMissingKey,
  resolveMissingItemNav,
  mapServerMissingItem,
  routeForMissingKey,
  resolveSupplementAction,
  resolveReviewSupplementAction,
  supplementCtaLabelForRoute,
  buildSupplementRows,
  firstActionableMissingRoute,
  resolveNextAction,
  storyComplete,
  basicsComplete,
  photosSatisfiedForPrototype,
  isBrokerDonePhase,
  isNeedsMoreInfoPhase,
  newSubmitIntentId,
};
