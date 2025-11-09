/**
 * Monitor Panel MVP - 6要素实时监控面板
 * 
 * 功能：
 * 1) 数据源：/api/metrics/mini (600s窗口) + /api/agent/summary (v3→v2回退)
 * 2) 组件：顶部4卡片(P95/Success%/QPS/Route%) + 双轴折线图 + 堆叠条 + 判定条
 * 3) 刷新：3s轮询，失联>10s提示"等待数据…"，不清空历史
 * 4) 防护：NaN/空窗处理，v3失败自动v2回退
 * 5) 路由：/monitor，纯/api前缀，无/ops残留
 */

import { useState, useEffect, useRef } from 'react'

// ========== Types ==========
interface MiniMetricsResponse {
    ok: boolean
    error?: string
    p95: number
    qps: number
    err_pct: number
    route_share: {
        milvus: number
        faiss: number
        qdrant: number
    }
    samples: number
}

interface AgentSummary {
    ok: boolean
    verdict: 'PASS' | 'EDGE' | 'FAIL' | string
    bullets: string[]
    mode?: string
    explainer_mode?: string
    cached?: boolean
    generated_at?: string
}

interface DataPoint {
    time: number  // local time
    p95: number
    qps: number
    err: number
    milvus: number
    faiss: number
    qdrant: number
}

// ========== API ==========
const BASE_API = '' // 相对路径，走前端代理

async function fetchMetrics(expId: string, windowSec: number): Promise<MiniMetricsResponse> {
    const resp = await fetch(`${BASE_API}/api/metrics/mini?exp_id=${expId}&window_sec=${windowSec}`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    return data
}

async function fetchAgentSummary(version: number): Promise<AgentSummary> {
    const url = `${BASE_API}/api/agent/summary?v=${version}`
    console.log(`🔍 Fetching Agent v${version}: ${url}`)

    try {
        const resp = await fetch(url)
        console.log(`📡 Response v${version}: ${resp.status} ${resp.statusText}`)

        if (!resp.ok) {
            // v3 失败 → 自动回退 v2
            if (version === 3) {
                console.warn(`⚠️ Agent v3 failed (${resp.status}), falling back to v2...`)
                return fetchAgentSummary(2)
            }
            throw new Error(`Agent summary v${version} failed: HTTP ${resp.status}`)
        }

        const data = await resp.json()
        console.log(`✅ Agent v${version} success:`, data)
        return data
    } catch (err) {
        // v3 网络错误 → 回退 v2
        if (version === 3) {
            console.warn(`⚠️ Agent v3 error (${err}), falling back to v2...`)
            return fetchAgentSummary(2)
        }
        throw err
    }
}

async function runAgentDry(version: number): Promise<any> {
    const url = `${BASE_API}/api/agent/run?v=${version}&dry=true`
    console.log(`🚀 Running: ${url}`)
    const resp = await fetch(url, { method: 'POST' })
    console.log(`📡 Run response: ${resp.status} ${resp.statusText}`)

    if (!resp.ok) {
        throw new Error(`Agent run failed: HTTP ${resp.status}. Only /api endpoints are supported.`)
    }

    const data = await resp.json()
    console.log(`✅ Run result:`, data)
    return data
}

// ========== Component ==========
export function Monitor() {
    const [dataPoints, setDataPoints] = useState<DataPoint[]>([])
    const [agentData, setAgentData] = useState<AgentSummary | null>(null)
    const [agentVersion, setAgentVersion] = useState<2 | 3>(2)
    const [expId, setExpId] = useState<string>('auto')
    const [expIdInput, setExpIdInput] = useState<string>('auto')
    const [latestWindowTime, setLatestWindowTime] = useState<string>('-')
    const [refreshing, setRefreshing] = useState<boolean>(false)
    const [running, setRunning] = useState<boolean>(false)
    const [error, setError] = useState<string>('')

    const intervalRef = useRef<number | null>(null)
    const lastDataTimeRef = useRef<number>(Date.now())
    const MAX_POINTS = 120  // 10 minutes @ 5s interval
    const POLL_INTERVAL = 3000  // 3秒轮询
    const DISCONNECT_THRESHOLD = 10000  // 失联>10s显示等待提示

    // Fetch metrics with NaN protection and disconnect detection
    const fetchData = async () => {
        const startTime = Date.now()
        try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), 3000)

            const result = await fetchMetrics(expId, 3600)
            clearTimeout(timeoutId)

            const fetchTime = Date.now() - startTime

            if (result.ok && result.samples > 0) {
                const now = Date.now()

                // NaN 防护：确保所有数值有效
                const safeNum = (val: any) => {
                    const num = Number(val)
                    return isNaN(num) || !isFinite(num) ? 0 : num
                }

                const newPoint: DataPoint = {
                    time: now,
                    p95: safeNum(result.p95),
                    qps: safeNum(result.qps),
                    err: safeNum(result.err_pct),
                    milvus: safeNum(result.route_share?.milvus),
                    faiss: safeNum(result.route_share?.faiss),
                    qdrant: safeNum(result.route_share?.qdrant)
                }

                setDataPoints(prev => [...prev, newPoint].slice(-MAX_POINTS))
                setLatestWindowTime(new Date().toLocaleTimeString())
                setError('')

                // 更新最后数据时间
                lastDataTimeRef.current = now

                console.log(`📊 Metrics: samples=${result.samples}, window=600s, fetch=${fetchTime}ms, p95=${result.p95}ms, qps=${result.qps}`)
            } else {
                // 保持上次数据，不清屏
                console.log(`⚠️ No data: ${result.error || 'no samples'}, samples=${result.samples}, fetch=${fetchTime}ms`)

                // 检查失联时间
                const timeSinceLastData = Date.now() - lastDataTimeRef.current
                if (timeSinceLastData > DISCONNECT_THRESHOLD) {
                    setError('等待数据流入…')
                } else {
                    setError('')
                }
            }
        } catch (err) {
            const fetchTime = Date.now() - startTime
            console.error(`❌ Metrics fetch failed (${fetchTime}ms):`, err)

            // 检查失联时间
            const timeSinceLastData = Date.now() - lastDataTimeRef.current
            if (timeSinceLastData > DISCONNECT_THRESHOLD) {
                setError('等待数据流入…（后端可能未响应）')
            } else {
                setError('')
            }
        }
    }

    // Fetch agent summary
    const fetchAgent = async () => {
        try {
            const data = await fetchAgentSummary(agentVersion)
            setAgentData(data)
            setError('')
        } catch (err) {
            console.error(`❌ Agent error:`, err)
            setError(`Agent: ${String(err).slice(0, 50)}`)
        }
    }

    // Run agent (dry)
    const handleRunDry = async () => {
        setRunning(true)
        try {
            await runAgentDry(agentVersion)
            await new Promise(resolve => setTimeout(resolve, 500))
            await fetchAgent()
        } catch (err) {
            console.error('Run dry error:', err)
            setError(`Run: ${String(err).slice(0, 50)}`)
        } finally {
            setRunning(false)
        }
    }

    // Refresh all
    const handleRefresh = async () => {
        setRefreshing(true)
        await Promise.all([fetchData(), fetchAgent()])
        setRefreshing(false)
    }

    // Setup polling (3s interval)
    useEffect(() => {
        fetchData()
        fetchAgent()

        intervalRef.current = window.setInterval(() => {
            fetchData()
        }, POLL_INTERVAL)

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [expId])  // Re-fetch when expId changes

    // Render charts
    const renderCharts = () => {
        if (dataPoints.length === 0) {
            return (
                <div style={styles.placeholder}>
                    ⚠️ 暂无数据流入<br />
                    <small>等待Redis数据或检查实验状态</small>
                </div>
            )
        }

        const width = 600
        const height = 300
        const padding = { top: 20, right: 60, bottom: 40, left: 60 }
        const chartWidth = width - padding.left - padding.right
        const chartHeight = height - padding.top - padding.bottom

        // Scales with better time axis
        const maxP95 = Math.max(...dataPoints.map(d => d.p95), 1)
        const maxQps = Math.max(...dataPoints.map(d => d.qps), 1)
        const maxErr = Math.max(...dataPoints.map(d => d.err), 1)

        const scaleY_P95 = (val: number) => chartHeight - (val / maxP95) * chartHeight
        const scaleY_QPS = (val: number) => chartHeight - (val / maxQps) * chartHeight
        const scaleY_Err = (val: number) => chartHeight - (val / maxErr) * chartHeight
        const scaleX = (idx: number) => (idx / Math.max(dataPoints.length - 1, 1)) * chartWidth

        // Time axis labels (show last 10 minutes)
        const now = Date.now()
        const timeLabels = []
        for (let i = 0; i <= 4; i++) {
            const time = new Date(now - (4 - i) * 2.5 * 60 * 1000) // 每2.5分钟一个标签
            timeLabels.push({
                x: (i / 4) * chartWidth,
                label: time.toLocaleTimeString().slice(0, 5)
            })
        }

        // Line paths
        const p95Path = dataPoints.map((d, i) =>
            `${i === 0 ? 'M' : 'L'} ${scaleX(i)},${scaleY_P95(d.p95)}`
        ).join(' ')

        const qpsPath = dataPoints.map((d, i) =>
            `${i === 0 ? 'M' : 'L'} ${scaleX(i)},${scaleY_QPS(d.qps)}`
        ).join(' ')

        const errPath = dataPoints.map((d, i) =>
            `${i === 0 ? 'M' : 'L'} ${scaleX(i)},${scaleY_Err(d.err)}`
        ).join(' ')

        return (
            <div>
                {/* 折线图 */}
                <div style={styles.chartContainer}>
                    <svg width={width} height={height}>
                        <g transform={`translate(${padding.left},${padding.top})`}>
                            {/* Grid */}
                            <line x1={0} y1={0} x2={0} y2={chartHeight} stroke="#334155" strokeWidth={1} />
                            <line x1={0} y1={chartHeight} x2={chartWidth} y2={chartHeight} stroke="#334155" strokeWidth={1} />

                            {/* Lines */}
                            <path d={p95Path} fill="none" stroke="#60a5fa" strokeWidth={2} />
                            <path d={qpsPath} fill="none" stroke="#34d399" strokeWidth={2} />
                            <path d={errPath} fill="none" stroke="#f87171" strokeWidth={1} strokeDasharray="4,4" />

                            {/* Y-axis labels */}
                            <text x={-10} y={0} fontSize={10} fill="#94a3b8" textAnchor="end">P95: {maxP95.toFixed(0)}ms</text>
                            <text x={chartWidth + 10} y={0} fontSize={10} fill="#94a3b8" textAnchor="start">QPS: {maxQps.toFixed(0)}</text>
                            <text x={chartWidth + 10} y={20} fontSize={10} fill="#94a3b8" textAnchor="start">Err: {maxErr.toFixed(1)}%</text>

                            {/* Time axis labels */}
                            {timeLabels.map((label, i) => (
                                <text key={i} x={label.x} y={chartHeight + 30} fontSize={10} fill="#94a3b8" textAnchor="middle">
                                    {label.label}
                                </text>
                            ))}

                            {/* Data points count */}
                            <text x={chartWidth + 10} y={chartHeight + 30} fontSize={10} fill="#94a3b8" textAnchor="start">
                                {dataPoints.length} pts
                            </text>
                        </g>
                    </svg>

                    <div style={styles.legend}>
                        <span style={{ color: '#60a5fa' }}>━ P95 (左轴)</span>
                        <span style={{ color: '#34d399', marginLeft: '1rem' }}>━ QPS (右轴)</span>
                        <span style={{ color: '#f87171', marginLeft: '1rem' }}>┄ Err%</span>
                    </div>
                </div>

                {/* Route 分布 */}
                <div style={styles.routeContainer}>
                    <div style={styles.routeTitle}>Route 分布</div>
                    <div style={styles.routeBar}>
                        {dataPoints.length > 0 && (() => {
                            const last = dataPoints[dataPoints.length - 1]
                            const total = last.milvus + last.faiss + last.qdrant || 1
                            return (
                                <>
                                    <div style={{ ...styles.routeSegment, width: `${(last.milvus / total) * 100}%`, backgroundColor: '#3b82f6' }}>
                                        {last.milvus > 0 && `Milvus ${((last.milvus / total) * 100).toFixed(0)}%`}
                                    </div>
                                    <div style={{ ...styles.routeSegment, width: `${(last.faiss / total) * 100}%`, backgroundColor: '#8b5cf6' }}>
                                        {last.faiss > 0 && `FAISS ${((last.faiss / total) * 100).toFixed(0)}%`}
                                    </div>
                                    <div style={{ ...styles.routeSegment, width: `${(last.qdrant / total) * 100}%`, backgroundColor: '#ec4899' }}>
                                        {last.qdrant > 0 && `Qdrant ${((last.qdrant / total) * 100).toFixed(0)}%`}
                                    </div>
                                </>
                            )
                        })()}
                    </div>
                </div>
            </div>
        )
    }

    // Render agent panel with verdict bar + bullets
    const renderAgentPanel = () => {
        if (!agentData) {
            return (
                <div style={styles.placeholder}>
                    等待 Agent 数据…
                </div>
            )
        }

        const verdictColor =
            agentData.verdict === 'PASS' ? '#4ade80' :
                agentData.verdict === 'EDGE' ? '#fbbf24' :
                    agentData.verdict === 'FAIL' ? '#f87171' : '#94a3b8'

        // 提取前3条要点用于判定条
        const topBullets = agentData.bullets && agentData.bullets.length > 0
            ? agentData.bullets.slice(0, 3)
            : ['暂无判定要点']

        return (
            <div>
                {/* 判定条：PASS/FAIL + 三条要点 */}
                <div style={{ ...styles.verdictBar, borderColor: verdictColor }}>
                    <div style={{ ...styles.verdictLabel, backgroundColor: verdictColor }}>
                        {agentData.verdict || 'N/A'}
                    </div>
                    <div style={styles.verdictBullets}>
                        {topBullets.map((bullet, idx) => (
                            <div key={idx} style={styles.verdictBulletItem}>
                                <span style={{ color: verdictColor }}>●</span> {bullet}
                            </div>
                        ))}
                    </div>
                </div>

                <div style={styles.agentMeta}>
                    <div style={styles.metaItem}>
                        <span style={styles.metaLabel}>Mode:</span>
                        <span style={styles.metaValue}>{agentData.explainer_mode || agentData.mode || '-'}</span>
                    </div>
                    <div style={styles.metaItem}>
                        <span style={styles.metaLabel}>Cached:</span>
                        <span style={styles.metaValue}>{agentData.cached ? 'true' : 'false'}</span>
                    </div>
                    <div style={styles.metaItem}>
                        <span style={styles.metaLabel}>Version:</span>
                        <span style={styles.metaValue}>v{agentVersion}</span>
                    </div>
                </div>

                {agentData.bullets && agentData.bullets.length > 3 && (
                    <div style={styles.bullets}>
                        <div style={styles.bulletsTitle}>其他要点 ({agentData.bullets.length - 3})</div>
                        <ul style={styles.bulletList}>
                            {agentData.bullets.slice(3).map((bullet, idx) => (
                                <li key={idx} style={styles.bulletItem}>{bullet || '—'}</li>
                            ))}
                        </ul>
                    </div>
                )}

                <div style={styles.agentActions}>
                    <button
                        onClick={handleRunDry}
                        disabled={running}
                        style={{
                            ...styles.agentButton,
                            ...(running ? styles.buttonDisabled : {})
                        }}
                    >
                        {running ? 'Running...' : 'Run (dry)'}
                    </button>
                    <button
                        onClick={fetchAgent}
                        disabled={running}
                        style={{
                            ...styles.agentButton,
                            ...(running ? styles.buttonDisabled : {})
                        }}
                    >
                        Refresh
                    </button>
                </div>

                {agentData.generated_at && (
                    <div style={styles.agentTimestamp}>
                        {agentData.generated_at}
                    </div>
                )}
            </div>
        )
    }

    // 计算顶部4卡片的实时数据
    const latestMetrics = dataPoints.length > 0 ? dataPoints[dataPoints.length - 1] : null
    const currentP95 = latestMetrics?.p95 || 0
    const currentQPS = latestMetrics?.qps || 0
    const currentSuccess = latestMetrics ? Math.max(0, 100 - (latestMetrics.err || 0)) : 0
    const currentRouteTotal = latestMetrics ? (latestMetrics.milvus + latestMetrics.faiss + latestMetrics.qdrant) : 1
    const currentMilvusShare = latestMetrics ? (latestMetrics.milvus / currentRouteTotal * 100) : 0

    return (
        <div style={styles.container}>
            <header style={styles.header}>
                <h1 style={styles.title}>Monitor Panel MVP</h1>
                <div style={styles.subtitle}>6要素实时监控：3s刷新 | 10s失联提示 | v3→v2回退</div>
            </header>

            {/* 顶部4卡片：P95, Success%, QPS, Route% */}
            <div style={styles.cardsContainer}>
                <div style={styles.card}>
                    <div style={styles.cardLabel}>P95 延迟</div>
                    <div style={styles.cardValue}>{currentP95.toFixed(1)}<span style={styles.cardUnit}>ms</span></div>
                </div>
                <div style={styles.card}>
                    <div style={styles.cardLabel}>Success%</div>
                    <div style={{ ...styles.cardValue, color: currentSuccess >= 99 ? '#4ade80' : '#fbbf24' }}>
                        {currentSuccess.toFixed(1)}<span style={styles.cardUnit}>%</span>
                    </div>
                </div>
                <div style={styles.card}>
                    <div style={styles.cardLabel}>QPS</div>
                    <div style={styles.cardValue}>{currentQPS.toFixed(1)}<span style={styles.cardUnit}>/s</span></div>
                </div>
                <div style={styles.card}>
                    <div style={styles.cardLabel}>Route (Milvus)</div>
                    <div style={styles.cardValue}>{currentMilvusShare.toFixed(0)}<span style={styles.cardUnit}>%</span></div>
                </div>
            </div>

            {/* Status bar */}
            <div style={styles.topBar}>
                <div style={styles.topItem}>
                    <span style={styles.topLabel}>Experiment:</span>
                    <input
                        type="text"
                        value={expIdInput}
                        onChange={(e) => setExpIdInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                setExpId(expIdInput)
                            }
                        }}
                        onBlur={() => setExpId(expIdInput)}
                        style={styles.expInput}
                        placeholder="输入实验ID"
                    />
                </div>
                <div style={styles.topItem}>
                    <span style={styles.topLabel}>Agent:</span>
                    <select
                        value={agentVersion}
                        onChange={(e) => {
                            const newVersion = parseInt(e.target.value) as 2 | 3
                            setAgentVersion(newVersion)
                            fetchAgentSummary(newVersion).then(setAgentData)
                        }}
                        style={styles.versionSelect}
                    >
                        <option value={2}>v2 (rules)</option>
                        <option value={3}>v3 (LLM+nav)</option>
                    </select>
                </div>
                <div style={styles.topItem}>
                    <span style={styles.topLabel}>Latest:</span>
                    <span style={styles.topValue}>{latestWindowTime}</span>
                </div>
                <div style={styles.topItem}>
                    <span style={styles.topLabel}>Poll:</span>
                    <span style={styles.topValue}>{POLL_INTERVAL / 1000}s</span>
                </div>
                <div style={styles.topItem}>
                    <span style={styles.topLabel}>Status:</span>
                    <span style={{
                        ...styles.topValue,
                        color: refreshing ? '#fbbf24' : '#4ade80'
                    }}>
                        {refreshing ? '⟳' : '●'}
                    </span>
                </div>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    style={{
                        ...styles.refreshButton,
                        ...(refreshing ? styles.buttonDisabled : {})
                    }}
                >
                    {refreshing ? 'Refreshing...' : 'Refresh All'}
                </button>
            </div>

            {/* Error banner */}
            {error && (
                <div style={styles.errorBanner}>
                    {error}
                </div>
            )}

            {/* Main content */}
            <div style={styles.main}>
                {/* Left: Charts */}
                <div style={styles.leftPanel}>
                    <h2 style={styles.panelTitle}>实时曲线 (10分钟)</h2>
                    {renderCharts()}
                </div>

                {/* Right: Agent */}
                <div style={styles.rightPanel}>
                    <h2 style={styles.panelTitle}>Agent 仪表</h2>
                    {renderAgentPanel()}
                </div>
            </div>
        </div>
    )
}

// ========== Styles ==========
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
        marginBottom: '1.5rem'
    },
    title: {
        fontSize: '2rem',
        fontWeight: 700,
        margin: 0,
        background: 'linear-gradient(to right, #60a5fa, #a78bfa)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text'
    },
    subtitle: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginTop: '0.5rem'
    },
    cardsContainer: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '1rem',
        marginBottom: '1.5rem',
        maxWidth: '1400px',
        margin: '0 auto 1.5rem auto'
    },
    card: {
        backgroundColor: '#1e293b',
        padding: '1.25rem',
        borderRadius: '0.75rem',
        border: '1px solid #334155',
        textAlign: 'center'
    },
    cardLabel: {
        fontSize: '0.75rem',
        color: '#94a3b8',
        marginBottom: '0.5rem',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        fontWeight: 600
    },
    cardValue: {
        fontSize: '2rem',
        fontWeight: 700,
        color: '#e2e8f0'
    },
    cardUnit: {
        fontSize: '1rem',
        fontWeight: 400,
        color: '#94a3b8',
        marginLeft: '0.25rem'
    },
    topBar: {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '2rem',
        padding: '1rem',
        backgroundColor: '#1e293b',
        borderRadius: '0.5rem',
        marginBottom: '2rem',
        flexWrap: 'wrap'
    },
    topItem: {
        display: 'flex',
        gap: '0.5rem',
        alignItems: 'center'
    },
    topLabel: {
        fontSize: '0.875rem',
        color: '#94a3b8'
    },
    topValue: {
        fontSize: '0.875rem',
        fontWeight: 600,
        color: '#e2e8f0'
    },
    expInput: {
        fontSize: '0.875rem',
        fontWeight: 600,
        color: '#e2e8f0',
        backgroundColor: '#334155',
        border: '1px solid #475569',
        borderRadius: '0.25rem',
        padding: '0.25rem 0.5rem',
        minWidth: '120px',
        outline: 'none'
    },
    versionSelect: {
        fontSize: '0.875rem',
        fontWeight: 600,
        color: '#e2e8f0',
        backgroundColor: '#334155',
        border: '1px solid #475569',
        borderRadius: '0.25rem',
        padding: '0.25rem 0.5rem',
        outline: 'none',
        cursor: 'pointer'
    },
    refreshButton: {
        padding: '0.5rem 1rem',
        fontSize: '0.875rem',
        fontWeight: 600,
        color: '#fff',
        backgroundColor: '#3b82f6',
        border: 'none',
        borderRadius: '0.375rem',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    buttonDisabled: {
        opacity: 0.5,
        cursor: 'not-allowed'
    },
    errorBanner: {
        padding: '0.75rem',
        backgroundColor: '#7f1d1d',
        color: '#fca5a5',
        borderRadius: '0.375rem',
        marginBottom: '1rem',
        fontSize: '0.875rem',
        textAlign: 'center'
    },
    main: {
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '2rem',
        maxWidth: '1400px',
        margin: '0 auto'
    },
    leftPanel: {
        backgroundColor: '#1e293b',
        padding: '1.5rem',
        borderRadius: '0.75rem',
        border: '1px solid #334155'
    },
    rightPanel: {
        backgroundColor: '#1e293b',
        padding: '1.5rem',
        borderRadius: '0.75rem',
        border: '1px solid #334155'
    },
    panelTitle: {
        fontSize: '1.25rem',
        fontWeight: 600,
        marginTop: 0,
        marginBottom: '1rem',
        color: '#a78bfa'
    },
    placeholder: {
        textAlign: 'center',
        padding: '3rem',
        color: '#fbbf24',
        fontSize: '1rem',
        backgroundColor: '#1e293b',
        borderRadius: '0.5rem',
        border: '1px solid #fbbf24'
    },
    chartContainer: {
        marginBottom: '1.5rem'
    },
    legend: {
        marginTop: '1rem',
        fontSize: '0.875rem',
        color: '#94a3b8',
        textAlign: 'center'
    },
    routeContainer: {
        marginTop: '2rem'
    },
    routeTitle: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginBottom: '0.5rem',
        fontWeight: 500
    },
    routeBar: {
        display: 'flex',
        height: '2rem',
        borderRadius: '0.375rem',
        overflow: 'hidden'
    },
    routeSegment: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '0.75rem',
        fontWeight: 600,
        color: '#fff',
        transition: 'width 0.3s'
    },
    verdictBar: {
        border: '2px solid',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1.5rem',
        backgroundColor: '#1e293b'
    },
    verdictLabel: {
        display: 'inline-block',
        padding: '0.5rem 1.5rem',
        borderRadius: '0.375rem',
        fontSize: '1.5rem',
        fontWeight: 700,
        color: '#0f172a',
        marginBottom: '0.75rem'
    },
    verdictBullets: {
        marginTop: '0.75rem'
    },
    verdictBulletItem: {
        fontSize: '0.875rem',
        color: '#cbd5e1',
        marginBottom: '0.5rem',
        lineHeight: 1.5
    },
    agentMeta: {
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        marginBottom: '1.5rem'
    },
    metaItem: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.875rem'
    },
    metaLabel: {
        color: '#94a3b8'
    },
    metaValue: {
        color: '#e2e8f0',
        fontWeight: 600
    },
    bullets: {
        marginBottom: '1.5rem'
    },
    bulletsTitle: {
        fontSize: '0.875rem',
        color: '#94a3b8',
        marginBottom: '0.5rem',
        fontWeight: 600
    },
    bulletList: {
        listStyle: 'disc',
        paddingLeft: '1.5rem',
        margin: 0
    },
    bulletItem: {
        fontSize: '0.875rem',
        color: '#cbd5e1',
        marginBottom: '0.375rem',
        lineHeight: 1.5
    },
    noBullets: {
        fontSize: '0.875rem',
        color: '#64748b',
        fontStyle: 'italic'
    },
    agentActions: {
        display: 'flex',
        gap: '0.75rem',
        marginBottom: '1rem'
    },
    agentButton: {
        flex: 1,
        padding: '0.75rem',
        fontSize: '0.875rem',
        fontWeight: 600,
        color: '#fff',
        backgroundColor: '#6366f1',
        border: 'none',
        borderRadius: '0.375rem',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    agentTimestamp: {
        fontSize: '0.75rem',
        color: '#64748b',
        textAlign: 'center'
    }
}

