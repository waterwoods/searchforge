#!/usr/bin/env node
/**
 * Adapter Probe - Test adapter transformations
 * Fetches raw data and runs through adapters
 */

import http from 'http';

const BASE_URL = 'http://localhost:8011';

// ========================================
// Inline Adapters (minimal versions)
// ========================================

function adaptForceStatus(raw) {
    if (!raw) return { ok: false, forceOverride: false, hardCap: false, params: {}, precedence: [] };
    return {
        ok: Boolean(raw.ok),
        forceOverride: Boolean(raw.force_override),
        hardCap: Boolean(raw.hard_cap_enabled),
        params: {
            numCandidates: raw.effective_params?.num_candidates || 0,
            rerankTopK: raw.effective_params?.rerank_topk || 0,
            qps: raw.effective_params?.qps || 0,
        },
        precedence: (raw.precedence_chain || []).slice(0, 10),
    };
}

function adaptVerify(raw) {
    if (!raw) return { ok: false, service: 'unknown', proxyToV2: false, data: {}, shadowPct: 0 };
    return {
        ok: Boolean(raw.ok),
        service: String(raw.service || 'unknown'),
        proxyToV2: Boolean(raw.proxy_to_v2),
        data: {
            redis: Boolean(raw.data_sources?.redis?.ok),
            qdrant: Boolean(raw.data_sources?.qdrant?.ok),
        },
        shadowPct: raw.shadow?.pct || 0,
    };
}

function adaptBlackSwanStatus(raw) {
    if (!raw) return { ok: false, phase: 'idle', progress: 0, runId: null };
    const validPhases = ['idle', 'warmup', 'baseline', 'trip', 'recovery', 'complete', 'error'];
    let phase = String(raw.phase || 'idle').toLowerCase();
    if (!validPhases.includes(phase)) phase = 'error';

    return {
        ok: raw.ok !== false,
        phase,
        progress: Math.max(0, Math.min(100, raw.progress || 0)),
        runId: raw.run_id || null,
    };
}

function adaptQdrantStats(raw) {
    if (!raw) return { ok: false, hits60s: 0, p95ms: null, remotePct: null };
    return {
        ok: Boolean(raw.ok),
        hits60s: raw.hits_60s || 0,
        p95ms: raw.p95_query_ms_60s ?? null,
        remotePct: raw.remote_pct_60s ?? null,
    };
}

function adaptQAFeed(raw) {
    if (!raw || !Array.isArray(raw.items)) return { ok: false, items: [], circuitOpen: false };
    return {
        ok: Boolean(raw.ok),
        items: raw.items.map(item => ({
            t: item.ts || 0,
            query: String(item.query || ''),
            topK: item.topk || 0,
            rerankTopK: item.rerank_k ?? null,
            latencyMs: item.latency_ms ?? null,
        })),
        circuitOpen: Boolean(raw.circuit_open),
    };
}

// ========================================
// Fetch and Probe
// ========================================

async function fetchEndpoint(path) {
    return new Promise((resolve) => {
        const url = `${BASE_URL}${path}`;
        http.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, data: parsed, status: res.statusCode });
                } catch (err) {
                    resolve({ ok: false, error: 'invalid_json', status: res.statusCode });
                }
            });
        }).on('error', (err) => {
            resolve({ ok: false, error: err.message, status: 0 });
        });
    });
}

async function main() {
    console.log('================================================================');
    console.log('ADAPTER VERIFICATION MINI REPORT');
    console.log('================================================================');
    console.log(`Generated: ${new Date().toISOString()}`);
    console.log(`Base URL: ${BASE_URL}`);
    console.log('');

    console.log('=== ENDPOINT AVAILABILITY ===');
    const endpoints = [
        ['/api/verify', 'verify'],
        ['/api/force_status', 'force_status'],
        ['/api/black_swan/config', 'black_swan_config'],
        ['/api/black_swan/status', 'black_swan_status'],
        ['/api/qdrant/stats', 'qdrant_stats'],
        ['/api/qa/feed?limit=5', 'qa_feed'],
    ];

    const results = [];
    for (const [path, name] of endpoints) {
        const result = await fetchEndpoint(path);
        const status = result.ok ? `OK [${result.status}]` : `FAIL [${result.status}]`;
        console.log(`  ${name.padEnd(25)} ${status}`);
        results.push({ path, name, ...result });
    }

    console.log('');
    console.log('=== ADAPTER SHAPES ===');

    // Test force_status adapter
    const forceResult = results.find(r => r.name === 'force_status');
    if (forceResult?.ok) {
        const adapted = adaptForceStatus(forceResult.data);
        console.log(`  force_status:`);
        console.log(`    ok: ${adapted.ok}`);
        console.log(`    forceOverride: ${adapted.forceOverride}`);
        console.log(`    hardCap: ${adapted.hardCap}`);
        console.log(`    params.numCandidates: ${adapted.params.numCandidates}`);
        console.log(`    params.rerankTopK: ${adapted.params.rerankTopK}`);
        console.log(`    params.qps: ${adapted.params.qps}`);
        console.log(`    precedence: [${adapted.precedence.length} items]`);
    }

    // Test verify adapter
    const verifyResult = results.find(r => r.name === 'verify');
    if (verifyResult?.ok) {
        const adapted = adaptVerify(verifyResult.data);
        console.log(`  verify:`);
        console.log(`    ok: ${adapted.ok}`);
        console.log(`    service: ${adapted.service}`);
        console.log(`    proxyToV2: ${adapted.proxyToV2}`);
        console.log(`    data.redis: ${adapted.data.redis}`);
        console.log(`    data.qdrant: ${adapted.data.qdrant}`);
        console.log(`    shadowPct: ${adapted.shadowPct}`);
    }

    // Test black_swan_status adapter
    const bsResult = results.find(r => r.name === 'black_swan_status');
    if (bsResult?.ok) {
        const adapted = adaptBlackSwanStatus(bsResult.data);
        console.log(`  black_swan_status:`);
        console.log(`    ok: ${adapted.ok}`);
        console.log(`    phase: ${adapted.phase}`);
        console.log(`    progress: ${adapted.progress}`);
        console.log(`    runId: ${adapted.runId || 'null'}`);
    }

    // Test qdrant_stats adapter
    const qsResult = results.find(r => r.name === 'qdrant_stats');
    if (qsResult?.ok) {
        const adapted = adaptQdrantStats(qsResult.data);
        console.log(`  qdrant_stats:`);
        console.log(`    ok: ${adapted.ok}`);
        console.log(`    hits60s: ${adapted.hits60s}`);
        console.log(`    p95ms: ${adapted.p95ms ?? 'null'}`);
        console.log(`    remotePct: ${adapted.remotePct ?? 'null'}`);
    }

    // Test qa_feed adapter
    const qafResult = results.find(r => r.name === 'qa_feed');
    if (qafResult?.ok) {
        const adapted = adaptQAFeed(qafResult.data);
        console.log(`  qa_feed:`);
        console.log(`    ok: ${adapted.ok}`);
        console.log(`    items: [${adapted.items.length} items]`);
        console.log(`    circuitOpen: ${adapted.circuitOpen}`);
        if (adapted.items.length > 0) {
            const first = adapted.items[0];
            console.log(`    sample[0].query: "${first.query.slice(0, 40)}..."`);
            console.log(`    sample[0].topK: ${first.topK}`);
        }
    }

    console.log('');
    console.log('=== VERDICT ===');
    const available = results.filter(r => r.ok).length;
    const total = results.length;
    const allOk = available === total;
    console.log(`  Availability: ${available}/${total}`);
    console.log(`  Status: ${allOk ? 'PASSED' : 'PARTIAL'}`);
    console.log('');
    console.log('=== END OF REPORT ===');

    process.exit(allOk ? 0 : 1);
}

main().catch(err => {
    console.error('ERROR:', err.message);
    process.exit(1);
});

