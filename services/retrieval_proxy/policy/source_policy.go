package policy

import (
	"context"
	"errors"
	"time"
)

// RateLimitConfig configures the token bucket limiter.
type RateLimitConfig struct {
	Capacity     int
	RefillTokens int
	RefillEvery  time.Duration
}

// SourceConfig configures the per-source policy controls.
type SourceConfig struct {
	Name     string
	Timeout  time.Duration
	Rate     RateLimitConfig
	Circuit  CircuitBreakerConfig
}

// SourcePolicy applies timeout, rate limiting, and circuit breaking policies for a source.
type SourcePolicy struct {
	name    string
	timeout time.Duration
	rate    *TokenBucket
	circuit *CircuitBreaker
	metrics *Metrics
}

// NewSourcePolicy constructs a SourcePolicy with the provided configuration.
func NewSourcePolicy(cfg SourceConfig, metrics *Metrics) (*SourcePolicy, error) {
	if cfg.Name == "" {
		return nil, errors.New("source name required")
	}
	if cfg.Timeout <= 0 {
		return nil, errors.New("source timeout must be positive")
	}

	var bucket *TokenBucket
	if cfg.Rate.Capacity > 0 && cfg.Rate.RefillTokens > 0 && cfg.Rate.RefillEvery > 0 {
		bucket = NewTokenBucket(cfg.Rate.Capacity, cfg.Rate.RefillTokens, cfg.Rate.RefillEvery)
	}

	cbCfg := normalizeCircuitConfig(cfg.Circuit)
	cb := NewCircuitBreaker(cfg.Name, cbCfg, metrics)

	return &SourcePolicy{
		name:    cfg.Name,
		timeout: cfg.Timeout,
		rate:    bucket,
		circuit: cb,
		metrics: metrics,
	}, nil
}

// Execute wraps a source call applying timeout, rate limiting, and circuit breaker checks.
func (s *SourcePolicy) Execute(parent context.Context, fn func(context.Context) error) error {
	if parent == nil {
		parent = context.Background()
	}

	now := time.Now()

	if !s.circuit.Allow(now) {
		s.metrics.ObserveSource(s.name, 0, ErrCircuitOpen)
		return ErrCircuitOpen
	}

	if s.rate != nil && !s.rate.Allow(now) {
		return ErrRateLimited
	}

	ctx, cancel := context.WithTimeout(parent, s.timeout)
	defer cancel()

	start := time.Now()
	err := fn(ctx)
	latency := time.Since(start)
	s.metrics.ObserveSource(s.name, latency, err)

	s.circuit.Record(time.Now(), err == nil)
	return err
}

func normalizeCircuitConfig(cfg CircuitBreakerConfig) CircuitBreakerConfig {
	if cfg.Window <= 0 {
		cfg.Window = 10 * time.Second
	}
	if cfg.FailureRateThreshold <= 0 {
		cfg.FailureRateThreshold = 0.5
	}
	if cfg.MinSamples <= 0 {
		cfg.MinSamples = 5
	}
	if cfg.Cooldown <= 0 {
		cfg.Cooldown = 5 * time.Second
	}
	if cfg.HalfOpenMaxCalls <= 0 {
		cfg.HalfOpenMaxCalls = 1
	}
	return cfg
}

