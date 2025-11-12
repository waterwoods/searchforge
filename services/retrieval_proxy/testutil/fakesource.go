package testutil

import (
	"net/http"
	"net/http/httptest"
	"sync"
	"time"
)

// FakeResponse describes the behaviour of a single fake upstream call.
type FakeResponse struct {
	Delay  time.Duration
	Status int
	Body   string
}

// FakeSource provides a controllable httptest server used to simulate
// upstream retrieval sources with configurable latency and status codes.
type FakeSource struct {
	server    *httptest.Server
	mu        sync.Mutex
	responses []FakeResponse
	index     int
	calls     int
}

// NewFakeSource constructs a new FakeSource with the provided response plan.
// When the number of executed calls exceeds the length of responses, the last
// response is reused.
func NewFakeSource(responses ...FakeResponse) *FakeSource {
	if len(responses) == 0 {
		responses = []FakeResponse{{Status: http.StatusOK}}
	}

	fs := &FakeSource{
		responses: responses,
	}

	fs.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		resp := fs.nextResponse()
		if resp.Delay > 0 {
			timer := time.NewTimer(resp.Delay)
			select {
			case <-timer.C:
			case <-r.Context().Done():
				timer.Stop()
				return
			}
		}

		status := resp.Status
		if status == 0 {
			status = http.StatusOK
		}

		w.WriteHeader(status)
		if resp.Body != "" {
			_, _ = w.Write([]byte(resp.Body))
		}
	}))

	return fs
}

func (f *FakeSource) nextResponse() FakeResponse {
	f.mu.Lock()
	defer f.mu.Unlock()

	f.calls++
	if f.index >= len(f.responses) {
		return f.responses[len(f.responses)-1]
	}

	resp := f.responses[f.index]
	f.index++
	return resp
}

// URL returns the base URL for the fake source.
func (f *FakeSource) URL() string {
	if f == nil || f.server == nil {
		return ""
	}
	return f.server.URL
}

// Calls returns the number of requests handled so far.
func (f *FakeSource) Calls() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.calls
}

// SetResponses overrides the remaining response plan, resetting the cursor.
func (f *FakeSource) SetResponses(responses ...FakeResponse) {
	if f == nil {
		return
	}
	if len(responses) == 0 {
		responses = []FakeResponse{{Status: http.StatusOK}}
	}
	f.mu.Lock()
	f.responses = responses
	f.index = 0
	f.calls = 0
	f.mu.Unlock()
}

// Close terminates the hosted httptest server.
func (f *FakeSource) Close() {
	if f == nil || f.server == nil {
		return
	}
	f.server.Close()
}

