#!/usr/bin/env python3
"""
Runtime patch to add orchestrator routes to app_main
"""
import sys
import os

# Ensure /app is in path
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

# Change to /app directory
os.chdir('/app')

try:
    # Import app after ensuring path is set
    from services.fiqa_api.app_main import app
    
    # Try to import and mount orchestrator router
    try:
        from services.orchestrate_router import router as orchestrate_router
        app.include_router(orchestrate_router, prefix="/orchestrate")
        print("[PATCH] ✅ Successfully mounted orchestrator router at /orchestrate")
    except Exception as e:
        print(f"[PATCH] ⚠️  Failed to mount orchestrator router: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"[PATCH] ❌ Failed to patch app: {e}")
    import traceback
    traceback.print_exc()

