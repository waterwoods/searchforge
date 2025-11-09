import React from 'react';
import QueryInput from './QueryInput';
import './SearchView.css';

const SearchView = () => {
    return (
        <div className="search-view">
            <div className="search-view-container">
                <div className="search-header">
                    <h2>Start by analyzing your codebase</h2>
                    <p>Enter a file path, function name, or a general query to begin exploring your code.</p>
                </div>

                <div className="search-input-section">
                    <QueryInput />
                </div>

                <div className="search-features">
                    <div className="feature-grid">
                        <div className="feature-card">
                            <h3>🔍 Code Search</h3>
                            <p>Find functions, classes, and files across your entire codebase</p>
                        </div>
                        <div className="feature-card">
                            <h3>📊 Graph Visualization</h3>
                            <p>Explore relationships and dependencies in an interactive graph</p>
                        </div>
                        <div className="feature-card">
                            <h3>🤖 AI Analysis</h3>
                            <p>Get intelligent insights and explanations about your code</p>
                        </div>
                        <div className="feature-card">
                            <h3>📈 Performance Metrics</h3>
                            <p>Identify bottlenecks and performance issues in your code</p>
                        </div>
                    </div>
                </div>

                {/* We can add search history or other features here later */}
            </div>
        </div>
    );
};

export default SearchView;
