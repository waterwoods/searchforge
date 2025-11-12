package main

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
	"github.com/searchforge/retrieval_proxy/obs"
	"github.com/searchforge/retrieval_proxy/policy"
	"github.com/searchforge/retrieval_proxy/sources"
)

const (
	defaultPort        = 7070
	defaultBudgetMs    = 600
	defaultTimeoutMs   = 800
	defaultTopK        = 10
	defaultTopKMax     = 64
	defaultTopKInit    = 32
	defaultRetryMax    = 2
	defaultLangfuseHost = "us.cloud.langfuse.com"
)

func main() {
	cfg := loadConfig()

	shutdown, err := obs.InitTracer("retrieval-proxy")
	if err != nil {
		log.Printf("obs: %v", err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := shutdown(ctx); err != nil {
			log.Printf("tracer shutdown error: %v", err)
		}
	}()

	client := newHTTPClient(cfg.Timeout)

	qdrant, err := sources.NewQdrantSource(cfg.QdrantURL, client, cfg.RetryMax)
	if err != nil {
		log.Fatalf("qdrant: %v", err)
	}

	metrics := policy.NewMetrics()

	ctrl, err := controller.New(qdrant, controller.Config{
		SourceName:        "qdrant",
		Collection:        cfg.QdrantCollection,
		DefaultK:          cfg.DefaultK,
		TopKMax:           cfg.TopKMax,
		Fuse: fuse.CombineConfig{
			RRFK:     cfg.RRFK,
			TopKInit: cfg.TopKInit,
			TopKMax:  cfg.TopKMax,
		},
		SourcePolicy: policy.SourceConfig{
			Name:    "qdrant",
			Timeout: cfg.Timeout,
			Rate: policy.RateLimitConfig{
				Capacity:     cfg.RateCapacity,
				RefillTokens: cfg.RateRefill,
				RefillEvery:  cfg.RateInterval,
			},
			Circuit: policy.CircuitBreakerConfig{
				Window:               cfg.CircuitWindow,
				FailureRateThreshold: cfg.CircuitThreshold,
				MinSamples:           cfg.CircuitMinSamples,
				Cooldown:             cfg.CircuitCooldown,
				HalfOpenMaxCalls:     cfg.CircuitHalfOpenMax,
			},
		},
		Metrics:           metrics,
		LangfuseProjectID: cfg.LangfuseProjectID,
		LangfuseHost:      cfg.LangfuseHost,
		FallbackOnError:   true,
	})
	if err != nil {
		log.Fatalf("controller: %v", err)
	}

	router, err := api.NewRouter(ctrl, cfg.BudgetMs)
	if err != nil {
		log.Fatalf("router: %v", err)
	}
	router.Handle("/metrics", promhttp.Handler())

	root := chi.NewRouter()
	root.Mount("/", router)

	server := &http.Server{
		Addr:         ":" + strconv.Itoa(cfg.Port),
		Handler:      root,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("retrieval proxy listening on :%d", cfg.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Printf("shutdown error: %v", err)
	}
}

type config struct {
	Port              int
	BudgetMs          int
	DefaultK          int
	TopKMax           int
	TopKInit          int
	RRFK              int
	QdrantURL         string
	QdrantCollection  string
	Timeout           time.Duration
	RetryMax          int
	LangfuseProjectID string
	LangfuseHost      string
	RateCapacity      int
	RateRefill        int
	RateInterval      time.Duration
	CircuitWindow     time.Duration
	CircuitThreshold  float64
	CircuitMinSamples int
	CircuitCooldown   time.Duration
	CircuitHalfOpenMax int
}

func loadConfig() config {
	return config{
		Port:              getEnvInt("PORT", defaultPort),
		BudgetMs:          getEnvInt("BUDGET_MS", defaultBudgetMs),
		DefaultK:          getEnvInt("DEFAULT_K", defaultTopK),
		TopKMax:           getEnvInt("TOPK_MAX", defaultTopKMax),
		TopKInit:          getEnvInt("TOPK_INIT", defaultTopKInit),
		RRFK:              getEnvInt("RRF_K", fuse.DefaultCombineConfig().RRFK),
		QdrantURL:         getEnvStr("QDRANT_URL", "http://qdrant:6333"),
		QdrantCollection:  getEnvStr("QDRANT_COLLECTION", ""),
		Timeout:           time.Duration(getEnvInt("TIMEOUT_MS", defaultTimeoutMs)) * time.Millisecond,
		RetryMax:          getEnvInt("RETRY_MAX", defaultRetryMax),
		LangfuseProjectID: getEnvStr("LANGFUSE_PROJECT_ID", ""),
		LangfuseHost:      getEnvStr("LANGFUSE_HOST", defaultLangfuseHost),
		RateCapacity:      getEnvInt("SOURCE_RATE_CAPACITY", 50),
		RateRefill:        getEnvInt("SOURCE_RATE_REFILL", 10),
		RateInterval:      time.Duration(getEnvInt("SOURCE_RATE_INTERVAL_MS", 1000)) * time.Millisecond,
		CircuitWindow:     time.Duration(getEnvInt("CIRCUIT_WINDOW_MS", 30000)) * time.Millisecond,
		CircuitThreshold:  getEnvFloat("CIRCUIT_THRESHOLD", 0.5),
		CircuitMinSamples: getEnvInt("CIRCUIT_MIN_SAMPLES", 5),
		CircuitCooldown:   time.Duration(getEnvInt("CIRCUIT_COOLDOWN_MS", 5000)) * time.Millisecond,
		CircuitHalfOpenMax: getEnvInt("CIRCUIT_HALF_OPEN_MAX", 1),
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

func getEnvStr(key string, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.Atoi(value); err == nil && parsed > 0 {
			return parsed
		}
	}
	return fallback
}

func getEnvFloat(key string, fallback float64) float64 {
	if value := os.Getenv(key); value != "" {
		if parsed, err := strconv.ParseFloat(value, 64); err == nil && parsed > 0 {
			return parsed
		}
	}
	return fallback
}

