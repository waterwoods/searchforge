package policy

// mvp-5

import (
	"context"
	"sync/atomic"
	"time"

	"github.com/searchforge/retrieval_proxy/obs"
)

// BudgetResult tracks whether the overall budget was exhausted.
// mvp-5
type BudgetResult struct {
	hit atomic.Bool
}

// Hit reports whether the allotted budget was consumed.
// mvp-5
func (b *BudgetResult) Hit() bool {
	if b == nil {
		return false
	}
	return b.hit.Load()
}

// BudgetArbiter derives a deadline-bound context from parent and records whether the budget was reached.
// mvp-5
func BudgetArbiter(parent context.Context, budgetMS int) (context.Context, context.CancelFunc, *BudgetResult) {
	if parent == nil {
		parent = context.Background()
	}

	result := &BudgetResult{}
	if budgetMS <= 0 {
		ctx, cancel := context.WithCancel(parent)
		return ctx, cancel, result
	}

	ctx, cancel := context.WithTimeout(parent, time.Duration(budgetMS)*time.Millisecond)
	go func() {
		<-ctx.Done()
		if ctx.Err() == context.DeadlineExceeded {
			result.hit.Store(true)
			obs.IncBudgetHit()
		}
	}()
	return ctx, cancel, result
}
