import { create } from 'zustand';

// Error slice - manages error state
export const createErrorSlice = (set, get) => ({
    // Error state
    error: null,

    // Actions
    setError: (error) => set({ error }),
    clearError: () => set({ error: null }),

    // Reset error state
    resetError: () => set({ error: null })
});
