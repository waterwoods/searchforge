package policy

import (
	"sync"
	"time"
)

// TokenBucket implements a basic token bucket rate limiter.
type TokenBucket struct {
	capacity     int
	tokens       float64
	refillAmount float64
	refillEvery  time.Duration
	lastRefill   time.Time
	mu           sync.Mutex
}

// NewTokenBucket constructs a token bucket with the provided parameters.
func NewTokenBucket(capacity int, refillAmount int, refillEvery time.Duration) *TokenBucket {
	if capacity <= 0 || refillAmount <= 0 || refillEvery <= 0 {
		return nil
	}
	now := time.Now()
	return &TokenBucket{
		capacity:     capacity,
		tokens:       float64(capacity),
		refillAmount: float64(refillAmount),
		refillEvery:  refillEvery,
		lastRefill:   now,
	}
}

// Allow consumes a single token if available and returns true. When no tokens
// are available the call returns false.
func (b *TokenBucket) Allow(now time.Time) bool {
	if b == nil {
		return true
	}
	b.mu.Lock()
	defer b.mu.Unlock()

	b.refill(now)
	if b.tokens < 1 {
		return false
	}
	b.tokens -= 1
	return true
}

func (b *TokenBucket) refill(now time.Time) {
	if b == nil {
		return
	}
	if now.Before(b.lastRefill) {
		b.lastRefill = now
		return
	}

	elapsed := now.Sub(b.lastRefill)
	if elapsed < b.refillEvery {
		return
	}

	units := float64(elapsed) / float64(b.refillEvery)
	b.tokens += units * b.refillAmount
	if b.tokens > float64(b.capacity) {
		b.tokens = float64(b.capacity)
	}
	b.lastRefill = now
}

