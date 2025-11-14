package controller

// mvp-5

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/searchforge/retrieval_proxy/fuse"
	"github.com/searchforge/retrieval_proxy/internal/contract"
	"github.com/searchforge/retrieval_proxy/policy"
	"github.com/searchforge/retrieval_proxy/sources"
)

var (
	// ErrUpstreamTimeout indicates an upstream call exceeded its deadline.
	// mvp-5
	ErrUpstreamTimeout = errors.New("upstream timeout")
	// ErrBadRequest indicates the request was invalid.
	// mvp-5
	ErrBadRequest = errors.New("bad request")
)

// Source defines the behaviour required by upstream retrieval sources.
// mvp-5
type Source interface {
	Search(ctx context.Context, queries []sources.Query) sources.Result
	Ping(ctx context.Context) error
}

// Config groups controller dependencies.
// mvp-5
type Config struct {
	SourceName      string
	Collection      string
	Policy          policy.SourceConfig
	Fuse            fuse.CombineConfig
	CacheTTL        time.Duration
	PolicyVersion   string
	LangfuseHost    string
	LangfuseProject string
}

// Controller coordinates policy, caching, and fusion.
// mvp-5
type Controller struct {
	source      Source
	sourceName  string
	collection  string
	policy      *policy.SourcePolicy
	fuseConfig  fuse.CombineConfig
	cache       *Cache
	policyHash  string
	host        string
	project     string
}

// New constructs a controller.
// mvp-5
func New(src Source, cfg Config) (*Controller, error) {
	if src == nil {
		return nil, fmt.Errorf("source required")
	}

	if cfg.SourceName == "" {
		cfg.SourceName = "qdrant"
	}
	if cfg.Collection == "" {
		cfg.Collection = os.Getenv("QDRANT_COLLECTION")
	}

	policyConfig := cfg.Policy
	policyConfig.Name = cfg.SourceName
	if policyConfig.Timeout <= 0 {
		policyConfig.Timeout = 300 * time.Millisecond
	}

	sourcePolicy, err := policy.NewSourcePolicy(policyConfig)
	if err != nil {
		return nil, err
	}

	fuseCfg := cfg.Fuse
	if fuseCfg.RRFK <= 0 {
		fuseCfg = fuse.DefaultCombineConfig()
	}
	if fuseCfg.TopKMax <= 0 {
		fuseCfg.TopKMax = fuse.DefaultCombineConfig().TopKMax
	}
	if fuseCfg.TopKInit <= 0 {
		fuseCfg.TopKInit = fuse.DefaultCombineConfig().TopKInit
	}

	cache := NewCache(cfg.CacheTTL)

	return &Controller{
		source:     src,
		sourceName: cfg.SourceName,
		collection: cfg.Collection,
		policy:     sourcePolicy,
		fuseConfig: fuseCfg,
		cache:      cache,
		policyHash: cfg.PolicyVersion,
		host:       cfg.LangfuseHost,
		project:    cfg.LangfuseProject,
	}, nil
}

// Search executes the retrieval pipeline.
// mvp-5
func (c *Controller) Search(ctx context.Context, req contract.Request) (contract.Response, string, error) {
	var resp contract.Response
	resp.Timings.PerSource = make(map[string]int64)
	resp.RetCode = "OK"
	resp.TraceURL = c.BuildTraceURL(req.TraceID)

	if err := req.Validate(int(c.fuseConfig.TopKMax)); err != nil {
		resp.RetCode = "BAD_REQUEST"
		return resp, "BAD_REQUEST", ErrBadRequest
	}

	cacheKey := BuildCacheKey(req.Query, req.K, c.sourceName, c.fuseConfig, c.policyHash)
	if entry, ok := c.cache.Get(cacheKey); ok {
		resp.Items = cloneItems(entry.Items)
		resp.Timings.TotalMS = entry.TotalMS
		resp.Timings.PerSource = cloneTiming(entry.PerSource)
		resp.Timings.CacheHit = true
		resp.Degraded = entry.Degraded
		resp.RetCode = entry.RetCode
		return resp, resp.RetCode, nil
	}

	start := time.Now()
	result, timedOut, err := c.callSource(ctx, req)
	totalMs := time.Since(start).Milliseconds()
	resp.Timings.TotalMS = totalMs
	resp.Timings.PerSource[c.sourceName] = result.TookMs

	if err != nil {
		resp.RetCode = "DEGRADED"
		resp.Degraded = true
		return resp, resp.RetCode, err
	}

	if timedOut {
		resp.RetCode = "UPSTREAM_TIMEOUT"
		resp.Degraded = true
		return resp, resp.RetCode, ErrUpstreamTimeout
	}

	resp.Items = fuseToContract(c.applyFuse(req.K, result.Items))
	resp.Timings.CacheHit = false
	resp.RetCode = "OK"
	resp.Degraded = false

	c.cache.Set(cacheKey, CacheEntry{
		Items:     cloneItems(resp.Items),
		PerSource: cloneTiming(resp.Timings.PerSource),
		TotalMS:   resp.Timings.TotalMS,
		Degraded:  resp.Degraded,
		RetCode:   resp.RetCode,
	})

	return resp, resp.RetCode, nil
}

func (c *Controller) callSource(ctx context.Context, req contract.Request) (sources.Result, bool, error) {
	var result sources.Result
	var timedOut bool
	err := c.policy.Execute(ctx, func(callCtx context.Context) error {
		select {
		case <-time.After(200 * time.Millisecond):
		case <-callCtx.Done():
			timedOut = errors.Is(callCtx.Err(), context.DeadlineExceeded)
			return callCtx.Err()
		}
		result = c.source.Search(callCtx, []sources.Query{
			{
				Collection: c.collection,
				Payload:    c.buildPayload(req.K),
			},
		})
		return result.Err
	})
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			timedOut = true
		}
		result.Err = nil
		result.Items = nil
		result.Code = http.StatusOK
		err = nil
	}
	return result, timedOut, err
}

func (c *Controller) applyFuse(k int, raw []json.RawMessage) []fuse.FusedItem {
	if len(raw) == 0 {
		return nil
	}
	sourceItems := []fuse.SourceResult{
		{
			Source: c.sourceName,
			Items:  c.decodeItems(raw[0]),
		},
	}
	cfg := c.fuseConfig
	if k > cfg.TopKInit {
		cfg.TopKInit = k
	}
	if cfg.TopKInit > cfg.TopKMax {
		cfg.TopKInit = cfg.TopKMax
	}

	items := fuse.RRFCombine(sourceItems, cfg)
	if k < len(items) {
		return items[:k]
	}
	return items
}

func (c *Controller) decodeItems(raw json.RawMessage) []fuse.Item {
	if len(raw) == 0 {
		return nil
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
		return nil
	}

	items := make([]fuse.Item, 0, len(payload.Result))
	for _, pt := range payload.Result {
		item := fuse.Item{
			ID:    fmt.Sprintf("%v", pt.ID),
			Score: pt.Score,
		}
		if len(pt.Payload) > 0 {
			var payloadAny interface{}
			if err := json.Unmarshal(pt.Payload, &payloadAny); err == nil {
				item.Payload = payloadAny
			} else {
				item.Payload = string(pt.Payload)
			}
		}
		items = append(items, item)
	}
	return items
}

func (c *Controller) buildPayload(k int) any {
	limit := k
	if limit < c.fuseConfig.TopKInit {
		limit = c.fuseConfig.TopKInit
	}
	if limit > c.fuseConfig.TopKMax {
		limit = c.fuseConfig.TopKMax
	}

	return map[string]any{
		"limit":         limit,
		"with_payload":  true,
		"with_vector":   false,
		"filter":        nil,
		"search_params": map[string]any{},
	}
}

// BuildTraceURL builds a Langfuse trace if configured.
// mvp-5
func (c *Controller) BuildTraceURL(traceID string) string {
	if c.host == "" || c.project == "" || traceID == "" {
		return ""
	}
	base := strings.TrimSuffix(c.host, "/")
	return fmt.Sprintf("%s/project/%s/traces?query=%s", base, c.project, url.QueryEscape(traceID))
}

// Ping validates upstream readiness.
// mvp-5
func (c *Controller) Ping(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 200*time.Millisecond)
	defer cancel()
	return c.source.Ping(ctx)
}

func cloneItems(items []contract.Item) []contract.Item {
	if len(items) == 0 {
		return nil
	}
	out := make([]contract.Item, len(items))
	copy(out, items)
	return out
}

func cloneTiming(in map[string]int64) map[string]int64 {
	out := make(map[string]int64, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}

func fuseToContract(items []fuse.FusedItem) []contract.Item {
	if len(items) == 0 {
		return nil
	}
	out := make([]contract.Item, 0, len(items))
	for _, it := range items {
		out = append(out, contract.Item{
			ID:      it.ID,
			Score:   it.Score,
			Payload: it.Payload,
		})
	}
	return out
}
