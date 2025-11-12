package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"golang.org/x/text/unicode/norm"

	"github.com/searchforge/retrieval_proxy/internal/controller"
)

const (
	traceHeader = "X-Trace-Id"
)

// Router wires the HTTP endpoints for the retrieval proxy.
type Router struct {
	controller  *controller.Controller
	topKMax     int
	defaultK    int
	defaultBudget int
}

// NewRouter constructs the HTTP router.
func NewRouter(ctrl *controller.Controller, defaultBudget int) (*chi.Mux, error) {
	if ctrl == nil {
		return nil, fmt.Errorf("controller is required")
	}
	r := &Router{
		controller:   ctrl,
		topKMax:      ctrl.TopKMax(),
		defaultK:     ctrl.DefaultK(),
		defaultBudget: defaultBudget,
	}

	mux := chi.NewRouter()
	mux.Get("/healthz", r.handleHealthz)
	mux.Get("/readyz", r.handleReadyz)
	mux.Get("/v1/search", r.handleSearch)

	return mux, nil
}

func (r *Router) handleHealthz(w http.ResponseWriter, req *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}

func (r *Router) handleReadyz(w http.ResponseWriter, req *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ready"))
}

func (r *Router) handleSearch(w http.ResponseWriter, req *http.Request) {
	ctx := req.Context()

	traceID := req.Header.Get(traceHeader)
	if traceID == "" {
		traceID = req.URL.Query().Get("trace_id")
	}
	if traceID == "" {
		traceID = uuid.NewString()
	}
	w.Header().Set(traceHeader, traceID)
	ctx = ContextWithTraceID(ctx, traceID)

	query := normalizeQuery(req.URL.Query().Get("q"))
	k := parseInt(req.URL.Query().Get("k"), r.defaultK)
	budgetMS := parseInt(req.URL.Query().Get("budget_ms"), r.defaultBudget)

	if budgetMS <= 0 {
		http.Error(w, "invalid budget_ms", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(ctx, time.Duration(budgetMS)*time.Millisecond)
	defer cancel()

	searchReq := SearchRequest{
		Query:    query,
		K:        k,
		BudgetMS: budgetMS,
		TraceID:  traceID,
	}

	if err := searchReq.Validate(r.topKMax); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	resp, err := r.controller.Search(ctx, searchReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	writeJSON(w, resp)
}

func normalizeQuery(q string) string {
	q = strings.TrimSpace(q)
	if q == "" {
		return q
	}
	q = norm.NFKC.String(q)
	fields := strings.Fields(q)
	return strings.Join(fields, " ")
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

func writeJSON(w http.ResponseWriter, payload any) {
	w.Header().Set("Content-Type", "application/json")
	encoder := json.NewEncoder(w)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(payload); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

