#!/bin/bash
# Short LIVE test (60s per side for demonstration)
cd /Users/nanxinli/Documents/dev/searchforge

# Create a temporary modified version
cat > /tmp/run_live_60s.py << 'PYEOF'
import os
import sys
sys.path.insert(0, '/Users/nanxinli/Documents/dev/searchforge')

# Import and patch
from labs.run_rag_rewrite_ab_live import *

# Override for shorter duration
TEST_CONFIG["mode"] = "live"
TEST_CONFIG["duration_per_side_sec"] = 60  # 60 seconds instead of 600
TEST_CONFIG["bucket_sec"] = 5  # 5-second buckets for 12 total
TEST_CONFIG["target_qps"] = 12

if __name__ == "__main__":
    main()
PYEOF

python /tmp/run_live_60s.py
