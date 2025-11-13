package api

// mvp-5

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"golang.org/x/text/unicode/norm"

	"github.com/searchforge/retrieval_proxy/internal/controller"
	"github.com/searchforge/retrieval_proxy/obs"
	"github.com/searchforge/retrieval_proxy/policy"
)

const traceIDHeader = "X-Trace-Id"

// Router wires the HTTP endpoints for the retrieval proxy.
// mvp-5
type Router struct {
	ctrl          *controller.Controller
	defaultK      int
	defaultBudget int
	topKMax       int
}

// NewRouter builds the chi router with /v1/search.
// mvp-5
func NewRouter(ctrl *controller.Controller, defaultK, defaultBudget, topKMax int) *chi.Mux {
	r := &Router{
		ctrl:          ctrl,
		defaultK:      defaultK,
		defaultBudget: defaultBudget,
		topKMax:       topKMax,
	}

	mux := chi.NewRouter()
	mux.Get("/v1/search", r.handleSearch)
	return mux
}

func (r *Router) handleSearch(w http.ResponseWriter, req *http.Request) {
	start := time.Now()
	traceID, traceParent := readTrace(req)
	w.Header().Set(traceIDHeader, traceID)

	searchReq, err := r.buildRequest(req, traceID, traceParent)
	if err != nil {
		writeError(w, http.StatusBadRequest, err)
		return
	}

	ctx, cancel, budget := policy.BudgetArbiter(req.Context(), searchReq.BudgetMS)
	defer cancel()
	ctx = ContextWithTraceID(ctx, traceID)

	resp, retCode, callErr := r.ctrl.Search(ctx, searchReq)
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

	obs.ObserveProxyRequest(resp.RetCode, duration)
	writeJSON(w, status, resp)
}

func (r *Router) buildRequest(req *http.Request, traceID, traceParent string) (controller.Request, error) {
	values := req.URL.Query()

	query := normalizeQuery(values.Get("q"))
	if query == "" {
		return controller.Request{}, fmt.Errorf("q required")
	}

	k := parseInt(values.Get("k"), r.defaultK)
	budget := parseInt(values.Get("budget_ms"), r.defaultBudget)

	searchReq := controller.Request{
		Query:       query,
		K:           k,
		BudgetMS:    budget,
		TraceID:     traceID,
		TraceParent: traceParent,
	}

	if err := searchReq.Validate(r.topKMax); err != nil {
		return controller.Request{}, err
	}
	return searchReq, nil
}

func readTrace(req *http.Request) (string, string) {
	traceID := req.Header.Get(traceIDHeader)
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
		traceID = uuid.NewString()
	}

	return traceID, traceParent
}

func normalizeQuery(q string) string {
	q = strings.TrimSpace(q)
	if q == "" {
		return q
	}
	q = norm.NFKC.String(q)
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

