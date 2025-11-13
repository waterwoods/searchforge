package health

// mvp-5

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/searchforge/retrieval_proxy/internal/controller"
)

// Readyz returns an http.Handler that reports Qdrant readiness.
// mvp-5
func Readyz(ctrl *controller.Controller) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		err := ctrl.Ping(r.Context())
		latency := time.Since(start)

		ok := err == nil && latency <= 200*time.Millisecond
		status := http.StatusOK
		if !ok {
			status = http.StatusServiceUnavailable
		}

		payload := map[string]any{
			"qdrant_ok":    err == nil,
			"last_ping_ms": latency.Milliseconds(),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		_ = json.NewEncoder(w).Encode(payload)
	}
}

