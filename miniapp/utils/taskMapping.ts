import type { CustomerTask, NextAction, NextActionKind } from "../types/task";

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

  return {
    kind: dash?.primary_cta?.includes("补充") ? "supplement" : "review",
    primaryCta: dash?.primary_cta || "继续补充资料",
    route: "/pages/task-home/task-home",
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
  resolveNextAction,
  storyComplete,
  basicsComplete,
  photosSatisfiedForPrototype,
  newSubmitIntentId,
};
