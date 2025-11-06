#!/usr/bin/env python3
"""
Basic smoke test for Agent V2 components
========================================
Tests imports and basic functionality without dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def test_imports():
    """Test that all V2 modules can be imported."""
    print("Testing imports...")
    
    try:
        from agents.labops.v2.explainers.rules import RuleBasedExplainer, explain_result
        print("  ✓ Explainer imports OK")
        
        from agents.labops.v2.agent_runner_v2 import LabOpsAgentV2, load_config
        print("  ✓ Agent runner imports OK")
        
        from agents.labops.v2.endpoints import router
        print("  ✓ Endpoints imports OK")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_explainer_fallback():
    """Test explainer with fallback template."""
    print("\nTesting explainer fallback...")
    
    try:
        from agents.labops.v2.explainers.rules import RuleBasedExplainer
        
        project_root = Path(__file__).parent.parent.parent.parent
        explainer = RuleBasedExplainer(project_root)
        
        # Test with health gate failure
        result = {
            "ok": False,
            "phase": "health_gate",
            "reason": "Redis unhealthy"
        }
        
        explanation = explainer.explain(result)
        
        assert "bullets" in explanation
        assert "sources" in explanation
        assert "mode" in explanation
        assert len(explanation["bullets"]) > 0
        
        print(f"  ✓ Fallback template works ({len(explanation['bullets'])} bullets)")
        return True
    except Exception as e:
        print(f"  ✗ Explainer test failed: {e}")
        return False


def test_explainer_with_metrics():
    """Test explainer with valid metrics."""
    print("\nTesting explainer with metrics...")
    
    try:
        from agents.labops.v2.explainers.rules import RuleBasedExplainer
        
        project_root = Path(__file__).parent.parent.parent.parent
        explainer = RuleBasedExplainer(project_root)
        
        # Test with PASS verdict
        result = {
            "ok": True,
            "phase": "complete",
            "judgment": {
                "ok": True,
                "metrics": {
                    "delta_p95_pct": -12.5,
                    "delta_qps_pct": -2.3,
                    "error_rate_pct": 0.15
                },
                "ab_imbalance": 2.1,
                "decision": {
                    "verdict": "pass",
                    "reason": "P95 improved significantly"
                }
            },
            "application": {
                "applied": False,
                "safe_mode": True
            },
            "config": {
                "experiment": {
                    "routing_mode": "cost_adaptive",
                    "flow_policy": "aimd"
                }
            }
        }
        
        explanation = explainer.explain(result)
        
        assert len(explanation["bullets"]) > 0
        assert explanation["mode"] in ["full", "template"]
        assert "sources" in explanation
        
        print(f"  ✓ Metrics explanation works ({len(explanation['bullets'])} bullets)")
        print(f"    Mode: {explanation['mode']}")
        print(f"    Sample bullet: {explanation['bullets'][0][:50]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_load():
    """Test config loading."""
    print("\nTesting config loading...")
    
    try:
        from agents.labops.v2.agent_runner_v2 import load_config
        
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "agents" / "labops" / "plan" / "plan_combo.yaml"
        
        if not config_path.exists():
            print(f"  ⊘ Config file not found (non-critical): {config_path}")
            return True
        
        config = load_config(config_path)
        
        assert "experiment" in config
        assert "thresholds" in config
        
        print("  ✓ Config loads successfully")
        return True
    except Exception as e:
        print(f"  ✗ Config test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent V2 Basic Smoke Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_explainer_fallback,
        test_explainer_with_metrics,
        test_config_load
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

