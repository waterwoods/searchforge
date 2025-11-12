package policy

import (
	"context"
	"errors"
	"sync"
	"time"
)

// BudgetArbiter manages the total execution budget for a search request.
// It exposes a context that will be cancelled once the assigned budget
// is exhausted. This budget is independent from per-source timeouts.
type BudgetArbiter struct {
	ctx     context.Context
	cancel  context.CancelFunc
	start   time.Time
	total   time.Duration
	bounded bool
	metrics *Metrics
	once    sync.Once
}

// NewBudgetArbiter creates a new budget arbiter for the provided parent context.
// budgetMs must be positive to create a bounded budget. When budgetMs is zero,
// the arbiter will return an already-cancelled context with ErrInvalidBudget.
func NewBudgetArbiter(parent context.Context, budgetMs int, metrics *Metrics) (*BudgetArbiter, error) {
	if budgetMs < 0 {
		return nil, ErrInvalidBudget
	}

	var (
		ctx     context.Context
		cancel  context.CancelFunc
		total   time.Duration
		bounded bool
	)

	if budgetMs == 0 {
		ctx, cancel = context.WithCancel(parent)
		total = 0
		bounded = false
	} else {
		total = time.Duration(budgetMs) * time.Millisecond
		ctx, cancel = context.WithTimeout(parent, total)
		bounded = true
	}

	arbiter := &BudgetArbiter{
		ctx:     ctx,
		cancel:  cancel,
		start:   time.Now(),
		total:   total,
		bounded: bounded,
		metrics: metrics,
	}

	if metrics != nil {
		go arbiter.observeCompletion()
	}

	return arbiter, nil
}

// Context returns the budget-aware context.
func (b *BudgetArbiter) Context() context.Context {
	return b.ctx
}

// Remaining returns the remaining time before the budget expires.
func (b *BudgetArbiter) Remaining() time.Duration {
	if !b.bounded {
		return time.Duration(1<<63 - 1)
	}
	if deadline, ok := b.ctx.Deadline(); ok {
		remaining := time.Until(deadline)
		if remaining < 0 {
			return 0
		}
		return remaining
	}
	return 0
}

// Cancel releases the budget early, preventing further work.
func (b *BudgetArbiter) Cancel() {
	b.once.Do(func() {
		b.cancel()
	})
}

func (b *BudgetArbiter) observeCompletion() {
	<-b.ctx.Done()

	err := b.ctx.Err()
	elapsed := time.Since(b.start)
	if elapsed < 0 {
		elapsed = 0
	}

	if b.metrics != nil {
		b.metrics.ObserveTotal(elapsed)

		if b.bounded && errors.Is(err, context.DeadlineExceeded) {
			b.metrics.IncBudgetHit()
		}
	}
}

