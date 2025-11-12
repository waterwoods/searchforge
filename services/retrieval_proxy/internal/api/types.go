package api

import (
	"context"
	"fmt"
)

// SearchRequest models an inbound search request.
type SearchRequest struct {
	Query     string
	K         int
	BudgetMS  int
	TraceID   string
	RequestID string
}

// TimingInfo includes per-source timing statistics.
type TimingInfo struct {
	TotalMs   int64            `json:"total_ms"`
	PerSource map[string]int64 `json:"per_source"`
}

// SearchResponse represents the HTTP response payload.
type SearchResponse struct {
	Items    any        `json:"items"`
	Timings  TimingInfo `json:"timings"`
	Degraded bool       `json:"degraded"`
	TraceID  string     `json:"trace_id"`
	TraceURL string     `json:"trace_url"`
}

type contextKey string

const (
	traceIDKey contextKey = "retrieval_proxy_trace_id"
)

// ContextWithTraceID stores the trace identifier in the context.
func ContextWithTraceID(ctx context.Context, traceID string) context.Context {
	return context.WithValue(ctx, traceIDKey, traceID)
}

// TraceIDFromContext extracts the trace identifier from the context.
func TraceIDFromContext(ctx context.Context) (string, bool) {
	if ctx == nil {
		return "", false
	}
	value := ctx.Value(traceIDKey)
	if value == nil {
		return "", false
	}
	traceID, ok := value.(string)
	return traceID, ok
}

// Validate ensures the inbound request parameters are consistent.
func (r SearchRequest) Validate(topKMax int) error {
	if r.Query == "" {
		return fmt.Errorf("query required")
	}
	if r.K <= 0 {
		return fmt.Errorf("k must be positive")
	}
	if topKMax > 0 && r.K > topKMax {
		return fmt.Errorf("k exceeds max (%d)", topKMax)
	}
	if r.BudgetMS <= 0 {
		return fmt.Errorf("budget_ms must be positive")
	}
	return nil
}

