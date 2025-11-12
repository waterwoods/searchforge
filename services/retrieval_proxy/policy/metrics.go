package policy

import (
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

// Metrics wraps policy specific Prometheus metrics.
type Metrics struct {
	perSourceLatency *prometheus.HistogramVec
	perSourceErrRate *prometheus.GaugeVec
	totalLatency     *prometheus.Histogram
	circuitState     *prometheus.GaugeVec
	budgetHit        prometheus.Counter

	requestsMu sync.Mutex
	requests   map[string]*sourceRequestStats
}

type sourceRequestStats struct {
	success int
	fail    int
}

// MetricsOption allows customizing the metrics registry.
type MetricsOption func(*metricsConfig)

type metricsConfig struct {
	registerer prometheus.Registerer
	buckets    []float64
}

// WithRegisterer overrides the default Prometheus registerer.
func WithRegisterer(r prometheus.Registerer) MetricsOption {
	return func(cfg *metricsConfig) {
		cfg.registerer = r
	}
}

// WithLatencyBuckets overrides the default latency histogram buckets (in ms).
func WithLatencyBuckets(buckets []float64) MetricsOption {
	return func(cfg *metricsConfig) {
		cfg.buckets = buckets
	}
}

// NewMetrics constructs Metrics and registers Prometheus collectors.
func NewMetrics(opts ...MetricsOption) *Metrics {
	cfg := metricsConfig{
		registerer: prometheus.DefaultRegisterer,
		buckets: []float64{
			5, 10, 20, 50, 100, 200, 500, 1000, 2000,
		},
	}

	for _, opt := range opts {
		opt(&cfg)
	}

	perSourceLatency := prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "retrieval_proxy_source_latency_ms",
		Help:    "Latency in milliseconds for each upstream retrieval source.",
		Buckets: cfg.buckets,
	}, []string{"source"})

	perSourceErrRate := prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "retrieval_proxy_source_error_rate",
		Help: "Rolling error rate for each upstream retrieval source.",
	}, []string{"source"})

	totalLatency := prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "retrieval_proxy_total_latency_ms",
		Help:    "Total latency in milliseconds for the retrieval proxy request.",
		Buckets: cfg.buckets,
	})

	circuitState := prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "retrieval_proxy_circuit_state",
		Help: "Circuit breaker state for each upstream retrieval source. 0=closed, 1=half-open, 2=open.",
	}, []string{"source"})

	budgetHit := prometheus.NewCounter(prometheus.CounterOpts{
		Name: "retrieval_proxy_budget_hit_total",
		Help: "Total number of requests that hit the configured budget.",
	})

	m := &Metrics{
		perSourceLatency: perSourceLatency,
		perSourceErrRate: perSourceErrRate,
		totalLatency:     totalLatency,
		circuitState:     circuitState,
		budgetHit:        budgetHit,
		requests:         make(map[string]*sourceRequestStats),
	}

	perSourceLatency = registerHistogramVec(cfg.registerer, perSourceLatency)
	perSourceErrRate = registerGaugeVec(cfg.registerer, perSourceErrRate)
	totalLatency = registerHistogram(cfg.registerer, totalLatency)
	circuitState = registerGaugeVec(cfg.registerer, circuitState)
	budgetHit = registerCounter(cfg.registerer, budgetHit)

	return m
}

// ObserveSource records the latency and error status for a source.
func (m *Metrics) ObserveSource(source string, latency time.Duration, err error) {
	if m == nil {
		return
	}

	ms := float64(latency.Milliseconds())
	if ms < 0 {
		ms = 0
	}
	m.perSourceLatency.WithLabelValues(source).Observe(ms)

	m.requestsMu.Lock()
	stats, ok := m.requests[source]
	if !ok {
		stats = &sourceRequestStats{}
		m.requests[source] = stats
	}
	if err != nil {
		stats.fail++
	} else {
		stats.success++
	}
	total := stats.fail + stats.success
	var rate float64
	if total > 0 {
		rate = float64(stats.fail) / float64(total)
	}
	m.requestsMu.Unlock()

	m.perSourceErrRate.WithLabelValues(source).Set(rate)
}

// ObserveTotal records the total latency for the proxy request.
func (m *Metrics) ObserveTotal(latency time.Duration) {
	if m == nil {
		return
	}
	ms := float64(latency.Milliseconds())
	if ms < 0 {
		ms = 0
	}
	m.totalLatency.Observe(ms)
}

// IncBudgetHit increments the budget hit counter.
func (m *Metrics) IncBudgetHit() {
	if m == nil {
		return
	}
	m.budgetHit.Inc()
}

// SetCircuitState records the circuit breaker state for a source.
func (m *Metrics) SetCircuitState(source string, state CircuitState) {
	if m == nil {
		return
	}
	m.circuitState.WithLabelValues(source).Set(float64(state))
}

func registerHistogramVec(registerer prometheus.Registerer, collector *prometheus.HistogramVec) *prometheus.HistogramVec {
	if registerer == nil {
		return collector
	}
	if err := registerer.Register(collector); err != nil {
		if are, ok := err.(prometheus.AlreadyRegisteredError); ok {
			if existing, ok := are.ExistingCollector.(*prometheus.HistogramVec); ok {
				return existing
			}
			return collector
		}
		panic(err)
	}
	return collector
}

func registerGaugeVec(registerer prometheus.Registerer, collector *prometheus.GaugeVec) *prometheus.GaugeVec {
	if registerer == nil {
		return collector
	}
	if err := registerer.Register(collector); err != nil {
		if are, ok := err.(prometheus.AlreadyRegisteredError); ok {
			if existing, ok := are.ExistingCollector.(*prometheus.GaugeVec); ok {
				return existing
			}
			return collector
		}
		panic(err)
	}
	return collector
}

func registerHistogram(registerer prometheus.Registerer, collector *prometheus.Histogram) *prometheus.Histogram {
	if registerer == nil {
		return collector
	}
	if err := registerer.Register(collector); err != nil {
		if are, ok := err.(prometheus.AlreadyRegisteredError); ok {
			if existing, ok := are.ExistingCollector.(*prometheus.Histogram); ok {
				return existing
			}
			return collector
		}
		panic(err)
	}
	return collector
}

func registerCounter(registerer prometheus.Registerer, collector prometheus.Counter) prometheus.Counter {
	if registerer == nil {
		return collector
	}
	if err := registerer.Register(collector); err != nil {
		if are, ok := err.(prometheus.AlreadyRegisteredError); ok {
			if existing, ok := are.ExistingCollector.(prometheus.Counter); ok {
				return existing
			}
			return collector
		}
		panic(err)
	}
	return collector
}

