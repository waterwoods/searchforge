import { create } from 'zustand';
import { createGraphSlice } from './slices/graphSlice';
import { createSearchSlice } from './slices/searchSlice';
import { createAnalysisSlice } from './slices/analysisSlice';
import { createErrorSlice } from './slices/errorSlice';

// Combined store using Zustand's slice pattern
const useStore = create((set, get) => ({
    // Combine all slices
    ...createGraphSlice(set, get),
    ...createSearchSlice(set, get),
    ...createAnalysisSlice(set, get),
    ...createErrorSlice(set, get),

    // Global reset function that resets all slices
    reset: () => set({
        // Graph slice reset
        graphData: null,
        nodes: [],
        edges: [],
        selectedNode: null,
        selectedNodeEvidence: null,
        
        // Search slice reset
        isLoading: false,
        query: '',
        searchResults: null,
        
        // Analysis slice reset
        explanation: '',
        trace: null,
        actionLogEvents: [],
        
        // Error slice reset
        error: null
    })
}));

export default useStore;
