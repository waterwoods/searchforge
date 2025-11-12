package policy

import (
	"context"
	"testing"
	"time"
)

func TestBudgetArbiterRejectsInvalidBudget(t *testing.T) {
	_, err := NewBudgetArbiter(context.Background(), -1, nil)
	if err != ErrInvalidBudget {
		t.Fatalf("expected ErrInvalidBudget, got %v", err)
	}
}

func TestBudgetArbiterCancelsWithinBudget(t *testing.T) {
	arbiter, err := NewBudgetArbiter(context.Background(), 50, nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	ctx := arbiter.Context()
	select {
	case <-ctx.Done():
	case <-time.After(200 * time.Millisecond):
		t.Fatal("expected context to cancel within budget window")
	}

	if ctx.Err() != context.DeadlineExceeded {
		t.Fatalf("expected deadline exceeded, got %v", ctx.Err())
	}
}

