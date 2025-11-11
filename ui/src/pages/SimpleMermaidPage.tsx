import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const SimpleMermaidPage: React.FC = () => {
    const mermaidRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const renderMermaid = async () => {
            try {
                console.log('SimpleMermaidPage: Starting...');

                // Initialize Mermaid
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose'
                });

                // Test diagram
                const mermaidCode = `
          graph TD
            A[开始] --> B[处理]
            B --> C[结束]
            C --> D[完成]
        `;

                console.log('SimpleMermaidPage: Mermaid code:', mermaidCode);

                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = '';
                    const graphId = 'simple-test-' + Date.now();
                    console.log('SimpleMermaidPage: Rendering with ID:', graphId);

                    const { svg } = await mermaid.render(graphId, mermaidCode);
                    console.log('SimpleMermaidPage: Render successful!');

                    mermaidRef.current.innerHTML = svg;
                }
            } catch (error) {
                console.error('SimpleMermaidPage: Error:', error);
                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = `<div style="color: red; padding: 20px;">Error: ${error}</div>`;
                }
            }
        };

        renderMermaid();
    }, []);

    return (
        <div style={{ padding: '20px' }}>
            <h1>Simple Mermaid Test</h1>
            <p>If you can see a flowchart below, Mermaid is working!</p>

            <div
                ref={mermaidRef}
                style={{
                    border: '2px solid #007acc',
                    padding: '20px',
                    margin: '20px 0',
                    minHeight: '300px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '8px'
                }}
            />

            <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#e9ecef', borderRadius: '4px' }}>
                <h3>Debug Info:</h3>
                <p>Check the browser console for detailed logs.</p>
                <p>If you see "Render successful!" in console, Mermaid is working.</p>
            </div>
        </div>
    );
};

export default SimpleMermaidPage;
