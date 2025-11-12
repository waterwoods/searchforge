package policy

import (
	"testing"
	"time"
)

func TestCircuitBreakerTransitions(t *testing.T) {
	cfg := CircuitBreakerConfig{
		Window:               200 * time.Millisecond,
		FailureRateThreshold: 0.5,
		MinSamples:           2,
		Cooldown:             100 * time.Millisecond,
		HalfOpenMaxCalls:     1,
	}

	cb := NewCircuitBreaker("test", cfg, nil)

	now := time.Now()
	if !cb.Allow(now) {
		t.Fatal("expected allow in closed state")
	}
	cb.Record(now, false)
	cb.Record(now.Add(10*time.Millisecond), false)

	if cb.State() != CircuitOpen {
		t.Fatalf("expected circuit open, got %v", cb.State())
	}

	if cb.Allow(now.Add(20 * time.Millisecond)) {
		t.Fatal("expected allow to be denied while circuit open")
	}

	halfOpenTime := now.Add(cfg.Cooldown + 20*time.Millisecond)
	if !cb.Allow(halfOpenTime) {
		t.Fatal("expected allow in half-open state")
	}

	cb.Record(halfOpenTime, true)

	if cb.State() != CircuitClosed {
		t.Fatalf("expected circuit closed after successful probe, got %v", cb.State())
	}
}

