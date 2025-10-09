#!/usr/bin/env python3
"""
Simple Canary Test

A simplified test to verify the canary system works end-to-end.
"""

import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import get_canary_executor, get_config_manager


def main():
    """Simple test of canary deployment."""
    print("Simple Canary Deployment Test")
    print("=" * 40)
    
    # Get components
    config_manager = get_config_manager()
    canary_executor = get_canary_executor()
    
    # Show current state
    print("Current state:")
    state = config_manager.get_canary_status()
    print(f"  Status: {state['status']}")
    print(f"  Active: {state['active_config']}")
    print(f"  Candidate: {state['candidate_config']}")
    
    # Show executor status
    print("\nExecutor status:")
    executor_status = canary_executor.get_current_status()
    print(f"  Is running: {executor_status['is_running']}")
    print(f"  Status: {executor_status['status']}")
    
    # If there's a running canary, stop it
    if executor_status['is_running']:
        print("\nStopping existing canary...")
        try:
            result = canary_executor.stop_canary(promote=False, reason="Test cleanup")
            print(f"  Stopped: {result.status}")
        except Exception as e:
            print(f"  Error stopping: {e}")
    
    # Start a new canary
    print("\nStarting new canary...")
    try:
        result = canary_executor.start_canary("candidate_high_recall")
        print(f"  Started: {result.deployment_id}")
        print(f"  Traffic split: {result.traffic_split}")
        
        # Wait a bit
        print("\nWaiting 3 seconds...")
        time.sleep(3)
        
        # Stop the canary
        print("\nStopping canary...")
        result = canary_executor.stop_canary(promote=False, reason="Test completed")
        print(f"  Stopped: {result.status}")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()


