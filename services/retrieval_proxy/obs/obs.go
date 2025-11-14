//go:build !nometrics

package obs

// mvp-5

import (
	"context"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

var (
	setupOnce sync.Once
	shutdown  = func(context.Context) error { return nil }
)

var (
	proxyRequests = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "retrieval_proxy_requests_total",
		Help: "Total proxy requests by return code.",
	}, []string{"code"})
	proxyDuration = promauto.NewHistogram(prometheus.HistogramOpts{
		Name:    "retrieval_proxy_request_duration_ms",
		Help:    "Histogram of proxy request latency in ms.",
		Buckets: prometheus.ExponentialBuckets(5, 2, 8),
	})
	sourceDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "retrieval_proxy_source_duration_ms",
		Help:    "Histogram of upstream source latency in ms.",
		Buckets: prometheus.ExponentialBuckets(5, 2, 8),
	}, []string{"source"})
	sourceErrors = promauto.NewCounterVec(prometheus.CounterOpts{
		Name: "retrieval_proxy_source_errors_total",
		Help: "Count of upstream errors grouped by source and code.",
	}, []string{"source", "code"})
	budgetHits = promauto.NewCounter(prometheus.CounterOpts{
		Name: "retrieval_proxy_budget_hit_total",
		Help: "Total requests that exhausted the configured budget.",
	})
	circuitStates = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Name: "retrieval_proxy_circuit_state",
		Help: "Circuit breaker state per source (0=closed,1=half-open,2=open).",
	}, []string{"source", "state"})
)

// ObserveProxyRequest records proxy-level metrics.
// mvp-5
func ObserveProxyRequest(code string, duration time.Duration, traceID string) {
	proxyRequests.WithLabelValues(code).Inc()
	if eo, ok := proxyDuration.(prometheus.ExemplarObserver); ok && traceID != "" {
		eo.ObserveWithExemplar(
			float64(duration.Milliseconds()),
			prometheus.Labels{"trace_id": traceID},
		)
		return
	}
	proxyDuration.Observe(float64(duration.Milliseconds()))
}

// RecordSourceDuration observes the latency for a source.
// mvp-5
func RecordSourceDuration(source string, duration time.Duration) {
	sourceDuration.WithLabelValues(source).Observe(float64(duration.Milliseconds()))
}

// RecordSourceError increments the error counter for a source/code combination.
// mvp-5
func RecordSourceError(source, code string) {
	sourceErrors.WithLabelValues(source, code).Inc()
}

// IncBudgetHit records a budget exhaustion event.
// mvp-5
func IncBudgetHit() {
	budgetHits.Inc()
}

// SetCircuitState updates the gauge representing circuit breaker state.
// mvp-5
func SetCircuitState(source, state string) {
	var value float64
	switch state {
	case "open":
		value = 2
	case "half-open":
		value = 1
	default:
		value = 0
		state = "closed"
	}
	circuitStates.WithLabelValues(source, state).Set(value)
}

// InitTracer sets up a minimal OpenTelemetry tracer provider.
// mvp-5
func InitTracer(serviceName string) (func(context.Context) error, error) {
	var initErr error
	setupOnce.Do(func() {
		res, err := resource.New(context.Background(),
			resource.WithAttributes(
				semconv.ServiceName(serviceName),
			),
		)
		if err != nil {
			initErr = err
			return
		}

		provider := sdktrace.NewTracerProvider(
			sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.TraceIDRatioBased(0.3))),
			sdktrace.WithResource(res),
		)
		otel.SetTracerProvider(provider)
		shutdown = provider.Shutdown
	})
	return shutdown, initErr
}
