import { create } from 'zustand';

// Analysis slice - manages explanation, trace, and action log data
export const createAnalysisSlice = (set, get) => ({
    // Explanation data
    explanation: '',

    // Execution trace data
    trace: null,

    // Action log events for real-time streaming
    actionLogEvents: [],

    // Actions
    setExplanation: (explanation) => set({ explanation }),
    setTrace: (trace) => set({ trace }),
    addActionLogEvent: (event) => set((state) => ({
        actionLogEvents: [...state.actionLogEvents, event]
    })),

    // Reset analysis state
    resetAnalysis: () => set({
        explanation: '',
        trace: null,
        actionLogEvents: []
    })
});
