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
  "accident_datetime",
  "accident_location",
  "own_vehicle_info",
]);

const UNSUPPORTED_KEYS = new Set([
  "other_party_plate",
  "other_party_info",
  "police_involved",
]);

const ACTIONABLE_ROUTES: Record<string, string> = {
  accident_description: "/pages/story/story",
  anyone_injured: "/pages/basics/basics",
  injury_status: "/pages/basics/basics",
  accident_datetime: "/pages/basics/basics",
  accident_location: "/pages/basics/basics",
  own_vehicle_info: "/pages/basics/basics",
  customer_damage_photo: "/pages/photos/photos",
  other_party_vehicle_photo: "/pages/photos/photos",
  scene_photo: "/pages/photos/photos",
  photos: "/pages/photos/photos",
};

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
  if (PHOTO_KEYS.has(raw)) return "photos";
  return raw;
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
      hint: "请返回微信联系陈总补充",
    };
  }

  const route = ACTIONABLE_ROUTES[key];
  if (route) {
    return { action: "ACTIONABLE_NOW", route, statusText: "待补充" };
  }

  return {
    action: "UNSUPPORTED",
    statusText: "待确认",
    hint: "请返回微信联系陈总",
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
  const submitted = isSubmitted(task);

  for (const item of SUPPLEMENT_CHECKLIST) {
    if (item.isComplete(task)) continue;
    if (submitted && item.key !== "photos") continue;
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
    const nav = resolveMissingItemNav(key, task);
    if (nav.action === "COMPLETED") continue;
    seen.add(key);
    rows.push({
      key,
      label: missingItemLabel(item),
      statusText: nav.statusText,
      actionable: nav.action === "ACTIONABLE_NOW",
      route: nav.route,
      hint: nav.hint,
    });
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

  if (submitted || task.current_step === "done") {
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
      route:
        firstActionableMissingRoute(task) ||
        "/pages/photos/photos",
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
      route:
        firstActionableMissingRoute(task) ||
        "/pages/basics/basics",
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
    invalid_or_expired_task_link: "链接已失效，请回微信联系陈总获取新的任务入口。",
    network_error: "网络不可用，请检查网络后重试。",
    save_failed: "保存失败，请稍后重试。",
    submit_failed: "提交失败，请稍后重试。",
    missing_required_fields: "还有必填资料未完成，请先补充。",
    already_submitted: "资料已提交，无需重复提交。",
  };
  return messages[code] || "出现错误，请稍后重试。";
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
