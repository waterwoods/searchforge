package main

// mvp-5

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/searchforge/retrieval_proxy/fuse"
	"github.com/searchforge/retrieval_proxy/internal/api"
	"github.com/searchforge/retrieval_proxy/internal/controller"
	"github.com/searchforge/retrieval_proxy/internal/health"
	"github.com/searchforge/retrieval_proxy/obs"
	"github.com/searchforge/retrieval_proxy/policy"
	"github.com/searchforge/retrieval_proxy/sources"
)

const (
	defaultPort         = 7070
	defaultBudgetMS     = 600
	defaultTimeoutMS    = 800
	defaultTopK         = 10
	defaultTopKMax      = 64
	defaultTopKInit     = 32
	defaultRetryMax     = 2
	defaultCacheTTLMS   = 0
	defaultLangfuseHost = "https://us.cloud.langfuse.com"
)

func main() {
	cfg := loadConfig()

	shutdown, err := obs.InitTracer("retrieval-proxy")
	if err != nil {
		log.Printf("otel init error: %v", err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := shutdown(ctx); err != nil {
			log.Printf("otel shutdown error: %v", err)
		}
	}()

	client := newHTTPClient(cfg.Timeout)
	qdrant, err := sources.NewQdrantSource(cfg.QdrantURL, client, cfg.RetryMax)
	if err != nil {
		log.Fatalf("qdrant init: %v", err)
	}

	ctrl, err := controller.New(qdrant, controller.Config{
		SourceName: cfg.SourceName,
		Collection: cfg.QdrantCollection,
		Policy: policy.SourceConfig{
			Name: cfg.SourceName,
			Timeout: cfg.Timeout,
			Rate: policy.RateLimitConfig{
				Capacity:     cfg.RateCapacity,
				RefillTokens: cfg.RateRefill,
				RefillEvery:  cfg.RateInterval,
			},
			Circuit: policy.CircuitConfig{
				FailureThreshold:  cfg.FailureThreshold,
				HalfOpenSuccesses: cfg.HalfOpenSuccesses,
				Cooldown:          cfg.CircuitCooldown,
			},
		},
		Fuse: fuse.CombineConfig{
			RRFK:     cfg.RRFK,
			TopKInit: cfg.TopKInit,
			TopKMax:  cfg.TopKMax,
		},
		CacheTTL:        cfg.CacheTTL,
		PolicyVersion:   cfg.PolicyVersion,
		LangfuseHost:    cfg.LangfuseHost,
		LangfuseProject: cfg.LangfuseProject,
	})
	if err != nil {
		log.Fatalf("controller init: %v", err)
	}

	root := chi.NewRouter()
	root.Get("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	root.Get("/readyz", health.Readyz(ctrl))
	root.Handle("/metrics", promhttp.Handler())

	apiRouter := api.NewRouter(ctrl, cfg.DefaultK, cfg.BudgetMS, cfg.TopKMax)
	root.Mount("/", apiRouter)

	server := &http.Server{
		Addr:         ":" + strconv.Itoa(cfg.Port),
		Handler:      root,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("retrieval proxy listening on :%d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		log.Printf("shutdown: %v", err)
	}
}

type config struct {
	Port              int
	BudgetMS          int
	DefaultK          int
	TopKMax           int
	TopKInit          int
	RRFK              int
	QdrantURL         string
	QdrantCollection  string
	SourceName        string
	Timeout           time.Duration
	RetryMax          int
	RateCapacity      int
	RateRefill        int
	RateInterval      time.Duration
	FailureThreshold  int
	HalfOpenSuccesses int
	CircuitCooldown   time.Duration
	CacheTTL          time.Duration
	PolicyVersion     string
	LangfuseHost      string
	LangfuseProject   string
}

func loadConfig() config {
	cacheTTL := time.Duration(getEnvInt("CACHE_TTL_MS", defaultCacheTTLMS)) * time.Millisecond
	return config{
		Port:              getEnvInt("PORT", defaultPort),
		BudgetMS:          getEnvInt("BUDGET_MS", defaultBudgetMS),
		DefaultK:          getEnvInt("DEFAULT_K", defaultTopK),
		TopKMax:           getEnvInt("TOPK_MAX", defaultTopKMax),
		TopKInit:          getEnvInt("TOPK_INIT", defaultTopKInit),
		RRFK:              getEnvInt("RRF_K", fuse.DefaultCombineConfig().RRFK),
		QdrantURL:         getEnvStr("QDRANT_URL", "http://qdrant:6333"),
		QdrantCollection:  getEnvStr("QDRANT_COLLECTION", ""),
		SourceName:        getEnvStr("SOURCE_NAME", "qdrant"),
		Timeout:           time.Duration(getEnvInt("TIMEOUT_MS", defaultTimeoutMS)) * time.Millisecond,
		RetryMax:          getEnvInt("RETRY_MAX", defaultRetryMax),
		RateCapacity:      getEnvInt("SOURCE_RATE_CAPACITY", 50),
		RateRefill:        getEnvInt("SOURCE_RATE_REFILL", 10),
		RateInterval:      time.Duration(getEnvInt("SOURCE_RATE_INTERVAL_MS", 1000)) * time.Millisecond,
		FailureThreshold:  getEnvInt("CIRCUIT_FAILURES", 3),
		HalfOpenSuccesses: getEnvInt("CIRCUIT_HALF_OPEN_SUCCESS", 1),
		CircuitCooldown:   time.Duration(getEnvInt("CIRCUIT_COOLDOWN_MS", 2000)) * time.Millisecond,
		CacheTTL:          cacheTTL,
		PolicyVersion:     getEnvStr("POLICY_VERSION", "v1"),
		LangfuseHost:      getEnvStr("LANGFUSE_HOST", defaultLangfuseHost),
		LangfuseProject:   getEnvStr("LANGFUSE_PROJECT_ID", ""),
	}
}

func newHTTPClient(timeout time.Duration) *http.Client {
	transport := &http.Transport{
		MaxConnsPerHost:     128,
		MaxIdleConns:        256,
		MaxIdleConnsPerHost: 128,
		IdleConnTimeout:     90 * time.Second,
	}
	return &http.Client{
		Timeout:   timeout,
		Transport: transport,
	}
}

func getEnvStr(key, fallback string) string {
	val := os.Getenv(key)
	if val == "" {
		return fallback
	}
	return val
}

func getEnvInt(key string, fallback int) int {
	val := os.Getenv(key)
	if val == "" {
		return fallback
	}
	parsed, err := strconv.Atoi(val)
	if err != nil {
		return fallback
	}
	return parsed
}
