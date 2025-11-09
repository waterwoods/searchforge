import React from 'react';
import useGraphStore from './graphStore';
import GraphPanel from './components/GraphPanel';
import EvidencePane from './components/EvidencePane';
import TracePanel from './components/TracePanel';
import SearchView from './components/SearchView';
import './styles/index.css';
import './styles/App.css';

const CodeLookupApp = () => {
  const { graphData } = useGraphStore();
  return (
    <div
      className="clu-app"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
      }}
    >
      <header className="clu-app-header" style={{ flexShrink: 0 }}>
        <div className="clu-header-content">
          <h1>Code Lookup Agent</h1>
          <p>Analyze, visualize, and trace your code intelligently</p>
        </div>
      </header>

      <main
        className="clu-app-main"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <section
          className="clu-graph-view"
          style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}
        >
          <div
            className="clu-main-content"
            style={{ flex: 1, display: 'flex', height: '100%', overflow: 'hidden' }}
          >
            {graphData ? (
              <>
                <div className="clu-graph-section">
                  <GraphPanel />
                </div>
                <aside className="clu-evidence-section">
                  <EvidencePane />
                </aside>
              </>
            ) : (
              <SearchView />
            )}
          </div>
        </section>

        <section
          className="clu-trace-section"
          style={{ flex: 'none', height: '200px' }}
        >
          <TracePanel />
        </section>
      </main>

      <footer className="clu-app-footer" style={{ flexShrink: 0 }}>
        <p>Powered by Searchforge</p>
      </footer>
    </div>
  );
};

export default CodeLookupApp;


