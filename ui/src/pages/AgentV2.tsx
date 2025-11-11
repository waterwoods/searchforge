/**
 * Agent V2 Micro UI - Rule-based agent control panel
 * Read-only display: 3 metrics + explanation bullets
 * Actions: Run (Dry), Run (Real), Refresh
 * No polling - manual refresh only
 */

import { useState } from 'react'

// Types
interface AgentV2Summary {
    ok: boolean
    delta_p95_pct: number
    delta_qps_pct: number
    error_rate_pct: number
    bullets: string[]
    generated_at: string | null
}

interface AgentV2RunResult {
    ok: boolean
    mode: 'dry' | 'live'
    verdict: string
    timestamp: string
    message?: string
}

// API calls - using proxy /api path
const API_BASE = ''  // Empty string uses same origin (proxy)

async function fetchSummary(): Promise<AgentV2Summary> {
    const resp = await fetch(`${API_BASE}/api/agent/summary?v=2`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return resp.json()
}

async function runAgent(dry: boolean): Promise<AgentV2RunResult> {
    const resp = await fetch(`${API_BASE}/api/agent/run?v=2&dry=${dry}`, {
        method: 'POST'
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    return resp.json()
}

export function AgentV2() {
    const [summary, setSummary] = useState<AgentV2Summary | null>(null)
    const [loading, setLoading] = useState(false)
    const [running, setRunning] = useState(false)
    const [lastAction, setLastAction] = useState<string>('-')

    const handleRefresh = async () => {
        setLoading(true)
        try {
            const data = await fetchSummary()
            setSummary(data)
            setLastAction(`Refreshed at ${new Date().toLocaleTimeString()}`)
        } catch (error) {
            console.error('Fetch error:', error)
            setSummary({
                ok: false,
                delta_p95_pct: 0,
                delta_qps_pct: 0,
                error_rate_pct: 0,
                bullets: [`Error: ${String(error).slice(0, 50)}`],
                generated_at: null
            })
        } finally {
            setLoading(false)
        }
    }

    const handleRun = async (dry: boolean) => {
        setRunning(true)
        try {
            const result = await runAgent(dry)
            setLastAction(`${dry ? 'Dry' : 'Real'} run: ${result.verdict} (${result.timestamp.slice(0, 19)})`)

            // Auto-refresh summary after run
            await new Promise(resolve => setTimeout(resolve, 500))
            await handleRefresh()
        } catch (error) {
            console.error('Run error:', error)
            setLastAction(`Run failed: ${String(error).slice(0, 50)}`)
        } finally {
            setRunning(false)
        }
    }

    const formatPercent = (value: number): string => {
        const sign = value > 0 ? '+' : ''
        return `${sign}${value.toFixed(1)}%`
    }

    const getMetricColor = (value: number, isError: boolean = false): string => {
        if (isError) {
            // Error rate: lower is better
            if (value >= 1.0) return '#f87171'  // red
            if (value >= 0.5) return '#fbbf24'  // yellow
            return '#4ade80'  // green
        } else {
            // P95/QPS: negative is improvement
            if (value <= -10) return '#4ade80'  // green
            if (value <= -5) return '#fbbf24'   // yellow
            if (value > 0) return '#f87171'     // red
            return '#94a3b8'  // gray
        }
    }

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h1 style={styles.title}>Agent V2 - Rule-based</h1>
                <div style={styles.subtitle}>No LLM • Template Explainer • Read-only</div>
            </header>

            <div style={styles.main}>
                {/* Action buttons */}
                <div style={styles.buttonGroup}>
                    <button
                        onClick={() => handleRun(true)}
                        disabled={loading || running}
                        style={{
                            ...styles.button,
                            ...styles.buttonDry,
                            ...(loading || running ? styles.buttonDisabled : {})
                        }}
                    >
                        {running ? 'Running...' : 'Run (Dry)'}
                    </button>

                    <button
                        onClick={() => handleRun(false)}
                        disabled={loading || running}
                        style={{
                            ...styles.button,
                            ...styles.buttonReal,
                            ...(loading || running ? styles.buttonDisabled : {})
                        }}
                    >
                        {running ? 'Running...' : 'Run (Real)'}
                    </button>

                    <button
                        onClick={handleRefresh}
                        disabled={loading || running}
                        style={{
                            ...styles.button,
                            ...(loading || running ? styles.buttonDisabled : {})
                        }}
                    >
                        {loading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>

                {/* Last action */}
                <div style={styles.lastAction}>
                    {lastAction}
                </div>

                {/* Metrics display */}
                {summary && (
                    <div style={styles.metricsContainer}>
                        <div style={styles.metricCard}>
                            <div style={styles.metricLabel}>ΔP95%</div>
                            <div style={{
                                ...styles.metricValue,
                                color: getMetricColor(summary.delta_p95_pct)
                            }}>
                                {formatPercent(summary.delta_p95_pct)}
                            </div>
                        </div>

                        <div style={styles.metricCard}>
                            <div style={styles.metricLabel}>ΔQPS%</div>
                            <div style={{
                                ...styles.metricValue,
                                color: getMetricColor(summary.delta_qps_pct)
                            }}>
                                {formatPercent(summary.delta_qps_pct)}
                            </div>
                        </div>

                        <div style={styles.metricCard}>
                            <div style={styles.metricLabel}>Error Rate</div>
                            <div style={{
                                ...styles.metricValue,
                                color: getMetricColor(summary.error_rate_pct, true)
                            }}>
                                {summary.error_rate_pct.toFixed(2)}%
                            </div>
                        </div>
                    </div>
                )}

                {/* Explanation bullets */}
                {summary && summary.bullets && summary.bullets.length > 0 && (
                    <div style={styles.explanationContainer}>
                        <h3 style={styles.explanationTitle}>Explainer (Rule-based)</h3>
                        <ul style={styles.bulletList}>
                            {summary.bullets.map((bullet, idx) => (
                                <li key={idx} style={styles.bulletItem}>
                                    {bullet || '—'}
                                </li>
                            ))}
                        </ul>
                        {summary.generated_at && (
                            <div style={styles.timestamp}>
                                Generated: {summary.generated_at}
                            </div>
                        )}
                    </div>
                )}

                {!summary && (
                    <div style={styles.placeholder}>
                        Click "Refresh" to load last summary
                    </div>
                )}
            </div>

            <footer style={styles.footer}>
                Agent V2 • No LLM calls • Rule-based explainer only
            </footer>
        </div>
    )
}

// Styles
const styles: Record<string, React.CSSProperties> = {
    container: {
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: '#f1f5f9',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '2rem'
    },
    header: {
        textAlign: 'center',
        marginBottom: '2rem'
    },
    title: {
        fontSize: '2rem',
        fontWeight: 700,
        margin: 0,
        background: 'linear-gradient(90deg, #60a5fa, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text'
    },
    subtitle: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginTop: '0.5rem'
    },
    main: {
        maxWidth: '800px',
        margin: '0 auto'
    },
    buttonGroup: {
        display: 'flex',
        gap: '1rem',
        marginBottom: '1rem',
        justifyContent: 'center'
    },
    button: {
        padding: '0.75rem 1.5rem',
        fontSize: '1rem',
        fontWeight: 600,
        border: 'none',
        borderRadius: '0.5rem',
        cursor: 'pointer',
        transition: 'all 0.2s',
        background: '#3b82f6',
        color: 'white'
    },
    buttonDry: {
        background: '#6366f1'
    },
    buttonReal: {
        background: '#ef4444'
    },
    buttonDisabled: {
        opacity: 0.5,
        cursor: 'not-allowed'
    },
    lastAction: {
        textAlign: 'center',
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginBottom: '1.5rem',
        minHeight: '1.5rem'
    },
    metricsContainer: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '1rem',
        marginBottom: '2rem'
    },
    metricCard: {
        background: 'rgba(30, 41, 59, 0.8)',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        textAlign: 'center',
        border: '1px solid rgba(148, 163, 184, 0.2)'
    },
    metricLabel: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginBottom: '0.5rem',
        fontWeight: 500
    },
    metricValue: {
        fontSize: '2rem',
        fontWeight: 700
    },
    explanationContainer: {
        background: 'rgba(30, 41, 59, 0.6)',
        borderRadius: '0.75rem',
        padding: '1.5rem',
        border: '1px solid rgba(148, 163, 184, 0.2)'
    },
    explanationTitle: {
        fontSize: '1.125rem',
        fontWeight: 600,
        marginTop: 0,
        marginBottom: '1rem',
        color: '#a78bfa'
    },
    bulletList: {
        listStyle: 'none',
        padding: 0,
        margin: 0
    },
    bulletItem: {
        padding: '0.5rem 0',
        borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
        fontSize: '0.875rem',
        lineHeight: '1.5'
    },
    timestamp: {
        marginTop: '1rem',
        fontSize: '0.75rem',
        color: '#64748b',
        textAlign: 'right'
    },
    placeholder: {
        textAlign: 'center',
        padding: '3rem',
        color: '#64748b',
        fontSize: '1rem'
    },
    footer: {
        marginTop: '3rem',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: '#475569'
    }
}

