#!/bin/bash
# Smoke test for Auto-Traffic TPS monitoring
# Prints /auto/status every 5s for 1 minute

ENDPOINT="${1:-http://localhost:8080/auto/status}"
INTERVAL=5
DURATION=60

echo "=== Auto-Traffic TPS Smoke Test ==="
echo "Endpoint: $ENDPOINT"
echo "Interval: ${INTERVAL}s"
echo "Duration: ${DURATION}s"
echo ""

start_time=$(date +%s)
end_time=$((start_time + DURATION))

while [ $(date +%s) -lt $end_time ]; do
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp]"
    
    # Fetch status and extract key metrics
    response=$(curl -s "$ENDPOINT" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        # Parse JSON fields (using grep/sed for portability, no jq required)
        enabled=$(echo "$response" | grep -o '"enabled":[^,}]*' | sed 's/.*://')
        running=$(echo "$response" | grep -o '"running":[^,}]*' | sed 's/.*://')
        qps=$(echo "$response" | grep -o '"qps":[^,}]*' | sed 's/.*://')
        eff_tps=$(echo "$response" | grep -o '"effective_tps_60s":[^,}]*' | sed 's/.*://')
        in_flight=$(echo "$response" | grep -o '"in_flight":[^,}]*' | sed 's/.*://')
        concurrency=$(echo "$response" | grep -o '"concurrency":[^,}]*' | sed 's/.*://')
        split_factor=$(echo "$response" | grep -o '"split_factor":[^,}]*' | sed 's/.*://')
        idle_secs=$(echo "$response" | grep -o '"idle_secs":[^,}]*' | sed 's/.*://')
        
        # Display formatted output
        echo "  enabled=$enabled running=$running"
        echo "  qps=$qps eff_tps=$eff_tps"
        echo "  in_flight=$in_flight concurrency=$concurrency"
        echo "  split_factor=$split_factor idle_secs=$idle_secs"
    else
        echo "  ERROR: Failed to fetch $ENDPOINT"
    fi
    
    echo ""
    sleep $INTERVAL
done

echo "=== Smoke test complete ==="

