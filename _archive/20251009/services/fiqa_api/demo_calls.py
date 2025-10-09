"""
Minimal Demo Client - Test the API
"""

import requests
import time
import csv
from pathlib import Path

BASE_URL = "http://localhost:9000"

# Finance-related queries
QUERIES = [
    "How do I calculate compound interest?",
    "What is the difference between a Roth IRA and Traditional IRA?",
    "How can I improve my credit score?",
    "What are the best investment strategies for beginners?",
    "How do I file taxes for freelance income?",
    "What is diversification in investment?",
    "Should I pay off debt or invest?",
    "How do index funds work?",
    "What is the best way to save for retirement?",
    "How do I create a budget?",
]


def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.json()}")
    return response.status_code == 200


def run_search_tests():
    """Run search tests and collect metrics"""
    latencies = []
    cache_hits = 0
    total_queries = len(QUERIES)
    
    print(f"\n🚀 Running {total_queries} search queries...\n")
    
    for i, query in enumerate(QUERIES, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/search",
                json={"query": query, "top_k": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                latencies.append(data['latency_ms'])
                if data['cache_hit']:
                    cache_hits += 1
                
                print(f"[{i}/{total_queries}] Query: {query[:40]}...")
                print(f"         Latency: {data['latency_ms']:.2f}ms | Cache: {data['cache_hit']} | Results: {len(data['answers'])}")
            else:
                print(f"[{i}/{total_queries}] ERROR: {response.status_code}")
                
        except Exception as e:
            print(f"[{i}/{total_queries}] EXCEPTION: {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Calculate statistics
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        cache_hit_rate = cache_hits / total_queries
        
        print(f"\n{'='*60}")
        print(f"📊 Performance Summary")
        print(f"{'='*60}")
        print(f"Total Queries:    {total_queries}")
        print(f"Avg Latency:      {avg_latency:.2f}ms")
        print(f"P95 Latency:      {p95_latency:.2f}ms")
        print(f"Cache Hit Rate:   {cache_hit_rate:.1%} ({cache_hits}/{total_queries})")
        print(f"{'='*60}\n")
        
        # Read and display CSV stats
        csv_path = Path(__file__).parent / "reports" / "fiqa_api_live.csv"
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                print(f"📝 Log file: {csv_path}")
                print(f"   Total entries: {len(rows) - 1}")  # Exclude header
        
        return True
    else:
        print("❌ No successful queries")
        return False


def main():
    """Main test runner"""
    print("="*60)
    print("🎯 Minimal FIQA API Demo Client")
    print("="*60)
    
    # Test health
    if not test_health():
        print("❌ Health check failed. Is the server running?")
        print("   Start with: uvicorn app:app --reload")
        return
    
    # Run search tests
    success = run_search_tests()
    
    if success:
        print("✅ Demo completed successfully!")
    else:
        print("❌ Demo had errors")


if __name__ == "__main__":
    main()

