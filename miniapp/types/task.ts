/** Customer-facing task shapes — channel-neutral, not H5-specific. */

export type TaskLaunchSource = "launch_query" | "dev_config" | "resume_storage";

export type TaskLaunchContext = {
  token: string;
  source: TaskLaunchSource;
};

export type DashboardSummary = {
  title: string;
  subtitle: string;
  status: string;
  received: string[];
  missing: string[];
  next_action: string;
  primary_cta: string;
  secondary_cta: string;
  submitted_supplement_allowed: boolean;
  warning: string;
};

export type CompletionSummary = {
  title: string;
  message: string;
  received: string[];
  missing: string[];
  missing_clear_message?: string | null;
  next_step: string;
  disclaimer: string;
};

export type MissingInfoItem = {
  key?: string;
  field?: string;
  label: string;
};

export type CustomerTask = {
  lane: string;
  flow: string;
  case_id: string;
  title: string;
  safety_copy: string;
  steps: string[];
  current_step: string;
  completed_count: number;
  step_total: number;
  submitted: boolean;
  phase: string;
  key_facts: Record<string, string | null>;
  missing_info: MissingInfoItem[];
  injury_alert?: boolean;
  already_submitted?: boolean;
  submit_intent_id?: string;
  upload_url?: string | null;
  attachment_count?: number;
  photo_count?: number;
  completion_summary?: CompletionSummary;
  dashboard_summary?: DashboardSummary;
};

export type UploadSlotInfo = {
  lane: string;
  flow: string;
  case_id: string;
  slot?: string;
  current_step?: string | null;
  step_index?: number;
  step_total?: number;
  flow_complete?: boolean;
  task_label?: string;
  instruction?: string;
};

export type PhotoSlotState = {
  slotKey: string;
  label: string;
  localPath?: string;
  uploaded: boolean;
  uploading: boolean;
  error?: string;
};

export type NextActionKind =
  | "story"
  | "photos"
  | "basics"
  | "review"
  | "receipt"
  | "supplement"
  | "done";

export type NextAction = {
  kind: NextActionKind;
  primaryCta: string;
  route?: string;
};
