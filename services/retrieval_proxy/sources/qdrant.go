package sources

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	defaultTimeout   = 2 * time.Second
	defaultRetryMax  = 2
	minBackoff       = 100 * time.Millisecond
	maxBackoff       = 2 * time.Second
	qdrantSearchPath = "/collections/%s/points/search"
	contentTypeJSON  = "application/json"
)

// HTTPClient represents a minimal http client.
type HTTPClient interface {
	Do(req *http.Request) (*http.Response, error)
}

// QdrantSource provides concurrent querying with retry and timeout controls.
type QdrantSource struct {
	baseURL  string
	client   HTTPClient
	retryMax int
}

// Query encapsulates a search request for a single Qdrant collection.
type Query struct {
	Collection string
	Payload    any
	Headers    http.Header
}

// Result aggregates the search results from Qdrant.
type Result struct {
	Items  []json.RawMessage
	TookMs int64
	Code   int
	Err    error
}

// NewQdrantSource creates a Qdrant source client.
func NewQdrantSource(baseURL string, client HTTPClient, retryMax int) (*QdrantSource, error) {
	if baseURL == "" {
		return nil, fmt.Errorf("qdrant baseURL required")
	}
	if client == nil {
		httpClient := &http.Client{
			Timeout: defaultTimeout,
		}
		client = httpClient
	}
	if retryMax < 0 {
		retryMax = defaultRetryMax
	}

	return &QdrantSource{
		baseURL:  strings.TrimRight(baseURL, "/"),
		client:   client,
		retryMax: retryMax,
	}, nil
}

// NewQdrantSourceFromEnv builds the source using environment variables.
func NewQdrantSourceFromEnv() (*QdrantSource, error) {
	baseURL := strings.TrimSpace(os.Getenv("QDRANT_URL"))
	if baseURL == "" {
		return nil, fmt.Errorf("QDRANT_URL not set")
	}

	timeout := parseDurationFromEnv("TIMEOUT_MS", defaultTimeout)
	retryMax := parseIntFromEnv("RETRY_MAX", defaultRetryMax)

	httpClient := &http.Client{
		Timeout: timeout,
	}

	return NewQdrantSource(baseURL, httpClient, retryMax)
}

// Search executes the provided queries concurrently.
func (s *QdrantSource) Search(ctx context.Context, queries []Query) Result {
	if len(queries) == 0 {
		return Result{}
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	result := Result{
		Items: make([]json.RawMessage, len(queries)),
	}
	start := time.Now()

	var (
		wg       sync.WaitGroup
		errOnce  sync.Once
		errMutex sync.Mutex
	)

	for idx, query := range queries {
		idx := idx
		query := query
		wg.Add(1)
		go func() {
			defer wg.Done()
			item, code, err := s.execute(ctx, query)
			if err != nil {
				errOnce.Do(func() {
					result.Err = err
					result.Code = code
					cancel()
				})
				return
			}

			errMutex.Lock()
			result.Items[idx] = item
			if result.Code == 0 {
				result.Code = code
			}
			errMutex.Unlock()
		}()
	}

	wg.Wait()
	result.TookMs = time.Since(start).Milliseconds()
	if result.Err == nil && result.Code == 0 {
		result.Code = http.StatusOK
	}
	return result
}

func (s *QdrantSource) execute(ctx context.Context, query Query) (json.RawMessage, int, error) {
	if query.Collection == "" {
		return nil, 0, fmt.Errorf("collection required")
	}

	payload, err := json.Marshal(query.Payload)
	if err != nil {
		return nil, 0, fmt.Errorf("marshal payload: %w", err)
	}

	endpoint := fmt.Sprintf(qdrantSearchPath, url.PathEscape(query.Collection))
	fullURL := fmt.Sprintf("%s%s", s.baseURL, endpoint)

	var (
		attempt   int
		lastError error
		status    int
		backoff   = minBackoff
	)

	for {
		attempt++
		req, err := http.NewRequestWithContext(ctx, http.MethodPost, fullURL, bytes.NewReader(payload))
		if err != nil {
			return nil, status, fmt.Errorf("create request: %w", err)
		}
		req.Header.Set("Content-Type", contentTypeJSON)
		req.Header.Set("Accept", contentTypeJSON)

		for k, values := range query.Headers {
			for _, v := range values {
				req.Header.Add(k, v)
			}
		}

		resp, err := s.client.Do(req)
		if err != nil {
			if ctx.Err() != nil {
				return nil, status, ctx.Err()
			}
			lastError = err
		} else {
			status = resp.StatusCode
			body, readErr := io.ReadAll(resp.Body)
			resp.Body.Close()

			if readErr != nil {
				lastError = fmt.Errorf("read response: %w", readErr)
			} else if status >= 500 && attempt <= s.retryMax {
				lastError = fmt.Errorf("server error: %s", strings.TrimSpace(string(body)))
			} else if status >= 400 {
				return body, status, fmt.Errorf("qdrant error: %s", strings.TrimSpace(string(body)))
			} else {
				return body, status, nil
			}
		}

		if attempt > s.retryMax {
			if lastError == nil {
				lastError = fmt.Errorf("request failed after %d attempts", attempt-1)
			}
			return nil, status, lastError
		}

		if !sleepWithContext(ctx, backoff) {
			if ctx.Err() != nil {
				return nil, status, ctx.Err()
			}
			return nil, status, fmt.Errorf("retry interrupted")
		}
		backoff = nextBackoff(backoff)
	}
}

func (s *QdrantSource) String() string {
	return fmt.Sprintf("qdrant_source{base=%s,retry_max=%d}", s.baseURL, s.retryMax)
}

func parseDurationFromEnv(key string, fallback time.Duration) time.Duration {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	ms, err := strconv.Atoi(value)
	if err != nil || ms <= 0 {
		return fallback
	}
	return time.Duration(ms) * time.Millisecond
}

func parseIntFromEnv(key string, fallback int) int {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	if parsed < 0 {
		return fallback
	}
	return parsed
}

func nextBackoff(current time.Duration) time.Duration {
	next := current * 2
	if next > maxBackoff {
		return maxBackoff
	}
	return next
}

func sleepWithContext(ctx context.Context, d time.Duration) bool {
	timer := time.NewTimer(d)
	defer timer.Stop()

	select {
	case <-ctx.Done():
		return false
	case <-timer.C:
		return true
	}
}

