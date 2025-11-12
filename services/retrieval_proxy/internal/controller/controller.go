package controller

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"time"

	"github.com/google/uuid"

	"github.com/searchforge/retrieval_proxy/fuse"
	"github.com/searchforge/retrieval_proxy/internal/api"
	"github.com/searchforge/retrieval_proxy/policy"
	"github.com/searchforge/retrieval_proxy/sources"
)

const (
	defaultTraceHost = "us.cloud.langfuse.com"
)

// Source defines the behaviour required by upstream retrieval sources.
type Source interface {
	Search(ctx context.Context, queries []sources.Query) sources.Result
}

// Config groups necessary controller parameters.
type Config struct {
	SourceName         string
	Collection         string
	DefaultK           int
	TopKMax            int
	Fuse               fuse.CombineConfig
	SourcePolicy       policy.SourceConfig
	Metrics            *policy.Metrics
	LangfuseProjectID  string
	LangfuseHost       string
	FallbackOnError    bool
}

// Controller orchestrates policy enforcement, source querying, and result fusion.
type Controller struct {
	source     Source
	config     Config
	metrics    *policy.Metrics
	projectID  string
	traceHost  string
	topKMax    int
	defaultK   int
}

// New constructs a Controller instance.
func New(source Source, cfg Config) (*Controller, error) {
	if source == nil {
		return nil, fmt.Errorf("source is required")
	}
	if cfg.SourceName == "" {
		cfg.SourceName = "qdrant"
	}
	if cfg.Collection == "" {
		cfg.Collection = os.Getenv("QDRANT_COLLECTION")
	}
	if cfg.DefaultK <= 0 {
		cfg.DefaultK = 10
	}
	if cfg.TopKMax <= 0 {
		cfg.TopKMax = fuse.DefaultCombineConfig().TopKMax
	}
	if cfg.Metrics == nil {
		cfg.Metrics = policy.NewMetrics()
	}
	if cfg.Fuse.RRFK <= 0 {
		cfg.Fuse.RRFK = fuse.DefaultCombineConfig().RRFK
	}
	if cfg.Fuse.TopKInit <= 0 {
		cfg.Fuse.TopKInit = fuse.DefaultCombineConfig().TopKInit
	}
	if cfg.Fuse.TopKMax <= 0 {
		cfg.Fuse.TopKMax = cfg.TopKMax
	}
	if cfg.Fuse.TopKMax > cfg.TopKMax {
		cfg.Fuse.TopKMax = cfg.TopKMax
	}

	traceHost := cfg.LangfuseHost
	if traceHost == "" {
		traceHost = defaultTraceHost
	}

	return &Controller{
		source:    source,
		config:    cfg,
		metrics:   cfg.Metrics,
		projectID: cfg.LangfuseProjectID,
		traceHost: traceHost,
		topKMax:   cfg.TopKMax,
		defaultK:  cfg.DefaultK,
	}, nil
}

// TopKMax exposes the configured cap for K.
func (c *Controller) TopKMax() int {
	return c.topKMax
}

// DefaultK returns the default K value.
func (c *Controller) DefaultK() int {
	return c.defaultK
}

// Search executes the retrieval pipeline.
func (c *Controller) Search(ctx context.Context, req api.SearchRequest) (api.SearchResponse, error) {
	response := api.SearchResponse{
		Timings: api.TimingInfo{
			PerSource: map[string]int64{},
		},
		TraceID: req.TraceID,
	}

	if err := req.Validate(c.topKMax); err != nil {
		return response, err
	}

	traceID := req.TraceID
	if traceID == "" {
		traceID = c.generateTraceID()
	}
	response.TraceID = traceID
	response.TraceURL = c.buildTraceURL(traceID)

	start := time.Now()

	ctrl, err := policy.NewController(ctx, policy.ControllerConfig{
		BudgetMs: req.BudgetMS,
		Sources: []policy.SourceConfig{
			c.config.SourcePolicy,
		},
	}, c.metrics)
	if err != nil {
		return response, fmt.Errorf("policy controller: %w", err)
	}

	budgetCtx := api.ContextWithTraceID(ctrl.Budget().Context(), traceID)

	sourcePolicy, ok := ctrl.Source(c.config.SourceName)
	if !ok {
		return response, fmt.Errorf("source %s not registered", c.config.SourceName)
	}

	var (
		result    sources.Result
		sourceErr error
	)

	err = sourcePolicy.Execute(budgetCtx, func(ctx context.Context) error {
		result = c.source.Search(ctx, []sources.Query{
			{
				Collection: c.config.Collection,
				Payload:    c.buildPayload(req),
			},
		})
		sourceErr = result.Err
		response.Timings.PerSource[c.config.SourceName] = result.TookMs
		if result.Err != nil {
			return result.Err
		}
		return nil
	})

	degraded := false
	if err != nil {
		degraded = true
		if !c.config.FallbackOnError {
			return response, err
		}
		sourceErr = nil
	}

	items := c.combineResults(req, result)

	response.Items = items
	response.Degraded = degraded
	response.Timings.TotalMs = time.Since(start).Milliseconds()

	return response, sourceErr
}

func (c *Controller) combineResults(req api.SearchRequest, result sources.Result) []fuse.FusedItem {
	if len(result.Items) == 0 {
		return []fuse.FusedItem{}
	}

	cfg := c.config.Fuse
	if req.K > cfg.TopKInit {
		cfg.TopKInit = req.K
	}
	if cfg.TopKInit > cfg.TopKMax {
		cfg.TopKInit = cfg.TopKMax
	}

	sourceResult := fuse.SourceResult{
		Source: c.config.SourceName,
		Items:  c.parseQdrantItems(result.Items[0]),
	}

	fused := fuse.RRFCombine([]fuse.SourceResult{sourceResult}, cfg)

	if req.K < len(fused) {
		return fused[:req.K]
	}
	return fused
}

func (c *Controller) parseQdrantItems(raw json.RawMessage) []fuse.Item {
	if len(raw) == 0 {
		return []fuse.Item{}
	}

	type point struct {
		ID      any             `json:"id"`
		Score   float64         `json:"score"`
		Payload json.RawMessage `json:"payload"`
	}
	var payload struct {
		Result []point `json:"result"`
	}

	if err := json.Unmarshal(raw, &payload); err != nil {
		return []fuse.Item{}
	}

	items := make([]fuse.Item, 0, len(payload.Result))
	for _, pt := range payload.Result {
		id := fmt.Sprintf("%v", pt.ID)
		var body any
		if len(pt.Payload) > 0 {
			if err := json.Unmarshal(pt.Payload, &body); err != nil {
				body = string(pt.Payload)
			}
		}
		items = append(items, fuse.Item{
			ID:      id,
			Score:   pt.Score,
			Payload: body,
		})
	}
	return items
}

func (c *Controller) buildPayload(req api.SearchRequest) any {
	// TODO: hook into embedding pipeline. Minimal stub to satisfy interface.
	limit := max(req.K, c.config.Fuse.TopKInit)
	if limit > c.config.Fuse.TopKMax {
		limit = c.config.Fuse.TopKMax
	}
	return map[string]any{
		"limit":         limit,
		"with_payload":  true,
		"with_vector":   false,
		"filter":        nil,
		"search_params": map[string]any{},
	}
}

func (c *Controller) buildTraceURL(traceID string) string {
	if c.projectID == "" || traceID == "" {
		return ""
	}
	return fmt.Sprintf("https://%s/project/%s/traces?query=%s", c.traceHost, c.projectID, url.QueryEscape(traceID))
}

func (c *Controller) generateTraceID() string {
	return uuid.NewString()
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

