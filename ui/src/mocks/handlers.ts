// frontend/src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';
// import { AutoTunerStatus } from '../types/api.types'; // COMMENTED OUT: Using real backend API

// --- "BEFORE" State Data (Slow) ---
const BEFORE_QUERY_RESPONSE = {
    ok: true,
    trace_id: 'tr_before_slow',
    question: 'Explain investment returns in simple terms',
    answer: 'Investment return is how much you gain or lose on money you invest... (This is the SLOW, un-reranked answer)',
    latency_ms: 118.6,
    route: 'milvus',
    params: { top_k: 20, rerank: false },
    sources: [
        { doc_id: 'doc_4102', title: 'Intro to Returns', url: 'https://example.com/returns-intro', score: 0.83 },
        { doc_id: 'doc_1659', title: 'Compounding Basics', url: 'https://example.com/compounding', score: 0.79 }
    ],
    ts: '2025-10-18T19:07:12.431Z',
};

const BEFORE_TRACE_RESPONSE = {
    ok: true,
    trace_id: 'tr_before_slow',
    total_ms: 118.6,
    stages: [
        { stage_name: 'Parse', start_ms: 0.0, duration_ms: 6.2 },
        { stage_name: 'Embed', start_ms: 6.2, duration_ms: 9.7 },
        { stage_name: 'Retrieve', start_ms: 15.9, duration_ms: 80.3, meta: { top_k: 20, index: 'milvus' } },
        { stage_name: '(no rerank)', start_ms: 96.2, duration_ms: 0.0 },
        { stage_name: 'Generate', start_ms: 96.2, duration_ms: 22.4, meta: { prompt_tokens: 312, model: 'gpt-mini' } }
    ],
    ts: '2025-10-18T19:07:12.500Z',
};

// --- "AFTER" State Data (Fast & Reranked) ---
const AFTER_QUERY_RESPONSE = {
    ok: true,
    trace_id: 'tr_after_fast',
    question: 'Explain investment returns in simple terms',
    answer: 'Investment return (or "return") is the profit or loss you make on an investment... (This is the FAST, high-quality RERANKED answer)',
    latency_ms: 44.8,
    route: 'milvus_reranked',
    params: { top_k: 6, rerank: true }, // Reflects the new params
    sources: [
        { doc_id: 'doc_1659', title: 'Compounding Basics', url: 'https://example.com/compounding', score: 0.95 },
        { doc_id: 'doc_4102', title: 'Intro to Returns', url: 'https://example.com/returns-intro', score: 0.91 }
    ],
    ts: '2025-10-18T19:09:30.100Z',
};

const AFTER_TRACE_RESPONSE = {
    ok: true,
    trace_id: 'tr_after_fast',
    total_ms: 44.8,
    stages: [
        { stage_name: 'Parse', start_ms: 0.0, duration_ms: 5.1 },
        { stage_name: 'Embed', start_ms: 5.1, duration_ms: 9.5 },
        { stage_name: 'Retrieve', start_ms: 14.6, duration_ms: 15.2, meta: { top_k: 6, index: 'milvus' } }, // Much faster
        { stage_name: 'Rerank', start_ms: 29.8, duration_ms: 8.0, meta: { model: 'mini-cross-encoder' } }, // New stage
        { stage_name: 'Generate', start_ms: 37.8, duration_ms: 7.0 }
    ],
    ts: '2025-10-18T19:09:30.200Z',
};

// --- AutoTuner State Management ---
// COMMENTED OUT: Now using real backend API via proxy
// let tunerStatus: AutoTunerStatus['status'] = 'idle';
// let tunerProgress = 0;

// --- DYNAMIC HANDLERS ---
export const handlers = [
    // 1. Dynamic Query Handler
    http.post('/api/query', async ({ request }) => {
        const body = (await request.json()) as { top_k: number; rerank: boolean };

        // Check if we are in the "After" state
        if (body.rerank === true && body.top_k <= 6) {
            return HttpResponse.json(AFTER_QUERY_RESPONSE);
        }

        // Otherwise, return the "Before" state
        return HttpResponse.json(BEFORE_QUERY_RESPONSE);
    }),

    // 2. Dynamic Trace Handler
    http.get('/api/traces/:trace_id', ({ params }) => {
        const { trace_id } = params;

        // Check which trace to return
        if (trace_id === 'tr_after_fast') {
            return HttpResponse.json(AFTER_TRACE_RESPONSE);
        }

        // Default to "Before" trace
        return HttpResponse.json(BEFORE_TRACE_RESPONSE);
    }),

    // 3. Static Metrics Handler (for now, this is fine)
    http.get('/api/metrics/mini', () => {
        return HttpResponse.json({
            ok: true,
            exp_id: 'monitor_demo',
            window_sec: 600,
            p95_ms: 120.4, // This will still show the "Before" P95
            recall_pct: 82.0, // This will still show the "Before" Recall
            qps: 3.2,
            err_pct: 0.0,
            route_share: {
                milvus: 100.0,
                faiss: 0.0,
                qdrant: 0.0
            },
            samples: 486,
            updated_at: '2025-10-18T19:07:10.002Z'
        });
    }),

    // 4. Experiment Leaderboard Handler
    http.get('/api/experiments/leaderboard', () => {
        return HttpResponse.json({
            "items": [
                {
                    "exp_id": "exp_2025_10_18_001",
                    "created_at": "2025-10-18T10:12:31Z",
                    "engine": "milvus",
                    "params": { "top_k": 8, "rerank": true, "ranker": "bge-m3", "chunk": "512/128" },
                    "p95_ms": 42.7,
                    "qps": 3.9,
                    "err_pct": 0.0,
                    "recall_k": 0.86,
                    "verdict": "PASS"
                },
                {
                    "exp_id": "exp_2025_10_18_002",
                    "created_at": "2025-10-18T11:05:02Z",
                    "engine": "milvus",
                    "params": { "top_k": 20, "rerank": false, "ranker": null, "chunk": "1024/200" },
                    "p95_ms": 95.3,
                    "qps": 2.1,
                    "err_pct": 0.2,
                    "recall_k": 0.81,
                    "verdict": "EDGE"
                }
            ],
            "total": 2
        });
    }),

    // 5. Agent Chat Handler (Dynamic)
    http.post('/api/agent/chat', async ({ request }) => {
        const body = (await request.json()) as { message: string };

        // --- Story B: Code Lookup ---
        if (body.message.includes('code') || body.message.includes('embedding')) {
            return HttpResponse.json({
                "agent": "sf_agent_v3",
                "intent": "code_lookup",
                "query": "show me the Embedding code",
                "summary_md": "Embedding  logic is in **backend_core/embedding/**. Main entrypoint: `embed.py::get_embeddings`.",
                "files": [
                    {
                        "path": "backend_core/embedding/embed.py",
                        "language": "python",
                        "start_line": 12,
                        "end_line": 54,
                        "snippet": "def get_embeddings(texts, model=None, batch_size=32):\n    model = model or os.getenv('EMBED_MODEL', 'bge-small-en')\n    ...\n    return vectors\n",
                        "why_relevant": "Main entrypoint: batches text to vectors."
                    },
                    {
                        "path": "services/fiqa_api/routes/search.py",
                        "language": "python",
                        "start_line": 88,
                        "end_line": 130,
                        "snippet": "from backend_core.embedding.embed import get_embeddings\n...\nq_vec = get_embeddings([query])[0]\nresults = router.search(q_vec, top_k=top_k)\n",
                        "why_relevant": "Usage: Encodes query before search."
                    }
                ]
            });
        }

        // --- Story A: AI Tuning (Default) ---
        return HttpResponse.json({
            "agent": "sf_agent_v3",
            "intent": "optimize_latency",
            "message_md": "Suggestion: Set **top_k** to 8 and **enable rerank (bge-m3)**. \nReason: Current `top_k=20` is noisy. A smaller set with reranking is more stable.",
            "params_patch": {
                "top_k": 8,
                "rerank": true,
                "ranker": "bge-m3",
                "rerank_top_n": 20
            },
            "apply_hint": "I can apply this to the 'Improve' panel for you."
        });
    }),

    // 5b. Agent Code Lookup Handler (for relative URL compatibility)
    http.post('/api/agent/code_lookup', async ({ request }) => {
        const body = (await request.json()) as { message: string };

        // Mock code lookup response with edges_json for graph rendering
        // Note: rid is included for graph viewer functionality
        return HttpResponse.json({
            "rid": "mock-rid-123",
            "agent": "sf_agent_code",
            "intent": "code_lookup",
            "query": body.message,
            "summary_md": `Found code related to: **${body.message}**. Here are the relevant files from the **searchforge** codebase.`,
            "files": [
                {
                    "path": "searchforge/frontend/src/pages/AgentStudioPage.tsx",
                    "language": "typescript",
                    "start_line": 88,
                    "end_line": 120,
                    "snippet": "export const AgentStudioPage = () => {\n    const { message } = App.useApp();\n    const [fsmState, dispatch] = useReducer(fsmReducer, {\n        phase: 'idle',\n        requestId: '',\n        edgesJson: [],\n        error: null\n    });\n    ...",
                    "why_relevant": "Main Agent Studio component with state management and FSM logic."
                },
                {
                    "path": "frontend/src/components/flowgraph/SimpleFlowGraph.tsx",
                    "language": "typescript",
                    "start_line": 31,
                    "end_line": 65,
                    "snippet": "const SimpleFlowGraph: React.FC<SimpleFlowGraphProps> = ({\n    phase,\n    containerId,\n    edgesJson,\n    maxNodes,\n    onNodeClick,\n    onGraphReady,\n    onError,\n    currentRequestId,\n    dispatch\n}) => {\n    const containerRef = useRef<HTMLDivElement>(null);\n    ...",
                    "why_relevant": "Flow graph rendering component using Mermaid for code relationship visualization."
                },
                {
                    "path": "frontend/src/mocks/handlers.ts",
                    "language": "typescript",
                    "start_line": 71,
                    "end_line": 96,
                    "snippet": "export const handlers = [\n    http.post('/api/query', async ({ request }) => {\n        const body = (await request.json()) as { top_k: number; rerank: boolean };\n        if (body.rerank === true && body.top_k <= 6) {\n            return HttpResponse.json(AFTER_QUERY_RESPONSE);\n        }\n        return HttpResponse.json(BEFORE_QUERY_RESPONSE);\n    }),\n    ...",
                    "why_relevant": "MSW mock handlers for API endpoints in development and testing."
                }
            ],
            "edges_json": [
                {
                    "src": "frontend/src/pages/AgentStudioPage.tsx::AgentStudioPage",
                    "dst": "frontend/src/components/flowgraph/SimpleFlowGraph.tsx::SimpleFlowGraph",
                    "type": "calls"
                },
                {
                    "src": "frontend/src/pages/AgentStudioPage.tsx::AgentStudioPage",
                    "dst": "frontend/src/mocks/handlers.ts::handlers",
                    "type": "calls"
                },
                {
                    "src": "frontend/src/components/flowgraph/SimpleFlowGraph.tsx::SimpleFlowGraph",
                    "dst": "mermaid::render",
                    "type": "calls"
                }
            ]
        });
    }),

    // 6. RAG Triad Details Handler
    http.get('/api/experiments/:exp_id/rag-triad', ({ params }) => {
        const { exp_id } = params;
        // We return the same mock data regardless of ID for this demo
        return HttpResponse.json({
            "exp_id": exp_id,
            "summary": {
                "context_relevance": 0.88,
                "groundedness": 0.92,
                "answer_relevance": 0.84
            },
            "samples": [
                {
                    "trace_id": "t_001",
                    "question": "What is SearchForge Milvus lane?",
                    "answer_snippet": "Milvus lane serves as the primary vector backend...",
                    "evidence_snippet": "We store embeddings in Milvus and route 100% traffic...",
                    "scores": { "context_relevance": 0.91, "groundedness": 0.95, "answer_relevance": 0.87 },
                    "labels": ["✓ grounded", "✓ relevant", "✓ adequate"]
                },
                {
                    "trace_id": "t_002",
                    "question": "How to reduce P95 latency?",
                    "answer_snippet": "Lower top_k and enable rerank...",
                    "evidence_snippet": "A/B test shows top_k 8 + rerank bge-m3 drops P95 by 18%...",
                    "scores": { "context_relevance": 0.85, "groundedness": 0.90, "answer_relevance": 0.82 },
                    "labels": ["✓ grounded", "✓ relevant", "✓ adequate"]
                }
            ]
        });
    }),

    // 7. Retriever Lab Simulation Handler
    http.get('/api/labs/retriever/simulate', ({ request }) => {
        const url = new URL(request.url);
        const ef = url.searchParams.get('ef') || '50'; // Default to 'Before' state

        // --- "AFTER" State (ef=200, Faster, Higher Recall) ---
        if (ef === '200') {
            return HttpResponse.json({
                ok: true,
                params: { ef: 200 },
                results: [
                    { doc_id: 'doc_A', score: 0.95, text_snippet: "Snippet A (More relevant, found with higher ef)..." },
                    { doc_id: 'doc_C', score: 0.92, text_snippet: "Snippet C (Also relevant)..." },
                ],
                metrics: { p95_ms: 15.5, recall_at_10: 0.98 },
            });
        }

        // --- "BEFORE" State (ef=50, Slower, Lower Recall) ---
        return HttpResponse.json({
            ok: true,
            params: { ef: 50 },
            results: [
                { doc_id: 'doc_B', score: 0.88, text_snippet: "Snippet B (Less relevant, found with lower ef)..." },
                { doc_id: 'doc_A', score: 0.85, text_snippet: "Snippet A..." },
            ],
            metrics: { p95_ms: 50.2, recall_at_10: 0.85 },
        });
    }),

    // 8. Ranker Lab Simulation Handler
    http.get('/api/labs/ranker/simulate', () => {
        // For simplicity, we return both results at once in this mock
        // In a real app, you might fetch them separately based on selection

        const modelA_Results = {
            ok: true,
            model_name: "Cross-Encoder (Fast)",
            results: [
                { doc_id: 'doc_X', score: 0.91, text_snippet: "Snippet X (Ranked higher by fast model)..." },
                { doc_id: 'doc_Y', score: 0.85, text_snippet: "Snippet Y..." },
            ],
            metrics: { ndcg_at_10: 0.75, latency_ms: 25.0 },
        };

        const modelB_Results = {
            ok: true,
            model_name: "LLM Ranker (Quality)",
            results: [
                { doc_id: 'doc_Y', score: 0.96, text_snippet: "Snippet Y (Ranked higher by quality model)..." },
                { doc_id: 'doc_X', score: 0.90, text_snippet: "Snippet X..." },
                { doc_id: 'doc_Z', score: 0.88, text_snippet: "Snippet Z (Only found by quality model)..." },
            ],
            metrics: { ndcg_at_10: 0.88, latency_ms: 150.0 }, // Higher quality, higher latency
        };

        // Return both in an array for the frontend to display side-by-side
        return HttpResponse.json([modelA_Results, modelB_Results]);
    }),

    // 9. Index Explorer Handler
    http.get('/api/index/browse', () => {
        // Example edges data (as a string)
        const exampleEdgesJson = JSON.stringify([
            { 'src': 'scripts/index_codebase.py::initialize_clients', 'dst': 'QdrantClient', 'etype': 'calls', 'loc': 135 },
            { 'src': 'scripts/index_codebase.py::initialize_clients', 'dst': 'SentenceTransformer', 'etype': 'calls', 'loc': 144 },
            { 'src': 'scripts/index_codebase.py::main', 'dst': 'initialize_clients', 'etype': 'calls', 'loc': 415 },
            { 'src': 'scripts/index_codebase.py::main', 'dst': 'load_dotenv', 'etype': 'imports', 'loc': 15 }
        ]);

        // In a real API, use offset/limit from query params
        return HttpResponse.json({
            ok: true,
            points: [
                {
                    id: 'uuid-1',
                    payload: {
                        text: "def initialize_clients(embedding_model_name: str):\n    \"\"\"\n    Initialize Qdrant client and embedding model.\n    ...", // Truncated snippet
                        file_path: "scripts/index_codebase.py",
                        chunk_index: 2,
                        kind: 'function',
                        name: 'initialize_clients',
                        start_line: 130,
                        end_line: 150,
                        edges_json: exampleEdgesJson // Mock edges for this point
                    }
                },
                {
                    id: 'uuid-2',
                    payload: {
                        text: "const handleSearch = (query: string) => {\n    if (!query) return;\n    setIsLoading(true);\n    ...", // Truncated snippet
                        file_path: "frontend/src/components/console/QueryConsole.tsx",
                        chunk_index: 5,
                        kind: 'function',
                        name: 'handleSearch',
                        start_line: 25,
                        end_line: 60,
                        // No edges_json here
                    }
                },
                {
                    id: 'uuid-3',
                    payload: {
                        text: "This file contains the main FastAPI application setup...",
                        file_path: "services/fiqa_api/app_main.py",
                        chunk_index: 0,
                        kind: 'file',
                        // No specific name/lines for file point
                        // No edges_json here
                    }
                }
            ],
            total: 3, // Mock total
            // next_page_offset: "offset-3" // Example pagination token
        });
    }),

    // 10. AutoTuner Status Handler (simple state machine)
    // COMMENTED OUT: Now using real backend API via proxy
    // http.get('/api/autotuner/status', () => {
    //     if (tunerStatus === 'running') {
    //         tunerProgress = Math.min(100, tunerProgress + 15);
    //         if (tunerProgress >= 100) tunerStatus = 'completed';
    //     }
    //     return HttpResponse.json({
    //         ok: true,
    //         job_id: 'tune_job_mock_123',
    //         status: tunerStatus,
    //         current_params: tunerStatus === 'running' ? { top_k: 8, rerank: true } : { top_k: 20, rerank: false },
    //         progress: tunerStatus === 'running' ? tunerProgress : undefined,
    //         last_update: new Date().toISOString(),
    //     });
    // }),

    // 11. Start AutoTuner Job
    // COMMENTED OUT: Now using real backend API via proxy
    // http.post('/api/autotuner/start', () => {
    //     tunerStatus = 'running';
    //     tunerProgress = 0;
    //     return HttpResponse.json({ ok: true, job_id: 'tune_job_mock_123' });
    // }),

    // 12. Stop AutoTuner Job
    // COMMENTED OUT: Now using real backend API via proxy
    // http.post('/api/autotuner/stop', () => {
    //     tunerStatus = 'idle';
    //     tunerProgress = 0;
    //     return HttpResponse.json({ ok: true });
    // }),

    // 13. AutoTuner Recommendations
    // COMMENTED OUT: Now using real backend API via proxy
    // http.get('/api/autotuner/recommendations', () => {
    //     return HttpResponse.json({
    //         ok: true,
    //         job_id: 'tune_job_mock_123',
    //         recommendations: [
    //             {
    //                 params: { top_k: 8, rerank: true },
    //                 estimated_impact: { delta_p95_ms: -35.2, delta_recall_pct: -1.5 },
    //                 reason: "Reduced top_k significantly lowers retrieval latency. Rerank mitigates recall drop.",
    //                 timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 mins ago
    //             },
    //             {
    //                 params: { top_k: 12, rerank: false },
    //                 estimated_impact: { delta_p95_ms: -10.1, delta_recall_pct: 0.5 },
    //                 reason: "Slightly lower top_k provides minor latency benefit without rerank cost.",
    //                 timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10 mins ago
    //             }
    //         ],
    //     });
    // }),
];

