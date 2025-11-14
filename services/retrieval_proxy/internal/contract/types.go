package contract

// mvp-5

import (
	"context"
	"fmt"
)

const TraceIDHeader = "X-Trace-Id"

// Request captures inbound search parameters.
// mvp-5
type Request struct {
	Query       string
	K           int
	BudgetMS    int
	TraceID     string
	TraceParent string
}

// Validate ensures the inbound request parameters are consistent.
// mvp-5
func (r Request) Validate(maxK int) error {
	if r.Query == "" {
		return fmt.Errorf("q required")
	}
	if r.K <= 0 {
		return fmt.Errorf("k must be positive")
	}
	if maxK > 0 && r.K > maxK {
		return fmt.Errorf("k exceeds max (%d)", maxK)
	}
	if r.BudgetMS <= 0 {
		return fmt.Errorf("budget_ms must be positive")
	}
	return nil
}

// Item represents a fused search result.
// mvp-5
type Item struct {
	ID      string      `json:"id"`
	Score   float64     `json:"score"`
	Payload interface{} `json:"payload,omitempty"`
}

// Response encapsulates the public response schema for /v1/search.
// mvp-5
type Response struct {
	Items   []Item `json:"items"`
	Timings struct {
		TotalMS   int64            `json:"total_ms"`
		PerSource map[string]int64 `json:"per_source_ms"`
		CacheHit  bool             `json:"cache_hit"`
	} `json:"timings"`
	RetCode  string `json:"ret_code"`
	Degraded bool   `json:"degraded"`
	TraceURL string `json:"trace_url,omitempty"`
}

type contextKey string

const traceIDKey contextKey = "retrieval_proxy_trace_id"

// WithTraceID stores the trace identifier in context.
// mvp-5
func WithTraceID(ctx context.Context, traceID string) context.Context {
	return context.WithValue(ctx, traceIDKey, traceID)
}

// TraceIDFromContext extracts the trace identifier.
// mvp-5
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

