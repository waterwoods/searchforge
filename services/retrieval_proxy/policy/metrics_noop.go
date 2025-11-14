//go:build nometrics

package policy

// mvp-5

import "time"

type Metrics struct{}

type MetricsOption func(*metricsConfig)

type metricsConfig struct{}

func NewMetrics(...MetricsOption) *Metrics {
	return nil
}

func WithRegisterer(_ any) MetricsOption {
	return func(*metricsConfig) {}
}

func WithLatencyBuckets(_ []float64) MetricsOption {
	return func(*metricsConfig) {}
}

func (m *Metrics) ObserveSource(string, time.Duration, error) {}

func (m *Metrics) ObserveTotal(time.Duration) {}

func (m *Metrics) IncBudgetHit() {}

func (m *Metrics) SetCircuitState(string, CircuitState) {}

