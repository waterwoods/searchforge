#!/bin/bash
# verify_milvus_lane.sh - Milvus Lane Verification Script
# ========================================================
# One-click verification of Milvus integration.
#
# Tests:
# 1. Start Milvus container
# 2. Create collection with HNSW index
# 3. Import 1000 vectors
# 4. Run 100 search queries
# 5. Report p95 latency and success rate
#
# Usage:
#   ./scripts/verify_milvus_lane.sh
#
# Environment:
#   MILVUS_HOST - Milvus host (default: localhost)
#   MILVUS_PORT - Milvus port (default: 19530)
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MILVUS_HOST="${MILVUS_HOST:-localhost}"
MILVUS_PORT="${MILVUS_PORT:-19530}"
COLLECTION_NAME="fiqa_test"
NUM_VECTORS=1000
NUM_QUERIES=100

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker is required but not installed"
        exit 1
    fi
    
    # Check if pymilvus is installed
    if ! python3 -c "import pymilvus" 2>/dev/null; then
        log_warning "pymilvus not installed, attempting to install..."
        pip3 install -q pymilvus sentence-transformers numpy
    fi
    
    log_success "Prerequisites OK"
}

# Start Milvus
start_milvus() {
    log_info "Starting Milvus services..."
    
    # Check if Milvus is already running
    if docker ps | grep -q milvus-standalone; then
        log_success "Milvus already running"
        return 0
    fi
    
    # Start via docker-compose
    if [ -f "docker-compose.yml" ]; then
        log_info "Starting Milvus via docker-compose..."
        docker-compose up -d milvus-standalone milvus-etcd milvus-minio
        
        # Wait for Milvus to be ready
        log_info "Waiting for Milvus to be ready (max 60s)..."
        for i in {1..60}; do
            if docker logs searchforge-milvus-standalone-1 2>&1 | grep -q "Server started"; then
                log_success "Milvus is ready"
                sleep 5  # Extra time for full initialization
                return 0
            fi
            sleep 1
        done
        
        log_error "Milvus failed to start in time"
        return 1
    else
        log_error "docker-compose.yml not found"
        exit 1
    fi
}

# Run verification test
run_verification() {
    log_info "Running Milvus verification test..."
    
    # Create Python test script
    cat > /tmp/milvus_verify.py <<'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""Milvus Lane Verification Test"""

import sys
import time
import numpy as np
from typing import List

try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configuration
MILVUS_HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
MILVUS_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 19530
COLLECTION_NAME = sys.argv[3] if len(sys.argv) > 3 else "fiqa_test"
NUM_VECTORS = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
NUM_QUERIES = int(sys.argv[5]) if len(sys.argv) > 5 else 100
DIM = 384

def main():
    print(f"\n{'='*70}")
    print("MILVUS LANE VERIFICATION TEST")
    print(f"{'='*70}")
    print(f"Host: {MILVUS_HOST}:{MILVUS_PORT}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Vectors: {NUM_VECTORS}")
    print(f"Queries: {NUM_QUERIES}")
    print(f"{'='*70}\n")
    
    # Step 1: Connect
    print("[1/5] Connecting to Milvus...")
    try:
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
        print("  ✓ Connected")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return 1
    
    # Step 2: Create collection
    print("\n[2/5] Creating collection...")
    try:
        # Drop if exists
        if utility.has_collection(COLLECTION_NAME):
            Collection(COLLECTION_NAME).drop()
            print(f"  ✓ Dropped existing collection")
        
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vec", dtype=DataType.FLOAT_VECTOR, dim=DIM),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        ]
        schema = CollectionSchema(fields=fields, description="Verification test collection")
        
        # Create collection
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        print(f"  ✓ Created collection '{COLLECTION_NAME}'")
        
        # Create HNSW index
        index_params = {
            "metric_type": "L2",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 64}
        }
        collection.create_index(field_name="vec", index_params=index_params)
        print(f"  ✓ Created HNSW index (M=16, ef=64)")
        
    except Exception as e:
        print(f"  ✗ Collection creation failed: {e}")
        return 1
    
    # Step 3: Import vectors
    print(f"\n[3/5] Importing {NUM_VECTORS} vectors...")
    try:
        # Generate random vectors
        vectors = np.random.rand(NUM_VECTORS, DIM).astype(np.float32).tolist()
        texts = [f"document_{i}" for i in range(NUM_VECTORS)]
        
        # Insert in batches
        batch_size = 200
        for i in range(0, NUM_VECTORS, batch_size):
            end = min(i + batch_size, NUM_VECTORS)
            batch_vectors = vectors[i:end]
            batch_texts = texts[i:end]
            
            collection.insert([batch_vectors, batch_texts])
        
        collection.flush()
        print(f"  ✓ Imported {NUM_VECTORS} vectors")
        
        # Load collection
        collection.load()
        print(f"  ✓ Loaded collection to memory")
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return 1
    
    # Step 4: Run queries
    print(f"\n[4/5] Running {NUM_QUERIES} search queries...")
    latencies = []
    successes = 0
    errors = 0
    
    try:
        search_params = {"metric_type": "L2", "params": {"ef": 64}}
        
        for i in range(NUM_QUERIES):
            # Generate random query vector
            query_vec = np.random.rand(DIM).astype(np.float32).tolist()
            
            start = time.perf_counter()
            try:
                results = collection.search(
                    data=[query_vec],
                    anns_field="vec",
                    param=search_params,
                    limit=10,
                    output_fields=["text"]
                )
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)
                
                if len(results[0]) > 0:
                    successes += 1
                
            except Exception as e:
                errors += 1
                print(f"  ✗ Query {i+1} failed: {e}")
        
        print(f"  ✓ Completed {NUM_QUERIES} queries")
        
    except Exception as e:
        print(f"  ✗ Search test failed: {e}")
        return 1
    
    # Step 5: Calculate metrics
    print(f"\n[5/5] Calculating metrics...")
    if latencies:
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        avg = np.mean(latencies)
        success_rate = successes / NUM_QUERIES * 100
        error_rate = errors / NUM_QUERIES * 100
        
        print(f"\n{'='*70}")
        print("VERIFICATION RESULTS")
        print(f"{'='*70}")
        print(f"Queries:        {NUM_QUERIES}")
        print(f"Successes:      {successes} ({success_rate:.1f}%)")
        print(f"Errors:         {errors} ({error_rate:.1f}%)")
        print(f"")
        print(f"Latency P50:    {p50:.2f} ms")
        print(f"Latency P95:    {p95:.2f} ms")
        print(f"Latency P99:    {p99:.2f} ms")
        print(f"Latency Avg:    {avg:.2f} ms")
        print(f"{'='*70}\n")
        
        # Verdict
        if success_rate >= 99.0 and p95 < 100:
            print("✅ PASS: Milvus lane is working correctly!")
            return 0
        elif success_rate >= 95.0:
            print("⚠️  WARN: Success rate is acceptable but not optimal")
            return 0
        else:
            print("❌ FAIL: Success rate too low or latency too high")
            return 1
    else:
        print("❌ FAIL: No successful queries")
        return 1

if __name__ == "__main__":
    sys.exit(main())
PYTHON_SCRIPT
    
    # Run the test
    python3 /tmp/milvus_verify.py "$MILVUS_HOST" "$MILVUS_PORT" "$COLLECTION_NAME" "$NUM_VECTORS" "$NUM_QUERIES"
    RESULT=$?
    
    # Cleanup
    rm -f /tmp/milvus_verify.py
    
    return $RESULT
}

# Main execution
main() {
    echo ""
    echo "======================================================================"
    echo "MILVUS LANE VERIFICATION"
    echo "======================================================================"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    echo ""
    
    # Start Milvus
    start_milvus
    echo ""
    
    # Run verification
    run_verification
    RESULT=$?
    
    echo ""
    if [ $RESULT -eq 0 ]; then
        log_success "Verification complete!"
        echo ""
        echo "Next steps:"
        echo "  1. Run with VECTOR_BACKEND=milvus"
        echo "  2. Test routing: ./scripts/run_lab_headless.sh routing --with-load --vector-backend milvus"
        echo ""
    else
        log_error "Verification failed!"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check Milvus logs: docker logs searchforge-milvus-standalone-1"
        echo "  2. Verify Milvus is running: docker ps | grep milvus"
        echo "  3. Check connectivity: curl http://localhost:9091/healthz"
        echo ""
    fi
    
    return $RESULT
}

# Run main
main

