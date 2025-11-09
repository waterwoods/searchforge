import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import useStore from '../store';
import './WorkflowPanel.css';

const WorkflowPanel = () => {
    const mermaidRef = useRef(null);
    const [chart, setChart] = useState('');

    // Connect to Zustand store
    const actionLogEvents = useStore((state) => state.actionLogEvents);

    // Event-to-node mapping based on the workflow steps
    const eventToNodeMap = {
        'plan': 'B',        // Parse & Plan
        'tool_start': 'C', // Execute Tools
        'tool_result': 'C', // Execute Tools (completion)
        'llm_result': 'D', // Invoke AI Analysis
        'judge': 'D',      // Invoke AI Analysis (judge validation)
        'final': 'E'       // Synthesize Final Answer
    };

    // Initialize Mermaid
    useEffect(() => {
        mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#4a9eff',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#666666',
                lineColor: '#888888',
                secondaryColor: '#2a2a2a',
                tertiaryColor: '#1a1a1a',
                background: '#1a1a1a',
                mainBkg: '#2a2a2a',
                secondBkg: '#333333',
                tertiaryBkg: '#444444'
            },
            flowchart: {
                nodeSpacing: 120,
                rankSpacing: 120,
                curve: 'basis',
                padding: 20
            },
            fontFamily: 'Inter, sans-serif'
        });
    }, []);

    // Dynamic styling logic based on actionLogEvents
    useEffect(() => {
        const completedNodes = new Set();

        // Always highlight the first node (A) when there are any events
        if (actionLogEvents.length > 0) {
            completedNodes.add('A');
        }

        // Process action log events to determine completed nodes
        actionLogEvents.forEach(event => {
            const nodeId = eventToNodeMap[event.event];
            if (nodeId) {
                completedNodes.add(nodeId);
            }
        });

        // Generate dynamic chart with styling
        let styleDefs = 'classDef completed fill:#28a745,stroke:#fff,stroke-width:2px,color:#fff;';
        let styleDefsPending = 'classDef pending fill:#6c757d,stroke:#fff,stroke-width:2px,color:#fff;';
        let classAssignments = '';

        // Apply completed styling to nodes with events
        completedNodes.forEach(nodeId => {
            classAssignments += `class ${nodeId} completed;`;
        });

        // Apply pending styling to nodes without events
        const allNodes = ['A', 'B', 'C', 'D', 'E'];
        allNodes.forEach(nodeId => {
            if (!completedNodes.has(nodeId)) {
                classAssignments += `class ${nodeId} pending;`;
            }
        });

        const newChart = `
            flowchart TD
                A[Receive & Route Query] --> B{Parse & Plan}
                B --> C[Execute Tools]
                C --> D[Invoke AI Analysis]
                D --> E[Synthesize Final Answer]

                ${styleDefs}
                ${styleDefsPending}
                ${classAssignments}
        `;

        setChart(newChart);
    }, [actionLogEvents]);

    // Render Mermaid diagram
    useEffect(() => {
        if (mermaidRef.current && chart) {
            const element = mermaidRef.current;
            element.innerHTML = '';

            mermaid.render('workflow-' + Date.now(), chart)
                .then(({ svg }) => {
                    element.innerHTML = svg;
                })
                .catch((error) => {
                    console.error('Mermaid rendering error:', error);
                    element.innerHTML = '<p>Error rendering workflow diagram</p>';
                });
        }
    }, [chart]);

    return (
        <div className="workflow-panel">
            <h2>Agent Workflow</h2>
            <div className="workflow-description">
                <p>This diagram shows the real-time execution steps of our AI agent:</p>
                <ul>
                    <li><strong>Receive & Route Query</strong> - Process and route user queries</li>
                    <li><strong>Parse & Plan</strong> - Analyze query and plan execution strategy</li>
                    <li><strong>Execute Tools</strong> - Run necessary tools and operations</li>
                    <li><strong>Invoke AI Analysis</strong> - Perform AI-powered analysis and processing</li>
                    <li><strong>Synthesize Final Answer</strong> - Compile and return the final result</li>
                </ul>
            </div>
            <div className="mermaid-wrapper">
                <div ref={mermaidRef} className="mermaid-diagram"></div>
            </div>
        </div>
    );
};

export default WorkflowPanel;
