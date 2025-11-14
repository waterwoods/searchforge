//go:build nometrics

package obs

// mvp-5

import (
	"context"
	"time"
)

func ObserveProxyRequest(string, time.Duration, string) {}

func RecordSourceDuration(string, time.Duration) {}

func RecordSourceError(string, string) {}

func IncBudgetHit() {}

func SetCircuitState(string, string) {}

func InitTracer(string) (func(context.Context) error, error) {
	return func(context.Context) error { return nil }, nil
}

