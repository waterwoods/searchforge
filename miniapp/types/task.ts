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

export type Slice1RequestItemType =
  | "vin"
  | "vehicle_information"
  | "policy_or_insurance_card"
  | "photo_evidence"
  | "free_text"
  | string;

/** Slice1 fact payload — free text / VIN value, or structured Claim Vehicle fields. */
export type Slice1FactPayload = {
  field: string;
  value?: string;
  year?: string;
  make?: string;
  model?: string;
  vin?: string;
  vin_unavailable?: boolean;
  license_plate?: string;
  plate_state?: string;
  final?: boolean;
  mode?: "draft" | "submit" | string;
};

export type Slice1ItemStatus =
  | "queued"
  | "active"
  | "in_progress"
  | "satisfied"
  | "withdrawn"
  | "superseded"
  | string;

export type Slice1CustomerActionType =
  | "provide_fact"
  | "provide_evidence"
  | "wait_for_broker_review"
  | "contact_broker"
  | string;

export type Slice1RequestItem = {
  request_item_id: string;
  request_id: string;
  item_type: Slice1RequestItemType;
  label: string;
  instructions: string;
  required: boolean;
  position: number;
  status: Slice1ItemStatus;
  actionable: boolean;
  created_at?: string;
  satisfied_at?: string | null;
  satisfied_by_event_id?: string | null;
};

export type Slice1CustomerNextAction = {
  action_type: Slice1CustomerActionType;
  request_id?: string | null;
  request_item_id?: string | null;
  title: string;
  instructions: string;
  required_input?: Slice1RequestItemType | null;
  status?: string;
  ordering?: { position?: number | null; total?: number | null };
  allowed_actions?: string[];
  version?: number;
  last_updated_at?: string;
};

export type Slice1BrokerNextAction = {
  action_type: string;
  status?: string;
  request_id?: string | null;
  version?: number;
  last_updated_at?: string;
};

export type Slice1RequestProgress = {
  satisfied: number;
  total: number;
  remaining: number;
};

export type Slice1RequestSummary = {
  request_id: string;
  status: string;
  reason?: string;
  created_at?: string;
  updated_at?: string;
  completed_at?: string | null;
  active_item?: Slice1RequestItem | null;
  queued_items?: Slice1RequestItem[];
  items?: Slice1RequestItem[];
  progress?: Slice1RequestProgress;
};

export type Slice1Projection = {
  case_id: string;
  workflow_state: string;
  aggregate_version: number;
  customer_next_action?: Slice1CustomerNextAction | null;
  broker_next_action?: Slice1BrokerNextAction | null;
  open_request?: Slice1RequestSummary | null;
  queued_request_items?: Slice1RequestItem[];
  request_progress?: Slice1RequestProgress;
  latest_events?: unknown[];
  server_timestamp?: string;
};

export type TaskContractV1 = {
  contract_version: "1";
  task_id: string;
  task_type: "claim_request_more" | string;
  workflow_state?: string;
  aggregate_version?: number;
  next_action?: Slice1CustomerNextAction | null;
  queued_request_items?: Slice1RequestItem[];
  request_progress?: Slice1RequestProgress;
  server_timestamp?: string;
};

export type Slice1CommandOutcome = "accepted" | "replayed" | "conflict" | "rejected" | string;

export type Slice1CommandResult = {
  outcome: Slice1CommandOutcome;
  command_id: string;
  correlation_id?: string;
  idempotency_key: string;
  event_ids?: string[];
  aggregate_version?: number;
  customer_projection?: Slice1Projection;
  broker_projection?: Slice1Projection;
  request_summary?: Slice1RequestSummary | null;
  server_timestamp?: string;
  error_code?: string;
  original_outcome?: string;
};

export type Slice1SubmissionCommand = {
  command_id: string;
  idempotency_key: string;
  expected_case_version: number;
  client_draft_id?: string;
  fact?: Slice1FactPayload;
  evidence?: { attachment_id: string };
};

/** P24D2 — additive Constitution Projection (customer slice from H5 intake). */
export type CustomerConstitutionTrust = {
  care_line?: string | null;
  care_note?: string | null;
};

export type CustomerConstitutionTaskAction = {
  kind?: string | null;
  route?: string | null;
  task_type?: string | null;
  task_source?: string | null;
  request_item_id?: string | null;
};

export type CustomerConstitutionTaskCard = {
  task_id?: string | null;
  title?: string | null;
  state?: string | null;
  progress?: { completed?: number | null; total?: number | null } | null;
  is_today?: boolean | null;
  route?: string | null;
  actionable?: boolean | null;
  primary_action?: string | null;
  /** P26G — system_default | broker_requested */
  task_source?: string | null;
  reason?: string | null;
  /** P26G-Q1 — semantic action; prefer over Chinese labels for routing */
  action?: CustomerConstitutionTaskAction | null;
};

export type CustomerConstitutionProjection = {
  today?: string | null;
  why?: string | null;
  after?: string | null;
  trust?: CustomerConstitutionTrust | null;
  current_stage?: string | null;
  /** Happy Path Loop 2 — broker stamped office_materials_accepted_at. */
  office_materials_accepted?: boolean | null;
  /** Passive office-processing UI (stamp set, no open Request More). */
  office_processing?: boolean | null;
  /** P26A — Constitution-first Task Home cards. */
  tasks?: CustomerConstitutionTaskCard[] | null;
};

export type ConstitutionProjection = {
  projection_version?: number;
  case_id?: string | null;
  current_stage?: string | null;
  customer?: CustomerConstitutionProjection | null;
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
  /** Additive Slice 1 projection — server authoritative when present. */
  slice1_projection?: Slice1Projection;
  task_contract_v1?: TaskContractV1;
  /**
   * P24D2 — server Customer Constitution (Today / Why / After / Trust).
   * Prefer via resolveCustomerConstitution; local mock remains fallback.
   */
  constitution_projection?: ConstitutionProjection | null;
  /** P0 Home resume — closed History must not keep Continue. */
  case_status?: string | null;
  case_history_state?: string | null;
  case_closed_read_only?: boolean;
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
