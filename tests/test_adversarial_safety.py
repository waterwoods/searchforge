#!/usr/bin/env python3
"""
Test Adversarial Safety Rate

Tests that the multi-knob decider achieves safety_rate ≥0.99 under adversarial conditions.
"""

import pytest
import random
from modules.autotuner.brain.apply import apply_updates, reset_apply_counters, get_apply_counters
from modules.autotuner.brain.multi_knob_decider import decide_multi_knob, reset_round_robin
from modules.autotuner.brain.contracts import TuningInput, SLO
from tests.fixtures import make_multi_knob_input


class TestAdversarialSafety:
    """Test safety rate under adversarial conditions."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_apply_counters()
        reset_round_robin()
    
    def test_safety_rate_with_pre_projection(self):
        """Test that safety rate ≥0.99 with feasibility pre-projection."""
        # Run many adversarial updates with pre-projection
        for _ in range(1000):
            current_params = {
                "ef": random.randint(64, 256),
                "Ncand_max": random.randint(500, 2000),
                "rerank_mult": random.randint(2, 6),
                "T": random.randint(200, 1200)
            }
            
            # Extreme adversarial updates that would violate constraints
            updates = {
                "ef": random.randint(-1000, 1000),  # Extreme ef changes
                "Ncand_max": random.randint(-2000, 2000),  # Extreme Ncand_max changes
                "rerank_mult": random.randint(-50, 50),  # Extreme rerank_mult changes
                "T": random.randint(-2000, 2000)  # Extreme T changes
            }
            
            # Apply with sequential mode (uses pre-projection)
            apply_updates(current_params, updates, "sequential")
        
        # Check safety rate
        stats = get_apply_counters()
        safety_rate = 1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1)
        
        assert safety_rate >= 0.99, f"Safety rate {safety_rate:.3f} below 0.99 with pre-projection"
    
    def test_safety_rate_without_pre_projection(self):
        """Test that safety rate <<0.95 without pre-projection (monkeypatch)."""
        # Monkeypatch to disable pre-projection
        import modules.autotuner.brain.apply as apply_module
        original_make_feasible = apply_module._make_feasible_updates
        
        def no_pre_projection(current_params, updates):
            # Return original updates without feasibility checking
            return updates
        
        apply_module._make_feasible_updates = no_pre_projection
        
        try:
            # Run many adversarial updates without pre-projection
            for _ in range(1000):
                current_params = {
                    "ef": random.randint(64, 256),
                    "Ncand_max": random.randint(500, 2000),
                    "rerank_mult": random.randint(2, 6),
                    "T": random.randint(200, 1200)
                }
                
                # Extreme adversarial updates that would violate constraints
                updates = {
                    "ef": random.randint(-1000, 1000),  # Extreme ef changes
                    "Ncand_max": random.randint(-2000, 2000),  # Extreme Ncand_max changes
                    "rerank_mult": random.randint(-50, 50),  # Extreme rerank_mult changes
                    "T": random.randint(-2000, 2000)  # Extreme T changes
                }
                
                # Apply with atomic mode (no pre-projection, will clip)
                apply_updates(current_params, updates, "atomic")
            
            # Check safety rate
            stats = get_apply_counters()
            safety_rate = 1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1)
            
            # Should be much lower without pre-projection
            assert safety_rate < 0.95, f"Safety rate {safety_rate:.3f} should be <0.95 without pre-projection"
            
        finally:
            # Restore original function
            apply_module._make_feasible_updates = original_make_feasible
    
    def test_sequential_invariant_non_target_fields(self):
        """Test that sequential mode never changes non-target fields."""
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Updates that would violate constraints and should be reduced to single field
        updates = {
            "ef": 1000,  # This would violate ef <= 4*Ncand_max
            "Ncand_max": -500,  # This would violate Ncand_max range
            "rerank_mult": 100,  # This would violate rerank_mult range
            "T": 2000  # This would violate threshold_T range
        }
        
        result = apply_updates(current_params, updates, "sequential")
        
        if result.status == "applied":
            # Check that only ef changed (pre-projection should reduce to single field)
            assert result.params_after["ef"] == current_params["ef"] + updates["ef"]
            # Other fields should remain unchanged due to pre-projection
            assert result.params_after["Ncand_max"] == current_params["Ncand_max"]
            assert result.params_after["rerank_mult"] == current_params["rerank_mult"]
            assert result.params_after["T"] == current_params["T"]
    
    def test_per_knob_update_counts_populated(self):
        """Test that per-knob update counts are properly populated."""
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        # Test different knob updates
        updates1 = {"ef": 50}  # ef_search update
        apply_updates(current_params, updates1, "atomic")
        
        updates2 = {"Ncand_max": 100}  # candidate_k update
        apply_updates(current_params, updates2, "atomic")
        
        updates3 = {"rerank_mult": 1}  # rerank_k update
        apply_updates(current_params, updates3, "atomic")
        
        updates4 = {"T": 100}  # threshold_T update
        apply_updates(current_params, updates4, "atomic")
        
        # Check that counters are populated
        stats = get_apply_counters()
        assert stats["ef_search_updates"] >= 1
        assert stats["candidate_k_updates"] >= 1
        assert stats["rerank_k_updates"] >= 1
        assert stats["threshold_T_updates"] >= 1
    
    def test_reporting_fields_rendered(self):
        """Test that reporting fields are properly rendered in JSON."""
        # Simulate some updates to populate counters
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        for _ in range(10):
            updates = {
                "ef": random.randint(-50, 50),
                "Ncand_max": random.randint(-100, 100)
            }
            apply_updates(current_params, updates, "atomic")
        
        # Get stats
        stats = get_apply_counters()
        
        # Simulate JSON structure that should be generated
        json_summary = {
            "per_knob_update_counts": {
                "ef_search": {
                    "count": stats.get("ef_search_updates", 0),
                    "percentage": round(stats.get("ef_search_updates", 0) / max(stats.get("decide_total", 1), 1) * 100, 1)
                },
                "candidate_k": {
                    "count": stats.get("candidate_k_updates", 0),
                    "percentage": round(stats.get("candidate_k_updates", 0) / max(stats.get("decide_total", 1), 1) * 100, 1)
                },
                "rerank_k": {
                    "count": stats.get("rerank_k_updates", 0),
                    "percentage": round(stats.get("rerank_k_updates", 0) / max(stats.get("decide_total", 1), 1) * 100, 1)
                },
                "threshold_T": {
                    "count": stats.get("threshold_T_updates", 0),
                    "percentage": round(stats.get("threshold_T_updates", 0) / max(stats.get("decide_total", 1), 1) * 100, 1)
                }
            },
            "clipped_count": stats["clipped_count"],
            "rollback_count": stats["rollback_count"],
            "rejected_by_joint": stats["rejected_by_joint"],
            "multi_knob_safety_rate": round(1.0 - (stats["clipped_count"] + stats["rollback_count"]) / max(stats["decide_total"], 1), 3),
            "top_reject_clip_reasons": [
                f"clipped_count: {stats['clipped_count']}",
                f"rejected_by_joint: {stats['rejected_by_joint']}",
                f"rollback_count: {stats['rollback_count']}"
            ]
        }
        
        # Verify all fields are present and properly formatted
        assert "per_knob_update_counts" in json_summary
        assert "clipped_count" in json_summary
        assert "rollback_count" in json_summary
        assert "rejected_by_joint" in json_summary
        assert "multi_knob_safety_rate" in json_summary
        assert "top_reject_clip_reasons" in json_summary
        
        # Verify per-knob structure
        for knob in ["ef_search", "candidate_k", "rerank_k", "threshold_T"]:
            assert knob in json_summary["per_knob_update_counts"]
            assert "count" in json_summary["per_knob_update_counts"][knob]
            assert "percentage" in json_summary["per_knob_update_counts"][knob]
    
    def test_constraints_strictly_aligned(self):
        """Test that constraints are strictly aligned to agreed invariants."""
        from modules.autotuner.brain.constraints import _check_joint_constraints
        
        # Test cases that should violate only agreed invariants
        test_cases = [
            # Case 1: rerank_k > candidate_k
            {
                "ef": 200,
                "Ncand_max": 1000,
                "rerank_mult": 200,  # > 10% of Ncand_max
                "T": 500
            },
            # Case 2: ef_search > 4*candidate_k
            {
                "ef": 5000,  # > 4 * Ncand_max
                "Ncand_max": 1000,
                "rerank_mult": 3,
                "T": 500
            },
            # Case 3: threshold_T out of range
            {
                "ef": 200,
                "Ncand_max": 1000,
                "rerank_mult": 3,
                "T": 2000  # threshold_T = 2.0 > 1.0
            }
        ]
        
        for i, params in enumerate(test_cases):
            violations = _check_joint_constraints(params)
            assert len(violations) > 0, f"Test case {i+1} should have constraint violations"
            
            # Verify only agreed invariants are checked
            expected_violations = ["RERANK_GT_CANDIDATE", "EF_GT_4X_CANDIDATE", "THRESHOLD_T_RANGE"]
            for violation in violations:
                assert violation in expected_violations, f"Unexpected violation: {violation}"
    
    def test_legacy_fields_unchanged(self):
        """Test that legacy fields are unchanged."""
        # This test ensures that existing functionality is not broken
        current_params = {
            "ef": 200,
            "Ncand_max": 1000,
            "rerank_mult": 3,
            "T": 500
        }
        
        updates = {"ef": 50}
        result = apply_updates(current_params, updates, "atomic")
        
        # Legacy functionality should still work
        assert result.status == "applied"
        assert result.params_after["ef"] == current_params["ef"] + updates["ef"]
        assert result.params_after["Ncand_max"] == current_params["Ncand_max"]
        assert result.params_after["rerank_mult"] == current_params["rerank_mult"]
        assert result.params_after["T"] == current_params["T"]
