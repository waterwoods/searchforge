/**
 * Mini Dashboard - Read-only metrics display
 * Shows 3 key metrics from lab report: ΔP95%, ΔQPS%, Err%
 */

import { useState } from 'react'
import { fetchMiniReport, toStringSafe, type SafeMiniReport } from '../adapters'

export function MiniDashboard() {
    const [report, setReport] = useState<SafeMiniReport | null>(null)
    const [loading, setLoading] = useState(false)
    const [lastFetchTime, setLastFetchTime] = useState<string>('-')

    const handleFetch = async () => {
        setLoading(true)
        try {
            const data = await fetchMiniReport()
            setReport(data)
            setLastFetchTime(new Date().toLocaleTimeString())
        } catch (error) {
            console.error('Fetch error:', error)
            // fetchMiniReport already handles errors, so this is just a safety net
            setReport({
                ok: false,
                deltaP95Pct: 0,
                deltaQpsPct: 0,
                errorRatePct: 0,
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

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h1 style={styles.title}>Mini Report</h1>
                <div style={styles.subtitle}>Lab Dashboard Metrics</div>
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
                    {loading ? 'Loading...' : 'Fetch latest report'}
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
                        </div>

                        {report.message && (
                            <div style={styles.messageBox}>
                                <div style={styles.messageLabel}>Message:</div>
                                <div style={styles.messageText}>
                                    {toStringSafe(report.message)}
                                </div>
                            </div>
                        )}
                    </>
                )}

                {!report && (
                    <div style={styles.emptyState}>
                        <div style={styles.emptyIcon}>📊</div>
                        <div style={styles.emptyText}>
                            Click "Fetch latest report" to load metrics
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        color: '#e2e8f0',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '2rem'
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
        maxWidth: '900px',
        margin: '0 auto'
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
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
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
        fontSize: '3rem',
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
        border: '1px solid #334155'
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
    }
}





































