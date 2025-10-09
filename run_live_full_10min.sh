#!/bin/bash
# Full 10-minute LIVE A/B Test
# Each side runs for 600 seconds (10 minutes)

cd /Users/nanxinli/Documents/dev/searchforge

echo "=================================================="
echo "🚀 Starting FULL 10-Minute LIVE A/B Test"
echo "=================================================="
echo ""
echo "⏱️  Duration: 600s per side (10 minutes each)"
echo "📊 Expected samples: ~720 per side (12 QPS x 60s)"
echo "🗂️  Buckets: ~60 per side (10s buckets)"
echo ""
echo "This will take approximately 20 minutes total."
echo ""
read -p "Press Enter to start, or Ctrl+C to cancel..."

# Create dedicated LIVE test script
cat > /tmp/run_live_10min.py << 'PYEOF'
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

# Force LIVE mode
os.environ['TEST_MODE'] = 'live'

# Import after setting env
from labs.run_rag_rewrite_ab_live import *

# Ensure LIVE configuration
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 600  # Full 10 minutes
TEST_CONFIG["bucket_sec"] = 10  # 10-second buckets
TEST_CONFIG["target_qps"] = 12  # 12 queries per second

if __name__ == "__main__":
    main()
PYEOF

# Run it
python /tmp/run_live_10min.py

echo ""
echo "=================================================="
echo "✅ LIVE Test Complete!"
echo "=================================================="
echo ""
echo "📊 Reports generated:"
echo "   HTML: reports/rag_rewrite_ab.html"
echo "   JSON: reports/rag_rewrite_ab.json"
echo ""
echo "Run: open reports/rag_rewrite_ab.html"
