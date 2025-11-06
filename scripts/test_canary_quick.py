#!/usr/bin/env python3
"""
Quick test of canary script - 30 seconds instead of 30 minutes
"""
import subprocess
import sys
from pathlib import Path

def main():
    script_path = Path(__file__).parent / "run_canary_30min.py"
    
    print("🧪 Running quick canary test (30 seconds)...")
    print("=" * 70)
    
    # Run with 30 second duration
    result = subprocess.run(
        [sys.executable, str(script_path), "--duration", "30", "--interval", "5"],
        capture_output=False
    )
    
    if result.returncode == 0:
        print()
        print("✅ Quick test completed successfully!")
        print()
        print("Next steps:")
        print("  1. Run full 30-minute test: python scripts/run_canary_30min.py")
        print("  2. Build dashboard: python scripts/build_dashboard.py")
        print("  3. View results: open http://localhost:8080/demo")
    else:
        print()
        print("❌ Test failed. Check that the API is running:")
        print("  bash launch.sh")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())




