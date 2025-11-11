/**
 * Experiment API Client
 * Provides functions to interact with experiment/job management endpoints
 */
import request from './request';

// ========================================
// Type Definitions
// ========================================

export type JobKind = 'fiqa-fast' | 'tune-fast';

// V10 types
export interface ExperimentGroupConfig {
  name: string;
  use_hybrid: boolean;
  rrf_k?: number;
  rerank: boolean;
  rerank_top_k?: number;
  rerank_if_margin_below?: number;
  max_rerank_trigger_rate?: number;
  rerank_budget_ms?: number;
  description?: string;
}

export interface ExperimentConfig {
  base_url?: string;
  dataset_name?: string;
  qrels_name?: string;
  qdrant_collection?: string;
  data_dir?: string;
  top_k?: number;
  repeats?: number;
  warmup?: number;
  concurrency?: number;
  sample?: number;
  fast_mode?: boolean;
  fast_rrf_k?: number;
  fast_topk?: number;
  fast_rerank_topk?: number;
  groups?: ExperimentGroupConfig[];
}

// V9/V10 compatible
export interface RunRequest {
  kind?: JobKind;
  dataset_name?: string;
  qrels_name?: string;
  sample?: number;
  repeats?: number;
  fast_mode?: boolean;
  config?: ExperimentConfig;
  preset_name?: string;
  config_file?: string | null;
}

export interface PresetMetadata {
  name: string;
  description: string;
  created_at?: string;
  updated_at?: string;
}

export interface PresetResponse {
  name: string;
  config: ExperimentConfig;
}

// V11: Versioned preset response
export interface VersionedPreset {
  label: string;
  name: string;
  config: ExperimentConfig;
}

export interface VersionedPresetsResponse {
  version: number;
  presets: VersionedPreset[];
}

export interface RunResponse {
  job_id: string;
}

export interface StatusResponse {
  state: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  error?: string;
  return_code?: number;
  queued_at?: string;
  started_at?: string;
  finished_at?: string;
  progress_hint?: string;
  last_update_at?: string;
}

export interface LogResponse {
  job_id: string;
  tail: string[];
}

export interface JobMeta {
  job_id: string;
  status: string;
  created_at: string;
  finished_at?: string | null;
  return_code?: number | null;
  params: Record<string, any>;
  cmd?: string[] | null;
  obs_url?: string;
}

export interface CancelResponse {
  job_id: string;
  status: string;
}

export interface QueueResponse {
  queued: string[];
  running: string[];
  queue_size: number;
}

// ========================================
// API Functions
// ========================================

/**
 * Submit an experiment job to the queue
 * Returns 202 Accepted with job_id, then poll /api/experiment/status/{id}
 */
export async function runExperiment(data: RunRequest): Promise<RunResponse> {
  console.info("[RUN PAYLOAD]", JSON.stringify(data, null, 2));
  try {
    const response = await request.post<RunResponse | { ok: boolean; job_id: string; status?: string }>('/api/experiment/run', data);
    console.info("[RUN RESPONSE]", response.status, response.data);
    
    // Handle 202 Accepted response
    if (response.status === 202) {
      const body = response.data;
      // Backend may return {"ok": true, "job_id": "...", "status": "..."} or just {"job_id": "..."}
      const jobId = (body as any).job_id;
      if (!jobId) {
        throw new Error('Response missing job_id');
      }
      return { job_id: jobId };
    }
    
    // Fallback for non-202 responses
    if (response.data && typeof (response.data as any).job_id === 'string') {
      return { job_id: (response.data as any).job_id };
    }
    
    throw new Error('Invalid response format: missing job_id');
  } catch (error: any) {
    console.error("[RUN ERROR]", error);
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data;
      const errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      const errorText = `HTTP ${status}: ${errorMessage}`;
      console.error("[RUN ERROR DETAIL]", status, error.response.data);
      throw new Error(errorText);
    } else if (error.request) {
      console.error("[RUN ERROR NO RESPONSE]", error.request);
      throw new Error('Network error: No response received');
    }
    throw error;
  }
}

/**
 * Get job status
 * Returns status with state field
 */
export async function getJobStatus(jobId: string): Promise<StatusResponse> {
  const response = await request.get<{ ok: boolean; job: any } | StatusResponse>(`/api/experiment/status/${jobId}`);
  
  // Backend may return {"ok": true, "job": {...}} or direct status object
  if ((response.data as any).ok && (response.data as any).job) {
    const job = (response.data as any).job;
    return {
      state: job.status || 'QUEUED',
      error: job.error,
      return_code: job.rc,
      queued_at: job.queued_at,
      started_at: job.started_at,
      finished_at: job.finished_at,
      progress_hint: job.progress_hint,
      last_update_at: job.last_update_at,
    };
  }
  
  // Direct status response format
  const data = response.data as StatusResponse;
  if (data.state) {
    return data;
  }
  
  // Legacy format with status field
  if ((data as any).status) {
    return {
      state: (data as any).status,
      error: (data as any).error,
      return_code: data.return_code,
      queued_at: data.queued_at,
      started_at: data.started_at,
      finished_at: data.finished_at,
      progress_hint: data.progress_hint,
      last_update_at: data.last_update_at,
    };
  }
  
  throw new Error('Invalid status response format');
}

/**
 * Alias for getJobStatus (for compatibility with new API naming)
 */
export const getExperimentStatus = getJobStatus;

/**
 * Get job logs (tail)
 * Returns logs as string
 */
export async function getJobLogs(jobId: string, tail: number = 50): Promise<string> {
  const response = await request.get<{ lines: string[] } | LogResponse>(`/api/experiment/logs/${jobId}`, {
    params: { tail },
  });
  
  // Backend may return {"lines": [...]} or {"tail": [...]}
  const data = response.data;
  if (Array.isArray((data as any).lines)) {
    return (data as any).lines.join('\n');
  }
  if (Array.isArray((data as any).tail)) {
    return (data as any).tail.join('\n');
  }
  
  return '';
}

/**
 * Alias for getJobLogs (for compatibility with new API naming)
 */
export const getExperimentLogs = getJobLogs;

/**
 * Get experiment job history
 */
export async function getExperimentHistory(limit: number = 100): Promise<JobMeta[]> {
  const response = await request.get<JobMeta[]>(`/api/experiment/history`, {
    params: { limit },
  });
  return response.data;
}

/**
 * Cancel a running job
 */
export async function cancelJob(jobId: string): Promise<CancelResponse> {
  const response = await request.post<CancelResponse>(`/api/experiment/cancel/${jobId}`);
  return response.data;
}

/**
 * Get current queue status
 */
export async function getQueueStatus(): Promise<QueueResponse> {
  const response = await request.get<QueueResponse>('/api/experiment/queue');
  return response.data;
}

// ========================================
// Artifact & Snapshot APIs
// ========================================

export interface SnapshotResponse {
  ok: boolean;
  path: string;
  timestamp: number;
}

export interface ArtifactsResponse {
  ok: boolean;
  artifacts: {
    job_id: string;
    timestamp: string;
    report_dir: string;
    yaml_report: string | null;
    combined_plot: string | null;
    report_data?: any;
  };
}

export interface JobsListResponse {
  jobs: any[];
  total: number;
}

export interface JobDetailResponse {
  job_id: string;
  status: string;
  cmd: string[];
  return_code?: number;
  queued_at?: string;
  started_at?: string;
  finished_at?: string;
  progress_hint?: string;
  pid?: number;
  artifacts?: any;
  config?: any;  // V10: Optional experiment config
  params?: any;  // Job parameters (dataset_name, qrels_name, etc.)
  last_update_at?: string;
  obs_url?: string;
}

/**
 * Create a snapshot of current best configuration
 */
export async function createSnapshot(): Promise<SnapshotResponse> {
  const response = await request.post<SnapshotResponse>('/api/snapshot');
  return response.data;
}

/**
 * Get artifacts for a completed job
 */
export async function getJobArtifacts(jobId: string): Promise<ArtifactsResponse> {
  const response = await request.get<ArtifactsResponse>(`/api/artifacts/${jobId}`);
  return response.data;
}

/**
 * List all jobs
 */
export async function listJobs(limit: number = 100): Promise<JobsListResponse> {
  const response = await request.get<JobsListResponse>('/api/experiment/jobs', {
    params: { limit },
  });
  return response.data;
}

/**
 * Get detailed information for a specific job
 */
export async function getJobDetail(jobId: string): Promise<JobDetailResponse> {
  const response = await request.get<JobDetailResponse>(`/api/experiment/job/${jobId}`);
  return response.data;
}

// ========================================
// V10/V11 Preset APIs
// ========================================

/**
 * V11: Get versioned presets (with version and full configs)
 */
export async function getPresets(): Promise<VersionedPresetsResponse> {
  const response = await request.get<VersionedPresetsResponse>('/api/experiment/presets');
  return response.data;
}

/**
 * V10: List all available presets (legacy, for backward compatibility)
 */
export async function listPresets(): Promise<{ presets: Record<string, PresetMetadata> }> {
  const response = await request.get<{ presets: Record<string, PresetMetadata> }>('/api/experiment/presets');
  return response.data;
}

/**
 * Get a preset by name
 */
export async function getPreset(presetName: string): Promise<PresetResponse> {
  const response = await request.get<PresetResponse>(`/api/experiment/presets/${presetName}`);
  return response.data;
}

/**
 * Create or update a preset
 */
export async function createPreset(
  presetName: string,
  config: ExperimentConfig,
  description: string = ''
): Promise<{ ok: boolean; name: string }> {
  const response = await request.post<{ ok: boolean; name: string }>(
    '/api/experiment/presets',
    config,
    {
      params: { preset_name: presetName, description },
    }
  );
  return response.data;
}

/**
 * Delete a preset
 */
export async function deletePreset(presetName: string): Promise<{ ok: boolean; name: string }> {
  const response = await request.delete<{ ok: boolean; name: string }>(
    `/api/experiment/presets/${presetName}`
  );
  return response.data;
}

// ========================================
// V11 Diff API
// ========================================

export interface DiffMetrics {
  recall_at_10: number;
  p95_ms: number;
  cost_per_query: number;
}

export interface DiffMeta {
  dataset_name: string;
  schema_version: number;
  git_sha?: string;
  git_sha_source?: 'env' | 'git' | 'unknown';
  created_at: { A: string; B: string } | string; // 兼容旧后端：临时保留 union
}

export interface DiffResponse {
  metrics: {
    A: DiffMetrics;
    B: DiffMetrics;
  };
  params_diff: Record<string, [any, any]>; // e.g., { "top_k": [40, 50], "fast_mode": [true, false] }
  meta: DiffMeta;
}

export interface DiffError {
  error: 'job_not_found' | 'job_in_progress' | 'job_failed' | 'metrics_missing' | 'incompatible_context';
  job_id?: string;
  status?: string;
  mismatch?: Record<string, [any, any]>;
}

/**
 * Compare two jobs (V11 Diff API)
 */
export async function diffJobs(jobIdA: string, jobIdB: string): Promise<DiffResponse> {
  const response = await request.get<DiffResponse>('/api/experiment/diff', {
    params: { A: jobIdA, B: jobIdB },
  });

  // Normalize created_at: convert old format (string) to new format ({A, B})
  if (typeof response.data.meta.created_at === 'string') {
    const createdAtStr = response.data.meta.created_at;
    response.data.meta.created_at = { A: createdAtStr, B: createdAtStr };
  }

  return response.data;
}

