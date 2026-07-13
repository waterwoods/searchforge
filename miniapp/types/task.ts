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
  task_contract?: TaskContractV0;
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

export type TaskContractStatus = "collecting" | "review_ready" | "submitted";

export type TaskSectionStatus = "received" | "needed" | "optional";

export type TaskComponentType =
  | "choice"
  | "short_text"
  | "long_text"
  | "text"
  | "date"
  | "datetime"
  | "number";

export type TaskContractSection = {
  key: string;
  label: string;
  component_type: TaskComponentType;
  required: boolean;
  status: TaskSectionStatus;
  choices?: Array<{ value: string; label: string }>;
  validation?: Record<string, unknown>;
};

export type TaskContractProgress = {
  completed: number;
  total: number;
};

export type TaskContractMissingItem = {
  key: string;
  label: string;
};

export type TaskEvidenceRequirement = {
  slot: string;
  label: string;
  min: number;
  received: number;
};

export type TaskContractNextAction = {
  type: "go_to_section" | "submit" | "view_status" | "contact_broker";
  target?: string;
  label: string;
};

export type TaskContractBranding = {
  office_name: string;
  safety_copy: string;
};

export type TaskContractError = {
  code: string;
  message: string;
  retryable?: boolean;
};

export type TaskContractV0 = {
  contract_version: "0";
  task_id: string;
  task_type: "claim_intake";
  task_status: TaskContractStatus;
  title: string;
  instruction: string;
  progress: TaskContractProgress;
  sections: TaskContractSection[];
  fields: Record<string, string>;
  missing_items: TaskContractMissingItem[];
  evidence_requirements: TaskEvidenceRequirement[];
  next_action: TaskContractNextAction;
  review_ready: boolean;
  submit_ready: boolean;
  revision: number;
  timestamps: {
    updated_at: string;
  };
  capabilities?: {
    voice?: boolean;
    scan?: boolean;
  };
  branding: TaskContractBranding;
  error: TaskContractError | null;
};

export type CustomerTaskSafeContract = Omit<
  TaskContractV0,
  "fields" | "sections" | "missing_items" | "evidence_requirements"
> & {
  fields: Record<string, string>;
  sections: TaskContractSection[];
  missing_items: TaskContractMissingItem[];
  evidence_requirements: TaskEvidenceRequirement[];
};

export type BusyState = {
  loading: boolean;
  saving: boolean;
  uploading: boolean;
  submitting: boolean;
  navigating: boolean;
  retrying: boolean;
};

export type TaskErrorState = {
  code: string;
  message: string;
  retryable: boolean;
  blocking: boolean;
};

export type TaskCtaViewModel = {
  label: string;
  actionType: TaskContractNextAction["type"];
  target: string;
  disabled: boolean;
  loading: boolean;
  disabledReason: string;
};

export type TaskViewModel = {
  source: "contract" | "legacy";
  shellMode: "loading" | "blocking_error" | "content";
  title: string;
  instruction: string;
  statusLabel: string;
  statusTone: "active" | "done";
  progress: {
    completed: number;
    total: number;
    percent: number;
  };
  cta: TaskCtaViewModel;
  missingItems: Array<{
    key: string;
    label: string;
    statusText: string;
    actionable: boolean;
    route: string;
    hint: string;
  }>;
  evidenceRequirements: TaskEvidenceRequirement[];
  reviewReady: boolean;
  submitReady: boolean;
  safetyCopy: string;
  error: TaskErrorState | null;
};

export type TaskPageContext = {
  route?: string;
  busy?: Partial<BusyState>;
};
