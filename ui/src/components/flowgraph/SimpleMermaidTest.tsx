import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const SimpleMermaidTest: React.FC = () => {
    const mermaidRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const renderMermaid = async () => {
            try {
                // Initialize Mermaid
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose'
                });

                // Simple test diagram
                const mermaidCode = `
          graph TD
            A[开始] --> B[处理]
            B --> C[结束]
        `;

                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = '';
                    const { svg } = await mermaid.render('simple-test-' + Date.now(), mermaidCode);
                    mermaidRef.current.innerHTML = svg;
                }
            } catch (error) {
                console.error('Mermaid error:', error);
                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = `<div style="color: red;">Error: ${error}</div>`;
                }
            }
        };

        renderMermaid();
    }, []);

    return (
        <div style={{ padding: '20px' }}>
            <h3>Simple Mermaid Test</h3>
            <div
                ref={mermaidRef}
                style={{
                    border: '1px solid #ccc',
                    padding: '20px',
                    margin: '20px 0',
                    minHeight: '200px',
                    backgroundColor: '#f5f5f5'
                }}
            />
        </div>
    );
};

export default SimpleMermaidTest;
