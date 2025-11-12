package policy

import (
	"sync"
	"time"
)

// CircuitState represents the state of the circuit breaker.
type CircuitState int

const (
	// CircuitClosed allows all traffic.
	CircuitClosed CircuitState = iota
	// CircuitHalfOpen allows limited traffic to probe recovery.
	CircuitHalfOpen
	// CircuitOpen blocks all traffic.
	CircuitOpen
)

type circuitEvent struct {
	timestamp time.Time
	success   bool
}

// CircuitBreakerConfig configures the circuit breaker behaviour.
type CircuitBreakerConfig struct {
	Window              time.Duration
	FailureRateThreshold float64
	MinSamples          int
	Cooldown            time.Duration
	HalfOpenMaxCalls    int
}

// CircuitBreaker implements a rolling window circuit breaker with half-open support.
type CircuitBreaker struct {
	cfg      CircuitBreakerConfig
	source   string
	metrics  *Metrics

	mu                sync.Mutex
	state             CircuitState
	lastStateChange   time.Time
	events            []circuitEvent
	halfOpenAttempts  int
	halfOpenSuccesses int
}

// NewCircuitBreaker constructs a new CircuitBreaker.
func NewCircuitBreaker(source string, cfg CircuitBreakerConfig, metrics *Metrics) *CircuitBreaker {
	cb := &CircuitBreaker{
		cfg:    cfg,
		source: source,
		metrics: metrics,
		state:  CircuitClosed,
	}
	cb.updateMetrics(CircuitClosed)
	return cb
}

// Allow returns whether the circuit permits executing a call at the given time.
func (c *CircuitBreaker) Allow(now time.Time) bool {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.refreshState(now)

	if c.state == CircuitOpen {
		return false
	}

	if c.state == CircuitHalfOpen {
		if c.cfg.HalfOpenMaxCalls > 0 && c.halfOpenAttempts >= c.cfg.HalfOpenMaxCalls {
			return false
		}
		c.halfOpenAttempts++
	}

	return true
}

// Record records the outcome of a call.
func (c *CircuitBreaker) Record(now time.Time, success bool) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.addEvent(now, success)
	c.refreshState(now)

	if c.state == CircuitHalfOpen {
		if success {
			c.halfOpenSuccesses++
			if c.cfg.HalfOpenMaxCalls > 0 && c.halfOpenSuccesses >= c.cfg.HalfOpenMaxCalls {
				c.transition(CircuitClosed, now)
				c.resetHalfOpenCounters()
			}
		} else {
			c.transition(CircuitOpen, now)
			c.resetHalfOpenCounters()
		}
	}
}

func (c *CircuitBreaker) addEvent(now time.Time, success bool) {
	c.events = append(c.events, circuitEvent{
		timestamp: now,
		success:   success,
	})
	c.prune(now)
}

func (c *CircuitBreaker) prune(now time.Time) {
	windowStart := now.Add(-c.cfg.Window)
	idx := 0
	for _, evt := range c.events {
		if !evt.timestamp.Before(windowStart) {
			break
		}
		idx++
	}
	if idx > 0 {
		c.events = c.events[idx:]
	}
}

func (c *CircuitBreaker) refreshState(now time.Time) {
	if c.state == CircuitOpen {
		if now.Sub(c.lastStateChange) >= c.cfg.Cooldown {
			c.transition(CircuitHalfOpen, now)
			c.resetHalfOpenCounters()
		}
		return
	}

	if c.state == CircuitHalfOpen {
		// Nothing to do here; state transitions handled in Record.
		return
	}

	// Evaluate failure rate in closed state.
	c.prune(now)
	total := len(c.events)
	if total < c.cfg.MinSamples || total == 0 {
		return
	}

	failures := 0
	for _, evt := range c.events {
		if !evt.success {
			failures++
		}
	}

	failureRate := float64(failures) / float64(total)
	if failureRate >= c.cfg.FailureRateThreshold {
		c.transition(CircuitOpen, now)
	}
}

func (c *CircuitBreaker) transition(state CircuitState, now time.Time) {
	if c.state == state {
		return
	}
	c.state = state
	c.lastStateChange = now
	c.updateMetrics(state)
}

func (c *CircuitBreaker) resetHalfOpenCounters() {
	c.halfOpenAttempts = 0
	c.halfOpenSuccesses = 0
}

func (c *CircuitBreaker) updateMetrics(state CircuitState) {
	if c.metrics != nil {
		c.metrics.SetCircuitState(c.source, state)
	}
}

// State returns the current state of the circuit breaker.
func (c *CircuitBreaker) State() CircuitState {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.state
}

