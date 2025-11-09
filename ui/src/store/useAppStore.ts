// frontend/src/store/useAppStore.ts
import { create } from 'zustand';
import { ApiMetricsResponse, RagTriadScores } from '../types/api.types';

// --- "BEFORE" State Metrics ---
const BEFORE_METRICS: ApiMetricsResponse = {
    ok: true,
    p95_ms: 120.4,
    recall_pct: 82.0,
    qps: 3.2,
    err_pct: 0.0,
};

// --- Default RAG Triad Scores ---
const BEFORE_TRIAD: RagTriadScores = { context_relevance: 0.75, groundedness: 0.70, answer_relevance: 0.80 };
const AFTER_TRIAD: RagTriadScores = { context_relevance: 0.95, groundedness: 0.99, answer_relevance: 0.92 };

interface AppState {
    // State for Improve Panel controls
    topK: number;
    rerank: boolean;
    setTopK: (k: number) => void;
    setRerank: (r: boolean) => void;

    // State for linking Console to Explain panel
    currentTraceId: string | null;
    setCurrentTraceId: (id: string | null) => void;

    // State for linking Workbench to RAG Triad panel
    currentExperimentId: string | null;
    setCurrentExperimentId: (id: string | null) => void;

    // State for dynamic KPIs
    currentMetrics: ApiMetricsResponse;
    setCurrentMetrics: (metrics: ApiMetricsResponse) => void;

    // State for RAG Quality Triad scores
    currentRagTriad: RagTriadScores | null;
    setCurrentRagTriad: (scores: RagTriadScores | null) => void;

    // Helper to reset the story
    resetToBeforeState: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    // Default "Before" state from our MVP story
    topK: 20,
    rerank: false,
    setTopK: (k) => set({ topK: k }),
    setRerank: (r) => set({ rerank: r }),

    currentTraceId: null,
    setCurrentTraceId: (id) => set({ currentTraceId: id }),

    currentExperimentId: null,
    setCurrentExperimentId: (id) => set({ currentExperimentId: id }),

    currentMetrics: BEFORE_METRICS,
    setCurrentMetrics: (metrics) => {
        const isAfter = metrics.p95_ms < 100; // Use the same check
        set({
            currentMetrics: metrics,
            currentRagTriad: isAfter ? AFTER_TRIAD : BEFORE_TRIAD // Set triad based on state
        });
    },

    currentRagTriad: null,
    setCurrentRagTriad: (scores) => set({ currentRagTriad: scores }),

    resetToBeforeState: () => set({
        topK: 20,
        rerank: false,
        currentTraceId: null,
        currentMetrics: BEFORE_METRICS,
        currentRagTriad: null, // Reset to null
    }),
}));

