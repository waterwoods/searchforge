import React, { useState } from 'react';
import useStore from '../store';
import './EvidencePane.css';

const EvidencePane = () => {
    const { selectedNode, selectedNodeEvidence } = useStore();
    const [activeTab, setActiveTab] = useState('evidence');

    const formatCode = (code) => {
        if (!code) return '';

        // Basic syntax highlighting for Python
        return code
            .replace(/(def|class|if|else|elif|for|while|try|except|finally|with|import|from|return|yield|async|await)\b/g, '<span class="keyword">$1</span>')
            .replace(/(\b\w+)\s*\(/g, '<span class="function">$1</span>(')
            .replace(/(["'].*?["'])/g, '<span class="string">$1</span>')
            .replace(/(#.*$)/gm, '<span class="comment">$1</span>')
            .replace(/\n/g, '<br>');
    };

    const renderEvidence = () => {
        if (!selectedNode || !selectedNodeEvidence) {
            return (
                <div className="no-selection">
                    <h3>No Node Selected</h3>
                    <p>Click on a node in the graph to view its evidence details.</p>
                </div>
            );
        }

        const { file, span, snippet } = selectedNodeEvidence;

        return (
            <div className="evidence-content">
                <div className="node-header">
                    <h3>Node Details</h3>
                    <div className="node-id">{selectedNode.id}</div>
                </div>

                <div className="node-info">
                    <div className="info-section">
                        <h4>Function Name</h4>
                        <p className="fqname">{selectedNode.fqName || 'N/A'}</p>
                    </div>

                    <div className="info-section">
                        <h4>Kind</h4>
                        <p className="kind">{selectedNode.kind || 'N/A'}</p>
                    </div>

                    <div className="info-section">
                        <h4>Language</h4>
                        <p className="language">{selectedNode.language || 'N/A'}</p>
                    </div>

                    {selectedNode.signature && (
                        <div className="info-section">
                            <h4>Signature</h4>
                            <p className="signature">{selectedNode.signature}</p>
                        </div>
                    )}

                    {selectedNode.doc && (
                        <div className="info-section">
                            <h4>Documentation</h4>
                            <p className="doc">{selectedNode.doc}</p>
                        </div>
                    )}

                    {selectedNode.metrics && (
                        <div className="info-section">
                            <h4>Metrics</h4>
                            <div className="metrics">
                                {selectedNode.metrics.loc && (
                                    <span className="metric">LOC: {selectedNode.metrics.loc}</span>
                                )}
                                {selectedNode.metrics.complexity && (
                                    <span className="metric">Complexity: {selectedNode.metrics.complexity}</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className="evidence-section">
                    <h3>Evidence</h3>

                    <div className="evidence-item">
                        <h4>File</h4>
                        <p className="file-path">{file || 'N/A'}</p>
                    </div>

                    {span && (
                        <div className="evidence-item">
                            <h4>Location</h4>
                            <p className="span-info">
                                Lines {span.start} - {span.end}
                                {span.start && span.end && (
                                    <span className="line-count">
                                        ({span.end - span.start + 1} lines)
                                    </span>
                                )}
                            </p>
                        </div>
                    )}

                    {snippet && (
                        <div className="evidence-item">
                            <h4>Code Snippet</h4>
                            <div className="code-container">
                                <pre className="code-block">
                                    <code
                                        dangerouslySetInnerHTML={{
                                            __html: formatCode(snippet)
                                        }}
                                    />
                                </pre>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="evidence-pane">
            <div className="tab-header">
                <button
                    className={`tab-button ${activeTab === 'evidence' ? 'active' : ''}`}
                    onClick={() => setActiveTab('evidence')}
                >
                    Evidence Details
                </button>
                <button
                    className={`tab-button ${activeTab === 'explanation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('explanation')}
                    disabled={true}
                >
                    AI Analysis (Coming Soon)
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'evidence' && renderEvidence()}
                {activeTab === 'explanation' && (
                    <div className="explanation-panel">
                        <div className="no-explanation">
                            <h3>AI Analysis Coming Soon</h3>
                            <p>This feature is being developed.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default EvidencePane;
