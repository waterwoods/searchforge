package policy

import (
	"context"
	"fmt"
)

// Controller wires together the budget arbiter with per-source policies.
type Controller struct {
	budget  *BudgetArbiter
	sources map[string]*SourcePolicy
	metrics *Metrics
}

// ControllerConfig groups the top-level policy configuration.
type ControllerConfig struct {
	BudgetMs int
	Sources  []SourceConfig
}

// NewController creates a policy controller with the provided configuration.
func NewController(ctx context.Context, cfg ControllerConfig, metrics *Metrics) (*Controller, error) {
	if metrics == nil {
		metrics = NewMetrics()
	}

	budget, err := NewBudgetArbiter(ctx, cfg.BudgetMs, metrics)
	if err != nil {
		return nil, fmt.Errorf("budget arbiter: %w", err)
	}

	sourcePolicies := make(map[string]*SourcePolicy, len(cfg.Sources))
	for _, sc := range cfg.Sources {
		policy, err := NewSourcePolicy(sc, metrics)
		if err != nil {
			return nil, fmt.Errorf("source %q: %w", sc.Name, err)
		}
		sourcePolicies[sc.Name] = policy
	}

	return &Controller{
		budget:  budget,
		sources: sourcePolicies,
		metrics: metrics,
	}, nil
}

// Budget returns the budget arbiter.
func (c *Controller) Budget() *BudgetArbiter {
	return c.budget
}

// Source returns the policy for the requested source.
func (c *Controller) Source(name string) (*SourcePolicy, bool) {
	policy, ok := c.sources[name]
	return policy, ok
}

// Metrics returns the metrics collector.
func (c *Controller) Metrics() *Metrics {
	return c.metrics
}


