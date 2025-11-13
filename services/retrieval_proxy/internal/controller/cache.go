package controller

// mvp-5

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"sync"
	"time"

	"github.com/searchforge/retrieval_proxy/fuse"
	"github.com/searchforge/retrieval_proxy/internal/api"
)

// CacheEntry captures cached response pieces.
// mvp-5
type CacheEntry struct {
	Items     []api.Item
	PerSource map[string]int64
	TotalMS   int64
	Degraded  bool
	RetCode   string
	storedAt  time.Time
}

// Cache is a lightweight in-memory cache with TTL.
// mvp-5
type Cache struct {
	ttl   time.Duration
	mu    sync.RWMutex
	store map[string]CacheEntry
}

// NewCache returns a cache; zero ttl disables caching.
// mvp-5
func NewCache(ttl time.Duration) *Cache {
	return &Cache{
		ttl:   ttl,
		store: make(map[string]CacheEntry),
	}
}

// Get retrieves an entry if still fresh.
// mvp-5
func (c *Cache) Get(key string) (CacheEntry, bool) {
	if c == nil || c.ttl <= 0 {
		return CacheEntry{}, false
	}

	c.mu.RLock()
	entry, ok := c.store[key]
	c.mu.RUnlock()
	if !ok {
		return CacheEntry{}, false
	}
	if time.Since(entry.storedAt) > c.ttl {
		c.mu.Lock()
		delete(c.store, key)
		c.mu.Unlock()
		return CacheEntry{}, false
	}
	return entry, true
}

// Set stores an entry.
// mvp-5
func (c *Cache) Set(key string, entry CacheEntry) {
	if c == nil || c.ttl <= 0 {
		return
	}
	entry.storedAt = time.Now()
	c.mu.Lock()
	c.store[key] = entry
	c.mu.Unlock()
}

// BuildCacheKey hashes the parameters that influence retrieval output.
// mvp-5
func BuildCacheKey(query string, k int, source string, fuseCfg fuse.CombineConfig, policyVersion string) string {
	payload := map[string]any{
		"query":          query,
		"k":              k,
		"sources":        source,
		"rrf_k":          fuseCfg.RRFK,
		"topk_init":      fuseCfg.TopKInit,
		"topk_max":       fuseCfg.TopKMax,
		"filters":        "", // placeholder for future filter support
		"tenant":         "", // placeholder for multi-tenant caching
		"policy_version": policyVersion,
	}
	raw, _ := json.Marshal(payload)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

