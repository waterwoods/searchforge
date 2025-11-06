#!/usr/bin/env python3
"""
Quick demonstration of CAG cache usage.

Shows how to use the cache in different scenarios.
"""
from modules.rag.contracts import CacheConfig, CacheStats
from modules.rag.cache import CAGCache


def demo_exact_cache():
    """Demonstrate exact matching cache."""
    print("\n" + "="*60)
    print("DEMO 1: Exact Matching Cache")
    print("="*60)
    
    config = CacheConfig(policy="exact", ttl_sec=10, normalize=False)
    cache = CAGCache(config)
    
    # First query - miss
    query = "What is machine learning?"
    result = cache.get(query)
    print(f"\n1. Query: {query}")
    print(f"   Cache result: {'HIT' if result else 'MISS'}")
    
    if not result:
        answer = "ML is a subset of AI..."
        cache.put(query, answer)
        print(f"   Cached answer: {answer}")
    
    # Second query - hit
    result = cache.get(query)
    print(f"\n2. Same query again")
    print(f"   Cache result: {'HIT' if result else 'MISS'}")
    if result:
        print(f"   Retrieved: {result['answer']}")
    
    # Different query - miss
    query2 = "What is deep learning?"
    result = cache.get(query2)
    print(f"\n3. Query: {query2}")
    print(f"   Cache result: {'HIT' if result else 'MISS'}")
    
    # Stats
    stats = cache.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Lookups: {stats.lookups}")
    print(f"   Hits: {stats.hits}")
    print(f"   Hit Rate: {stats.hit_rate:.1%}")


def demo_normalized_cache():
    """Demonstrate normalized matching cache."""
    print("\n" + "="*60)
    print("DEMO 2: Normalized Matching Cache")
    print("="*60)
    
    config = CacheConfig(policy="normalized", ttl_sec=10)
    cache = CAGCache(config)
    
    # Store with one format
    query1 = "Hello World"
    cache.put(query1, "Answer 1")
    print(f"\n1. Stored: '{query1}'")
    
    # Retrieve with different formats
    variations = [
        "hello world",
        "HELLO WORLD",
        "  hello   world  "
    ]
    
    print(f"\n2. Testing variations:")
    for var in variations:
        result = cache.get(var)
        print(f"   '{var}' -> {'HIT ✓' if result else 'MISS ✗'}")
    
    # Stats
    stats = cache.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Lookups: {stats.lookups}")
    print(f"   Hits: {stats.hits}")
    print(f"   Hit Rate: {stats.hit_rate:.1%}")


def demo_metrics():
    """Demonstrate metrics tracking."""
    print("\n" + "="*60)
    print("DEMO 3: Metrics Tracking")
    print("="*60)
    
    config = CacheConfig(policy="exact", capacity=3)  # Small capacity
    cache = CAGCache(config)
    
    # Fill cache
    print("\n1. Filling cache (capacity=3):")
    for i in range(3):
        cache.put(f"query{i}", f"answer{i}")
        print(f"   Cached query{i}")
    
    # Access to make q1 most recent
    cache.get("query1")
    print(f"\n2. Accessed query1 (making it most recent)")
    
    # Add one more - should evict q0 (LRU)
    cache.put("query3", "answer3")
    print(f"\n3. Added query3 (should evict query0)")
    
    # Verify
    print(f"\n4. Testing what's still cached:")
    for i in range(4):
        result = cache.get(f"query{i}")
        print(f"   query{i}: {'HIT ✓' if result else 'MISS ✗'}")
    
    # Final stats
    stats = cache.get_stats()
    print(f"\n📊 Final Stats:")
    print(f"   Lookups: {stats.lookups}")
    print(f"   Hits: {stats.hits}")
    print(f"   Misses: {stats.misses}")
    print(f"   Evictions: {stats.evictions}")
    print(f"   Hit Rate: {stats.hit_rate:.1%}")


def main():
    """Run all demos."""
    print("\n🎯 CAG Cache Demonstration")
    print("="*60)
    
    demo_exact_cache()
    demo_normalized_cache()
    demo_metrics()
    
    print("\n" + "="*60)
    print("✅ All demos complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

