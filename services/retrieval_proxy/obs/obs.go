package obs

import (
	"context"
	"sync"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

var (
	setupOnce sync.Once
	shutdown  = func(context.Context) error { return nil }
)

// InitTracer sets up a minimal OpenTelemetry tracer provider.
func InitTracer(serviceName string) (func(context.Context) error, error) {
	var initErr error
	setupOnce.Do(func() {
		res, err := resource.New(context.Background(),
			resource.WithAttributes(
				semconv.ServiceName(serviceName),
			),
		)
		if err != nil {
			initErr = err
			return
		}

		provider := sdktrace.NewTracerProvider(
			sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.TraceIDRatioBased(0.3))),
			sdktrace.WithResource(res),
		)
		otel.SetTracerProvider(provider)
		shutdown = provider.Shutdown
	})
	return shutdown, initErr
}

