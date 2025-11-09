import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import './SearchResults.css';

const SearchResults = () => {
    const location = useLocation();
    const results = location.state?.results || [];

    if (results.length === 0) {
        return (
            <div className="search-results-container">
                <div className="search-results-empty">
                    <h2>No Results Found</h2>
                    <p>No search results were found. Please try a different query.</p>
                    <Link to="/" className="back-to-search-link">
                        Back to Search
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="search-results-container">
            <div className="search-results-header">
                <h2>Search Results</h2>
                <p className="results-count">
                    Found {results.length} potential match{results.length !== 1 ? 'es' : ''}
                </p>
            </div>

            <div className="results-list">
                {results.map((result, index) => (
                    <Link
                        key={result.id || index}
                        to={`/graph/${result.id}`}
                        className="result-item"
                    >
                        <div className="result-header">
                            <span className="result-kind">{result.kind || 'unknown'}</span>
                            <span className="result-fqname">{result.fqName || result.id}</span>
                        </div>
                        {result.snippet && (
                            <div className="result-snippet">
                                <code>{result.snippet}</code>
                            </div>
                        )}
                        <div className="result-footer">
                            <span className="result-id">ID: {result.id}</span>
                        </div>
                    </Link>
                ))}
            </div>

            <div className="search-results-footer">
                <Link to="/" className="back-to-search-link">
                    ← Back to Search
                </Link>
            </div>
        </div>
    );
};

export default SearchResults;

