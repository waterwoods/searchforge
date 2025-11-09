import React, { useState } from 'react';
// Navigation removed in favor of shared Zustand graph store
import useGraphStore from '../graphStore';
import useStore from '../store';
import { GraphDataSchema } from '../schemas/graphSchemas';
import './QueryInput.css';

const QueryInput = () => {
    const [inputValue, setInputValue] = useState('');
    const { fetchGraphData, isLoading } = useGraphStore();
    const {
        query,
        setQuery,
        setLoading,
        setGraphData,
        setExplanation,
        setTrace,
        setError,
        clearError,
        reset,
        addActionLogEvent
    } = useStore();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!inputValue.trim()) {
            setError('Please enter a query');
            return;
        }

        try {
            clearError();
            setQuery(inputValue);
            // Delegate streaming to shared graph store
            fetchGraphData(inputValue.trim());

        } catch (error) {
            setError(`Error: ${error.message}`);
            setLoading(false);
        }
    };

    const handleClear = () => {
        setInputValue('');
        reset();
    };

    const exampleQueries = [
        '#overview',
        '#file services/fiqa_api/app.py',
        '#func services.fiqa_api.search',
        'what is the repository',
        'analyze the file at services/fiqa_api/app.py'
    ];

    return (
        <div className="query-input-container">
            <form onSubmit={handleSubmit} className="query-form">
                <div className="input-group">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Enter your query (e.g., #overview, #file services/fiqa_api/app.py, #func services.fiqa_api.search)"
                        className="query-input"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="submit-button"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Loading...' : 'Submit'}
                    </button>
                    <button
                        type="button"
                        onClick={handleClear}
                        className="clear-button"
                        disabled={isLoading}
                    >
                        Clear
                    </button>
                </div>
            </form>

            <div className="example-queries">
                <h4>Example Queries:</h4>
                <div className="example-list">
                    {exampleQueries.map((example, index) => (
                        <button
                            key={index}
                            className="example-button"
                            onClick={() => setInputValue(example)}
                            disabled={useStore.getState().isLoading}
                        >
                            {example}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default QueryInput;
