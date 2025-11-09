/**
 * RAG Lab Store - Zustand state management
 * Handles experiment job lifecycle, polling, and logs
 */
import { create } from 'zustand';
import * as experimentApi from '../api/experiment';
import type {
  JobKind,
  RunResponse,
  StatusResponse,
  LogResponse,
  QueueResponse,
  ArtifactsResponse,
  ExperimentConfig,
  RunRequest,
  PresetMetadata,
  DiffResponse,
  DiffError,
  VersionedPreset,
  JobMeta,
} from '../api/experiment';

// ========================================
// State Interface
// ========================================

interface RagLabState {
  // Current job state
  currentJobId: string | null;
  currentJobStatus: StatusResponse | null;
  currentJobLogs: string[];

  // Queue state
  queueStatus: QueueResponse | null;

  // Artifacts state
  currentArtifacts: ArtifactsResponse | null;

  // V10: Preset state (legacy)
  presets: Record<string, PresetMetadata>;

  // V11: Versioned preset state
  versionedPresets: VersionedPreset[];
  presetsVersion: number | null;

  // V11: Diff state
  diffLoading: boolean;
  diffResult: DiffResponse | null;
  diffError: DiffError | null;

  // V11: Run overrides state
  runOverrides: {
    top_k?: number;
    bm25_k?: number;
    rerank_topk?: number; // legacy input
    rerank_top_k?: number; // canonical
    rerank?: boolean;
    sample?: number;
    repeats?: number;
    fast_mode?: boolean;
  } | null;

  // New polling state fields
  jobId?: string;
  phase: 'idle' | 'submitting' | 'queued' | 'running' | 'succeeded' | 'failed';
  logs?: string;
  abortController: AbortController | null;

  // UI state
  loading: boolean;
  error: string | null;

  // Polling state
  isPolling: boolean;
  pollIntervalId: NodeJS.Timeout | null;

  // History state
  history: JobMeta[];

  // Actions
  runExperiment: (kind?: JobKind, datasetName?: string, config?: ExperimentConfig, presetName?: string) => Promise<void>;
  startExperiment: (params: { sample: number; repeats: number; fast_mode: boolean; config_file?: string | null; dataset_name?: string; qrels_name?: string }) => Promise<void>;
  cancelCurrentJob: () => Promise<void>;
  refreshJobStatus: () => Promise<void>;
  fetchJobLogs: (tail?: number) => Promise<void>;
  fetchQueueStatus: () => Promise<void>;
  fetchJobArtifacts: (jobId: string) => Promise<void>;
  fetchPresets: () => Promise<void>;
  fetchVersionedPresets: () => Promise<void>;
  runDiff: (jobIdA: string, jobIdB: string) => Promise<void>;
  clearDiff: () => void;
  startPolling: (intervalMs?: number) => void;
  stopPolling: () => void;
  clearError: () => void;
  setRunOverrides: (overrides: RagLabState['runOverrides']) => void;
  loadHistory: () => Promise<void>;
  reset: () => void;
}

// ========================================
// Helper Functions
// ========================================

/**
 * Converts error details from API responses to string format.
 * Handles FastAPI validation errors and other error formats.
 */
const errorToString = (error: any): string => {
  if (typeof error === 'string') {
    return error;
  }

  if (Array.isArray(error)) {
    // FastAPI validation error array format
    return error.map((e: any) => {
      if (typeof e === 'string') return e;
      if (e?.msg) {
        const loc = e.loc ? ` (${e.loc.join('.')})` : '';
        return `${e.msg}${loc}`;
      }
      return JSON.stringify(e);
    }).join(', ');
  }

  if (error && typeof error === 'object') {
    // Single validation error object
    if (error.msg) {
      const loc = error.loc ? ` (${error.loc.join('.')})` : '';
      return `${error.msg}${loc}`;
    }
    // Other error objects
    if (error.message) return error.message;
    if (error.detail) return errorToString(error.detail);
    return JSON.stringify(error);
  }

  return String(error || 'Unknown error');
};

// ========================================
// Store Implementation
// ========================================

export const useRagLabStore = create<RagLabState>((set, get) => ({
  // Initial state - all arrays default to [], objects to {}, strings to ''
  currentJobId: null,
  currentJobStatus: null,
  currentJobLogs: [],
  queueStatus: null,
  currentArtifacts: null,
  presets: {},
  versionedPresets: [],
  presetsVersion: null,
  diffLoading: false,
  diffResult: null,
  diffError: null,
  runOverrides: null,
  jobId: undefined,
  phase: 'idle',
  logs: undefined,
  abortController: null,
  loading: false,
  error: null,
  isPolling: false,
  pollIntervalId: null,
  history: [],

  // Run experiment (V9/V10/V11 compatible)
  runExperiment: async (kind?: JobKind, datasetName?: string, config?: ExperimentConfig, presetName?: string) => {
    set({ loading: true, error: null });

    try {
      // Build request based on provided params
      const request: RunRequest = {};
      const { runOverrides } = get();

      if (kind) {
        // V9 mode
        request.kind = kind;
        if (datasetName) {
          request.dataset_name = datasetName;
        }
      } else if (presetName) {
        // V11 mode: preset with overrides
        // Get preset config first - try from cached versionedPresets first
        const { versionedPresets } = get();
        let presetConfig: ExperimentConfig | null = null;

        // Try to find in cached versioned presets
        const cachedPreset = versionedPresets.find(p => p.name === presetName);
        if (cachedPreset) {
          presetConfig = cachedPreset.config;
        } else {
          // Fallback to API call
          const presetResponse = await experimentApi.getPreset(presetName);
          presetConfig = presetResponse.config;
        }

        // Merge with overrides if present
        if (runOverrides && presetConfig) {
          // Helper function to remove undefined/null values
          const compact = (obj: any) => {
            const result: any = {};
            for (const key in obj) {
              if (obj[key] !== undefined && obj[key] !== null) {
                result[key] = obj[key];
              }
            }
            return result;
          };

          const merged = { ...presetConfig } as any;

          // Ensure groups
          if (!merged.groups || !Array.isArray(merged.groups) || merged.groups.length === 0) {
            merged.groups = [{ name: 'Baseline', use_hybrid: false, rerank: false }];
          }

          // Normalize legacy overrides
          const norm: any = compact(runOverrides);
          if (norm.rerank_topk !== undefined && norm.rerank_top_k === undefined) {
            norm.rerank_top_k = norm.rerank_topk;
            delete norm.rerank_topk;
          }

          // Apply group-level overrides
          // Always ensure rerank and rerank_top_k are set when rerank is ON
          if (typeof norm.rerank === 'boolean') {
            merged.groups[0].rerank = norm.rerank;
            // When rerank is ON, ensure rerank_top_k is set
            if (norm.rerank && typeof norm.rerank_top_k === 'number') {
              merged.groups[0].rerank_top_k = norm.rerank_top_k;
            } else if (norm.rerank && !merged.groups[0].rerank_top_k) {
              merged.groups[0].rerank_top_k = norm.rerank_top_k || 10;
            }
          }
          if (typeof norm.rerank_top_k === 'number') {
            merged.groups[0].rerank_top_k = norm.rerank_top_k;
          }
          // Top-level rerank for suite convenience
          if (typeof norm.rerank === 'boolean') {
            merged.rerank = norm.rerank;
          }
          if (typeof norm.rerank_top_k === 'number') {
            merged.rerank_top_k = norm.rerank_top_k;
          }

          // Apply top-level simple overrides
          ["top_k", "repeats", "sample", "bm25_k", "fast_rrf_k", "fast_topk"].forEach((k) => {
            if (norm[k] !== undefined) merged[k] = norm[k];
          });
          // fast_mode must always be present and reflect the UI toggle (default false)
          merged.fast_mode = (typeof norm.fast_mode === 'boolean') ? norm.fast_mode : false;

          // Ensure default values for sample/repeats even if not in overrides
          if (typeof merged.sample !== 'number') merged.sample = 200;
          if (typeof merged.repeats !== 'number') merged.repeats = 1;

          // Ensure default values for sample/repeats even if not in overrides
          if (typeof merged.sample !== 'number') merged.sample = 200;
          if (typeof merged.repeats !== 'number') merged.repeats = 1;

          // If not hybrid, remove bm25_k
          if (!merged.groups?.[0]?.use_hybrid) {
            delete merged.bm25_k;
          }

          // Log UI overrides before sending
          const uiOverridesLog = {
            ...norm,
            fast_mode: (typeof norm.fast_mode === 'boolean') ? norm.fast_mode : false,
          };
          // Do not drop falsy values; log exact shape
          // eslint-disable-next-line no-console
          console.log('[UI-OVR]', uiOverridesLog);

          request.config = merged;
          request.preset_name = undefined;
        } else {
          // Even without runOverrides, ensure default values are set
          if (presetConfig) {
            const merged = { ...presetConfig } as any;
            // Ensure default values for sample/repeats/fast_mode
            if (typeof merged.sample !== 'number') merged.sample = 200;
            if (typeof merged.repeats !== 'number') merged.repeats = 1;
            if (typeof merged.fast_mode !== 'boolean') merged.fast_mode = false;
            request.config = merged;
            request.preset_name = undefined;
          } else {
            request.preset_name = presetName;
          }
        }
      } else if (config) {
        // V10 mode: config - merge with runOverrides if present
        if (runOverrides) {
          // Helper function to remove undefined/null values
          const compact = (obj: any) => {
            const result: any = {};
            for (const key in obj) {
              if (obj[key] !== undefined && obj[key] !== null) {
                result[key] = obj[key];
              }
            }
            return result;
          };

          const merged = { ...config } as any;

          // Ensure groups exist
          if (!merged.groups || !Array.isArray(merged.groups) || merged.groups.length === 0) {
            merged.groups = [{ name: 'Baseline', use_hybrid: false, rerank: false }];
          }

          const norm: any = compact(runOverrides);
          if (norm.rerank_topk !== undefined && norm.rerank_top_k === undefined) {
            norm.rerank_top_k = norm.rerank_topk;
            delete norm.rerank_topk;
          }

          // Apply group-level overrides
          // Always ensure rerank and rerank_top_k are set when rerank is ON
          if (typeof norm.rerank === 'boolean') {
            merged.groups[0].rerank = norm.rerank;
            // When rerank is ON, ensure rerank_top_k is set
            if (norm.rerank && typeof norm.rerank_top_k === 'number') {
              merged.groups[0].rerank_top_k = norm.rerank_top_k;
            } else if (norm.rerank && !merged.groups[0].rerank_top_k) {
              merged.groups[0].rerank_top_k = norm.rerank_top_k || 10;
            }
          }
          if (typeof norm.rerank_top_k === 'number') {
            merged.groups[0].rerank_top_k = norm.rerank_top_k;
          }
          // Top-level rerank for suite convenience
          if (typeof norm.rerank === 'boolean') {
            merged.rerank = norm.rerank;
          }
          if (typeof norm.rerank_top_k === 'number') {
            merged.rerank_top_k = norm.rerank_top_k;
          }

          ["top_k", "repeats", "sample", "bm25_k", "fast_rrf_k", "fast_topk"].forEach((k) => {
            if (norm[k] !== undefined) merged[k] = norm[k];
          });
          // fast_mode must always be present and reflect the UI toggle (default false)
          merged.fast_mode = (typeof norm.fast_mode === 'boolean') ? norm.fast_mode : false;

          // Ensure default values for sample/repeats even if not in overrides
          if (typeof merged.sample !== 'number') merged.sample = 200;
          if (typeof merged.repeats !== 'number') merged.repeats = 1;

          // If not hybrid, remove bm25_k
          if (!merged.groups?.[0]?.use_hybrid) {
            delete merged.bm25_k;
          }

          // Log UI overrides before sending
          const uiOverridesLog = {
            ...norm,
            fast_mode: (typeof norm.fast_mode === 'boolean') ? norm.fast_mode : false,
          };
          // Do not drop falsy values; log exact shape
          // eslint-disable-next-line no-console
          console.log('[UI-OVR]', uiOverridesLog);

          request.config = merged;
        } else {
          // Even without explicit runOverrides, ensure fast_mode is explicit and log overrides as false
          const merged = { ...config } as any;
          if (typeof merged.fast_mode !== 'boolean') {
            merged.fast_mode = false;
          }
          // eslint-disable-next-line no-console
          console.log('[UI-OVR]', { fast_mode: merged.fast_mode });
          request.config = merged;
        }
      } else {
        throw new Error('Must provide either kind, config, or presetName');
      }

      console.log('[STORE] Calling runExperiment with request:', JSON.stringify(request, null, 2));
      const response: RunResponse = await experimentApi.runExperiment(request);
      console.log('[STORE] Received response:', response);

      set({
        currentJobId: response.job_id,
        loading: false,
        // Reset runOverrides after successful run
        runOverrides: null,
      });

      // Immediately fetch status
      await get().refreshJobStatus();

      // Start polling if job is queued or running
      if (response.status === 'QUEUED' || response.status === 'RUNNING') {
        get().startPolling();
      }
    } catch (err: any) {
      console.error('[STORE] runExperiment error:', err);
      console.error('[STORE] Error response:', err.response);
      console.error('[STORE] Error message:', err.message);

      // Handle 409 collection_missing error specially
      if (err.response?.status === 409 && err.response?.data?.detail?.error === 'collection_missing') {
        const detail = err.response.data.detail;
        set({
          loading: false,
          error: `未发现集合 ${detail.collection}，请先在后端运行: ${detail.hint || 'make fiqa-v1-50k'}`,
        });
      } else {
        set({
          loading: false,
          error: errorToString(err.response?.data?.detail || err.message || 'Failed to start experiment'),
        });
      }
    }
  },

  // Cancel current job
  cancelCurrentJob: async () => {
    const { currentJobId } = get();
    if (!currentJobId) return;

    set({ loading: true, error: null });

    try {
      await experimentApi.cancelJob(currentJobId);
      // Stop polling
      get().stopPolling();

      // Reset state after successful cancel
      set({
        loading: false,
        currentJobId: null,
        currentJobStatus: null,
        currentJobLogs: [],
      });
    } catch (err: any) {
      set({
        loading: false,
        error: errorToString(err.response?.data?.detail || err.message || 'Failed to cancel job'),
      });
    }
  },

  // Refresh job status
  refreshJobStatus: async () => {
    const { currentJobId } = get();
    if (!currentJobId) return;

    try {
      const status = await experimentApi.getJobStatus(currentJobId);
      set({ currentJobStatus: status });

      // Auto-stop polling if job is finished
      const state = status.state || (status as any).status;
      if (
        state === 'SUCCEEDED' ||
        state === 'FAILED' ||
        state === 'CANCELLED' ||
        state === 'ABORTED'
      ) {
        get().stopPolling();

        // Auto-fetch artifacts if job succeeded
        if (state === 'SUCCEEDED') {
          get().fetchJobArtifacts(currentJobId);
        }

        // Auto-reset state when job is finished
        set({
          loading: false,
          currentJobId: null,
          currentJobStatus: null,
          currentJobLogs: [],
        });
      }
    } catch (err: any) {
      // If job not found, clear state
      if (err.response?.status === 404) {
        set({
          currentJobId: null,
          currentJobStatus: null,
          currentJobLogs: [],
          currentArtifacts: null,
        });
        get().stopPolling();
      } else {
        set({ error: errorToString(err.response?.data?.detail || err.message || 'Failed to fetch status') });
      }
    }
  },

  // Fetch job logs
  fetchJobLogs: async (tail: number = 200) => {
    const { currentJobId } = get();
    if (!currentJobId) return;

    try {
      const logs = await experimentApi.getJobLogs(currentJobId, tail);
      const logLines = logs ? logs.split('\n').filter(Boolean) : [];
      set({ currentJobLogs: logLines, logs });
    } catch (err: any) {
      set({ error: errorToString(err.response?.data?.detail || err.message || 'Failed to fetch logs') });
    }
  },

  // Fetch queue status
  fetchQueueStatus: async () => {
    try {
      const queueStatus = await experimentApi.getQueueStatus();
      set({ queueStatus });
    } catch (err: any) {
      set({ error: errorToString(err.response?.data?.detail || err.message || 'Failed to fetch queue status') });
    }
  },

  // Fetch job artifacts
  fetchJobArtifacts: async (jobId: string) => {
    try {
      const artifacts = await experimentApi.getJobArtifacts(jobId);
      set({ currentArtifacts: artifacts });
    } catch (err: any) {
      // Don't set error for artifacts - it's optional data
      console.warn('Failed to fetch artifacts:', err);
    }
  },

  // Fetch presets (legacy V10)
  fetchPresets: async () => {
    try {
      const response = await experimentApi.listPresets();
      set({ presets: response.presets });
    } catch (err: any) {
      console.warn('Failed to fetch presets:', err);
    }
  },

  // Fetch versioned presets (V11)
  fetchVersionedPresets: async () => {
    try {
      const CACHE_KEY = 'PRESETS_V3';
      const cachedStr = localStorage.getItem(CACHE_KEY);

      // Try to use cache first
      if (cachedStr) {
        try {
          const cachedData = JSON.parse(cachedStr);
          // Use cache immediately, then check version in background
          set({
            versionedPresets: cachedData.presets || [],
            presetsVersion: cachedData.version || null,
          });
        } catch (e) {
          // Invalid cache, ignore
          localStorage.removeItem(CACHE_KEY);
        }
      }

      // Always fetch from API to check version and get latest
      const response = await experimentApi.getPresets();

      // Check if version changed
      const cachedStrAfter = localStorage.getItem(CACHE_KEY);
      let shouldUpdateCache = true;
      if (cachedStrAfter) {
        try {
          const cachedData = JSON.parse(cachedStrAfter);
          if (cachedData.version === response.version && response.version === 3) {
            shouldUpdateCache = false;
          }
        } catch (e) {
          // Invalid cache, will update
        }
      }

      // Update cache if needed
      if (shouldUpdateCache) {
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          version: response.version,
          presets: response.presets,
        }));
      }

      // Update state with latest data
      set({
        versionedPresets: response.presets,
        presetsVersion: response.version,
      });
    } catch (err: any) {
      console.warn('Failed to fetch versioned presets:', err);
    }
  },

  // Run diff comparison (V11)
  runDiff: async (jobIdA: string, jobIdB: string) => {
    set({ diffLoading: true, diffError: null, diffResult: null });

    try {
      const result = await experimentApi.diffJobs(jobIdA, jobIdB);
      set({
        diffLoading: false,
        diffResult: result,
        diffError: null,
      });
    } catch (err: any) {
      // Handle different error types
      const status = err.response?.status;
      let diffError: DiffError | null = null;

      if (status === 404) {
        diffError = {
          error: 'job_not_found',
          job_id: err.response?.data?.detail?.missing || jobIdA,
        };
      } else if (status === 409) {
        const detail = err.response?.data?.detail || {};
        diffError = {
          error: detail.error || 'metrics_missing',
          job_id: detail.job_id,
          status: detail.status,
        };
      } else if (status === 422) {
        const detail = err.response?.data?.detail || {};
        diffError = {
          error: 'incompatible_context',
          mismatch: detail.mismatch || {},
        };
      } else {
        diffError = {
          error: 'metrics_missing',
          job_id: jobIdA,
        };
      }

      set({
        diffLoading: false,
        diffError,
        diffResult: null,
      });
    }
  },

  // Clear diff state
  clearDiff: () => {
    set({
      diffLoading: false,
      diffResult: null,
      diffError: null,
    });
  },

  // Start polling for job status and logs
  startPolling: (intervalMs: number = 3000) => {
    const { isPolling, pollIntervalId } = get();

    // Don't start if already polling
    if (isPolling) return;

    // Clear any existing interval
    if (pollIntervalId) {
      clearInterval(pollIntervalId);
    }

    // Fetch immediately
    get().refreshJobStatus();
    get().fetchJobLogs();
    get().fetchQueueStatus();

    // Set up interval
    const intervalId = setInterval(() => {
      get().refreshJobStatus();
      get().fetchJobLogs();
      get().fetchQueueStatus();
    }, intervalMs);

    set({
      isPolling: true,
      pollIntervalId: intervalId,
    });
  },

  // Stop polling
  stopPolling: () => {
    const { pollIntervalId } = get();

    if (pollIntervalId) {
      clearInterval(pollIntervalId);
    }

    set({
      isPolling: false,
      pollIntervalId: null,
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Set run overrides
  setRunOverrides: (overrides) => {
    set({ runOverrides: overrides });
  },

  // Load job history
  loadHistory: async () => {
    try {
      // Increase limit to 100 to ensure we see all jobs including RUNNING/QUEUED
      const history = await experimentApi.getExperimentHistory(100);
      // DO NOT filter out RUNNING/QUEUED - keep all states
      set({ history });
    } catch (err: any) {
      console.error('Failed to load history:', err);
      set({ error: errorToString(err.response?.data?.detail || err.message || 'Failed to load history') });
    }
  },

  // New startExperiment action with polling
  startExperiment: async (params: { sample: number; repeats: number; fast_mode: boolean; config_file?: string | null; dataset_name?: string; qrels_name?: string }) => {
    // Cancel any existing polling
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
    }

    // Create new abort controller
    const newAbortController = new AbortController();
    set({
      phase: 'submitting',
      error: null,
      abortController: newAbortController,
      loading: true
    });

    try {
      // Call runExperiment API
      const requestBody: any = {
        sample: params.sample,
        repeats: params.repeats,
        fast_mode: params.fast_mode,
      };
      if (params.config_file) {
        requestBody.config_file = params.config_file;
      }
      // Always include dataset_name and qrels_name if provided (even if empty string)
      if (params.dataset_name !== undefined && params.dataset_name !== null) {
        requestBody.dataset_name = params.dataset_name;
      }
      if (params.qrels_name !== undefined && params.qrels_name !== null) {
        requestBody.qrels_name = params.qrels_name;
      }

      console.info("[RUN PAYLOAD]", JSON.stringify(requestBody, null, 2));

      const response = await experimentApi.runExperiment(requestBody);
      const jobId = response.job_id;

      if (!jobId) {
        throw new Error('Response missing job_id');
      }

      set({
        jobId,
        currentJobId: jobId,
        phase: 'queued',
        loading: false
      });

      // Start polling
      const MAX_POLL_TIME = 10 * 60 * 1000; // 10 minutes
      const POLL_INTERVAL = 2000; // 2 seconds
      const startTime = Date.now();

      const pollStatus = async () => {
        if (newAbortController.signal.aborted) {
          return;
        }

        try {
          const status = await experimentApi.getExperimentStatus(jobId);
          const state = status.state;

          console.log('[POLL] Status update:', { jobId, state, status });

          // Update phase based on state (normalize to uppercase for comparison)
          const stateUpper = state?.toUpperCase();
          let phase: 'queued' | 'running' | 'succeeded' | 'failed' = 'queued';
          if (stateUpper === 'RUNNING') {
            phase = 'running';
          } else if (stateUpper === 'SUCCEEDED') {
            phase = 'succeeded';
          } else if (stateUpper === 'FAILED') {
            phase = 'failed';
          }

          set({
            phase,
            currentJobStatus: {
              ...status,
              job_id: jobId,
              status: state,
            } as any,
          });

          // Fetch logs periodically (every poll)
          try {
            const logs = await experimentApi.getExperimentLogs(jobId);
            const logLines = logs ? logs.split('\n').filter(Boolean) : [];
            set({
              logs,
              currentJobLogs: logLines,
            });
          } catch (logErr) {
            console.warn('Failed to fetch logs:', logErr);
            // Don't fail polling if logs fetch fails
          }

          // If failed, set error and stop polling
          if (state === 'FAILED') {
            set({
              error: status.error || 'Experiment failed',
            });
            return; // Stop polling
          }

          // If succeeded, stop polling
          if (state === 'SUCCEEDED') {
            return; // Stop polling
          }

          // Check timeout
          if (Date.now() - startTime > MAX_POLL_TIME) {
            set({
              phase: 'failed',
              error: 'Polling timeout after 10 minutes',
            });
            return;
          }

          // Continue polling if not aborted
          if (!newAbortController.signal.aborted) {
            setTimeout(pollStatus, POLL_INTERVAL);
          }
        } catch (err: any) {
          if (newAbortController.signal.aborted) {
            return;
          }
          console.error('Polling error:', err);
          set({
            phase: 'failed',
            error: errorToString(err),
          });
        }
      };

      // Start polling immediately
      pollStatus().catch((err) => {
        console.error('[POLL] Initial poll error:', err);
        if (!newAbortController.signal.aborted) {
          set({
            phase: 'failed',
            loading: false,
            error: errorToString(err),
          });
        }
      });
    } catch (err: any) {
      if (!newAbortController.signal.aborted) {
        set({
          phase: 'failed',
          loading: false,
          error: errorToString(err),
        });
      }
    }
  },

  // Reset all state
  reset: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
    }
    get().stopPolling();
    set({
      currentJobId: null,
      currentJobStatus: null,
      currentJobLogs: [],
      queueStatus: null,
      currentArtifacts: null,
      loading: false,
      error: null,
      diffLoading: false,
      diffResult: null,
      diffError: null,
      runOverrides: null,
      jobId: undefined,
      phase: 'idle',
      logs: undefined,
      abortController: null,
      history: [],
    });
  },
}));

