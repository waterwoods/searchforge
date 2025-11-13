package policy

// mvp-5

import (
	"context"
	"errors"
	"strings"
	"sync"
	"time"

	"github.com/searchforge/retrieval_proxy/obs"
)

// RateLimitConfig configures the token bucket limiter.
// mvp-5
type RateLimitConfig struct {
	Capacity     int
	RefillTokens int
	RefillEvery  time.Duration
}

// CircuitConfig provides minimal circuit-breaker tuning knobs.
// mvp-5
type CircuitConfig struct {
	FailureThreshold   int
	HalfOpenSuccesses  int
	Cooldown           time.Duration
}

// SourceConfig configures timeout, rate limit, and circuit breaker behaviour.
// mvp-5
type SourceConfig struct {
	Name    string
	Timeout time.Duration
	Rate    RateLimitConfig
	Circuit CircuitConfig
}

// SourcePolicy applies timeout, rate limiting, and circuit breakers per upstream.
// mvp-5
type SourcePolicy struct {
	name    string
	timeout time.Duration
	rate    *TokenBucket
	breaker *lightBreaker
}

// NewSourcePolicy constructs a SourcePolicy with sane defaults.
// mvp-5
func NewSourcePolicy(cfg SourceConfig) (*SourcePolicy, error) {
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

	breaker := newLightBreaker(cfg.Name, cfg.Circuit)

	return &SourcePolicy{
		name:    cfg.Name,
		timeout: cfg.Timeout,
		rate:    bucket,
		breaker: breaker,
	}, nil
}

// Execute applies the policy controls to fn.
// mvp-5
func (s *SourcePolicy) Execute(parent context.Context, fn func(context.Context) error) error {
	if parent == nil {
		parent = context.Background()
	}

	if !s.breaker.Allow() {
		return ErrCircuitOpen
	}

	if s.rate != nil && !s.rate.Allow(time.Now()) {
		return ErrRateLimited
	}

	ctx, cancel := context.WithTimeout(parent, s.timeout)
	defer cancel()

	start := time.Now()
	err := fn(ctx)
	duration := time.Since(start)

	if err != nil {
		s.breaker.Fail()
		obs.RecordSourceError(s.name, classifyError(err))
	} else {
		s.breaker.Success()
	}

	obs.RecordSourceDuration(s.name, duration)
	return err
}

// classifyError maps errors to metric codes.
// mvp-5
func classifyError(err error) string {
	if err == nil {
		return "ok"
	}
	if errors.Is(err, context.Canceled) {
		return "canceled"
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return "timeout"
	}
	return sanitize(err.Error())
}

func sanitize(msg string) string {
	if msg == "" {
		return "unknown"
	}
	msg = strings.ToLower(msg)
	if idx := strings.IndexByte(msg, ' '); idx > 0 {
		msg = msg[:idx]
	}
	msg = strings.Trim(msg, ":.")
	if msg == "" {
		msg = "error"
	}
	return msg
}

type breakerState string

const (
	stateClosed   breakerState = "closed"
	stateOpen     breakerState = "open"
	stateHalfOpen breakerState = "half-open"
)

type lightBreaker struct {
	source            string
	mu                sync.Mutex
	state             breakerState
	failures          int
	successes         int
	cfg               CircuitConfig
	lastStateChange   time.Time
}

func newLightBreaker(source string, cfg CircuitConfig) *lightBreaker {
	if cfg.FailureThreshold <= 0 {
		cfg.FailureThreshold = 3
	}
	if cfg.HalfOpenSuccesses <= 0 {
		cfg.HalfOpenSuccesses = 1
	}
	if cfg.Cooldown <= 0 {
		cfg.Cooldown = 2 * time.Second
	}
	b := &lightBreaker{
		source: source,
		state:  stateClosed,
		cfg:    cfg,
	}
	obs.SetCircuitState(source, string(stateClosed))
	return b
}

func (b *lightBreaker) Allow() bool {
	b.mu.Lock()
	defer b.mu.Unlock()

	switch b.state {
	case stateOpen:
		if time.Since(b.lastStateChange) >= b.cfg.Cooldown {
			b.transition(stateHalfOpen)
			return true
		}
		return false
	default:
		return true
	}
}

func (b *lightBreaker) Fail() {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.failures++
	switch b.state {
	case stateHalfOpen:
		b.transition(stateOpen)
	case stateClosed:
		if b.failures >= b.cfg.FailureThreshold {
			b.transition(stateOpen)
		}
	}
}

func (b *lightBreaker) Success() {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.failures = 0
	switch b.state {
	case stateHalfOpen:
		b.successes++
		if b.successes >= b.cfg.HalfOpenSuccesses {
			b.transition(stateClosed)
		}
	case stateOpen:
		// ignored
	default:
		obs.SetCircuitState(b.source, string(stateClosed))
	}
}

func (b *lightBreaker) transition(next breakerState) {
	if b.state == next {
		return
	}
	b.state = next
	b.failures = 0
	b.successes = 0
	b.lastStateChange = time.Now()
	obs.SetCircuitState(b.source, string(next))
}
