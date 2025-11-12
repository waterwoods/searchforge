package policy

import "errors"

var (
	// ErrCircuitOpen indicates the circuit breaker is currently open.
	ErrCircuitOpen = errors.New("circuit breaker open")
	// ErrRateLimited indicates the source requests are rate limited.
	ErrRateLimited = errors.New("rate limited")
	// ErrBudgetExceeded indicates the overall budget has been exhausted.
	ErrBudgetExceeded = errors.New("budget exceeded")
	// ErrInvalidBudget indicates the provided budget is invalid.
	ErrInvalidBudget = errors.New("invalid budget")
)

