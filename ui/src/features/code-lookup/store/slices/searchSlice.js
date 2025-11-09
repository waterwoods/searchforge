import { create } from 'zustand';

// Search slice - manages search functionality and results
export const createSearchSlice = (set, get) => ({
    // Loading state
    isLoading: false,

    // Query state
    query: '',

    // Search results (could be expanded to include different types of results)
    searchResults: null,

    // Actions
    setQuery: (query) => set({ query }),
    setLoading: (isLoading) => set({ isLoading }),
    setSearchResults: (results) => set({ searchResults: results }),

    // Reset search state
    resetSearch: () => set({
        isLoading: false,
        query: '',
        searchResults: null
    })
});
