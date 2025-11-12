package policy

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/searchforge/retrieval_proxy/testutil"
)

func TestSourcePolicyTimeoutTriggersError(t *testing.T) {
	fake := testutil.NewFakeSource(testutil.FakeResponse{
		Delay:  150 * time.Millisecond,
		Status: http.StatusOK,
	})
	defer fake.Close()

	policy, err := NewSourcePolicy(SourceConfig{
		Name:    "fake",
		Timeout: 50 * time.Millisecond,
	}, nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	ctx := context.Background()
	callErr := policy.Execute(ctx, func(ctx context.Context) error {
		req, _ := http.NewRequestWithContext(ctx, http.MethodGet, fake.URL(), nil)
		resp, err := http.DefaultClient.Do(req)
		if resp != nil {
			resp.Body.Close()
		}
		return err
	})

	if !errors.Is(callErr, context.DeadlineExceeded) {
		t.Fatalf("expected deadline exceeded, got %v", callErr)
	}
}

func TestSourcePolicyCircuitOpensAfterFailures(t *testing.T) {
	fake := testutil.NewFakeSource(
		testutil.FakeResponse{Status: http.StatusInternalServerError},
		testutil.FakeResponse{Status: http.StatusInternalServerError},
		testutil.FakeResponse{Status: http.StatusInternalServerError},
	)
	defer fake.Close()

	cfg := SourceConfig{
		Name:    "fake",
		Timeout: 200 * time.Millisecond,
		Circuit: CircuitBreakerConfig{
			Window:               500 * time.Millisecond,
			FailureRateThreshold: 0.5,
			MinSamples:           2,
			Cooldown:             100 * time.Millisecond,
			HalfOpenMaxCalls:     1,
		},
	}

	policy, err := NewSourcePolicy(cfg, nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	ctx := context.Background()
	call := func(ctx context.Context) error {
		req, _ := http.NewRequestWithContext(ctx, http.MethodGet, fake.URL(), nil)
		resp, err := http.DefaultClient.Do(req)
		if resp != nil {
			resp.Body.Close()
		}
		if err != nil {
			return err
		}
		if resp.StatusCode >= 400 {
			return fmt.Errorf("status %d", resp.StatusCode)
		}
		return nil
	}

	for i := 0; i < 3; i++ {
		_ = policy.Execute(ctx, call)
	}

	if err := policy.Execute(ctx, call); !errors.Is(err, ErrCircuitOpen) {
		t.Fatalf("expected circuit open error, got %v", err)
	}

	time.Sleep(cfg.Cooldown + 20*time.Millisecond)

	fake.SetResponses(testutil.FakeResponse{Status: http.StatusOK})

	if err := policy.Execute(ctx, call); err != nil {
		t.Fatalf("expected circuit half-open success, got %v", err)
	}
}

