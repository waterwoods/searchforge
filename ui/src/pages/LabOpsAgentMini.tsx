/**
 * LabOps Agent Mini Dashboard - Read-only agent report display
 * Shows last agent run: verdict, 3 key metrics + FAISS% (if combo)
 * No polling - manual refresh only
 */

import { useState } from 'react'
import { fetchLabOpsReport, toStringSafe, type SafeLabOpsReport } from '../adapters'

export function LabOpsAgentMini() {
    const [report, setReport] = useState<SafeLabOpsReport | null>(null)
    const [loading, setLoading] = useState(false)
    const [lastFetchTime, setLastFetchTime] = useState<string>('-')

    const handleFetch = async () => {
        setLoading(true)
        try {
            const data = await fetchLabOpsReport()
            setReport(data)
            setLastFetchTime(new Date().toLocaleTimeString())
        } catch (error) {
            console.error('Fetch error:', error)
            setReport({
                ok: false,
                verdict: null,
                deltaP95Pct: 0,
                deltaQpsPct: 0,
                errorRatePct: 0,
                faissSharePct: 0,
                applied: false,
                applyCommand: null,
                message: `Unexpected error: ${toStringSafe(error)}`,
                generatedAt: '-'
            })
        } finally {
            setLoading(false)
        }
    }

    const formatPercent = (value: number): string => {
        const sign = value > 0 ? '+' : ''
        return `${sign}${value.toFixed(1)}%`
    }

    const getStatusColor = (ok: boolean): string => {
        return ok ? '#4ade80' : '#94a3b8'
    }

    const getVerdictColor = (verdict: string | null): string => {
        if (!verdict) return '#94a3b8'
        if (verdict === 'PASS') return '#4ade80'
        if (verdict === 'EDGE') return '#fbbf24'
        return '#f87171'
    }

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h1 style={styles.title}>LabOps Agent Mini</h1>
                <div style={styles.subtitle}>Last Autonomous Experiment Report</div>
            </header>

            <div style={styles.main}>
                <button
                    onClick={handleFetch}
                    disabled={loading}
                    style={{
                        ...styles.button,
                        ...(loading ? styles.buttonDisabled : {})
                    }}
                >
                    {loading ? 'Loading...' : 'Fetch Last Report'}
                </button>

                {report && (
                    <>
                        <div style={styles.statusBar}>
                            <div style={styles.statusItem}>
                                <span style={styles.statusLabel}>Status:</span>
                                <span style={{
                                    ...styles.statusValue,
                                    color: getStatusColor(report.ok)
                                }}>
                                    {toStringSafe(report.ok ? 'OK' : 'No Data')}
                                </span>
                            </div>
                            <div style={styles.statusItem}>
                                <span style={styles.statusLabel}>Verdict:</span>
                                <span style={{
                                    ...styles.statusValue,
                                    color: getVerdictColor(report.verdict),
                                    fontWeight: 700
                                }}>
                                    {toStringSafe(report.verdict || 'N/A')}
                                </span>
                            </div>
                            <div style={styles.statusItem}>
                                <span style={styles.statusLabel}>Applied:</span>
                                <span style={{
                                    ...styles.statusValue,
                                    color: report.applied ? '#4ade80' : '#94a3b8'
                                }}>
                                    {toStringSafe(report.applied ? 'YES' : 'NO')}
                                </span>
                            </div>
                            <div style={styles.statusItem}>
                                <span style={styles.statusLabel}>Generated:</span>
                                <span style={styles.statusValue}>
                                    {toStringSafe(report.generatedAt)}
                                </span>
                            </div>
                            <div style={styles.statusItem}>
                                <span style={styles.statusLabel}>Last Fetch:</span>
                                <span style={styles.statusValue}>
                                    {toStringSafe(lastFetchTime)}
                                </span>
                            </div>
                        </div>

                        <div style={styles.metricsGrid}>
                            <div style={styles.metricCard}>
                                <div style={styles.metricLabel}>ΔP95%</div>
                                <div style={{
                                    ...styles.metricValue,
                                    color: report.deltaP95Pct <= 0 ? '#4ade80' : '#f87171'
                                }}>
                                    {toStringSafe(formatPercent(report.deltaP95Pct))}
                                </div>
                                <div style={styles.metricHint}>P95 latency change</div>
                            </div>

                            <div style={styles.metricCard}>
                                <div style={styles.metricLabel}>ΔQPS%</div>
                                <div style={{
                                    ...styles.metricValue,
                                    color: report.deltaQpsPct >= 0 ? '#4ade80' : '#f87171'
                                }}>
                                    {toStringSafe(formatPercent(report.deltaQpsPct))}
                                </div>
                                <div style={styles.metricHint}>QPS change</div>
                            </div>

                            <div style={styles.metricCard}>
                                <div style={styles.metricLabel}>Err%</div>
                                <div style={{
                                    ...styles.metricValue,
                                    color: report.errorRatePct === 0 ? '#4ade80' : '#f87171'
                                }}>
                                    {toStringSafe(report.errorRatePct.toFixed(2))}%
                                </div>
                                <div style={styles.metricHint}>Error rate</div>
                            </div>

                            {report.faissSharePct > 0 && (
                                <div style={styles.metricCard}>
                                    <div style={styles.metricLabel}>FAISS%</div>
                                    <div style={{
                                        ...styles.metricValue,
                                        color: '#a78bfa'
                                    }}>
                                        {toStringSafe(report.faissSharePct.toFixed(1))}%
                                    </div>
                                    <div style={styles.metricHint}>FAISS routing share</div>
                                </div>
                            )}
                        </div>

                        {report.message && (
                            <div style={styles.messageBox}>
                                <div style={styles.messageLabel}>Message:</div>
                                <div style={styles.messageText}>
                                    {toStringSafe(report.message)}
                                </div>
                            </div>
                        )}

                        {report.applyCommand && !report.applied && (
                            <div style={styles.commandBox}>
                                <div style={styles.commandLabel}>
                                    ⚠️ Safe Mode - Manual Apply Required:
                                </div>
                                <pre style={styles.commandText}>
                                    {toStringSafe(report.applyCommand)}
                                </pre>
                            </div>
                        )}
                    </>
                )}

                {!report && (
                    <div style={styles.emptyState}>
                        <div style={styles.emptyIcon}>🤖</div>
                        <div style={styles.emptyText}>
                            Click "Fetch Last Report" to load agent results
                        </div>
                    </div>
                )}
            </div>

            <footer style={styles.footer}>
                <div style={styles.footerText}>
                    LabOps Agent V1 - Autonomous COMBO Experiment Orchestration
                </div>
            </footer>
        </div>
    )
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        color: '#e2e8f0',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column'
    },
    header: {
        textAlign: 'center',
        marginBottom: '3rem'
    },
    title: {
        fontSize: '2.5rem',
        fontWeight: 700,
        margin: 0,
        marginBottom: '0.5rem',
        background: 'linear-gradient(to right, #60a5fa, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent'
    },
    subtitle: {
        fontSize: '1rem',
        color: '#94a3b8'
    },
    main: {
        maxWidth: '1000px',
        margin: '0 auto',
        width: '100%',
        flex: 1
    },
    button: {
        width: '100%',
        padding: '1rem 2rem',
        fontSize: '1.125rem',
        fontWeight: 600,
        color: '#ffffff',
        backgroundColor: '#3b82f6',
        border: 'none',
        borderRadius: '0.5rem',
        cursor: 'pointer',
        transition: 'all 0.2s',
        marginBottom: '2rem'
    },
    buttonDisabled: {
        backgroundColor: '#475569',
        cursor: 'not-allowed',
        opacity: 0.6
    },
    statusBar: {
        display: 'flex',
        justifyContent: 'space-around',
        padding: '1rem',
        backgroundColor: '#1e293b',
        borderRadius: '0.5rem',
        marginBottom: '2rem',
        flexWrap: 'wrap',
        gap: '1rem'
    },
    statusItem: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.25rem'
    },
    statusLabel: {
        fontSize: '0.875rem',
        color: '#94a3b8'
    },
    statusValue: {
        fontSize: '1rem',
        fontWeight: 600
    },
    metricsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
    },
    metricCard: {
        backgroundColor: '#1e293b',
        padding: '2rem',
        borderRadius: '0.75rem',
        textAlign: 'center',
        border: '1px solid #334155',
        transition: 'transform 0.2s',
        cursor: 'default'
    },
    metricLabel: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        marginBottom: '1rem'
    },
    metricValue: {
        fontSize: '2.5rem',
        fontWeight: 700,
        marginBottom: '0.5rem',
        lineHeight: 1
    },
    metricHint: {
        fontSize: '0.875rem',
        color: '#64748b'
    },
    messageBox: {
        backgroundColor: '#1e293b',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        border: '1px solid #334155',
        marginBottom: '1rem'
    },
    messageLabel: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        fontWeight: 600,
        marginBottom: '0.5rem'
    },
    messageText: {
        fontSize: '1rem',
        color: '#e2e8f0',
        lineHeight: 1.6
    },
    commandBox: {
        backgroundColor: '#1e293b',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        border: '2px solid #fbbf24'
    },
    commandLabel: {
        fontSize: '0.875rem',
        color: '#fbbf24',
        fontWeight: 600,
        marginBottom: '1rem'
    },
    commandText: {
        fontSize: '0.875rem',
        color: '#e2e8f0',
        backgroundColor: '#0f172a',
        padding: '1rem',
        borderRadius: '0.25rem',
        overflowX: 'auto',
        whiteSpace: 'pre-wrap',
        lineHeight: 1.6,
        fontFamily: 'Monaco, Consolas, monospace'
    },
    emptyState: {
        textAlign: 'center',
        padding: '4rem 2rem',
        color: '#64748b'
    },
    emptyIcon: {
        fontSize: '4rem',
        marginBottom: '1rem'
    },
    emptyText: {
        fontSize: '1.125rem'
    },
    footer: {
        marginTop: '3rem',
        textAlign: 'center',
        paddingTop: '2rem',
        borderTop: '1px solid #334155'
    },
    footerText: {
        fontSize: '0.875rem',
        color: '#64748b'
    }
}

