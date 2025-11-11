import React from 'react';
import useStore from '../store';
import './ExplanationPanel.css';

const ExplanationPanel = () => {
    const { explanation } = useStore();

    if (!explanation) {
        return (
            <div className="explanation-panel">
                <div className="no-explanation">
                    <h3>No Explanation Available</h3>
                    <p>Run a query to generate an intelligent analysis of your codebase.</p>
                </div>
            </div>
        );
    }

    // Simple markdown-like rendering without react-markdown
    const renderMarkdown = (text) => {
        return text
            .replace(/^# (.*$)/gim, '<h1 class="markdown-h1">$1</h1>')
            .replace(/^## (.*$)/gim, '<h2 class="markdown-h2">$1</h2>')
            .replace(/^### (.*$)/gim, '<h3 class="markdown-h3">$1</h3>')
            .replace(/^#### (.*$)/gim, '<h4 class="markdown-h4">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong class="markdown-strong">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em class="markdown-em">$1</em>')
            .replace(/`(.*?)`/g, '<code class="markdown-code">$1</code>')
            .replace(/^- (.*$)/gim, '<li class="markdown-li">$1</li>')
            .replace(/^(\d+)\. (.*$)/gim, '<li class="markdown-li">$2</li>')
            .replace(/\n\n/g, '</p><p class="markdown-p">')
            .replace(/\n/g, '<br>');
    };

    return (
        <div className="explanation-panel">
            <div className="explanation-header">
                <h3>Intelligent Analysis</h3>
                <div className="explanation-meta">
                    <span className="analysis-type">AI-Generated Summary</span>
                </div>
            </div>

            <div className="explanation-content">
                <div
                    className="markdown-content"
                    dangerouslySetInnerHTML={{
                        __html: `<p class="markdown-p">${renderMarkdown(explanation)}</p>`
                    }}
                />
            </div>
        </div>
    );
};

export default ExplanationPanel;
