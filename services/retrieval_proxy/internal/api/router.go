package api

// mvp-5

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/searchforge/retrieval_proxy/internal/contract"
	"github.com/searchforge/retrieval_proxy/internal/controller"
	"github.com/searchforge/retrieval_proxy/obs"
	"github.com/searchforge/retrieval_proxy/policy"
)

type handler struct {
	ctrl          *controller.Controller
	defaultK      int
	defaultBudget int
	topKMax       int
}

// NewHandler returns an http.Handler for /v1/search.
// mvp-5
func NewHandler(ctrl *controller.Controller, defaultK, defaultBudget, topKMax int) http.Handler {
	return &handler{
		ctrl:          ctrl,
		defaultK:      defaultK,
		defaultBudget: defaultBudget,
		topKMax:       topKMax,
	}
}

func (h *handler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodGet {
		writeError(w, http.StatusMethodNotAllowed, fmt.Errorf("method not allowed"))
		return
	}

	start := time.Now()
	traceID, traceParent := readTrace(req)
	w.Header().Set(contract.TraceIDHeader, traceID)

	searchReq, err := h.buildRequest(req, traceID, traceParent)
	if err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}

	ctx, cancel, budget := policy.BudgetArbiter(req.Context(), searchReq.BudgetMS)
	defer cancel()
	ctx = contract.WithTraceID(ctx, traceID)

	resp, retCode, callErr := h.ctrl.Search(ctx, searchReq)
	duration := time.Since(start)

	if budget.Hit() {
		resp.Degraded = true
		if resp.RetCode == "" {
			resp.RetCode = "UPSTREAM_TIMEOUT"
		}
	}

	if resp.RetCode == "" {
		resp.RetCode = retCode
	}

	status := http.StatusOK
	if callErr != nil {
		switch {
		case errors.Is(callErr, context.DeadlineExceeded) || errors.Is(callErr, controller.ErrUpstreamTimeout):
			resp.RetCode = "UPSTREAM_TIMEOUT"
			resp.Degraded = true
		case errors.Is(callErr, controller.ErrBadRequest):
			status = http.StatusBadRequest
		default:
			status = http.StatusInternalServerError
			if resp.RetCode == "" {
				resp.RetCode = "ERROR"
			}
		}
	}

	obs.ObserveProxyRequest(resp.RetCode, duration, traceID)
	log.Printf("trace_id=%s route=proxy ret_code=%s degraded=%t duration_ms=%d status=%d", traceID, resp.RetCode, resp.Degraded, duration.Milliseconds(), status)
	writeJSON(w, status, resp)
}

func (h *handler) buildRequest(req *http.Request, traceID, traceParent string) (contract.Request, error) {
	values := req.URL.Query()

	query := normalizeQuery(values.Get("q"))
	if query == "" {
		return contract.Request{}, fmt.Errorf("q required")
	}

	k := parseInt(values.Get("k"), h.defaultK)
	budget := parseInt(values.Get("budget_ms"), h.defaultBudget)

	searchReq := contract.Request{
		Query:       query,
		K:           k,
		BudgetMS:    budget,
		TraceID:     traceID,
		TraceParent: traceParent,
	}

	if err := searchReq.Validate(h.topKMax); err != nil {
		return contract.Request{}, err
	}
	return searchReq, nil
}

func readTrace(req *http.Request) (string, string) {
	traceID := req.Header.Get(contract.TraceIDHeader)
	if traceID == "" {
		traceID = req.URL.Query().Get("trace_id")
	}

	traceParent := req.Header.Get("traceparent")
	if traceParent == "" {
		traceParent = req.URL.Query().Get("traceparent")
	}

	if traceID == "" && traceParent != "" {
		parts := strings.Split(traceParent, "-")
		if len(parts) >= 2 && len(parts[1]) == 32 {
			traceID = parts[1]
		}
	}

	if traceID == "" {
		traceID = generateTraceID()
	}

	return traceID, traceParent
}

func generateTraceID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(b[:])
}

func normalizeQuery(q string) string {
	q = strings.TrimSpace(q)
	if q == "" {
		return q
	}
	return strings.Join(strings.Fields(q), " ")
}

func parseInt(value string, fallback int) int {
	if value == "" {
		return fallback
	}
	num, err := strconv.Atoi(value)
	if err != nil || num <= 0 {
		return fallback
	}
	return num
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(payload)
}

func writeError(w http.ResponseWriter, status int, err error) {
	writeJSON(w, status, map[string]string{"error": err.Error()})
}
